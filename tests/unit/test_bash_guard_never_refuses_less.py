"""#582 R2 (the security review of #561's owner bundle): the Bash guard never refuses less than the protected base's.

Both security rounds on run 1102 found a guard or reader change that refused less than the code it replaced (#553's
first reader, #561's first split), and only a reviewer's differential caught it. This is that differential as a test:
the guard at the protected base (the merge-base with the default branch, read from git, never from the change) and the
guard in this tree judge every command written in the guard's two corpora, and a command the base refuses and this
tree allows fails the test -- unless it is named in DELIBERATE_LOOSENINGS with its reason.

It fails closed: no base, a base guard that does not load, or a corpus of fewer than MIN_CORPUS commands is a failure.
# covers #582
"""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ".claude/hooks/bash_guard.py"
CORPORA = ("tests/unit/test_bash_guard_bounds.py", "conformance/test-bash-guard.py")
MIN_CORPUS = 500
#: A command this tree allows on purpose although the base refused it: command -> the ADR or issue that says why.
#: A hand-kept list, named and with a reason each (AGENTS.md 3.5); empty while no loosening is deliberate.
DELIBERATE_LOOSENINGS: dict[str, str] = {}

sys.path.insert(0, str(ROOT / "scripts"))
import brief_fields  # noqa: E402

pytestmark = pytest.mark.needs("git")


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # its dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


def corpus() -> list[str]:
    """Every one-line string literal in the corpora that reads as a command: a lower-case or path-like first
    character (a docstring or a message starts with a capital), at most 400 characters."""
    found: dict[str, None] = {}
    for rel in CORPORA:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if 3 <= len(text) <= 400 and "\n" not in text and (text[0].islower() or text[0] in "./~$({!\"'"):
                    found[text] = None
    return list(found)


def _judge(guard: ModuleType, call: dict) -> str | None:
    """As the hook's `main` judges a call: a call the guard cannot read, or any error, is a refusal."""
    try:
        why: str | None = guard.judge_call(dict(call))
        return why
    except BaseException as error:  # the hook refuses on any doubt, and so does this reading
        return f"BLOCKED: cannot read ({type(error).__name__})"


def refused_less(base: ModuleType, head: ModuleType, commands: list[str], cwd: Path) -> list[str]:
    """The commands `base` refuses and `head` allows, judged as the hook judges a Bash call from `cwd`."""
    out: list[str] = []
    for command in commands:
        call = {"tool_input": {"command": command}, "cwd": str(cwd)}
        if _judge(base, call) and not _judge(head, call) and command not in DELIBERATE_LOOSENINGS:
            out.append(command)
    return out


@pytest.fixture(scope="module")
def guards(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[ModuleType, ModuleType, Path]]:
    base = brief_fields.protected_base(ROOT)
    assert base, "no protected base: the differential has nothing to compare against (fail closed)"
    blob = subprocess.run(["git", "show", f"{base}:{GUARD}"], cwd=ROOT, capture_output=True, check=False)
    assert blob.returncode == 0 and blob.stdout, blob.stderr
    where = tmp_path_factory.mktemp("guard-differential")
    (where / "base_guard.py").write_bytes(blob.stdout)
    elsewhere, own, repo = where / "elsewhere", where / "own", where / "repo"
    for d in (elsewhere, own, *(repo / sub for sub in (".git", ".claude/hooks", ".claude/worktrees", ".githooks"))):
        d.mkdir(parents=True)
    saved = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = str(elsewhere)  # no brief: no deploy gate in either reading
    try:
        loaded = (_load(where / "base_guard.py", "bash_guard_base_582"), _load(ROOT / GUARD, "bash_guard_head_582"))
        for module in loaded:
            module.OWN = str(own)
        yield loaded[0], loaded[1], repo
    finally:
        if saved is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = saved


def test_582_the_corpus_is_not_empty() -> None:
    assert len(corpus()) >= MIN_CORPUS, len(corpus())


def test_582_the_guard_never_refuses_less_than_the_protected_base(guards: tuple[ModuleType, ModuleType, Path]) -> None:
    base, head, repo = guards
    assert refused_less(base, head, corpus(), repo) == []


def test_582_the_control_a_loosened_guard_is_caught(guards: tuple[ModuleType, ModuleType, Path],
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """Can the check fail at all: a head that allows one command the base refuses is reported."""
    base, head, repo = guards
    command = "git push --force origin main"
    real = head.judge_call
    monkeypatch.setattr(head, "judge_call", lambda call: None if call["tool_input"]["command"] == command else real(call))
    assert refused_less(base, head, [command, "git status"], repo) == [command]
