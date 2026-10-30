"""The release Tester of 2026-10-31, on #510: the verified reader's own hash check on a commit.

`tests/unit/test_deploy_gate_494.py::test_a_forged_pinned_commit_is_not_read_as_the_pinned_tree` stays green with
the commit check in `brief_fields.batch_read` dropped, since `_commit` peels the pinned commit and git then refuses
the forged object first; it goes red only with both gone. #510's mutant was in `_object`, which #511 removed. This
test holds the reader's check alone: red with `kind != "commit"` added to its hash comparison.
"""

from __future__ import annotations

import subprocess
import zlib
from pathlib import Path

from .test_deploy_gate_444 import _module
from .test_deploy_gate_pin import _installed


def test_the_verified_reader_refuses_a_commit_that_does_not_hash(tmp_path: Path) -> None:
    """#510, #511: a commit object rewritten to name another tree is refused by the one verified reader."""
    repo = _installed(tmp_path)
    fields = _module("brief_fields")
    pinned = repo.git("show", "main:docs/devflow-pin.txt").split()[1]
    body = subprocess.run(["git", "cat-file", "commit", pinned], cwd=repo.root, capture_output=True,
                          check=True).stdout
    batch = fields.open_batch(repo.root)
    try:
        assert fields.batch_read(batch, pinned, "commit") == body, "the control: the real commit reads"
    finally:
        fields.close_batch(batch)
    forged = body.replace(repo.git("rev-parse", f"{pinned}^{{tree}}").encode(),
                          repo.git("rev-parse", "HEAD^{tree}").encode(), 1)
    assert forged != body
    loose = repo.root / ".git" / "objects" / pinned[:2] / pinned[2:]
    assert loose.is_file(), "the fixture's objects are loose"
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"commit %d\0" % len(forged) + forged))
    batch = fields.open_batch(repo.root)
    try:
        read = fields.batch_read(batch, pinned, "commit")
    finally:
        fields.close_batch(batch)
    assert isinstance(read, str) and "does not hash" in read, read
