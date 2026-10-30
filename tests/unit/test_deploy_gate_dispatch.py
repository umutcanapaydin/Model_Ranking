"""#390: a `gh` command that starts a deploy workflow is a deploy, however it is spelled.

The brief's `Deploy commands:` names `gh workflow run nightly-hosted.yml` (D-217 clause 6), and the gate matched that
declaration word for word with options dropped (`deploy_gate.matches`). So `gh workflow run -R a/b nightly-hosted.yml`
(an option's value before the file), `gh workflow run nightly-hosted` (the workflow's name), the workflow's id or its
path, the REST `dispatches` call and `gh run rerun` all started the night unjudged.

Now the gate reads a `gh` command by what it starts (`deploy_gate.gh_dispatch`). The deploy workflows are DERIVED:
every workflow file (`.github/workflows/`, and the proposals under `scripts/ci/` the owner installs) with a line
that runs a declared deploy command, in the tree or at the protected base, and every workflow a declared
`gh workflow run <file>` names. Each is known by its file name, its stem and its `name:`. What cannot be told --
a workflow id, an expansion, no workflow at all, a rerun of a run this cannot see -- is a deploy whenever a deploy
workflow exists (fail closed), and nothing when none does. The Bash guard hands every simple command's words to
the gate (`.claude/hooks/bash_guard.py`, `CANDIDATES`), so the guard itself needs no change; the last cases run
through it.

Each case is a throwaway repository: `main` holds the brief, a deploy workflow and a CI workflow.
"""

from __future__ import annotations

import importlib.util
import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "deploy_gate.py"
GUARD = ROOT / ".claude" / "hooks" / "bash_guard.py"

RELEASE = """name: Release to production
on:
  workflow_dispatch:
jobs:
  ship:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ship
        run: |
          echo "shipping"
          ./ship.sh --prod
"""
CI = """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -q
"""


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("deploy_gate_390", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                          cwd=root, capture_output=True, text=True, check=True, env=_env(), timeout=60).stdout.strip()


def _project(root: Path, deploy: str = "./ship.sh", workflows: dict[str, str] | None = None) -> Path:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    (root / "docs").mkdir()
    (root / "docs" / "project-brief.md").write_text(
        f"- **Working mode:** `light`\n- **Deploy commands:** `{deploy}`\n", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    for name, text in (workflows if workflows is not None else {"release.yml": RELEASE, "ci.yml": CI}).items():
        (root / ".github" / "workflows" / name).write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    return root


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _project(tmp_path_factory.mktemp("dispatch") / "p")


#: Every spelling of starting the release workflow, or of starting a workflow this cannot tell from it.
DEPLOYS = [
    "gh workflow run release.yml",
    "gh workflow run release.yml --ref main",
    "gh -R a/b workflow run release.yml",
    "gh workflow run -R a/b release.yml",
    "gh workflow run --repo=a/b release.yml",
    "gh workflow run --ref main -f x=1 release.yml",
    "gh workflow run RELEASE.YML",
    "gh workflow run release",
    "gh workflow run 'Release to production'",
    "gh workflow run .github/workflows/release.yml",
    "gh workflow run 123456",
    "gh workflow run",
    "gh workflow run $w",
    "gh workflow run $(...)",
    "/opt/homebrew/bin/gh workflow run release.yml",
    "env GH_REPO=a/b gh workflow run release.yml",
    "gh api -X POST repos/o/r/actions/workflows/release.yml/dispatches -f ref=main",
    "gh api --method POST repos/o/r/actions/workflows/release.yml/dispatches -f ref=main",
    "gh api --method=post /repos/o/r/actions/workflows/release.yml/dispatches",
    "gh api repos/{owner}/{repo}/actions/workflows/release.yml/dispatches -f ref=main",
    "gh api https://api.github.com/repos/o/r/actions/workflows/release.yml/dispatches",
    "gh api repos/o/r/actions/workflows/release%2Eyml/dispatches",
    "gh api repos/o/r/actions/workflows/987/dispatches",
    "gh api repos/o/r/actions/workflows/$(...)/dispatches",
    "gh api $url",
    "gh api repos/o/r/dispatches -f event_type=ship",
    "gh run rerun 123",
    "gh run rerun --failed",
    "gh run rerun 123 --job 456",
    "gh run rerun",
    "gh api -X POST repos/o/r/actions/runs/123/rerun",
    "gh api -X POST repos/o/r/actions/runs/123/rerun-failed-jobs",
    "gh api -X POST repos/o/r/actions/jobs/456/rerun",
    "gh alias set ship 'workflow run release.yml'",
    "gh alias set --shell ship '!gh workflow run release.yml'",
    "gh alias import aliases.yml",
    # The Security-Reviewer's round 1 on the bundle. M1: the workflow's path, its slashes URL-encoded.
    "gh api -X POST repos/o/r/actions/workflows/.github%2Fworkflows%2Frelease.yml/dispatches -f ref=main",
    "gh api repos/o/r/actions/workflows/.github%2fworkflows%2frelease.yml/dispatches",
    # M2: a word the shell or a wrapper rewrites, or a workflow no file the gate read is known by.
    "gh workflow run .github/workflows/rel*.yml",
    "gh workflow run rel*",
    "gh workflow run [r]elease.yml",
    "gh workflow run {release.yml,}",
    "gh workflow run {}",
    "gh workflow run X",
    "gh workflow run typo.yml",
    "gh api repos/o/r/actions/workflows/other.yml/dispatches",
    # M3: the invocation is judged, not the definition. Every alias definition, and every command that is
    # not one of gh's own, is a workflow this cannot name.
    "gh alias set prs 'pr list'",
    "gh alias set -s ship 'gh workflow run release.yml'",
    "gh alias set ship -",
    "gh alias set w workflow",
    "gh w run release.yml",
    "gh a -X POST repos/o/r/actions/workflows/release.yml/dispatches",
    "gh ship",
    "gh co 12",
    "gh my-extension run",
    # Round 2. M7: gh resolves its command word case-sensitively, so `Api` may be an alias.
    "gh Api repos/o/r/pulls",
    "gh Workflow",
    "gh RUN",
    # M8: an option this does not read may take the next word as its value in gh.
    "gh -z workflow zz",
    "gh --zz workflow zz",
    "gh -Ra/b workflow run release.yml",
    # M9: `gh extension exec` runs an extension.
    "gh extension exec x",
    "gh extension exec x release.yml",
]

#: What reads, lists or starts a workflow that deploys nothing: never a deploy.
NOT_DEPLOYS = [
    "gh workflow run ci.yml",
    "gh workflow run CI",
    "gh workflow run ci.yml -f note=release.yml",
    "gh workflow list",
    "gh workflow view release.yml",
    "gh run list -w release.yml",
    "gh run view 123",
    "gh run watch 123",
    "gh api repos/o/r/actions/workflows/release.yml/runs",
    "gh api repos/o/r/actions/workflows/ci.yml/dispatches -f ref=main",
    "gh api repos/$r/pulls",
    "gh pr list",
    "gh alias list",
    "gh --version",
    "gh -R a/b pr list",
    "gh --repo=a/b issue view 1",
    "gh --help",
    "gh extension list",
    "gh help workflow",
    "echo gh workflow run release.yml",
    "git commit -m 'gh workflow run release.yml'",
]


@pytest.mark.parametrize("command", DEPLOYS)
def test_every_spelling_that_starts_a_deploy_workflow_is_a_deploy(project: Path, command: str) -> None:
    words = shlex.split(command.replace("$(...)", "__SUB__"))
    words = [w.replace("__SUB__", "$(...)") for w in words]
    assert _gate().deploy_in([words], project), command


@pytest.mark.parametrize("command", NOT_DEPLOYS)
def test_a_gh_command_that_starts_no_deploy_is_not_one(project: Path, command: str) -> None:
    assert _gate().deploy_in([shlex.split(command)], project) is None, command


def test_with_no_deploy_workflow_nothing_gh_starts_is_a_deploy(tmp_path: Path) -> None:
    """No workflow runs a declared deploy: a dispatch this cannot name starts nothing that deploys."""
    root = _project(tmp_path / "p", deploy="fly deploy", workflows={"ci.yml": CI})
    gate = _gate()
    for command in ("gh workflow run 123", "gh run rerun 1", "gh workflow run $w", "gh workflow run ci.yml",
                    "gh api repos/o/r/dispatches"):
        assert gate.deploy_in([shlex.split(command)], root) is None, command


def test_a_workflow_that_deploys_with_flyctl_or_over_a_continued_line_is_a_deploy_workflow(tmp_path: Path) -> None:
    """Round 1's M4, its fixable part: `flyctl` is `fly` (the guard holds both, D-185), and a `\\` joins a line."""
    flyctl = RELEASE.replace("./ship.sh --prod", "flyctl deploy --remote-only")
    continued = RELEASE.replace("./ship.sh --prod", "fly \\\n            deploy --remote-only")
    for text in (flyctl, continued):
        root = _project(tmp_path / f"p{len(text)}", deploy="fly deploy", workflows={"release.yml": text, "ci.yml": CI})
        gate = _gate()
        assert gate.deploy_in([["gh", "workflow", "run", "release.yml"]], root), text
        assert gate.deploy_in([["gh", "workflow", "run", "ci.yml"]], root) is None, text


def test_a_pattern_word_is_unknown_even_when_it_spells_a_known_name(tmp_path: Path) -> None:
    """Round 1's M2: the guard hands over words unquoted, so `lint [fast]` may be a pattern the shell expands
    to a deploy workflow's file, though a workflow is also named that."""
    lint = CI.replace("name: CI", 'name: "lint [fast]"')
    root = _project(tmp_path / "p", workflows={"release.yml": RELEASE, "lint.yml": lint})
    gate = _gate()
    assert gate.deploy_in([["gh", "workflow", "run", "lint [fast]"]], root)
    assert gate.deploy_in([["gh", "workflow", "run", "lint"]], root) is None


def test_a_quoted_name_that_holds_a_hash_is_the_whole_name(tmp_path: Path) -> None:
    """Round 1's N2: `name: "Ship #1"` was read as `ship`."""
    root = _project(tmp_path / "p", workflows={"release.yml": RELEASE.replace("name: Release to production",
                                                                              'name: "Ship #1"  # the release'),
                                               "ci.yml": CI})
    gate = _gate()
    assert "ship #1" in gate.deploy_workflows(root, gate.declared(root))["release.yml"]
    assert gate.deploy_in([["gh", "workflow", "run", "Ship #1"]], root)


def test_a_base_file_git_cannot_show_makes_every_dispatch_a_deploy(tmp_path: Path,
                                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """Round 1's N1: a failed `git show` at the base was swallowed, and the files after it went unread. Now the
    rest are still read, and the read is marked incomplete, so every dispatch is judged a deploy. (#509: the base's
    files are read through the verified reader, so the failure is injected there, where `git show` was.)"""
    root = _project(tmp_path / "p", deploy="fly deploy", workflows={"a.yml": CI, "z.yml": CI.replace("CI", "Z")})
    gate = _gate()
    assert gate.deploy_in([["gh", "workflow", "run", "a.yml"]], root) is None
    real = gate.brief_fields.batch_read
    failing = _git(root, "rev-parse", "HEAD:.github/workflows/a.yml")

    def flaky(batch: object, oid: str, kind: str) -> object:
        return f"object {oid} cannot be read as a {kind}" if oid == failing else real(batch, oid, kind)

    monkeypatch.setattr(gate.brief_fields, "batch_read", flaky)
    texts, complete = gate._workflow_texts(root)
    assert not complete
    assert len(texts["z.yml"]) == 2, "the file after the failing one was still read at the base"
    assert gate.deploy_in([["gh", "workflow", "run", "a.yml"]], root)
    assert gate.deploy_in([["ls"]], root) is None


def test_a_workflow_the_brief_names_is_a_deploy_workflow_by_its_name_too(tmp_path: Path) -> None:
    """D-217's `gh workflow run nightly-hosted.yml`: the proposal under `scripts/ci/` gives its `name:`."""
    root = _project(tmp_path / "p", deploy="gh workflow run night.yml", workflows={"ci.yml": CI})
    (root / "scripts" / "ci").mkdir(parents=True)
    (root / "scripts" / "ci" / "night.yml").write_text("name: the-night\non: [workflow_dispatch]\n", encoding="utf-8")
    gate = _gate()
    for command in ("gh -R a/b workflow run night.yml", "gh workflow run night", "gh workflow run the-night",
                    "gh run rerun 9", "gh api repos/o/r/actions/workflows/night.yml/dispatches"):
        assert gate.deploy_in([shlex.split(command)], root), command
    assert gate.deploy_in([["gh", "workflow", "run", "ci.yml"]], root) is None


def test_a_change_that_drops_the_deploy_step_still_dispatches_a_deploy(tmp_path: Path) -> None:
    """Base-pinned (#283): a dispatch runs the default branch's copy of the workflow, so the base's copy counts."""
    root = _project(tmp_path / "p")
    _git(root, "checkout", "-q", "-b", "change")
    (root / ".github" / "workflows" / "release.yml").write_text(RELEASE.replace("./ship.sh --prod", "true"),
                                                                 encoding="utf-8")
    _git(root, "commit", "-q", "-am", "ci: no ship")
    assert _gate().deploy_in([["gh", "workflow", "run", "release.yml"]], root)


def test_the_real_tree_judges_the_spellings_the_review_found() -> None:
    """The #387 security review's M1, against this repository's own brief and `scripts/ci/nightly-hosted.yml`."""
    gate = _gate()
    for command in ("gh workflow run -R umutcanapaydin/Model_Ranking nightly-hosted.yml",
                    "gh workflow run nightly-hosted", "gh workflow run .github/workflows/nightly-hosted.yml",
                    "gh api -X POST repos/o/r/actions/workflows/nightly-hosted.yml/dispatches -f ref=main",
                    "gh run rerun 123"):
        assert gate.deploy_in([shlex.split(command)], ROOT), command
    assert gate.deploy_in([["gh", "workflow", "run", "ci.yml"]], ROOT) is None
    assert gate.deploy_in([["gh", "run", "list"]], ROOT) is None


# --- through the Bash guard, the real entry point -------------------------------------------------------------

@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bash_guard_390", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def own(guard: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The guard's own project: this gate, the release workflow, and no verdict, so every deploy is refused."""
    root = _project(tmp_path / "own")
    (root / "scripts").mkdir()
    for name in ("deploy_gate.py", "brief_fields.py"):
        (root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the gate")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    monkeypatch.setattr(guard, "OWN", str(root))
    return root


@pytest.mark.parametrize("command", [
    "gh workflow run -R a/b release.yml", "gh -R a/b workflow run release", "gh run rerun --failed",
    "gh api -X POST repos/o/r/actions/workflows/release.yml/dispatches -f ref=main",
    'w=release.yml; gh workflow run "$w"', "bash -c 'gh workflow run release.yml'", "a=gh; $a run rerun 1",
])
def test_the_guard_refuses_a_dispatch_of_the_deploy_workflow(guard: ModuleType, own: Path, command: str) -> None:
    why = guard.judge_call({"tool_input": {"command": command}, "cwd": str(own)})
    assert why and "deploy gate" in why and "is a deploy" in why, (command, why)


@pytest.mark.parametrize("command", [
    "gh workflow run ci.yml", "gh run list -w release.yml", "echo 'gh workflow run release.yml'",
    "git commit -m 'gh run rerun 1'",
])
def test_the_guard_allows_what_starts_no_deploy(guard: ModuleType, own: Path, command: str) -> None:
    assert guard.judge_call({"tool_input": {"command": command}, "cwd": str(own)}) is None, command
