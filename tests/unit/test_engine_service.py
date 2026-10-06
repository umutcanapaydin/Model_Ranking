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
import re
import subprocess
from pathlib import Path

import pytest

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
                          env={**_CLEAN_GIT_ENV, "MODEL_RANKING_REPO": str(repo), "HOME": str(target.parent / "home")})


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
    assert "starting on" not in done.stdout


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
                   "uvicorn app.adapter.main:app", '--host "${MODEL_RANKING_BIND:-127.0.0.1}"'):  # D-171
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


# A stand-in launchd, curl, lsof and plutil: they record what the installer asks and answer as told.
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
    # macOS-only; CI runs on Linux, where the installer's lint step would otherwise fail first.
    # The real `plutil` lints the generated plist in the owner's install run.
    "plutil": "#!/bin/bash\nexit 0\n",
}


def _install(tmp_path: Path, repo: Path, health: str | None, *flags: str, **extra: str) -> subprocess.CompletedProcess[str]:
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
    env.update(extra)
    return subprocess.run(["/bin/bash", str(INSTALLER), *flags], capture_output=True, text=True,
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


def test_a_release_rolled_back_to_survives_later_prunes(tmp_path: Path) -> None:
    """N5: after failed upgrades roll back, `current` points at a release that grows OLDER with
    every attempt. Pruning by age alone would delete the very release the engine runs from."""
    import time

    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    assert _deploy(repo, target).returncode == 0
    live = (target / "current").readlink()
    for n in range(4):
        time.sleep(1.1)  # distinct modification times, so "oldest" is unambiguous
        _push_new_main(repo, f"an upgrade that fails {n}\n")
        assert _deploy(repo, target).returncode == 0
        (target / "current").unlink()
        (target / "current").symlink_to(live)  # the installer's rollback leaves it so
    assert (target / live).is_dir(), "the release the engine runs from was pruned"


def test_the_app_script_addresses_the_simulator_it_boots_by_name() -> None:
    """M17 closure, found by the owner's first look at the W5 app: with a second simulator booted,
    `simctl install booted` put the fresh build on the other device, and the owner's screen ran a
    day-old test build that asked port 8081 ("the engine is not answering"). Every simctl call that
    acts on the app names `$DEVICE`, the device `app.sh` boots."""
    script = (Path(__file__).resolve().parents[2] / "ios" / "app.sh").read_text(encoding="utf-8")
    code = "\n".join(line.split("#", 1)[0] for line in script.splitlines())
    acting = re.findall(r"xcrun simctl (?:install|launch|terminate|spawn)\s+(\S+)", code)
    assert len(acting) >= 4, f"the script's app commands were not found: {acting}"
    assert all(target == '"$DEVICE"' for target in acting), (
        f"an app command targets something other than the booted-by-name device: {acting}"
    )


# --- M18-W1 (#87, D-171, REQ-DEV-001; #86): loopback by default, the home network by opt-in, tested by running --


def test_the_wrapper_binds_loopback_and_names_its_hosts_by_default() -> None:
    wrapper = _installer("--print-wrapper").stdout
    assert 'export MODEL_RANKING_BIND="127.0.0.1"' in wrapper
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost"' in wrapper


def test_the_home_network_is_opt_in_and_names_the_macs_own_names() -> None:
    done = subprocess.run(["/bin/bash", str(INSTALLER), "--lan", "--print-wrapper"], capture_output=True,
                          text=True, timeout=60, env={**_CLEAN_GIT_ENV, "HOME": HOME,
                                                      "ENGINE_LAN_NAME": "Probe-Mac", "ENGINE_LAN_IP": "192.168.9.9"})
    assert done.returncode == 0, done.stdout + done.stderr
    assert 'export MODEL_RANKING_BIND="0.0.0.0"' in done.stdout
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost,probe-mac.local,192.168.9.9"' in done.stdout


def test_the_launcher_binds_exactly_one_host_and_reads_it_from_the_bind_variable() -> None:
    """#86: appending `--host 0.0.0.0` passed the whole suite; uvicorn takes the last one."""
    code = "\n".join(line.split("#", 1)[0] for line in LAUNCHER.read_text(encoding="utf-8").splitlines())
    starts = [line for line in code.splitlines() if "uvicorn" in line]
    assert len(starts) == 1, starts
    assert starts[0].count("--host") == 1, starts[0]
    assert '--host "${MODEL_RANKING_BIND:-127.0.0.1}"' in starts[0]


def test_the_launchers_preflight_refuses_a_bind_beyond_loopback_without_hosts(tmp_path: Path) -> None:
    """#86: disabling the preflight passed the whole suite. This checkout's launcher, run for real."""
    import sys

    from .test_api_v1 import _seeded_db

    db = tmp_path / "advisor.db"
    _seeded_db(db)
    # The launcher runs `$REPO/.venv/bin/python`. CI installs into its own interpreter and has no
    # `.venv` (PR #99's first CI run), so the tree's `.venv` hands over to the one running this test.
    tree = tmp_path / "tree"
    (tree / ".venv" / "bin").mkdir(parents=True)
    (tree / ".venv" / "bin" / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    (tree / ".venv" / "bin" / "python").chmod(0o755)
    # TEST-NET-1: an address this Mac cannot bind, so a regressed preflight fails to start rather
    # than serving the developer's Mac on every interface for the test's timeout (W1 review M5).
    done = _launch(tree, MODEL_RANKING_DB=str(db), MODEL_RANKING_BIND="192.0.2.1")
    assert done.returncode == 1, done.stdout + done.stderr
    assert "REFUSED" in done.stdout and "MODEL_RANKING_ALLOWED_HOSTS" in done.stdout
    assert "starting on" not in done.stdout


@pytest.mark.parametrize("bound", ["MODEL_RANKING_MAX_RANKED_ROWS", "MODEL_RANKING_MAX_PUBLISHED_STANDINGS_ROWS"])
def test_the_launcher_refuses_an_artifact_past_a_serving_bound(tmp_path: Path, bound: str) -> None:
    """#123: the preflight's other refusal, run as a script. M17's seat lowered the standings bound by
    hand and saw `REFUSED`; no test did. Bound to one row, the seeded artifact is past it."""
    import sys

    from .test_api_v1 import _seeded_db

    db = tmp_path / "advisor.db"
    _seeded_db(db)
    tree = tmp_path / "tree"
    (tree / ".venv" / "bin").mkdir(parents=True)
    (tree / ".venv" / "bin" / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    (tree / ".venv" / "bin" / "python").chmod(0o755)
    # TEST-NET-1 with a Host list: the bind itself is allowed, so the bound is the only problem, and
    # a regressed preflight fails to bind rather than serving this Mac for the test's timeout.
    done = _launch(tree, MODEL_RANKING_DB=str(db), MODEL_RANKING_BIND="192.0.2.1",
                   MODEL_RANKING_ALLOWED_HOSTS="probe.example", **{bound: "1"})
    assert done.returncode == 1, done.stdout + done.stderr
    assert "REFUSED" in done.stdout and bound in done.stdout, done.stdout
    assert "MODEL_RANKING_ALLOWED_HOSTS" not in done.stdout, "the bind, not the bound, was refused"
    assert "starting on" not in done.stdout


def test_the_installed_wrapper_is_the_owners_alone(tmp_path: Path) -> None:
    """#86: a `chmod 777` on the wrapper passed the whole suite."""
    import stat

    repo = _scratch_repo(tmp_path)
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}')
    assert done.returncode == 0, done.stdout + done.stderr
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    assert stat.S_IMODE(wrapper.stat().st_mode) == 0o700


def test_a_reinstall_keeps_the_home_network_unless_told_to_close_it(tmp_path: Path) -> None:
    """W1 review M2: D-170 reruns the installer after every merge, and without --lan it silently put
    the phone's engine back on loopback."""
    home = tmp_path / "home"
    installed = home / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    installed.parent.mkdir(parents=True)
    installed.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    env = {**_CLEAN_GIT_ENV, "HOME": str(home), "ENGINE_LAN_NAME": "probe-mac", "ENGINE_LAN_IP": "192.168.9.9"}
    kept = subprocess.run(["/bin/bash", str(INSTALLER), "--print-wrapper"], capture_output=True, text=True,
                          timeout=60, env=env)
    assert 'export MODEL_RANKING_BIND="0.0.0.0"' in kept.stdout, kept.stdout + kept.stderr
    closed = subprocess.run(["/bin/bash", str(INSTALLER), "--no-lan", "--print-wrapper"], capture_output=True,
                            text=True, timeout=60, env=env)
    assert 'export MODEL_RANKING_BIND="127.0.0.1"' in closed.stdout, closed.stdout + closed.stderr
    # W1 second review M7: and the other direction -- a reinstall over a loopback wrapper stays on
    # loopback; an existing wrapper is not a reason to open the network.
    installed.write_text('export MODEL_RANKING_BIND="127.0.0.1"\n', encoding="utf-8")
    stayed = subprocess.run(["/bin/bash", str(INSTALLER), "--print-wrapper"], capture_output=True, text=True,
                            timeout=60, env=env)
    assert 'export MODEL_RANKING_BIND="127.0.0.1"' in stayed.stdout, stayed.stdout + stayed.stderr


def test_only_writing_the_wrapper_reads_the_mode_it_finds(tmp_path: Path) -> None:
    """W1 third review M12: the keep-the-mode check ran before the mode dispatch, so `--print-plist`
    and `--deploy-only` read the owner's live wrapper and asked this Mac for its name and address."""
    home = tmp_path / "home"
    installed = home / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    installed.parent.mkdir(parents=True)
    installed.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    env = {**_CLEAN_GIT_ENV, "HOME": str(home), "ENGINE_LAN_NAME": "probe-mac", "ENGINE_LAN_IP": "192.168.9.9"}
    printed = subprocess.run(["/bin/bash", str(INSTALLER), "--print-plist"], capture_output=True, text=True,
                             timeout=60, env=env)
    assert printed.returncode == 0, printed.stdout + printed.stderr
    assert "home network" not in printed.stderr, printed.stderr


def test_make_run_binds_loopback() -> None:
    """W1 review B1: `make run` bound 0.0.0.0, with no Host list, on a Mac whose firewall is off."""
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    recipe = makefile[makefile.index("\nrun:"):]
    recipe = recipe[: recipe.index("\n\n")]
    assert "--host 127.0.0.1" in recipe and "0.0.0.0" not in recipe, recipe


def test_the_app_script_builds_for_the_simulators_loopback_whatever_the_owners_override() -> None:
    """W1 review M2: the owner's Engine.local.xcconfig reached app.sh's simulator builds. A setting on
    the command line beats the xcconfig, so the simulator build talks to loopback, under the bundle id
    the script launches."""
    script = APP_SH.read_text(encoding="utf-8")
    build = script[script.index("xcodebuild -project"):]
    build = build[: build.index("then")]
    assert "ENGINE_URL=http://127.0.0.1:8080" in build, build
    assert 'PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE"' in build, build


def test_a_plain_reinstall_writes_the_mode_it_found_and_says_so(tmp_path: Path) -> None:
    """W1 Tester T1, T6 (REQ-DEV-001, D-171 note 2): the redeploy after a merge is a plain install, not
    `--print-wrapper`. It writes the home-network wrapper it found, and says so on both lines the owner
    reads. launchctl, curl and plutil are the module's stubs; HOME is scratch."""
    repo = _scratch_repo(tmp_path)
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}',
                    ENGINE_LAN_NAME="probe-mac", ENGINE_LAN_IP="192.168.9.9")
    assert done.returncode == 0, done.stdout + done.stderr
    written = wrapper.read_text(encoding="utf-8")
    assert 'export MODEL_RANKING_BIND="0.0.0.0"' in written, written
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost,probe-mac.local,192.168.9.9"' in written
    assert "home network: kept" in done.stderr, done.stderr
    assert "home network: on" in done.stdout, done.stdout


def test_a_deploy_reads_no_live_wrapper(tmp_path: Path) -> None:
    """W1 Tester T7: the other half of the third review's M12 -- `--deploy-only` reads no wrapper."""
    repo, target = _scratch_repo(tmp_path), tmp_path / "engine"
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    done = _deploy(repo, target)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "home network" not in done.stdout + done.stderr, done.stdout + done.stderr


def test_no_lan_closes_the_home_network_on_the_install_the_owner_runs(tmp_path: Path) -> None:
    """W1 second Tester T9 (D-171 note 7): while the network is open, `--no-lan` is the one control, and
    the owner runs it as an install, not `--print-wrapper`. It writes loopback and says so. launchctl,
    curl and plutil are the module's stubs; HOME is scratch."""
    repo = _scratch_repo(tmp_path)
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}', "--no-lan",
                    ENGINE_LAN_NAME="probe-mac", ENGINE_LAN_IP="192.168.9.9")
    assert done.returncode == 0, done.stdout + done.stderr
    written = wrapper.read_text(encoding="utf-8")
    assert 'export MODEL_RANKING_BIND="127.0.0.1"' in written, written
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost"' in written, written
    assert "home network: kept" not in done.stderr, done.stderr
    assert "home network: off" in done.stdout, done.stdout


def test_nothing_in_the_repository_installs_the_retired_refresher() -> None:
    """#76 (D-173 clause 7): the engine service runs the nightly refresh (D-170, D-154). The retired
    launchd refresher's installer still shipped, and it ran the development checkout: a second
    nightly refresher the shared lock alone kept apart from the first."""
    offenders = [
        str(path) for folder in (REPO / "scripts", REPO / "deploy") if folder.is_dir()
        for path in sorted(folder.rglob("*"))  # W4 Tester T9: every folder below, not the top only
        if path.is_file() and path.suffix != ".md"  # what runs or installs, not what describes it
        and "__pycache__" not in path.parts
        and "com.hcs.modelranking.refresh" in path.read_text(encoding="utf-8", errors="replace")
    ]
    assert offenders == []


def test_every_simctl_call_in_the_app_script_names_its_device() -> None:
    """M17 closure Tester N1 (#92): the test above lists four simctl verbs, and an added
    `simctl uninstall booted` passed. Every simctl call addresses the simulator the script boots."""
    script = (REPO / "ios" / "app.sh").read_text(encoding="utf-8")
    # W5 review M5: a call continued over lines with `\` is one call.
    joined = re.sub(r"\\\n\s*", " ", script)
    calls = [line.strip() for line in joined.splitlines() if "simctl " in line and not line.strip().startswith("#")]
    assert calls, "found no simctl call; this reads the wrong file"
    booted = [line for line in calls if re.search(r"\bbooted\b", line)]
    assert booted == [], booted


def test_every_command_a_script_tells_the_operator_to_run_exists() -> None:
    """#104: the launcher told the operator to run `build --fetch-epoch`, a flag `build.py` does not
    have, so the command it printed exited 2 with a usage line. Every `-m app...` command a script
    prints must take every flag it is printed with: its `--help` is read for each one."""
    import re
    import subprocess
    import sys

    hints = []
    for script in sorted((REPO / "scripts").glob("*.sh")):
        for line in script.read_text(encoding="utf-8").splitlines():
            found = re.search(r"-m (app\.[\w.]+)(.*)", line)  # the rest of the printed line
            if line.lstrip().startswith("echo") and found:
                hints.append((script.name, found.group(1), re.findall(r"--[\w-]+", found.group(2))))
    assert hints, "no script prints a command any more; the test reads nothing"
    for name, module, flags in hints:
        helped = subprocess.run([sys.executable, "-m", module, "--help"], capture_output=True, text=True,
                                timeout=60, env={**os.environ, "PYTHONPATH": str(REPO / "src")}, check=False)
        assert helped.returncode == 0, f"{name} prints `-m {module}`, which does not run: {helped.stderr[-300:]}"
        # The options argparse declares, one per line; not a flag the help merely mentions in prose.
        declared = set(re.findall(r"^\s{2}(?:-\w, )?(--[\w-]+)", helped.stdout, re.M))
        missing = [flag for flag in flags if flag not in declared]
        assert not missing, f"{name} prints `-m {module}` with {missing}, which it does not take"


@pytest.mark.parametrize("folder", ["data", "Application Support"])  # the service's own (the Tester's T2)
def test_the_launchers_hint_builds_the_artifact_it_looked_for(tmp_path: Path, folder: str) -> None:
    """Tester (M18-W7), the W7 review's M6: the hint printed `--db advisor.db`, a file in the release
    folder, while the service reads `$DEPLOY/data/advisor.db`; run as printed, it built a file the
    next start would not read. The printed command must name the path that was missing."""
    import shlex

    tree = tmp_path / "release"
    tree.mkdir()
    missing = tmp_path / folder / "advisor.db"
    done = _launch(tree, MODEL_RANKING_DB=str(missing))
    assert done.returncode == 1, done.stdout + done.stderr
    hints = [line.split("build it:", 1)[1] for line in done.stdout.splitlines() if "build it:" in line]
    assert len(hints) == 1, done.stdout
    argv = shlex.split(hints[0])
    assert argv[argv.index("--db") + 1] == str(missing), hints[0]


def test_a_preflight_that_dies_without_a_word_stops_the_start(tmp_path: Path) -> None:
    """#145 (the M18 closure's S11): the launcher read the preflight's output, not its exit status,
    so a preflight killed with nothing printed (out of memory, say) let the engine start unchecked.
    The tree's python dies with status 137 and no output on the preflight; were the engine started,
    it would only say so and exit, so no server runs whatever the launcher does."""
    tree = tmp_path / "tree"
    (tree / ".venv" / "bin").mkdir(parents=True)
    python = tree / ".venv" / "bin" / "python"
    python.write_text('#!/bin/sh\ncase "$1" in\n  -B) exit 137 ;;\n  *) echo "the engine would start here"; exit 0 ;;\n'
                      "esac\n", encoding="utf-8")
    python.chmod(0o755)
    db = tmp_path / "advisor.db"
    db.write_bytes(b"")
    done = _launch(tree, MODEL_RANKING_DB=str(db))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "REFUSED" in done.stdout and "137" in done.stdout, done.stdout
    assert "starting on" not in done.stdout and "the engine would start here" not in done.stdout
