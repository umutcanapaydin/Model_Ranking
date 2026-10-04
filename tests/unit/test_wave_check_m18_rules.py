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
    assert done.returncode != 0 and "src/app/clients/" in done.stdout, done.stdout


def test_a_high_wave_touching_input_parsing_and_a_med_wave_not_touching_it_pass(tmp_path: Path) -> None:
    assert _wave_check(_record(tmp_path / "a", tier="HIGH", touched="src/app/clients/epoch.py")).returncode == 0
    assert _wave_check(_record(tmp_path / "b", tier="MED", touched="src/app/workflows/rank.py")).returncode == 0
