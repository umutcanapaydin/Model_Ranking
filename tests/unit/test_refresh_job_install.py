"""The 12-hour refresh can be installed from this repository, and the pieces agree.

M14 closure seat, MAJOR-1. W-096 moved the job's program out of `~/Desktop` (macOS privacy
protection stops launchd opening a program that lives there) to a wrapper under Application
Support. The plist was rewritten; the installer was not. Anyone running the documented install
path got a launchd job whose program did not exist -- the silent 24-day outage W-096 was raised
for, reinstated by the fix for it, and no gate could see it because `conformance/` only checks
`make` targets.

These tests are structural on purpose: nothing here can install a launchd job (there is no macOS
in either agent lane, and `deploy/` is the owner's surface). What they CAN do is refuse a tree
where the three pieces disagree, which is the only failure this defect had.
"""

from __future__ import annotations

import plistlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLIST = REPO / "deploy" / "com.hcs.modelranking.refresh.plist"
WRAPPER = REPO / "scripts" / "refresh_job.sh"
INSTALLERS = (REPO / "scripts" / "enable_refresh.sh", REPO / "scripts" / "install_refresh_wrapper.sh")


def _program() -> str:
    with PLIST.open("rb") as handle:
        arguments = plistlib.load(handle)["ProgramArguments"]
    assert arguments[0] == "/bin/bash", "the job's program is no longer the wrapper shape W-096 found"
    return arguments[1]


def test_the_job_runs_a_wrapper_this_repository_ships() -> None:
    assert WRAPPER.is_file(), "the job's program is not in the repository at all"
    assert Path(_program()).name == WRAPPER.name, (
        "the plist runs a program with a different name from the wrapper this repository ships"
    )


def test_every_installer_writes_the_wrapper_where_the_plist_looks_for_it() -> None:
    """A path in the plist and a path in a script are two accounts of one fact. Pin them together."""
    program = _program()
    assert "Desktop" not in program, "the job's program is back under ~/Desktop (W-096)"
    tail = program.split("/Library/", 1)[1]
    for installer in INSTALLERS:
        text = installer.read_text(encoding="utf-8")
        assert re.search(r'DST="\$HOME/Library/' + re.escape(tail) + r'"', text) or re.search(
            r'WRAPPER_DST="\$HOME/Library/' + re.escape(tail) + r'"', text
        ), f"{installer.name} does not write the wrapper to the path the plist runs ({program})"
        assert "refresh_job.sh" in text, f"{installer.name} never copies the wrapper"


def test_the_logs_are_not_under_desktop_either() -> None:
    """The other half of W-096: launchd could not open the job's log files under ~/Desktop."""
    with PLIST.open("rb") as handle:
        job = plistlib.load(handle)
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert "Desktop" not in job[key], f"{key} is back under ~/Desktop (W-096)"


def test_the_launchd_wrapper_fetches_epoch_instead_of_passing_a_hand_kept_bundle() -> None:
    """M16-W4 review MAJOR-1, D-158: the wrapper passed the owner's 2026-08-15 bundle, which wins
    over the fetch, so the refresher actually running never fetched -- and after the deliberate
    publish it would be refused every cycle (the stale bundle lacks the rows the fresh one added)."""
    text = WRAPPER.read_text(encoding="utf-8")
    assert "--fetch-epoch" in text
    assert "--epoch-dir" not in text
    assert "epoch_data" not in text, "the hand-kept bundle directory is retired; nothing names it"
