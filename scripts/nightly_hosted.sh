#!/usr/bin/env bash
# #387 (D-217): the hosted engine's night, run by the owner's workflow `nightly-hosted.yml` in two jobs.
#
#   scripts/nightly_hosted.sh refresh <state>   the `refresh` job: fetch, build, keep the state
#   scripts/nightly_hosted.sh prepare <state>   the `refresh` job, next: derive the public copy and its stamp
#   scripts/nightly_hosted.sh deploy <public>   the `deploy` job: the deploy gate, then ship the prepared copy
#
# <state> holds the live artifact (advisor.db) and its refresh record (advisor.db.refresh.json): the previous
# good night's, kept by the workflow as the `hosted-state` Actions artifact, which carry-forward reads (D-156).
# <public> holds what `prepare` wrote to build/hosted: advisor.db and build.txt, the `hosted-public` artifact.
#
# refresh and prepare refuse to run beside a token (FLY_API_TOKEN, GITHUB_TOKEN, GH_TOKEN): the code that
#   parses fetched data, and the code that opens what it built, never run beside one (D-217 clause 2, #389).
# refresh: runs the cycle the Mac's engine runs, stamped release-<sha>, and writes
#   `outcome=<published|unchanged|failed|refused|busy>` to $GITHUB_OUTPUT. Passes only when the night
#   published or kept its data, so the workflow keeps the state of that night alone.
# prepare: the deploy script's dry run on the state: the public copy at build/hosted/advisor.db and its stamp
#   at build/hosted/build.txt. Data another release built is refused there.
# deploy: `scripts/deploy_gate.py --check` first; while a release verdict is stale nothing deploys and the
#   night fails (D-217 clause 4). Then the deploy script's --ship, which reads the copy only for its digest
#   and deploys it unless /health already answers its stamp. DEPLOY_ACCEPT_DATA_FROM is never passed, and
#   neither is MODEL_RANKING_REPO, so the tree the gate judged is the tree that ships (the #387 review's M2).
set -euo pipefail
# Git's place variables are not read: the refresh's stamp and the deploy gate's tree are this checkout's,
# whatever GIT_DIR or GIT_WORK_TREE name (the queue-1021 integration review's M5).
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"

if [ "$#" -ne 2 ] || { [ "$1" != refresh ] && [ "$1" != prepare ] && [ "$1" != deploy ]; }; then
  echo "usage: scripts/nightly_hosted.sh refresh|prepare <state> | deploy <public>" >&2
  exit 2
fi
MODE="$1"
STATE="$2"
cd "$REPO"

if [ "$MODE" = refresh ] || [ "$MODE" = prepare ]; then
  for secret in FLY_API_TOKEN GITHUB_TOKEN GH_TOKEN; do
    if [ -n "${!secret:-}" ]; then
      echo "[night] refused: $secret is in the $MODE's environment; it runs beside no token (D-217, #389)" >&2
      exit 1
    fi
  done
fi

if [ "$MODE" = prepare ]; then
  exec env -u DEPLOY_ACCEPT_DATA_FROM -u MODEL_RANKING_REPO MODEL_RANKING_SERVED="$STATE/advisor.db" \
    PYTHON="$PYTHON" scripts/deploy_hosted_engine.sh --dry-run
fi

if [ "$MODE" = refresh ]; then
  mkdir -p "$STATE"
  code=0
  APP_BUILD="release-$(git rev-parse --short=7 HEAD)" \
    "$PYTHON" -B -P -m app.workflows.refresh --db "$STATE/advisor.db" --fetch-epoch || code=$?
  case "$code" in
    0) outcome=published ;;
    1) outcome=unchanged ;;
    2) outcome=failed ;;
    3) outcome=refused ;;
    4) outcome=busy ;;
    *) outcome=failed ;;
  esac
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "outcome=$outcome" >> "$GITHUB_OUTPUT"
  fi
  echo "[night] the refresh $outcome (exit $code)"
  case "$outcome" in
    published|unchanged) exit 0 ;;
    *) exit 1 ;;
  esac
fi

PUBLIC="$STATE"
if [ ! -f "$PUBLIC/advisor.db" ] || [ ! -f "$PUBLIC/build.txt" ]; then
  echo "[night] refused: no prepared copy at $PUBLIC (advisor.db and build.txt)" >&2
  exit 1
fi
if ! "$PYTHON" scripts/deploy_gate.py --check; then
  echo "[night] nothing deployed: a release verdict has not seen the code on main; run /going-live's delta" >&2
  echo "        review, and the next night deploys (D-217)" >&2
  exit 1
fi
# The copy is moved into the build context, the file the image's `hosted` stage copies; its bytes are not read.
mkdir -p build/hosted
if [ "$(cd "$PUBLIC" && pwd -P)" != "$(cd build/hosted && pwd -P)" ]; then
  cp "$PUBLIC/advisor.db" "$PUBLIC/build.txt" build/hosted/
fi
exec env -u DEPLOY_ACCEPT_DATA_FROM -u MODEL_RANKING_REPO PYTHON="$PYTHON" scripts/deploy_hosted_engine.sh --ship
