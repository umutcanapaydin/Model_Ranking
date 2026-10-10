#!/usr/bin/env bash
# M19-W5: deploy the hosted engine to Fly.io (D-116, `fly.toml`). The owner runs it; nothing else does.
#
#   scripts/deploy_hosted_engine.sh             derive the public artifact, deploy, check /health
#   scripts/deploy_hosted_engine.sh --dry-run   derive it and check the tree; deploy nothing
#
# In order, stopping at the first failure:
#  1. The tree must be committed, untracked files included, and its commit on origin/main: the image
#     is stamped with this commit (APP_BUILD, L.7) and built from this tree, and a release is what
#     `main` holds.
#  2. The public artifact (#88, `app.workflows.public`) is derived from the one this Mac's engine
#     serves (MODEL_RANKING_SERVED) into build/hosted/advisor.db, the file the image's `hosted` stage
#     copies. The Mac's artifact is only read; the refresh stays on the Mac (D-116).
#  3. `fly deploy` builds that stage on Fly's builder, on one machine (`--ha=false`; Fly places two by
#     default), stamped release-<sha>-data-<digest>-from-<sha>: the code, the data it carries, and the
#     release that built that data, read from the refresh's record beside it (#198). Data another
#     release built is refused unless DEPLOY_ACCEPT_DATA_FROM names that release (the M21-W1 review's M4).
#  4. https://<app>.fly.dev/health must answer that build.
#
# The first time, the owner's own steps (D-123): `fly auth login`, a payment method on the Fly
# account, and `fly apps create <app>` with the `app` name in fly.toml.
set -euo pipefail
REPO="${MODEL_RANKING_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
SERVED="${MODEL_RANKING_SERVED:-$HOME/Library/Application Support/model-ranking/engine/data/advisor.db}"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"
TRIES="${DEPLOY_HEALTH_TRIES:-12}"
# No argument, or exactly --dry-run: anything else is refused, never read as a deploy (the second W5
# review's M1).
DRY=0
case "$#:${1:-}" in
  0:) ;;
  1:--dry-run) DRY=1 ;;
  *) echo "[deploy] refused: the only argument is --dry-run (got: $*)" >&2; exit 2 ;;
esac

cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
  echo "[deploy] refused: the tree has changes not committed; the image is stamped with the commit" >&2
  git status --short >&2
  exit 1
fi
# A release is main's tip, read fresh: an older main commit, or a stale origin/main, is refused (the
# second W5 review's R5).
git fetch -q origin main || { echo "[deploy] refused: could not fetch origin/main" >&2; exit 1; }
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  echo "[deploy] refused: HEAD is not the tip of origin/main; a release is what main holds (pull, then deploy)" >&2
  exit 1
fi
APP="$("$PYTHON" -c 'import tomllib; print(tomllib.load(open("fly.toml", "rb"))["app"])')"
if [ ! -f "$SERVED" ]; then
  echo "[deploy] refused: no served artifact at $SERVED (set MODEL_RANKING_SERVED)" >&2
  exit 1
fi

# #198: the release that built the served data, from the refresh's record beside it. Names and ids are
# applied when the data is built, so a Mac that runs an older release ships that release's data.
# `unknown` is a record that names no builder (one written before #198); a copy with no record beside it,
# or a record nobody can read, is `missing` or `unreadable`, which no acceptance covers (the second
# M21-W1 review's R1).
DATA_BY="$("$PYTHON" -c 'import json, os, sys
if not os.path.exists(sys.argv[1]):
    built = "missing"
else:
    try:
        record = json.load(open(sys.argv[1]))
        built = (record.get("served_built_by") if isinstance(record, dict) else None) or "unknown"
    except (OSError, ValueError):
        built = "unreadable"
print(built)' "$SERVED.refresh.json")"
case "$DATA_BY" in
  release-*) FROM="$(printf '%s' "${DATA_BY#release-}" | cut -c1-7)" ;;
  *) FROM="unknown" ;;
esac
HEAD_SHORT="$(git rev-parse HEAD | cut -c1-7)"
echo "[deploy] the data was built by $DATA_BY; the code is release-$HEAD_SHORT"
# The M21-W1 review's M4: data another release built ships that release's names, ids and boards under
# HEAD's stamp (`web-dev` dark before D-190's board arrives). Refused, a dry run included, unless the owner
# names that very release in DEPLOY_ACCEPT_DATA_FROM (`unknown` for a record from before #198).
if [ "$DATA_BY" = "missing" ] || [ "$DATA_BY" = "unreadable" ]; then
  echo "[deploy] refused: the served data's refresh record is $DATA_BY ($SERVED.refresh.json), so nothing" >&2
  echo "         says which release built it, and no DEPLOY_ACCEPT_DATA_FROM accepts that; let the Mac's" >&2
  echo "         engine publish a refresh with this release (docs/release-testflight.md, the v2 section)" >&2
  exit 1
fi
if [ "$FROM" != "$HEAD_SHORT" ]; then
  if [ "${DEPLOY_ACCEPT_DATA_FROM:-}" != "$DATA_BY" ] || { [ "$DATA_BY" != "unknown" ] && [ "${DATA_BY#release-}" = "$DATA_BY" ]; }; then
    echo "[deploy] refused: the served data was built by $DATA_BY, not release-$HEAD_SHORT; let the Mac's" >&2
    echo "         engine publish a refresh with this release (docs/release-testflight.md, the v2 section):" >&2
    echo "         a night whose data is unchanged keeps the old builder's name, and a refresh run by hand" >&2
    echo "         without APP_BUILD records unknown" >&2
    case "$DATA_BY" in  # S5: only a release, or a record from before #198, may be named
      release-*|unknown) echo "         Or deploy it anyway with DEPLOY_ACCEPT_DATA_FROM=$DATA_BY" >&2 ;;
    esac
    exit 1
  fi
  if [ "$DATA_BY" = "unknown" ]; then
    echo "[deploy] accepting data whose builder the record does not name (a record from before #198), as"
    echo "         DEPLOY_ACCEPT_DATA_FROM=unknown asks; it may be an older release's data"
  else
    echo "[deploy] accepting data built by $DATA_BY, as DEPLOY_ACCEPT_DATA_FROM asks"
  fi
fi
mkdir -p build/hosted
"$PYTHON" -m app.workflows.public --from "$SERVED" --to build/hosted/advisor.db
DATA="$("$PYTHON" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:8])' build/hosted/advisor.db)"
BUILD="release-$(git rev-parse --short HEAD)-data-$DATA-from-$FROM"
if [ "$DRY" = 1 ]; then
  echo "[deploy] dry run: build/hosted/advisor.db is ready; $BUILD would be deployed to $APP"
  exit 0
fi

fly deploy --build-arg "APP_BUILD=$BUILD" --remote-only --ha=false

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
