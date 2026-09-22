#!/usr/bin/env bash
# launchd entry point for the 12-hour refresh (REQ-REF-005, D-130; W-096).
#
# WHY A WRAPPER. From 2026-08-27 to 2026-09-20 the job exited 78 (EX_CONFIG) on every trigger and
# wrote nothing. Nine probes cleared, by measurement, the Desktop log paths, the Desktop working
# directory, the venv interpreter, the symlink chain, the plist's location, its contents and the
# job's registration; the command itself runs and publishes by hand. The one shape that worked
# under launchd was this: /bin/bash as the program, the directory and PYTHONPATH set by the script.
# The exact mechanism behind the 78 was not isolated, and the hunt stopped deliberately once a
# working shape existed. See `docs/warnings.ledger.md` W-096.
#
# Everything this job does is written to stdout/stderr, which the plist sends to the refresh logs,
# so a failure is never silent again: the first line appears before anything can go wrong.

set -u

REPO="/Users/umutcanapaydin/Desktop/ILGAR/model_ranking"
EPOCH="/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data"

echo "[refresh_job] $(date '+%Y-%m-%d %H:%M:%S') start"
cd "$REPO" || { echo "[refresh_job] cannot cd to $REPO"; exit 90; }
export PYTHONPATH="$REPO/src"

"$REPO/.venv/bin/python" -B -m app.workflows.refresh --db "$REPO/advisor.db" --epoch-dir "$EPOCH"
rc=$?

# refresh's own codes: 0 published, 1 unchanged, 2 failed, 3 refused (D-128), 4 busy.
echo "[refresh_job] $(date '+%Y-%m-%d %H:%M:%S') exit $rc"
exit $rc
