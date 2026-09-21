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

# M14 closure seat, MAJOR-1. The plist no longer names a program inside the repository: since
# W-096 it runs a wrapper under Application Support, because macOS privacy protection stops
# launchd opening a program that lives under ~/Desktop. Installing only the plist therefore left a
# job whose program did not exist -- the same silent outage W-096 was raised for, reinstated by the
# fix for it. The wrapper is part of THIS install, and the two are checked against each other so a
# future edit to either cannot drift apart unnoticed.
WRAPPER_SRC="$REPO/scripts/refresh_job.sh"
WRAPPER_DST="$HOME/Library/Application Support/model-ranking/refresh_job.sh"
WANTED="$(/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:1' "$SRC" 2>/dev/null)"
[ -f "$WRAPPER_SRC" ] || { echo "FAIL: $WRAPPER_SRC is not there"; exit 1; }
if [ "$WANTED" != "$WRAPPER_DST" ]; then
  echo "FAIL: the plist runs"
  echo "        $WANTED"
  echo "      and this installer writes"
  echo "        $WRAPPER_DST"
  echo "      One of the two is wrong. Nothing was installed."
  exit 1
fi
mkdir -p "$(dirname "$WRAPPER_DST")"
cp "$WRAPPER_SRC" "$WRAPPER_DST" || { echo "FAIL: could not copy the wrapper"; exit 1; }
chmod 700 "$WRAPPER_DST"
echo "installed: $WRAPPER_DST"

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
echo "It is on. **The first cycle is in 12 hours, not now.**"
echo
echo "  \`RunAtLoad\` is deliberately absent from the plist, and its own comment says why:"
echo "  installing the job must not immediately rebuild the artifact somebody is serving."
echo "  An earlier version of THIS script said \"the first cycle runs now\", which was a"
echo "  message contradicting the plist it had just installed. Measured after a real load:"
echo "  runs = 0, no log, and the refresh record still showing the previous day."
echo
echo "  To run one through launchd RIGHT NOW — same environment, same redirection, the"
echo "  production path, only the trigger is yours:"
echo "    launchctl kickstart gui/\$(id -u)/$LABEL"
echo "What it leaves behind, which is what actually gets checked:"
echo "  $REPO/advisor.db.refresh.json     <- the record of every cycle"
echo "  ./runner                          <- reads it and reports staleness"
