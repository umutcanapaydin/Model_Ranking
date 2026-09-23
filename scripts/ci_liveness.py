#!/usr/bin/env python3
"""`make ci-liveness`: did this repository's CI start any step lately? ADVISORY, never a gate leg.

WHY. A workflow whose jobs never start is not red in any way a push notices. The measured case: a
repository whose last ten runs all concluded `failure` without starting a single step -- every job
with an empty step list, the latest annotated "The job was not started because recent account
payments have failed or your spending limit needs to be increased". A run that never began reports
the same `failure` as a red build, and all that time the only thing gating a push was the local
`make gate` at pre-push.

WHAT IT READS. `gh run list --limit 10`, then `gh run view <id> --json jobs` for each completed
run, judged newest first. A run none of whose jobs started a step (a step in progress or completed,
and not `skipped`) never started. A run skipped or cancelled before any step ran says nothing
either way and is passed over: the shipped workflows produce both, with an `if:`-gated job and
`cancel-in-progress`. The count stops at the first run that executed a step.

WHAT IT IS NOT. It is not reachable from `make gate` and exits 0 whatever it finds: it reads runs
that already happened, on a server this tree does not control, so it can say CI has stopped
starting; it cannot stop a push. `/start-session` and bootstrap-check C12 report its line.

    python3 scripts/ci_liveness.py

Prints one line. Exit: always 0.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

LIMIT = 10
TIMEOUT = 30
#: A run concluded this way before any step ran is no evidence either way.
NO_EVIDENCE = {"skipped", "cancelled"}


class CannotCheck(Exception):
    """gh could not answer; the message is the reason printed after `CANNOT CHECK --`."""


def gh(args: list[str]) -> object:
    """The JSON gh prints for `args`, or CannotCheck with the reason."""
    try:
        # `gh` found on PATH; the arguments are this script's own.
        r = subprocess.run(["gh", *args], capture_output=True, encoding="utf-8",  # noqa: S603, S607
                           errors="replace", timeout=TIMEOUT, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CannotCheck(f"gh did not answer within {TIMEOUT}s") from exc
    except OSError as exc:
        raise CannotCheck(f"gh could not run: {exc}") from exc
    err = r.stderr.strip()
    low = err.lower()
    if r.returncode != 0:
        # The repository first: gh's "no GitHub remote" message also suggests `gh auth login`.
        if any(s in low for s in ("not a git repository", "failed to determine base repo",
                                  "none of the git remotes", "could not resolve to a repository",
                                  "no git remotes")):
            raise CannotCheck("not a GitHub repository")
        # gh exits 4 when it needs authentication; a rejected token is an HTTP 401.
        if r.returncode == 4 or "gh auth login" in low or "http 401" in low \
                or "bad credentials" in low:
            raise CannotCheck("gh is not authenticated")
        first = err.splitlines()[0][:120] if err else f"exit {r.returncode}"
        raise CannotCheck(f"gh failed: {first}")
    try:
        return json.loads(r.stdout)
    except ValueError as exc:
        raise CannotCheck("gh failed: its output is not JSON") from exc


def started_a_step(jobs: object) -> bool:
    """Did any job of the run start any step?"""
    if not isinstance(jobs, list):
        return False
    for job in jobs:
        for step in (job.get("steps") or []) if isinstance(job, dict) else []:
            if isinstance(step, dict) and step.get("status") in ("in_progress", "completed") \
                    and step.get("conclusion") != "skipped":
                return True
    return False


def steps_started(runs: list[dict]) -> Iterator[bool]:
    """For each run in order: did it start a step? The newest is asked alone -- on a live CI that
    one answer is the verdict -- and the rest together, so an inert CI costs one wait, not ten."""
    def one(run: dict) -> bool:
        view = gh(["run", "view", str(run.get("databaseId")), "--json", "jobs"])
        return started_a_step(view.get("jobs") if isinstance(view, dict) else None)

    if not runs:
        return
    yield one(runs[0])
    if len(runs) > 1:
        with ThreadPoolExecutor(max_workers=len(runs) - 1) as pool:
            yield from pool.map(one, runs[1:])


def verdict() -> str:
    if shutil.which("gh") is None:
        return "CANNOT CHECK -- gh not installed"
    try:
        runs = gh(["run", "list", "--limit", str(LIMIT),
                   "--json", "databaseId,status,conclusion,workflowName"])
        if not isinstance(runs, list):
            raise CannotCheck("gh failed: `gh run list` did not return a list")
        if not runs:
            return "no runs yet"
        done = [r for r in runs if isinstance(r, dict) and r.get("status") == "completed"]
        never = 0
        for run, started in zip(done, steps_started(done), strict=False):    # newest first, as gh lists them
            if started:
                if never:
                    break
                return (f"ok -- the latest run executed steps ({run.get('workflowName')}, "
                        f"{run.get('conclusion')})")
            if run.get("conclusion") in NO_EVIDENCE:
                continue
            never += 1
    except CannotCheck as exc:
        return f"CANNOT CHECK -- {exc}"
    if never:
        return (f"WARN -- the last {never} CI run(s) started no step (a billing or runner limit?); "
                "the only enforcement here is the local gate and pre-push")
    return (f"no completed run to judge -- the last {len(runs)} run(s) are queued, in progress, "
            "skipped or cancelled")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    print(f"ci-liveness: {verdict()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
