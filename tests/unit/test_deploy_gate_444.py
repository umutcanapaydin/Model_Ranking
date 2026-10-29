"""#444 (the #410 security review's M1-M3 and R2): the deploy gate's DevFlow exemption, tightened.

A file DevFlow shipped, byte for byte as the commit pinned at the protected base has it, is not this product's code
(v7.2). Four ways that exemption reached further than it should: a symlink whose target holds the pinned bytes; a
workflow or script the brief's deploy commands start, which a hand-kept list did not name; a loose object forged at
the pinned id, which git serves without checking its hash; and the pin file itself, which no review was routed to.
"""

from __future__ import annotations

import importlib.util
import zlib
from pathlib import Path

import pytest

from .test_deploy_gate_pin import ROOT, Repo, _installed
from .test_review_need_base_policy import Repo as NeedRepo
from .test_review_need_base_policy import _brief


def _module(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(f"{name}_444", ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_symlink_to_the_pinned_bytes_is_code(tmp_path: Path) -> None:
    """M2: `shipped_unchanged` followed a symlink, so a link to any file holding the pinned bytes read as unchanged."""
    repo = _installed(tmp_path)
    elsewhere = tmp_path / "elsewhere.py"
    elsewhere.write_text("VERSION = 1\n", encoding="utf-8")
    (repo.root / "scripts" / "tool.py").unlink()
    (repo.root / "scripts" / "tool.py").symlink_to(elsewhere)
    repo.commit("tool.py is a link now")
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def _upgrade_shipping(repo: Repo, rel: str, text: str, brief: str | None = None) -> None:
    """On main: DevFlow ships `rel` as `text` and the owner pins that commit, as an upgrade would."""
    repo.git("checkout", "-q", "main")
    if brief is not None:
        repo.write("docs/project-brief.md", brief)
        repo.commit("the brief names its deploy commands")
    repo.write(rel, text)
    shipped = repo.commit(f"DevFlow v9.10 ships {rel}")
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.commit("pin v9.10")
    repo.git("checkout", "-q", "-b", "after-upgrade")


BRIEF = ("- **Working mode:** `light`\n"
         "- **Deploy commands:** `scripts/ship_it.sh`, `gh workflow run release.yml`\n")


@pytest.mark.parametrize(("rel", "text"), [
    ("scripts/ship_it.sh", "echo ship --somewhere-else\n"),
    (".github/workflows/release.yml", "on: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: echo hi\n"),
    (".github/workflows/carrier.yml", "on: push\njobs:\n  a:\n    steps:\n      - run: scripts/ship_it.sh\n"),
    # The release Tester, night-1028 round: `gh workflow run release.yml` dispatches `Release.yml` as well. Only the
    # surface's on-disk names hold that spelling, and dropping them stayed green while every workflow was lower-case.
    (".github/workflows/Release.yml", "on: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: echo hi\n"),
], ids=["a-declared-deploy-script", "a-dispatched-workflow", "a-workflow-that-runs-a-deploy",
        "a-dispatched-workflow-not-in-lower-case"])
def test_what_the_deploy_commands_start_is_code_even_byte_identical(tmp_path: Path, rel: str, text: str) -> None:
    """M3: the safety surface was a hand-kept list, and the installed nightly workflow was not on it. What the brief's
    deploy commands start -- a declared script, a dispatched workflow, a workflow whose run line is a deploy command --
    is derived from the brief and the workflows, and is code to the gate even when an upgrade ships it unchanged."""
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, rel, text, brief=BRIEF)
    code, out = repo.check()
    assert code != 0, out
    assert rel in out, out


def test_a_plain_tooling_file_from_the_same_upgrade_owes_nothing(tmp_path: Path) -> None:
    """M3's control: with the same brief, a tooling file no deploy command starts stays DevFlow's."""
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=BRIEF)
    code, out = repo.check()
    assert code == 0, out


def test_a_loose_object_forged_at_the_pinned_blob_is_not_read_as_the_pinned_bytes(tmp_path: Path) -> None:
    """R2: git serves a loose object at its id without hashing it. Overwrite the pinned blob's file with the agent's
    bytes, and the changed tool read as DevFlow's, unchanged."""
    repo = _installed(tmp_path)
    pinned = repo.git("show", "main:docs/devflow-pin.txt").split()[1]
    blob = repo.git("rev-parse", f"{pinned}:scripts/tool.py")
    changed = b"VERSION = 1  # the agent's change\n"
    (repo.root / "scripts" / "tool.py").write_bytes(changed)
    repo.commit("a change")
    loose = repo.root / ".git" / "objects" / blob[:2] / blob[2:]
    assert loose.is_file(), "the fixture's objects are loose"
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"blob %d\0" % len(changed) + changed))
    code, out = repo.check()
    assert code != 0, out


def test_the_pin_file_goes_to_a_security_review(tmp_path: Path) -> None:
    """M1: the pin decides which bytes the gate exempts, so a change to it is policy, in either mode."""
    repo = NeedRepo(tmp_path / "light", _brief("light"))
    repo.write("docs/devflow-pin.txt", "v9.9 " + "0" * 40 + "\n")
    repo.commit("re-pin")
    _, last, out = repo.need()
    assert last == "review-need: security", out
    assert "policy edit: docs/devflow-pin.txt" in out, out


def test_review_need_routes_the_file_the_gate_reads() -> None:
    """M1, derived, not typed twice: the pin review-need routes is the deploy gate's own."""
    assert _module("deploy_gate").DEVFLOW_PIN in _module("review_need").EXCEPTION_FILES
