"""#506: rename detection hid a code deletion from the deploy gate.

`changed_since` ran `git diff --name-only <reviewed head>` with git's rename detection on, which lists a renamed file
by its new name only. `git mv src/app.py docs/app.md` then listed `docs/app.md`, a deploy record, and the gate said no
code changed since although the product's code was gone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_pin import _installed


@pytest.mark.parametrize("how", ["committed", "uncommitted", "intent-to-add"])
def test_a_code_file_renamed_into_a_record_path_is_still_a_change(tmp_path: Path, how: str) -> None:
    """`intent-to-add` (the review's R1): a plain `mv` and `git add -N` of the new name is a rename to git as well."""
    repo = _installed(tmp_path)
    assert repo.check()[0] == 0, "the control: nothing changed since the reviewed head"
    (repo.root / "docs").mkdir(exist_ok=True)
    if how == "intent-to-add":
        (repo.root / "src" / "app.py").rename(repo.root / "docs" / "app.md")
        repo.git("add", "-N", "docs/app.md")
    else:
        repo.git("mv", "src/app.py", "docs/app.md")
    if how == "committed":
        repo.commit("move the app into the records")
    code, out = repo.check()
    assert code != 0, out
    assert "src/app.py" in out, out


def test_a_rename_detection_setting_does_not_hide_it_either(tmp_path: Path) -> None:
    """The change may write its clone's config: `diff.renames` set to copies must not bring the hiding back."""
    repo = _installed(tmp_path)
    repo.git("config", "diff.renames", "copies")
    (repo.root / "docs").mkdir(exist_ok=True)
    repo.git("mv", "src/app.py", "docs/app.md")
    repo.commit("move the app into the records")
    code, out = repo.check()
    assert code != 0, out
    assert "src/app.py" in out, out
