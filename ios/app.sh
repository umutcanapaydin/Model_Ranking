#!/bin/bash
# Run the app on the simulator: one command, repeatable, no Xcode window.
#
#   ./ios/app.sh up        simulator + build + install + launch
#   ./ios/app.sh restart   rebuild and relaunch the app
#   ./ios/app.sh down      stop the app (leaves the simulator open)
#   ./ios/app.sh status    what is running right now
#
# No engine is started here: the hosted engine is the only engine (D-222). A simulator build talks to
# loopback, so for a local engine run `make run` in another terminal first; without one, the app shows
# its failure screen. A phone build asks the hosted engine (#288).
#
# Why `open -a Simulator` is in here: `simctl boot` starts the device HEADLESS. It runs, the app
# installs, screenshots work — and nothing appears on screen.

set -u

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEVICE="${MR_DEVICE:-iPhone 17 Pro}"
BUNDLE="com.ilgar.modelranking"
PORT=8080
BUILD_DIR="$REPO/ios/.build"

cd "$REPO" || exit 1
mkdir -p "$BUILD_DIR"

engine_up() { curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; }

say_engine() {
  if engine_up; then
    echo "engine   : up  $(curl -s "http://127.0.0.1:$PORT/health")"
  else
    echo "engine   : nothing answers on :$PORT -- run \`make run\` in another terminal"
  fi
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
      ENGINE_URL=http://127.0.0.1:8080 PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE" \
      > "$BUILD_DIR/build.log" 2>&1; then
    echo "build    : FAILED"
    grep -E "error:" "$BUILD_DIR/build.log" | head -10
    exit 1
  fi
  echo "build    : ok"

  local app
  app=$(find "$BUILD_DIR/dd" -name "ModelRanking.app" -type d | head -1)
  xcrun simctl terminate "$DEVICE" "$BUNDLE" 2>/dev/null
  xcrun simctl install "$DEVICE" "$app" || exit 1
  xcrun simctl launch "$DEVICE" "$BUNDLE" >/dev/null && echo "app      : launched"
}

case "${1:-up}" in
  up|restart)
    say_engine
    start_simulator
    build_and_launch
    echo
    echo "Ready. The Simulator window should be in front of you."
    echo "  ./ios/app.sh restart   after a code change"
    echo "  ./ios/app.sh down      when you are finished"
    ;;
  down)
    xcrun simctl terminate "$DEVICE" "$BUNDLE" 2>/dev/null && echo "app      : stopped"
    echo "simulator: left open on purpose — 'xcrun simctl shutdown all' closes it"
    ;;
  status)
    say_engine
    xcrun simctl list devices | grep "$DEVICE (" | head -1 | sed 's/^ */simulator: /'
    xcrun simctl spawn "$DEVICE" launchctl list 2>/dev/null | grep -q "$BUNDLE" \
      && echo "app      : running" || echo "app      : not running"
    ;;
  *)
    echo "usage: ./ios/app.sh [up|restart|down|status]"
    exit 2
    ;;
esac
