#!/usr/bin/env bash
# Deploy `origin/main` and keep the ENGINE running under launchd (#32). The owner runs this, and
# runs it again after merging a pull request to put the new `main` live: it changes his machine
# (AGENTS.md §5, W-074).
#
#   scripts/install_engine_service.sh                  deploy, install or restart, wait for /health
#   scripts/install_engine_service.sh --print-plist    the plist it writes (tests read it)
#   scripts/install_engine_service.sh --print-wrapper  the wrapper it writes
#   scripts/install_engine_service.sh --deploy-only DIR [--no-venv]   deploy into DIR, nothing else
#
# The shape, and why (the owner's ruling on the review of #32):
# - The service runs a DEPLOYED copy of `origin/main`, never this development checkout:
#   ~/Library/Application Support/model-ranking/engine/releases/<sha>, exported with `git archive`
#   (no `.git`), with its own venv, and `current` pointing at the live one. The served artifact
#   and its refresh record live in engine/data/ and survive every redeploy. So the engine and its
#   nightly refresh child run reviewed code, whatever branch is checked out here (review B2).
# - Nothing launchd touches is under ~/Desktop: launchd runs /bin/bash on a wrapper in Application
#   Support, which hands over to the release's launcher; the logs are in ~/Library/Logs (W-096,
#   review B1).
# `scripts/remove_engine_service.sh` takes the service off.
set -u
REPO="${MODEL_RANKING_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
LABEL="com.ilgar.modelranking.engine"
BASE="$HOME/Library/Application Support/model-ranking"
DEPLOY="$BASE/engine"
WRAPPER="$HOME/Library/Application Support/model-ranking/engine_service.sh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/model-ranking-engine.log"
LAUNCHD_LOG="$HOME/Library/Logs/model-ranking-engine-launchd.log"
KEEP_RELEASES=3
PORT=8080

wrapper() {
  cat <<WRAP
#!/bin/bash
# Written by scripts/install_engine_service.sh (#32). launchd runs this; it hands over to the
# deployed release, which serves the artifact kept beside the releases.
export MODEL_RANKING_DB="$DEPLOY/data/advisor.db"
export ENGINE_LOG_FILE="$LOG"
exec /bin/bash "$DEPLOY/current/scripts/engine_service.sh" --service
WRAP
}

plist() {
  cat <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$WRAPPER</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>StandardOutPath</key><string>$LAUNCHD_LOG</string>
  <key>StandardErrorPath</key><string>$LAUNCHD_LOG</string>
</dict>
</plist>
PLIST
}

# deploy TARGET WITH_VENV: origin/main into TARGET/releases/<sha>, then TARGET/current -> it.
deploy() {
  local target="$1" with_venv="$2" sha rel python
  git -C "$REPO" fetch -q origin main || { echo "FAIL: git fetch origin main"; return 1; }
  sha="$(git -C "$REPO" rev-parse --short origin/main)" || return 1
  rel="$target/releases/$sha"
  if [ ! -f "$rel/RELEASE" ]; then
    # RELEASE is written last: a tree without it is an interrupted deploy, redone from scratch.
    rm -rf "$rel" && mkdir -p "$rel"
    git -C "$REPO" archive origin/main | tar -x -C "$rel" || { echo "FAIL: export of origin/main"; return 1; }
    if [ "$with_venv" = yes ]; then
      python="$("$REPO/.venv/bin/python" -c 'import sys; print(sys._base_executable)')" \
        || { echo "FAIL: no base interpreter from $REPO/.venv"; return 1; }
      "$python" -m venv "$rel/.venv" && "$rel/.venv/bin/python" -m pip install -q -e "$rel" \
        || { echo "FAIL: the release's venv"; return 1; }
    fi
    echo "$sha" > "$rel/RELEASE"
  fi
  mkdir -p "$target/data"
  if [ ! -f "$target/data/advisor.db" ] && [ -f "$REPO/advisor.db" ]; then
    cp "$REPO/advisor.db" "$target/data/advisor.db" && echo "artifact: copied from $REPO"
    [ -f "$REPO/advisor.db.refresh.json" ] && cp "$REPO/advisor.db.refresh.json" "$target/data/"
  fi
  ln -sfn "releases/$sha" "$target/current"
  # Older releases go, keeping the live one and the ones just before it.
  ls -1t "$target/releases" | tail -n +$((KEEP_RELEASES + 1)) | while read -r old; do
    [ "$old" = "$sha" ] || rm -rf "$target/releases/$old"
  done
  echo "deployed: $sha -> $target/current"
}

case "${1:-}" in
  --print-plist) plist; exit 0 ;;
  --print-wrapper) wrapper; exit 0 ;;
  --deploy-only)
    [ -n "${2:-}" ] || { echo "usage: --deploy-only DIR [--no-venv]"; exit 2; }
    WITH_VENV=yes; [ "${3:-}" = "--no-venv" ] && WITH_VENV=no
    deploy "$2" "$WITH_VENV"; exit $? ;;
  "") ;;
  *) echo "usage: scripts/install_engine_service.sh [--print-plist|--print-wrapper|--deploy-only DIR]"; exit 2 ;;
esac

[ -n "${HOME:-}" ] || { echo "FAIL: HOME is empty"; exit 1; }
[ -x "$REPO/.venv/bin/python" ] || { echo "FAIL: $REPO/.venv is missing; run make install first"; exit 1; }
deploy "$DEPLOY" yes || exit 1
[ -f "$DEPLOY/data/advisor.db" ] || { echo "FAIL: no artifact to serve in $DEPLOY/data"; exit 1; }

# An engine started by hand holds the port, and the service's would then fail and retry. Stop it,
# but only if the listener IS this project's engine (review M4).
LISTENER="$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1)"
if [ -n "$LISTENER" ] && ! launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  if ps -o command= -p "$LISTENER" | grep -q "app.adapter.main:app"; then
    kill "$LISTENER" && echo "stopped: the engine started by hand (pid $LISTENER)" && sleep 2
  else
    echo "FAIL: something else listens on :$PORT; nothing was installed"; exit 1
  fi
fi

mkdir -p "$(dirname "$WRAPPER")" "$(dirname "$PLIST")" "$(dirname "$LOG")"
wrapper > "$WRAPPER" && chmod 700 "$WRAPPER" && echo "written: $WRAPPER"
plist > "$PLIST" && plutil -lint -s "$PLIST" && echo "written: $PLIST" \
  || { echo "FAIL: the plist did not lint"; exit 1; }

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/$LABEL" && echo "restarted: $LABEL"
else
  launchctl bootstrap "gui/$(id -u)" "$PLIST" || { echo "FAIL: launchd refused the service"; exit 1; }
  echo "loaded: $LABEL"
fi

for _ in $(seq 1 120); do
  if curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null; then
    echo "engine: UP  $(curl -s "http://127.0.0.1:$PORT/health")"
    echo "log:    $LOG"
    exit 0
  fi
  sleep 0.5
done
# Review M4: a service that cannot start is not left retrying every minute unnoticed.
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
echo "FAIL: the engine did not answer within 60 s; the service is unloaded again. Last lines:"
tail -8 "$LOG" 2>/dev/null; tail -3 "$LAUNCHD_LOG" 2>/dev/null
exit 1
