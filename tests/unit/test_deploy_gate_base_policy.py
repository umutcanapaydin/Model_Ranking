"""#283: `scripts/deploy_gate.py` reads the brief's policy fields at the protected base, not from the tree.

`Deploy commands:` says what the gate guards and `Working mode:` which Tester verdict it asks for. Read from the
tree about to ship, a change could delete a deploy command, or switch the mode to the verdict it has. Now the
base is the merge-base of HEAD with the default branch: a deploy is any command the base's brief or the tree's
declares, both modes' Tester verdicts are asked for when the tree's mode is not the base's, and a base git cannot
read refuses every declared deploy and fails `--check` (D-185's hard refusals in the guard are unchanged).

Each case is a throwaway repository: `main` holds the brief and current verdicts, the tree under it the change.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "deploy_gate.py"


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("deploy_gate_283", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                          cwd=root, capture_output=True, text=True, check=True, env=_env(), timeout=60).stdout.strip()


def _brief(mode: str | None, deploy: str) -> str:
    lines = ["---", "record_type: brief", "id: project-brief", "status: draft", "---"]
    if mode is not None:
        lines.append(f"- **Working mode:** `{mode}`")
    return "\n".join([*lines, f"- **Deploy commands:** `{deploy}`"]) + "\n"


def _verdict(head: str) -> str:
    return f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {head}\n"


def _project(root: Path, mode: str | None = "light", deploy: str = "vercel deploy", branch: str = "main") -> Path:
    """A repository whose `branch` holds the brief, one source file, and the light mode's verdicts at its head."""
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", branch)
    (root / "docs" / "reviews").mkdir(parents=True)
    (root / "docs" / "project-brief.md").write_text(_brief(mode, deploy), encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    head = _git(root, "rev-parse", "HEAD")
    for name in ("release-security.md", "release-tester.md"):
        (root / "docs" / "reviews" / name).write_text(_verdict(head), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs: the verdicts")
    return root


def _brief_edit(root: Path, mode: str | None, deploy: str, commit: bool) -> None:
    (root / "docs" / "project-brief.md").write_text(_brief(mode, deploy), encoding="utf-8")
    if commit:
        _git(root, "checkout", "-q", "-b", "change")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "docs: the brief")


def test_the_base_is_readable_and_every_verdict_current(tmp_path: Path) -> None:
    root = _project(tmp_path / "p")
    whys = [why for why, _ in _gate().verdicts(root)]
    assert whys == [None, None, None], whys
    assert _gate().deploy_in([["vercel", "deploy"]], root) == "vercel deploy"


def test_a_deploy_command_the_change_deletes_is_still_a_deploy(tmp_path: Path) -> None:
    for commit in (False, True):
        root = _project(tmp_path / f"p{commit}")
        _brief_edit(root, "light", "none", commit)
        (root / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")   # code the verdicts have not seen
        gate = _gate()
        assert gate.deploy_in([["vercel", "deploy"]], root) == "vercel deploy", commit
        assert gate.judge([["vercel", "deploy"]], root) == 2, commit


def test_a_deploy_command_the_change_adds_is_a_deploy_too(tmp_path: Path) -> None:
    root = _project(tmp_path / "p")
    _brief_edit(root, "light", "vercel deploy, ./ship.sh", commit=False)
    assert _gate().deploy_in([["./ship.sh"]], root) == "./ship.sh"


def test_a_change_to_light_mode_still_needs_the_heavy_tester(tmp_path: Path) -> None:
    """A heavy project whose change says light: the base's mode asks for `m<N>-tester.md`, which it lacks."""
    for commit in (False, True):
        root = _project(tmp_path / f"p{commit}", mode="heavy")
        _brief_edit(root, "light", "vercel deploy", commit)
        whys = [why or "" for why, _ in _gate().verdicts(root)]
        assert any("no milestone Tester verdict" in why for why in whys), whys
        assert _gate().judge([["vercel", "deploy"]], root) == 2


def test_a_change_of_mode_asks_for_both_testers(tmp_path: Path) -> None:
    root = _project(tmp_path / "p", mode="light")
    _brief_edit(root, None, "vercel deploy", commit=True)                 # the mode line deleted: heavy
    summaries = [summary for _, summary in _gate().verdicts(root)]
    assert any("tester (light mode)" in s for s in summaries) and any("tester (heavy mode)" in s for s in summaries)
    head = _git(root, "rev-parse", "HEAD")
    (root / "docs" / "reviews" / "m1-tester.md").write_text(_verdict(head), encoding="utf-8")
    assert [why for why, _ in _gate().verdicts(root)] == [None, None, None, None]


def test_a_base_that_cannot_be_read_refuses_the_deploy_and_fails_the_check(tmp_path: Path) -> None:
    """No default branch to take a merge-base with: the deploy is refused, `--check` fails, and a command that is
    not a declared deploy still passes (the tree's brief is read to tell one)."""
    root = _project(tmp_path / "p", branch="work")
    gate = _gate()
    why, _ = gate.verdicts(root)[0]
    assert why and "cannot be read at the protected base" in why and "#283" in why, why
    assert gate.judge([["vercel", "deploy"]], root) == 2
    assert gate.judge([["ls"]], root) == 0
    done = subprocess.run([sys.executable, str(SCRIPT), "--check"], cwd=root, capture_output=True, text=True,
                          check=False, env=_env(), timeout=60)
    assert done.returncode == 1 and "deploy-check FAIL: the brief's policy fields cannot be read" in done.stdout, done


def test_no_git_on_path_refuses_a_deploy_and_nothing_else(tmp_path: Path) -> None:
    """The guard asks `--judge` of every Bash call, sometimes with only python3 on PATH (`test-hook-claims.py`):
    the base read must fail soft there, so `ls` passes and a declared deploy is refused."""
    root = _project(tmp_path / "p")
    bare = tmp_path / "bin"
    bare.mkdir()
    (bare / "python3").symlink_to(sys.executable)
    for words, want in ((["ls"], 0), (["vercel", "deploy"], 2)):
        done = subprocess.run([str(bare / "python3"), str(SCRIPT), "--judge"], cwd=root, capture_output=True,
                              text=True, check=False, env={**_env(), "PATH": str(bare)}, timeout=60,
                              input=json.dumps({"commands": [words]}))
        assert done.returncode == want, (words, done)
