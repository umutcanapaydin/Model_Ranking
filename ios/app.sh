#!/bin/bash
# Run the app the way a person wants to: one command, repeatable, no Xcode window.
#
#   ./ios/app.sh up       engine + simulator + build + install + launch
#   ./ios/app.sh down     stop the app and the engine (leaves the simulator open)
#   ./ios/app.sh restart   rebuild and relaunch BOTH the engine and the app
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
# D-158: the engine's nightly refresh fetches the Epoch bundle itself. An owner-supplied bundle is
# passed only when MR_EPOCH_DIR names one; the hand-kept 2026-08-15 folder is retired.
EPOCH_DIR="${MR_EPOCH_DIR:-}"
if [ -n "$EPOCH_DIR" ]; then export MODEL_RANKING_EPOCH_DIR="$EPOCH_DIR"; else unset MODEL_RANKING_EPOCH_DIR; fi
PORT=8080
BUILD_DIR="$REPO/ios/.build"
ENGINE_LOG="$BUILD_DIR/engine.log"
# #32: the launchd service that keeps the engine up (scripts/install_engine_service.sh). When it is
# installed, the engine is started and stopped THROUGH launchd: a `pkill` would only be undone by
# its KeepAlive a minute later.
SERVICE_LABEL="com.ilgar.modelranking.engine"
SERVICE_PLIST="$HOME/Library/LaunchAgents/$SERVICE_LABEL.plist"
SERVICE_LOG="$HOME/Library/Logs/model-ranking-engine.log"
service_installed() { [ -f "$SERVICE_PLIST" ]; }

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
  if service_installed; then
    # Unloaded until the next `up` or login; the plist stays, so the service comes back then.
    launchctl bootout "gui/$(id -u)/$SERVICE_LABEL" 2>/dev/null
  else
    pkill -f "uvicorn app.adapter.main:app" 2>/dev/null
  fi
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
  # One launcher (#32): scripts/engine_service.sh runs the W-042 preflight and starts the engine
  # with the nightly refresh (D-151, D-154), exactly as the launchd service does.
  if service_installed; then
    echo "engine   : starting through the launchd service $SERVICE_LABEL (runs from main only)"
    launchctl bootstrap "gui/$(id -u)" "$SERVICE_PLIST" 2>/dev/null \
      || launchctl kickstart "gui/$(id -u)/$SERVICE_LABEL"
  else
    echo "engine   : starting on :$PORT (refreshes itself nightly, 23:00-01:00; D-151, D-154)"
    "$REPO/scripts/engine_service.sh" > "$ENGINE_LOG" 2>&1 &
  fi
  for _ in $(seq 1 20); do
    sleep 0.5
    engine_up && { echo "engine   : up  $(curl -s http://127.0.0.1:$PORT/health)"; return; }
  done
  echo "engine   : FAILED to start. Last lines:"
  if service_installed; then tail -5 "$SERVICE_LOG"; else tail -5 "$ENGINE_LOG"; fi
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
    # The ENGINE is cycled too, and it was not always. This command used to leave the engine
    # running while `up` advertised it as the thing to run "after a code change" — true for Swift,
    # silently false for Python and for a rebuilt advisor.db, because a running process keeps the
    # old file's inode and `/health` goes on answering 200. That is L.7 exactly: restart is not
    # rebuild, and the build stamp is the only thing that tells you which you got. It cost one
    # debugging round here: nine categories in the artifact, three on the wire, everything green.
    if engine_up; then stop_engine; fi
    start_engine
    start_simulator
    build_and_launch
    echo "engine   : $(curl -sf -m 2 "http://127.0.0.1:$PORT/health" || echo unreachable)"
    ;;
  down)
    xcrun simctl terminate booted "$BUNDLE" 2>/dev/null && echo "app      : stopped"
    if engine_up; then stop_engine; else echo "engine   : was not running"; fi
    echo "simulator: left open on purpose — 'xcrun simctl shutdown all' closes it"
    ;;
  logs)
    LOG="$ENGINE_LOG"; service_installed && LOG="$SERVICE_LOG"
    echo "following $LOG (ctrl-C to stop)"
    tail -f "$LOG"
    ;;
  status)
    engine_up && echo "engine   : UP    $(curl -s http://127.0.0.1:$PORT/health)" \
               || echo "engine   : down"
    if service_installed; then
      launchctl print "gui/$(id -u)/$SERVICE_LABEL" >/dev/null 2>&1 \
        && echo "service  : $SERVICE_LABEL installed and loaded" \
        || echo "service  : $SERVICE_LABEL installed, not loaded (./ios/app.sh up loads it)"
    else
      echo "service  : not installed (scripts/install_engine_service.sh keeps the engine up)"
    fi
    xcrun simctl list devices | grep "$DEVICE (" | head -1 | sed 's/^ */simulator: /'
    xcrun simctl spawn booted launchctl list 2>/dev/null | grep -q "$BUNDLE" \
      && echo "app      : running" || echo "app      : not running"
    ;;
  *)
    echo "usage: ./ios/app.sh [up|restart|down|logs|status]"
    exit 2
    ;;
esac
