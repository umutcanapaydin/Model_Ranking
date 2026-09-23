#!/usr/bin/env python3
"""`make check-fast` runs every leg of `make check`, each in exactly one leg.

WHY. The post-edit hook runs `make check-fast`: `make check`'s legs side by side instead of one
after another. `make check` stays the merge gate, so a gate that never joined a leg would not be
lost at the merge -- it would be lost on every edit before it, each one reported GREEN without it.
A gate in two legs runs twice at the same time against one tree.

What this compares: the prerequisites of `check:` as make itself reads them (`make -pq`: the
Makefile and `stack.mk`, which it includes) against `scripts/check_fast.py --plan`, which prints
`leg: target target...` per line and runs nothing. Every prerequisite must appear exactly once.
Asking make, not reading the Makefile's `check:` line: a prerequisite that `stack.mk` adds is run by
`make check`, and the Makefile's text never names it.
A prerequisite that `check-fast` runs in another form (`CHECK_FAST_FORMS`, e.g. a parallel test
target) is printed `target=form`, and counts as `target`: the leg runs the form in its place, so
the prerequisite is covered under its own name. A pair with an empty side is a finding.
A plan target that `check:` does not name is printed, not failed: it makes the edit check
stricter than the merge gate, never weaker. And the `check-fast` target must exist and invoke the
script, because that is the command the hook types.

FAILS CLOSED: no prerequisites for `check:`, a missing script, a plan that exits non-zero or prints
no leg is a FAILURE. Without `make` neither side can be read (the plan asks make for the check-fast
settings): NOT-EVALUABLE, after the checks that need only the Makefile's text.

Exit: 0 every prerequisite in exactly one leg - 1 findings - 2 not evaluable here (no `make`).
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool                                  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = "scripts/check_fast.py"
LEG = re.compile(r"^\s*([A-Za-z0-9_.-]+):[ \t]*(.*?)\s*$")


def target_block(mk: str, name: str) -> str | None:
    """The target line and recipe of `name`, or None when the Makefile has no such target."""
    m = re.search(rf"^{re.escape(name)}:(?!=)[^\n]*\n((?:[ \t].*\n|#.*\n)*)", mk, re.M)
    return m.group(0) if m else None


def check_prerequisites() -> list[str]:
    """`check:`'s prerequisites from make's own database (`make -pq` runs no recipe), `stack.mk`
    included, order-only ones after `|` left out."""
    r = subprocess.run(["make", "--no-print-directory", "-pq"], cwd=ROOT, capture_output=True,
                       encoding="utf-8", errors="replace", timeout=120)
    found = re.search(r"^check:(?![:=])[ \t]*([^\n#]*)", r.stdout, re.M)
    return found.group(1).split("|")[0].split() if found else []


def main() -> int:
    mk = (ROOT / "Makefile").read_text(encoding="utf-8")
    bad = []
    block = target_block(mk, "check-fast")
    if block is None:
        bad.append("the Makefile has no `check-fast` target, and the post-edit hook runs "
                   "`make check-fast` after every edit")
    elif SCRIPT not in "\n".join(ln for ln in block.splitlines()[1:]
                                 if not ln.strip().startswith("#")):
        bad.append(f"`make check-fast` does not invoke `{SCRIPT}` -- the plan graded here is not "
                   "what the hook runs")
    no_make = missing_tool("make", "read `check:` as make does, or the check-fast settings, so "
                                   "the plan is not graded here")
    prereqs = [] if no_make else check_prerequisites()
    if not no_make and not prereqs:
        print("test-check-fast FAIL: make reads no prerequisites for `check:` -- there is nothing "
              "to compare the plan with, and an empty check passes everything")
        return 1
    if not (ROOT / SCRIPT).is_file():
        bad.append(f"`{SCRIPT}` is missing -- `make check-fast` has nothing to run")
    elif not no_make:
        r = subprocess.run([sys.executable, str(ROOT / SCRIPT), "--plan"], cwd=ROOT,
                           capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        legs = [(m.group(1), m.group(2).split()) for m in map(LEG.match, r.stdout.splitlines()) if m]
        if r.returncode != 0 or not legs:
            tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or ["(no output)"]
            bad.append(f"`{SCRIPT} --plan` exited {r.returncode} with {len(legs)} leg(s) "
                       f"(`{tail[0][:100]}`) -- a plan nobody can read cannot be shown to cover "
                       "`check:`")
        else:
            where: dict[str, list[str]] = {}
            forms: list[str] = []
            for leg, targets in legs:
                for t in targets:
                    name, eq, form = t.partition("=")
                    if eq and not (name and form):
                        bad.append(f"leg `{leg}` of the plan prints `{t}`, which is not "
                                   "target=form -- nobody can tell which `check:` gate it runs")
                        continue
                    if eq:
                        forms.append(t)
                    where.setdefault(name, []).append(leg)
            for t in prereqs:
                if t not in where:
                    bad.append(f"`{t}` is a prerequisite of `check:` and in no leg of "
                               f"`{SCRIPT} --plan` -- every edit goes green without it")
                elif len(where[t]) > 1:
                    bad.append(f"`{t}` is in {len(where[t])} legs of the plan "
                               f"({', '.join(where[t])}) -- it runs twice, at the same time, "
                               "against one tree")
            extra = sorted(set(where) - set(prereqs))
    for b in bad:
        print(f"  FAIL {b}")
    if bad:
        print(f"test-check-fast FAIL: {len(prereqs)} `check:` prerequisite(s), {len(bad)} finding(s)")
        return 1
    if no_make:
        print(f"  NOT-EVALUABLE {no_make}")
        print("test-check-fast NOT-EVALUABLE: the `check-fast` target invokes the script; the plan "
              "was not graded here")
        return 2
    more = f"; also runs {', '.join(extra)}, which `check:` does not name" if extra else ""
    more += f"; in another form: {', '.join(forms)}" if forms else ""
    print(f"test-check-fast PASS: {len(prereqs)} `check:` prerequisite(s), each in exactly one of "
          f"{len(legs)} leg(s) of `{SCRIPT} --plan`{more}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
