#!/usr/bin/env bash
# #387 (D-217): the hosted engine's night, run by the owner's workflow `nightly-hosted.yml` in two jobs.
#
#   scripts/nightly_hosted.sh refresh <state>   the `refresh` job: fetch, build, keep the state
#   scripts/nightly_hosted.sh deploy <state>    the `deploy` job: the deploy gate, then the deploy script
#
# <state> holds the live artifact (advisor.db) and its refresh record (advisor.db.refresh.json): the previous
# good night's, kept by the workflow as the `hosted-state` Actions artifact, which carry-forward reads (D-156).
#
# refresh: refuses to run beside a token (FLY_API_TOKEN, GITHUB_TOKEN, GH_TOKEN), since the code that parses
#   untrusted data never runs beside one (D-217 clause 2). Runs the cycle the Mac's engine runs, stamped
#   release-<sha>, and writes `outcome=<published|unchanged|failed|refused|busy>` to $GITHUB_OUTPUT. Passes
#   only when the night published or kept its data, so the workflow keeps the state of that night alone.
# deploy: `scripts/deploy_gate.py --check` first; while a release verdict is stale nothing deploys and the
#   night fails (D-217 clause 4). Then the deploy script with --if-new on the kept state, which Fly
#   deploys only when /health does not already answer its build. DEPLOY_ACCEPT_DATA_FROM is never passed, and
#   neither is MODEL_RANKING_REPO, so the tree the gate judged is the tree that ships (the #387 review's M2).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"

if [ "$#" -ne 2 ] || { [ "$1" != refresh ] && [ "$1" != deploy ]; }; then
  echo "usage: scripts/nightly_hosted.sh refresh|deploy <state>" >&2
  exit 2
fi
MODE="$1"
STATE="$2"
cd "$REPO"

if [ "$MODE" = refresh ]; then
  for secret in FLY_API_TOKEN GITHUB_TOKEN GH_TOKEN; do
    if [ -n "${!secret:-}" ]; then
      echo "[night] refused: $secret is in the refresh's environment; the cycle runs beside no token (D-217)" >&2
      exit 1
    fi
  done
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

if [ ! -f "$STATE/advisor.db" ]; then
  echo "[night] refused: no kept artifact at $STATE/advisor.db" >&2
  exit 1
fi
if ! "$PYTHON" scripts/deploy_gate.py --check; then
  echo "[night] nothing deployed: a release verdict has not seen the code on main; run /going-live's delta" >&2
  echo "        review, and the next night deploys (D-217)" >&2
  exit 1
fi
env -u DEPLOY_ACCEPT_DATA_FROM -u MODEL_RANKING_REPO MODEL_RANKING_SERVED="$STATE/advisor.db" PYTHON="$PYTHON" \
  scripts/deploy_hosted_engine.sh --if-new
