#!/usr/bin/env bash
# The engine, started ONE way (#32): by `ios/app.sh` from the development checkout, and by the
# launchd service `com.ilgar.modelranking.engine` from a DEPLOYED release of `main`.
#
#   scripts/engine_service.sh             start the engine from this tree (ios/app.sh)
#   scripts/engine_service.sh --service   the same, but only from a deployed release
#
# A deployed release is what `scripts/install_engine_service.sh` writes under
# ~/Library/Application Support/model-ranking/engine/releases/<sha>: `origin/main` exported without
# `.git`, stamped with a RELEASE file, with its own venv. The service runs only such a tree (the
# owner's ruling on the review of #32):
# - nothing launchd touches lives under ~/Desktop, where macOS privacy protection stops launchd's
#   bash from reading a script and git from finding its directory (W-096, review B1);
# - the engine and its nightly refresh child import from the release, so the refresh runs the
#   code the engine was started with, never a branch checked out that night (review B2).
#
# It runs in the foreground (`exec`), so launchd sees the engine itself and restarts it (KeepAlive)
# after the plist's ThrottleInterval. With ENGINE_LOG_FILE set, it writes there, moving the file
# aside first once it passes ENGINE_LOG_MAX_BYTES.
set -u
REPO="${MODEL_RANKING_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
PORT=8080
WAIT_S="${ENGINE_SERVICE_WAIT_S:-300}"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

if [ -n "${ENGINE_LOG_FILE:-}" ]; then
  if [ -f "$ENGINE_LOG_FILE" ] && [ "$(wc -c < "$ENGINE_LOG_FILE")" -gt "${ENGINE_LOG_MAX_BYTES:-10485760}" ]; then
    mv -f "$ENGINE_LOG_FILE" "$ENGINE_LOG_FILE.1"
  fi
  exec >> "$ENGINE_LOG_FILE" 2>&1
fi

cd "$REPO" || { echo "[engine] $(stamp) cannot cd to $REPO"; exit 90; }

if [ -f "$REPO/RELEASE" ]; then
  BUILD="release-$(tr -d '[:space:]' < "$REPO/RELEASE")"
elif [ "${1:-}" = "--service" ]; then
  echo "[engine] $(stamp) $REPO is not a deployed release (no RELEASE stamp): not starting (#32)."
  echo "[engine] $(stamp) deploy one with scripts/install_engine_service.sh; checking again in $WAIT_S s"
  sleep "$WAIT_S"
  exit 0
else
  BUILD="dev-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
fi

DB="${MODEL_RANKING_DB:-advisor.db}"
if [ ! -f "$DB" ]; then
  echo "[engine] $(stamp) the artifact is missing: $DB (MODEL_RANKING_DB, or advisor.db in $REPO)"
  echo "         build it: .venv/bin/python -m app.workflows.build --db advisor.db --fetch-epoch"
  exit 1
fi

export APP_ENV=test MODEL_RANKING_DB="$DB" APP_BUILD="$BUILD"
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
# when the last good cycle is over a day old. Its child runs from this same tree (nightly._REPO).
export MODEL_RANKING_REFRESH=nightly
echo "[engine] $(stamp) starting on :$PORT, $APP_BUILD, serving $DB"
exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host 127.0.0.1 --port "$PORT"
