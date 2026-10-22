---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-23
---
# Security Review — release v0.1.0 (Stage 5.1, delta since the last release verdict)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`), Stage 5.1, light mode, dispatched by `/going-live` for release v0.1.0
**Independent:** yes. I wrote none of this range's code, tests, records or earlier reviews.
**Date:** 2026-10-23
**Release range:** `958458d0f2166dce4ddf4b530314231e618f7f0f..660af4b9b46dce2d769101da7ae4f80b6e6d3132` (310 commits). `958458d` is the reviewed head of the verdict this one replaces; `660af4b` is `release/v0.1.0`: main's tip `044a309` (#409), the release Tester's two test commits `3e227ae` and `471bd73`, and its verdict commit.
**Reviewed head:** 660af4b9b46dce2d769101da7ae4f80b6e6d3132
**Risk tier:** HIGH. The range touches the deploy gate (`scripts/deploy_gate.py`), both deploy scripts, the brief's `Deploy commands:`, the Bash guard and its pin (three owner patches), CI, the compiled client gate, the serving adapter (`/v1/categories` field, an error body), the app's on-device model session, and seven new or changed parsers of fetched input. The brief declares no HIGH path, so the §11 senior-review trigger does not fire on a path; no auth, PII, payment or migration code is in the range.
**Seat:** my own worktree `review/release-security-v0.1.0` at `660af4b`, its own `.venv` (`make install`, `make hooks`), a copy of the main clone's `advisor.db` in my scratch directory for the two loopback probes. Scratch clones and probes stayed outside the repository. I sent no request to the owner's launchd engine, to Fly or to any mutating GitHub endpoint.

> **This record replaces** the verdict of 2026-10-17 (`81af5ba..958458d`, PASS WITH FINDINGS, reviewed head `958458d`). Its text is kept in git: `git show 958458d:docs/reviews/release-security.md`.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 3 · NIT 0 · risks queued 3.

Shipped as it stands, nothing in the release is exploitable from outside, and nothing I found blocks the deploy. The engine still serves five GET routes and no mutating route. Its Host list, CORS allowlist, strict boot and generic errors behave as before; I probed them live on a loopback server at the head. The app reaches the network only through `EngineClient.swift`, and the compiled privacy gate passes in all four configurations. The new parsers fetch through the unchanged bounded fetch and its host lists. Every earlier security finding in the range has its fix and test at the head, or is open and filed. That includes #242's third BLOCKING, closed in code by #373 and #374.

The three MINORs are all fail-closed in effect, and two of them can be triggered only by an upstream host:
- **M1** concerns the deploy gate. Since v7.2 (#327, whose guard review the owner waived), the gate exempts a "DevFlow file, unchanged". The exemption trusts two inputs an agent can write without any guard refusal: a local tag, and an untracked marker. I forged both in a scratch clone, and the gate then passed an unreviewed change to `scripts/deploy_hosted_engine.sh`. This release's deploy does not depend on the exemption, because this review covers every file it exempts. CI never applies it.
- **M2.** The queue-1021 review's M2 is fixed only in part. Datacurve's and LiveBench's parsers still let a non-`SourceError` out, so one bad optional file aborts the whole night's build.
- **M3.** SimpleBench's board regex is quadratic. One upstream file can stall the night until the cycle is killed.

## How this review was split (what earlier verdicts cover)

| Part of the range | Verdict of record | What I did here |
|---|---|---|
| `958458d..3f9306f`, DevFlow v7.2 (#327): guard `973e408a→3aea0170`, `settings.json`, `issue-agent.yml`, `.githooks/post-rewrite`, the `pre-push` gate stamp, `deploy_gate.py` (+130), `review_need.py`, `net_cache.py`, `gate_stamp.py`, `.mcp.json` removed | **none: the owner waived the guard-change review** (`2ee7867`, one `docs/control-events.csv` row) | Read in full: deploy gate, hooks, workflow, settings, new scripts. Guard: no must-block case was removed from `conformance/test-bash-guard.py` or `tests/unit/test_bash_guard_bounds.py` across the range, only added, and both corpora pass at the head. **M1 found here.** |
| run bug-night (`0bb0ea4..c41bea8`): #256, #287, #305, #314, #317–#320, #326, #341, #344 | `fix-issue-319-security.md` (#319 policy scripts only) | Product parts read in full: `StandingsStore.swift` (#314: size refused before read), `Router.swift`, `terminalbench.py` (#326: the old N1 `%2e%2e` path is refused now; probed `False`). Tooling read for sinks and subprocesses. |
| bug-night owner bundle (`f9d9a8f`, #383) | `run-bug-night-owner-bundle-security.md` (round 4: patch `e3755901…`, guard `d255f6cb`) | I applied `build/owner-bug-night.patch` (sha256 matches round 4) to `7fe3ba4`. `ci.yml`, `contract-tests.yml`, `issue-agent.yml` and `commit-msg` are byte-identical to what merged. The merged guard (`da39a4d0`) differs from the reviewed one only in two message strings and its pin. It is superseded at the head anyway. |
| run night-351 (#357): #352, #358, #360 | `enhancement-issue-351-apple-intelligence-security.md` (`2be1474`), `integration-run-night-351-security.md` (`3a3ef39`) | `3a3ef39..14ed9cf` is docs only, so I lean on both. I re-read the on-device model's schema boundary (`Router.swift`, `ModelRouter.session`, `anyOf` over the served ids). |
| #361, #363, #367, #328, golden rules (#350) | none | Read. #367 moves the locks to `certifi 2026.10.19`, which is security-positive. The rest is Router word lists, the client gate's SDK path, tests and docs. |
| #242 + #373–#376 (`integration/merge-1021`, #385) | `enhancement-issue-242-allowlists-security.md`: **BLOCKING at `fae9d85`, third round, loop ended** | Its round-3 B1 forms and M2 forms are planted by #373/#374 (`tests/unit/test_client_decl_gate.py:1385-1420`, red first in `cd59b2e` and `35db3f6`), and they pass at the head. `make client-decls` passes. B1 is closed in code, not by a security re-verification: I record it here as closed. #376 only removes copies (`public.py` `RETIRED_COPIES`). |
| #265 Datacurve (#386) | none found | Read in full. **M2 found here.** |
| run queue-1021 (#394): #378, #387, #389, #390–#392, #397–#400, #405 | `fix-issue-387-security.md` (`e4b8459`), `fix-issue-389-security.md` (`93d9ee2`), `integration-run-queue-1021-security.md` (`fc02b04`) | `fc02b04..976b093` (the fixes of that review's M1–M5, N1 and N2, and #405) **had no security re-read: read here in full**. M1, M3, M4 and M5 are fixed. M3 mutant: deleting the two expat refusals fails `tests/unit/test_osworld.py:257` (2 failed), and the file was restored byte-identical. M2 is **incomplete**: this review's M2. |
| queue-1021 owner bundle (#409) | `run-queue-1021-owner-bundle-security.md` (round 4: `e837548` + patch `d46a465f…`, guard `728db666`) | `build/owner-run-queue-1021.patch` (sha256 matches) applied to `e837548` equals the head's `.claude/`, `.githooks/` and `.github/` **byte for byte** (`diff -r` on all three trees). The guard pin at the head is `728db666`. |
| Tester commits `3e227ae`, `471bd73`, `660af4b` | — | Tests and the Tester record only. |

Earlier open items I did not re-file:
- **#401** stays MINOR. A workflow started by curl or an extension still reaches `nightly_hosted.sh deploy`, which runs `deploy_gate.py --check` itself on the runner (`scripts/nightly_hosted.sh:80-84`). So the gap is the guard's early refusal, not the deploy.
- **#403** (a price shown on a media surface) and **#396** (client-decls G-2 rebuilds) are product and privacy-gate residuals. This read does not change them.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **M1** `scripts/deploy_gate.py:203-230` (`shipped_unchanged`) with `:135-136` (`.gp/installed` is a record). The deploy gate's "DevFlow file, unchanged" exemption (v7.2, #327) fails open on inputs an agent can write. A path under `scripts/`, `.claude/`, `.githooks/`, `conformance/`, `.agents/` or `.github/`, or the `Makefile`, that is outside the four-file `SAFETY_SURFACE` is not counted as code when its bytes equal `refs/tags/<gp_version>:<path>`. `gp_version` is read from `.gp/installed`, which is untracked and gitignored (`.gitignore:71`).
  - **The inputs are agent-writable.** The Bash guard allows `git tag -f v7.2 HEAD`, `git tag v7.3 HEAD`, `git update-ref refs/tags/v7.2 HEAD` and `echo "gp_version: v7.3" > .gp/installed`: all four judged exit 0, nothing run. The editor guard does not cover `.gp/`.
  - **Probe** (scratch clone of the head, verdicts pointed at its HEAD):
    1. Append one line to `scripts/deploy_hosted_engine.sh` and commit it. `deploy_gate.py --check` gives `FAIL: 1 file(s) changed since the reviewed head … scripts/deploy_hosted_engine.sh`.
    2. Run `git tag v7.99 HEAD` and write `gp_version: v7.99` to `.gp/installed`. The check now gives `deploy-check PASS … no code changed since`, and `deploy_gate.py "scripts/deploy_hosted_engine.sh --ship"` exits 0.
  - **Without forging.** A change that reverts a project hardening back to DevFlow's bytes is also not code. 34 project-customised files at the head have a v7.2 counterpart, among them `.github/workflows/ci.yml` (hashed installs, #392), `scripts/secrets_scan.py`, `scripts/slopsquat_check.py` and `scripts/review_need.py`.
  - **Not exploitable in this release.** The local `v7.2` tag is the GitHub-signed merge `49f6634` ("Merge pull request #22 from SADCAIVibe/release/v7.2"). The 33 files it exempts in this range are process files I read as part of this range. CI's deploy job has no `.gp/installed`, so the exemption never applies there. An agent cannot run a deploy (`.claude/hooks/bash_guard.py:140-142`, D-185).
  - **Why it matters.** The exposure is the owner's own `make deploy-check` and hand deploys, after an agent session. That is the class the guard already defends for `origin/main` and the hooks path ("the deploy gate reads its base", #318).
  - **Remedy.** Do not read the version from an untracked file. Pin the DevFlow commit in a tracked record, and accept a tag only when it resolves to that pinned commit (`git rev-parse refs/tags/<v>^{commit}`). Add the product's deploy scripts (`scripts/deploy_hosted_engine.sh`, `scripts/nightly_hosted.sh`, `scripts/ci/`) to `SAFETY_SURFACE`. Ask the owner to make the guard refuse creating or moving `refs/tags/v*`. Add a test that forges a tag and a marker and expects `FAIL`.
  - **Who changes it.** `deploy_gate.py` is gate-definition code (AGENTS.md §3, Escalate NOW), and the guard part is the owner's. **New issue.**
- **M2** `src/app/clients/datacurve.py:54-58` and `src/app/clients/livebench.py:51-56,86-91`: a bad optional file still aborts the whole night. This is the queue-1021 integration review's M2, fixed only in part.
  - **The catches are too narrow.** `json.loads` raises `RecursionError` on deep nesting, and a plain `ValueError` (not a `JSONDecodeError`) on an integer of more than 4,300 digits. Datacurve catches only `JSONDecodeError`. LiveBench catches `JSONDecodeError` and `RecursionError`, not the `ValueError`.
  - **Through `build._ingest_sources`** (the shape of `tests/unit/test_livebench.py:218`, Datacurve first, SimpleBench after it): both the deep JSON and a 4,400-digit `pass_at_1` gave `BUILD ABORTED: RecursionError` / `ValueError`, and SimpleBench was never read.
  - **Directly:** `parse_livebench` and `LiveBenchClient.fetch_raw` both let `ValueError` out on a 4,400-digit number.
  - **The rule this breaks.** `build.py:669` catches only `SourceError` and `BuildError`. So this breaks D-121, and the source's own comment (`sources.py:263-266`: "it never fails another source's night").
  - **Who can trigger it.** The upstream host (`deepswe.datacurve.ai`, LiveBench's), or whoever controls it.
  - **The effect.** No night publishes until the file changes. Carry-forward is skipped for every source. Serving and the data's integrity are untouched, and it fails closed: that makes it MINOR.
  - **The same class, pre-existing:** `arc_prize.py:58-59`, `models_dev.py:65-66`, `litellm.py:66-67`, `terminalbench.py:51-52,137-138`.
  - **Remedy.** One helper in `clients/protocols.py`: `loads_source(text, name)` turns `ValueError` (the parent of `JSONDecodeError`) and `RecursionError` into `SourceError`. Use it at every client's `json.loads`. Add one test per class through `_ingest_sources`. **New issue.**
- **M3** `src/app/clients/simplebench.py:29` (`_BOARD`, used at `:63`): the board regex `\[(?P<body>.*?)\n\s*\];` with `DOTALL` is quadratic in a body with no closing `];`. At each newline, `\s*` runs over every following whitespace character, newlines included, before it fails.
  - **Measured at the head:** 10k newlines 0.13 s · 20k 0.51 s · 40k 2.0 s · 100k 12.6 s. Extrapolated: about 20 minutes per MB, and days at the 32 MB fetch cap (`protocols.py:45`).
  - **The effect.** The parse runs after the fetch's deadline, so no download bound applies. The cycle ends only at the 27-minute alarm (`refresh.py:103`) or the engine's 30-minute kill (`nightly.py:76`). On the runner, it ends at the job's 45-minute timeout. The whole night is lost, every source with it, and nothing deploys: fail closed.
  - **Who can trigger it.** `simple-bench.com`, or whoever controls it.
  - **Remedy.** End the body at `\n[ \t]*\];`: a horizontal-only whitespace class cannot cross the newlines, so the scan stays linear. Or find the end with `str.find` after the anchor. Add a timing-bounded test with about 200k newlines. **New issue** (it may share M2's).

### PASS — what I checked and found sound
- **Serving surface, live on loopback** (`APP_ENV=production`, random port, stopped after):
  - `POST`, `PUT`, `DELETE` and `PATCH` on `/v1/recommendations` each return 405. `/docs`, `/redoc` and `/openapi.json` return 404.
  - With `MODEL_RANKING_ALLOWED_HOSTS=model-ranking.fly.dev`, `Host: evil.example` returns 400 and the listed host returns 200.
  - With `MODEL_RANKING_CORS_ORIGINS=https://ok.example`, the listed origin gets `access-control-allow-origin` and no `allow-credentials`; another origin gets no CORS header.
  - The new unknown-task error reflects at most a truncated echo and names `/v1/categories` (`main.py:1637-1643`).
- **Dependencies.** No new third-party package. The locks change versions only: `fastapi 0.156.3`, `starlette 1.9.0`, `pydantic 2.14.1`, `certifi 2026.10.19` (#367), `pyarrow 26.0.0`, `setuptools 84.2.1`. The new parsers use the standard library only: OSWorld's workbook is read with `zipfile` and `expat`, with DTD and entity refusal (`osworld.py:140-142`).
- **Dormant credential path.** `bounded_get`'s new `headers=` (`protocols.py:118,193`, D-216) has no caller in `src/`. No token is read or sent: grepping `src/` for `HF_TOKEN` or `Authorization` finds only the docstring.
- **Deploy scripts.**
  - `deploy_hosted_engine.sh` refuses a dirty tree, a HEAD that is not `origin/main`, a call from another tree (`:57-64`, the M4 fix), and git's place variables (`:37`, the M5 fix).
  - `--ship` checks the stamp against this commit and the copy's digest.
  - `nightly_hosted.sh` refuses a token beside the parsers (`:38-45`).
- **The nightly proposal** (`scripts/ci/nightly-hosted.yml`). The token-holding deploy job needs the `fly-production` environment and `main`. It installs nothing and runs the gate first. The refresh job holds no secret. All actions are pinned to commit SHAs.
- **`issue-agent.yml`.** Switched off, `workflow_dispatch` only. Inputs reach the prompt, never a `run:` shell. Least-privilege token.
- **`ci.yml`.** `pull_request` (not `_target`), `contents: read`, PR SHAs passed through `env:`, actions pinned.
- **Guard and settings.** The v7.2 settings add a `PowerShell` matcher that blocks, two read-only `make` allows, and remove the `.mcp.json` GitHub MCP server: a tightening. The gate stamp states its own limits (`scripts/gate_stamp.py:22-26`), and CI re-runs every leg.
- **App.**
  - The kept answers file is size-checked before it is read (`StandingsStore.swift` `contents(atMost:)`, #314).
  - Prices are optional, never zero, on surfaces ranked on quality only (`Models.swift`, `Detail.swift`). The phone words them; the engine sends no sentence.
  - The model router uses greedy decoding with the `anyOf` schema boundary unchanged (INV-69).
  - No `openURL`, logging, sharing or new file sink in the range's Swift additions.

## Baseline walk (`main:docs/security-baseline.md`, against the head)

| # | Item | At the head | Evidence |
|---|---|---|---|
| 1 | No plaintext creds / default admin | No credential exists. gitleaks is clean over the tree and over the range's 254 non-merge commits. | `make secrets`: `no leaks found`; `gitleaks git --log-opts=958458d..660af4b`: `no leaks found` |
| 2 | Server-side authz on mutating routes | No mutating route: five GETs (`main.py:1381,1470,1539,1582,1626`); docs routes off (`:773-775`) | `tests/unit/test_api_v1.py:509` (INV-30); live probe above |
| 3 | CORS allowlist, never `*` + credentials | Off unless set; `*` refused at boot (`main.py:404`); `allow_credentials=False`, GET only (`:809-810`) | `tests/unit/test_api_config.py:35,109,120` (INV-31); live probe |
| 4 | Validate config at startup | Unchanged in the range (`main.py:635-729`) | `tests/unit/test_api_config.py` green in my run |
| 5 | Creds/PII encrypted at rest | The engine stores no PII. The app keeps the typed question only in the gap register (INV-67). The range adds no store. | `make client-decls` PASS (4 configurations) |
| 6 | Generic client errors | 500 handler unchanged (`main.py:868`) | `tests/unit/test_stage40_minors.py`, INV-34 |
| — | Host list | 400 off the list (live) | `tests/unit/test_engine_host.py:46` (INV-26) |
| — | Fail direction | The limiter (fairness) fails open, unchanged (`main.py:815`). Host, CORS, boot and both deploy scripts fail closed. **The deploy gate's exemption fails open on forged inputs (M1).** | INV-88; M1 probe |
| — | Built ≠ wired | Datacurve, LiveBench, METR, OSWorld and SimpleBench are wired in `sources.py` (`REMOTE_SOURCES`). The nightly deploy runs the gate in its own step. | `tests/unit/test_livebench.py:218` (through `_ingest_sources`) |

`docs/security-invariants.md` changes in the range: INV-62/63/64/66/67/76/89 and G-1/G-2/G-11/G-12/G-13 are reworded for #242's allowlists, and INV-69 is widened to D-213's declared values. No row loses a citing test.

## Gates passed
- [x] Secret scan green (`make secrets` at the head; gitleaks over `958458d..660af4b`: 254 commits, no leaks)
- [x] `make deps` (pip-audit over all four locks): `No known vulnerabilities found`
- [x] `make slopsquat`: `PASS: 20 declared dependency(ies), 0 suspect`; no new import of a third-party package
- [x] Default-deny preserved for new external surfaces: no new route; the only new `/v1/categories` field is `priced` (static)
- [x] Permission matrix not violated: no destructive op in the range's code; the owner directories at the head are exactly the reviewed owner patch
- [x] Prompt-injection hygiene: fetched text is parsed as data, never followed. The on-device model answers through a closed schema (INV-69). The issue agent is off and gets no shell interpolation.
- [x] Auth/PII checks: no auth, PII, payment or migration path in the range, and the brief declares no HIGH path, so the §11 trigger does not fire
- [x] SAST: bandit is not installed; I ran its rule set through ruff (`ruff --isolated --select S`) over every changed `src/` and `scripts/` Python file. 36 findings, all S603/S607: `git` with literal argument vectors.
- [x] Tests: `pytest -n auto` under `scripts/offline.sb`: 4423 passed, 89 skipped (the `advisor.db`-reading tests are skipped, since `MODEL_RANKING_REQUIRE_ARTIFACT` was off; the Tester ran them). `make conformance`: 33 passed. `make client-decls`: PASS, 4 configurations. I did not re-run `make swift-test`; the gate ran it on `044a309`, and the range after it touches no Swift.

## Acceptance criteria evidence
- REQ-API-001 / INV-30 (read-only `/v1`) → `src/app/adapter/main.py:1381-1626`; `tests/unit/test_api_v1.py:509`
- INV-31 (CORS) → `src/app/adapter/main.py:404,809-810`; `tests/unit/test_api_config.py:35,120`
- INV-26 (Host list) → `fly.toml:26`; `tests/unit/test_engine_host.py:46`
- D-121 (an optional source never stops the build), as fixed for the queue-1021 M2 → `src/app/clients/livebench.py:96-104`, `src/app/clients/osworld.py:159-171`; `tests/unit/test_livebench.py:218`. Its remainder is M2.
- The queue-1021 M1 (OSWorld output cap) → `src/app/clients/osworld.py:216-228`; `tests/unit/test_osworld.py:152`
- The queue-1021 M3 (DTD and entity refusal) → `src/app/clients/osworld.py:140-142`; `tests/unit/test_osworld.py:257` (mutant killed)
- The queue-1021 M4/M5 (deploy from its own checkout, no place variables) → `scripts/deploy_hosted_engine.sh:37,57-64`; `tests/unit/test_deploy_hosted.py:90,108`, `tests/unit/test_nightly_hosted.py:75`
- #326 (raw-path check) → `src/app/clients/terminalbench.py:84-86`; `tests/unit/test_terminalbench_4.py:155-156`
- #314 (size before read) → `ios/ModelRanking/Engine/StandingsStore.swift` `contents(atMost:)`; `tests/unit/test_answers_size_before_read.py`
- #242 B1/M2 closure (#373/#374) → `scripts/client_decl_gate.py`; `tests/unit/test_client_decl_gate.py:1385-1420`
- D-217 clause 2 (no token beside the parsers) → `scripts/nightly_hosted.sh:38-45`; `tests/unit/test_nightly_hosted.py`

## Risks queued
- **R1** `src/app/adapter/main.py:815` (the limiter) still trusts `Fly-Client-IP`, checked only by the runbook's manual check after a deploy (M20 closure S5; INV-88 "Partial"). Carried: run that check on this release's first deploy.
- **R2** When the owner installs `scripts/ci/nightly-hosted.yml`, the hosted deploy runs unattended every night. It is held by `deploy_gate.py --check` on the runner, and by the `fly-production` environment's branch rule, which is a GitHub setting this seat cannot see (unverified). Confirm that environment allows `main` only before the first scheduled night.
- **R3** Open and filed, context only, not re-filed: #401 (the guard does not see a curl, extension or action-started workflow; the deploy step still gates itself), #403, #396, #371, #323, #309.

## What I ran
`git worktree add … review/release-security-v0.1.0 660af4b`; `make install`; `make hooks`; `make secrets`; `make deps`; `make slopsquat`; `gitleaks git --log-opts=958458d..660af4b`; `pytest -n auto` (offline sandbox); `make conformance`; `make client-decls`; `ruff --isolated --select S`; `git apply` of both owner patches in scratch trees, and `diff -r` against the head; the deploy-gate forgery probe in a scratch clone; the four guard verdicts in M1 (judged, not run); the parser probes in M2 and M3 (in-process, no network); two `uvicorn` servers on random loopback ports, each stopped after its probe; one OSWorld mutant, restored byte-identical.
