"""#139, D-222: `make ui-test` starts its engine from a copy of the artifact MODEL_RANKING_DB names, else
the checkout's `advisor.db` (D-175).

It once preferred the artifact the Mac's engine service served; that service is retired (#427), so its
folder is no longer read. An artifact older than the screen is refused instead (#139). Each test runs a copy of `scripts/ui_test.sh` in a scratch layout of the repository,
with a stub `xcodebuild` that fails at once: the script stops after copying the artifact it chose,
and no build, simulator or engine is ever started.
"""

from __future__ import annotations

import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
#: Where the retired Mac service kept its artifact (D-222): planted to show it is no longer read.
SERVED = Path("Library/Application Support/model-ranking/engine/data/advisor.db")


def _artifact(path: Path, name: str) -> None:
    """Enough of an artifact for the script's check (#139): a row of a declared Arena slice, and a
    mark that says which artifact the engine would have started from."""
    from app.workflows.board_tables import ARENA_SLICES

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE scores (model_id TEXT, source TEXT, score REAL)")
        db.execute("INSERT INTO scores VALUES ('m', ?, 1.0)", (ARENA_SLICES[0].source_name,))
        db.execute("CREATE TABLE mark (name TEXT)")
        db.execute("INSERT INTO mark VALUES (?)", (name,))
    db.close()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _layout(tmp_path: Path, *, served: bool) -> dict[str, str]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "ui_test.sh", repo / "scripts" / "ui_test.sh")
    python = repo / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")  # this suite's own
    python.chmod(0o755)
    _artifact(repo / "advisor.db", "the checkout's copy")
    home = tmp_path / "home"
    if served:
        _artifact(home / SERVED, "the served artifact")
    stubs = tmp_path / "bin"
    stubs.mkdir()
    (stubs / "xcodebuild").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (stubs / "xcodebuild").chmod(0o755)
    return {"PATH": f"{stubs}:/usr/bin:/bin", "HOME": str(home), "UI_TEST_PORT": str(_free_port()),
            "UI_TEST_OUT": str(tmp_path / "out")}


def _chosen(tmp_path: Path, env: dict[str, str]) -> str:
    run = subprocess.run(["bash", str(tmp_path / "repo" / "scripts" / "ui_test.sh")], env=env,
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 1 and "the build failed" in run.stdout, run.stdout + run.stderr
    with sqlite3.connect(tmp_path / "out" / "advisor.db") as db:
        (name,) = db.execute("SELECT name FROM mark").fetchone()
    db.close()
    return str(name)


@pytest.mark.needs("bash_curl")
def test_ui_test_starts_from_the_checkout_and_reads_no_retired_service_folder(tmp_path: Path) -> None:
    """D-222 (#427): the Mac's service folder is no longer an engine's; a copy left there is not read."""
    assert _chosen(tmp_path, _layout(tmp_path, served=True)) == "the checkout's copy"
    assert _chosen(tmp_path / "bare", _layout(tmp_path / "bare", served=False)) == "the checkout's copy"


@pytest.mark.needs("bash_curl")
def test_ui_test_obeys_its_variable(tmp_path: Path) -> None:
    named = tmp_path / "named.db"
    _artifact(named, "the named artifact")
    env = {**_layout(tmp_path / "again", served=True), "MODEL_RANKING_DB": str(named)}
    assert _chosen(tmp_path / "again", env) == "the named artifact"
    assert os.environ.get("MODEL_RANKING_DB") != str(named)


#: #525: a stand-in `xcrun simctl` that keeps the device's state in a file, as CoreSimulator answers (measured
#: 2026-11-01): `uninstall` on a shut-down device fails (149, "Unable to lookup in current state: Shutdown"), and
#: on a booted one succeeds, the app installed or not; `boot` on a booted device fails (149); `bootstatus -b`
#: boots the device if it must and returns once it has. `UNINSTALL_ERROR` makes a booted device's uninstall fail.
SIMCTL = r"""#!/bin/sh
echo "xcrun $*" >> "$UI_STUB_LOG"
state="$(cat "$UI_STUB_STATE")"
case "$1 $2" in
  "simctl boot")
    [ "$state" = Booted ] && { echo "Unable to boot device in current state: Booted" >&2; exit 149; }
    echo Booted > "$UI_STUB_STATE" ;;
  "simctl bootstatus")
    case " $* " in *" -b "*) echo Booted > "$UI_STUB_STATE" ;; *) [ "$state" = Booted ] || exit 1 ;; esac ;;
  "simctl uninstall")
    [ "$state" = Booted ] || { echo "Unable to lookup in current state: $state" >&2; exit 149; }
    [ -z "${UNINSTALL_ERROR:-}" ] || { echo "$UNINSTALL_ERROR" >&2; exit 1; }
    echo "removed $4" >> "$UI_STUB_LOG" ;;
esac
exit 0
"""
#: xcodebuild passes, and shuts the device down after a test pass, as it does after a pass it booted it for.
XCODEBUILD = r"""#!/bin/sh
echo "xcodebuild $1 $*" >> "$UI_STUB_LOG"
[ "$1" = test-without-building ] && echo Shutdown > "$UI_STUB_STATE"
exit 0
"""


def _harness(tmp_path: Path, **extra: str) -> tuple[dict[str, str], Path]:
    """The whole script on stand-ins: the build, both passes and the simulator are stubs, and the engine is a
    plain HTTP server whose `/health` answers, so the passes run in order and nothing real is started."""
    env = _layout(tmp_path, served=False)
    stubs, log, state = Path(env["PATH"].split(":")[0]), tmp_path / "calls.log", tmp_path / "device-state"
    state.write_text("Shutdown\n", encoding="utf-8")
    (stubs / "xcrun").write_text(SIMCTL, encoding="utf-8")
    (stubs / "xcodebuild").write_text(XCODEBUILD, encoding="utf-8")
    for stub in ("xcrun", "xcodebuild"):
        (stubs / stub).chmod(0o755)
    health = tmp_path / "health-root"
    health.mkdir()
    (health / "health").write_text("ok\n", encoding="utf-8")
    python = tmp_path / "repo" / ".venv" / "bin" / "python"
    python.write_text(f'#!/bin/sh\n[ "$1 $2" = "-m uvicorn" ] && exec "{sys.executable}" -m http.server --bind 127.0.0.1 '
                      f'--directory "{health}" "$UI_TEST_PORT"\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    return {**env, "UI_STUB_LOG": str(log), "UI_STUB_STATE": str(state), **extra}, log


def _run(tmp_path: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(tmp_path / "repo" / "scripts" / "ui_test.sh")], env=env,
                          capture_output=True, text=True, timeout=120, check=False)


@pytest.mark.needs("bash_curl")
@pytest.mark.parametrize("only", ["", "FailureScreenTests"], ids=["both-passes", "the-offline-pass-alone"])
def test_the_offline_pass_starts_from_a_removed_app_when_the_simulator_was_shut_down(tmp_path: Path, only: str) -> None:
    """#525 (the release Tester's M10): xcodebuild shuts the simulator down after a pass it booted it for, the
    uninstall then failed, `|| true` hid it, and the offline pass met the app's kept answer (#503 again)."""
    env, log = _harness(tmp_path, **({"UI_TEST_ONLY": only} if only else {}))
    done = _run(tmp_path, env)
    calls = log.read_text(encoding="utf-8").splitlines()
    assert done.returncode == 0, done.stdout + done.stderr + "\n".join(calls)
    removed = [i for i, call in enumerate(calls) if call == "removed com.ilgar.modelranking"]
    offline = [i for i, call in enumerate(calls) if "-only-testing:ModelRankingUITests/FailureScreenTests" in call]
    assert removed and offline and removed[-1] < offline[0], calls


@pytest.mark.needs("bash_curl")
def test_an_uninstall_that_fails_fails_the_run_before_the_offline_pass(tmp_path: Path) -> None:
    """#525: an app that is not installed uninstalls with exit 0, so any failure means the app may keep its answer:
    the run fails, says why, and the offline pass is not run against it."""
    env, log = _harness(tmp_path, UNINSTALL_ERROR="An error was encountered processing the command (code=1)")
    done = _run(tmp_path, env)
    calls = log.read_text(encoding="utf-8").splitlines()
    assert done.returncode != 0, done.stdout + done.stderr
    assert "could not remove the app" in done.stdout + done.stderr, done.stdout + done.stderr
    assert not [call for call in calls if "-only-testing:ModelRankingUITests/FailureScreenTests" in call], calls
