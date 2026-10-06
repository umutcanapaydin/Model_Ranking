#!/usr/bin/env bash
# Stage 5.2 (M19-W5): `make cold-start`. The REAL image's `hosted` stage, booted from nothing: no
# volume, no state, a fresh container, as Fly boots it. It derives the public artifact the image
# carries (#88), builds the image locally with Docker, runs it on loopback, waits for /health,
# runs the black-box journey against it, and removes the container whatever happens. Run it before
# a deploy, with Docker Desktop running.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
SERVED="${MODEL_RANKING_SERVED:-$HOME/Library/Application Support/model-ranking/engine/data/advisor.db}"
PORT="${COLD_START_PORT:-18080}"
WAIT_S="${COLD_START_WAIT_S:-60}"
IMAGE="model-ranking:cold-start"
NAME="model-ranking-cold-start"

if [ ! -f "$SERVED" ]; then
  echo "[cold-start] no served artifact at $SERVED (set MODEL_RANKING_SERVED)" >&2
  exit 1
fi
mkdir -p build/hosted
"$PYTHON" -m app.workflows.public --from "$SERVED" --to build/hosted/advisor.db
docker build --target hosted --build-arg "APP_BUILD=cold-start-$(git rev-parse --short HEAD)" -t "$IMAGE" .

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Loopback only, nothing mounted; the Host list names the address the journey asks.
docker run -d --name "$NAME" -p "127.0.0.1:$PORT:8080" -e MODEL_RANKING_ALLOWED_HOSTS=127.0.0.1 "$IMAGE"

for _ in $(seq 1 "$WAIT_S"); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    "$PYTHON" scripts/journey.py --base-url "http://127.0.0.1:$PORT"
    exit $?
  fi
  sleep 1
done
echo "[cold-start] the container never answered /health; its log:" >&2
docker logs "$NAME" >&2 || true
exit 1
