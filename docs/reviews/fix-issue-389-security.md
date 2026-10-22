---
record_type: review
id: fix-issue-389-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-21
---
# Security Review — fix-issue-389

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), light mode, run queue-1021. `make review-need` routed this change to `security` for four reasons: gate or control code changed, the sensitive path `scripts/deploy_hosted_engine.sh`, a `json.load`, and a policy edit in `scripts/nightly_hosted.sh`.
**Independent:** yes. I wrote none of this range's code, tests or records. #389 is my own round-1 finding M3 on #387 (`docs/reviews/fix-issue-387-security.md`); I did not write the fix.
**Date:** 2026-10-21
**Release range:** `0837789b200c65186c3b97c7d5865b45f8f52187..93d9ee274cde796fd062381fea14a1357ea7d7bc`, the merge-base with `integration/run-queue-1021`, which already carries #388. Two commits: red `9b53587` and fix `93d9ee2`. Branch `fix/issue-389-token-apart`, draft PR #395.
**Reviewed head:** 93d9ee274cde796fd062381fea14a1357ea7d7bc
**Risk tier:** MEDIUM. This is deploy and gate code beside a deploy credential. The brief declares no HIGH paths, and no auth, PII, payment or migration path is touched, so no senior review is triggered.

I reviewed it in a detached worktree at the head, with its own venv (`make install`).
- **Tests:** `tests/unit/test_nightly_hosted.py` gives 40 passed.
- **Mutants:** four, each restored from a copy afterwards; `git status` was clean.
- **Probes:** in throwaway repositories with stand-ins for `fly` and `curl`.
- **Network:** nothing contacted Fly.io and no workflow ran. The only network call was a read-only fetch of `actions/download-artifact`'s bundle at the pinned SHA, to read how it extracts.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MINOR 2 · NIT 1 · risks queued 2. **M1 is not a security hole: it fails closed. But as shipped, every night would be refused, so fix it before merge.**

**#389's property holds: the token's step opens no database and parses nothing the refresh produced, beyond one line of text it compares exactly.** In `--ship` (`scripts/deploy_hosted_engine.sh:73-84`), the token step touches the following:
- **The copy:** read only as bytes, to hash with `hashlib` (`:77`). The test `tests/unit/test_nightly_hosted.py:194` ships a file that is not SQLite at all, and checks that no interpreter call names `sqlite` or `app.workflows`.
- **The stamp:** `head -n 1 | tr -d '[:space:]'` (`:76`) takes the first line with all whitespace removed. It is compared with `WANT` exactly, and `WANT` is built only from `git` output, hex and literals (`:78`).
  - A multi-line stamp contributes only its first line.
  - Embedded whitespace cannot help a stamp match.
  - Whatever passes contains only `[a-z0-9-]`, and it reaches `fly deploy --build-arg "APP_BUILD=$BUILD"` quoted.
  - A refused stamp is echoed after the `[deploy] refused:` prefix. The whitespace is gone, so no newline remains, and the echo cannot start a workflow-command line (`::...`).
- **`fly.toml`:** comes from the checkout of `main` (trusted), read with `tomllib`.
- **`/health`'s JSON:** comes from our own app, read with Python's memory-safe `json`. This was already there before #389 (`:63-69`).
- **The gate:** `deploy_gate.py` and `brief_fields.py` import only the standard library. A probe ran the ship step with a bare `venv --without-pip` interpreter: exit 0, and `fly` was called.
- **The image's `hosted` stage only `COPY`s the file** (`Dockerfile:65-67`), so nothing parses it on Fly's builder either.

**`hosted-public` cannot be poisoned across runs.**
- `download-artifact` by name, with no `run-id`, reads the current run's artifact (`scripts/ci/nightly-hosted.yml:129-132`), and only this run's `refresh` job uploads that name (`:99-106`).
- The pinned `download-artifact` (`9000827c`, v8.0.2) extracts with unzip-stream's `Extract`. That writes every entry through `fs.createWriteStream`, so a symlink entry lands as a regular file. `build/` does not exist in a fresh checkout, so there is nothing to follow.
- Within the run, the producer is the `refresh` job, the same trust as before (see M2).

**Mutants, each failing tests:**
- `WANT="$BUILD"`, no check at all: 6 tests fail.
- Taking `from-` from the stamp itself: 2 tests fail (`:232`).
- Dropping the token refusal from `prepare`: 1 test fails (`:186`).
- `if false` on the comparison: 6 tests fail.

**Other properties that hold:**
- `prepare` refuses all three tokens (`scripts/nightly_hosted.sh:35-41`) and strips `DEPLOY_ACCEPT_DATA_FROM` and `MODEL_RANKING_REPO` (`:45`, `:87`).
- The dry run's data-builder refusal still runs, now in the token-free job.
- `--ship` additionally refuses a stamp `from-` anything but HEAD, so it is stricter than the dry run, which an owner's `DEPLOY_ACCEPT_DATA_FROM` can loosen.
- **The owner's manual path (no argument) lost nothing:**
  - it still derives from `SERVED` with the builder check;
  - it still runs `fly deploy` and the health loop;
  - it now also writes `build/hosted/build.txt` (`:141`), which is harmless.
- `--if-new` is gone, and nothing outside the reviews and the process log names it.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/deploy_hosted_engine.sh:78` and `:140`, with `scripts/ci/nightly-hosted.yml:122`: the two jobs abbreviate HEAD differently, so `--ship` refuses every night's stamp. This fails closed and is not a security hole.
  - **The cause.** Both lines use `git rev-parse --short HEAD`, whose length git scales with the number of objects in the clone. The stamp is written in the `refresh` job, a depth-1 checkout. It is checked in the `deploy` job, a `fetch-depth: 0` checkout.
  - **Measured on this repository.** A `--depth 1` clone of `main` prints `3eb4189`, and a full clone prints `3eb4189a`. So the deploy job's `WANT` is `release-3eb4189a-...` against a stamp of `release-3eb4189-...`.
  - **Reproduced.** In `probe_bare_ship.py`, `git config core.abbrev 9` in the shipping clone gives `refused: the prepared stamp 'release-7e242d8-data-4e79611e-from-7e242d8' is not release-7e242d81b-data-4e79611e-from-7e242d8`, and `fly` is not called.
  - **Fix.** Use one fixed length in both places: `HEAD_SHORT` (7, `:60`) at `:78` and `:140`, as the refresh's `APP_BUILD` already does with `--short=7`. Add a test that sets `core.abbrev` higher in the scratch repo between `prepare` and `deploy` and expects a deploy.
- **M2** `scripts/deploy_hosted_engine.sh:73-84`, and D-217's "Amended before merge" line (`docs/decisions.md:5787`): `--ship` checks that the stamp agrees with itself, not where the copy came from. The ADR says it "checks it against the stamp (this commit, data this release built)". In fact `from-<HEAD>` and the digest are the stamp writer's own claims, and the writer also wrote the copy.
  - **In CI.** The writer is the `refresh` job, so a compromised parser ships whatever data it likes. This is not a regression: before #389, the deploy derived the public copy from a state the same parser controlled.
  - **Locally, this is new.** `scripts/deploy_hosted_engine.sh --ship` (judged as a declared deploy, so the gate runs) ships whatever sits in `build/hosted/`. That directory is gitignored, so the gate cannot see it. The caller only has to write a self-consistent `build.txt`, which skips:
    - the `LEFT_OUT` strip (`app.workflows.public`);
    - the builder check.

    It needs a deliberate caller, and D-185 clause 5 already bars an agent from deploying.
  - **Remedy.**
    - Word the ADR line and the script header as "a consistency check of the prepared pair; the pair's provenance is the token-free `refresh` job".
    - Say in the header that the owner's manual deploy is the no-argument form.
    - Optionally, refuse `--ship` when `GITHUB_ACTIONS` is unset. That is a tripwire against a mistaken local use, not a control.

### NIT
- **N1** `scripts/deploy_hosted_engine.sh:77`: the stamp carries 8 hex characters (32 bits) of the copy's sha256. That is not a weakness today. An attacker who controls the copy also writes the stamp, so a second preimage would gain nothing. And the `/health` skip at `:148` only skips a deploy. If a later change ever lets the copy and the stamp come from different writers, put the full sha256 on a second line of `build.txt` and check that. The 8-character label can stay in the build name.

## Gates passed
- [x] Secret scan green (`make secrets` on 93d9ee2: gitleaks `no leaks found`, the coordinator's gate line)
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found`
- [x] `make slopsquat` green: `20 declared dependency(ies), 0 suspect`. No new import: the test's `hashlib` is the standard library.
- [x] Default-deny preserved for new external surfaces. The new `hosted-public` artifact holds only the public copy the image already serves, kept for 1 day. The deploy job keeps `fly-production` and the `main` condition.
- [x] Permission-matrix not violated: no `.github/`, `.claude/` or `.githooks/` edit (the workflow is the proposal under `scripts/ci/`), and no destructive operation in the range.
- [x] Prompt-injection hygiene: nothing fetched is interpreted, and no `${{ github.event.* }}` reaches a `run:`.
- [ ] Auth/PII checks + human review trigger: n/a (not HIGH)
- [x] SAST: conformance `33 test(s) ... 0 failing` (the coordinator's gate line). Shellcheck and bandit are not installed. The new shell has no unquoted expansion of the stamp.

## Acceptance criteria evidence
- #389 "the step that holds the token never opens the refresh's database" → `tests/unit/test_nightly_hosted.py:194` (a non-SQLite file ships, and no `sqlite`/`app.workflows` call is made), plus the shape test that the deploy job takes no `hosted-state` and installs no `requirements/` (`:437-438`).
- The public copy is derived in the job that holds no token → `:186` (`prepare` refuses `FLY_API_TOKEN`), and the shape test that `prepare` follows `refresh` in the `refresh` job, with no `env:` on either step (`:375`).
- A copy or stamp that does not match is refused → `:219` (a byte appended to the copy) and `:232` (other code, other data, `from-0000000`, `from-unknown`, empty).
- The deploy still runs the gate and checks `/health` → `:174` (a full night through `prepare` and `deploy`).
- Verifiable only once the owner applies the workflow: the dry run's clean-tree and `git fetch` checks on a real runner, and the download into `build/hosted`. M1 shows a case that the scratch tests, all in one clone, cannot see.

## Risks queued
- **R1** `scripts/ci/nightly-hosted.yml:97`: the refresh job now runs the deploy script's dry run. That dry run fetches `origin/main` anonymously and requires a clean tree and `HEAD == origin/main`. If `main` moves during the night, or the cycle leaves anything untracked in the tree, `prepare` fails after `hosted-state` is uploaded. So the state is kept and nothing deploys, which fails closed. Watch the first real nights.
- **R2** The scratch tests run every step in one clone, so a difference between the two jobs' checkouts (depth, abbreviation, tags) is invisible to them. That is how M1 got through. Have one test run `prepare` and `deploy` in two different clones of one origin: a shallow one and a full one.
