"""#400: the Bash guard reads `env -S` wherever env's options put it, and refuses an option it cannot read.

The run queue-1021 owner bundle's security review, round 1, M6: the guard read the command `env -S` carries only
from a word that starts with `-S` or `--split-string`. A cluster (`env -iS 'fly deploy'`, `-vS`, `-0S`), a glued
value (`env -iS'fly deploy'`), `-S` after a valued option and its value (`env -u X -S ...`) and an abbreviated long
option (`env --sp ...`) passed the guard whole: no D-185 `fly` refusal and no deploy gate. Now `-S` is read
anywhere in a short-option cluster and after any option's value, and a cluster or a long option the guard cannot
read is refused. The guard is the owner's (`.claude/hooks/bash_guard.py`): the change is in
`build/owner-run-queue-1021.patch`, and these cases are red until the owner applies it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD_DIR = ROOT / ".claude" / "hooks"
GUARD = GUARD_DIR / "bash_guard.py"

RELEASE = """name: Release
on: [workflow_dispatch]
jobs:
  ship:
    runs-on: ubuntu-latest
    steps:
      - run: ./ship.sh --prod
"""


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bash_guard_400", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ungoverned(guard: ModuleType, tmp_path: Path, tmp_path_factory: pytest.TempPathFactory,
               monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory no brief governs, and a guard checkout with no brief: only the guard's own rules answer."""
    where = tmp_path / "elsewhere"
    where.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(where))
    monkeypatch.setattr(guard, "OWN", str(tmp_path_factory.mktemp("own")))
    return where


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                   cwd=root, capture_output=True, check=True, env=env, timeout=60)


@pytest.fixture
def own(guard: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The guard's own project: this deploy gate, a workflow that deploys, and no verdict."""
    root = tmp_path / "own"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "project-brief.md").write_text("- **Working mode:** `light`\n- **Deploy commands:** `./ship.sh`\n",
                                                    encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "release.yml").write_text(RELEASE, encoding="utf-8")
    (root / "scripts").mkdir()
    for name in ("deploy_gate.py", "brief_fields.py"):
        (root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    monkeypatch.setattr(guard, "OWN", str(root))
    return root


def _bash(guard: ModuleType, command: str, cwd: Path) -> str | None:
    why: str | None = guard.judge_call({"tool_input": {"command": command}, "cwd": str(cwd)})
    return why


@pytest.mark.parametrize("command", [
    "env -iS 'fly deploy'", "env -iS'fly deploy'", "env -vS'fly deploy'", "env -0S 'fly deploy'",
    "env -i0vS 'fly deploy'", "env -u X -S 'fly deploy'", "env -uX -iS 'fly deploy'", "env --sp 'fly deploy'",
    "env --split='fly deploy'", "env -C /tmp -S 'fly deploy'", "env -i -- env -iS 'fly deploy'",
])
def test_fly_carried_by_env_s_in_any_spelling_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    why = _bash(guard, command, ungoverned)
    assert why and "fly deploy" in why, (command, why)


@pytest.mark.parametrize("command", [
    r"env -S 'fly\_deploy'", r"env -S 'fl${X}y deploy'", r"env -S'sh -c fly\_deploy'", r"env -S'-iS fly\_deploy'",
    r"env -S'-S fly\tdeploy'", r"env -S'-iS gh\_workflow\_run\_release.yml'", r'env -S "fly\_deploy"',
    r"env --split-string='fly\_deploy'", r"env -iS 'echo\_x'",
])
def test_an_env_s_string_with_env_s_own_escapes_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """The bundle review's round 2, B1: env splits its `-S` string by its own rules -- `\\_` separates words, `\\t`
    is a space, `${NAME}` expands -- so `env -S 'fly\\_deploy'` runs `fly deploy`. A backslash or a `$` there is
    refused, not translated."""
    why = _bash(guard, command, ungoverned)
    assert why and "#400" in why and "env -S" in why, (command, why)


@pytest.mark.parametrize("command", [
    r"env -S $'fly\vdeploy'", r"env -S $'fly\fdeploy'", r"env -S $'fly\rdeploy'", r"env -S $'fly\ndeploy'",
    r"env -S $'fly\x0bdeploy'", r"env -S $'fly\013deploy'", r"env --split-string=$'fly\fdeploy'",
    "env -iS 'fly\x0bdeploy'", "env -S 'fly\x0bdeploy'", "env -S 'gh\x0bworkflow\x0brun\x0brelease.yml'",
    "env -S 'sh -c fly\x0bdeploy'", "env -S 'fly\x0cdeploy'", "env -S 'fly\rdeploy'",
    # One rule, so a tab too: env splits on it, and it is not printable.
    "env -S 'fly\tdeploy'", r"env -S $'fly\tdeploy'",
])
def test_an_env_s_string_with_a_character_env_splits_on_is_refused(guard: ModuleType, ungoverned: Path,
                                                                    command: str) -> None:
    """The bundle review's round 3, B2: env splits its `-S` string on a raw VT, FF, CR, LF or tab, and the shell
    does not (a raw LF is the shell's command separator), so `env -S $'fly\\vdeploy'` ran `fly deploy`. Any
    character that is not printable, but the plain space, is refused there, with a backslash and a `$`."""
    why = _bash(guard, command, ungoverned)
    assert why and "#400" in why and "env -S" in why, (command, why)


@pytest.mark.parametrize("command", [
    r"find . -exec env fly deploy \;", r"find . -exec env -S 'fly deploy' \;", r"find . -execdir env fly deploy \;",
    r"find . -execdir env -iS 'fly deploy' {} +", r"find . -ok sudo fly deploy \;", r"find . -okdir nice fly deploy \;",
    r"find . -exec env -S $'fly\vdeploy' \;", r"find . -name x -exec env -u X fly deploy \;",
])
def test_a_wrapper_behind_find_exec_is_unwrapped(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """Round 3's M10: `find . -exec fly deploy \\;` was refused, but an `env` (or any wrapper) behind `-exec` was
    never unwrapped, so `find . -exec env fly deploy \\;` passed."""
    why = _bash(guard, command, ungoverned)
    assert why and ("fly deploy" in why or "#400" in why), (command, why)


@pytest.mark.parametrize("command", [
    r"find . -name x -exec ls {} \;", r"find . -type f -exec wc -l {} +", r"find . -exec env -i ls \;",
    r"find . -execdir env A=1 pwd \;",
])
def test_find_exec_that_runs_nothing_guarded_is_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize("command", ["env -iZ ls", "env -Zi ls", "env --frobnicate ls", "env --i ls"])
def test_an_env_option_the_guard_cannot_read_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """`--i` is ambiguous (`--ignore-environment`, `--ignore-signal`): GNU env refuses it too."""
    why = _bash(guard, command, ungoverned)
    assert why and "#400" in why, (command, why)


@pytest.mark.parametrize("command", [
    "env -i ls", "env -u TMPDIR ls", "env -uTMPDIR ls", "env --unset=X ls", "env --unset X ls", "env A=b ls",
    "env - ls", "env -i0v ls", "env -C /tmp ls", "env --chdir /tmp ls", "env --ignore-environment ls",
    "env -S 'ls -l'", "env -S 'ls -la'", "env -iS 'echo hi'", "env -- ls",
])
def test_env_spellings_that_run_nothing_guarded_are_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize("command", ["env -iS'gh workflow run release.yml'", "env -vS 'gh run rerun 1'"])
def test_a_dispatch_carried_by_env_s_meets_the_deploy_gate(guard: ModuleType, own: Path, command: str) -> None:
    why = _bash(guard, command, own)
    assert why and "deploy gate" in why and "is a deploy" in why, (command, why)


def test_the_hook_exits_exactly_2_on_a_clustered_env_s(tmp_path: Path) -> None:
    """Through the guard's own `main`, as Claude Code runs it: a hook blocks only on exit 2."""
    program = (f"import sys, tempfile; sys.path.insert(0, {str(GUARD_DIR)!r}); import bash_guard as g\n"
               "g.OWN = tempfile.mkdtemp()\nsys.exit(g.main())\n")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}   # a directory no brief governs
    for command, want in (("env -iS 'fly deploy'", 2), ("env -i ls", 0)):
        done = subprocess.run([sys.executable, "-c", program], input=json.dumps({"tool_input": {"command": command}}),
                              capture_output=True, text=True, timeout=60, check=False, env=env,
                              cwd=tmp_path)
        assert done.returncode == want, (command, done.returncode, done.stderr)
