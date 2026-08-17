#!/usr/bin/env bash
# Stage 4.3 / seed L.8 entry point. The work is in `scripts/smoke_deps.py`, which invokes each
# dependency THROUGH ITS OWN CLIENT and hands the result to the real parser — because a probe with
# the endpoint typed into it tests a URL nothing calls. That is not hypothetical: the first version
# of this file was that script, and it reported a 404 for a working dependency because it said
# `main/` where the client says `master/`.
set -euo pipefail
cd "$(dirname "$0")/.."
exec "$(command -v .venv/bin/python || command -v python3)" scripts/smoke_deps.py "$@"
