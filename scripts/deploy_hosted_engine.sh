#!/usr/bin/env bash
# M19-W5: deploy the hosted engine to Fly.io (D-116, `fly.toml`). The owner runs it; nothing else does.
#
#   scripts/deploy_hosted_engine.sh             derive the public artifact, deploy, check /health
#   scripts/deploy_hosted_engine.sh --dry-run   derive it and check the tree; deploy nothing
#
# In order, stopping at the first failure:
#  1. The tree must be committed, untracked files included: the image is stamped with this commit
#     (APP_BUILD, L.7) and built from this tree, so it must be exactly what the commit holds.
#  2. The public artifact (#88, `app.workflows.public`) is derived from the one this Mac's engine
#     serves (MODEL_RANKING_SERVED) into build/hosted/advisor.db, the file the image's `hosted` stage
#     copies. The Mac's artifact is only read; the refresh stays on the Mac (D-116).
#  3. `fly deploy` builds that stage on Fly's builder, stamped release-<sha>.
#  4. https://<app>.fly.dev/health must answer that build.
#
# The first time, the owner's own steps (D-123): `fly auth login`, a payment method on the Fly
# account, and `fly apps create <app>` with the `app` name in fly.toml.
set -euo pipefail
REPO="${MODEL_RANKING_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
SERVED="${MODEL_RANKING_SERVED:-$HOME/Library/Application Support/model-ranking/engine/data/advisor.db}"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"
TRIES="${DEPLOY_HEALTH_TRIES:-12}"
DRY=0
if [ "${1:-}" = "--dry-run" ]; then DRY=1; fi

cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
  echo "[deploy] refused: the tree has changes not committed; the image is stamped with the commit" >&2
  git status --short >&2
  exit 1
fi
BUILD="release-$(git rev-parse --short HEAD)"
APP="$("$PYTHON" -c 'import tomllib; print(tomllib.load(open("fly.toml", "rb"))["app"])')"
if [ ! -f "$SERVED" ]; then
  echo "[deploy] refused: no served artifact at $SERVED (set MODEL_RANKING_SERVED)" >&2
  exit 1
fi

mkdir -p build/hosted
"$PYTHON" -m app.workflows.public --from "$SERVED" --to build/hosted/advisor.db
if [ "$DRY" = 1 ]; then
  echo "[deploy] dry run: build/hosted/advisor.db is ready; $BUILD would be deployed to $APP"
  exit 0
fi

fly deploy --build-arg "APP_BUILD=$BUILD" --remote-only

LIVE=""
for try in $(seq 1 "$TRIES"); do
  ANSWER="$(curl -fsS --max-time 20 "https://$APP.fly.dev/health" || true)"
  LIVE="$(printf '%s' "$ANSWER" | "$PYTHON" -c 'import json, sys
try:
    print(json.load(sys.stdin).get("build", ""))
except ValueError:
    print("")')"
  if [ "$LIVE" = "$BUILD" ]; then
    echo "[deploy] https://$APP.fly.dev serves $BUILD"
    exit 0
  fi
  if [ "$try" -lt "$TRIES" ]; then sleep 10; fi
done
echo "[deploy] https://$APP.fly.dev answers build '${LIVE:-nothing}', not $BUILD" >&2
exit 1
