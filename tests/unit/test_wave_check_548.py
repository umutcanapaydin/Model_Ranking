"""#548: `wave_check._wave_base` read the previous milestone's closure branch by short names (`origin/closure/m<N>`,
`closure/m<N>`), and git resolves a short name to `refs/<name>` and `refs/tags/<name>` before `refs/heads/` or
`refs/remotes/`. A planted tag of that name at HEAD moved the wave's start to HEAD, so the close read an empty range.
Now each is read by its full ref through `brief_fields.exact_ref` (#545, #546).
"""

from __future__ import annotations

import re

import pytest

from tests.unit.test_wave_check_546 import _plant, _rule_beside_code
from tests.unit.test_wave_check_m21_rules import _git, _module

IDS = re.match(r"m(\d+)-w(\d+)", "m2-w1")
PLANTS = [("tag", "closure/m1"), ("tag", "origin/closure/m1"), ("update-ref", "refs/closure/m1"),
          ("update-ref", "refs/origin/closure/m1")]


def test_the_control_a_real_closure_branch_moves_the_wave_base(tmp_path) -> None:
    """A milestone stacked on an unmerged closure starts at that closure (the M21 repo review's M2)."""
    root = _rule_beside_code(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "branch", "closure/m1", head)
    assert _module("wave_check")._wave_base(root, IDS, "HEAD") == head


@pytest.mark.parametrize("plant", PLANTS, ids=["tag", "tag-origin", "ref", "ref-origin"])
def test_a_planted_closure_name_does_not_narrow_the_wave_base(tmp_path, plant: tuple[str, str]) -> None:
    root = _rule_beside_code(tmp_path)
    real = _git(root, "merge-base", "refs/heads/main", "HEAD")
    _plant(root, *plant, _git(root, "rev-parse", "HEAD"))
    assert _module("wave_check")._wave_base(root, IDS, "HEAD") == real, f"a planted {plant[1]} moved the wave base"
