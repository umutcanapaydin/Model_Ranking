#!/usr/bin/env bash
# Take off the launchd service the retired installer put on (#32). The owner runs this once, after a
# hosted night has published (D-222 clause 2); it changes his machine. The engine stops, and nothing in
# the tree restarts it: the hosted engine is the only engine. The deployed releases and the served
# artifact in ~/Library/Application Support/model-ranking/engine are kept; delete that folder by hand
# if wanted. This script goes once the owner has run it (D-224 clause 3).
set -u
[ -n "${HOME:-}" ] || { echo "FAIL: HOME is empty, so the paths below would be wrong"; exit 1; }
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
echo "kept: $HOME/Library/Application Support/model-ranking/engine (releases and the served artifact)"
