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
import concurrent.futures
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(HERE))
from lib_record import pool_jobs  # noqa: E402

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
CHILD_ENV = {**{k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}, "PYTHONIOENCODING": "utf-8"}


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


CI_MARK = re.compile(r"^#[ \t]*ci:[ \t]*(?:job[ \t]+([\w-]+)|none[ \t]+--[ \t]+(\S.{11,}))[ \t]*$", re.M)


def ci_marker(target: str, body: str) -> tuple[str, str] | None:
    """A target's own declaration of its CI caller, read from the comment block under it:

        # ci: job <name>          -- that job in an executing workflow is the caller
        # ci: none -- <reason>    -- nothing in CI can run it, and the reason says why

    A named entry with a written reason, beside the thing it describes -- never a list kept here.
    `job` is verified (the job must exist); `none` must carry a reason of a sentence."""
    rule = re.search(rf"^{re.escape(target)}:[ \t]*([^\n#]*)(?:#[^\n]*)?\n((?:[ \t].*\n|#.*\n|\n)*)",
                     body, re.M)
    m = CI_MARK.search(rule.group(2)) if rule else None
    if not m:
        return None
    return ("job", m.group(1)) if m.group(1) else ("none", m.group(2))


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
        # What is still missing may belong to a target that names its caller (`ci_marker`).
        if missing:
            owners = {leg: leg_tokens(leg, body)} | leg_tokens_by_subtarget(leg, body)
            for target, toks in owners.items():
                mark = ci_marker(target, body)
                if not mark or not (set(missing) & set(toks)):
                    continue
                if mark[0] == "job" and not re.search(rf"(?m)^\s+{re.escape(mark[1])}:\s*$", ci):
                    problems.append(f"caller-liveness: `make {target}` names CI job `{mark[1]}` as "
                                    "its caller, and no executing workflow has that job")
                    continue
                missing = [tok for tok in missing if tok not in toks]
        if missing:
            problems.append(f"caller-liveness: `make {leg}` is a leg of `make gate` and nothing in "
                            f"the executing workflows runs: {', '.join(missing)}")
    return problems


VERBOSE = bool(os.environ.get("DEVFLOW_VERBOSE"))
#: Tests whose verdict depends only on these files (plus the test itself): in an installation, outside CI,
#: a pass is remembered by their content and not run again while none changed (v7.2, the owner's ruling
#: of 2026-10-17 -- they re-proved the pinned Bash guard on every push, about 60 s).
CACHEABLE = {
    # Every file a hook or the guard can reach, and every script a claim may name as its enforcer: a
    # wider key costs one extra run after an edit; a narrower one keeps a pass for a deleted script.
    "test-bash-guard.py": (".claude/hooks/**/*", ".claude/settings.json", "scripts/**/*", "conformance/lib_record.py", ".devflow-stack",
                           "docs/project-brief.md"),
    "test-hook-claims.py": (".claude/hooks/**/*", ".claude/settings.json", "scripts/**/*", ".githooks/*", "Makefile", "stack.mk",
                            ".devflow-stack", "conformance/lib_record.py", "AGENTS.md", "README.md",
                            "permission-matrix.md", "docs/**/*.md", ".agents/**/*.md", ".github/workflows/*.yml"),
}
CACHE_DIR = PKG / "build" / "conformance-cache"
#: How long each test took on its last run here. The pool starts the longest first, a test with no time
#: before them: in name order the tests that wait more than they compute started last and held the leg
#: (v7.3.1, #114). It only schedules; a file that does not read is the name order.
DURATIONS = CACHE_DIR / "durations.json"


def last_durations() -> dict[str, float]:
    try:
        got = json.loads(DURATIONS.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in got.items() if isinstance(k, str) and isinstance(v, (int, float))}
    except Exception:    # noqa: BLE001 -- any file that does not read as numbers: the name order (a 400-digit int, a deep array)
        return {}


def cache_key(script: str) -> str | None:
    """The content of the test and its inputs; None where nothing may be cached (CI, the distribution)."""
    if script not in CACHEABLE or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") \
            or os.environ.get("DEVFLOW_FRESH") or (PKG / ".gp-distribution").is_file():
        return None
    h = hashlib.sha256((HERE / script).read_bytes())
    for pattern in CACHEABLE[script]:
        for f in sorted(PKG.glob(pattern)):
            if f.is_file() and "__pycache__" not in f.parts:
                h.update(str(f.relative_to(PKG)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def cached(script: str) -> str:
    key = cache_key(script)
    entry = CACHE_DIR / script
    if key and entry.is_file() and entry.read_text(encoding="utf-8").strip() == key:
        return f"CACHED {script}: passed on these exact inputs before -- not run again (DEVFLOW_FRESH=1 runs it)"
    return ""


def remember(script: str) -> None:
    if (key := cache_key(script)):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / script).write_text(key + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")    # a console that cannot show a character gets `?`
    tests = discover_tests()
    if not tests:
        print("conformance FAIL: no test-*.py discovered in this directory. An empty derived set is "
              "a failure, never a vacuous pass -- there is nothing here to trust.")
        return 1

    fails = []
    not_evaluable: list[str] = []
    # Each test builds its own throwaway trees, so they run side by side, the longest first; the report
    # keeps the discovery order. DEVFLOW_JOBS=1 runs them one at a time. Each test gets its share of the
    # CPUs as DEVFLOW_SHARE, for the pool it may run itself (lib_record.pool_jobs).
    jobs, share = pool_jobs(8)
    env = {**CHILD_ENV, "DEVFLOW_SHARE": str(share)}
    took: dict[str, float] = {}

    def run(script: str) -> subprocess.CompletedProcess:
        if (hit := cached(script)):
            return subprocess.CompletedProcess([], 0, stdout=hit, stderr="")
        start = time.monotonic()
        result = subprocess.run([PY, str(HERE / script)], capture_output=True, encoding="utf-8",
                                errors="replace", env=env)
        took[script] = round(time.monotonic() - start, 2)
        if result.returncode == 0:
            remember(script)
        return result
    last = last_durations()
    runnable = [script for script, why in tests if not why.startswith("!!")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        results = {script: pool.submit(run, script)
                   for script in sorted(runnable, key=lambda s: -last.get(s, float("inf")))}
    # Written whole, then renamed into place: a run beside this one reads the old file or the new, never half.
    tmp = DURATIONS.with_name(f"{DURATIONS.name}.{os.getpid()}.tmp")
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({s: took.get(s, last.get(s)) for s in runnable if s in took or s in last},
                                  indent=0, sort_keys=True), encoding="utf-8")
        os.replace(tmp, DURATIONS)
    except OSError:
        tmp.unlink(missing_ok=True)    # the next run starts in name order: slower, never wrong
    for script, why in tests:
        if why.startswith("!!"):
            print(f"  [FAIL      ] {script:26s} {why}")
            fails.append(script)
            continue
        result = results[script].result()
        # A test that died prints nothing on stdout: its traceback's last line is the only evidence CI keeps.
        tail = (result.stdout.strip().splitlines() or [f"(no output; stderr: {line})" for line in
                                                         result.stderr.strip().splitlines()[-1:]] or ["(no output)"])[-1]
        # Named verdicts, because did-not-run and ran-and-failed are different facts:
        # 0 PASS · 1 FAIL · 2 NOT-EVALUABLE. NOT-EVALUABLE is printed loudly and does not fail the
        # suite -- the test could not evaluate here and says so (for example, no git history to
        # attest). Any other exit is FAIL: an unknown exit is not a verdict.
        verdict = {0: "PASS", 1: "FAIL", 2: "NOT-EVALUABLE"}.get(result.returncode, "FAIL")
        # A green test is one line in a summary unless DEVFLOW_VERBOSE asks for each (v7.2: a green gate
        # printed 11.6 KB, read three to five times per change).
        if verdict != "PASS" or VERBOSE:
            print(f"  [{verdict:10}] {script:26s} {tail}  (exit {result.returncode})")
        if verdict == "NOT-EVALUABLE":
            not_evaluable.append(script)
        if verdict == "FAIL":
            fails.append(script)
            for line in result.stdout.strip().splitlines()[:-1]:
                print(f"         {line}")
            # A test that died says why on stderr, which was dropped: CI showed `(no output) (exit 1)` and
            # nothing else (two field projects, v7.2). Its last lines go with the verdict.
            err = (result.stderr or "").strip().splitlines()
            if err:
                print("         stderr (last lines):")
                for line in err[-15:]:
                    print(f"         | {line}")

    liveness = caller_liveness()
    for line in liveness:
        print(f"  [FAIL      ] {line}")

    total = len(fails) + len(liveness)
    hits = [s for s in runnable if results[s].result().stdout.startswith("CACHED ")]
    if hits:
        print(f"  cached (inputs unchanged since their last pass; CI and the distribution always run them): "
              f"{', '.join(hits)}")
    if not VERBOSE:
        print(f"  {len(tests) - len(fails) - len(not_evaluable)} test(s) passed; DEVFLOW_VERBOSE=1 lists each")
    print(f"conformance {'FAIL' if total else 'PASS'}: {len(tests)} test(s) derived from "
          f"{HERE.name}/, {len(fails)} failing, {len(liveness)} caller-liveness finding(s) "
          f"[graded against {scope_note()}]")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
