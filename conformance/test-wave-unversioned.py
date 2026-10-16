#!/usr/bin/env python3
"""A wave close that declares no process_version is history only if it predates the installation.

WHY (v7.1.1; model_ranking's D-161 refuses it locally, and two cases here carry that rule). `scripts/wave_check.py` graded every close
with no `process_version:` line as history -- frontmatter, table, statuses, sign-off -- so a NEW
hand-written close that left the line out skipped the footprint, the review files and the milestone
Tester. History is for records older than DevFlow here: the installation is dated by `installed_on`
in `.gp/installed` (`scripts/write_install_marker.py`), the close by its frontmatter `date:`, else its
sign-off's `Date:`. With no marker (the package itself) nothing changes.

Each case copies the fixture `conformance/wave/m905-wave-1-close.md` into a throwaway tree, writes the
marker the case names, and runs the checker there -- never against this tree's own records.

Exit: 0 every case behaves - 1 one does not.
"""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "wave_check.py"
FIXTURE = ROOT / "conformance" / "wave" / "m905-wave-1-close.md"
REFUSED = "a close written after DevFlow was installed declares process_version"
MARKER = "gp_version: v7.1\ninstalled_on: {}\n"
REVIEW = ("---\nrecord_type: review\nid: m905-wave-1-review\nstatus: draft\nseat: independent\ndate: 2026-08-10\n---\n"
          "# Review: M905 wave 1\n\n**Independent:** yes\n\nPASS\n")


def undated(text: str) -> str:
    text = re.sub(r"(?m)^date:.*\n", "", text, count=1)
    return re.sub(r"Date: `\d{4}-\d{2}-\d{2}`", "Date: `none`", text)


# name, marker text (None: no marker), the close's text from the fixture's, the words the output must
# carry, whether it must pass
CASES = [
    ("no marker: history, as before", None, lambda t: t, "graded as history", True),
    ("installed after the close: history", MARKER.format("2026-09-01"), lambda t: t, "graded as history", True),
    ("installed the day the close is dated: refused", MARKER.format("2026-08-10"), lambda t: t, REFUSED, False),
    ("installed before the close: refused", MARKER.format("2026-08-01"), lambda t: t, REFUSED, False),
    ("the frontmatter date is the close's date, before the sign-off's", MARKER.format("2026-08-05"),
     lambda t: t.replace("date: 2026-08-10", "date: 2026-08-01", 1), "graded as history", True),
    ("no frontmatter date: the sign-off's date is read", MARKER.format("2026-08-05"),
     lambda t: re.sub(r"(?m)^date:.*\n", "", t, count=1), "dated 2026-08-10", False),
    ("undated beside a marker: refused", MARKER.format("2026-09-01"), undated, "is undated", False),
    # model_ranking (D-161): an undated close is refused with or without a marker -- a missing date would
    # skip the rules written since this project adopted DevFlow.
    ("undated with no marker: refused here (D-161)", None, undated, "is undated", False),
    ("a marker with no readable installed_on fails closed", "gp_version: v7.1\n", lambda t: t,
     "fail closed", False),
    ("a versioned close is untouched by the marker", MARKER.format("2026-08-01"),
     lambda t: t.replace("status: ratified\n", "status: ratified\nprocess_version: v4.0\n", 1),
     "wave-check PASS", True),
]


def main() -> int:
    if not FIXTURE.is_file():
        print(f"test-wave-unversioned FAIL: the fixture {FIXTURE.relative_to(ROOT)} is missing")
        return 1
    base = FIXTURE.read_text(encoding="utf-8")
    if re.search(r"(?m)^process_version:", base):
        print("test-wave-unversioned FAIL: the fixture declares a process_version -- it must not")
        return 1
    bad: list[str] = []
    for name, marker, edit, said, passes in CASES:
        with tempfile.TemporaryDirectory() as d:
            tree = pathlib.Path(d)
            close = tree / "docs" / "plans" / FIXTURE.name
            close.parent.mkdir(parents=True)
            close.write_text(edit(base), encoding="utf-8")
            # model_ranking (REQ-REV-001): a cited review must exist and declare its seat, in every era,
            # so the tree holds the review the fixture cites.
            review = tree / "docs" / "reviews" / "m905-wave-1-review.md"
            review.parent.mkdir(parents=True)
            review.write_text(REVIEW, encoding="utf-8")
            if marker is not None:
                (tree / ".gp").mkdir()
                (tree / ".gp" / "installed").write_text(marker, encoding="utf-8")
            r = subprocess.run([sys.executable, str(CHECK), f"docs/plans/{FIXTURE.name}"], cwd=tree,
                               capture_output=True, encoding="utf-8", errors="replace")
            out = r.stdout + r.stderr
        if (r.returncode == 0) != passes or said not in out:
            bad.append(f"{name}: exit {r.returncode}, expected {'0' if passes else 'non-zero'} saying "
                       f"`{said}`:\n    " + "\n    ".join(out.strip().splitlines()[-4:]))
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-wave-unversioned {'FAIL' if bad else 'PASS'}: {len(CASES)} cases of scripts/wave_check.py "
          f"on {FIXTURE.relative_to(ROOT).as_posix()} in throwaway trees -- history before the "
          "installation's `installed_on`, refused on or after it")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
