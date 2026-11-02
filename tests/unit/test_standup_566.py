"""#566: `scripts/standup.sh` chose the default branch whose `docs/decisions.md` it compares by SHORT name
(`origin/HEAD origin/main origin/master main master`), and git resolves `origin/HEAD` to `refs/tags/origin/HEAD` and
`main` to `refs/tags/main` first. A tag of either name at the branch's tip made every ADR the branch adds read as
already merged, so "ADRs awaiting the owner's merge" listed none. Display only; read by full ref now, as #554 did
for the gates.
# covers #566
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = "# Decisions\n\n## D-100 — Merged\n\nBody.\n"
NEW = "\n## D-101 — On the branch\n\nBody.\n"


def _awaiting(clone: Path, env: dict[str, str]) -> list[str]:
    out = subprocess.run(["bash", str(clone / "scripts" / "standup.sh")], cwd=clone, capture_output=True, text=True,
                         env=env).stdout
    m = re.search(r"^-+ ADRs awaiting[^\n]*\n(.*?)^-----", out, re.M | re.S)
    return re.findall(r"^## ([DP]-\d+)", m.group(1), re.M) if m else ["<no ADR section>"]


def _clone(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A clone whose `main` and `origin/main` hold D-100, on a branch that adds D-101."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp_path)})
    origin, clone = tmp_path / "origin", tmp_path / "clone"

    def git(where: Path, *args: str) -> None:
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=where, check=True,
                       capture_output=True, env=env)

    origin.mkdir()
    git(origin, "init", "-q", "--bare", "-b", "main")
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    git(clone, "switch", "-q", "-c", "main")
    (clone / "docs").mkdir()
    (clone / "docs" / "decisions.md").write_text(DECISIONS, encoding="utf-8")
    git(clone, "add", "-A")
    git(clone, "commit", "-q", "-m", "decisions")
    git(clone, "push", "-q", "-u", "origin", "main")
    git(clone, "remote", "set-head", "origin", "main")
    (clone / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts" / "standup.sh", clone / "scripts" / "standup.sh")
    git(clone, "switch", "-q", "-c", "fix/issue-1-x")
    with (clone / "docs" / "decisions.md").open("a", encoding="utf-8") as f:
        f.write(NEW)
    git(clone, "commit", "-q", "-am", "an ADR on a branch")
    return clone, env


def test_the_control_an_adr_on_the_branch_awaits_the_merge(tmp_path: Path) -> None:
    clone, env = _clone(tmp_path)
    assert _awaiting(clone, env) == ["D-101"]


@pytest.mark.parametrize("tag", ["origin/HEAD", "origin/main", "main"])
def test_a_tag_named_like_the_default_branch_does_not_hide_an_awaiting_adr(tmp_path: Path, tag: str) -> None:
    """covers #566: a tag at the branch's tip named like a default-branch ref is not the default branch."""
    clone, env = _clone(tmp_path)
    subprocess.run(["git", "tag", tag, "HEAD"], cwd=clone, check=True, capture_output=True, env=env)
    assert _awaiting(clone, env) == ["D-101"]


@pytest.mark.parametrize("tag", ["origin/main", "main"])
def test_without_origin_head_a_tag_still_does_not_choose_the_base(tmp_path: Path, tag: str) -> None:
    """covers #566: a clone with no `origin/HEAD` reads `origin/main` next, and a tag of that name is not it either."""
    clone, env = _clone(tmp_path)
    for args in (["remote", "set-head", "origin", "-d"], ["tag", tag, "HEAD"]):
        subprocess.run(["git", *args], cwd=clone, check=True, capture_output=True, env=env)
    assert _awaiting(clone, env) == ["D-101"]
