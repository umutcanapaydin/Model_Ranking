"""D-257 clause 4 (#639): a LOW finding is a row in `docs/later.md`, not an issue.

A findings table answers it `later`, and `make findings-check` (and wave-check, which shares the grammar) accepts
that only when the later file holds a row whose first cell names the verdict file and the id
(`fix-issue-12-security.md R1`): `later` with no row is a finding with no disposition.
# covers D-257
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "pr_check.py"
GH = ('#!/bin/sh\n[ "$1 $2" = "pr view" ] && exec cat "$FAKE_GH_DIR/pr.json"\n'
      'echo "no pull requests found" >&2\nexit 1\n')
VERDICT = ("# Security Review — fix-issue-12\n\n**Independent:** yes\n**Date:** 2026-11-26\n\n## Verdict\nMINOR\n\n"
           "## Findings\n\n### MINOR\n- **M1** src/a.py:9 — a broad except\n\n## Risks queued\n"
           "- **R1** the cache has no bound — LOW\n")
LATER = ("# Later\n\n| finding | what | why later |\n|---|---|---|\n"
         "| `fix-issue-12-security.md R1` | the cache has no bound | LOW: no user sees it (D-257) |\n")


def _wave_check():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("wave_check_d257", ROOT / "scripts" / "wave_check.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WAVE = _wave_check()


def test_later_is_a_disposition_of_the_shared_grammar() -> None:
    assert WAVE.DISPOSITION.match("later")
    assert WAVE.DISPOSITION.match("later — docs/later.md")
    assert not WAVE.DISPOSITION.match("laterally")


def test_the_later_file_yields_its_first_cells_as_keys() -> None:
    assert WAVE.later_rows(LATER) == {"fix-issue-12-security.md r1"}
    assert WAVE.later_rows("") == set()


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, capture_output=True, text=True, check=True, env=env, timeout=60).stdout.strip()


def _repo(tmp: Path, later: str | None) -> tuple[Path, str, str]:
    proj = tmp / "proj"
    proj.mkdir()
    _git(proj, "init", "-q", "-b", "main")
    (proj / "src").mkdir()
    (proj / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "base")
    base = _git(proj, "rev-parse", "HEAD")
    (proj / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "fix: a")
    fix = _git(proj, "rev-parse", "HEAD")
    (proj / "docs" / "reviews").mkdir(parents=True)
    (proj / "docs" / "reviews" / "fix-issue-12-security.md").write_text(VERDICT, encoding="utf-8")
    if later is not None:
        (proj / "docs" / "later.md").write_text(later, encoding="utf-8")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "review: the verdict")
    return proj, base, fix


def _check(tmp: Path, proj: Path, base: str, rows: str) -> tuple[int, str]:
    (tmp / "bin").mkdir(exist_ok=True)
    (tmp / "bin" / "gh").write_text(GH, encoding="utf-8")
    (tmp / "bin" / "gh").chmod(0o755)
    (tmp / "pr.json").write_text(json.dumps({"body": f"| finding | disposition |\n|---|---|\n{rows}"}), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(FAKE_GH_DIR=str(tmp), PATH=f"{tmp / 'bin'}{os.pathsep}{env.get('PATH', '')}")
    done = subprocess.run([sys.executable, str(SCRIPT), "findings", "--range", f"{base}..HEAD", "--pr", "1"],
                          cwd=proj, capture_output=True, text=True, env=env, timeout=120, check=False)
    return done.returncode, done.stdout + done.stderr


def test_a_later_finding_the_file_holds_passes(tmp_path: Path) -> None:
    proj, base, fix = _repo(tmp_path, LATER)
    rc, out = _check(tmp_path, proj, base, f"| security M1 | fixed {fix[:7]} |\n| security R1 | later |\n")
    assert rc == 0 and "findings-check PASS" in out, out


@pytest.mark.parametrize("later", [None, LATER.replace("R1", "R2")], ids=["no-file", "no-row"])
def test_a_later_finding_the_file_does_not_hold_fails(tmp_path: Path, later: str | None) -> None:
    proj, base, fix = _repo(tmp_path, later)
    rc, out = _check(tmp_path, proj, base, f"| security M1 | fixed {fix[:7]} |\n| security R1 | later |\n")
    assert rc == 1 and "R1" in out and "docs/later.md" in out, out
