"""The v7.1 upgrade review's M1: `check_records.py --self-test` calls `version_rule()` and
`session_numbers()` directly, so replacing either call in `main()` with `[]` left every gate green
(mutant Mu8). These tests run `main()` on a tree whose brief and marker disagree, and whose process
log uses one session number twice, and read V1 and S1 from what it prints.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BRIEF = "---\nrecord_type: brief\nid: brief-probe\nstatus: draft\nprocess_version: {version}\ndate: 2026-10-15\n---\n# Brief\n"
LOG = "# Process Log\n\n## S1 — first\n\nx\n\n## S{second} — second\n\ny\n"


def _run(tmp_path: pathlib.Path, *, version: str, second: int) -> str:
    (tmp_path / ".gp").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / ".gp" / "installed").write_text("gp_version: v7.1\n", encoding="utf-8")
    (tmp_path / "docs" / "project-brief.md").write_text(BRIEF.format(version=version), encoding="utf-8")
    (tmp_path / "docs" / "process-log.md").write_text(LOG.format(second=second), encoding="utf-8")
    done = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts" / "check_records.py"), "--root",
                           str(tmp_path)], capture_output=True, text=True, encoding="utf-8", check=False)
    return done.stdout + done.stderr


def test_main_reports_a_brief_whose_version_is_not_the_installed_one(tmp_path: pathlib.Path) -> None:
    out = _run(tmp_path, version="v6.6", second=2)
    assert "[V1]" in out and "`v6.6`" in out
    assert "[S1]" not in out


def test_main_reports_a_session_number_used_twice(tmp_path: pathlib.Path) -> None:
    out = _run(tmp_path, version="v7.1", second=1)
    assert "[S1]" in out
    assert "[V1]" not in out
