"""#32 -- the engine keeps running: a launchd service that runs its own DEPLOYED copy of `main`.

Since D-154 the engine refreshes itself nightly, and since #16 nothing else does. The engine was
started only by hand (`./ios/app.sh up`), so after a restart nothing refreshed, and nothing said
so (2026-09-24 to 2026-09-25). The owner ruled (2026-09-25) that a service keeps the engine up,
and, after the independent review (`docs/reviews/issue-32-review.md`, BLOCKING), that it runs a
deployed copy of `main` outside `~/Desktop`:

- B1: under launchd, bash cannot read a script under `~/Desktop` and git cannot `getcwd()` there
  (W-096), so nothing launchd touches may live there;
- B2: the nightly refresh child runs the code on disk where the engine was imported from. Run from
  the development checkout, it ran whatever branch was checked out that night. Run from a release
  directory, it runs the release.

Nothing here installs a launchd job: that is the owner's action on his machine. The deploy step is
exercised against a scratch git repository into a temporary directory, without a venv.
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
HOME = "/Users/probe"
DEPLOY = f"{HOME}/Library/Application Support/model-ranking/engine"

#: Review M1: git inherits GIT_DIR and friends from a hook; a scratch repository must not.
_CLEAN_GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _installer(*flags: str, home: str = HOME) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(INSTALLER), *flags], capture_output=True, text=True,
                          timeout=120, env={**_CLEAN_GIT_ENV, "HOME": home})


def _plist() -> dict[str, object]:
    return plistlib.loads(_installer("--print-plist").stdout.encode())


def test_the_service_keeps_the_engine_up_and_starts_at_login() -> None:
    job = _plist()
    assert job["Label"] == LABEL
    assert job["RunAtLoad"] is True
    assert job["KeepAlive"] is True
    assert isinstance(job["ThrottleInterval"], int) and job["ThrottleInterval"] >= 30


def test_launchd_touches_nothing_under_desktop() -> None:
    """B1 / W-096: the program, the wrapper it runs, the release it hands over to and every log
    live under ~/Library."""
    job = _plist()
    arguments = job["ProgramArguments"]
    assert arguments == ["/bin/bash", f"{HOME}/Library/Application Support/model-ranking/engine_service.sh"]
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert str(job[key]).startswith(f"{HOME}/Library/Logs/"), key
    wrapper = _installer("--print-wrapper").stdout
    assert "Desktop" not in wrapper and "Desktop" not in str(job)


def test_the_wrapper_runs_the_deployed_release_with_its_own_artifact() -> None:
    """B2: the engine and its nightly child run the deployed release, never the development
    checkout, and serve the artifact kept beside the releases."""
    wrapper = _installer("--print-wrapper").stdout
    code = [line.strip() for line in wrapper.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    handover = [line for line in code if line.startswith("exec ")]
    assert handover == [f'exec /bin/bash "{DEPLOY}/current/scripts/engine_service.sh" --service'], wrapper
    assert f'MODEL_RANKING_DB="{DEPLOY}/data/advisor.db"' in wrapper
    assert f'ENGINE_LOG_FILE="{HOME}/Library/Logs/model-ranking-engine.log"' in wrapper


def _git(*args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                   check=True, capture_output=True, env=_CLEAN_GIT_ENV)


def _scratch_repo(tmp_path: Path) -> Path:
    """A repository with a `main` published to an `origin`, plus an unmerged branch checked out."""
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    _git("init", "-q", "--bare", "-b", "main", str(origin))
    _git("clone", "-q", str(origin), str(repo))
    (repo / "scripts").mkdir()
    (repo / "scripts" / "engine_service.sh").write_text("echo main's launcher\n", encoding="utf-8")
    (repo / "README").write_text("main\n", encoding="utf-8")
    _git("-C", str(repo), "add", ".")
    _git("-C", str(repo), "commit", "-qm", "main")
    _git("-C", str(repo), "push", "-q", "origin", "main")
    _git("-C", str(repo), "checkout", "-qb", "wave/m99-w1")
    (repo / "README").write_text("an unreviewed branch\n", encoding="utf-8")
    _git("-C", str(repo), "commit", "-qam", "branch")
    (repo / "advisor.db").write_bytes(b"artifact")
    return repo


def _deploy(repo: Path, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(INSTALLER), "--deploy-only", str(target), "--no-venv"],
                          capture_output=True, text=True, timeout=120,
                          env={**_CLEAN_GIT_ENV, "MODEL_RANKING_REPO": str(repo)})


def test_a_deploy_takes_origin_main_whatever_is_checked_out(tmp_path: Path) -> None:
    """B2 at the source: the release is `origin/main`, exported without `.git`; the branch the
    developer has checked out never reaches it."""
    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    done = _deploy(repo, target)
    assert done.returncode == 0, done.stdout + done.stderr
    current = target / "current"
    assert current.is_symlink() and (current / "README").read_text(encoding="utf-8") == "main\n"
    assert not (current / ".git").exists()
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "origin/main"],
                         capture_output=True, text=True, check=True, env=_CLEAN_GIT_ENV).stdout.strip()
    assert (current / "RELEASE").read_text(encoding="utf-8").strip() == sha


def test_the_first_deploy_brings_the_artifact_and_later_ones_keep_the_served_one(tmp_path: Path) -> None:
    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    assert _deploy(repo, target).returncode == 0
    served = target / "data" / "advisor.db"
    assert served.read_bytes() == b"artifact"
    served.write_bytes(b"refreshed by the service")
    assert _deploy(repo, target).returncode == 0
    assert served.read_bytes() == b"refreshed by the service", "a redeploy overwrote the served artifact"


def _launch(tree: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(LAUNCHER), *args], capture_output=True, text=True,
                          timeout=30, env={**_CLEAN_GIT_ENV, "MODEL_RANKING_REPO": str(tree),
                                           "ENGINE_SERVICE_WAIT_S": "0", **env})


def test_the_service_runs_only_a_deployed_release(tmp_path: Path) -> None:
    """A tree with no RELEASE stamp is a development checkout: the service does not start it."""
    tree = tmp_path / "checkout"
    tree.mkdir()
    done = _launch(tree, "--service")
    assert done.returncode == 0 and "not a deployed release" in done.stdout
    assert "starting on :" not in done.stdout


def test_on_a_release_the_service_goes_on_to_the_artifact(tmp_path: Path) -> None:
    """The positive control: past the release check, the next thing checked is the artifact."""
    tree = tmp_path / "release"
    tree.mkdir()
    (tree / "RELEASE").write_text("abc1234\n", encoding="utf-8")
    done = _launch(tree, "--service", MODEL_RANKING_DB=str(tmp_path / "data" / "advisor.db"))
    assert done.returncode != 0
    assert "advisor.db" in done.stdout and "not a deployed release" not in done.stdout


def test_by_hand_the_launcher_runs_a_development_checkout(tmp_path: Path) -> None:
    """`ios/app.sh` uses the same launcher without `--service`: a developer runs branches."""
    tree = tmp_path / "checkout"
    tree.mkdir()
    done = _launch(tree)
    assert "not a deployed release" not in done.stdout and "advisor.db" in done.stdout


def test_the_service_log_is_rotated_before_it_grows_without_bound(tmp_path: Path) -> None:
    """Review M6: the log only grew. Past `ENGINE_LOG_MAX_BYTES` it is moved aside at start."""
    tree, log = tmp_path / "release", tmp_path / "engine.log"
    tree.mkdir()
    (tree / "RELEASE").write_text("abc1234\n", encoding="utf-8")
    log.write_bytes(b"x" * 2048)
    _launch(tree, "--service", ENGINE_LOG_FILE=str(log), ENGINE_LOG_MAX_BYTES="1024",
            MODEL_RANKING_DB=str(tmp_path / "missing.db"))
    assert (tmp_path / "engine.log.1").read_bytes() == b"x" * 2048
    assert "advisor.db" in log.read_text(encoding="utf-8") or "missing.db" in log.read_text(encoding="utf-8")


def test_the_launcher_starts_the_engine_the_way_the_app_script_did() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    for needle in ("APP_ENV=test", "MODEL_RANKING_REFRESH=nightly", "validate_startup_config",
                   "uvicorn app.adapter.main:app", "--host 127.0.0.1"):
        assert needle in text, needle


def test_the_app_script_starts_through_the_launcher_and_restarts_the_service_in_place() -> None:
    """Review M2: bootout followed at once by bootstrap races launchd; a restart is `kickstart -k`."""
    text = APP_SH.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "scripts/engine_service.sh" in code and "-m uvicorn" not in code
    assert LABEL in code
    assert "kickstart -k" in code, "a restart through the service must not unload it"


def test_the_remover_takes_off_what_the_installer_puts_on() -> None:
    installer, remover = INSTALLER.read_text(encoding="utf-8"), REMOVER.read_text(encoding="utf-8")
    for piece in (LABEL, "Library/LaunchAgents", "Application Support/model-ranking/engine_service.sh"):
        assert piece in installer and piece in remover, piece
    assert "launchctl bootout" in remover


# --- the re-review's findings (docs/reviews/issue-32-rereview.md) ---------------------------------


def _push_new_main(repo: Path, text: str) -> None:
    """A new commit on origin/main, as a merged pull request would make."""
    _git("-C", str(repo), "checkout", "-q", "main")
    (repo / "README").write_text(text, encoding="utf-8")
    _git("-C", str(repo), "commit", "-qam", text)
    _git("-C", str(repo), "push", "-q", "origin", "main")


def test_a_redeploy_of_the_same_commit_leaves_the_live_release_alone(tmp_path: Path) -> None:
    """M4: the live release is never deleted and rebuilt under a running engine."""
    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    assert _deploy(repo, target).returncode == 0
    marker = target / "current" / "in-use"
    marker.write_text("an engine runs from here", encoding="utf-8")
    assert _deploy(repo, target).returncode == 0
    assert marker.read_text(encoding="utf-8") == "an engine runs from here"


def test_pruning_keeps_the_new_release_and_the_one_it_replaced(tmp_path: Path) -> None:
    """N5 / M4: after many deploys, at most KEEP releases remain, and the previous live one is kept
    so a failed upgrade can fall back to it."""
    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    assert _deploy(repo, target).returncode == 0
    for n in range(5):
        before = (target / "current").readlink()
        _push_new_main(repo, f"main {n}\n")
        assert _deploy(repo, target).returncode == 0
        kept = {p.name for p in (target / "releases").iterdir()}
        assert before.name in kept and (target / "current").readlink().name in kept
        assert len(kept) <= 3


# A stand-in launchd, curl and lsof: they record what the installer asks and answer as told.
_STUBS = {
    "launchctl": """#!/bin/bash
echo "$*" >> "$STUB_LOG"
case "$1" in
  print) [ -f "$STUB_STATE/loaded" ] ;;
  bootstrap) touch "$STUB_STATE/loaded" ;;
  bootout) rm -f "$STUB_STATE/loaded" ;;
  kickstart) true ;;
esac
""",
    "curl": """#!/bin/bash
[ -n "${STUB_HEALTH:-}" ] || exit 7
echo "$STUB_HEALTH"
""",
    "lsof": "#!/bin/bash\nexit 1\n",
}


def _install(tmp_path: Path, repo: Path, health: str | None) -> subprocess.CompletedProcess[str]:
    stubs, state, home = tmp_path / "stubs", tmp_path / "state", tmp_path / "home"
    for folder in (stubs, state, home):
        folder.mkdir(exist_ok=True)
    for name, body in _STUBS.items():
        (stubs / name).write_text(body, encoding="utf-8")
        (stubs / name).chmod(0o755)
    (repo / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (repo / ".venv" / "bin" / "python").write_text("#!/bin/bash\n", encoding="utf-8")
    (repo / ".venv" / "bin" / "python").chmod(0o755)
    env = {**_CLEAN_GIT_ENV, "HOME": str(home), "MODEL_RANKING_REPO": str(repo),
           "PATH": f"{stubs}:{os.environ['PATH']}", "STUB_LOG": str(tmp_path / "calls.log"),
           "STUB_STATE": str(state), "ENGINE_DEPLOY_NO_VENV": "1", "ENGINE_INSTALL_WAIT_S": "1"}
    if health is not None:
        env["STUB_HEALTH"] = health
    return subprocess.run(["/bin/bash", str(INSTALLER)], capture_output=True, text=True,
                          timeout=120, env=env)


def _sha(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "origin/main"],
                          capture_output=True, text=True, check=True, env=_CLEAN_GIT_ENV).stdout.strip()


def test_an_install_succeeds_only_when_the_new_release_answers(tmp_path: Path) -> None:
    """M3: any 200 was taken as success; the engine must report the release just deployed."""
    repo = _scratch_repo(tmp_path)
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}')
    assert done.returncode == 0, done.stdout + done.stderr
    assert (tmp_path / "state" / "loaded").exists()


def test_a_first_install_that_never_answers_leaves_nothing_behind(tmp_path: Path) -> None:
    """M1: a failed first install left the plist and wrapper, so the broken service started again at
    every login and `app.sh up` went through it."""
    repo = _scratch_repo(tmp_path)
    done = _install(tmp_path, repo, None)
    assert done.returncode != 0
    home = tmp_path / "home"
    assert not (home / "Library" / "LaunchAgents" / f"{LABEL}.plist").exists()
    assert not (home / "Library" / "Application Support" / "model-ranking" / "engine_service.sh").exists()
    assert not (tmp_path / "state" / "loaded").exists()


def test_an_upgrade_that_serves_the_old_build_falls_back_to_the_previous_release(tmp_path: Path) -> None:
    """M1 / M3: the new release does not come up (the engine still reports the old build), so the
    installer points `current` back at the release that worked and restarts it."""
    repo = _scratch_repo(tmp_path)
    first = _sha(repo)
    assert _install(tmp_path, repo, f'{{"status":"ok","build":"release-{first}"}}').returncode == 0
    _push_new_main(repo, "a release that will not start\n")
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{first}"}}')
    assert done.returncode != 0 and "back" in done.stdout
    deploy = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine"
    assert (deploy / "current").readlink().name == first
