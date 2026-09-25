#!/usr/bin/env bash
# Install the launchd service that keeps the ENGINE running (#32). The owner runs this: it adds a
# background job to his machine (AGENTS.md §5, W-074).
#
#   scripts/install_engine_service.sh                 install, start, and wait for /health
#   scripts/install_engine_service.sh --print-plist   print the plist it would write (tests read it)
#   scripts/install_engine_service.sh --print-wrapper print the wrapper it would write
#
# The shape is W-096's, the one that worked for the retired refresher: launchd cannot open a
# program or a log under ~/Desktop, where this repository lives. So launchd runs /bin/bash on a
# one-line wrapper in Application Support, which hands over to the repository's own launcher
# (`scripts/engine_service.sh --service`), and the logs go to ~/Library/Logs. The plist and the
# wrapper are generated here, so the tree holds no second copy of either.
#
# The service starts the engine only while this checkout is on `main` (see engine_service.sh).
# `scripts/remove_engine_service.sh` takes it off.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.ilgar.modelranking.engine"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
WRAPPER="$HOME/Library/Application Support/model-ranking/engine_service.sh"
LOG="$HOME/Library/Logs/model-ranking-engine.log"
LAUNCHER="$REPO/scripts/engine_service.sh"
PORT=8080

wrapper() {
  cat <<WRAP
#!/bin/bash
# Written by scripts/install_engine_service.sh (#32). launchd cannot open programs under ~/Desktop
# (W-096), so it runs this, and this hands over to the repository's launcher.
exec /bin/bash "$LAUNCHER" --service
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
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLIST
}

case "${1:-}" in
  --print-plist) plist; exit 0 ;;
  --print-wrapper) wrapper; exit 0 ;;
  "") ;;
  *) echo "usage: scripts/install_engine_service.sh [--print-plist|--print-wrapper]"; exit 2 ;;
esac

[ -x "$REPO/.venv/bin/python" ] || { echo "FAIL: $REPO/.venv is missing; run make install first"; exit 1; }
[ -f "$REPO/advisor.db" ] || { echo "FAIL: $REPO/advisor.db is missing; build it first"; exit 1; }
BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "main" ] || echo "note: this checkout is on '$BRANCH'; the service waits until it is on main"

# An engine started by hand holds the port, and the service's engine would then fail and retry
# every minute. Stop it first, as ios/app.sh does.
if lsof -nP -iTCP:$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  pkill -f "uvicorn app.adapter.main:app" 2>/dev/null && echo "stopped: the engine started by hand"
  sleep 2
fi

mkdir -p "$(dirname "$WRAPPER")" "$(dirname "$PLIST")" "$(dirname "$LOG")"
wrapper > "$WRAPPER" && chmod 700 "$WRAPPER" && echo "written: $WRAPPER"
plist > "$PLIST" && plutil -lint -s "$PLIST" && echo "written: $PLIST" \
  || { echo "FAIL: the plist did not lint"; exit 1; }

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$PLIST" || { echo "FAIL: launchd refused the service"; exit 1; }
echo "loaded: $LABEL"

for _ in $(seq 1 40); do
  if curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null; then
    echo "engine: UP  $(curl -s "http://127.0.0.1:$PORT/health")"
    echo "log:    $LOG"
    exit 0
  fi
  sleep 0.5
done
echo "engine: not answering yet. Read the log: $LOG"
tail -5 "$LOG" 2>/dev/null
exit 1
