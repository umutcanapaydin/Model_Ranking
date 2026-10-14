"""#274 (D-198 clause 3): a backlog wave's decision comes before its code.

D-192 clause 2 (#201) was read only for a milestone wave's close, so a backlog wave, which has none, could
write its ADR in the commit that changed its code (the reading wave's D-196 did). The branch's own range,
from its merge base with `origin/main`, is read the same way when it adds no milestone close."""

from __future__ import annotations

from pathlib import Path

from tests.unit.test_wave_check_m21_rules import _commit, _git, _module

DECISIONS = "# Decisions\n\n## D-1 — One\n\nBody.\n"
WITH_D2 = DECISIONS + "\n## D-2 — Two\n\nNew.\n"


def _branch(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "base", "2026-10-01T12:00:00", {"docs/decisions.md": DECISIONS, "src/app/other.py": "x = 1\n"})
    _git(root, "update-ref", "refs/remotes/origin/main", "main")
    _git(root, "checkout", "-q", "-b", "wave/backlog-x")
    return root


def test_a_backlog_adr_written_beside_its_code_is_refused(tmp_path: Path) -> None:
    root = _branch(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n"})
    problems, skipped = _module("wave_check").branch_adr_problems(root)
    assert skipped is None
    assert any("D-2" in p and "#274" in p for p in problems), problems


def test_a_backlog_adr_written_after_a_code_commit_that_cites_it_is_refused(tmp_path: Path) -> None:
    root = _branch(tmp_path)
    _commit(root, "code under D-2", "2026-10-10T13:00:00", {"src/app/other.py": "x = 2\n"})
    _commit(root, "docs: the rule", "2026-10-10T14:00:00", {"docs/decisions.md": WITH_D2})
    problems, _ = _module("wave_check").branch_adr_problems(root)
    assert any("D-2" in p for p in problems), problems


def test_a_backlog_adr_written_first_passes(tmp_path: Path) -> None:
    root = _branch(tmp_path)
    _commit(root, "docs: the rule", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2})
    _commit(root, "code under D-2", "2026-10-10T14:00:00", {"src/app/other.py": "x = 2\n"})
    assert _module("wave_check").branch_adr_problems(root) == ([], None)


def test_a_range_with_a_milestone_close_is_left_to_the_close(tmp_path: Path) -> None:
    root = _branch(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00",
            {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n", "docs/plans/m30-wave-1-close.md": "close\n"})
    assert _module("wave_check").branch_adr_problems(root) == ([], None)


def test_no_origin_main_says_it_skipped_and_main_itself_reads_nothing(tmp_path: Path) -> None:
    root = _branch(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n"})
    _git(root, "update-ref", "-d", "refs/remotes/origin/main")
    problems, skipped = _module("wave_check").branch_adr_problems(root)
    assert problems == [] and skipped and "origin/main" in skipped, (problems, skipped)
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    assert _module("wave_check").branch_adr_problems(root) == ([], None)


def test_wave_check_all_runs_the_backlog_rule() -> None:
    source = (Path(__file__).resolve().parents[2] / "scripts" / "wave_check_all.py").read_text(encoding="utf-8")  # raw: not Swift
    assert "branch_adr_problems(" in source, "make wave-check-all does not read a backlog wave's decision order"
