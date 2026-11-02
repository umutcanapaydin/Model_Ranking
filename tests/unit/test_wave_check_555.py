"""#555 (the fixes-1101 review's R2): `wave_check._wave_base` took a LOCAL `refs/heads/closure/m<N-1>` as the previous
milestone's closure wherever it stood. #548 closed the tag route; a branch a session makes at the close's end still
moved the wave's start to the end, so the close read an empty range.

Now a closure branch counts only through the closure record it carries -- `docs/closure-report-m<N-1>.md` or
`docs/reviews/m<N-1>-tester.md` -- and the wave starts no later than the commit that last wrote that record in the
branch's history. A branch moved past its record cannot move the base with it.
"""

from __future__ import annotations

import re

from tests.unit.test_wave_check_546 import _rule_beside_code
from tests.unit.test_wave_check_m21_rules import _commit, _git, _module

IDS = re.match(r"m(\d+)-w(\d+)", "m2-w1")


def test_a_closure_branch_made_at_the_close_s_end_does_not_empty_the_range(tmp_path) -> None:
    """covers #555: no m1 closure record anywhere; a session-made `closure/m1` at HEAD leaves the base on main."""
    root = _rule_beside_code(tmp_path)
    real = _git(root, "merge-base", "refs/heads/main", "HEAD")
    _git(root, "branch", "closure/m1", _git(root, "rev-parse", "HEAD"))
    assert _module("wave_check")._wave_base(root, IDS, "HEAD") == real


def test_a_closure_branch_moved_past_its_record_starts_the_wave_at_the_record(tmp_path) -> None:
    """covers #555: the record exists, but the branch was moved to the close's end; the wave starts at the record."""
    root = _rule_beside_code(tmp_path)
    record = _git(root, "rev-parse", _commit(root, "m1 closes", "2026-10-11T12:00:00",
                                             {"docs/reviews/m1-tester.md": "# m1 Tester\n"}))
    _commit(root, "m2's first wave", "2026-10-12T12:00:00", {"src/app/later.py": "y = 1\n"})
    _git(root, "branch", "closure/m1", _git(root, "rev-parse", "HEAD"))
    assert _module("wave_check")._wave_base(root, IDS, "HEAD") == record


def test_the_control_a_real_closure_branch_still_moves_the_wave_base(tmp_path) -> None:
    """covers #555: a milestone stacked on an unmerged closure, whose tip wrote its record, starts at that closure
    (the M21 repo review's M2), from origin's ref as from the local one."""
    for ref in ("refs/heads/closure/m1", "refs/remotes/origin/closure/m1"):
        root = _rule_beside_code(tmp_path / ref.replace("/", "_"))
        record = _git(root, "rev-parse", _commit(root, "m1 closes", "2026-10-11T12:00:00",
                                                 {"docs/closure-report-m1.md": "# m1 closure\n"}))
        _git(root, "update-ref", ref, record)
        _commit(root, "m2's first wave", "2026-10-12T12:00:00", {"src/app/later.py": "y = 1\n"})
        assert _module("wave_check")._wave_base(root, IDS, "HEAD") == record, ref
