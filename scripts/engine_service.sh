#!/usr/bin/env bash
# The engine, started ONE way (#32): by `ios/app.sh` in the foreground of a developer's day, and by
# the launchd service `com.ilgar.modelranking.engine` that keeps it up across restarts.
#
#   scripts/engine_service.sh             start the engine from whatever is checked out (app.sh)
#   scripts/engine_service.sh --service   the same, but ONLY from `main`; otherwise wait and exit
#
# Why the branch gate. The retired launchd refresher ran "whatever branch is checked out in this
# directory", so working a wave on a branch here made the nightly job run unreviewed code. The
# service refuses that: off `main` it logs why, sleeps, and exits 0, and launchd (KeepAlive) asks
# again, so the engine comes back on its own the moment the checkout is on `main` again.
#
# It runs in the foreground (`exec`), so launchd sees the engine itself: when it dies, launchd
# restarts it after the plist's ThrottleInterval. Everything goes to stdout/stderr, which the
# service sends to ~/Library/Logs and app.sh to ios/.build/engine.log.
set -u
REPO="${MODEL_RANKING_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
PORT=8080
WAIT_S="${ENGINE_SERVICE_WAIT_S:-300}"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

cd "$REPO" || { echo "[engine] $(stamp) cannot cd to $REPO"; exit 90; }

if [ "${1:-}" = "--service" ]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  if [ "$BRANCH" != "main" ]; then
    echo "[engine] $(stamp) the checkout is on '$BRANCH', not main: not starting (#32)."
    echo "[engine] $(stamp) checking again in $WAIT_S s"
    sleep "$WAIT_S"
    exit 0
  fi
fi

if [ ! -f "$REPO/advisor.db" ]; then
  echo "[engine] $(stamp) advisor.db is missing in $REPO: build it first"
  echo "         .venv/bin/python -m app.workflows.build --db advisor.db --fetch-epoch"
  exit 1
fi

export APP_ENV=test MODEL_RANKING_DB=advisor.db APP_BUILD="dev-$(git rev-parse --short HEAD)"
# PREFLIGHT (W-042). The engine serves in the RELAXED lane (`APP_ENV=test`), where
# `validate_startup_config` RETURNS its problems instead of raising; so they are run here, and any
# problem refuses the start. Same evidence and messages, strict consequence.
PREFLIGHT=$("$REPO/.venv/bin/python" -B -c 'from app.adapter.main import validate_startup_config
import sys
problems = validate_startup_config()
if problems:
    print("\n".join(problems))
    sys.exit(1)' 2>&1)
if [ -n "$PREFLIGHT" ]; then
  echo "[engine] $(stamp) REFUSED to start; the startup checks reported:"
  echo "$PREFLIGHT" | sed 's/^/         /'
  exit 1
fi

# D-154: the engine owns the refresh: once a night inside 23:00-01:00, plus one catch-up at start
# when the last good cycle is over a day old.
export MODEL_RANKING_REFRESH=nightly
echo "[engine] $(stamp) starting on :$PORT from $(git rev-parse --abbrev-ref HEAD) at $APP_BUILD"
exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host 127.0.0.1 --port "$PORT"
