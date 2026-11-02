"""#554: three reads of the default branch by SHORT name, which a planted tag answers first.

git resolves `origin/main` to `refs/tags/origin/main` before `refs/remotes/origin/main`, and `main` to `refs/tags/main`
before `refs/heads/main` (gitrevisions(7)). #545 moved the deploy gate's policy readers to full refs; these three were
left (the fixes-1101 security review's M5, R1 and R3; the release delta's M13):

- `scripts/deploy_hosted_engine.sh` checks that HEAD is `origin/main`'s tip; a tag `origin/main` at an unmerged HEAD
  passed it, on the owner's Mac and on the nightly runner, whose checkout fetches every tag.
- `conformance/test-commit-identity.py` takes `main` as the protected base; a tag `main` at HEAD emptied the range it
  grades, so AI attribution on the branch passed.
- the Makefile's `closes` recipe read `origin/HEAD` for its changed-only range.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from .test_deploy_hosted import _deploy, _git, _scratch

ROOT = Path(__file__).resolve().parents[2]


def test_a_tag_named_origin_main_does_not_pass_the_deploy_tip_check(tmp_path: Path) -> None:
    """covers #554 (M5, M13): an unmerged HEAD with a tag `origin/main` on it is still not main's tip."""
    repo, _served, calls, env = _scratch(tmp_path)
    (repo / "README").write_text("an unmerged change\n", encoding="utf-8")
    _git("-C", str(repo), "commit", "-qam", "unmerged")
    # The served data names this commit as its builder, so the data check passes and only the tip check can refuse.
    head = _git("-C", str(repo), "rev-parse", "--short=7", "HEAD")
    (tmp_path / "served.db.refresh.json").write_text(f'{{"served_built_by": "release-{head}"}}', encoding="utf-8")
    _git("-C", str(repo), "tag", "origin/main", "HEAD")
    done = _deploy(env)
    assert done.returncode != 0 and "HEAD is not the tip of origin/main" in done.stderr, done.stdout + done.stderr
    assert not calls.exists(), "fly was called for a commit main does not hold"


def test_the_deploy_still_ships_main_s_tip_beside_a_tag_named_origin_main(tmp_path: Path) -> None:
    """covers #554: the full-ref read keeps the real case working -- HEAD at origin/main's tip deploys, whatever a
    tag of that name says."""
    repo, _served, calls, env = _scratch(tmp_path)
    _git("-C", str(repo), "tag", "origin/main", "HEAD")
    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert calls.exists()


def _identity_verdict(tmp_path: Path, plant_main_tag: bool) -> subprocess.CompletedProcess[str]:
    """test-commit-identity on a branch whose one commit carries AI attribution (a refusal), with or without a tag
    named `main` planted at HEAD."""
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp_path),
           "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
           "GIT_AUTHOR_NAME": "O", "GIT_COMMITTER_NAME": "O", "GIT_AUTHOR_EMAIL": "o@x", "GIT_COMMITTER_EMAIL": "o@x"}

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    (repo / "f").write_text("a", encoding="utf-8")
    git("add", "f")
    git("commit", "-qm", "owner work")
    git("switch", "-q", "-c", "work/1")
    (repo / "f").write_text("b", encoding="utf-8")
    git("commit", "-qam", "work", "-m", "Co-Authored-By: Claude <noreply@anthropic.com>")
    if plant_main_tag:
        git("tag", "main", "HEAD")
    return subprocess.run([sys.executable, str(ROOT / "conformance/test-commit-identity.py"), "--owner-email", "o@x"],
                          cwd=repo, env=env, capture_output=True, encoding="utf-8", check=False)


def test_the_attribution_control_refuses_without_a_planted_tag(tmp_path: Path) -> None:
    """covers #554: the control below -- the branch's attribution is refused."""
    done = _identity_verdict(tmp_path, plant_main_tag=False)
    assert done.returncode == 1, done.stdout + done.stderr


def test_a_tag_named_main_does_not_empty_the_graded_range(tmp_path: Path) -> None:
    """covers #554 (R1): with a tag `main` at HEAD the protected base is still the branch `main`."""
    done = _identity_verdict(tmp_path, plant_main_tag=True)
    assert done.returncode == 1, done.stdout + done.stderr


#: A git command that reads a revision, and a short name of the default branch in the same command.
_SHORT_READ = re.compile(r"\bgit\b[^;|&)]*?\b(?:merge-base|rev-parse|rev-list|log|diff)\b[^;|&)]*?"
                         r"(?<![\w/.-])(?:origin/(?:HEAD|main|master)|main|master)(?![\w/.-])")


def test_no_makefile_recipe_reads_the_default_branch_by_short_name() -> None:
    """covers #554 (R1, Makefile): every revision of the default branch the Makefile reads goes through its full ref."""
    hits = [f"Makefile:{n}: {line.strip()[:120]}"
            for n, line in enumerate((ROOT / "Makefile").read_text(encoding="utf-8").splitlines(), 1)
            if not line.lstrip().startswith("#") and _SHORT_READ.search(line)]
    assert not hits, "\n".join(hits)


def test_the_short_read_shape_is_caught() -> None:
    """covers #554: the shape test can go red -- it matches the line it replaced, and not its full-ref form."""
    assert _SHORT_READ.search("only=$$(git diff --name-only $$(git merge-base HEAD origin/HEAD 2>/dev/null))")
    assert _SHORT_READ.search("git rev-parse main")
    assert not _SHORT_READ.search("git show-ref --verify --hash refs/remotes/origin/HEAD")
    assert not _SHORT_READ.search("git merge-base HEAD \"$$base\"")
