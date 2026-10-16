"""The v7.1 upgrade security review's M3: `scripts/secrets_scan.py` (`make secrets`) had no test, and two
mutants passed every gate -- copying no tracked file (gitleaks then scans an empty directory and passes),
and a missing gitleaks returning 0. A stand-in `gitleaks` on PATH records what it was given to scan and
exits as told, so the wrapper is measured without the real scanner: what it hands over, and what it
returns. An empty derived set is a failure, never a pass (AGENTS.md section 3.5).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "secrets_scan.py"
SYSTEM_PATH = "/usr/bin:/bin"
FAKE = "#!/bin/sh\nfind . -type f | sort > \"$SCAN_LOG\"\nexit \"${SCAN_RC:-0}\"\n"


def _env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(extra)
    return env


def _repo(root: pathlib.Path, tracked: dict[str, str]) -> pathlib.Path:
    repo = root / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=_env(PATH=SYSTEM_PATH))
    for rel, text in tracked.items():
        (repo / rel).write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", rel], cwd=repo, check=True, env=_env(PATH=SYSTEM_PATH))
    return repo


def _scan(root: pathlib.Path, repo: pathlib.Path, rc: int = 0, fake: bool = True) -> tuple[int, list[str]]:
    path = SYSTEM_PATH
    log = root / "scanned.txt"
    if fake:
        bin_dir = root / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / "gitleaks").write_text(FAKE, encoding="utf-8")
        (bin_dir / "gitleaks").chmod(0o755)
        path = f"{bin_dir}:{SYSTEM_PATH}"
    done = subprocess.run([sys.executable, "-I", str(SCRIPT)], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", check=False, env=_env(PATH=path, SCAN_LOG=str(log), SCAN_RC=str(rc)))
    scanned = log.read_text(encoding="utf-8").split() if log.exists() else []
    return done.returncode, scanned


def test_no_gitleaks_on_path_cannot_run(tmp_path: pathlib.Path) -> None:
    assert not any(pathlib.Path(d, "gitleaks").exists() for d in SYSTEM_PATH.split(":"))
    repo = _repo(tmp_path, {"a.txt": "a\n"})
    assert _scan(tmp_path, repo, fake=False)[0] == 2


def test_a_tracked_file_is_scanned_and_an_untracked_one_is_not(tmp_path: pathlib.Path) -> None:
    repo = _repo(tmp_path, {"tracked.txt": "a\n"})
    (repo / "notes.txt").write_text("untracked\n", encoding="utf-8")
    rc, scanned = _scan(tmp_path, repo)
    assert rc == 0
    assert "./tracked.txt" in scanned
    assert "./notes.txt" not in scanned


def test_a_leak_the_scanner_reports_fails_the_gate(tmp_path: pathlib.Path) -> None:
    repo = _repo(tmp_path, {"tracked.txt": "a\n"})
    assert _scan(tmp_path, repo, rc=1)[0] == 1


def test_a_tree_that_hands_the_scanner_no_file_cannot_pass(tmp_path: pathlib.Path) -> None:
    repo = _repo(tmp_path, {})
    rc, scanned = _scan(tmp_path, repo)
    assert rc == 2
    assert scanned == []
