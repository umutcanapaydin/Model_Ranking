#!/bin/bash
# Run the app the way a person wants to: one command, repeatable, no Xcode window.
#
#   ./ios/app.sh up       engine + simulator + build + install + launch
#   ./ios/app.sh down     stop the app and the engine (leaves the simulator open)
#   ./ios/app.sh restart   rebuild and relaunch, engine untouched
#   ./ios/app.sh logs      follow the engine's log
#   ./ios/app.sh status    what is actually running right now
#
# Why `open -a Simulator` is in here: `simctl boot` starts the device HEADLESS. It runs, the app
# installs, screenshots work — and nothing appears on screen. That is almost certainly what
# "the simulator wasn't working" was.

set -u

REPO="/Users/umutcanapaydin/Desktop/ILGAR/model_ranking"
DEVICE="${MR_DEVICE:-iPhone 17 Pro}"
BUNDLE="com.ilgar.modelranking"
PORT=8080
BUILD_DIR="$REPO/ios/.build"
ENGINE_LOG="$BUILD_DIR/engine.log"

cd "$REPO" || exit 1
mkdir -p "$BUILD_DIR"

engine_up() { curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; }

# Kills the engine and WAITS for it to actually be gone.
#
# The first version of this script reported "engine: stopped" and returned immediately, and a
# following `up` then saw the dying process still answering /health and skipped starting a new one
# -- so the app talked to an engine that was on its way out. A stop that reports success without
# confirming it is the defect this whole project keeps finding, and it took about ninety seconds to
# reproduce in the script written to avoid it.
stop_engine() {
  pkill -f "uvicorn app.adapter.main:app" 2>/dev/null
  for _ in $(seq 1 20); do
    engine_up || { echo "engine   : stopped"; return 0; }
    sleep 0.25
  done
  echo "engine   : STILL ANSWERING on :$PORT after being asked to stop."
  echo "           Something else is holding the port:"
  lsof -nP -iTCP:$PORT -sTCP:LISTEN 2>/dev/null | tail -2
  return 1
}

start_engine() {
  if engine_up; then
    echo "engine   : already up  $(curl -s http://127.0.0.1:$PORT/health)"
    return
  fi
  if [ ! -f "$REPO/advisor.db" ]; then
    echo "engine   : FAILED — advisor.db is missing. Build it first:"
    echo "           .venv/bin/python -m app.workflows.build --db advisor.db --epoch-dir <bundle>"
    exit 1
  fi
  echo "engine   : starting on :$PORT"
  APP_ENV=test MODEL_RANKING_DB=advisor.db APP_BUILD="dev-$(git rev-parse --short HEAD)" \
    "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app \
    --host 127.0.0.1 --port "$PORT" > "$ENGINE_LOG" 2>&1 &
  for _ in $(seq 1 20); do
    sleep 0.5
    engine_up && { echo "engine   : up  $(curl -s http://127.0.0.1:$PORT/health)"; return; }
  done
  echo "engine   : FAILED to start. Last lines:"
  tail -5 "$ENGINE_LOG"
  exit 1
}

start_simulator() {
  local state
  state=$(xcrun simctl list devices | grep "$DEVICE (" | head -1)
  if echo "$state" | grep -q "Booted"; then
    echo "simulator: already booted"
  else
    echo "simulator: booting $DEVICE"
    xcrun simctl boot "$DEVICE" 2>/dev/null
    sleep 8
  fi
  # THE LINE THAT MAKES IT VISIBLE. `simctl boot` runs the device headless.
  open -a Simulator
  sleep 2
}

build_and_launch() {
  echo "build    : compiling…"
  if ! xcodebuild -project ios/ModelRanking.xcodeproj -scheme ModelRanking \
      -destination "platform=iOS Simulator,name=$DEVICE" -configuration Debug \
      -derivedDataPath "$BUILD_DIR/dd" build CODE_SIGNING_ALLOWED=NO \
      > "$BUILD_DIR/build.log" 2>&1; then
    echo "build    : FAILED"
    grep -E "error:" "$BUILD_DIR/build.log" | head -10
    exit 1
  fi
  echo "build    : ok"

  local app
  app=$(find "$BUILD_DIR/dd" -name "ModelRanking.app" -type d | head -1)
  xcrun simctl terminate booted "$BUNDLE" 2>/dev/null
  xcrun simctl install booted "$app" || exit 1
  xcrun simctl launch booted "$BUNDLE" >/dev/null && echo "app      : launched"
}

case "${1:-up}" in
  up)
    start_engine
    start_simulator
    build_and_launch
    echo
    echo "Ready. The Simulator window should be in front of you."
    echo "  ./ios/app.sh restart   after a code change"
    echo "  ./ios/app.sh down      when you are finished"
    ;;
  restart)
    engine_up || { echo "engine   : not running — use 'up'"; exit 1; }
    start_simulator
    build_and_launch
    ;;
  down)
    xcrun simctl terminate booted "$BUNDLE" 2>/dev/null && echo "app      : stopped"
    if engine_up; then stop_engine; else echo "engine   : was not running"; fi
    echo "simulator: left open on purpose — 'xcrun simctl shutdown all' closes it"
    ;;
  logs)
    echo "following $ENGINE_LOG (ctrl-C to stop)"
    tail -f "$ENGINE_LOG"
    ;;
  status)
    engine_up && echo "engine   : UP    $(curl -s http://127.0.0.1:$PORT/health)" \
               || echo "engine   : down"
    xcrun simctl list devices | grep "$DEVICE (" | head -1 | sed 's/^ */simulator: /'
    xcrun simctl spawn booted launchctl list 2>/dev/null | grep -q "$BUNDLE" \
      && echo "app      : running" || echo "app      : not running"
    ;;
  *)
    echo "usage: ./ios/app.sh [up|restart|down|logs|status]"
    exit 2
    ;;
esac
