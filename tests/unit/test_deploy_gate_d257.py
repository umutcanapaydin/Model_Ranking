"""D-257 clause 2 (#639): a test re-opens no deploy verdict unless `docs/security-invariants.md` cites it.

The brief's `Security-invariant tests:` line names the register instead of globs. The deploy gate derives the cited
test files from it at the tree and at every protected base (their union), and the register itself is code. A
register that cites no test, or cannot be read, fails closed: every test is code. No CI answer is needed: the night's
deploy job cannot ask GitHub (`nightly-hosted.yml`'s deploy job has no token), so the glob form's
"test-and-CI while CI is green" never let a test change through there. The glob form keeps its v7.3 meaning.
# covers D-257
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from .test_deploy_gate_731_tester import _brief, _commit, _env, _gate, _git, _verdict, _write

ROOT = Path(__file__).resolve().parents[2]
REGISTER = "docs/security-invariants.md"
LINE = f"- **Security-invariant tests:** `{REGISTER}`"
RED_GH = ('#!/bin/sh\n[ "$1 $2" = "run list" ] || exit 1\n'
          'echo \'[{"status": "completed", "conclusion": "failure"}]\'\n')
CITING = ("# Security invariants\n\n| id | invariant | source | test |\n|---|---|---|---|\n"
          "| INV-1 | A tenant sees only its rows. | D-1 | `tests/test_tenant_scope.py::test_scope`<br>"
          "`tests/test_tenant_scope.py::test_other` |\n"
          "| INV-2 | The phone pins its host. | D-2 | `ios/EngineTests/PinTests.swift::testPin` |\n"
          "| INV-3 | The lock is hashed. | D-3 | `make deps` |\n")
CITING_NONE = "# Security invariants\n\n| id | invariant | source | test |\n|---|---|---|---|\n| INV-1 | x | D-1 | `make deps` |\n"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_d257", ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _script("deploy_gate")
DERIVED = [REGISTER, "tests/test_tenant_scope.py", "ios/EngineTests/PinTests.swift"]


def test_the_register_yields_every_test_file_it_cites_and_nothing_else() -> None:
    assert GATE.register_tests(CITING) == ["ios/EngineTests/PinTests.swift", "tests/test_tenant_scope.py"]
    assert GATE.register_tests(CITING_NONE) == []


def test_a_register_on_the_line_expands_to_itself_and_its_citations() -> None:
    read = {REGISTER: CITING.encode()}.get
    assert GATE.expand_invariants([REGISTER], read) == DERIVED


@pytest.mark.parametrize("body", [CITING_NONE.encode(), None], ids=["cites-no-test", "unreadable"])
def test_a_register_that_yields_no_test_fails_closed(body: bytes | None) -> None:
    assert GATE.expand_invariants([REGISTER], {REGISTER: body}.get) is None


@pytest.mark.parametrize("path", ["tests/unit/test_api_scores.py", "tests/integration/test_live.py",
                                  "ios/EngineTests/EngineClientTests.swift"])
def test_a_test_the_register_does_not_cite_is_a_record(path: str) -> None:
    assert GATE.change_class(path, DERIVED) == "record"


@pytest.mark.parametrize("path", ["tests/test_tenant_scope.py", "ios/EngineTests/PinTests.swift", REGISTER,
                                  "tests/unit/test_deploy_gate_563.py", "src/app/x.py", "scripts/survey_boards.py"])
def test_a_cited_test_the_register_a_policy_test_and_code_stay_code(path: str) -> None:
    assert GATE.change_class(path, DERIVED) == "code"


def test_conformance_stays_test_and_ci_and_the_glob_form_keeps_its_meaning() -> None:
    assert GATE.change_class("conformance/test-prune-merged.py", DERIVED) == "test-and-ci"
    assert GATE.change_class("tests/unit/test_api_scores.py", ["tests/test_tenant_*.py"]) == "test-and-ci"
    assert GATE.change_class("tests/unit/test_api_scores.py", None) == "code"
    assert GATE.change_class(REGISTER, None) == "record"


@pytest.mark.parametrize("path", [".language-allow", ".skill-refs-allow"])
@pytest.mark.parametrize("invariants", [None, DERIVED], ids=["no-line", "register"])
def test_the_check_allow_lists_are_records(path: str, invariants: list[str] | None) -> None:
    assert GATE.change_class(path, invariants) == "record"


def _repo(tmp: Path, base_register: str | None, base_line: bool = True, gh: str = RED_GH) -> tuple[Path, dict]:
    """`main` with the register line (or none) and both verdicts current, CI red; `change` branched from it."""
    root, env = tmp / "p", _env(tmp, gh)
    root.mkdir()
    _git(root, env, "init", "-q", "-b", "main")
    _git(root, env, "remote", "add", "origin", "https://github.com/o/r.git")
    _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", *((LINE,) if base_line else ())))
    if base_register is not None:
        _write(root, REGISTER, base_register)
    _write(root, "src/a.py", "a = 1\n")
    _write(root, "tests/test_app.py", "def test_x():\n    assert 1\n")
    _write(root, "tests/test_tenant_scope.py", "def test_scope():\n    assert scope_of('a') == 'tenant-a'\n")
    head = _commit(root, env, "base")
    _verdict(root, "release-security.md", head)
    _verdict(root, "release-tester.md", head)
    _commit(root, env, "docs: the verdicts")
    _git(root, env, "checkout", "-q", "-b", "change")
    if not base_line:
        _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", LINE))
        _commit(root, env, "docs: the line, in the change only")
    return root, env


def _edit(root: Path, env: dict, rel: str, text: str = "def test_x():\n    assert True\n") -> None:
    _write(root, rel, text)
    _commit(root, env, f"change {rel}")


def test_a_test_change_passes_the_gate_with_ci_red(tmp_path: Path) -> None:
    root, env = _repo(tmp_path, CITING)
    _edit(root, env, "tests/test_app.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 0 and "deploy-check PASS" in out, out


def test_a_cited_test_change_is_refused(tmp_path: Path) -> None:
    root, env = _repo(tmp_path, CITING)
    _edit(root, env, "tests/test_tenant_scope.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/test_tenant_scope.py" in out, out


def test_dropping_a_citation_from_the_register_is_refused(tmp_path: Path) -> None:
    root, env = _repo(tmp_path, CITING)
    _edit(root, env, REGISTER, CITING_NONE)
    _edit(root, env, "tests/test_tenant_scope.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and REGISTER in out and "tests/test_tenant_scope.py" in out, out


@pytest.mark.parametrize(("register", "base_line"), [(CITING_NONE, True), (None, True), (CITING, False)],
                         ids=["register-cites-no-test", "no-register", "line-only-in-the-change"])
def test_without_a_register_every_base_derives_from_a_test_change_is_refused(
        tmp_path: Path, register: str | None, base_line: bool) -> None:
    root, env = _repo(tmp_path, register, base_line)
    if register is None:
        _write(root, REGISTER, CITING)
        _commit(root, env, "docs: a register the base does not hold")
    _edit(root, env, "tests/test_app.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/test_app.py" in out, out
