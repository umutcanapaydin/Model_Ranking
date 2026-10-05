#!/usr/bin/env bash
# D-175: the iOS UI test target (ModelRankingUITests), on the simulator, against a local engine.
#
# Builds the app for 127.0.0.1:$UI_TEST_PORT, starts an engine there from a COPY of the artifact
# (MODEL_RANKING_DB; else the one the engine service serves; else advisor.db in the repo, #139), and
# runs the target in two passes: every class but FailureScreenTests with the engine up, then
# FailureScreenTests after the engine is stopped.
# ScreenAuditTests (#63) captures and asserts nothing, so it runs only when named in UI_TEST_ONLY.
# Not a leg of check-fast, gate or CI: none of them has a simulator and a built artifact. A wave that
# changes a screen cites a run of this in its close record. UI_TEST_ONLY=Class[/test] runs one pass.
set -u

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${UI_TEST_PORT:-8090}"
# #139: the service's artifact first. The checkout's copy can be weeks older (2026-09-24, before the
# refinement boards), and the screen would then be tested on boards the phone no longer gets.
SERVED="$HOME/Library/Application Support/model-ranking/engine/data/advisor.db"
if [ -n "${MODEL_RANKING_DB:-}" ]; then DB="$MODEL_RANKING_DB"
elif [ -f "$SERVED" ]; then DB="$SERVED"
else DB="$REPO/advisor.db"
fi
DEVICE="${UI_TEST_DEVICE:-iPhone 17 Pro}"
OUT="${UI_TEST_OUT:-$REPO/build/ui-test}"
ONLY="${UI_TEST_ONLY:-}"
OFFLINE="FailureScreenTests"

[ -f "$DB" ] || { echo "ui-test: no artifact at $DB (set MODEL_RANKING_DB)"; exit 2; }
[ -x "$REPO/.venv/bin/python" ] || { echo "ui-test: $REPO/.venv is missing; run make install"; exit 2; }
# #139: an artifact without Arena's slice boards, the refinement boards (D-168), is older than the
# screen, which would then be tested on boards the phone no longer gets. Any doubt refuses: the
# check prints `ok` only when the artifact opens read-only and holds a row of a declared slice.
slices="$("$REPO/.venv/bin/python" - "$DB" 2>/dev/null <<'PY'
import sys

from app.workflows.board_tables import ARENA_SLICES
from app.workflows.schema import open_readonly

names = sorted({board.source_name for board in ARENA_SLICES})
marks = ",".join("?" for _ in names)
row = open_readonly(sys.argv[1]).execute(f"SELECT 1 FROM scores WHERE source IN ({marks}) LIMIT 1", names)
print("ok" if row.fetchone() else "none")
PY
)"
if [ "$slices" != ok ]; then
  echo "ui-test: $DB holds none of Arena's slice boards, the refinement boards (D-168): it is older than the screen"
  echo "         build a current one: .venv/bin/python -m app.workflows.refresh --db $(printf '%q' "$DB") --fetch-epoch"
  echo "         or set MODEL_RANKING_DB to a current artifact"
  exit 2
fi
if curl -s -m 1 -o /dev/null "http://127.0.0.1:$PORT/"; then
  echo "ui-test: something already answers on :$PORT; stop it or set UI_TEST_PORT"; exit 2
fi
mkdir -p "$OUT"
rm -rf "$OUT"/*.xcresult
cp "$DB" "$OUT/advisor.db"
echo "ui-test: the engine starts from a copy of $DB"

ENGINE=""
stop_engine() {
  [ -n "$ENGINE" ] || return 0
  kill "$ENGINE" 2>/dev/null
  wait "$ENGINE" 2>/dev/null
  ENGINE=""
}
trap stop_engine EXIT

xcode() {  # $1: action, $2: result bundle name, rest: extra arguments
  local action="$1" name="$2"
  shift 2
  xcodebuild "$action" -project "$REPO/ios/ModelRanking.xcodeproj" -scheme ModelRankingUITests \
    -destination "platform=iOS Simulator,name=$DEVICE" -derivedDataPath "$OUT/dd" \
    ${name:+-resultBundlePath "$OUT/$name.xcresult"} "$@" \
    ENGINE_URL="http://127.0.0.1:$PORT" CODE_SIGNING_ALLOWED=NO >> "$OUT/xcodebuild.log" 2>&1
}

: > "$OUT/xcodebuild.log"
xcode build-for-testing "" || { tail -30 "$OUT/xcodebuild.log"; echo "ui-test: the build failed"; exit 1; }

APP_BUILD=ui-test MODEL_RANKING_DB="$OUT/advisor.db" \
  "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host 127.0.0.1 --port "$PORT" \
  > "$OUT/engine.log" 2>&1 &
ENGINE=$!
for _ in $(seq 1 60); do
  curl -sf -m 1 -o /dev/null "http://127.0.0.1:$PORT/health" && break
  sleep 0.5
done
curl -sf -m 2 -o /dev/null "http://127.0.0.1:$PORT/health" \
  || { echo "ui-test: the engine did not answer on :$PORT; see $OUT/engine.log"; exit 1; }

online=0 offline=0
if [ -n "$ONLY" ]; then
  case "$ONLY" in "$OFFLINE"*) stop_engine ;; esac
  xcode test-without-building only -only-testing:"ModelRankingUITests/$ONLY"; online=$?
else
  xcode test-without-building online -skip-testing:"ModelRankingUITests/$OFFLINE" \
    -skip-testing:ModelRankingUITests/ScreenAuditTests; online=$?
  stop_engine
  xcode test-without-building offline -only-testing:"ModelRankingUITests/$OFFLINE"; offline=$?
fi

grep -E "Test Case .*(passed|failed)|Executed [0-9]+ test|error:" "$OUT/xcodebuild.log" | tail -30
echo "ui-test: engine up exit $online, engine down exit $offline (log $OUT/xcodebuild.log, screenshots in $OUT/*.xcresult)"
[ "$online" -eq 0 ] && [ "$offline" -eq 0 ]
