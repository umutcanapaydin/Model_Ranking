"""#546 (the fixes-1101 security review's R3): `wave_check` named the default branch by short names (`origin/main`,
`main`), and git resolves a short name to `refs/<name>` and `refs/tags/<name>` before `refs/heads/` or
`refs/remotes/`. A planted tag of that name then chose the commits a backlog wave's decision order (#274), a close's
wave base and its "merged into main" skip were read against. Now each is `brief_fields.exact_ref` over
`brief_fields.DEFAULT_BRANCHES` (#545), one list read exactly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.test_wave_check_backlog_order import WITH_D2, _branch
from tests.unit.test_wave_check_m21_rules import _commit, _git, _module

ROOT = Path(__file__).resolve().parents[2]
PLANTS = [("tag", "origin/main"), ("tag", "main"), ("update-ref", "refs/main"), ("update-ref", "refs/origin/main")]
IDS = ["tag-origin-main", "tag-main", "ref-main", "ref-origin-main"]


def _plant(root: Path, kind: str, name: str, at: str) -> None:
    _git(root, *(["tag", name, at] if kind == "tag" else ["update-ref", name, at]))


def _rule_beside_code(tmp_path: Path) -> Path:
    root = _branch(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n"})
    return root


def test_the_control_a_rule_beside_its_code_is_found(tmp_path: Path) -> None:
    problems, skipped = _module("wave_check").branch_adr_problems(_rule_beside_code(tmp_path))
    assert skipped is None and any("D-2" in p for p in problems), (problems, skipped)


@pytest.mark.parametrize("plant", PLANTS, ids=IDS)
def test_a_planted_name_does_not_hide_a_backlog_wave_s_decision_order(tmp_path: Path, plant: tuple[str, str]) -> None:
    """A name planted at HEAD made the range since `origin/main` empty, so the ADR written beside its code passed."""
    root = _rule_beside_code(tmp_path)
    _plant(root, *plant, _git(root, "rev-parse", "HEAD"))
    problems, skipped = _module("wave_check").branch_adr_problems(root)
    assert skipped is None and any("D-2" in p for p in problems), f"a planted {plant[1]} hid the finding: {problems}"


@pytest.mark.parametrize("plant", PLANTS, ids=IDS)
def test_a_planted_name_does_not_mark_a_close_merged(tmp_path: Path, plant: tuple[str, str]) -> None:
    """`_merged` skips every history rule of a close; a planted name at the close's commit answered yes."""
    root = _rule_beside_code(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    wave_check = _module("wave_check")
    assert wave_check._merged(root, head) is False, "the control: the branch's commit is not on main"
    _plant(root, *plant, head)
    assert wave_check._merged(root, head) is False, f"a planted {plant[1]} marked the close merged"


@pytest.mark.parametrize("plant", PLANTS, ids=IDS)
def test_a_planted_name_does_not_narrow_the_wave_base(tmp_path: Path, plant: tuple[str, str]) -> None:
    """The wave starts at the merge base with the default branch; a planted name at HEAD moved it to HEAD."""
    root = _rule_beside_code(tmp_path)
    real = _git(root, "merge-base", "refs/heads/main", "HEAD")
    _plant(root, *plant, _git(root, "rev-parse", "HEAD"))
    assert _module("wave_check")._wave_base(root, None, "HEAD") == real


def test_the_default_branch_is_named_once_and_read_exactly() -> None:
    """Derive, don't enumerate (AGENTS.md §3.5): wave_check reads brief_fields' list and names no branch itself."""
    source = (ROOT / "scripts" / "wave_check.py").read_text(encoding="utf-8")
    assert "brief_fields.DEFAULT_BRANCHES" in source and "brief_fields.exact_ref" in source
    assert '("origin/main", "main")' not in source and '"origin/main^{commit}"' not in source
