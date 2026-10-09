"""#249 (M21-W4): a test that runs git says so with `needs("git")`, so it skips where there is no checkout.

A seat builds a red commit with `git archive`, which has no `.git`; six tests ran `git ls-files` there
and failed with `CalledProcessError` instead of skipping. A test reaches git directly, through a helper
in its module, or through a fixture in its module; each of those needs the marker, on itself or on the
module (`pytestmark`).
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _runs_git(node: ast.AST) -> bool:
    """A call whose command line starts with "git" and that reads this checkout (`ROOT` in the call). A
    test that makes a repository of its own needs git, not this checkout, and runs in an extracted tree."""
    return any(
        isinstance(call, ast.Call)
        and "ROOT" in ast.unparse(call)
        and any(
            isinstance(arg, ast.List)
            and arg.elts
            and isinstance(arg.elts[0], ast.Constant)
            and arg.elts[0].value == "git"
            for arg in call.args
        )
        for call in ast.walk(node)
    )


def _marks_git(decorators: list[ast.expr]) -> bool:
    return any(
        "needs" in ast.unparse(d) and "'git'" in ast.unparse(d).replace('"', "'")
        for d in decorators
    )


def unmarked_git_tests(source: str) -> list[str]:
    """The tests in a module that reach git and carry no `needs("git")`, on themselves or the module."""
    tree = ast.parse(source)
    module_marked = any(
        isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in n.targets)
        and "needs" in ast.unparse(n.value)
        and "git" in ast.unparse(n.value)
        for n in tree.body
    )
    if module_marked:
        return []
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    using = {name for name, fn in functions.items() if _runs_git(fn)}
    for _ in range(3):  # a helper that calls a helper that runs git
        using |= {
            name
            for name, fn in functions.items()
            if any(
                isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in using
                for c in ast.walk(fn)
            )
        }
    unmarked = []
    for name, fn in functions.items():
        if not name.startswith("test_"):
            continue
        reaches = name in using or any(arg.arg in using for arg in fn.args.args)
        if reaches and not _marks_git(fn.decorator_list):
            unmarked.append(name)
    return unmarked


def test_every_test_that_runs_git_says_it_needs_git() -> None:
    """The live suite."""
    found = {
        path.name: names
        for path in sorted((ROOT / "tests").rglob("test_*.py"))
        if (names := unmarked_git_tests(path.read_text(encoding="utf-8")))
    }
    assert found == {}, found


def test_the_check_sees_git_through_a_helper_and_a_fixture_and_honours_the_marker() -> None:
    """Shown red on planted shapes, and quiet on marked ones."""
    plain = 'import subprocess\ndef test_a():\n    subprocess.run(["git", "ls-files"], cwd=ROOT)\n'
    helper = 'def listed():\n    return run(["git", "ls-files"], cwd=ROOT)\ndef test_b():\n    listed()\n'
    fixture = 'import pytest\n@pytest.fixture\ndef repo():\n    run(["git", "log"], cwd=ROOT)\ndef test_c(repo):\n    pass\n'
    assert unmarked_git_tests(plain) == ["test_a"]
    assert unmarked_git_tests(helper) == ["test_b"]
    assert unmarked_git_tests(fixture) == ["test_c"]
    assert unmarked_git_tests('@pytest.mark.needs("git")\n' + plain.split("\n", 1)[1]) == []
    assert unmarked_git_tests(plain + 'pytestmark = pytest.mark.needs("git")\n') == []
    assert unmarked_git_tests('def test_d():\n    run(["ls"], cwd=ROOT)\n') == []
    assert (
        unmarked_git_tests('def test_e(tmp_path):\n    run(["git", "init"], cwd=tmp_path)\n') == []
    ), "a repository of its own needs no checkout"
