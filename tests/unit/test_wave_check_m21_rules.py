"""M21-W4 (D-192): the close checks read the history, and the decision log pairs its pointers.

- #200: `make check-records` refuses an ADR whose Amends names an ADR that carries no Amended-by line
  naming it back.
- #183: the HIGH rule reads the files the close's commit range changed, not only the footprint.
- #201: an ADR a wave adds first appears in a commit that changes no code, or its plan names it.
- #203: the process log has a heading dated inside the wave's commit range.
- #202: row 9's skipped gates, and a session started outside the repository, each have a ledger row.

The history rules hold closes dated from 2026-10-10. Where there is no history (no git, or a shallow
clone, as CI's test job checks out), they say SKIPPED; where the history is there and the range cannot be
read, the close fails.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]

GLOBS = """
## 3. Risk tiers and security globs

- **Security globs.** A diff touching any of these makes a wave HIGH:
  - `src/app/adapter/main.py`
"""


def _module(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- #200 -----------------------------------------------------------------------------------------


def _decisions(root: Path, text: str) -> Path:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "decisions.md").write_text(text, encoding="utf-8")
    return root


AMENDED = """# Decisions

## D-1 — The first

**Status:** accepted · **Date:** 2026-09-01

Body.
{pointer}
## D-2 — The second

**Status:** accepted · **Date:** 2026-09-02 · **Amends** D-1 clause 2; **applies** D-3 · from #9.

Body.

## D-3 — The third

**Status:** proposed · **Date:** 2026-09-03 · **Would amend** D-2 · from #10.
"""


def test_an_amends_with_no_pointer_back_is_refused(tmp_path: Path) -> None:
    """#200: D-180 and D-181 amended five ADRs and none carried a pointer until a closure added them by
    hand. `**Amends**` and `**Would amend**` each need an `**Amended by` line under the ADR they name."""
    check = _module("check_records")
    root = _decisions(tmp_path, AMENDED.format(pointer=""))
    found = [f.msg for f in check.adr_pointer_findings(root)]
    assert any("D-2" in m and "D-1" in m for m in found), found
    assert any("D-3" in m and "D-2" in m for m in found), found
    assert not any("D-3" in m and "D-2 clause" in m for m in found), "`**applies**` is no amendment"


def test_an_amends_with_its_pointer_back_passes_and_applies_is_not_read(tmp_path: Path) -> None:
    """Quiet when it should be: the pointer is there; `**applies**` is not an amendment."""
    check = _module("check_records")
    text = AMENDED.format(pointer="\n**Amended by D-2 (2026-09-02)**: clause 2.\n")
    text = text.replace("Body.\n\n## D-3", "Body.\n\n**Amended by D-3 (2026-09-03, proposed)**: all.\n\n## D-3")
    assert [f.msg for f in check.adr_pointer_findings(_decisions(tmp_path, text))] == []


def test_the_decision_log_pairs_every_pointer() -> None:
    """The real log, as it stands."""
    check = _module("check_records")
    assert [f.msg for f in check.adr_pointer_findings(ROOT)] == []


# --- the history rules: a small repository per test ----------------------------------------------


def _git(root: Path, *args: str, date: str = "2026-10-10T12:00:00") -> str:
    env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=env, timeout=30,
                          check=True)
    return done.stdout.strip()


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(root: Path, message: str, date: str, files: dict[str, str]) -> str:
    for rel, text in files.items():
        _write(root, rel, text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message, date=date)
    return _git(root, "rev-parse", "--short", "HEAD")


def _repo(tmp_path: Path, *, plan: str = GLOBS, log: str = "## 2026-10-10 — M30-W1\n\nwork.\n") -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    base = _commit(root, "base", "2026-10-01T12:00:00", {
        "docs/plans/m30-plan.md": f"# M30\n\n### W1 — one\n{plan}",
        "docs/decisions.md": "# Decisions\n\n## D-1 — One\n\nBody.\n",
        "docs/process-log.md": "# Process log\n\n## 2026-10-01 — before\n\nold.\n",
        "src/app/other.py": "x = 1\n"})
    _write(root, "docs/process-log.md", "# Process log\n\n## 2026-10-01 — before\n\nold.\n\n" + log)
    return root, base


def _close_text(base: str, tier: str = "HIGH", date: str = "2026-10-10") -> str:
    return (f"---\nrecord_type: wave\nid: m30-wave-1-close\nstatus: draft\nprocess_version: v6.6\ndate: {date}\n---\n"
            f"| # | Check | Evidence | ✅/WAIVED |\n|---|---|---|---|\n| 1 | Risk tier | `x`: **{tier}** | ✅ |\n\n"
            f"Filled by: lead · Date: {date} · Wave commit range: `{base}...HEAD`\n")


def test_a_med_close_whose_range_changes_a_security_glob_is_refused(tmp_path: Path) -> None:
    """#183: the footprint is typed by the author, and a path left out of it was not read. The range's
    own diff is the authority."""
    check = _module("wave_check")
    root, base = _repo(tmp_path)
    _commit(root, "change the engine", "2026-10-10T13:00:00", {"src/app/adapter/main.py": "x = 2\n"})
    text = _close_text(base, tier="MED")
    problems, skipped = check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md", text, root)
    assert skipped is None
    assert any("src/app/adapter/main.py" in p for p in problems), problems
    assert check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md",
                                  _close_text(base, tier="HIGH"), root)[0] == []


def test_an_adr_first_written_beside_its_code_is_refused(tmp_path: Path) -> None:
    """#201: four of seven M19 ADRs first appeared in a commit that also changed code."""
    check = _module("wave_check")
    root, base = _repo(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00",
            {"docs/decisions.md": "# Decisions\n\n## D-1 — One\n\nBody.\n\n## D-2 — Two\n\nNew.\n",
            "src/app/other.py": "x = 3\n"})
    problems, _ = check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md", _close_text(base), root)
    assert any("D-2" in p for p in problems), problems


def test_an_adr_written_first_or_named_in_the_plan_passes(tmp_path: Path) -> None:
    """Quiet when it should be: the ADR's own docs-only commit came first; or the plan names it."""
    check = _module("wave_check")
    root, base = _repo(tmp_path)
    _commit(root, "the rule", "2026-10-10T13:00:00",
            {"docs/decisions.md": "# Decisions\n\n## D-1 — One\n\nBody.\n\n## D-2 — Two\n\nNew.\n"})
    _commit(root, "the code", "2026-10-10T14:00:00", {"src/app/other.py": "x = 3\n"})
    close = root / "docs" / "plans" / "m30-wave-1-close.md"
    assert check.history_problems(close, _close_text(base), root)[0] == []

    other, start = _repo(tmp_path / "b", plan=GLOBS + "\nD-2 records the rule.\n")
    _commit(other, "rule and code", "2026-10-10T13:00:00",
            {"docs/decisions.md": "# Decisions\n\n## D-1 — One\n\nBody.\n\n## D-2 — Two\n\nNew.\n",
            "src/app/other.py": "x = 3\n"})
    assert check.history_problems(other / "docs" / "plans" / "m30-wave-1-close.md", _close_text(start), other)[0] == []


def test_a_wave_with_no_process_log_entry_in_its_range_is_refused(tmp_path: Path) -> None:
    """#203: M19's five waves wrote no entry until the closure, and a new session started from M18's."""
    check = _module("wave_check")
    root, base = _repo(tmp_path, log="")
    _commit(root, "work", "2026-10-10T13:00:00", {"src/app/other.py": "x = 4\n"})
    problems, _ = check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md", _close_text(base), root)
    assert any("process-log" in p for p in problems), problems


def test_a_process_log_heading_spanning_the_range_passes(tmp_path: Path) -> None:
    """A heading written as a span of days (`2026-10-09/11`) covers each day in it."""
    check = _module("wave_check")
    root, base = _repo(tmp_path, log="## 2026-10-09/11 — M30\n\nwork.\n")
    _commit(root, "work", "2026-10-10T13:00:00", {"src/app/other.py": "x = 5\n"})
    assert check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md", _close_text(base), root)[0] == []


def test_a_range_that_cannot_be_read_fails_closed(tmp_path: Path) -> None:
    """#183: where the history is there, an unreadable range is a failure, never a pass."""
    check = _module("wave_check")
    root, _ = _repo(tmp_path)
    problems, skipped = check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md",
                                               _close_text("no-such-ref"), root)
    assert skipped is None and any("range" in p for p in problems), problems


def test_a_shallow_clone_or_no_history_says_skipped(tmp_path: Path) -> None:
    """CI's test job checks out one commit; there the history rules say SKIPPED, loudly."""
    check = _module("wave_check")
    root, base = _repo(tmp_path)
    _commit(root, "work", "2026-10-10T13:00:00", {"src/app/other.py": "x = 6\n"})
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{root}", str(shallow)], check=True, timeout=30,
                   capture_output=True)
    problems, skipped = check.history_problems(shallow / "docs" / "plans" / "m30-wave-1-close.md",
                                               _close_text(base), shallow)
    assert problems == [] and skipped and "shallow" in skipped
    bare = tmp_path / "none"
    bare.mkdir()
    problems, skipped = check.history_problems(bare / "m30-wave-1-close.md", _close_text(base), bare)
    assert problems == [] and skipped


def test_a_close_dated_before_the_rules_is_not_read_for_history(tmp_path: Path) -> None:
    """GPF-001: a gate does not invalidate a record written before it."""
    check = _module("wave_check")
    root, base = _repo(tmp_path, log="")
    _commit(root, "rule and code", "2026-10-09T13:00:00",
            {"docs/decisions.md": "# Decisions\n\n## D-1 — One\n\nBody.\n\n## D-2 — Two\n\nNew.\n",
            "src/app/adapter/main.py": "x = 7\n"})
    assert check.history_problems(root / "docs" / "plans" / "m30-wave-1-close.md",
                                  _close_text(base, tier="MED", date="2026-10-09"), root) == ([], None)


# --- #202 ----------------------------------------------------------------------------------------


def _row9(skipped: str, extra: str = "") -> str:
    return (f"---\ndate: 2026-10-10\n---\n| 8 | No checkout | None. {extra} (`x`) | ✅ |\n"
            f"| 9 | Ledger | `gates run: make check-fast · gates SKIPPED: {skipped} · outcome: shipped` | ✅ |\n")


def test_a_skipped_gate_with_no_ledger_row_is_refused(tmp_path: Path) -> None:
    """#202: a skip written inside a ✅ row's run line passed, and reached the ledger only at a closure."""
    check = _module("wave_check")
    problems = check.skip_ledger_problems(_row9("make ui-test (no simulator)"), "m30-w1", [])
    assert any("ui-test" in p for p in problems), problems
    rows = [["ui-test", "m30-w1", "skip", "no simulator", "2026-10-10"]]
    assert check.skip_ledger_problems(_row9("make ui-test (no simulator)"), "m30-w1", rows) == []
    assert check.skip_ledger_problems(_row9("none"), "m30-w1", []) == []


def test_a_session_outside_the_repository_needs_its_ledger_row(tmp_path: Path) -> None:
    """#202: every M19 session ran without the hooks, recorded only in each close's prose."""
    check = _module("wave_check")
    text = _row9("none", extra="The session started outside the repository, so its hooks did not load (#142).")
    assert any("repository-hooks" in p for p in check.skip_ledger_problems(text, "m30-w1", []))
    milestone_row = [["repository-hooks", "m30", "skip", "every session", "2026-10-10"]]
    assert check.skip_ledger_problems(text, "m30-w1", milestone_row) == []


def test_a_close_dated_before_the_rule_needs_no_ledger_row(tmp_path: Path) -> None:
    check = _module("wave_check")
    text = _row9("make ui-test").replace("date: 2026-10-10", "date: 2026-10-09")
    assert check.skip_ledger_problems(text, "m30-w1", []) == []


pytestmark = pytest.mark.needs("git")
