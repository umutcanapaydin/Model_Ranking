"""M18-W5 -- two controls that were prose (#82, #83), now checks.

- #82: `wave-check-all` globbed the close records that exist, so a wave with none was invisible
  (M17-W1 closed with no record and no gate noticed). For a milestone that has closed, every wave its
  plan names must have a close record, be marked dropped in the plan, or carry a `wave-close` row in
  `docs/control-events.csv`. From M18 on (GPF-001: a control does not grade what predates it).
- #83: the template escalates to HIGH a wave whose diff touches input parsing, and neither M17-W2 nor
  W3 was HIGH. `wave-check` refuses a close dated from 2026-10-04 whose footprint touches
  `src/app/clients/` while its risk-tier row is not HIGH.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "docs" / "plans" / "m18-wave-1-close.md"


def _module(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(tmp_path: Path, *, closes: tuple[int, ...], closed: bool = True, ledger: str = "",
          milestone: int = 18, plan_extra: str = "") -> Path:
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / f"m{milestone}-plan.md").write_text(
        f"# M{milestone} plan\n\n### W1 — one\n\n### W2 — two\n{plan_extra}", encoding="utf-8")
    for wave in closes:
        (plans / f"m{milestone}-wave-{wave}-close.md").write_text("a close\n", encoding="utf-8")
    if closed:
        (tmp_path / "docs" / f"closure-report-m{milestone}.md").write_text("closed\n", encoding="utf-8")
    (tmp_path / "docs" / "control-events.csv").write_text(
        "control,wave,kind,reason,date\n" + ledger, encoding="utf-8")
    return tmp_path


def test_a_closed_milestone_with_a_planned_wave_and_no_close_is_refused(tmp_path: Path) -> None:
    """#82: W2 is in the plan, the milestone closed, and W2 has no record."""
    missing = _module("wave_check_all").missing_closes(_tree(tmp_path, closes=(1,)))
    assert len(missing) == 1 and "m18" in missing[0] and "W2" in missing[0], missing


def test_a_wave_dropped_in_the_plan_or_on_the_ledger_needs_no_close(tmp_path: Path) -> None:
    check = _module("wave_check_all")
    assert check.missing_closes(_tree(tmp_path / "a", closes=(1,), plan_extra="\n### W3 — three (dropped)\n")) != []
    assert check.missing_closes(_tree(tmp_path / "b", closes=(1,),
                                      plan_extra="\n### W3 — three (dropped)\n",
                                      ledger="wave-close,m18-w2,skip,merged into W1 (owner),2026-10-04\n")) == []


def test_an_open_milestone_and_one_before_the_control_are_not_graded(tmp_path: Path) -> None:
    check = _module("wave_check_all")
    assert check.missing_closes(_tree(tmp_path / "open", closes=(1,), closed=False)) == []
    assert check.missing_closes(_tree(tmp_path / "old", closes=(1,), milestone=17)) == []


def _record(tmp_path: Path, *, tier: str, touched: str) -> Path:
    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"^date: .*$", "date: 2026-10-04", text, count=1, flags=re.M)
    text = re.sub(r"\(risk: \*\*HIGH\*\*", f"(risk: **{tier}**", text, count=1)
    text = re.sub(r"^Touched:.*$", f"Touched:        {touched}", text, count=1, flags=re.M)
    record = tmp_path / "docs" / "plans" / "m18-wave-1-close.md"
    record.parent.mkdir(parents=True)
    record.write_text(text, encoding="utf-8")
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir()
    for seat in ("review", "tester"):  # the verdicts the record cites, as the real close has them
        name = f"m18-wave-1-{seat}.md"
        verdict = (ROOT / "docs" / "reviews" / name).read_text(encoding="utf-8")
        (reviews / name).write_text(re.sub(r"^date: .*$", "date: 2026-10-04", verdict, count=1, flags=re.M),
                                    encoding="utf-8")
    return record


def _wave_check(record: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "wave_check.py"), str(record)],
                          capture_output=True, text=True, cwd=record.parents[2], timeout=60, check=False)


def test_a_wave_touching_input_parsing_must_be_high(tmp_path: Path) -> None:
    """#83: a close whose footprint names `src/app/clients/` and whose tier row is not HIGH."""
    done = _wave_check(_record(tmp_path, tier="MED", touched="src/app/clients/epoch.py · tests/unit/x.py"))
    assert done.returncode != 0 and "src/app/clients" in done.stdout, done.stdout


def test_a_high_wave_touching_input_parsing_and_a_med_wave_not_touching_it_pass(tmp_path: Path) -> None:
    assert _wave_check(_record(tmp_path / "a", tier="HIGH", touched="src/app/clients/epoch.py")).returncode == 0
    assert _wave_check(_record(tmp_path / "b", tier="MED", touched="src/app/workflows/rank.py")).returncode == 0


def test_a_plan_whose_waves_cannot_be_counted_fails_closed(tmp_path: Path) -> None:
    """W5 review M3: a closed milestone whose plan names its waves in a shape the parser did not read
    reported nothing missing (AGENTS.md §3.5: fail closed)."""
    check = _module("wave_check_all")
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "m19-plan.md").write_text("# M19\n\nNo waves named here.\n", encoding="utf-8")
    (tmp_path / "docs" / "closure-report-m19.md").write_text("closed\n", encoding="utf-8")
    assert check.missing_closes(tmp_path) != []


def test_other_spellings_of_a_wave_heading_are_counted(tmp_path: Path) -> None:
    check = _module("wave_check_all")
    for heading in ("## Wave 2 — two", "### M19-W2 — two"):
        root = tmp_path / heading[:6].strip("# ").replace(" ", "")
        plans = root / "docs" / "plans"
        plans.mkdir(parents=True)
        (plans / "m19-plan.md").write_text(f"# M19\n\n### W1 — one\n\n{heading}\n", encoding="utf-8")
        (plans / "m19-wave-1-close.md").write_text("a close\n", encoding="utf-8")
        (root / "docs" / "closure-report-m19.md").write_text("closed\n", encoding="utf-8")
        assert any("W2" in line for line in check.missing_closes(root)), heading


def test_the_input_parsing_rule_has_no_way_around_it(tmp_path: Path) -> None:
    """W5 review M4: an undated close, a footprint whose fields come in another order, and
    `src/app/clients` without its slash each passed."""
    undated = _record(tmp_path / "a", tier="MED", touched="src/app/clients/epoch.py")
    undated.write_text(re.sub(r"^date: .*\n", "", undated.read_text(encoding="utf-8"), count=1, flags=re.M),
                       encoding="utf-8")
    assert "src/app/clients" in _wave_check(undated).stdout
    slashless = _record(tmp_path / "b", tier="MED", touched="src/app/clients (the epoch parser)")
    assert "src/app/clients" in _wave_check(slashless).stdout
    reordered = _record(tmp_path / "c", tier="MED", touched="src/app/clients/epoch.py")
    text = reordered.read_text(encoding="utf-8")
    touched = re.search(r"^Touched:.*$", text, re.M).group(0)  # type: ignore[union-attr]
    text = text.replace(touched + "\n", "").replace("Hand-kept lists:", touched + "\nHand-kept lists:")
    reordered.write_text(text, encoding="utf-8")
    assert "src/app/clients" in _wave_check(reordered).stdout


def test_only_a_dropped_mark_excuses_a_wave_and_an_unread_heading_is_reported(tmp_path: Path) -> None:
    """W5 second review M9: any heading containing "dropped" was excused ("the dropped-frames fix"),
    and when one heading parsed, a heading it could not read was skipped."""
    check = _module("wave_check_all")
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "m19-plan.md").write_text(
        "# M19\n\n### W1 — one\n\n### W2 — the dropped-frames fix\n\n## Wave Three — three\n", encoding="utf-8")
    (plans / "m19-wave-1-close.md").write_text("a close\n", encoding="utf-8")
    (tmp_path / "docs" / "closure-report-m19.md").write_text("closed\n", encoding="utf-8")
    missing = check.missing_closes(tmp_path)
    assert any("W2" in line for line in missing), missing
    assert any("Wave Three" in line for line in missing), missing


def test_the_tier_is_read_from_the_evidence_not_the_template_wording(tmp_path: Path) -> None:
    """W5 second review M10: row 1's check column says "LOW/MED/HIGH; auto-HIGH", so a MED close that
    kept the template's wording passed the input-parsing rule."""
    record = _record(tmp_path, tier="MED", touched="src/app/clients/epoch.py")
    text = record.read_text(encoding="utf-8")
    text = re.sub(r"^\| 1 \| [^|]*\|", "| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH "
                  "if the diff touches input-parsing) |", text, count=1, flags=re.M)
    record.write_text(text, encoding="utf-8")
    assert "src/app/clients" in _wave_check(record).stdout


def test_wave_check_all_itself_fails_on_a_planned_wave_with_no_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """W5 Tester: the plan's check is that `wave-check-all` FAILS on a planned wave with no close. Every
    test above calls `missing_closes`; with its result dropped from `main()`'s exit, all of them, and
    `make wave-check-all`, passed."""
    check = _module("wave_check_all")
    root = _tree(tmp_path, closes=(1,))
    (root / "docs" / "plans" / "m18-wave-1-close.md").write_text(
        "---\nprocess_version: v6.6\ndate: 2026-10-04\n---\n# W1\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "wave_check.py").write_text("def main(argv):\n    return 0\n", encoding="utf-8")
    monkeypatch.setattr(check, "ROOT", root)
    assert check.main() == 1
    assert "m18 W2 is in the plan and has no close record" in capsys.readouterr().out


def test_the_whole_footprint_is_read_not_its_first_line(tmp_path: Path) -> None:
    """W5 Tester: a real footprint runs over several lines (the M18-W4 close's does). Read up to its
    first newline only, a `src/app/clients` path on the second line passed as MED."""
    record = _record(tmp_path, tier="MED", touched="src/app/workflows/rank.py ·\n                src/app/clients/epoch.py")
    assert "src/app/clients" in _wave_check(record).stdout


def test_a_bold_or_deep_wave_heading_is_reported_when_another_one_parses(tmp_path: Path) -> None:
    """W5 Tester (round 2's M9, second half): `LOOKS_LIKE_A_WAVE` reads `### W2` and `## Wave Three`, but
    not `### **W2** — two` or `##### W2 — two`. With `### W1` parsing beside either, the second wave
    was never counted and nothing was missing."""
    check = _module("wave_check_all")
    for name, heading in (("bold", "### **W2** — two"), ("deep", "##### W2 — two")):
        root = tmp_path / name
        plans = root / "docs" / "plans"
        plans.mkdir(parents=True)
        (plans / "m19-plan.md").write_text(f"# M19\n\n### W1 — one\n\n{heading}\n", encoding="utf-8")
        (plans / "m19-wave-1-close.md").write_text("a close\n", encoding="utf-8")
        (root / "docs" / "closure-report-m19.md").write_text("closed\n", encoding="utf-8")
        assert any("W2" in line for line in check.missing_closes(root)), heading
