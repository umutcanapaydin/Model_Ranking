#!/usr/bin/env bash
# Take off the service `scripts/install_engine_service.sh` put on (#32). The owner runs this; it
# changes his machine. The engine stops, and nothing restarts it until `./ios/app.sh up` or the
# installer. Nothing in the repository is deleted.
set -u
LABEL="com.ilgar.modelranking.engine"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
WRAPPER="$HOME/Library/Application Support/model-ranking/engine_service.sh"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)/$LABEL" || { echo "FAIL: launchd refused the bootout"; exit 1; }
  echo "unloaded: $LABEL"
else
  echo "not loaded: $LABEL"
fi
rm -f "$PLIST" && echo "removed: $PLIST"
rm -f "$WRAPPER" && echo "removed: $WRAPPER"
