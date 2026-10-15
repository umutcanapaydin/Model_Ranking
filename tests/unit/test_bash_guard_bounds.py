"""The Bash guard's own bounds, and the project's rules it carries since the DevFlow v7.1 upgrade.

The M21 closure security seat's S2: the Bash guard's own time bound. Below Claude Code 2.1.295 a hook that
times out lets the call through, so the guard's own deadline is the only bound there. It is a timer thread
that writes the BLOCKED line and exits 2: it works where SIGALRM does not (Windows' Git Bash, which INSTALL.md
supports). It does not stop a long call into C that holds the interpreter, which runs to its end first (the
M21 closure fixes review's M6, measured); the hook's 30 s timeout and `onFailure` bound that. The tests slow
the reading with `time.sleep`, which lets the thread run.

The DevFlow v7.1 upgrade took v7.1's guard as the base and carried over every protection of the project's own
M21 guard that v7.1 lacks. Before it, three of them lived as `grep` patterns in `.claude/settings.json` (fly
deploy or destroy, the hosted engine's deploy script, and the shell rules v7.1 also holds); the rest lived in
the M21 guard. Each is a case below, judged in-process by `judge_call` (Bash) and `judge_file` (Write and
Edit), from a directory no brief governs, so the deploy gate never answers for them. The hooks themselves are
run as Claude Code runs them by `conformance/test-hook-claims.py` and `conformance/test-bash-guard.py`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD_DIR = ROOT / ".claude" / "hooks"
GUARD = GUARD_DIR / "bash_guard.py"
SETTINGS = ROOT / ".claude" / "settings.json"


def _run(setup: str, command: str) -> subprocess.CompletedProcess[str]:
    program = (f"import sys; sys.path.insert(0, {str(GUARD_DIR)!r}); import bash_guard as g\n{setup}\n"
               "sys.exit(g.main())\n")
    return subprocess.run([sys.executable, "-c", program], input=json.dumps({"tool_input": {"command": command}}),
                          capture_output=True, text=True, timeout=60, check=False)


#: A reading that takes longer than the deadline, so the bound, not the race with a fast reading, decides.
SLOW = "import time\ng.DEADLINE_S = 0.2\ng.judge_text = lambda text, depth=0: time.sleep(3)"


def test_a_reading_past_the_deadline_blocks_even_git_status() -> None:
    """Mutant G2 (the timer never started) survived every gate."""
    done = _run(SLOW, "git status")
    assert done.returncode == 2 and "BLOCKED" in done.stderr, done


def test_the_deadline_holds_where_there_is_no_sigalrm() -> None:
    """On Windows `signal.setitimer` does not exist; the guard then blocked every call, `git status` too."""
    setup = "import signal\nfor name in ('setitimer', 'SIGALRM', 'ITIMER_REAL', 'alarm'):\n    if hasattr(signal, name): delattr(signal, name)"
    assert _run(setup, "git status").returncode == 0
    assert _run(setup + "\n" + SLOW, "git status").returncode == 2


# --- the project's rules, in the v7.1 guard ------------------------------------------------------------

@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bash_guard_under_test", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ungoverned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory outside any repository, with no `$CLAUDE_PROJECT_DIR`: no brief, so no deploy gate."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    where = tmp_path / "elsewhere"
    where.mkdir()
    return where


@pytest.fixture
def repo(ungoverned: Path) -> Path:
    """A work tree (a `.git` directory) with the owner's `.claude/` and `.githooks/`, and a subdirectory."""
    tree = ungoverned.parent / "repo"
    for d in (".git", ".claude/hooks", ".claude/worktrees", ".githooks", "ios"):
        (tree / d).mkdir(parents=True)
    return tree


def _bash(guard: ModuleType, command: str, cwd: Path) -> str | None:
    why: str | None = guard.judge_call({"tool_input": {"command": command}, "cwd": str(cwd)})
    return why


@pytest.mark.parametrize("command", [
    "fly deploy", "fly deploy --remote-only", "flyctl deploy", "fly apps destroy model-ranking",
    "flyctl apps destroy model-ranking", "/usr/local/bin/fly deploy", "FLY_API_TOKEN=x fly deploy",
    "env fly deploy", "sudo fly deploy", "(fly deploy)", "$(fly deploy)", "bash -c 'fly deploy'",
    "eval 'fly deploy'", "a=fly; $a deploy", "fly launch", "fly secrets set A=b", "fly scale count 0",
    "fly machine stop x", "fly ssh console", "echo deploy | xargs fly", "git status\nfly deploy",
])
def test_fly_that_may_change_the_hosted_engine_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """D-185: deploying or destroying the hosted engine is the owner's, whatever the deploy gate says. The rule
    was a `grep` in settings.json's Bash hook before v7.1; it is code in the guard now."""
    why = _bash(guard, command, ungoverned)
    assert why and "D-185" in why, (command, why)


@pytest.mark.parametrize("command", [
    "fly status", "fly logs -a model-ranking", "fly auth whoami", "fly apps list", "fly version",
    "git commit -m 'fly deploy notes'", "echo 'fly deploy'", "gh issue comment 1 --body 'run fly deploy'",
])
def test_fly_that_only_reads_or_only_names_it_is_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize("command", [
    "scripts/deploy_hosted_engine.sh", "./scripts/deploy_hosted_engine.sh --prod",
    "bash scripts/deploy_hosted_engine.sh", "source scripts/deploy_hosted_engine.sh",
    "MODEL_RANKING_SERVED=x scripts/deploy_hosted_engine.sh",
    "scripts/deploy_hosted_engine.sh --dry-run && scripts/deploy_hosted_engine.sh",
    "scripts/deploy_hosted_engine.sh --dry-run --force", "echo x | xargs scripts/deploy_hosted_engine.sh --dry-run",
])
def test_the_deploy_script_without_exactly_dry_run_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """D-185: an agent may run `scripts/deploy_hosted_engine.sh --dry-run` and nothing else of it."""
    why = _bash(guard, command, ungoverned)
    assert why and "D-185" in why, (command, why)


@pytest.mark.parametrize("command", [
    "scripts/deploy_hosted_engine.sh --dry-run", "bash scripts/deploy_hosted_engine.sh --dry-run",
    "grep -n deploy_hosted_engine.sh docs/release-testflight.md",
])
def test_the_deploy_scripts_dry_run_is_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize("command", [
    # what settings.json's `grep` patterns refused before v7.1: each must still be refused by the file
    "git push origin main", "git push origin master", "git push o trunk", "git push origin HEAD:refs/heads/main",
    "git reset --hard HEAD~1", "git push --force origin x", "git push -uf origin x", "git push --mirror o",
    "git push --mi o", "git push origin +x", "git clean -fd", "git checkout -- .", "git checkout .",
    "git restore src/a.py", "git restore --staged --worktree a",
])
def test_the_rules_settings_json_held_as_text_are_refused_by_the_file(guard: ModuleType, ungoverned: Path,
                                                                      command: str) -> None:
    assert _bash(guard, command, ungoverned), command


@pytest.mark.parametrize(("command", "where"), [
    ("echo x > .claude/settings.json", "."), ("echo x >> .githooks/pre-push", "."),
    ("printf x | tee .claude/hooks/bash_guard.py", "."), ("cp x .githooks/pre-commit", "."),
    ("cp -t .claude/hooks x.py", "."), ("install -vt .githooks x", "."), ("dd if=x of=.claude/settings.json", "."),
    ("sed -i '' 's/a/b/' .claude/settings.json", "."), ("cp x .CLAUDE/settings.json", "."),
    ("rm .claude/hooks/bash_guard.py", "."), ("rm -rf .claude/hooks", "."), ("find .claude -delete", "."),
    ("echo x >& .claude/x", "."), ("d=.claude; echo x > $d/settings.json", "."),
    ("cd ios && cp x ../.claude/settings.json", "."), ("cp x ../.githooks/y", "ios"),
    ("cd ios; cd ..; touch .githooks/x", "."), ("(cd ios) && touch .githooks/x", "."),
])
def test_a_write_into_a_work_trees_claude_or_githooks_is_refused(guard: ModuleType, repo: Path, command: str,
                                                                  where: str) -> None:
    """The M21 closure security seat's S3: the owner's hooks and settings, resolved from the cwd and each `cd`."""
    why = _bash(guard, command, repo / where)
    assert why and ".claude/ and .githooks/" in why, (command, why)


def test_git_c_into_a_work_tree_is_followed(guard: ModuleType, repo: Path, ungoverned: Path) -> None:
    why = _bash(guard, f"git -C {repo} rm .githooks/pre-push", ungoverned)
    assert why and ".claude/ and .githooks/" in why, why


@pytest.mark.parametrize("command", [
    "cat .claude/settings.json", "git add .claude/hooks/bash_guard.py", "cp -t /tmp/out .claude/settings.json",
    "rsync -t .claude/settings.json /tmp/out", "cd .claude && ls && cd .. && echo x > notes.txt",
    # v7.1's scratch: a worktree under `.claude/worktrees/` may be removed
    "rm -rf .claude/worktrees/agent-x",
])
def test_reading_the_owners_directories_is_allowed(guard: ModuleType, repo: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


def test_a_claude_directory_with_no_work_tree_above_it_is_not_the_owners(guard: ModuleType, ungoverned: Path) -> None:
    """Claude Code's own `~/.claude` has no `.git` above it."""
    (ungoverned / ".claude").mkdir()
    assert _bash(guard, "echo x > .claude/notes.md", ungoverned) is None


def test_rm_rf_is_scratch_only_from_every_directory_the_command_runs_in(guard: ModuleType, ungoverned: Path) -> None:
    """v7.1 resolved a relative `rm -rf` target from the payload's cwd alone; a `cd` out of the temp directory
    first made `rm -rf build` look like scratch. The project's `cd` reading closes that."""
    assert _bash(guard, "rm -rf build", ungoverned) is None
    why = _bash(guard, "cd / && rm -rf build", ungoverned)
    assert why and "destructive" in why, why


@pytest.mark.parametrize(("path", "where", "refused"), [
    (".claude/settings.json", ".", True), (".githooks/pre-push", ".", True), ("../.claude/hooks/x.py", "ios", True),
    (".CLAUDE/settings.json", ".", True), (".env", ".", True), ("cfg/.env.prod", ".", True), (".envrc", ".", True),
    (".env.example", ".", False), ("src/config.env.py", ".", False), ("ios/App.swift", ".", False),
    (".githooks/x", "ios", False),
])
def test_the_write_and_edit_hook_refuses_the_owners_directories_and_secrets(guard: ModuleType, repo: Path, path: str,
                                                                            where: str, refused: bool) -> None:
    why = guard.judge_file({"tool_input": {"file_path": path}, "cwd": str(repo / where)})
    assert bool(why) is refused, (path, why)


def test_the_write_hooks_main_reads_write_mode(guard: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    payload = json.dumps({"tool_input": {"file_path": ".claude/settings.json"}, "cwd": str(repo)}).encode()
    monkeypatch.setattr(sys, "stdin", type("In", (), {"buffer": type("B", (), {"read": lambda self: payload})()})())
    assert guard.main(["--write"]) == 2
    assert ".claude/ and .githooks/" in capsys.readouterr().err


@pytest.mark.parametrize("command", [
    "git push --no-verify -u origin x", "git push --no-veri origin x", "git commit -n -m x",
    "git -c core.hooksPath=/dev/null push origin x", "git --config-env=core.hooksPath=X push origin x",
])
def test_a_skipped_hook_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    why = _bash(guard, command, ungoverned)
    assert why and "--no-verify" in why, (command, why)


# --- the hooks in settings.json -------------------------------------------------------------------------

def _hooks() -> dict[str, str]:
    cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out = {}
    for event, groups in cfg["hooks"].items():
        for group in groups:
            out[f"{event}:{group.get('matcher', '*')}"] = group["hooks"][0]["command"]
    return out


def test_both_pretooluse_hooks_run_the_guard_under_one_current_pin() -> None:
    """One refusal for both hooks: a changed guard blocks every command and every write until the owner runs
    `make guard-pin` and restarts Claude Code."""
    hooks = _hooks()
    bash, write = hooks["PreToolUse:Bash"], hooks["PreToolUse:Write|Edit|MultiEdit"]
    have = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    for hook in (bash, write):
        assert "bash_guard.py" in hook
        assert set(re.findall(r'\[ "\$h" = "([0-9a-f]{64})" \]', hook)) == {have}
        assert f"sha256 {have[:12]}" in hook and "restart Claude Code" in hook
    assert '"$g" --write' in write and '"$g" --write' not in bash


def test_every_hook_interpreter_runs_isolated() -> None:
    """`python3 -I -S`: neither a module where a hook runs nor a site-packages `.pth` changes what it imports."""
    for name, hook in _hooks().items():
        for start in re.findall(r'"\$py"\s+(?!\])\S+(?:\s+\S+)?', hook):
            assert start.split()[1:3] == ["-I", "-S"], (name, start)


def test_the_settings_keep_the_project_attribution_and_exact_allow_targets() -> None:
    cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert cfg["attribution"] == {"commit": "", "pr": ""}
    assert not [r for r in cfg["permissions"]["allow"] if re.match(r"^(Bash|PowerShell)\(make\s+\S+:\*\)$", r)]
