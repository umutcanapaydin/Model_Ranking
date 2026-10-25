"""#32, retired by D-222 (#427): the engine ran on the owner's Mac as a launchd service. It runs only on Fly.io now.

The launcher, the installer and their tests are gone with INV-27 to INV-29 (D-224; `docs/watchlist.md`
names what brings them back). What stays here:
- the remover, until the owner has run it once (D-222 clause 2, D-224 clause 3);
- `ios/app.sh`, a simulator-only helper now: it starts no engine, and its build is pinned to loopback
  (INV-73), where `make run` serves;
- `make run`'s loopback bind, and the checks that read every script.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REMOVER = REPO / "scripts" / "remove_engine_service.sh"
APP_SH = REPO / "ios" / "app.sh"
LABEL = "com.ilgar.modelranking.engine"


def test_the_remover_takes_off_the_service_the_retired_installer_put_on() -> None:
    """D-222 clause 2: the owner takes the Mac's service off with the remover once a hosted night has
    published. It unloads the job and removes the plist and the wrapper the installer wrote."""
    remover = REMOVER.read_text(encoding="utf-8")
    for piece in (LABEL, 'PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"',
                  'WRAPPER="$HOME/Library/Application Support/model-ranking/engine_service.sh"'):
        assert piece in remover, piece
    assert 'launchctl bootout "gui/$(id -u)/$LABEL"' in remover
    assert 'rm -f "$PLIST"' in remover and 'rm -f "$WRAPPER"' in remover


def test_the_app_script_starts_no_engine() -> None:
    """D-222: nothing runs on the Mac. The simulator helper builds, installs and launches the app; a local
    engine is `make run`, started by the developer, and the script only says whether one answers."""
    script = APP_SH.read_text(encoding="utf-8")  # raw: not Swift
    code = "\n".join(line.split("#", 1)[0] for line in script.splitlines())
    for started in ("uvicorn", "launchctl bootstrap", "launchctl kickstart", "engine_service", "pkill"):
        assert started not in code, started
    assert "make run" in code, "the script does not say how to start a local engine"


def test_the_app_script_addresses_the_simulator_it_boots_by_name() -> None:
    """M17 closure, found by the owner's first look at the W5 app: with a second simulator booted,
    `simctl install booted` put the fresh build on the other device, and the owner's screen ran a
    day-old test build that asked port 8081 ("the engine is not answering"). Every simctl call that
    acts on the app names `$DEVICE`, the device `app.sh` boots."""
    script = APP_SH.read_text(encoding="utf-8")  # raw: not Swift
    code = "\n".join(line.split("#", 1)[0] for line in script.splitlines())
    acting = re.findall(r"xcrun simctl (?:install|launch|terminate|spawn)\s+(\S+)", code)
    assert len(acting) >= 4, f"the script's app commands were not found: {acting}"
    assert all(target == '"$DEVICE"' for target in acting), (
        f"an app command targets something other than the booted-by-name device: {acting}"
    )


def test_every_simctl_call_in_the_app_script_names_its_device() -> None:
    """M17 closure Tester N1 (#92): the test above lists four simctl verbs, and an added
    `simctl uninstall booted` passed. Every simctl call addresses the simulator the script boots."""
    script = (REPO / "ios" / "app.sh").read_text(encoding="utf-8")  # raw: not Swift
    # W5 review M5: a call continued over lines with `\` is one call.
    joined = re.sub(r"\\\n\s*", " ", script)
    calls = [line.strip() for line in joined.splitlines() if "simctl " in line and not line.strip().startswith("#")]
    assert calls, "found no simctl call; this reads the wrong file"
    booted = [line for line in calls if re.search(r"\bbooted\b", line)]
    assert booted == [], booted


def test_the_app_script_builds_for_the_simulators_loopback_whatever_the_owners_override() -> None:
    """W1 review M2: the owner's Engine.local.xcconfig reached app.sh's simulator builds. A setting on
    the command line beats the xcconfig, so the simulator build talks to loopback, under the bundle id
    the script launches."""
    script = APP_SH.read_text(encoding="utf-8")  # raw: not Swift
    build = script[script.index("xcodebuild -project"):]
    build = build[: build.index("then")]
    assert "ENGINE_URL=http://127.0.0.1:8080" in build, build
    assert 'PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE"' in build, build


def test_make_run_binds_loopback() -> None:
    """W1 review B1: `make run` bound 0.0.0.0, with no Host list, on a Mac whose firewall is off."""
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    recipe = makefile[makefile.index("\nrun:"):]
    recipe = recipe[: recipe.index("\n\n")]
    assert "--host 127.0.0.1" in recipe and "0.0.0.0" not in recipe, recipe


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
