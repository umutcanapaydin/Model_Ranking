#!/usr/bin/env bash
# M19-W5: deploy the hosted engine to Fly.io (D-116, `fly.toml`). The owner runs it, and since D-217 the
# owner's nightly workflow does (`scripts/nightly_hosted.sh`); no agent does.
#
#   scripts/deploy_hosted_engine.sh             derive the public artifact, deploy, check /health
#   scripts/deploy_hosted_engine.sh --dry-run   derive it and check the tree, record its stamp; deploy nothing
#   scripts/deploy_hosted_engine.sh --ship      deploy the copy a dry run derived, as it is, unless /health
#                                               already answers its stamp (the night's token step, #389)
#
# In order, stopping at the first failure:
#  1. The tree must be committed, untracked files included, and its commit on origin/main: the image
#     is stamped with this commit (APP_BUILD, L.7) and built from this tree, and a release is what
#     `main` holds.
#  2. The public artifact (#88, `app.workflows.public`) is derived from the one this Mac's engine
#     serves (MODEL_RANKING_SERVED; the night's kept state, D-217) into build/hosted/advisor.db, the file
#     the image's `hosted` stage copies. The served artifact is only read; the refresh never runs on the
#     serving host (D-116).
#  3. `fly deploy` builds that stage on Fly's builder, on one machine (`--ha=false`; Fly places two by
#     default), stamped release-<sha>-data-<digest>-from-<sha>: the code, the data it carries, and the
#     release that built that data, read from the refresh's record beside it (#198). Data another
#     release built is refused unless DEPLOY_ACCEPT_DATA_FROM names that release (the M21-W1 review's M4).
#     A dry run writes that stamp beside the copy, build/hosted/build.txt. --ship opens neither the served
#     artifact nor its record: it reads the stamp, checks that it names this commit, that its writer said
#     this release built the data, and that it carries the copy's own digest, and deploys it unless /health
#     already answers it (D-217 clause 5; #389: the step that holds the token never parses a database).
#     --ship trusts whoever wrote build/hosted: in the night that is the token-free refresh job. By hand,
#     build/hosted is gitignored and no gate sees it, so ship only what a dry run of yours just wrote
#     (the #389 review's M2).
#  4. https://<app>.fly.dev/health must answer that build.
#
# The first time, the owner's own steps (D-123): `fly auth login`, a payment method on the Fly
# account, and `fly apps create <app>` with the `app` name in fly.toml.
set -euo pipefail
# The checkout this script lives in, and no other: the deploy gate judges the tree the call runs in, so
# MODEL_RANKING_REPO, which pointed it at another clone, is not read (#391).
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SERVED="${MODEL_RANKING_SERVED:-$HOME/Library/Application Support/model-ranking/engine/data/advisor.db}"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"
TRIES="${DEPLOY_HEALTH_TRIES:-12}"
# No argument, or exactly --dry-run or --ship: anything else is refused, never read as a deploy (the
# second W5 review's M1).
DRY=0
SHIP=0
case "$#:${1:-}" in
  0:) ;;
  1:--dry-run) DRY=1 ;;
  1:--ship) SHIP=1 ;;
  *) echo "[deploy] refused: the only arguments are --dry-run and --ship (got: $*)" >&2; exit 2 ;;
esac
# The call's tree must be this checkout. The deploy gate matches a command by its basename and judges the
# tree the call runs in, so this script called by path from another clone shipped a tree nobody had judged
# (the queue-1021 integration review's M4, the path form of #391). Both sides are resolved with `pwd -P`.
OWN="$(cd "$REPO" && pwd -P)"
CALLER="$(git rev-parse --show-toplevel 2>/dev/null || true)"
CALLER="${CALLER:+$(cd "$CALLER" && pwd -P)}"
if [ "$CALLER" != "$OWN" ]; then
  echo "[deploy] refused: run it from its own checkout ($OWN); this call runs in ${CALLER:-no git tree}," \
    "and the deploy gate judges the call's tree" >&2
  exit 1
fi

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
# Seven characters always: `git rev-parse --short` grows with the clone, and the night's two jobs clone
# differently (the #389 review's M1).
HEAD_SHORT="$(git rev-parse HEAD | cut -c1-7)"

# The build /health answers, or nothing when it does not answer one.
live_build() {
  curl -fsS --max-time 20 "https://$APP.fly.dev/health" 2>/dev/null | "$PYTHON" -c 'import json, sys
try:
    print(json.load(sys.stdin).get("build", ""))
except ValueError:
    print("")' || true
}

if [ "$SHIP" = 1 ]; then
  if [ ! -f build/hosted/advisor.db ] || [ ! -f build/hosted/build.txt ]; then
    echo "[deploy] refused: nothing prepared; run the dry run first (build/hosted/advisor.db and build.txt)" >&2
    exit 1
  fi
  BUILD="$(head -n 1 build/hosted/build.txt | tr -d '[:space:]')"
  DATA="$("$PYTHON" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:8])' build/hosted/advisor.db)"
  WANT="release-$HEAD_SHORT-data-$DATA-from-$HEAD_SHORT"
  if [ "$BUILD" != "$WANT" ]; then
    echo "[deploy] refused: the prepared stamp '$BUILD' is not $WANT -- this commit, data this release" >&2
    echo "         built, and the prepared copy's own digest $DATA" >&2
    exit 1
  fi
else
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
    echo "         without APP_BUILD records unstamped, which nothing accepts" >&2
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
BUILD="release-$HEAD_SHORT-data-$DATA-from-$FROM"
printf '%s\n' "$BUILD" > build/hosted/build.txt
if [ "$DRY" = 1 ]; then
  echo "[deploy] dry run: build/hosted/advisor.db is ready; $BUILD would be deployed to $APP"
  exit 0
fi
fi

if [ "$SHIP" = 1 ] && [ "$(live_build)" = "$BUILD" ]; then
  echo "[deploy] https://$APP.fly.dev already serves $BUILD; nothing deployed"
  exit 0
fi

fly deploy --build-arg "APP_BUILD=$BUILD" --remote-only --ha=false

LIVE=""
for try in $(seq 1 "$TRIES"); do
  LIVE="$(live_build)"
  if [ "$LIVE" = "$BUILD" ]; then
    echo "[deploy] https://$APP.fly.dev serves $BUILD"
    exit 0
  fi
  if [ "$try" -lt "$TRIES" ]; then sleep 10; fi
done
echo "[deploy] https://$APP.fly.dev answers build '${LIVE:-nothing}', not $BUILD" >&2
exit 1
