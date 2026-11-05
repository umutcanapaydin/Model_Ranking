"""#568: the deploy-gate fixtures forge a LOOSE object by its path (`test_deploy_gate_493.py`, `_494.py`, ...), and
failed now and then with "the fixture's objects are loose". Measured cause: `git commit` runs `git gc --auto`, which
packs every loose object once `objects/17/` holds more than 6700/256 of them -- a matter of how the fixture's hashes
fall -- and by default does it DETACHED, in the background, so it races with the fixture's next read. The shared
`Repo` now turns automatic packing off. The tests run that `gc --auto` in the foreground, so the race is not needed.
# covers #568
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .test_deploy_gate_pin import Repo


def _blobs_in_17(count: int) -> list[bytes]:
    """`count` file bodies whose git blob ids start `17`: the directory `gc --auto` samples."""
    found: list[bytes] = []
    n = 0
    while len(found) < count:
        body = f"probe {n}\n".encode()
        if hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest().startswith("17"):
            found.append(body)
        n += 1
    return found


def test_a_commit_past_the_auto_gc_threshold_leaves_the_fixtures_objects_loose(tmp_path: Path) -> None:
    """covers #568: 40 blobs in `objects/17/` (past 6700/256) -- without the fix `git commit` packs them all."""
    repo = Repo(tmp_path / "repo")
    for i, body in enumerate(_blobs_in_17(40)):
        (repo.root / f"f{i}.txt").write_bytes(body)
    repo.commit("past the threshold")
    repo.git("-c", "gc.autoDetach=false", "gc", "--auto")  # what `git commit` starts in the background
    assert not list((repo.root / ".git" / "objects" / "pack").glob("*.pack")), "git gc --auto packed the fixture"


def test_the_threshold_packs_a_repository_that_does_not_turn_it_off(tmp_path: Path) -> None:
    """covers #568: the control -- in a plain repository the same commit is packed, so the test above can go red."""
    import subprocess

    root = tmp_path / "plain"
    root.mkdir()
    # #593: the commit's own `gc --auto` in the foreground too -- detached, it raced the assertion below (and the
    # explicit `gc --auto` found its lock and skipped)
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false", "-c", "gc.autoDetach=false"]
    subprocess.run([*git, "init", "-q"], cwd=root, check=True, capture_output=True)
    for i, body in enumerate(_blobs_in_17(40)):
        (root / f"f{i}.txt").write_bytes(body)
    for args in (["add", "-A"], ["commit", "-q", "-m", "x"], ["gc", "--auto"]):
        subprocess.run([*git, *args], cwd=root, check=True, capture_output=True)
    assert list((root / ".git" / "objects" / "pack").glob("*.pack"))
