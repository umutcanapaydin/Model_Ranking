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
    """A directory outside any repository, and a `$CLAUDE_PROJECT_DIR` with no brief: no deploy gate. (The
    deploy gate is the project root's own since the v7.1 upgrade security review's MAJOR-2, so an unset
    `$CLAUDE_PROJECT_DIR` would make the guard's own checkout, which has a brief, the project root.)"""
    where = tmp_path / "elsewhere"
    where.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(where))
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


# --- the v7.1 upgrade security review (B1, MAJOR-1, MAJOR-2, M1) and #282 --------------------------------

@pytest.fixture
def temp_dir(ungoverned: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`$TMPDIR` as the guard's process sees it: a directory of its own under the system temp directory."""
    where = ungoverned.parent / "T"
    where.mkdir()
    monkeypatch.setenv("TMPDIR", str(where))
    return where


@pytest.mark.parametrize("command", [
    "rm -rf $TMPDIR/{up}Users/x/model_ranking",
    'rm -rf "${TMPDIR}/{up}Users/x"',
    'rm -rf "$TMPDIR/$unset"', 'rm -rf "$TMPDIR"', 'rm -rf "$TMPDIR/"', "rm -rf ${TMPDIR:-/}x",
    'TMPDIR=/x; rm -rf "$TMPDIR"', 'TMPDIR=/x; rm -rf "$TMPDIR/sub"', "export TMPDIR=$HOME && rm -rf $TMPDIR",
    "export TMPDIR=$HOME && rm -rf $TMPDIR/sub", "unset TMPDIR; rm -rf $TMPDIR/x",
    'd=$(mktemp -d); rm -rf "$d/../.."', 'd=$(mktemp -d)/../../../../Users/x; rm -rf "$d"',
    "d=$(mktemp -d; echo /Users/x); rm -rf $d", 'd=$(mktemp -d); rm -rf "${d}x"', 'd=$(mktemp -d); rm -rf "/x/$d"',
    "find $TMPDIR/{up}Users/x -delete",
])
def test_rm_rf_of_a_path_that_only_starts_with_a_temp_variable_is_refused(guard: ModuleType, temp_dir: Path,
                                                                          ungoverned: Path, command: str) -> None:
    """The v7.1 upgrade security review's B1: `$TMPDIR` or a `mktemp` variable at the start of a target made it
    scratch, wherever the rest led. The target is resolved where it lands now, and a variable this text
    assigned something else, or one it never assigned, is not scratch. `{up}` climbs past the root from
    wherever pytest put `$TMPDIR` (one level deeper under xdist), so the target always lands outside it."""
    command = command.replace("{up}", "../" * (len(temp_dir.resolve().parts) + 1))
    why = _bash(guard, command, ungoverned)
    assert why and "destructive" in why, (command, why)


@pytest.mark.parametrize("command", [
    'd=$(mktemp -d); rm -rf "$d"', 'rm -rf "$TMPDIR/foo"', "rm -rf $TMPDIR/foo/bar", "rm -rf ${TMPDIR}/foo",
    'd=$(mktemp -d) && rm -rf "$d/sub"', "D=`mktemp -d`; rm -rf $D", 'TMPDIR=$(mktemp -d); rm -rf "$TMPDIR/x"',
    "find $TMPDIR/foo -delete",
])
def test_rm_rf_of_a_temp_variables_own_scratch_is_allowed(guard: ModuleType, temp_dir: Path, ungoverned: Path,
                                                          command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize(("command", "where"), [
    ("rm -rf .", "."), ("rm -rf .git", "."), ("rm -rf ios", "."), ("rm -rf ./ios ./.git", "."), ("rm -rf ../", "."),
    ("rm -rf ..", "ios"), ("rm -fr ../repo", "ios"), ("find . -delete", "."), ("find ios -delete", "."),
])
def test_rm_rf_in_above_or_of_a_work_tree_under_the_temp_directory_is_refused(guard: ModuleType, repo: Path,
                                                                              command: str, where: str) -> None:
    """The v7.1 upgrade security review's MAJOR-1 (round 1's M2): this project's work trees and review seats
    live under the system temp directory, so "under a temp directory" let `rm -rf .` remove one."""
    why = _bash(guard, command, repo / where)
    assert why and ("destructive" in why or "#282" in why), (command, why)


def test_rm_rf_of_a_temp_directory_that_holds_work_trees_is_refused(guard: ModuleType, repo: Path,
                                                                    ungoverned: Path) -> None:
    """`rm -rf /private/tmp/claude-501` held every session's tree; here the directory holding `repo`."""
    why = _bash(guard, f"rm -rf {repo.parent}", ungoverned)
    assert why and "destructive" in why, why
    why = _bash(guard, f"rm -rf {repo.parent}/elsewhere {repo}", ungoverned)
    assert why and "destructive" in why, why


@pytest.mark.parametrize(("command", "where"), [
    ("rm -r .", "."), ("rm -R ./", "."), ("rm -r ..", "ios"), ("rm --recursive ../../repo", "ios"),
    ("mv ../repo ../gone", "."), ("mv . ../gone", "."), ("mv -t /x ../repo", "."), ("cd .. && mv repo gone", "."),
    ("git rm -r .", "."), ("git mv ../../repo ../../gone", "ios"),
])
def test_removing_or_moving_what_holds_a_work_trees_claude_or_githooks_is_refused(guard: ModuleType, repo: Path,
                                                                                  command: str, where: str) -> None:
    """#282: the owner's-directory rule asked only whether a path lay inside `.claude/` or `.githooks/`, so a
    directory that holds them -- the work tree's root, or a directory above it -- could be removed or moved."""
    why = _bash(guard, command, repo / where)
    assert why and "#282" in why, (command, why)


@pytest.fixture
def seat(repo: Path) -> Path:
    """A throwaway worktree under `.claude/worktrees/`, a full checkout with its own `.claude/` and `.githooks/`."""
    tree = repo / ".claude" / "worktrees" / "seat"
    for d in ("src", ".claude/hooks", ".githooks"):
        (tree / d).mkdir(parents=True)
    (tree / ".git").write_text("gitdir: ../../../.git/worktrees/seat\n", encoding="utf-8")
    return tree


@pytest.mark.parametrize("command", [
    "rm -rf .claude/worktrees/seat", "rm -r .claude/worktrees/seat", "rm -rf .claude/worktrees/seat/src",
    "git worktree remove .claude/worktrees/seat", "git worktree remove --force .claude/worktrees/seat",
    "rm -r ios", "mv ios/a ios/b", "git rm -r ios", "git mv ios mobile", "rm file.txt", "mv -t . ios/a",
    "git rm -r --cached .",
])
def test_a_throwaway_worktree_and_ordinary_paths_may_still_be_removed(guard: ModuleType, repo: Path, seat: Path,
                                                                      command: str) -> None:
    """MAJOR-1's exception: `.claude/worktrees/<name>`. `git worktree remove [--force] <path>` is how an agent
    drops its own throwaway worktree (git also prunes its record); the guard allows it."""
    assert _bash(guard, command, repo) is None, command


def test_rm_rf_of_scratch_that_holds_no_work_tree_is_allowed(guard: ModuleType, ungoverned: Path) -> None:
    """A `git archive` copy has the owner's directories and no `.git`: it is no work tree, so it is scratch."""
    copy = ungoverned.parent / "copy"
    for d in (".claude/hooks", ".githooks", "src"):
        (copy / d).mkdir(parents=True)
    (copy / ".claude" / "hooks" / "bash_guard.py").write_text("x\n", encoding="utf-8")
    assert _bash(guard, f"rm -rf {copy}", ungoverned) is None
    assert _bash(guard, "rm -rf build", ungoverned) is None


def _git_init(where: Path) -> None:
    subprocess.run(["git", "init", "-q", str(where)], check=True, capture_output=True, timeout=60)


@pytest.fixture
def foreign(ungoverned: Path) -> Path:
    """Another repository, with a brief and a `scripts/deploy_gate.py` of its own that leaves a mark when run."""
    other = ungoverned.parent / "foreign"
    (other / "docs").mkdir(parents=True)
    (other / "scripts").mkdir()
    (other / "docs" / "project-brief.md").write_text("- **Deploy commands:** `vercel deploy`\n", encoding="utf-8")
    (other / "scripts" / "deploy_gate.py").write_text(
        "import pathlib\npathlib.Path(__file__).with_name('RAN').write_text('x')\n", encoding="utf-8")
    _git_init(other)
    return other


@pytest.fixture
def gated(ungoverned: Path) -> Path:
    """The project root (`$CLAUDE_PROJECT_DIR`) with its own deploy gate."""
    (ungoverned / "scripts").mkdir()
    for name in ("deploy_gate.py", "brief_fields.py"):
        (ungoverned / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    return ungoverned


def test_another_repositorys_deploy_gate_never_runs(guard: ModuleType, gated: Path, foreign: Path) -> None:
    """The v7.1 upgrade security review's MAJOR-2: the hook ran `scripts/deploy_gate.py` from whatever work
    tree the call ran in, so a cloned repository's script ran on the next `ls`. Only the project's own gate
    runs; the tree the call runs in still governs, so its declared deploy is refused by that gate."""
    assert _bash(guard, "ls", foreign) is None
    why = _bash(guard, "vercel deploy", foreign)
    assert why and "is a deploy" in why, why
    assert not (foreign / "scripts" / "RAN").exists()


def test_another_repositorys_deploy_gate_never_runs_with_no_project_dir(guard: ModuleType, foreign: Path,
                                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """With `$CLAUDE_PROJECT_DIR` unset, the project root is the checkout the guard file lives in."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert _bash(guard, "ls", foreign) is None
    assert not (foreign / "scripts" / "RAN").exists()


def test_a_project_whose_gate_is_missing_refuses_even_from_another_repository(guard: ModuleType, foreign: Path,
                                                                              ungoverned: Path) -> None:
    """Fails closed: a brief declares deploys and the project root has no gate; another tree's is no stand-in."""
    why = _bash(guard, "ls", foreign)
    assert why and "has no scripts/deploy_gate.py" in why and str(ungoverned) in why, why
    assert not (foreign / "scripts" / "RAN").exists()


@pytest.mark.parametrize("command", [
    "git config alias.nuke 'reset --hard' && git nuke", "git -c alias.p='push --force' p",
    "git config --global alias.pm 'push origin main'", "git config alias.x '!rm -rf /'",
    "git config set alias.x '!git push origin main'", "git -c 'alias.y=!sh -c \"git reset --hard\"' y",
    "git config alias.c 'commit --no-verify'", "git --config-env=alias.z=ENV z",
    "ssh host rm -rf /srv/data", "ssh -p 22 -i key host 'git push origin main'", "ssh host rm -rf build",
    "ssh -o BatchMode=yes -- host git reset --hard", "ssh host 'fly deploy'",
])
def test_a_git_alias_and_an_ssh_command_are_judged_by_what_they_run(guard: ModuleType, ungoverned: Path,
                                                                     command: str) -> None:
    """The v7.1 upgrade security review's M1: `main` refused these as text and v7.1 let them through. An alias's
    value is judged as the git subcommand it names, or as shell text after `!`; `ssh`'s remote words as a
    command, a relative path in them resolved from the remote home, never a local temp directory."""
    assert _bash(guard, command, ungoverned), command


@pytest.mark.parametrize("command", [
    "git config alias.st status", "git config alias.lg 'log --oneline --graph'", "git -c alias.l='log -1' l",
    "git config user.name x", "git config --get alias.st", "git config --unset alias.st",
    "ssh host", "ssh host ls -la", "ssh -i key -p 2222 host uptime", "ssh host 'fly status'",
])
def test_a_harmless_git_alias_and_ssh_command_are_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command
