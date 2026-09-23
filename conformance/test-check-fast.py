#!/usr/bin/env python3
"""`make check-fast` runs every leg of `make check`, each in exactly one leg.

WHY. The post-edit hook runs `make check-fast`: `make check`'s legs side by side instead of one
after another. `make check` stays the merge gate, so a gate that never joined a leg would not be
lost at the merge -- it would be lost on every edit before it, each one reported GREEN without it.
A gate in two legs runs twice at the same time against one tree.

What this compares: the prerequisites of `check:` in the Makefile (read here, from the same line
`scripts/check_fast.py` derives its legs from) against `scripts/check_fast.py --plan`, which prints
`leg: target target...` per line and runs nothing. Every prerequisite must appear exactly once.
A plan target that `check:` does not name is printed, not failed: it makes the edit check
stricter than the merge gate, never weaker. And the `check-fast` target must exist and invoke the
script, because that is the command the hook types.

FAILS CLOSED: an empty `check:` line, a missing script, a plan that exits non-zero or prints no leg
is a FAILURE.

Exit: 0 every prerequisite in exactly one leg - 1 findings.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = "scripts/check_fast.py"
LEG = re.compile(r"^\s*([A-Za-z0-9_.-]+):[ \t]*(.*?)\s*$")


def target_block(mk: str, name: str) -> str | None:
    """The target line and recipe of `name`, or None when the Makefile has no such target."""
    m = re.search(rf"^{re.escape(name)}:(?!=)[^\n]*\n((?:[ \t].*\n|#.*\n)*)", mk, re.M)
    return m.group(0) if m else None


def main() -> int:
    mk = (ROOT / "Makefile").read_text(encoding="utf-8")
    found = re.search(r"^check:[ \t]*([^\n#]*)", mk, re.M)
    prereqs = found.group(1).split() if found else []
    if not prereqs:
        print("test-check-fast FAIL: `check:` has no prerequisites in the Makefile -- there is "
              "nothing to compare the plan with, and an empty check passes everything")
        return 1
    bad = []
    block = target_block(mk, "check-fast")
    if block is None:
        bad.append("the Makefile has no `check-fast` target, and the post-edit hook runs "
                   "`make check-fast` after every edit")
    elif SCRIPT not in "\n".join(ln for ln in block.splitlines()[1:]
                                 if not ln.strip().startswith("#")):
        bad.append(f"`make check-fast` does not invoke `{SCRIPT}` -- the plan graded here is not "
                   "what the hook runs")
    if not (ROOT / SCRIPT).is_file():
        bad.append(f"`{SCRIPT}` is missing -- `make check-fast` has nothing to run")
    else:
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
            for leg, targets in legs:
                for t in targets:
                    where.setdefault(t, []).append(leg)
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
    more = f"; also runs {', '.join(extra)}, which `check:` does not name" if extra else ""
    print(f"test-check-fast PASS: {len(prereqs)} `check:` prerequisite(s), each in exactly one of "
          f"{len(legs)} leg(s) of `{SCRIPT} --plan`{more}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
