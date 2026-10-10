"""The owner's ruling of 2026-10-10 on `commit-after-check-fast` ("fix and narrow").

`.githooks/pre-commit` (installed by `make hooks`) asks `scripts/commit_gate.py` which gate a commit's
staged paths need, and refuses the commit when that gate fails:
- a docs-only commit runs `make check-records`;
- any other commit runs `make check-fast`.
Docs-only means every staged path ends in `.md` and lies outside the code directories (CODE_DIRS:
`src/`, `tests/`, `ios/`, `scripts/`, `conformance/`, `.claude/`, `.githooks/`, `.github/`). A non-Markdown
file under `docs/` (the ledger, a probe run's JSON) is not docs-only: the gates read it.

The hook tests build a repository of their own, with a stub `make` that records what it was asked.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("commit_gate", ROOT / "scripts" / "commit_gate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("paths", "target"), [
    (["docs/process-log.md"], "check-records"),
    (["AGENTS.md", "INSTALL.md", "docs/decisions.md", ".agents/rules/practices.md"], "check-records"),
    ([], "check-records"),
    (["docs/control-events.csv"], "check-fast"),
    (["docs/research/m21-w2-runs/x.json"], "check-fast"),
    (["src/app/adapter/main.py"], "check-fast"),
    (["docs/prd.md", "scripts/wave_check.py"], "check-fast"),
    (["tests/unit/README.md"], "check-fast"),
    (["ios/README.md"], "check-fast"),
    (["scripts/router_probe/README.md"], "check-fast"),
    ([".claude/skills/fix-issue/SKILL.md"], "check-fast"),
    ([".githooks/README.md"], "check-fast"),
    ([".github/PULL_REQUEST_TEMPLATE.md"], "check-fast"),
    (["conformance/README.md"], "check-fast"),
    (["docs/release-testflight.MD"], "check-fast"),
])
def test_docs_only_is_markdown_outside_the_code_directories(paths: list[str], target: str) -> None:
    assert _gate().target(paths) == target


def _repo(tmp_path: Path, make_exit: int) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    (repo / ".githooks").mkdir(parents=True)
    (repo / "scripts").mkdir()
    shutil.copy(ROOT / ".githooks" / "pre-commit", repo / ".githooks" / "pre-commit")
    shutil.copy(ROOT / "scripts" / "commit_gate.py", repo / "scripts" / "commit_gate.py")
    log = tmp_path / "make.log"
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "make").write_text(f"#!/bin/sh\necho \"$*\" >> '{log}'\nexit {make_exit}\n", encoding="utf-8")
    (stub / "make").chmod(0o755)
    env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    for args in (["init", "-q", "-b", "main"], ["config", "core.hooksPath", ".githooks"]):
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, timeout=30)
    return repo, log, env


def _commit(repo: Path, env: dict[str, str], path: str) -> subprocess.CompletedProcess[str]:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", path], cwd=repo, env=env, check=True, capture_output=True, timeout=30)
    return subprocess.run(["git", "commit", "-q", "-m", path], cwd=repo, env=env, capture_output=True, text=True,
                          timeout=60, check=False)


def test_the_hook_runs_check_records_for_docs_and_check_fast_for_the_rest(tmp_path: Path) -> None:
    repo, log, env = _repo(tmp_path, make_exit=0)
    assert _commit(repo, env, "docs/notes.md").returncode == 0
    assert _commit(repo, env, "src/app/x.py").returncode == 0
    assert log.read_text(encoding="utf-8").split() == ["check-records", "check-fast"]


def test_the_hook_refuses_the_commit_when_its_gate_fails(tmp_path: Path) -> None:
    repo, log, env = _repo(tmp_path, make_exit=2)
    done = _commit(repo, env, "src/app/x.py")
    assert done.returncode != 0 and "REFUSED" in done.stdout + done.stderr, done
    head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], cwd=repo, env=env, capture_output=True,
                          text=True, timeout=30, check=False)
    assert head.returncode != 0, "a refused commit was made"
