# The serving image (D-116), and its `hosted` stage for Fly.io (D-185, M19-W5). K.10: this file is a
# cross-team contract surface, and `.github/CODEOWNERS` marks it as such; the owner reviews each change.
#
# Shape follows D-116: one read-only process, one SQLite file, no managed datastore, and no
# ingestion on the serving host — the network-fetching code and the untrusted-producer boundary
# W-005 guards stay off the public surface entirely.

# #141: the base by digest (read 2026-10-07), so a rebuild takes this base and its pip, the tool that
# checks the hashes. To move it, read the index digest of the tag and replace both lines:
#   docker buildx imagetools inspect python:3.11-slim   (the "Digest:" line)
FROM python:3.11-slim@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce AS build
WORKDIR /app
COPY pyproject.toml ./
COPY requirements/serve.lock requirements/build.lock ./requirements/
COPY src ./src
# M18-W6 (D-177): the locked versions, hash-checked (#35), and no refresh dependencies, pyarrow among
# them (#26): the serving image runs no refresh (D-116, D-154). The locked build backend goes into
# this stage only; the project is then built with it, with nothing resolved or fetched.
RUN pip install --no-cache-dir --require-hashes -r requirements/build.lock \
 && pip install --no-cache-dir --prefix=/install --require-hashes -r requirements/serve.lock \
 && pip install --no-cache-dir --prefix=/install --no-deps --no-build-isolation .

FROM python:3.11-slim@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce AS serve
# L.7: the build stamp is what makes `curl /health | jq .build` answer "which code is live", and
# REQ-API-006 refuses to boot production without it. Passed at build time, never baked in source.
ARG APP_BUILD=unknown
ENV APP_BUILD=${APP_BUILD}

# REQ-API-006: no default. An unset value is a fail-closed 503, because a working-directory-relative
# default serves the WRONG DATABASE with a 200 rather than refusing to start.
ENV MODEL_RANKING_DB=/data/advisor.db
ENV APP_ENV=production
# #94: where the command below binds, told to the startup check, which reads it from here. Beyond
# loopback it refuses to BOOT with no MODEL_RANKING_ALLOWED_HOSTS (D-171): the deployment names the
# Host it answers to (fly.toml), and an image run with none fails at once instead of answering 400.
ENV MODEL_RANKING_BIND=0.0.0.0

# No cross-origin access unless an explicit allowlist is supplied. A wildcard is refused outright
# (D-115's surface serves public data and needs none), so this is left unset rather than permissive.
# ENV MODEL_RANKING_CORS_ORIGINS=https://your-client.example

COPY --from=build /install /usr/local
WORKDIR /app

# Runs as a non-root user: the process reads one file and writes nothing, so it needs no more.
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8080
# In this stage the evidence database is a MOUNTED artifact, rebuilt on the owner's machine and
# shipped (D-116); the `hosted` stage below carries one inside the image instead.
VOLUME ["/data"]

# With a Host list set, the engine answers only to those names, loopback included (D-171), so the
# check asks for the first of them.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,sys,urllib.request as u; h=(os.environ.get('MODEL_RANKING_ALLOWED_HOSTS') or '127.0.0.1').split(',')[0].strip(); sys.exit(0 if u.urlopen(u.Request('http://127.0.0.1:8080/health', headers={'Host': h})).status==200 else 1)"

CMD ["uvicorn", "app.adapter.main:app", "--host", "0.0.0.0", "--port", "8080"]

# M19-W5: the hosted engine, the stage `fly.toml` builds. It carries the public artifact, which
# `scripts/deploy_hosted_engine.sh` builds on the owner's Mac (ingestion never runs here, D-116), so a
# deploy is one immutable pair of code and data and a rollback restores both. Not under /data: that
# is the stage above's VOLUME, and a file copied under a declared volume is not kept.
FROM serve AS hosted
COPY build/hosted/advisor.db /srv/advisor.db
ENV MODEL_RANKING_DB=/srv/advisor.db
