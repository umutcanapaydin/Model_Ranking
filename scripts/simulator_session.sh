#!/usr/bin/env bash
# REQ-RUN-001 — put the product in front of a person.
#
# Everything this milestone has verified so far describes CODE. 711 Python tests, 39 Swift tests,
# a green contract workflow: none of them has opened the app. This script does the one thing none
# of them can, in one command, and then gets out of the way.
#
# It starts the engine, waits until it actually answers, builds the app, installs it on a booted
# simulator, launches it, and leaves both running until Ctrl-C. It writes nothing into the repo.
set -u

REPO="/Users/umutcanapaydin/Desktop/ILGAR/model_ranking"
OUT="/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/simulator"
mkdir -p "$OUT"
STAMP="$(date '+%Y-%m-%d_%H%M%S')"
LOG="$OUT/session_${STAMP}.log"
ENGINE_LOG="$OUT/engine_${STAMP}.log"
ln -sf "$LOG" "$OUT/latest.log" 2>/dev/null

say() { printf '%s\n' "$*" | tee -a "$LOG"; }

cleanup() {
  say ""
  say "shutting the engine down (pid ${ENGINE_PID:-none})"
  [ -n "${ENGINE_PID:-}" ] && kill "$ENGINE_PID" 2>/dev/null
  say "engine log : $ENGINE_LOG"
  say "session log: $LOG"
}
trap cleanup EXIT INT TERM

say "=== simulator session $STAMP ==="
say "repo : $REPO"
say "HEAD : $(cd "$REPO" && git rev-parse --short HEAD) $(cd "$REPO" && git log -1 --pretty=%s | cut -c1-60)"
say ""

# --- 1. the engine ------------------------------------------------------------------------------
if curl -sf -m 2 http://127.0.0.1:8080/health > /dev/null 2>&1; then
  say "[1/4] engine already answering on 8080 — reusing it, NOT starting a second one"
  ENGINE_PID=""
  # L.7, and this script found it on its own first run: the engine that was already listening was
  # built from an older commit, so it answered `/health` perfectly while serving different code.
  # A session that walks the product against yesterday's engine and writes down what it saw is
  # worse than no session, because the notes look like evidence.
  RUNNING_BUILD="$(printf '%s' "$(curl -sf -m 3 http://127.0.0.1:8080/health)" \
                   | sed -n 's/.*"build":"\([^"]*\)".*/\1/p')"
  HEAD_SHA="$(cd "$REPO" && git rev-parse --short HEAD)"
  case "$RUNNING_BUILD" in
    *"$HEAD_SHA"*) say "  build: $RUNNING_BUILD (current)" ;;
    *) say "  WARNING: the running engine reports build '$RUNNING_BUILD' and HEAD is '$HEAD_SHA'."
       say "           It was started from different code. Stop it and re-run this script, or you"
       say "           will be walking the app against an engine that is not this tree." ;;
  esac
else
  say "[1/4] starting the engine"
  # Both are REQUIRED and the process refuses to boot without them — `validate_startup_config`
  # fails closed on an unset `MODEL_RANKING_DB` (nothing to serve) and an unset `APP_BUILD`
  # (`/health` cannot say which code is live, which is L.7). The first version of this script
  # omitted them and the engine died on import; the error was in a log nobody would have read if
  # the script had not been run before being handed over.
  #
  # `APP_BUILD` is derived from HEAD, which is what makes the drift check above mean anything:
  # an engine started by this script always stamps the commit it was started from.
  ( cd "$REPO" && MODEL_RANKING_DB="$REPO/advisor.db" \
      APP_BUILD="dev-$(git rev-parse --short HEAD)" \
      .venv/bin/python -m uvicorn app.adapter.main:app \
      --host 127.0.0.1 --port 8080 > "$ENGINE_LOG" 2>&1 ) &
  ENGINE_PID=$!
  for _ in $(seq 1 40); do
    curl -sf -m 2 http://127.0.0.1:8080/health > /dev/null 2>&1 && break
    sleep 0.5
  done
fi

HEALTH="$(curl -sf -m 3 http://127.0.0.1:8080/health 2>/dev/null)"
if [ -z "$HEALTH" ]; then
  say "  FAIL: the engine never answered. Last lines of its log:"
  tail -5 "$ENGINE_LOG" 2>/dev/null | sed 's/^/        /' | tee -a "$LOG"
  say "  full log: $ENGINE_LOG"
  exit 1
fi
say "  health: $HEALTH"
# W-058: an engine that is up but cannot rank is the exact state a deploy check used to miss.
# THREE states, not two. The first version of this had two, and reported an engine with no
# `evidence` field at all — every build before M11-W3 — as "not servable". Absent is not the same
# as bad, and reporting a missing measurement as a failed one is how somebody rebuilds a healthy
# artifact. This script's own first run made that mistake against a stale engine.
case "$HEALTH" in
  *'"evidence":"servable"'*|*'"evidence": "servable"'*)
      say "  evidence: servable" ;;
  *'"evidence":"unavailable"'*|*'"evidence": "unavailable"'*)
      say "  STOP: the engine is up and its evidence is NOT servable. The app will show its"
      say "        unavailable state, which is worth seeing once — but it is not a product walk."
      say "        Rebuild: python -m app.workflows.build --db advisor.db --epoch-dir <bundle>" ;;
  *)  say "  evidence: UNKNOWN — this engine has no \`evidence\` field, so it predates M11-W3."
      say "        Not a fault in the artifact; a fault in what is running. Restart the engine." ;;
esac
say ""

# --- 2. the simulator ---------------------------------------------------------------------------
say "[2/4] finding a booted simulator"
DEVICE="$(xcrun simctl list devices booted -j 2>/dev/null \
          | python3 -c 'import json,sys
d=json.load(sys.stdin)["devices"]
for rt in d.values():
    for dev in rt:
        print(dev["udid"]); raise SystemExit' 2>/dev/null)"
if [ -z "$DEVICE" ]; then
  DEVICE="$(xcrun simctl list devices available -j 2>/dev/null \
            | python3 -c 'import json,sys
d=json.load(sys.stdin)["devices"]
best=None
for rt,devs in d.items():
    for dev in devs:
        if dev.get("isAvailable") and dev["name"].startswith("iPhone"):
            best=dev["udid"]
if best: print(best)' 2>/dev/null)"
  say "  none booted — booting $DEVICE"
  xcrun simctl boot "$DEVICE" 2>/dev/null
  open -a Simulator 2>/dev/null
  sleep 6
else
  say "  using booted device $DEVICE"
  open -a Simulator 2>/dev/null
fi

# Both keyboards on, idempotently. Owner ruling 2026-08-23: typing from the Mac keyboard AND the
# app's own keyboard on tap. The Simulator suppresses the on-screen keyboard when a hardware one is
# connected, so the default gives you one or the other.
if osascript "$REPO/scripts/simtools/keyboards_on.scpt" >> "$LOG" 2>&1; then
  say "  hardware keyboard: on — you can type from the Mac"
  say "  software keyboard: press Cmd-K in the Simulator to show it as well."
  say "                     It cannot be set from here: unlike the hardware item, that menu"
  say "                     entry carries no state a script can read, so a script could only"
  say "                     FLIP it — and would turn it back off on the next run."
else
  say "  keyboards: could not be set — grant Accessibility to this terminal in"
  say "             System Settings > Privacy & Security > Accessibility, or set them by hand"
  say "             in the Simulator's I/O > Keyboard menu."
fi
say ""

# --- 3. build + install -------------------------------------------------------------------------
say "[3/4] building for the simulator (this is the first time this app is INSTALLED, not just compiled)"
DERIVED="$OUT/DerivedData"
if ! ( cd "$REPO/ios" && xcodebuild -project ModelRanking.xcodeproj -scheme ModelRanking \
        -destination "id=$DEVICE" -derivedDataPath "$DERIVED" \
        -configuration Debug build ) >> "$LOG" 2>&1; then
  say "  FAIL: the build did not succeed. Read $LOG"
  exit 1
fi
APP="$(find "$DERIVED/Build/Products" -maxdepth 2 -name 'ModelRanking.app' -type d | head -1)"
[ -z "$APP" ] && { say "  FAIL: built, but no .app was produced"; exit 1; }
say "  app: $APP"
xcrun simctl install "$DEVICE" "$APP" >> "$LOG" 2>&1 || { say "  FAIL: install"; exit 1; }
BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist" 2>/dev/null)"
say "  bundle: $BUNDLE_ID"
say ""

# --- 4. launch ----------------------------------------------------------------------------------
say "[4/4] launching"
xcrun simctl launch "$DEVICE" "$BUNDLE_ID" >> "$LOG" 2>&1 || { say "  FAIL: launch"; exit 1; }
say ""
say "=================================================================="
say "The app is running. WHAT TO WALK, and what to write down:"
say ""
say "  1. Does the first screen answer at all, and how long did it take?"
say "  2. The ASK field — type a question in your own words. Try one the"
say "     catalogue measures (\"fix a bug in my python repo\") and one it"
say "     does NOT (\"write me a poem\"). The second must SAY it is not"
say "     something we measure. If it does not say so, that is REQ-RTR-005."
say "  3. Open a category. It shows three picks and the full ranking:"
say "     is the full list too long to be useful? That is W-040, and it is"
say "     the question you said you would answer from the app."
say "  4. Switch the budget. Does 'See all N — M fit your budget' agree"
say "     with what you see?"
say "  5. Anything that looks wrong, however small. A defect found here"
say "     becomes a RED test before it is fixed."
say ""
say "Ctrl-C when you are done — that stops the engine."
say "=================================================================="
wait "${ENGINE_PID:-$$}" 2>/dev/null || true
