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
import os
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
def ungoverned(guard: ModuleType, tmp_path: Path, tmp_path_factory: pytest.TempPathFactory,
               monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory outside any repository, a `$CLAUDE_PROJECT_DIR` with no brief, and a guard checkout with no
    brief: no deploy gate. Since DevFlow v7.1.2 (D-205) the gate is always the guard's own checkout's (`OWN`,
    the v7.1 upgrade security review's MAJOR-2 as DevFlow closed it), and that checkout's brief judges a call
    from any directory, so `OWN` is pointed at an empty directory beside the test's own."""
    where = tmp_path / "elsewhere"
    where.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(where))
    monkeypatch.setattr(guard, "OWN", str(tmp_path_factory.mktemp("own")))
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


@pytest.mark.parametrize("command", [
    'rm -rf "$(pwd)"', 'rm -rf "$(pwd -P)"', 'rm -rf "$( pwd )"',
    'pwd() { echo ~; }; rm -rf "$(pwd)"', 'function pwd { echo ~; }; rm -rf "$(pwd)"',
    'pwd() { echo ~; }\nrm -rf "$(pwd)"', "alias pwd='echo ~'\nrm -rf \"$(pwd)\"",
    'pwd() { echo ~; }; find "$(pwd)" -delete', 'pwd() { echo ~; }; rm -rf "$(pwd)/Desktop"',
    'p""wd() { echo ~; }; rm -rf "$(pwd)"', "'pwd'() { echo ~; }; rm -rf \"$(pwd)\"",
    "alias p''wd='echo ~'\nrm -rf \"$(pwd)\"", 'eval "p""wd() { echo ~; }"; rm -rf "$(pwd)"',
    'f=pwd; eval "$f() { echo ~; }"; rm -rf "$(pwd)"', "eval \"$(printf 'p%sd() { echo ~; }' w)\"; rm -rf \"$(pwd)\"",
    'enable -n pwd; PATH=/tmp/evil:$PATH; rm -rf "$(pwd)"', 'enable -n pwd; hash -p /tmp/evil/pwd pwd; rm -rf "$(pwd)"',
    'disable pwd; PATH=/tmp/evil:$PATH; rm -rf "$(pwd)"', "functions[pwd]='echo ~'; rm -rf \"$(pwd)\"",
    'mktemp() { echo ~; }; d=$(mktemp -d); rm -rf "$d"', 'function mktemp { echo ~; }; d=$(mktemp -d); rm -rf "$d"',
    "alias mktemp='echo ~'\nd=$(mktemp -d); rm -rf \"$d\"",
])
def test_pwd_is_never_read_as_scratch_and_a_redefined_mktemp_is_not_trusted(guard: ModuleType, temp_dir: Path,
                                                                            ungoverned: Path, command: str) -> None:
    """The v7.1.2 upgrade security review's B1, B1-R and M1. v7.1.2 read `$(pwd)` as the directory the command
    runs in, and a command can redefine `pwd` in more ways than any pattern lists (a quoted name, `eval`,
    `enable -n`, zsh's `functions[pwd]=`), so `$(pwd)` stays a substitution the guard cannot name, as it was before
    v7.1.2, even from inside scratch. A `mktemp` result is a new directory unless the same command defines
    `mktemp`."""
    inside = temp_dir / "work"
    inside.mkdir()
    assert _bash(guard, command, inside), command
    assert _bash(guard, "rm -rf .", inside) is None, "the scratch directory itself, by `.`, stays scratch"


@pytest.mark.parametrize("command", [
    "rm -rf /var/folders/zz", "rm -rf /private/var/folders/zz/x", "find /var/folders/zz -delete",
    "rm -r /var/folders/qf/abc/C", "rm -rf /var/folders",
])
def test_the_rest_of_var_folders_is_not_scratch(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """The v7.1.2 upgrade security review's M4: v7.1.2 counted all of `/var/folders` as scratch, and beside each
    user's `T/` it holds macOS's per-user state and caches. Only `$TMPDIR` and the interpreter's own temp directory
    there are scratch."""
    why = _bash(guard, command, ungoverned)
    assert why, command


@pytest.mark.parametrize(("command", "where"), [
    ("rm -rf .", "."), ("rm -rf .git", "."), ("rm -rf ios", "."), ("rm -rf ./ios ./.git", "."), ("rm -rf ../", "."),
    ("rm -rf ..", "ios"), ("rm -fr ../repo", "ios"), ("find . -delete", "."), ("find ios -delete", "."),
    # DevFlow v7.1.2: `rm -r` without `-f` meets the scratch rule too -- Claude Code runs Bash with no terminal,
    # so it never prompts and removes what `rm -rf` removes (it was allowed below through v7.1.1).
    ("rm -r ios", "."),
])
def test_rm_rf_in_above_or_of_a_work_tree_under_the_temp_directory_is_refused(guard: ModuleType, repo: Path,
                                                                              command: str, where: str) -> None:
    """The v7.1 upgrade security review's MAJOR-1 (round 1's M2): this project's work trees and review seats
    live under the system temp directory, so "under a temp directory" let `rm -rf .` remove one. DevFlow v7.1.2
    refuses a target that is or holds a work tree in words of its own (HOLDS_REPO)."""
    why = _bash(guard, command, repo / where)
    assert why and any(w in why for w in ("destructive", "#282", "holds a git work tree")), (command, why)


def test_rm_rf_of_a_temp_directory_that_holds_work_trees_is_refused(guard: ModuleType, repo: Path,
                                                                    ungoverned: Path) -> None:
    """`rm -rf /private/tmp/claude-501` held every session's tree; here the directory holding `repo`. DevFlow
    v7.1.2 refuses a scratch target that holds a work tree in words of its own (HOLDS_REPO)."""
    held = ("destructive", "holds a git work tree")
    why = _bash(guard, f"rm -rf {repo.parent}", ungoverned)
    assert why and any(w in why for w in held), why
    why = _bash(guard, f"rm -rf {repo.parent}/elsewhere {repo}", ungoverned)
    assert why and any(w in why for w in held), why


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
    "mv ios/a ios/b", "git rm -r ios", "git mv ios mobile", "rm file.txt", "mv -t . ios/a",
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


@pytest.mark.parametrize("command", [
    'HOME=$(mktemp -d) true && rm -rf "$HOME"', 'TMPDIR=$(mktemp -d) make test; rm -rf "$TMPDIR"',
    "PWD=/tmp/x rm -rf $PWD", 'd=$(mktemp -d) env; rm -rf "$d"', "X=/tmp/x true; rm -rf $X",
    'TMPDIR=$(mktemp -d) rm -rf "$TMPDIR"',
])
def test_an_assignment_before_a_program_sets_nothing_for_its_words_or_later_commands(
        guard: ModuleType, temp_dir: Path, ungoverned: Path, command: str) -> None:
    """The v7.1 upgrade security rereview's B1-R: `NAME=value cmd` puts NAME in that one program's environment
    only. The shell expands the command's own words before it applies it, and no later command sees it, so the
    name's value from there on is not known, and a target built from it is not scratch."""
    why = _bash(guard, command, ungoverned)
    assert why and "destructive" in why, (command, why)


@pytest.mark.parametrize("command", ['d=$(mktemp -d); X=1 true; rm -rf "$d"', "X=/tmp/x; rm -rf $TMPDIR/foo"])
def test_a_plain_assignment_still_holds_for_later_commands(guard: ModuleType, temp_dir: Path, ungoverned: Path,
                                                           command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


def test_rm_rf_of_scratch_too_large_to_walk_is_refused(guard: ModuleType, temp_dir: Path, ungoverned: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """The rereview's R3 (mutant N8): a temp directory the guard cannot walk within its budget may hold a work
    tree, so `rm -rf` of it is refused, not allowed."""
    big = temp_dir / "big"
    for i in range(3):
        (big / f"d{i}").mkdir(parents=True)
    assert _bash(guard, f"rm -rf {big}", ungoverned) is None
    monkeypatch.setattr(guard, "MAX_WALK", 2)
    why = _bash(guard, f"rm -rf {big}", ungoverned)
    assert why and ("destructive" in why or "more files than this guard looks through" in why), why


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
def gated(guard: ModuleType, ungoverned: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The project root (`$CLAUDE_PROJECT_DIR`, and the guard's own checkout, `OWN`) with its own deploy gate."""
    (ungoverned / "scripts").mkdir()
    for name in ("deploy_gate.py", "brief_fields.py"):
        (ungoverned / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    monkeypatch.setattr(guard, "OWN", str(ungoverned))
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
    monkeypatch.setattr(guard, "OWN", str(GUARD.resolve().parents[2]))
    assert _bash(guard, "ls", foreign) is None
    assert not (foreign / "scripts" / "RAN").exists()


def test_a_project_whose_gate_is_missing_refuses_even_from_another_repository(guard: ModuleType, foreign: Path,
                                                                              ungoverned: Path) -> None:
    """Fails closed: a brief declares deploys and the project root has no gate; another tree's is no stand-in.
    Since DevFlow v7.1.2 the project root whose gate runs is the guard's own checkout (`OWN`)."""
    why = _bash(guard, "ls", foreign)
    assert why and "has no scripts/deploy_gate.py" in why and str(guard.OWN) in why, why
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


# --- the owner's guard patch of run golden-night (D-206 clause 9): #285 and #286 --------------------------------

@pytest.mark.parametrize(("command", "where"), [
    ("git config --edit", "."), ("git config -e", "."), ("git config --global --edit", "."), ("git config edit", "."),
    ("git config --ed", "."), ("git config --edit=x", "."), ("git config -le", "."),
    ("git config --file .git/config -e", "."), ("git config --global edit", "."),
    ("git -c alias.x='config --edit' x", "."), ("GIT_EDITOR=true git config --edit", "."),
    ("bash -c 'git config -e'", "."), ("git -C ios config --edit", "."),
    ("echo '[core] hooksPath = /dev/null' >> .git/config", "."), ("printf x > .git/hooks/pre-commit", "."),
    ("echo x >| .git/config", "."), ("echo x &> .git/hooks/pre-push", "."), ("echo x > ./.git/../.git/config", "."),
    ("tee -a .git/config < x", "."), ("cat x | tee .git/hooks/commit-msg", "."), ("cp x .git/hooks/pre-push", "."),
    ("cp -t .git/hooks x", "."), ("mv x .git/config", "."), ("install -m 755 x .git/hooks/pre-push", "."),
    ("ln -s /tmp/x .git/hooks/pre-commit", "."), ("chmod +x .git/hooks/pre-push", "."),
    ("touch .git/hooks/post-checkout", "."), ("dd if=x of=.git/config", "."),
    ("sed -i '' 's/a/b/' .git/config", "."), ("perl -pi -e 's/a/b/' .git/config", "."),
    ("echo x > .GIT/CONFIG", "."), ("echo x > .git/config.worktree", "."),
    ("echo x > .git/worktrees/w/config.worktree", "."), ("cd ios && echo x >> ../.git/config", "."),
    ("echo x >> ../.git/config", "ios"), ("bash -c 'echo x >> .git/config'", "."), ("d=.git; echo x > $d/config", "."),
    ("cp x ~/.gitconfig", "."), ("echo x >> ~/.gitconfig", "."), ("cat x | tee -a ~/.gitconfig", "."),
    ("mv x $HOME/.gitconfig", "."), ("echo x > ~/.config/git/config", "."),
    ("echo x >> /elsewhere/clone/.git/config", "."), ("cp -r myhooks/hooks .git/", "."), ("mv x .git", "."),
    ("rsync -a hooks/ .git/hooks/", "."), ("cp -r myhooks/hooks /elsewhere/clone/.git/", "."),
])
def test_git_config_edit_and_a_write_into_gits_config_or_hooks_are_refused(guard: ModuleType, repo: Path,
                                                                           command: str, where: str) -> None:
    """#285: the guard read `git config <key> <value>` (core.hooksPath, aliases, keys git runs) but not an editor
    git opens on the config, nor a file written straight into `.git/config`, `.git/hooks/` or `~/.gitconfig`:
    either sets `core.hooksPath` or a hook, switching the commit and push gates off for every later command."""
    why = _bash(guard, command, repo / where)
    assert why and "#285" in why, (command, why)


@pytest.mark.parametrize("command", [
    "git config user.name x", "git config --get core.hooksPath", "git config --list", "git config -l",
    "git config --get-regexp edit", "git config user.email e@x", "cat .git/config", "grep url .git/config",
    "cp .git/config /tmp/config.bak", "cp ~/.gitconfig /tmp/gitconfig.bak", "rm -f .git/index.lock",
    "echo x > notes/git-config.md", "git commit -m 'git config --edit and .git/config'", "ls .git/hooks",
])
def test_reading_gits_config_and_hooks_is_allowed(guard: ModuleType, repo: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


def test_a_git_directory_not_named_dot_git_is_held_too(guard: ModuleType, ungoverned: Path) -> None:
    """`git init --separate-git-dir`: the work tree's `.git` is a file naming a git directory of another name, whose
    `config` and `hooks/` git reads as it reads `.git/config`."""
    tree, gitdir = ungoverned.parent / "sep", ungoverned.parent / "sepgit"
    tree.mkdir()
    (gitdir / "hooks").mkdir(parents=True)
    (tree / ".git").write_text("gitdir: ../sepgit\n", encoding="utf-8")
    for command in ("echo x >> ../sepgit/config", "cp x ../sepgit/hooks/pre-commit", "cp -r h ../sepgit/"):
        why = _bash(guard, command, tree)
        assert why and "#285" in why, (command, why)


def test_core_hooks_path_set_by_git_config_stays_refused(guard: ModuleType, repo: Path) -> None:
    for command in ("git config core.hooksPath /dev/null", "git config --global core.hooksPath x",
                    "git config --unset core.hooksPath"):
        why = _bash(guard, command, repo)
        assert why and "--no-verify" in why, (command, why)


def _git(where: Path, *args: str) -> str:
    """git as a test runs it: none of a hook's `GIT_*` (a commit-msg hook exports `GIT_DIR`), a fixed identity."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false", *args],
                          cwd=where, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 0, (args, done.stderr)
    return done.stdout


@pytest.fixture
def live(ungoverned: Path) -> Path:
    """A real repository with a clean, live worktree at `.claude/worktrees/w` (its `.git` file names a gitdir that
    exists), a nested one at `w/.claude/worktrees/n`, and `.claude/worktrees/` ignored, as Claude Code leaves it."""
    tree = ungoverned.parent / "live"
    (tree / "ios").mkdir(parents=True)
    _git(tree, "init", "-q")
    (tree / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (tree / "a.txt").write_text("a\n", encoding="utf-8")
    (tree / "ios" / "b.txt").write_text("b\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-qm", "base")
    _git(tree, "worktree", "add", "-q", str(tree / ".claude" / "worktrees" / "w"), "-b", "w")
    _git(tree, "worktree", "add", "-q", str(tree / ".claude" / "worktrees" / "w" / ".claude" / "worktrees" / "n"), "-b", "n")
    return tree


#: The ways to remove `.claude/worktrees/w`, each from the repository's root.
REMOVALS = [
    "rm -rf .claude/worktrees/w", "rm -r .claude/worktrees/w", "rm -R -f .claude/worktrees/w/",
    "git worktree remove .claude/worktrees/w", "git worktree remove --force .claude/worktrees/w",
    "git worktree remove -f -f .claude/worktrees/w", "git worktree remove --force w",
    "git -C ios worktree remove --force ../.claude/worktrees/w", "cd .claude && rm -rf worktrees/w",
    "rm -rf $PWD/.claude/worktrees/w", "find .claude/worktrees/w -delete",
]


@pytest.mark.parametrize("dirt", ["untracked", "modified", "staged"])
@pytest.mark.parametrize("command", [*REMOVALS, "rm -rf .claude/worktrees/w/ios",
                                     "git -c alias.wr='worktree remove' wr -f w"])
def test_removing_a_worktree_with_uncommitted_work_is_refused(guard: ModuleType, live: Path, command: str,
                                                              dirt: str) -> None:
    """#286: `.claude/worktrees/<name>` is scratch, and `rm -r`, `find -delete` and `git worktree remove --force`
    deleted one holding uncommitted work -- every review seat and implementer works in one (D-174)."""
    w = live / ".claude" / "worktrees" / "w"
    if dirt == "untracked":
        (w / "review.md").write_text("findings\n", encoding="utf-8")
    else:
        (w / "a.txt").write_text("changed\n", encoding="utf-8")
        if dirt == "staged":
            _git(w, "add", "a.txt")
    why = _bash(guard, command, live)
    assert why and "#286" in why and "uncommitted work" in why, (command, why)


@pytest.mark.parametrize("command", REMOVALS)
def test_removing_a_clean_worktree_is_allowed(guard: ModuleType, live: Path, command: str) -> None:
    assert _bash(guard, command, live) is None, command


def test_a_dirty_worktree_nested_below_the_one_removed_is_refused(guard: ModuleType, live: Path) -> None:
    nested = live / ".claude" / "worktrees" / "w" / ".claude" / "worktrees" / "n"
    (nested / "work.txt").write_text("x\n", encoding="utf-8")
    for command in ("rm -rf .claude/worktrees/w", "git worktree remove --force .claude/worktrees/w"):
        why = _bash(guard, command, live)
        assert why and "#286" in why and str(nested.resolve()) in why, (command, why)


def test_a_dirty_worktree_is_refused_by_its_absolute_path_from_anywhere(guard: ModuleType, live: Path,
                                                                        ungoverned: Path) -> None:
    w = (live / ".claude" / "worktrees" / "w").resolve()
    (w / "review.md").write_text("findings\n", encoding="utf-8")
    for command in (f"rm -rf {w}", f"git -C {live} worktree remove --force {w}"):
        why = _bash(guard, command, ungoverned)
        assert why and "#286" in why, (command, why)


def test_a_dirty_worktree_outside_claude_worktrees_is_not_force_removed(guard: ModuleType, live: Path,
                                                                        ungoverned: Path) -> None:
    other = ungoverned.parent / "other-wt"
    _git(live, "worktree", "add", "-q", str(other), "-b", "other")
    assert _bash(guard, f"git worktree remove --force {other}", live) is None
    (other / "new.txt").write_text("x\n", encoding="utf-8")
    why = _bash(guard, f"git worktree remove --force {other}", live)
    assert why and "#286" in why, why
    why = _bash(guard, "git worktree remove --force other-wt", live)
    assert why and "#286" in why, why


@pytest.mark.parametrize("how", ["no budget", "no git"])
def test_a_live_worktree_whose_status_cannot_be_measured_is_not_removed(guard: ModuleType, live: Path,
                                                                        monkeypatch: pytest.MonkeyPatch,
                                                                        how: str) -> None:
    if how == "no budget":
        monkeypatch.setattr(guard, "STATUS_S", 0.0)
    else:
        monkeypatch.setenv("PATH", str(live / "ios"))
    for command in ("rm -rf .claude/worktrees/w", "git worktree remove --force .claude/worktrees/w"):
        why = _bash(guard, command, live)
        assert why and "#286" in why and "could not" in why, (command, why)


def test_a_worktree_whose_git_file_cannot_be_read_is_not_removed(guard: ModuleType, live: Path) -> None:
    odd = live / ".claude" / "worktrees" / "odd"
    odd.mkdir()
    (odd / ".git").write_text("not a gitdir line\n", encoding="utf-8")
    why = _bash(guard, "rm -rf .claude/worktrees/odd", live)
    assert why and "#286" in why, why


@pytest.mark.parametrize("command", [
    "rm -rf .claude/worktrees/gone", "git worktree remove --force .claude/worktrees/gone", "rm -rf .claude/worktrees/none",
    "rm -rf .claude/worktrees/plain",
])
def test_a_worktree_whose_gitdir_is_gone_or_a_plain_directory_is_removed_as_before(guard: ModuleType, live: Path,
                                                                                   command: str) -> None:
    """A `.git` file naming a gitdir that does not exist is no live worktree (the `seat` fixture above), and a
    directory with no `.git` holds no git work: both stay scratch."""
    gone = live / ".claude" / "worktrees" / "gone"
    gone.mkdir()
    (gone / ".git").write_text("gitdir: /nowhere/.git/worktrees/gone\n", encoding="utf-8")
    (gone / "left.txt").write_text("x\n", encoding="utf-8")
    (live / ".claude" / "worktrees" / "plain" / "build").mkdir(parents=True)
    assert _bash(guard, command, live) is None, command


@pytest.mark.parametrize("command", [
    "git worktree remove --force \"$W\"", "git worktree remove --force .claude/worktrees/*",
    "echo .claude/worktrees/w | xargs git worktree remove --force",
])
def test_a_worktree_removal_whose_path_this_cannot_read_is_refused(guard: ModuleType, live: Path, command: str) -> None:
    why = _bash(guard, command, live)
    assert why and "#286" in why, (command, why)


# --- the owner-bundle security review of run golden-night: P1, M1 and M2 ---------------------------------------
@pytest.mark.parametrize("command", [
    "bash -c 'rm -rf ~' --help", "sh -c 'git push --force origin main' --version", "bash -c 'fly deploy' --help",
    "zsh -c 'rm -rf ~' --version --help",
    "bash --help -c 'rm -rf ~'", "bash -c 'git config --edit' --help",
])
def test_a_shell_given_help_or_version_beside_a_command_still_has_the_command_read(guard: ModuleType,
                                                                                  ungoverned: Path,
                                                                                  command: str) -> None:
    """P1: `--help` or `--version` anywhere in a shell's words let the call through unread, while bash runs
    `bash -c 'echo RAN' --help` (`--help` is its $0). Only a shell asked for nothing but its help or version is
    let through."""
    assert _bash(guard, command, ungoverned), command


@pytest.mark.parametrize("command", ["bash --help", "sh --version", "zsh --version --help"])
def test_a_shell_asked_only_for_its_help_or_version_is_allowed(guard: ModuleType, ungoverned: Path,
                                                               command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


@pytest.mark.parametrize("command", [
    "scripts/DEPLOY_HOSTED_ENGINE.sh", "SCRIPTS/DEPLOY_HOSTED_ENGINE.SH", "bash scripts/Deploy_Hosted_Engine.sh --dry-run --force",
])
def test_the_deploy_scripts_are_named_whatever_their_case(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """M1: the owner's disk is case-insensitive, so a script named in another case is the same script."""
    assert _bash(guard, command, ungoverned), command


def test_untracked_work_counts_even_when_the_repository_hides_untracked_files(guard: ModuleType, live: Path) -> None:
    """M2: `status.showUntrackedFiles=no`, which an agent may set, hid a worktree's new files from the check."""
    w = live / ".claude" / "worktrees" / "w"
    _git(w, "config", "status.showUntrackedFiles", "no")
    (w / "review.md").write_text("findings\n", encoding="utf-8")
    for command in ("rm -rf .claude/worktrees/w", "git worktree remove --force .claude/worktrees/w"):
        why = _bash(guard, command, live)
        assert why and "#286" in why, (command, why)


# --- run bug-night's owner bundle: #256, #287, #305, #317, #318, #320 ----------------------------------------
#
# Each rule is held in both polarities: the spellings that walked through the guard on `main`, and the near-misses
# an agent runs every day, which must stay allowed.

@pytest.mark.parametrize(("planted", "path"), [
    (".claude", ".claude/settings.json"), (".claude", ".claude/hooks/bash_guard.py"),
    (".claude/hooks", ".claude/hooks/bash_guard.py"), (".githooks", ".githooks/pre-push"),
    (".claude/worktrees", ".claude/worktrees/plain/notes.md"),
])
def test_a_git_directory_planted_inside_the_owners_directories_does_not_open_them(guard: ModuleType, repo: Path,
                                                                                  planted: str, path: str) -> None:
    """#256: the refusal looked only at the NEAREST directory holding `.git`, so after `git init .claude` the
    owner's `.claude/` was a work tree of its own and every Write, Edit and shell write into it passed. Every work
    tree above the path is asked now, through a nested one."""
    (repo / planted / ".git").mkdir(parents=True, exist_ok=True)
    why = guard.judge_file({"tool_input": {"file_path": path}, "cwd": str(repo)})
    assert why and ".claude/ and .githooks/" in why, (planted, path, why)
    why = _bash(guard, f"cp x {path}", repo)
    assert why and ".claude/ and .githooks/" in why, (planted, path, why)
    why = _bash(guard, f"echo x > {path}", repo)
    assert why and ".claude/ and .githooks/" in why, (planted, path, why)


def test_a_worktree_under_claude_worktrees_and_a_nested_repository_elsewhere_stay_writable(guard: ModuleType,
                                                                                           repo: Path,
                                                                                           seat: Path) -> None:
    """#256's near-misses: a seat or an implementer works in `.claude/worktrees/<name>`, a work tree of its own
    inside the owner's `.claude/`, and a repository nested anywhere else is no owner's directory either. A seat's
    own `.claude/` stays refused."""
    (repo / "vendor" / "lib" / ".git").mkdir(parents=True)
    for path in (seat / "src" / "a.py", repo / "vendor" / "lib" / "x.py", repo / "ios" / "App.swift"):
        assert guard.judge_file({"tool_input": {"file_path": str(path)}, "cwd": str(repo)}) is None, path
        assert _bash(guard, f"echo x > {path}", repo) is None, path
    assert _bash(guard, "cd .claude/worktrees/seat && echo x > src/b.py && git init -q build/sub", repo) is None
    why = guard.judge_file({"tool_input": {"file_path": str(seat / ".claude" / "settings.json")}, "cwd": str(repo)})
    assert why and ".claude/ and .githooks/" in why, why


@pytest.mark.parametrize(("command", "where"), [
    ("git init .claude", "."), ("git init -q .claude/hooks", "."), ("git init --bare .githooks/x", "."),
    ("cd .claude && git init", "."), ("git -C .claude init", "."), ("git init", ".claude"),
    ("git init --separate-git-dir .claude/g build/x", "."), ("git init --separate-git-dir=.githooks/g x", "."),
    ("git clone /x .claude/x", "."), ("git clone --depth 1 /x .githooks/x", "."), ("git clone -b x /x .CLAUDE/x", "."),
    ("git clone https://example.com/a/hooks.git", ".claude"), ("git worktree add .claude/x", "."),
    ("git worktree add -b b .githooks/w", "."), ("git worktree add .claude/worktreesx main", "."),
    ("git worktree add --detach ../.claude/x", "ios"), ("git submodule add /x .claude/x", "."),
    ("git submodule add --name h https://example.com/a/hooks.git", ".githooks"),
])
def test_git_init_clone_or_worktree_add_into_the_owners_directories_is_refused(guard: ModuleType, repo: Path,
                                                                               command: str, where: str) -> None:
    """#256: the command that plants the `.git` is refused where it plants it, but Claude Code's own
    `.claude/worktrees/<name>`."""
    why = _bash(guard, command, repo / where)
    assert why and ".claude/ and .githooks/" in why, (command, why)


@pytest.mark.parametrize("command", [
    "git worktree add .claude/worktrees/x", "git worktree add -b x .claude/worktrees/x main",
    "git worktree add --detach .claude/worktrees/seat2 HEAD", "git init build/sub", "git init -q",
    "git clone /x vendor/x", "git clone --depth 1 https://example.com/a/b.git", "git worktree list",
    "git init --bare /tmp/bare.git", "git clone /x .claude-notes/x", "git submodule add /x vendor/x",
])
def test_git_init_clone_and_worktree_add_elsewhere_are_allowed(guard: ModuleType, repo: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


@pytest.mark.parametrize("command", [
    '(X=$(mktemp -d)); rm -rf "$X"/Users/x', '(export X=$(mktemp -d); make test); rm -rf "$X"/Users/x',
    'f() { local X=$(mktemp -d); }; f; rm -rf "$X"/Users/x', 'f () { X=$(mktemp -d); }; rm -rf "$X"/Users/x',
    'function f { X=$(mktemp -d); }; rm -rf "$X"/Users/x', 'X=$(mktemp -d) | true; rm -rf "$X"/Users/x',
    'true | X=$(mktemp -d); rm -rf "$X"/Users/x', 'for i in $L; do X=$(mktemp -d); done; rm -rf "$X"/Users/x',
    'while false; do X=$(mktemp -d); done; rm -rf "$X"/Users/x', 'if false; then X=$(mktemp -d); fi; rm -rf "$X"/Users/x',
    'case $a in b) X=$(mktemp -d);; esac; rm -rf "$X"/Users/x', 'true || X=$(mktemp -d); rm -rf "$X"/Users/x',
    'false && X=$(mktemp -d); rm -rf "$X"/Users/x', 'X=$(mktemp -d) & rm -rf "$X"/Users/x',
    'y=$(X=$(mktemp -d)); rm -rf "$X"/Users/x', '(export HOME=$(mktemp -d); make test); rm -rf "$HOME"',
    "functions[cd]='builtin cd ~'; cd x; rm -rf build",
    # a child process's or a deferred text's assignment: the shell running this text never takes it, or takes it later
    "bash -c 'X=$(mktemp -d)'; rm -rf \"$X\"/Users/x", "sh <<'E'\nX=$(mktemp -d)\nE\nrm -rf \"$X\"/Users/x",
    "trap 'X=$(mktemp -d)' EXIT; rm -rf \"$X\"/Users/x", "alias a='X=$(mktemp -d)'; rm -rf \"$X\"/Users/x",
    "git -c alias.x='!X=$(mktemp -d)' x; rm -rf \"$X\"/Users/x",
    "X=$(mktemp -d); bash -c 'X=/'; rm -rf \"$X\"/Users/x", "eval 'false && X=$(mktemp -d)'; rm -rf \"$X\"/Users/x",
])
def test_a_variable_set_where_it_may_not_happen_or_does_not_last_is_not_scratch_after_it(
        guard: ModuleType, temp_dir: Path, command: str) -> None:
    """#287: the guard kept one flat table of values for the whole text, and a name with no value before took the
    `mktemp` result set in a subshell, a function, a pipeline stage, a loop or a branch -- where the shell may never
    set it, or drops it again -- so `rm -rf "$X"/Users/x` ran as `rm -rf /Users/x`. zsh's `functions[cd]=` defines
    `cd` as a function, so a relative `cd` after it lands where this cannot name. Text another process runs (`bash
    -c`, a shell's here-document, a git alias) or that runs later (a `trap`, an `alias`) sets nothing here either."""
    inside = temp_dir / "work"
    inside.mkdir()
    why = _bash(guard, command, inside)
    assert why and "destructive" in why, (command, why)


@pytest.mark.parametrize("command", [
    'X=$(mktemp -d); (cd "$X" && make); rm -rf "$X"', 'X=$(mktemp -d) && rm -rf "$X"/sub',
    'X=$(mktemp -d); for f in a b; do touch "$X/$f"; done; rm -rf "$X"',
    'for f in a b; do echo "$f"; done; X=$(mktemp -d); rm -rf "$X"', 'make build && X=$(mktemp -d) && rm -rf "$X"',
    'if true; then echo y; fi; X=$(mktemp -d); rm -rf "$X"', '(X=$(mktemp -d)); rm -rf "$TMPDIR/foo"',
    'X=$(mktemp -d); echo "$X" | cat; rm -rf "$X"', "bash -c 'd=$(mktemp -d); rm -rf \"$d\"'",
    "eval 'X=$(mktemp -d)'; rm -rf \"$X\"",
])
def test_a_variable_set_in_the_line_of_the_text_still_holds_after_a_subshell_loop_or_pipe(
        guard: ModuleType, temp_dir: Path, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


def test_git_rm_of_a_path_this_cannot_read_is_refused(guard: ModuleType, repo: Path) -> None:
    """#287's P5: `git rm -r "$(pwd)"` from the repository removed every tracked file; `$(pwd)` may be the
    repository, and a command can redefine `pwd`. `git rm -r --cached` of one, and a plain path, stay allowed."""
    for command in ('git rm -r "$(pwd)"', 'git rm -r "$D"', "git rm -rf `pwd`"):
        assert _bash(guard, command, repo), command
    for command in ('git rm -r --cached "$(pwd)"', "git rm -r ios", 'git rm "$f"'):
        assert _bash(guard, command, repo) is None, command


@pytest.mark.parametrize("command", [
    "git config credential.helper '!rm -rf ~'", "git config --global credential.helper '!rm -rf ~'",
    "git -c credential.helper='!rm -rf ~' fetch", "git config credential.https://example.com.helper '!rm -rf ~'",
    "git config core.pager '!rm -rf ~'", "git config gpg.program '!rm -rf ~'", "git config core.sshCommand ' !rm -rf ~'",
    "git config credential.helper '/bin/rm -rf ~'", "git config credential.helper 'store; rm -rf ~'",
    "git -c core.fsmonitor='!git push --force origin x' status",
])
def test_a_code_running_config_value_that_starts_with_a_bang_is_judged_as_the_command_it_runs(
        guard: ModuleType, ungoverned: Path, command: str) -> None:
    """#305: a value git runs through the shell was judged with its leading `!` on, so `!rm` read as a program
    named `!rm` and passed; git strips the `!` and runs the rest."""
    assert _bash(guard, command, ungoverned), command


@pytest.mark.parametrize("command", [
    "git config credential.helper store", "git config --global credential.helper osxkeychain",
    "git config credential.helper '!gh auth git-credential'", "git -c credential.helper= fetch",
    "git config core.pager 'less -R'", "git config --get credential.helper", "git -c core.pager=cat log",
])
def test_a_harmless_code_running_config_value_is_allowed(guard: ModuleType, ungoverned: Path, command: str) -> None:
    assert _bash(guard, command, ungoverned) is None, command


def _dirty(live: Path) -> Path:
    w = live / ".claude" / "worktrees" / "w"
    (w / "review.md").write_text("findings\n", encoding="utf-8")
    return w


@pytest.mark.parametrize("command", [
    "rm .claude/worktrees/w/.git", "rm -f .claude/worktrees/w/.git", "mv .claude/worktrees/w/.git /tmp/g",
    "truncate -s 0 .claude/worktrees/w/.git", "chmod 000 .claude/worktrees/w/.git", "unlink .claude/worktrees/w/.git",
    "git worktree move .claude/worktrees/w /tmp/x", "git worktree move w ../moved",
    "git worktree move --force .claude/worktrees/w /tmp/x",
])
def test_a_dirty_worktree_is_not_unlinked_or_moved_out_of_reach(guard: ModuleType, live: Path, command: str) -> None:
    """#317: the removal refusal (#286) held only while the worktree was live and in place; removing or emptying its
    `.git` first, or `git worktree move` to the temp directory, made the next `rm -rf` a plain directory's. (`mv` of a
    `.claude/worktrees/<name>` is refused already, as a write into the owner's `.claude/`, and a write onto a `.git`
    by `>` or `cp` as one into git's own files, #285.)"""
    _dirty(live)
    why = _bash(guard, command, live)
    assert why and "#286" in why, (command, why)


@pytest.mark.parametrize("command", [
    "rm .claude/worktrees/w/.git", "git worktree move .claude/worktrees/w .claude/worktrees/w2",
    "mv .claude/worktrees/w/a.txt .claude/worktrees/w/b.txt",
])
def test_a_clean_worktree_may_be_unlinked_or_moved(guard: ModuleType, live: Path, command: str) -> None:
    assert _bash(guard, command, live) is None, command


def test_moving_a_file_inside_a_dirty_worktree_is_allowed(guard: ModuleType, live: Path) -> None:
    w = _dirty(live)
    assert _bash(guard, "mv review.md notes.md && git mv a.txt c.txt", w) is None


def test_work_hidden_by_a_self_ignoring_gitignore_still_counts(guard: ModuleType, live: Path) -> None:
    """#317: `echo '*' > <wt>/notes/.gitignore` hides the directory's work, and itself, from `git status`."""
    notes = live / ".claude" / "worktrees" / "w" / "notes"
    notes.mkdir()
    (notes / "review.md").write_text("findings\n", encoding="utf-8")
    (notes / ".gitignore").write_text("*\n", encoding="utf-8")
    for command in ("rm -rf .claude/worktrees/w", "git worktree remove --force .claude/worktrees/w"):
        why = _bash(guard, command, live)
        assert why and "#286" in why, (command, why)


def test_files_ignored_by_the_committed_rules_do_not_make_a_worktree_dirty(guard: ModuleType, live: Path) -> None:
    """#317's near-miss: a tool's own ignore file (`.pytest_cache/.gitignore` holds `*`) inside a directory the
    committed `.gitignore` ignores hides nothing the worktree's history would keep."""
    w = live / ".claude" / "worktrees" / "w"
    cache = w / ".claude" / "worktrees" / "cache"
    cache.mkdir(parents=True)
    (cache / ".gitignore").write_text("*\n", encoding="utf-8")
    (cache / "v").write_text("x\n", encoding="utf-8")
    assert _bash(guard, "rm -rf .claude/worktrees/w", live) is None


@pytest.mark.parametrize("command", [
    "echo x >> .git/info/exclude", "echo '*' > .git/info/exclude", "echo x > .git/info/attributes",
    "cp x .git/info/sparse-checkout", "echo x > .git/modules/sub/config", "cp x .git/modules/sub/hooks/pre-commit",
    "echo x > .git/modules/a/b/config", "echo /x > .git/commondir", "echo /x > .git/worktrees/w/commondir",
    "tee .GIT/INFO/exclude < x",
])
def test_a_write_into_gits_info_modules_or_commondir_is_refused(guard: ModuleType, repo: Path, command: str) -> None:
    """#320 (#285's rest): `.git/info/exclude` hides work from `git status`, `.git/modules/<name>/` is a submodule's
    own git directory with its config and hooks, and `commondir` points a git directory's config elsewhere."""
    why = _bash(guard, command, repo)
    assert why and "#320" in why, (command, why)


@pytest.mark.parametrize("command", [
    "git init --template=/tmp/t", "git init --template /tmp/t x", "git clone --template=/tmp/t /x y",
    "git clone --tem=/tmp/t /x y", "git init --t=/tmp/t x", "git config init.templateDir /tmp/t", "git config --global init.templatedir /tmp/t",
    "git -c init.templateDir=/tmp/t init x", "GIT_TEMPLATE_DIR=/tmp/t git init x", "export GIT_TEMPLATE_DIR=/tmp/t",
    "env GIT_TEMPLATE_DIR=/tmp/t git clone /x y", "read GIT_TEMPLATE_DIR",
])
def test_a_git_template_directory_is_refused(guard: ModuleType, ungoverned: Path, command: str) -> None:
    """#320: a template directory's hooks and config are copied into the repository `git init` or `git clone`
    makes, or re-initialises, from a place this guard does not read."""
    try:
        why = _bash(guard, command, ungoverned)
    except guard.Unreadable as error:   # `read NAME` refuses from inside the reading, as `main` reports it
        why = str(error)
    assert why and "#320" in why, (command, why)


@pytest.mark.parametrize("command", [
    "cat .git/info/exclude", "cp .git/info/exclude /tmp/exclude.bak", "ls .git/modules", "git init x",
    "git clone /x y", "git config --get init.templateDir", "echo x > notes/info/exclude",
    "echo x > .git-notes/commondir", "git submodule status",
])
def test_reading_gits_info_and_modules_and_a_plain_init_are_allowed(guard: ModuleType, repo: Path,
                                                                    command: str) -> None:
    assert _bash(guard, command, repo) is None, command


@pytest.mark.parametrize("command", [
    "git branch -f main HEAD", "git branch --force main", "git branch -f master x", "git branch -M x main",
    "git branch -m main", "git branch -c fix/x origin/HEAD", "git branch -C x main", "git branch main", "git update-ref refs/remotes/origin/HEAD HEAD", "git update-ref refs/remotes/origin/main HEAD",
    "git update-ref -d refs/remotes/origin/HEAD", "git update-ref --stdin",
    "git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/x", "git symbolic-ref -d refs/remotes/origin/HEAD",
    "git symbolic-ref HEAD refs/heads/main", "git remote set-head origin x", "git remote set-head origin -d",
    "git remote set-url origin /tmp/evil", "git remote rename origin old", "git remote add origin /tmp/evil",
    "git config remote.origin.url /tmp/evil", "git config remote.origin.fetch '+refs/heads/x:refs/remotes/origin/main'",
    "git fetch . HEAD:main", "git fetch origin +x:refs/remotes/origin/main", "git fetch /tmp/e 'refs/heads/*:refs/remotes/origin/*'",
    "git pull . HEAD:main", "git checkout -B main", "git checkout -b main origin/x", "git switch -C main",
    "git switch --force-create main", "git switch -c master",
    "echo 0123 > .git/refs/heads/main", "echo x >> .git/packed-refs", "cp x .git/refs/remotes/origin/HEAD",
    'git branch -M x "$b"', 'git branch -f "$b" HEAD', 'git checkout -B "$b"', 'git update-ref "$r" HEAD',
    'git fetch . "HEAD:$b"', "git branch -m x `echo main`", "git branch -f MAIN HEAD", "git update-ref REFS/heads/main x",
    "git push . HEAD:refs/remotes/origin/main", "git replace 0123abc HEAD", "git replace --graft main",
    "cp x .git/refs/replace/0123abc", "echo 0123 > .git/shallow",
])
def test_the_default_branch_the_deploy_gate_reads_cannot_be_moved(guard: ModuleType, repo: Path, command: str) -> None:
    """#318: the deploy gate reads the brief at the merge-base of HEAD with origin/HEAD, origin/main or main; an
    agent that moves one of them chooses the policy its own deploy is judged by. (Deleting a local one moves the gate
    to the next, or to none, which refuses every deploy: `git branch -D main` stays allowed, as DevFlow's
    conformance holds it.)"""
    why = _bash(guard, command, repo)
    assert why and "#318" in why, (command, why)


@pytest.mark.parametrize("command", [
    "git branch fix/x", "git branch -f fix/x HEAD", "git branch -f fix/x main", "git branch -d fix/old",
    "git branch -m main old", 'git branch -D "$b"',
    "git branch --list main", "git branch --contains main", "git branch -a", "git branch -u origin/main",
    "git branch --set-upstream-to=origin/main", "git branch -m fix/old fix/new", "git update-ref refs/heads/fix/x HEAD",
    "git symbolic-ref refs/remotes/origin/HEAD", "git symbolic-ref --short HEAD", "git remote set-head origin --auto",
    "git remote -v", "git remote add upstream https://example.com/a/b.git", "git fetch origin", "git fetch origin main",
    "git fetch origin fix/x:fix/x", "git pull --ff-only origin main", "git checkout -B fix/x", "git switch -c fix/x main",
    "git checkout main", "cat .git/refs/heads/main", "git rev-parse origin/HEAD", "git config --get remote.origin.url",
    'git checkout -b "fix/issue-$n"', 'git switch -c "$b"', 'git branch "fix/$n"', "git replace -l",
    "git push . HEAD:refs/heads/fix/x", "git push -u origin fix/x",
])
def test_reading_or_moving_another_branch_is_allowed(guard: ModuleType, repo: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


# --- the bundle's security review (B1, M1-M3): a value that MAY be set is judged as each value it may take -------

@pytest.mark.parametrize("command", [
    'f() { :; }; d=.claude; echo x > "$d"/settings.json', "true && d=.claude/hooks/bash_guard.py; cp /tmp/x $d",
    'if :; then d=.claude; fi; cp /tmp/x "$d"/settings.json', 'f() { :; }; d=.git; echo x >> "$d"/config',
    "f() { :; }; d=~/.gitconfig; echo x >> $d", "f() { :; }; k=core.hooksPath; git config $k /dev/null",
    "f() { :; }; o=--no-verify; git commit $o -m x", "f() { :; }; b=main; git push origin $b",
    "f() { :; }; o=--hard; git reset $o HEAD~1", "f() { :; }; o=--force; git push $o origin x",
    "f() { :; }; p=fly; $p deploy", "f() { :; }; d=.env; echo x > $d", "true && d=.env; echo x > $d",
    "true && o=--hard; git reset $o HEAD~1", "if :; then b=main; fi; git push origin $b",
    "true && k=core.hooksPath; git config $k /dev/null", "true && o=--force; git push $o origin x",
    "true && d=~/.gitconfig; echo x >> $d", 'd=x; true && d=.claude; echo y > "$d"/settings.json',
    'd=.claude; (d=x); echo y > "$d"/settings.json', "d=.claude; bash -c 'd=x'; echo y > \"$d\"/settings.json",
    'd=.claude :; echo x > "$d"/settings.json',
])
def test_a_value_that_may_be_set_is_judged_as_each_value_it_may_take(guard: ModuleType, repo: Path,
                                                                      command: str) -> None:
    """The review's B1: #287's first fix made such a name unknown, and every refusal that reads a name's value read
    unknown as harmless, so `f() { :; }; d=.claude; echo x > "$d"/settings.json` passed where it was refused. The
    call is judged with the assignment made and without it."""
    assert _bash(guard, command, repo), command


@pytest.mark.parametrize("command", [
    "git checkout -Bmain feat", "git switch -Cmain feat", "git switch --force-create main feat",
    "git switch --force-cr main feat", "git switch --cr main", "git checkout -qB main", "git checkout -bmain",
    "git config url./tmp/evil.insteadOf https://github.com/a/b",
    "git -c url./tmp/evil.insteadOf=https://github.com/a/b fetch origin",
])
def test_a_branch_made_with_an_attached_or_abbreviated_option_or_a_rewritten_url_is_refused(
        guard: ModuleType, repo: Path, command: str) -> None:
    """The review's M1 (#318): `-Bmain` and `--force-cr` move main as `-B main` does, and `insteadOf` rewrites
    origin's URL with `remote.origin.url` untouched."""
    why = _bash(guard, command, repo)
    assert why and "#318" in why, (command, why)


@pytest.mark.parametrize("command", [
    "git checkout -bwave/x", "git switch -cwave/x main", "git switch --create fix/x", "git checkout -q main",
    "git config --get-regexp url", "git switch --cr fix/x",
])
def test_a_branch_made_by_another_name_is_allowed(guard: ModuleType, repo: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


@pytest.mark.parametrize("command", [
    "GIT_DIR=.claude/.git git init", "git --git-dir=.claude/.git init", "git --git-dir .githooks/g init",
    "GIT_WORK_TREE=.claude git status", "export GIT_DIR=.claude/.git", "env GIT_DIR=.githooks/x git init",
    "git --work-tree=.githooks checkout x",
])
def test_a_git_directory_placed_in_the_owners_directories_is_refused(guard: ModuleType, repo: Path,
                                                                     command: str) -> None:
    """The review's M2 (#256): `GIT_DIR` and `--git-dir` plant a git directory where `git init` is told."""
    why = _bash(guard, command, repo)
    assert why and ".claude/ and .githooks/" in why, (command, why)


@pytest.mark.parametrize("command", [
    "GIT_DIR=/tmp/x.git git init", "git --git-dir=.git status", "GIT_DIR=.git git log",
    "git --git-dir=.claude/worktrees/seat/.git status",
])
def test_a_git_directory_placed_elsewhere_is_allowed(guard: ModuleType, repo: Path, seat: Path, command: str) -> None:
    assert _bash(guard, command, repo) is None, command


@pytest.mark.parametrize("command", [
    "sed -i '' d .claude/worktrees/w/.git", "perl -i -pe 's/gitdir/x/' .claude/worktrees/w/.git",
    "sed --in-place=.bak d .claude/worktrees/w/.git",
])
def test_an_in_place_edit_of_a_dirty_worktrees_git_file_is_refused(guard: ModuleType, live: Path, command: str) -> None:
    """The review's M3 (#317): `sed -i` emptied the `.git` that `rm` may not remove."""
    _dirty(live)
    why = _bash(guard, command, live)
    assert why and "#286" in why, (command, why)
    (live / ".claude" / "worktrees" / "w" / "review.md").unlink()
    assert _bash(guard, command, live) is None, command


# --- #344 (the bundle review's R1): a value this cannot read is never read as harmless ------------------------------

@pytest.mark.parametrize("command", [
    'd=$(echo .claude); echo x > "$d"/settings.json', 'a=(.claude); echo x > "$a"/settings.json',
    'd=`echo .git`; echo x >> "$d"/config', 'd=$(echo .git); cp x "$d"/config', 'echo x >> "$(echo .git)"/config',
    'a=(.git); echo x >> "${a[0]}"/config', 'dd if=x of="$(echo .git)/config"', 'd=$(echo .env); echo x > $d',
    "d=$(echo .claude/settings.json); sed -i '' s/a/b/ \"$d\"", 'set -- .claude; echo x > "$1"/settings.json',
    'd=$1; echo x > "$d"/settings.json', 'echo x > "${d:-.claude}"/settings.json',
    'mapfile -t a < f; echo x > "$a"/settings.json', 'declare -a a=(.githooks); cp x "$a"/pre-push',
    'b=$(git branch --show-current); git push origin "$b"', 'git push origin "$(echo main)"',
    "b=`echo main`; git push origin $b", 'o=$(echo --no-verify); git commit $o -m x',
    'o=$(echo --hard); git reset $o HEAD~1', 'o=$(echo --force); git push $o origin x',
    'k=$(echo core.hooksPath); git config $k /dev/null', 'p=$(echo fly); $p deploy', '"$(echo fly)" deploy',
    'd=$(echo /Users/x); rm -rf "$d"', 'rm -rf "$(echo ~)"', 'a=(/Users/x); rm -rf "${a[@]}"',
])
def test_a_value_this_cannot_read_is_refused_where_a_refusal_reads_it(guard: ModuleType, repo: Path,
                                                                     command: str) -> None:
    """#344: a command substitution's output, an array, a positional parameter or a `${...}` form was read as no
    protected path, no protected branch and no option, so `d=$(echo .claude); echo x > "$d"/settings.json` passed."""
    assert _bash(guard, command, repo), command


@pytest.mark.parametrize("command", [
    'd=$(mktemp -d); rm -rf "$d"', "x=$(date); echo $x", "ls $(pwd)", 'git commit -m "$(cat msg.txt)"',
    'git commit -am "$(date)"', 'out=$(mktemp); echo x > "$out"', 'd=$HOME/notes; echo x > "$d/a.txt"',
    'git log --since="$(date)"', "echo $(date) > out.txt", "x=(a b c); echo ${x[0]}", "echo x > /tmp/out.$$",
    '"$(git rev-parse --show-toplevel)"/scripts/check.sh', 'git -C "$(git rev-parse --show-toplevel)" status',
    'git add "$(git ls-files -m | head -1)"', 'n=$(git rev-parse --short HEAD); echo "$n" > build/head.txt',
])
def test_a_value_this_cannot_read_where_nothing_reads_it_is_allowed(guard: ModuleType, temp_dir: Path, repo: Path,
                                                                     command: str) -> None:
    assert _bash(guard, command, repo) is None, command


# --- the bundle review's M5: a `${NAME:-literal}` is judged as each value it may take ----------------------------

@pytest.mark.parametrize("command", [
    'echo x > "${X:-.claude}"/settings.json', 'echo x >> "${G-.git}/config"', 'cp x "${D:=.githooks}"/pre-push',
    '"${P:-fly}" deploy', 'git push origin "${B:-main}"', "git commit ${O:---no-verify} -m x",
    'X=.claude; echo x > "${X:-a}"/settings.json', 'rm -rf "${D:-/Users/x}"', "rm -rf ${TMPDIR:-/}x",
])
def test_a_default_is_refused_when_either_value_is(guard: ModuleType, repo: Path, command: str) -> None:
    """M5: the name's value or the literal -- each is judged, and either refused refuses the command."""
    assert _bash(guard, command, repo), command


@pytest.mark.parametrize("command", [
    'echo hi > "${TMPDIR:-/tmp}/x.txt"', '"${PY:-python3}" -V', 'git switch -c "fix/issue-${N:-1}-x"',
    'echo "${HOME:-/tmp}"', 'cat "${F:-README.md}"', 'make test PY="${PY:-python3}"',
])
def test_a_default_whose_values_are_both_harmless_is_allowed(guard: ModuleType, temp_dir: Path, repo: Path,
                                                             command: str) -> None:
    """M5: #344 refused every `${...}` form as unreadable; a plain literal default is read instead."""
    assert _bash(guard, command, repo) is None, command
