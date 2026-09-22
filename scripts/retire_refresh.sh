#!/usr/bin/env bash
# Turn the launchd refresh OFF, because the engine refreshes itself now (D-151, D-154).
#
# The OWNER runs this; an agent does not. It removes a background job from the owner's machine,
# which is the owner's surface in the same way installing it was (scripts/enable_refresh.sh).
#
# Run it only after `./ios/app.sh restart` has started an engine that reports
#   curl -s http://127.0.0.1:8080/health | jq .refresh     ->  "scheduled" or "running"
# so there is never a night with neither refresher. It refuses otherwise.
#
# Nothing in the repository is deleted: deploy/com.hcs.modelranking.refresh.plist stays until the
# owner has run this, and the M16 closure removes it.
set -u

LABEL="com.hcs.modelranking.refresh"
DST="$HOME/Library/LaunchAgents/$LABEL.plist"
WRAPPER="$HOME/Library/Application Support/model-ranking/refresh_job.sh"

[ -n "${HOME:-}" ] || { echo "FAIL: HOME is empty, so the paths below would be wrong"; exit 1; }

# Whatever answers on :8080 is asked only after checking it IS this engine (M16-W2 security pass,
# MINOR-3): another process on that port could otherwise say "scheduled" and retire the only
# refresher there is.
LISTENER="$(lsof -nP -iTCP:8080 -sTCP:LISTEN -t 2>/dev/null | head -1)"
if [ -z "$LISTENER" ] || ! ps -o command= -p "$LISTENER" | grep -q "app.adapter.main:app"; then
  echo "FAIL: nothing on :8080 is this project's engine. Start it with ./ios/app.sh restart first."
  exit 1
fi

STATE="$(curl -sf -m 3 http://127.0.0.1:8080/health | /usr/bin/python3 -c \
  'import json,sys; print(json.load(sys.stdin).get("refresh", "missing"))' 2>/dev/null)"
case "$STATE" in
  scheduled|running) echo "engine refresh: $STATE -- safe to retire the launchd job" ;;
  *)
    echo "FAIL: the engine does not report its own refresh (got: '${STATE:-no answer}')."
    echo "      Start it with ./ios/app.sh restart first; retiring launchd now would leave nothing"
    echo "      refreshing. Nothing was changed."
    exit 1
    ;;
esac

if launchctl print "gui/$(id -u)/$LABEL" > /dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)/$LABEL" || { echo "FAIL: launchd refused the bootout"; exit 1; }
  echo "unloaded: $LABEL"
else
  echo "not loaded: $LABEL"
fi
rm -f "$DST" && echo "removed: $DST"
rm -f "$WRAPPER" && echo "removed: $WRAPPER"

if launchctl print "gui/$(id -u)/$LABEL" > /dev/null 2>&1; then
  echo "FAIL: $LABEL is still loaded"
  exit 1
fi
echo "done: the engine is the only refresher. Its log is ios/.build/engine.log."
