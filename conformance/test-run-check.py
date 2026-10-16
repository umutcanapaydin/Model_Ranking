#!/usr/bin/env python3
"""`make run-check` refuses a run record that is hollow, inconsistent or ended with a wave still running, and accepts a filled one.

WHY (v7.1, the owner's rule of 2026-10-13: an unattended run works every wave of two to five
milestones overnight and stops only for a decision). The run's one record is
`docs/plans/run-<name>.md`; the next session resumes from it and the owner reads it in the morning.
A record nobody grades says `stacked` for a wave that was never closed and `closed` for a milestone
with a wave still queued, so `scripts/run_check.py` grades it and `make closes` runs it on every run
file in the tree. This proves the checker by the input it refuses -- for each reason the negative
fixture declares, not only for being thin -- and by the filled fixture it accepts.

Exit: 0 every case behaves - 1 one does not.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "run_check.py"
GOOD = "conformance/run/run-m901.md"
BAD = "conformance/run/run-m902-broken.md"
# Each reason the negative fixture plants, and the words the refusal must say for it.
REASONS = (
    ("a mode outside the vocabulary", "`Mode:` is `medium`"),
    ("an end reason outside the vocabulary", "`Ended:` is `2026-10-14"),
    ("a ruling no ADR holds", "ruling `D-99999` is not in docs/decisions.md"),  # model_ranking holds a real D-999 (D-199)
    ("a ruling with no owner-ruling line", "ruling `D-100` carries no `**Owner ruling:**` line"),
    ("a closed milestone with no base sha", "is closed and names no `Base` sha"),
    ("a running milestone in an ended run", "the run has ended and milestone `M903` is still running"),
    ("a template placeholder in a line the run owns", "a template placeholder is still in a line the run owns"),
    ("a stacked wave with no close record", "is stacked and its close record"),
    ("a wave status outside the vocabulary", "status `merged` is not one of"),
    ("a milestone whose plan does not exist", "which does not exist"),
    ("a closed milestone with a wave not stacked", "is closed while its wave(s)"),
    ("a stop class that is not an event", "stop class `tired` is not one of"),
    ("a stop that says nothing", "says nothing about what the owner decides"),
    ("a stopped wave with no stop row", "is stopped and Stops has no row for it"),
)


def run(path: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(CHECK), path], cwd=ROOT, capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    bad: list[str] = []
    rc, out = run(GOOD)
    if rc != 0 or "run-check PASS" not in out:
        bad.append(f"the filled fixture {GOOD} must be accepted (exit {rc}):\n{out}")
    rc, out = run(BAD)
    if rc == 0:
        bad.append(f"the broken fixture {BAD} must be refused, and was accepted")
    for why, said in REASONS:
        if said not in out:
            bad.append(f"{BAD} was not refused for {why}: the output never said `{said}` -- a "
                       "refusal for another reason proves nothing about this rule")
    rc, out = run("README.md")
    if rc == 0:
        bad.append("README.md must be refused as a run record, and was accepted")
    rc, out = run("docs/plans/run-nowhere.md")
    if rc == 0:
        bad.append("a missing file must be refused, and was accepted")
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-run-check {'FAIL' if bad else 'PASS'}: {len(REASONS)} declared refusals on {BAD}, "
          f"{GOOD} accepted, README.md and a missing file refused")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
