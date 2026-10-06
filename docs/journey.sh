#!/usr/bin/env bash
# Stage 5.2 (M19-W5): the black-box journey against the DEPLOYED engine, by `make journey URL=...`.
# After a deploy: `make journey URL=https://model-ranking.fly.dev` (docs/release-testflight.md).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${URL:?URL is the deployed engine, for example https://model-ranking.fly.dev}"
PYTHON="${PYTHON:-$(command -v .venv/bin/python || command -v python3)}"
exec "$PYTHON" scripts/journey.py --base-url "$URL"
