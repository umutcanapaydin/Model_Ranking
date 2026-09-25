"""#32 -- the engine keeps running: a launchd service for the engine itself.

Since D-154 the engine refreshes itself nightly, and since #16 nothing else does. The engine was
started only by hand (`./ios/app.sh up`), so after a restart nothing refreshed, and nothing said
so (2026-09-24 to 2026-09-25). The owner ruled (2026-09-25) that a service keeps the engine up.

Nothing here installs a launchd job: that is the owner's action on his machine. These tests hold
the pieces to each other and to the W-096 lessons (launchd cannot open a program or a log under
`~/Desktop`, where the repository lives), and they run `scripts/engine_service.sh` against a
scratch git repository to prove the branch gate: a service must never run a branch checkout as
the engine, the trap the old launchd refresher had.
"""

from __future__ import annotations

import os
import plistlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts" / "engine_service.sh"
INSTALLER = REPO / "scripts" / "install_engine_service.sh"
REMOVER = REPO / "scripts" / "remove_engine_service.sh"
APP_SH = REPO / "ios" / "app.sh"
LABEL = "com.ilgar.modelranking.engine"


def _installer(flag: str) -> str:
    return subprocess.run(["/bin/bash", str(INSTALLER), flag], capture_output=True, text=True,
                          check=True, env={**os.environ, "HOME": "/Users/probe"}).stdout


def _plist() -> dict[str, object]:
    return plistlib.loads(_installer("--print-plist").encode())


def test_the_service_keeps_the_engine_up_and_starts_at_login() -> None:
    job = _plist()
    assert job["Label"] == LABEL
    assert job["RunAtLoad"] is True
    assert job["KeepAlive"] is True
    # A crash loop must not spin: launchd waits this long between starts.
    assert isinstance(job["ThrottleInterval"], int) and job["ThrottleInterval"] >= 30


def test_launchd_is_never_asked_to_open_anything_under_desktop() -> None:
    """W-096: from 2026-08-27 to 2026-09-20 a job whose program lived under ~/Desktop exited 78 on
    every trigger and wrote nothing. The program is /bin/bash on a wrapper in Application Support,
    and the logs are under ~/Library/Logs."""
    job = _plist()
    arguments = job["ProgramArguments"]
    assert isinstance(arguments, list) and arguments[0] == "/bin/bash"
    assert arguments[1] == "/Users/probe/Library/Application Support/model-ranking/engine_service.sh"
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert str(job[key]).startswith("/Users/probe/Library/Logs/"), key
    assert "Desktop" not in " ".join(str(a) for a in arguments)


def test_the_wrapper_runs_the_repositorys_launcher_in_service_mode() -> None:
    """One launcher, in the tree: the installed wrapper only hands over to it, so a change to the
    launcher needs no reinstall (the refresher's installed copy once drifted from the tree)."""
    wrapper = _installer("--print-wrapper")
    code = [line for line in wrapper.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert any(f'"{LAUNCHER}"' in line and "--service" in line and line.lstrip().startswith("exec")
               for line in code), wrapper


def _scratch_repo(tmp_path: Path, branch: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run([*git, "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "README").write_text("scratch\n", encoding="utf-8")
    subprocess.run([*git, "-C", str(repo), "add", "README"], check=True)
    subprocess.run([*git, "-C", str(repo), "commit", "-qm", "scratch"], check=True)
    if branch != "main":
        subprocess.run([*git, "-C", str(repo), "checkout", "-qb", branch], check=True)
    return repo


def _launch(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(LAUNCHER), *args], capture_output=True, text=True,
                          timeout=30, env={**os.environ, "MODEL_RANKING_REPO": str(repo),
                                           "ENGINE_SERVICE_WAIT_S": "0"})


def test_the_service_never_runs_a_branch_checkout_as_the_engine(tmp_path: Path) -> None:
    done = _launch(_scratch_repo(tmp_path, "wave/m99-w1"), "--service")
    assert done.returncode == 0, done.stdout + done.stderr  # waits and exits; launchd asks again
    assert "not main" in done.stdout and "not starting" in done.stdout
    assert "uvicorn" not in done.stdout


def test_on_main_the_service_goes_on_to_start_the_engine(tmp_path: Path) -> None:
    """The positive control: past the branch gate, the next thing checked is the artifact."""
    done = _launch(_scratch_repo(tmp_path, "main"), "--service")
    assert done.returncode != 0
    assert "advisor.db" in done.stdout and "not main" not in done.stdout


def test_by_hand_the_launcher_runs_any_branch(tmp_path: Path) -> None:
    """`ios/app.sh` uses the same launcher without `--service`: a developer runs branches."""
    done = _launch(_scratch_repo(tmp_path, "wave/m99-w1"))
    assert "not main" not in done.stdout and "advisor.db" in done.stdout


def test_the_launcher_starts_the_engine_the_way_the_app_script_did() -> None:
    """The engine's environment: the relaxed lane with its preflight, the served artifact, and the
    nightly refresh (D-154)."""
    text = LAUNCHER.read_text(encoding="utf-8")
    for needle in ("APP_ENV=test", "MODEL_RANKING_DB=advisor.db", "MODEL_RANKING_REFRESH=nightly",
                   "validate_startup_config", "uvicorn app.adapter.main:app", "--host 127.0.0.1"):
        assert needle in text, needle


def test_the_app_script_starts_the_engine_through_the_one_launcher_and_knows_the_service() -> None:
    text = APP_SH.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "scripts/engine_service.sh" in code, "ios/app.sh starts the engine some other way"
    assert "-m uvicorn" not in code, "ios/app.sh has its own copy of the engine's start command"
    assert LABEL in code, "ios/app.sh does not know the service, so `down` would fight KeepAlive"
    assert "launchctl bootout" in code and "launchctl bootstrap" in code


def test_the_remover_takes_off_what_the_installer_puts_on() -> None:
    installer, remover = INSTALLER.read_text(encoding="utf-8"), REMOVER.read_text(encoding="utf-8")
    for piece in (LABEL, "Library/LaunchAgents", "Application Support/model-ranking/engine_service.sh"):
        assert piece in installer and piece in remover, piece
    assert "launchctl bootout" in remover
