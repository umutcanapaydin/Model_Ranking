#!/usr/bin/env python3
"""Run every conformance test and report each by name.

The record validator's `--self-test` calls rule functions directly, which can prove a rule works
while nothing shipped ever invokes it. These tests go the other way: they exercise the DOCUMENTED
surface -- the Makefile, the workflows, the hook config, the record globs -- and assert that the
claims match the code.

Every test here must be reachable from `make gate`, or it is a control with no caller.

Two properties, both checked here:

  1. THE SUITE IS DERIVED, NOT ENUMERATED. The suite is `test-*.py` in this directory, and each
     test's own docstring is its description. Add a file and it runs; there is no second list to
     remember. A file with no docstring, or one that does not parse, FAILS.

  2. CALLER-LIVENESS. Every leg of `make gate` must be run by a job the workflows actually execute.
     A gate whose only caller is a human who already knows its name is a control nobody runs.

Fail-closed: a derived set that comes back EMPTY, or a check that cannot parse its input, is a
FAILURE. A vacuous pass is the shape of every defect a suite like this exists to catch.

Exit: 0 all pass - 1 any fail.
"""
import ast
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent

# The required job is the one that runs the governance validator -- identified by what it DOES,
# not by what it is called, so the check survives a rename of the job.
REQUIRED_MARKER = "check_records.py"


def required_job(body: str) -> str | None:
    """The job that runs the governance validator, by what it does rather than what it is called."""
    for m in re.finditer(r"^  ([a-z][\w-]*):\n((?:    .*\n|\n)*)", body, re.M):
        if REQUIRED_MARKER in m.group(2):
            return m.group(1)
    return None

# The dev dependencies -- PyYAML among them -- live in `.venv`, not in the system interpreter.
# Running with the system python made `test-ci-yaml` report CANNOT RUN: the correct refusal from the
# wrong interpreter. Prefer the venv when it exists -- `bin/` on macOS and Linux, `Scripts/` on
# Windows.
PY = next((str(p) for p in (PKG / ".venv" / "bin" / "python", PKG / ".venv" / "Scripts" / "python.exe")
           if p.exists()), sys.executable)
# The tests print to a pipe this runner reads. Both ends are UTF-8, whatever the console's code page:
# on a cp1254 console a test printing a character outside it died mid-report, and the runner filed
# the traceback as the test's verdict.
CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def discover_tests() -> list[tuple[str, str]]:
    """Derive the suite from the directory; a test's docstring is its description.

    A file that cannot be parsed, or that carries no docstring, is reported and FAILS. It is not
    skipped: silence is how a leg leaves a gate unnoticed.
    """
    out = []
    for path in sorted(HERE.glob("test-*.py")):
        try:
            doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
        except SyntaxError as exc:
            out.append((path.name, f"!! does not parse: {exc.msg}"))
            continue
        first = (doc or "").strip().splitlines()[0].strip() if doc else ""
        out.append((path.name, first or "!! no docstring -- an unregistered gate"))
    return out


def gate_legs() -> list[str]:
    """The prerequisites of `make gate`, read from the Makefile rather than copied beside it."""
    body = (PKG / "Makefile").read_text(encoding="utf-8")
    found = re.search(r"^gate:[ \t]*([^\n#]*)", body, re.M)
    return found.group(1).split() if found else []


def norm(token: str) -> str:
    """`pip_audit` the module and `pip-audit` the console script are the same tool.

    Without this a gate reads as having no CI caller because the Makefile invokes the module and
    the workflow invokes the entry point -- true about spelling, false about the control.
    """
    return token.replace("_", "-").lower()


def leg_tokens(leg: str, body: str, seen: set[str] | None = None) -> set[str]:
    """Distinctive tokens a leg runs, expanded through sub-targets ONLY when it runs nothing itself.

    Tokens are the things that would appear in a CI step: script paths and tool names, extracted
    from the Makefile recipe and never listed here -- a hand-kept map of leg to tool is the shape
    this check exists to remove.

    A leg with its own recipe is judged on THAT recipe. Descending into prerequisites regardless
    would let `deps: install` be scored green because CI runs something in `install`, which is a
    caller for the prerequisite and not for the gate.
    """
    seen = set() if seen is None else seen
    if leg in seen:
        return set()
    seen.add(leg)

    # The target line may carry a `## help` comment; skip it, then take the recipe block. The block
    # includes UNINDENTED `#` comment lines, because a target may carry a paragraph of rationale
    # between its target line and its first command -- stopping at the first such line read a leg
    # as running nothing at all.
    rule = re.search(rf"^{re.escape(leg)}:[ \t]*([^\n#]*)(?:#[^\n]*)?\n((?:[ \t].*\n|#.*\n|\n)*)",
                     body, re.M)
    if not rule:
        return set()
    prereqs, recipe = rule.group(1).split(), rule.group(2)

    # TOKENS must not come from prose: a tool named only in a comment would certify a leg that
    # never runs it. Comment lines are dropped before extraction.
    code = "\n".join(ln for ln in recipe.splitlines() if not ln.strip().startswith("#"))
    # `.sh` as well as `.py`: a leg implemented in shell must produce tokens too, or the check cannot
    # see half the surface it grades.
    tokens = set(re.findall(r"(?:scripts|conformance)/[\w.-]+\.(?:py|sh)", code))
    tokens |= set(re.findall(r"\b(gitleaks|pip_audit|pip-audit|ruff|mypy|pytest|black)\b", code))
    if tokens:
        return tokens
    for prereq in prereqs:
        tokens |= leg_tokens(prereq, body, seen)
    return tokens


def leg_tokens_by_subtarget(leg: str, body: str) -> dict:
    """{sub-target: its tokens} for a leg that runs nothing itself.

    A leg with no recipe of its own expands into its prerequisites. Keeping each token attributed
    to the sub-target it came from lets a workflow that calls the sub-target BY NAME (`make closes`)
    count as the caller of that sub-target's tokens -- the better caller, because it goes through
    the documented command.
    """
    rule = re.search(rf"^{re.escape(leg)}:[ \t]*([^\n#]*)(?:#[^\n]*)?\n((?:[ \t].*\n|#.*\n|\n)*)",
                     body, re.M)
    if not rule:
        return {}
    prereqs = rule.group(1).split()
    return {pr: leg_tokens(pr, body) for pr in prereqs}


def scope_note() -> str:
    """Which workflows this run grades. In the distribution package they are the TEMPLATE a
    project receives; in an installation they are the project's own."""
    return ("the package template a project receives"
            if (PKG / ".gp-distribution").is_file() else "this repository's workflows")


def caller_liveness() -> list[str]:
    """Is every leg of `make gate` reachable from a job CI actually runs? Returns failure lines."""
    workflows = PKG / ".github" / "workflows"
    if not workflows.is_dir():
        return ["caller-liveness: no .github/workflows -- cannot establish that any gate has a caller"]

    # `issue-agent.yml` runs only when an issue is labelled, and it runs an agent, not the gate: a
    # leg certified live because its token appears THERE is certified by a caller that never calls.
    wf_files = [q for q in sorted(workflows.glob("*.yml")) if q.name != "issue-agent.yml"]

    # Comment lines are stripped from the workflow text as well as from the Makefile recipe: a
    # `make check` mentioned in a YAML comment would otherwise vouch for every token of that leg.
    def _decomment(text: str) -> str:
        out = []
        for ln in text.splitlines():
            stripped = ln.lstrip()
            if stripped.startswith("#"):
                continue
            # A trailing `#` inside a quoted YAML scalar is not a comment; only strip one that
            # follows whitespace and sits outside quotes, which is YAML's own rule.
            if " #" in ln and ln.count('"') % 2 == 0 and ln.count("'") % 2 == 0:
                ln = ln.split(" #", 1)[0]
            out.append(ln)
        return "\n".join(out)

    ci = _decomment("\n".join(q.read_text(encoding="utf-8") for q in wf_files))
    named = [(q, required_job(q.read_text(encoding="utf-8"))) for q in wf_files]
    named = [(q, j) for q, j in named if j]
    if not named:
        return [f"caller-liveness: no workflow runs `{REQUIRED_MARKER}` -- the one unconditional "
                f"check this package claims does not exist in any executing workflow"]
    # The required job must carry no `if:` and no `continue-on-error:`. GitHub reports a SKIPPED
    # required job as SUCCESS, so a required job that can be skipped is the whole claim failing
    # silently.
    for q, job in named:
        body = q.read_text(encoding="utf-8")
        blk = re.search(rf"^  {re.escape(job)}:\n((?:    .*\n|\n)*)", body, re.M)
        if not blk:
            continue
        head = blk.group(1).split("    steps:")[0]
        for key in ("if:", "continue-on-error:"):
            if re.search(rf"^    {re.escape(key)}", head, re.M):
                return [f"caller-liveness: the required job `{job}` carries `{key}` in {q.name} -- "
                        f"a job that can be skipped, or that fails without failing the build, is "
                        f"not unconditional, and GitHub reports a skipped required job as SUCCESS"]

    body = (PKG / "Makefile").read_text(encoding="utf-8")
    legs = gate_legs()
    if not legs:
        return ["caller-liveness: `gate:` has no prerequisites in the Makefile -- the canonical "
                "gate is empty, which is a vacuous pass by construction"]

    problems = []
    ci_norm = norm(ci)
    for leg in legs:
        tokens = leg_tokens(leg, body)
        if not tokens:
            problems.append(f"caller-liveness: `make {leg}` runs nothing this check can identify -- "
                            f"it cannot be shown to have a CI caller")
            continue
        # A workflow may call the leg by NAME (`make closes`) rather than by the script inside it.
        # That is a caller -- and a better one, because it goes through the documented command.
        if re.search(rf"\bmake\s+{re.escape(leg)}\b", ci):
            continue
        # EVERY token must be present, not any one of them: with `any()`, one tool vouched for all
        # of its siblings, and deleting four CI steps still reported no finding.
        missing = [tok for tok in sorted(tokens) if norm(tok) not in ci_norm]
        # A token belonging to a sub-target the workflow calls BY NAME is called.
        if missing:
            by_sub = leg_tokens_by_subtarget(leg, body)
            called = {sub for sub in by_sub if re.search(rf"\bmake\s+{re.escape(sub)}\b", ci)}
            covered = set().union(*(by_sub[sub] for sub in called)) if called else set()
            missing = [tok for tok in missing if tok not in covered]
        if missing:
            problems.append(f"caller-liveness: `make {leg}` is a leg of `make gate` and nothing in "
                            f"the executing workflows runs: {', '.join(missing)}")
    return problems


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")    # a console that cannot show a character gets `?`
    tests = discover_tests()
    if not tests:
        print("conformance FAIL: no test-*.py discovered in this directory. An empty derived set is "
              "a failure, never a vacuous pass -- there is nothing here to trust.")
        return 1

    fails = []
    for script, why in tests:
        if why.startswith("!!"):
            print(f"  [FAIL      ] {script:26s} {why}")
            fails.append(script)
            continue
        path = HERE / script
        result = subprocess.run([PY, str(path)], capture_output=True, encoding="utf-8",
                                errors="replace", env=CHILD_ENV)
        tail = (result.stdout.strip().splitlines() or ["(no output)"])[-1]
        # Named verdicts, because did-not-run and ran-and-failed are different facts:
        # 0 PASS · 1 FAIL · 2 NOT-EVALUABLE. NOT-EVALUABLE is printed loudly and does not fail the
        # suite -- the test could not evaluate here and says so (for example, no git history to
        # attest). Any other exit is FAIL: an unknown exit is not a verdict.
        verdict = {0: "PASS", 1: "FAIL", 2: "NOT-EVALUABLE"}.get(result.returncode, "FAIL")
        print(f"  [{verdict:10}] {script:26s} {tail}  (exit {result.returncode})")
        if verdict == "FAIL":
            fails.append(script)
            for line in result.stdout.strip().splitlines()[:-1]:
                print(f"         {line}")

    liveness = caller_liveness()
    for line in liveness:
        print(f"  [FAIL      ] {line}")

    total = len(fails) + len(liveness)
    print(f"conformance {'FAIL' if total else 'PASS'}: {len(tests)} test(s) derived from "
          f"{HERE.name}/, {len(fails)} failing, {len(liveness)} caller-liveness finding(s) "
          f"[graded against {scope_note()}]")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
