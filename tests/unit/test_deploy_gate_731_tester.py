"""The release delta Tester of the DevFlow v7.3.1 upgrade (D-241, 2026-11-01): #283 on v7.3's two new brief lines.

D-241 clause 2 keeps the project's base-pinned policy (#283) where v7.3's `Deploy targets:` and
`Security-invariant tests:` meet it (`bc5d9b8`'s message): a team-only target counts only when every protected
base's brief declares it too, and the invariant-tests line takes effect only when every base AND the tree carry
it -- so a change can add a deploy, or name one more invariant test, but cannot lower what a deploy owes.
`conformance/test-deploy-classes.py` proves v7.3's classes in repositories whose only base is HEAD's own branch,
so no case there has a change whose brief differs from its base's: two faults stayed green on every test --
F-P9 (a team-only entry taken from the tree alone) and F-P10a (the invariant-tests line read in the tree alone,
so the change could drop a glob the base names, or name none).

D-233 (the pin read at every protected base) meets v7.3's reviewer-profile `model:` exemption in
`shipped_unchanged`: a profile less its frontmatter `model:` line must match the bytes EVERY pin holds. Every
fixture of the exemption pins one commit at both bases, so F-P7c (the profile compared with the first pin alone)
stayed green: a branch cut before an upgrade put the older profile back, with a `model:` line, unreviewed.

Each case runs the real entry point, `scripts/deploy_gate.py` as a program -- the by-hand command form the Bash
guard's `--judge` shares (`judge`), and `--check` -- in a throwaway repository whose `main` is the protected base
and whose `change` branch is the change, with a `gh` on PATH that says CI is green on HEAD.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_pin import _installed

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "deploy_gate.py"
GREEN_GH = '#!/bin/sh\n[ "$1 $2" = "run list" ] || exit 1\necho \'[{"status": "completed", "conclusion": "success"}]\'\n'


def _env(tmp: Path, gh: str = GREEN_GH) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    (tmp / "bin").mkdir(parents=True, exist_ok=True)
    (tmp / "bin" / "gh").write_text(gh, encoding="utf-8")
    (tmp / "bin" / "gh").chmod(0o755)
    env["PATH"] = f"{tmp / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    return env


def _git(root: Path, env: dict[str, str], *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                          cwd=root, capture_output=True, text=True, check=True, env=env, timeout=60).stdout.strip()


def _gate(root: Path, env: dict[str, str], *argv: str) -> tuple[int, str]:
    done = subprocess.run([sys.executable, str(SCRIPT), *argv], cwd=root, capture_output=True, text=True,
                          check=False, env=env, timeout=120)
    return done.returncode, done.stdout + done.stderr


def _write(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


def _brief(*lines: str) -> str:
    return "\n".join(["---", "record_type: brief", "id: project-brief", "status: draft", "---",
                      "- **Working mode:** `light`", *lines]) + "\n"


def _verdict(root: Path, name: str, head: str) -> None:
    _write(root, f"docs/reviews/{name}", f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {head}\n")


def _commit(root: Path, env: dict[str, str], msg: str) -> str:
    _git(root, env, "add", "-A")
    _git(root, env, "commit", "-q", "-m", msg)
    return _git(root, env, "rev-parse", "HEAD")


def _staging_ready(tmp: Path, base_lines: tuple[str, ...], change_lines: tuple[str, ...]) -> tuple[Path, dict]:
    """`main` with `base_lines` in its brief and both verdicts at its head; `change` with `change_lines`, a product
    change only the Tester has seen (the security verdict is stale), and an `unreleased` line naming HEAD: what a
    team-only deploy owes and a production one does not have."""
    root, env = tmp / "p", _env(tmp)
    root.mkdir()
    _git(root, env, "init", "-q", "-b", "main")
    _write(root, "docs/project-brief.md", _brief(*base_lines))
    _write(root, "src/a.py", "a = 1\n")
    head = _commit(root, env, "base")
    _verdict(root, "release-security.md", head)
    _verdict(root, "release-tester.md", head)
    _commit(root, env, "docs: the verdicts")
    _git(root, env, "checkout", "-q", "-b", "change")
    _write(root, "docs/project-brief.md", _brief(*change_lines))
    _write(root, "src/a.py", "a = 2\n")
    head = _commit(root, env, "the change")
    _verdict(root, "release-tester.md", head)
    _write(root, "docs/releases/unreleased.md", f"- 2026-11-01, staging, {head[:7]}: a is 2 (unreleased)\n")
    _commit(root, env, "docs: the Tester's delta and the release note")
    return root, env


# covers D-241 clause 2, #283 -- a team-only target the change adds is production until a merge puts it at the base
def test_a_staging_target_only_the_change_declares_is_guarded_as_production(tmp_path: Path) -> None:
    for name, base, command in (
            ("refines a base production command", ("- **Deploy commands:** `fly deploy`",),
             "fly deploy -c fly.staging.toml"),
            ("a program the base does not declare at all", (), "./stg.sh")):
        targets = "- **Deploy targets:** `staging: fly deploy -c fly.staging.toml`, `staging: ./stg.sh`"
        root, env = _staging_ready(tmp_path / name.replace(" ", "-"), base, (*base, targets))
        rc, out = _gate(root, env, command)
        assert rc == 2 and "BLOCKED: deploy gate" in out and "release-security.md" in out, (name, out)
        assert "not declared at every protected base" in out and "#283" in out, (name, out)


# covers D-241 clause 2, #283 -- the control: the same target at the base is staging, and owes no security delta
def test_the_same_staging_target_at_the_base_is_staging(tmp_path: Path) -> None:
    targets = "- **Deploy targets:** `staging: fly deploy -c fly.staging.toml`, `staging: ./stg.sh`"
    lines = ("- **Deploy commands:** `fly deploy`", targets)
    root, env = _staging_ready(tmp_path, lines, lines)
    for command in ("fly deploy -c fly.staging.toml", "./stg.sh"):
        rc, out = _gate(root, env, command)
        assert rc == 0, (command, out)
    rc, out = _gate(root, env, "fly deploy")
    assert rc == 2 and "release-security.md" in out, out


def _tests_changed(tmp: Path, base_lines: tuple[str, ...], change_lines: tuple[str, ...],
                   edit: str = "tests/test_app.py", gh: str = GREEN_GH) -> tuple[Path, dict]:
    """`main` with `base_lines` and both verdicts current; `change` with `change_lines` and one test changed."""
    root, env = tmp / "p", _env(tmp, gh)
    root.mkdir()
    _git(root, env, "init", "-q", "-b", "main")
    _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", *base_lines))
    _write(root, "src/a.py", "a = 1\n")
    _write(root, "tests/test_app.py", "def test_x():\n    assert 1\n")
    _write(root, "tests/test_tenant_scope.py", "def test_scope():\n    assert scope_of('a') == 'tenant-a'\n")
    head = _commit(root, env, "base")
    _verdict(root, "release-security.md", head)
    _verdict(root, "release-tester.md", head)
    _commit(root, env, "docs: the verdicts")
    _git(root, env, "checkout", "-q", "-b", "change")
    _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", *change_lines))
    _write(root, edit, "def test_x():\n    assert True\n")
    _commit(root, env, "a test change")
    return root, env


# covers D-241 clause 2, #283 -- a change cannot opt itself into "a test change re-opens no verdict"
def test_an_invariant_tests_line_only_the_change_writes_keeps_every_test_code(tmp_path: Path) -> None:
    for line in ("- **Security-invariant tests:** `none`", "- **Security-invariant tests:** `tests/test_tenant_*.py`"):
        root, env = _tests_changed(tmp_path / str(len(line)), (), (line,))
        rc, out = _gate(root, env, "--check")
        assert rc == 1 and "tests/test_app.py" in out, (line, out)
        rc, out = _gate(root, env, "./deploy.sh prod")
        assert rc == 2 and "BLOCKED: deploy gate" in out, (line, out)


# covers D-241 clause 2, #283 -- the change cannot drop an invariant test the base names, nor the base's line
def test_the_change_cannot_drop_an_invariant_test_the_base_names(tmp_path: Path) -> None:
    base = ("- **Security-invariant tests:** `tests/test_tenant_*.py`",)
    for name, change in (("none", ("- **Security-invariant tests:** `none`",)), ("other", (
            "- **Security-invariant tests:** `tests/test_other.py`",))):
        root, env = _tests_changed(tmp_path / name, base, change, edit="tests/test_tenant_scope.py")
        rc, out = _gate(root, env, "--check")
        assert rc == 1 and "tests/test_tenant_scope.py" in out, (name, out)


# covers D-241 clause 2, #283 -- the control: with the line at the base and in the tree, CI green, a test change
# re-opens neither verdict (v7.3's harvest Q2), so the two tests above can pass
def test_the_line_at_the_base_and_in_the_tree_lets_a_test_change_pass(tmp_path: Path) -> None:
    line = ("- **Security-invariant tests:** `tests/test_tenant_*.py`",)
    root, env = _tests_changed(tmp_path, line, line)
    rc, out = _gate(root, env, "--check")
    assert rc == 0 and "deploy-check PASS" in out, out



MIXED_GH = ('#!/bin/sh\n[ "$1 $2" = "run list" ] || exit 1\n'
            'echo \'[{"status": "completed", "conclusion": "success"}, {"status": "completed", "conclusion": "failure"}]\'\n')


# covers v7.3 harvest Q2(b) -- "CI green on HEAD" is every run, not one: a failed run beside a passing one is not green
def test_one_failed_run_beside_a_passing_one_is_not_green(tmp_path: Path) -> None:
    line = ("- **Security-invariant tests:** `tests/test_tenant_*.py`",)
    root, env = _tests_changed(tmp_path, line, line, gh=MIXED_GH)
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/test_app.py" in out and "CI is not green" in out, out

PROFILE_OLD = "---\nname: tester\ndescription: x\n---\n# Tester\nEvery criterion needs a citing test.\n"
PROFILE_NEW = "---\nname: tester\ndescription: x\n---\n# Tester\nEvery criterion needs a citing test, run red.\n"


def _with_model(profile: str) -> str:
    return profile.replace("description: x\n", "description: x\nmodel: sonnet\n", 1)


# covers D-233, D-241 clause 3 -- the `model:` exemption reads the bytes every pin holds, as every other file
def test_a_branch_cut_before_an_upgrade_cannot_restore_an_older_profile_with_a_model_line(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, ".claude/agents/Tester.md", PROFILE_OLD)   # v9.10 ships the profile, pinned on main
    before = repo.git("rev-parse", "main")
    repo.git("checkout", "-q", "main")
    repo.write(".claude/agents/Tester.md", PROFILE_NEW)
    shipped = repo.commit("DevFlow v9.11 changes what the Tester reviews")
    repo.write("docs/devflow-pin.txt", f"v9.11 {shipped}\n")
    head = repo.commit("pin v9.11")
    verdict = f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n"
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", verdict)
    repo.commit("verdicts after v9.11")

    # The control: on main's history, v9.11's profile plus the project's `model:` line is DevFlow's.
    repo.git("checkout", "-q", "-b", "current", "main")
    repo.write(".claude/agents/Tester.md", _with_model(PROFILE_NEW))
    repo.commit("the reviewers' model")
    code, out = repo.check()
    assert code == 0, out

    # Cut before v9.11: its merge-base pins v9.10, whose profile this is, but main's tip pins v9.11.
    repo.git("checkout", "-q", "-b", "old", before)
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", verdict)
    repo.write(".claude/agents/Tester.md", _with_model(PROFILE_OLD))
    repo.commit("the newer verdicts on the older profile, with a model line")
    code, out = repo.check()
    assert code != 0 and ".claude/agents/Tester.md" in out, out
