#!/usr/bin/env python3
"""Run every conformance test and report each by name.

V4C-80. `--self-test` calls rule functions directly; it proved `M1`/`M2` worked while they could not
fire through any shipped command. These tests go the other way: they exercise the DOCUMENTED surface --
the Makefile, the workflows, the hook config, the record globs -- and assert the claims match the code.

Every test here must be reachable from `make gate`, or it is a control with no caller, which this
pipeline has now shipped four separate times.

v5.2, condition 16-8 (Increment 16), TWO changes, both from candidate G:

  1. THE SUITE IS DERIVED, NOT ENUMERATED. This file used to carry a hand-kept `TESTS` list sitting
     beside the directory it described. The council's unanimous point: declaring a hand-kept list
     "sufficient" would commit rule A -- `V5C-110`, derive don't enumerate -- inside the very registry
     adopting it. The suite is now `test-*.py` in this directory, and each test's own docstring is its
     description. Add a file and it runs; there is no second place to remember.

  2. CALLER-LIVENESS, the level-up check. Every leg of `make gate` must be transitively reachable
     from CI's one unconditional required job. `test-hook-claims.py` asks whether the docs' claims
     reach `make gate`; nothing asked whether `make gate` reaches a job that actually runs on a pull
     request. The field precedent is `issue-agent.yml`: 114 runs, 0 executions -- a caller that never
     calls. A gate whose only caller is a human who already knows its name is the founding defect of
     this lineage, and it has now been shipped at four different altitudes.

Fail-closed (Security seat): a derived set that comes back EMPTY, or a check that cannot parse its
input, is a FAILURE. A vacuous pass is the shape of every defect in this file's history.

Exit: 0 all pass · 1 any fail.
"""
import ast
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent

# v5.3, 18-B/18-C (Increment 18). This was a hand-kept job NAME -- `install-and-governance` -- and
# scoping the check to the EXECUTING workflows immediately proved why that is the wrong shape: GP's
# own root workflow calls its job `governance-contract`, while the package TEMPLATE calls it
# `install-and-governance`. One literal, two trees, and the check knew only one of them. `V5C-110`,
# in the file that enforces caller-liveness.
#
# Derived instead: the required job is the one that runs the GOVERNANCE VALIDATOR. That is a fact
# about what the job does, not about what someone named it, and it survives a rename.
REQUIRED_MARKER = "check_records.py"


def required_job(body: str) -> str | None:
    """The job that runs the governance validator, by what it does rather than what it is called."""
    for m in re.finditer(r"^  ([a-z][\w-]*):\n((?:    .*\n|\n)*)", body, re.M):
        if REQUIRED_MARKER in m.group(2):
            return m.group(1)
    return None

# The dev dependencies -- PyYAML among them -- live in `.venv`, not in the system interpreter. Running
# `python3 conformance/run-all.py` with the system python made `test-ci-yaml` report CANNOT RUN, which
# is the correct refusal and the wrong interpreter. Prefer the venv when it exists.
PY = str(PKG / ".venv" / "bin" / "python")
if not pathlib.Path(PY).exists():
    PY = sys.executable


def discover_tests() -> list[tuple[str, str]]:
    """Derive the suite from the directory; a test's docstring is its description.

    A file that cannot be parsed, or that carries no docstring, is reported and FAILS. It is not
    skipped: silence is how a leg leaves a gate unnoticed, which is the whole subject of this file.
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

    Without this the check reports a gate as having no CI caller because the Makefile invokes the
    module and the workflow invokes the entry point -- a true statement about spelling and a false
    one about the control, which is the confusion this whole file exists to stop making.
    """
    return token.replace("_", "-").lower()


def leg_tokens(leg: str, body: str, seen: set[str] | None = None) -> set[str]:
    """Distinctive tokens a leg runs, expanded through sub-targets ONLY when it runs nothing itself.

    Tokens are the things that would appear in a CI step: script paths and tool names, extracted
    from the Makefile recipe and never listed here -- a hand-kept map of leg to tool is the exact
    shape this condition exists to remove.

    A leg with its own recipe is judged on THAT recipe. Descending into prerequisites regardless
    would let `deps: install` be scored green because CI runs something in `install`, which is a
    caller for the prerequisite and not for the gate.
    """
    seen = set() if seen is None else seen
    if leg in seen:
        return set()
    seen.add(leg)

    # The target line may carry a `## help` comment; skip it, then take the recipe block. The block
    # includes UNINDENTED `#` comment lines: several targets here carry a paragraph of rationale
    # between the target line and its first tab-indented command, and stopping at the first such
    # line read `falsify` as running nothing at all.
    rule = re.search(rf"^{re.escape(leg)}:[ \t]*([^\n#]*)(?:#[^\n]*)?\n((?:[ \t].*\n|#.*\n|\n)*)",
                     body, re.M)
    if not rule:
        return set()
    prereqs, recipe = rule.group(1).split(), rule.group(2)

    # v5.3, 18-B (Increment 18). The recipe block deliberately includes unindented `#` comment
    # lines, because several targets carry a paragraph of rationale before their first command.
    # But TOKENS must not come from prose: measured, `typecheck -> ['gitleaks','mypy','pip-audit']`
    # while `make typecheck` runs mypy alone -- the other two bled in from a v4.3 REPAIR comment.
    # A leg was being certified live by a tool named in a comment.
    code = "\n".join(ln for ln in recipe.splitlines() if not ln.strip().startswith("#"))
    # TB-101 (Increment 19, 18-L). This pattern read `\.py` only, so a leg implemented in SHELL
    # produced zero tokens and was reported as "runs nothing this check can identify" -- on the
    # first gate leg GP added that is a shell script, although GP ships six of them and condition
    # 15-12 says in as many words that "GP's own control surface IS shell". The check could not see
    # half the surface it grades, which is TB-089's family: the declared subject and the actual
    # subject were different sets.
    tokens = set(re.findall(r"(?:scripts|conformance)/[\w.-]+\.(?:py|sh)", code))
    tokens |= set(re.findall(r"\b(gitleaks|pip_audit|pip-audit|ruff|mypy|pytest|black)\b", code))
    if tokens:
        return tokens
    for prereq in prereqs:
        tokens |= leg_tokens(prereq, body, seen)
    return tokens


def leg_tokens_by_subtarget(leg: str, body: str) -> dict:
    """{sub-target: its tokens} for a leg that runs nothing itself.

    B8(b), Increment 19. A leg with no recipe of its own expands into its prerequisites, and the
    expansion flattened them -- so a sub-target CI invokes by name (`make harvest-context-check`,
    which `ci.yml` has run since Increment 18) could not satisfy its own token, because the
    `make <leg>` short-circuit only ever tested the leg being graded. Keeping the sub-target
    attribution lets a documented `make` call count for the thing it actually calls, which is the
    better caller anyway -- 18-B(iv) says so in as many words.
    """
    rule = re.search(rf"^{re.escape(leg)}:[ \t]*([^\n#]*)(?:#[^\n]*)?\n((?:[ \t].*\n|#.*\n|\n)*)",
                     body, re.M)
    if not rule:
        return {}
    prereqs = rule.group(1).split()
    return {pr: leg_tokens(pr, body) for pr in prereqs}


def caller_liveness() -> list[str]:
    """Is every leg of `make gate` reachable from a job CI actually runs? Returns failure lines."""
    workflows = PKG / ".github" / "workflows"
    if not workflows.is_dir():
        return ["caller-liveness: no .github/workflows -- cannot establish that any gate has a caller"]

    # 18-B(ii), and the chair got this wrong once before writing it down. The DevOps seat's finding
    # is right: in the DISTRIBUTION these workflows are TEMPLATES GitHub never executes, so the
    # check adopted to prove controls have callers is, about GP itself, reading a file with no
    # caller. The first repair pointed it at the repository root instead -- and that was WRONG,
    # because the root workflow does not run `make gate`; it tests the package. Two different
    # questions:
    #     template mode      does the ci.yml a PROJECT receives call every leg of `make gate`?
    #     distribution mode  does GP's own CI exercise the package?
    # Only the first is this check's subject. So it keeps reading the template -- and now SAYS SO,
    # which is the scope declaration the Security and Quality seats asked for on every headline.
    # Pointing it at a tree that answers a different question would have been a second wrong answer
    # wearing the first one's repair.
    scope = ("the package template a project receives"
             if (PKG / ".gp-distribution").is_file() else "this repository's workflows")
    # 18-B(iii). `issue-agent.yml` is the archetype this file's docstring names: 114 runs, 0
    # executions. A leg certified live because its token appears THERE is certified by the canonical
    # example of a caller that never calls.
    wf_files = [q for q in sorted(workflows.glob("*.yml")) if q.name != "issue-agent.yml"]
    # B8, Increment 19 council (DevOps seat) -- the finding of the sitting.
    #
    # 18-B(ii) stripped `#` comment lines from the MAKEFILE recipe, because a tool named in a
    # comment was certifying a leg. Nothing stripped them from the WORKFLOW text, and the
    # short-circuit below matches `make <leg>` anywhere in the concatenated YAML. Two comment
    # lines mention `make check` in prose:
    #
    #     ci.yml:116                    "...is a leg of `make check` and had no..."
    #     governance-contract.yml:45    "`make check-templates`" -- a control DELETED at the v5 screen
    #
    # Either one alone vouched for all six tokens of the `check` leg. The same defect, the same
    # function, one increment after 18-B fixed the other half of it.
    #
    # And it was masking a live finding *created by this increment's own repair*: TB-101 taught
    # the token extractor to see `.sh`, which made `scripts/shell_dialect_check.sh` visible for
    # the first time -- and `grep -rn "shell_dialect" .github/ .pre-commit-config.yaml
    # .claude/settings.json` returned ZERO. Condition 15-12's gate, adopted at Increment 18, had
    # no caller in the template. The repair exposed it, this line swallowed it, the suite printed
    # `0 caller-liveness finding(s)`, and the chair read that as the repair closing.
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
    # 18-C. The claim four lines above -- "carries no `if:` and no `continue-on-error`" -- was
    # enforced by nothing: `REQUIRED_JOB not in ci` is a substring test over concatenated YAML.
    # The DevOps seat added both keys to the required job and the suite stayed at 10/10 PASS.
    # GitHub reports a SKIPPED required job as SUCCESS, which is this lineage's founding defect,
    # so a required job that can be skipped is the whole claim failing silently.
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
    for leg in legs:
        tokens = leg_tokens(leg, body)
        if not tokens:
            problems.append(f"caller-liveness: `make {leg}` runs nothing this check can identify -- "
                            f"it cannot be shown to have a CI caller")
            continue
        # 18-B(iv). This was `any()`: one matching token certified every sibling. `check` expands
        # to seven tokens, so `ruff` vouched for pytest, mypy, the governance validator and the
        # harvest-context check. Four CI steps were deleted -- including the skip budget adopted
        # four days earlier -- and the suite still reported 0 findings.
        ci_norm = norm(ci)
        # A workflow may call the leg by NAME (`make harvest-context-check`) rather than by the
        # script inside it. That is a caller -- and a better one, because it goes through the
        # documented command. Tightening `any()` to `all()` surfaced this immediately: a leg wired
        # into CI as a make target was reported as having no caller at all.
        if re.search(rf"\bmake\s+{re.escape(leg)}\b", ci):
            continue
        missing = [tok for tok in sorted(tokens) if norm(tok) not in ci_norm]
        # B8(b): a token belonging to a sub-target the workflow calls BY NAME is called.
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
        result = subprocess.run([PY, str(path)], capture_output=True, text=True)
        tail = (result.stdout.strip().splitlines() or ["(no output)"])[-1]
        # v5.1 -- the F-EXIT lesson applied to GP's own runner (first half of condition 15-8). The
        # field harness filed a genuine lint FAILURE as a SKIP because both used exit 2. This runner
        # was binary: exit 2 ("CANNOT RUN: no .git / no PyYAML") filed as FAIL, indistinguishable
        # from a finding -- so `test-commit-identity` permanently failed the DISTRIBUTION package,
        # which by construction has no history to attest. Named verdicts now: 0 PASS · 1 FAIL ·
        # 2 NOT-EVALUABLE (printed loudly, does not fail the suite -- the thing it cannot check is
        # guarded elsewhere: install-check M5 fails a project with no .git, and falsify proves the
        # control fires in a synthetic repo). Any other exit is FAIL: an unknown exit is not a verdict.
        verdict = {0: "PASS", 1: "FAIL", 2: "NOT-EVALUABLE"}.get(result.returncode, "FAIL")
        print(f"  [{verdict:10}] {script:26s} {tail}  (exit {result.returncode})")
        if verdict == "FAIL":
            fails.append(script)
            for line in result.stdout.strip().splitlines()[:-1]:
                print(f"         {line}")

    liveness = caller_liveness()
    _scope_note = ("the package template a project receives"
                   if (PKG / ".gp-distribution").is_file() else "this repository's workflows")
    for line in liveness:
        print(f"  [FAIL      ] {line}")

    total = len(fails) + len(liveness)
    print(f"conformance {'FAIL' if total else 'PASS'}: {len(tests)} test(s) derived from "
          f"{HERE.name}/, {len(fails)} failing, {len(liveness)} caller-liveness finding(s) "
          f"[graded against {_scope_note}]")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
