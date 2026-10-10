"""The owner's ruling of 2026-10-10 on `commit-after-check-fast` ("fix and narrow"), as the M21 closure applies it
after its fixes review's B1, M1 and M2.

`.githooks/commit-msg` (installed by `make hooks`) asks `scripts/commit_gate.py` which gate a commit needs, from
its staged paths and its subject, and refuses the commit when that gate fails:
- `check-docs` when every staged path is docs-only: a Markdown file outside the code directories (CODE_DIRS);
  it is `make check-fast` without the Swift tests and the compiled gate, which read no Markdown;
- `check-red` for a declared red test commit: the subject starts `test:` and says `red`, and a staged path is a
  test; it is `make check-fast` without the legs that run tests;
- `check-fast` for any other commit.
The hook reads the staged paths with `--no-renames`, so both sides of a rename count, and runs `HEAD`'s copy of
the gate, so a commit that changes the gate is not judged by its own change.

The hook tests build a repository of their own, with a stub `make` that records what it was asked.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
RED = "test: the thing fails, red -- #1 (M30-W1)"


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("commit_gate", ROOT / "scripts" / "commit_gate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("paths", "subject", "target"), [
    (["docs/process-log.md"], "docs: x", "check-docs"),
    (["AGENTS.md", "INSTALL.md", "docs/decisions.md", ".agents/rules/practices.md"], "docs: x", "check-docs"),
    # Round 2, M1: nothing staged (a reworded amend) is judged as any commit is, never as docs-only.
    ([], "docs: x", "check-fast"),
    ([], RED, "check-fast"),
    (["docs/control-events.csv"], "docs: x", "check-fast"),
    (["src/app/adapter/main.py"], "fix: x", "check-fast"),
    (["tests/unit/README.md"], "docs: x", "check-fast"),
    ([".claude/skills/fix-issue/SKILL.md"], "docs: x", "check-fast"),
    (["docs/release-testflight.MD"], "docs: x", "check-fast"),
    # B1: a declared red test commit
    (["tests/unit/test_x.py"], RED, "check-red"),
    (["tests/unit/test_x.py", "src/app/x.py"], RED, "check-red"),
    (["ios/EngineTests/XTests.swift", "ios/EngineTests/test-manifest.txt"], RED, "check-red"),
    (["ios/UITests/XTests.swift"], RED, "check-red"),
    (["conformance/test-x.py"], RED, "check-red"),
    (["tests/unit/test_x.py"], "test: the RED case of x", "check-red"),
    (["tests/unit/test_x.py"], "test: x (red)", "check-red"),
    # Round 2, M1: `red` as a word of its own, not inside `red-to-green` or `red-ish`.
    (["tests/unit/test_x.py", "src/app/x.py"], "test: the red-to-green order holds", "check-fast"),
    (["tests/unit/test_x.py"], "test: a red-ish case", "check-fast"),
    (["tests/unit/test_x.py"], "test: the pre-red state", "check-fast"),
    (["tests/unit/test_x.py"], "test: x holds", "check-fast"),
    (["tests/unit/test_x.py"], "test: reduce the noise", "check-fast"),
    (["tests/unit/test_x.py"], "fix: the red test passes", "check-fast"),
    (["src/app/x.py"], RED, "check-fast"),
])
def test_the_gate_reads_the_paths_and_the_subject(paths: list[str], subject: str, target: str) -> None:
    assert _gate().target(paths, subject) == target


def _repo(tmp_path: Path, make_exit: int = 0, with_make: bool = True) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    (repo / ".githooks").mkdir(parents=True)
    (repo / "scripts").mkdir()
    shutil.copy(ROOT / ".githooks" / "commit-msg", repo / ".githooks" / "commit-msg")
    shutil.copy(ROOT / "scripts" / "commit_gate.py", repo / "scripts" / "commit_gate.py")
    log = tmp_path / "make.log"
    stub = tmp_path / "bin"
    stub.mkdir()
    if with_make:
        (stub / "make").write_text(f"#!/bin/sh\necho \"$*\" >> '{log}'\nexit {make_exit}\n", encoding="utf-8")
        (stub / "make").chmod(0o755)
    if with_make:
        path = f"{stub}{os.pathsep}{os.environ['PATH']}"
    else:  # the tools the hook runs, and no make
        for tool in ("bash", "sh", "env", "git", "python3", "mktemp", "rm", "cat", "dirname", "basename"):
            found = shutil.which(tool)
            if found:
                (stub / tool).symlink_to(found)
        path = str(stub)
    env = {**os.environ, "PATH": path, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    git = shutil.which("git", path=os.environ["PATH"]) or "git"
    for args in (["init", "-q", "-b", "main"], ["config", "core.hooksPath", ".githooks"]):
        subprocess.run([git, *args], cwd=repo, env=env, check=True, capture_output=True, timeout=30)
    env["GIT"] = git
    return repo, log, env


def _git(repo: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([env["GIT"], *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60,
                          check=False)


def _commit(repo: Path, env: dict[str, str], path: str, subject: str = "") -> subprocess.CompletedProcess[str]:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(f"{path}\n", encoding="utf-8")
    _git(repo, env, "add", path)
    return _git(repo, env, "commit", "-q", "-m", subject or path)


def _logged(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").split() if log.exists() else []


def test_a_merge_is_never_docs_only_or_red() -> None:
    """Round 2, M4: a merge brings in what its other parent holds, so neither its diff nor its subject
    narrows its gate."""
    assert _gate().target(["docs/notes.md"], "docs: x", merge=True) == "check-fast"
    assert _gate().target(["tests/unit/test_x.py"], RED, merge=True) == "check-fast"


def _editor(tmp_path: Path, message: str) -> str:
    """A GIT_EDITOR that writes `message` above git's own template, as a person typing in the editor does."""
    script = tmp_path / "editor.py"
    script.write_text("import sys\nfrom pathlib import Path\nf = Path(sys.argv[1])\n"
                      f"f.write_text({message!r} + '\\n' + f.read_text(encoding='utf-8'), encoding='utf-8')\n",
                      encoding="utf-8")
    return f"{sys.executable} {script}"


@pytest.mark.parametrize(("form", "message", "target"), [
    ("-m", ["test: e, red"], "check-red"),
    # Under -m git keeps a `#` line: the subject is `#241 wire e`, which declares nothing (the review's probe).
    ("-m", ["#241 wire e", "test: e, red"], "check-fast"),
    ("-m", ["test: y\n# red"], "check-red"),
    # In the editor git strips its comment lines, the template's and any typed.
    ("editor", "test: x, red", "check-red"),
    ("editor", "# a note to self\ntest: y, red", "check-red"),
    ("editor", "test: y\n# red", "check-fast"),
])
def test_the_subject_is_read_as_git_records_it(tmp_path: Path, form: str, message: str | list[str],
                                               target: str) -> None:
    """Round 2, M1 and M7: the hook skipped every `#` line, which git keeps under `-m`, so it read `test: e,
    red` where git recorded `#241 wire e` (mutant X4 survived: no test gave it git's comment lines). The gate
    reads the subject under the cleanup git applies, and agrees with the `%s` git records."""
    repo, log, env = _repo(tmp_path)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, env, "add", "tests/test_x.py")
    if form == "-m":
        done = _git(repo, env, "commit", "-q", *[a for line in message for a in ("-m", line)])
    else:
        done = subprocess.run([env["GIT"], "commit", "-q"], cwd=repo, env={**env, "GIT_EDITOR": _editor(tmp_path, str(message))},
                              capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 0, done
    recorded = _git(repo, env, "log", "-1", "--format=%s").stdout.strip()
    assert _logged(log) == [target] == [_gate().target(["tests/test_x.py"], recorded)], recorded


def test_a_reworded_amend_runs_check_fast(tmp_path: Path) -> None:
    """Round 2, M1: an amend that only rewords stages nothing, and was gated as docs-only, so a Swift red commit
    reworded to `fix:` landed without the Swift tests."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "tests/unit/test_x.py", RED).returncode == 0
    assert _git(repo, env, "commit", "-q", "--amend", "-m", "fix: x").returncode == 0
    assert _logged(log) == ["check-red", "check-fast"]


def test_the_hook_gates_a_merge_with_check_fast(tmp_path: Path) -> None:
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "src/app/x.py", "fix: x").returncode == 0
    _git(repo, env, "checkout", "-q", "-b", "side")
    assert _commit(repo, env, "docs/notes.md", "docs: notes").returncode == 0
    _git(repo, env, "checkout", "-q", "main")
    assert _git(repo, env, "merge", "-q", "--no-ff", "--no-edit", "side").returncode == 0
    assert _logged(log) == ["check-fast", "check-docs", "check-fast"]


def test_the_hook_is_commit_msg_and_the_pre_commit_hook_is_gone() -> None:
    """B1: the gate needs the subject, which only commit-msg sees; commit-msg runs on `git merge` too."""
    assert (ROOT / ".githooks" / "commit-msg").is_file()
    assert not (ROOT / ".githooks" / "pre-commit").exists()


def test_the_hook_runs_each_target_by_the_commit(tmp_path: Path) -> None:
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "docs/notes.md").returncode == 0
    assert _commit(repo, env, "src/app/x.py", "fix: x").returncode == 0
    assert _commit(repo, env, "tests/unit/test_x.py", RED).returncode == 0
    assert _logged(log) == ["check-docs", "check-fast", "check-red"]


def test_the_hook_refuses_the_commit_when_its_gate_fails(tmp_path: Path) -> None:
    repo, _, env = _repo(tmp_path, make_exit=2)
    done = _commit(repo, env, "src/app/x.py", "fix: x")
    assert done.returncode != 0 and "REFUSED" in done.stdout + done.stderr, done
    assert _git(repo, env, "rev-parse", "--verify", "-q", "HEAD").returncode != 0, "a refused commit was made"


def test_a_rename_out_of_the_code_directories_counts_both_paths(tmp_path: Path) -> None:
    """M1: `git mv tests/unit/test_x.py docs/test_x.md` was gated as docs-only."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "tests/unit/test_x.py", "fix: x").returncode == 0
    (repo / "docs").mkdir()
    assert _git(repo, env, "mv", "tests/unit/test_x.py", "docs/test_x.md").returncode == 0
    assert _git(repo, env, "commit", "-q", "-m", "docs: move").returncode == 0
    assert _logged(log)[-1] == "check-fast"


def test_a_commit_that_changes_the_gate_is_judged_by_heads_copy(tmp_path: Path) -> None:
    """M1: the hook ran the working tree's gate, so a commit changing the gate judged itself."""
    repo, log, env = _repo(tmp_path)
    _git(repo, env, "add", "scripts/commit_gate.py")
    assert _git(repo, env, "commit", "-q", "-m", "fix: the gate").returncode == 0
    gate = repo / "scripts" / "commit_gate.py"
    gate.write_text(gate.read_text(encoding="utf-8").replace('return "check-fast"', 'return "check-docs"'),
                    encoding="utf-8")
    _git(repo, env, "add", "scripts/commit_gate.py")
    assert _commit(repo, env, "src/app/x.py", "fix: x").returncode == 0
    assert _logged(log)[-1] == "check-fast"


def test_a_missing_make_is_said_as_such(tmp_path: Path) -> None:
    """M1: with no make on PATH the hook refused, saying `make check-fast failed above`."""
    repo, _, env = _repo(tmp_path, with_make=False)
    done = _commit(repo, env, "src/app/x.py", "fix: x")
    assert done.returncode != 0 and "make not found" in done.stdout + done.stderr, done


def test_the_swift_tests_and_the_compiled_gate_read_no_markdown() -> None:
    """M2: `check-docs` leaves out the Swift tests and the compiled gate because neither reads a Markdown file;
    their comments and docstrings may cite one."""
    for swift in sorted((ROOT / "ios").glob("*Tests/**/*.swift")):
        code = re.sub(r"/\*.*?\*/", "", swift.read_text(encoding="utf-8"), flags=re.S)
        code = "\n".join(line.split("//", 1)[0] for line in code.splitlines())
        assert ".md" not in code, f"{swift.relative_to(ROOT)} reads a Markdown file"
    gate = ROOT / "scripts" / "client_decl_gate.py"
    tree = ast.parse(gate.read_text(encoding="utf-8"))
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
                  and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
    reads = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
             and id(node) not in docstrings and re.search(r"\.md\b", node.value)]
    assert reads == [], f"client_decl_gate.py names a Markdown file in code: {reads}"


def test_r1_says_who_checks_a_red_commit_and_claims_no_check_nobody_holds() -> None:
    """Round 2, M1: R-1 and the gate said the Tester checks that each red commit fails only on its own tests, and
    no role definition holds that check. R-1 says who does check a red commit, and that it may carry code."""
    r1 = next(line for line in (ROOT / "docs" / "refusals.md").read_text(encoding="utf-8").splitlines()
              if line.startswith("| R-1 |"))
    gate = (ROOT / "scripts" / "commit_gate.py").read_text(encoding="utf-8")
    for text in (r1, gate):
        assert "Tester checks that each" not in re.sub(r"\s+", " ", text)
    assert "SKILL.md" in r1 and "no role definition" in r1 and "may carry code" in r1, r1
    assert "swift-build-tests" in r1 and "pytest-collect" in r1, r1


def test_the_hook_runs_only_the_three_gates(tmp_path: Path) -> None:
    """Round 2, R1: the hook ran whatever name HEAD's gate printed, so a committed gate that printed `help` let
    the next commit pass on `make help`. A name other than check-fast, check-red or check-docs is refused."""
    repo, log, env = _repo(tmp_path)
    _git(repo, env, "add", "scripts/commit_gate.py")
    assert _commit(repo, env, "src/app/x.py", "fix: x").returncode == 0
    (repo / "scripts" / "commit_gate.py").write_text("print('help')\n", encoding="utf-8")
    _git(repo, env, "add", "scripts/commit_gate.py")
    assert _git(repo, env, "commit", "-q", "-m", "fix: the gate").returncode == 0  # judged by HEAD's real gate
    done = _commit(repo, env, "src/app/y.py", "fix: y")
    assert done.returncode != 0 and "help" in done.stderr and "REFUSED" in done.stderr, done
    assert "help" not in _logged(log)
