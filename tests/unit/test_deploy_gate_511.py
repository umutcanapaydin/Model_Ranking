"""#511: the deploy gate reads git objects through one verified reader.

`_unhashed` (#493) and `verified_blob` (#444) each kept their own object reader and their own tree parser, and the two
disagreed on the hash kind and the tree-mode spelling. One rule in two hand-kept copies is a finding (AGENTS.md §3.5):
a fix to one copy leaves the other. Both now read through `brief_fields.batch_read` and parse trees with
`brief_fields.tree_entries` (#509 moved the reader there, so the brief is read verified too).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _module
from .test_deploy_gate_pin import Repo


def _pinned(tmp_path: Path) -> tuple[Repo, str]:
    repo = Repo(tmp_path / "pinned")
    repo.write("scripts/tool.py", "VERSION = 1\n")
    return repo, repo.commit("pinned")


def test_verified_blob_refuses_what_the_shared_reader_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, commit = _pinned(tmp_path)
    gate = _module("deploy_gate")
    assert gate.verified_blob(repo.root, commit, "scripts/tool.py") == b"VERSION = 1\n", "the control"
    real = gate.brief_fields.batch_read

    def forged_blobs(batch, oid: str, kind: str):  # type: ignore[no-untyped-def]
        return f"object {oid} ({kind}) does not hash to its id" if kind == "blob" else real(batch, oid, kind)

    monkeypatch.setattr(gate.brief_fields, "batch_read", forged_blobs)
    assert gate.verified_blob(repo.root, commit, "scripts/tool.py") is None


def test_verified_blob_parses_trees_with_the_shared_parser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, commit = _pinned(tmp_path)
    gate = _module("deploy_gate")
    monkeypatch.setattr(gate.brief_fields, "tree_entries", lambda body, size: [])
    assert gate.verified_blob(repo.root, commit, "scripts/tool.py") is None


def test_verified_blob_still_refuses_a_path_that_is_not_a_file(tmp_path: Path) -> None:
    """The stricter reading at the pin stays: a directory or a missing name is no shipped file."""
    repo, commit = _pinned(tmp_path)
    gate = _module("deploy_gate")
    assert gate.verified_blob(repo.root, commit, "scripts") is None
    assert gate.verified_blob(repo.root, commit, "scripts/other.py") is None
    assert gate.verified_blob(repo.root, "0" * 40, "scripts/tool.py") is None
