#!/usr/bin/env bash
# Install ONLY the launchd wrapper, for a job that is already loaded. W-096, M14 closure MAJOR-1.
#
# `scripts/enable_refresh.sh` installs the wrapper and the plist together and is the path to use
# from scratch. This script exists for the other case: the job is installed and running, the
# wrapper changed, and re-bootstrapping the whole job would be a heavier action than the change.
# `docs/warnings.ledger.md` W-096 names this script; it did not exist until the closure seat
# looked for it, which is the defect this file closes.
#
# It CHANGES STATE on the owner's machine (it writes into ~/Library/Application Support), so it is
# his to run knowingly -- AGENTS.md §5, W-074.
set -u

REPO="/Users/umutcanapaydin/Desktop/ILGAR/model_ranking"
LABEL="com.hcs.modelranking.refresh"
SRC="$REPO/scripts/refresh_job.sh"
DST="$HOME/Library/Application Support/model-ranking/refresh_job.sh"
WANTED="$(/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:1' "$REPO/deploy/$LABEL.plist" 2>/dev/null)"

[ -f "$SRC" ] || { echo "FAIL: $SRC is not there"; exit 1; }
if [ "$WANTED" != "$DST" ]; then
  echo "FAIL: the plist runs '$WANTED', this script writes '$DST'. Nothing installed."
  exit 1
fi

mkdir -p "$(dirname "$DST")"
cp "$SRC" "$DST" || { echo "FAIL: could not copy the wrapper"; exit 1; }
chmod 700 "$DST"
echo "installed: $DST"
echo
echo "The running job picks the new wrapper up on its next cycle -- the plist is unchanged, so"
echo "nothing needs reloading. To run one cycle now, through launchd, with the production"
echo "environment and redirection:"
echo "    launchctl kickstart gui/\$(id -u)/$LABEL"
echo "Then read:  ~/Library/Logs/model-ranking-refresh.log"
