# PROPOSAL — M6-W4, not yet adopted. K.10: this file is a cross-team contract surface, and
# `.github/CODEOWNERS` marks it as such. It ships in this wave for the owner's review, per the
# signed plan's Trap 3, and is not treated as settled until he says so.
#
# Shape follows D-116: one read-only process, one SQLite file, no managed datastore, and no
# ingestion on the serving host — the network-fetching code and the untrusted-producer boundary
# W-005 guards stay off the public surface entirely.

FROM python:3.11-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim
# L.7: the build stamp is what makes `curl /health | jq .build` answer "which code is live", and
# REQ-API-006 refuses to boot production without it. Passed at build time, never baked in source.
ARG APP_BUILD=unknown
ENV APP_BUILD=${APP_BUILD}

# REQ-API-006: no default. An unset value is a fail-closed 503, because a working-directory-relative
# default serves the WRONG DATABASE with a 200 rather than refusing to start.
ENV MODEL_RANKING_DB=/data/advisor.db
ENV APP_ENV=production

# No cross-origin access unless an explicit allowlist is supplied. A wildcard is refused outright
# (D-115's surface serves public data and needs none), so this is left unset rather than permissive.
# ENV MODEL_RANKING_CORS_ORIGINS=https://your-client.example

COPY --from=build /install /usr/local
WORKDIR /app

# Runs as a non-root user: the process reads one file and writes nothing, so it needs no more.
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8080
# The evidence database is a MOUNTED ARTIFACT, not part of the image — it is rebuilt on the owner's
# machine and shipped. Baking it in would make every data refresh an image rebuild and would put
# a stale answer inside a container that claims a fresh build stamp.
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health').status==200 else 1)"

CMD ["uvicorn", "app.adapter.main:app", "--host", "0.0.0.0", "--port", "8080"]
