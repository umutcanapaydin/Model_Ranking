#!/usr/bin/env bash
# Turn the 12-hour refresh on. REQ-RUN-002, W-054, W-071.
#
# A script rather than a command to paste, for a boring measured reason: the paste wrapped in the
# owner's terminal, `cp` received one argument instead of two, and `launchctl load` then failed
# with `Input/output error` — which is what launchd says when the file is not there, and reads like
# a disk fault. A one-line command that cannot survive a line break is a command that will be run
# wrong.
#
# `bootstrap` rather than `load`: `load` is the deprecated path on this OS and reports failures as
# a single errno with no detail. `bootstrap gui/<uid>` says what actually went wrong.
set -u

REPO="/Users/umutcanapaydin/Desktop/ILGAR/model_ranking"
LABEL="com.hcs.modelranking.refresh"
SRC="$REPO/deploy/$LABEL.plist"
DST="$HOME/Library/LaunchAgents/$LABEL.plist"

[ -f "$SRC" ] || { echo "FAIL: $SRC is not there"; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents"

# Already running? Take it down first, or bootstrap refuses with "service already loaded".
if launchctl print "gui/$(id -u)/$LABEL" > /dev/null 2>&1; then
  echo "already loaded — taking it down first so the new plist is the one that runs"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
fi

cp "$SRC" "$DST" || { echo "FAIL: could not copy the plist"; exit 1; }
echo "installed: $DST"

if ! launchctl bootstrap "gui/$(id -u)" "$DST"; then
  echo "FAIL: launchd refused it. The line above is its own reason — read that, not this."
  exit 1
fi

echo
launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null \
  | grep -E "state|program|last exit code|runs" | sed 's/^/  /'
echo
echo "It is on. The first cycle runs now; the second in 12 hours."
echo "What it leaves behind, which is what actually gets checked:"
echo "  $REPO/advisor.db.refresh.json     <- the record of every cycle"
echo "  ./runner                          <- reads it and reports staleness"
