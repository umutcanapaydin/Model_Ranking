"""The v7.1 upgrade security review's M4: `scripts/review_need.py`'s sensitive-path signal was untested.
`conformance/test-review-need-mode.py` reaches it only through a path that a declared HIGH glob also
covers, so the mutant `hit = []` on the sensitive-name list passed every gate. Here no HIGH path is
declared, so the name alone must route the range to security; a test file with such a name alone must not.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "review_need.py"
BRIEF = ("---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n"
         "- **Working mode:** `light`\n- **Paths that make a change HIGH:** `none`\n")


def _git(root: pathlib.Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                   cwd=root, capture_output=True, check=True, env=env)


def _need(root: pathlib.Path, rel: str) -> str:
    _git(root, "init", "-q")
    (root / "docs").mkdir()
    (root / "docs" / "project-brief.md").write_text(BRIEF, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "change")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run([sys.executable, str(SCRIPT), "--range", "HEAD~1..HEAD"], cwd=root, capture_output=True,
                          text=True, encoding="utf-8", check=False, env=env)
    return done.stdout + done.stderr


def test_a_product_file_with_a_sensitive_name_is_printed_for_the_release_review_with_no_high_path_declared(
        tmp_path: pathlib.Path) -> None:
    """D-207 clause 1 (v7.2): in light mode only the declared HIGH paths route a change to security; the
    sensitive name is still detected and printed for the release review, so the mutant `hit = []` fails here."""
    out = _need(tmp_path, "src/deploy_x.py")
    assert out.strip().splitlines()[-1] == "review-need: none"
    assert "sensitive path names: src/deploy_x.py" in out
    assert "for the release review" in out


def test_a_test_file_with_a_sensitive_name_alone_needs_nothing(tmp_path: pathlib.Path) -> None:
    out = _need(tmp_path, "tests/test_auth.py")
    assert out.strip().splitlines()[-1] == "review-need: none"
    assert "test-only files with sensitive names" in out
