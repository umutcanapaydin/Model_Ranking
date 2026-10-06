"""M19-W3, #140: the two wave gates read what the plan says, not a narrower copy of it.

- #82's check counted a milestone's waves from its `### W<n>` headings. A wave added by an amendment
  paragraph, or named only in a table, has none, so its missing close was invisible. Any wave the
  plan names must now have its heading, in every plan from M18 on.
- #83's HIGH rule read one path, `src/app/clients`, while the plan lists its own security globs
  (`m19-plan.md` §3). From 2026-10-06 a close whose footprint touches any of its plan's globs must be
  HIGH, and a plan with no glob list fails closed.
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
GLOBS = """
## 3. Risk tiers and security globs

- **Security globs.** A diff touching any of these makes a wave HIGH:
  - `src/app/adapter/main.py`
  - `ios/ModelRanking/Engine/EngineClient.swift`
  - `src/app/clients/**` (input parsing, #83)
  - `.github/workflows/**` and `.claude/settings.json` (the owner's)
"""


def _module(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan(root: Path, text: str, *, milestone: int = 19, closes: tuple[int, ...] = (1, 2),
          closed: bool = True) -> Path:
    plans = root / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / f"m{milestone}-plan.md").write_text(f"# M{milestone}\n\n### W1 — one\n\n### W2 — two\n{text}",
                                                 encoding="utf-8")
    for wave in closes:
        (plans / f"m{milestone}-wave-{wave}-close.md").write_text("a close\n", encoding="utf-8")
    if closed:
        (root / "docs" / f"closure-report-m{milestone}.md").write_text("closed\n", encoding="utf-8")
    (root / "docs" / "control-events.csv").write_text("control,wave,kind,reason,date\n", encoding="utf-8")
    return root


def test_a_wave_an_amendment_adds_without_a_heading_is_refused(tmp_path: Path) -> None:
    """#140, slice 1: M18-W7 was added by an amendment; had it no heading, its missing close was
    invisible. A wave an amendment names must carry a heading, so its close can be required."""
    check = _module("wave_check_all")
    root = _plan(tmp_path, "\n**Amendment (2026-10-06, the owner).** W3 joins the milestone: the backlog.\n")
    problems = check.headless_waves(root)
    assert any("W3" in line and "heading" in line for line in problems), problems


def test_a_wave_a_table_names_without_a_heading_is_refused(tmp_path: Path) -> None:
    """#140: the issue inventory names each wave in its first column (`| W3 | #12 |`)."""
    check = _module("wave_check_all")
    root = _plan(tmp_path, "\n| Wave | Issues |\n|---|---|\n| W1 | #1 |\n| W3 | #12 |\n")
    assert any("W3" in line for line in check.headless_waves(root))


def test_an_open_milestones_plan_is_held_to_it_too(tmp_path: Path) -> None:
    """#140: found while the milestone runs, not at its closure, when the wave is already invisible."""
    check = _module("wave_check_all")
    root = _plan(tmp_path, "\n**Amendment (2026-10-06).** W3 is added.\n", closes=(1,), closed=False)
    assert any("W3" in line for line in check.headless_waves(root))


def test_waves_named_with_their_headings_and_other_milestones_waves_pass(tmp_path: Path) -> None:
    """Quiet when it should be: W2 named in an amendment has its heading; `M17-W5` is another
    milestone's wave; `W-108` is a warning, not a wave."""
    check = _module("wave_check_all")
    root = _plan(tmp_path, "\n**Amendment (2026-10-06).** W2 runs before W1, as M17-W5 did; W-108 stays.\n")
    assert check.headless_waves(root) == []


def _close(root: Path, *, tier: str, touched: str, plan: str | None) -> Path:
    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"^date: .*$", "date: 2026-10-06", text, count=1, flags=re.M)
    text = re.sub(r"\(risk: \*\*HIGH\*\*", f"(risk: **{tier}**", text, count=1)
    text = re.sub(r"^Touched:.*$", f"Touched:        {touched}", text, count=1, flags=re.M)
    record = root / "docs" / "plans" / "m18-wave-1-close.md"
    record.parent.mkdir(parents=True)
    record.write_text(text, encoding="utf-8")
    if plan is not None:
        (root / "docs" / "plans" / "m18-plan.md").write_text(f"# M18\n\n### W1 — one\n{plan}", encoding="utf-8")
    reviews = root / "docs" / "reviews"
    reviews.mkdir()
    for seat in ("review", "tester"):
        name = f"m18-wave-1-{seat}.md"
        verdict = (ROOT / "docs" / "reviews" / name).read_text(encoding="utf-8")
        (reviews / name).write_text(re.sub(r"^date: .*$", "date: 2026-10-06", verdict, count=1, flags=re.M),
                                    encoding="utf-8")
    return record


def _wave_check(record: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "wave_check.py"), str(record)],
                          capture_output=True, text=True, cwd=record.parents[2], timeout=60, check=False)


def test_a_med_close_touching_one_of_its_plans_security_globs_is_refused(tmp_path: Path) -> None:
    """#140, slice 2: a MED close touching `EngineClient.swift` passed, because the rule read only
    `src/app/clients`. The plan's own globs make it HIGH."""
    done = _wave_check(_close(tmp_path, tier="MED", touched="ios/ModelRanking/Engine/EngineClient.swift", plan=GLOBS))
    assert done.returncode != 0 and "EngineClient.swift" in done.stdout, done.stdout


def test_a_close_whose_plan_names_no_security_globs_fails_closed(tmp_path: Path) -> None:
    """#140: a plan with no glob list, or no plan, cannot say what is HIGH; that is a failure."""
    assert "security glob" in _wave_check(_close(tmp_path / "a", tier="HIGH", touched="x.py", plan="")).stdout
    assert "security glob" in _wave_check(_close(tmp_path / "b", tier="HIGH", touched="x.py", plan=None)).stdout


def test_a_high_close_on_a_glob_and_a_med_close_off_them_pass(tmp_path: Path) -> None:
    """Quiet when it should be."""
    high = _close(tmp_path / "a", tier="HIGH", touched="ios/ModelRanking/Engine/EngineClient.swift", plan=GLOBS)
    assert _wave_check(high).returncode == 0, _wave_check(high).stdout
    med = _close(tmp_path / "b", tier="MED", touched="src/app/workflows/rank.py", plan=GLOBS)
    assert _wave_check(med).returncode == 0, _wave_check(med).stdout
