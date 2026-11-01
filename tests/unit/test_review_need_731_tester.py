"""The release delta Tester of the DevFlow v7.3.1 upgrade (D-241, 2026-11-01): `make review-need` on v7.3's two
policy lines.

`bc5d9b8` makes `Deploy targets:` and `Security-invariant tests:` policy fields (`brief_fields.POLICY_FIELDS`), and
keeps the project's rule that a policy edit is never "record only" (`review_need.assess`, #283), beside v7.3's new
short cut that routes a range of records alone to no review. A range that edits only one of those two lines is a
range of one record, `docs/project-brief.md`: dropping either line from POLICY_FIELDS (F-P15), or the `not edits`
from the short cut (F-P13), routed it to `none`, and no test went red.

Each case runs `scripts/review_need.py` as a program on a throwaway repository, as `make review-need` does.
"""

from __future__ import annotations

import pytest

from .test_review_need_base_policy import Repo, _brief


# covers D-241 clause 2, #283 -- an edit of a v7.3 policy line is a policy edit, never a record-only range
@pytest.mark.parametrize(("name", "before", "after"), [
    ("Deploy targets", "", "- **Deploy targets:** `staging: ./stg.sh`\n"),
    ("Deploy targets", "- **Deploy targets:** `production: ./ship.sh`\n", "- **Deploy targets:** `staging: ./ship.sh`\n"),
    ("Security-invariant tests", "- **Security-invariant tests:** `tests/test_scope.py`\n", ""),
    ("Security-invariant tests", "", "- **Security-invariant tests:** `none`\n"),
], ids=["targets-added", "targets-lowered", "invariants-dropped", "invariants-added"])
def test_an_edit_of_a_v73_policy_line_alone_still_owes_security(tmp_path, name: str, before: str, after: str) -> None:
    repo = Repo(tmp_path, _brief("light", extra=before))
    repo.write("docs/project-brief.md", _brief("light", extra=after))
    repo.commit("docs: the brief")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: security"), out
    assert f"policy edit: the brief's `{name}:`" in out, out
    assert "record only" not in out, out


# covers D-241 clause 2 -- the control: a brief edit outside the policy fields is a record, and owes no review
def test_a_brief_edit_outside_the_policy_fields_is_record_only(tmp_path) -> None:
    repo = Repo(tmp_path, _brief("light", extra="- **Rollback command:** `none`\n"))
    repo.write("docs/project-brief.md", _brief("light", extra="- **Rollback command:** `fly releases rollback`\n"))
    repo.commit("docs: the brief")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: none"), out
    assert "record only" in out, out
