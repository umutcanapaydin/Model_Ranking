---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.1.2
date: 2026-10-17
---
# Security Review — release (run golden-night head, Stage 5.1)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), Stage 5.1, light mode (D-206 clause 10)
**Independent:** yes. I wrote none of this range's code, tests, records or earlier reviews.
**Date:** 2026-10-17
**Release range:** `81af5ba..958458d` (589 commits). `81af5ba` is the head the previous release verdict reviewed; `958458d` is `integration/run-golden-night`.
**Reviewed head:** 958458d0f2166dce4ddf4b530314231e618f7f0f
**Risk tier:** HIGH. The range touches the serving surface (`src/app/adapter/main.py`: rate limiter, `/v1/categories` fields), the deploy surface (`fly.toml`, `scripts/deploy_hosted_engine.sh`, `scripts/deploy_gate.py`), the app's transport and engine address (`ios/Config/*`, `EngineClient.swift`), an on-device store (`answers.json`), and new parsers of untrusted input (#268).

> **This record replaces** the verdict of the first release, `3426ff3..81af5ba`, MINOR, dated 2026-10-07, which named no reviewed head. Its text is kept in git: `git show a16cbf4:docs/reviews/release-security.md` (first written in `8084c23`).

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 1 · NIT 1.

Shipped as it stands, the release has no exploitable defect that I could find. The engine still serves five GET routes and has no mutating route. It answers only to its Host list, keeps CORS off unless an allowlist is set, refuses to boot strict on a bad config, and returns generic errors. The hosted engine sets its rate limit, and the limiter fails open. The app reaches the hosted engine over HTTPS only: a Release build cannot be pointed anywhere else. The run product-night and golden-night changes that `review-need` routed to `none` are on-device classifiers, test-only changes, and two development scripts. None of them adds a network path, a file sink, a log of the typed question, or a code-execution path.

The one MINOR is about coverage, not a defect. #268 (licensed sources) added three ingestion parsers of untrusted input. `make review-need` routes that range to `security` today, but it merged with no security verdict. I reviewed it here (M1), and the only thing I found in it is the NIT (N1).

## How this review was split (what earlier verdicts cover)

| Part of the range | Verdict of record | Read here |
|---|---|---|
| M20 waves (`bd273bc...d005135`), M21 waves (`closure/m20...9cbba60`) | `m20-closure-security-review.md`, `m21-closure-security-review.md` (MINOR) | findings read; S5 carried as R1 |
| DevFlow v7.1 / v7.1.2 (process, guard) | `devflow-v7.1-upgrade-security*.md`, `devflow-v7.1.2-upgrade-security.md` | not redone |
| #288 (phone → hosted engine, kept answers) | `enhancement-issue-288-phone-security*.md` | re-walked as shipped (baseline below) |
| #289 golden set, product-night combination (`7bdb7c5..d953ca5`), #297 | `enhancement-issue-289-golden-security.md`, `integration-run-product-night-security.md`, `fix-issue-297-security.md` | not redone |
| **#298, #299, #300, #303, #310, #311, #312, #313, #316, #324, `9217c6c`, the golden-night stacking merges** | **none: reviewed here (Focus a)** | full diff |
| **#207 (`45d72e8..bd273bc`), #259, #263, #268, #270, #277** | **none found: no `*-security*.md` names these ranges** | full product diff (M1) |

## Findings

### BLOCKING
- none

### MINOR
- **M1** `src/app/clients/terminalbench.py:1-161`, `src/app/clients/models_dev.py:1-104`, `src/app/clients/arc_prize.py:1-96` (merge `9d2bbfc`, #268). Three new parsers of fetched input merged with no security verdict. On that range, `make review-need RANGE=51b2ee2..9d2bbfc` prints `new parser or fetch of untrusted input: httpx., json.loads` and `review-need: security`. The issue-265 records are code and Tester reviews only. **Not exploitable as shipped:** every fetch goes through the unchanged `fetch_bounded`, with its size bound and host list (`protocols.py:232`). Every field is type-checked and range-checked before it becomes a row: finite scores in 0–100, efforts from a closed set, positive prices only, and a 250-file ceiling. No input reaches a path, a shell or an evaluator. Ingestion runs only on the owner's Mac, and the serving image does not carry it (`nightly.py:106-117` refuses the switch on a strict engine). **Disposition:** covered by this review. No re-review needed. The routing gap is not a regression: the range merged before `review-need` ran in light mode on every change.

### NIT
- **N1** `src/app/clients/terminalbench.py:34,74-85`. `_in_submissions` matches the **decoded** `httpx.URL.path`, but the request sends the raw path. A `download_url` with `%2e%2e` as its ref segment passes the check. Measured here, offline:
  `_in_submissions(".../harbor-framework/terminal-bench/%2e%2e/leaderboard/submissions/a.json")` → `True`, with path `'/harbor-framework/terminal-bench/../leaderboard/submissions/a.json'` and `raw_path b'.../%2e%2e/...'`. The regex allows one segment there, so at most the request leaves the repository for the `harbor-framework` organisation, on the same host. Only whoever controls GitHub's listing for that repository could plant such a link, and they control its submissions anyway. So this is a NIT, but it is a gap in the #265 review's M2 fix. The test `tests/unit/test_terminalbench_4.py:154` plants only literal `..`. **Remedy:** refuse a `%` in `url.raw_path`, or match the regex against `raw_path.decode()`, and add `%2e%2e` to that parametrised test.

### PASS — the uncovered changes, read in full (Focus a)
- **#298, #299** (`Router.swift:677` `readsEnglish`, `:751` `turkishBesideModelNames`): `NLLanguageRecognizer` on the device, pure functions of the typed text. Nothing stored, sent or logged.
- **#300** (`Reading.swift:136,184`): adds instruction-to-the-app phrases (`"write nothing else"`, `"başka bir şey yazma"`) and `noMeaning`. These only add to the "not a search" signals. No signal was removed or weakened.
- **#303** (`Router.swift:427`), **#316** (example sentences), **#324** (`Router.swift:484,584`): word lists, plus bounded index arithmetic in `agentThatCodes`. `words.indices.contains` guards every index, and `(verb-3...verb-1)` is a valid closed range for every `verb >= 0`. No unbounded work.
- **#310**, **`9217c6c`**: test data and tests only. They contain no network call, environment read, secret or path. The `db01bdf` conflict was resolved by keeping #294's `disputed` mark, in test data. Every other golden-night merge (`9dd9a77`, `22c1429`, `7aa43ee`, `2fc953e`, `af99318`, `958458d`) is exactly the tree `git merge-tree` writes. `5b0acf9` differs only by adding the #297 security record.
- **#311** (`OfflineTestCase.swift:66`): INV-6 is strengthened. An `XCTestObservation` adds a teardown check. The INV-6 row gains two tests and loses none. What it still cannot see is filed as #309.
- **#312** (`check_records.py:1453`): L1 now skips only what git ignores **and** does not track (`--others --ignored`). When git fails, the skip set is empty, so the gate gets noisier, never quieter. L1 is not a security control.
- **#313** (`scripts/closing_keywords.py:62`): advisory only, not in `check`. It runs `git` with a literal argument vector and no shell, and fails closed (exit 2) on an empty or unreadable range.

### PASS — the other uncovered segments (part of M1's sweep)
- **#207** (`public.py:31`, `LEFT_OUT = {}`): the hosted artifact now carries every source, on the owner's ruling D-186. That is a licence matter, not an exposure: R2. Its Router keyword tier is on-device word matching.
- **#259** (`nightly.py`, `built_by_another`): a startup catch-up on the owner's Mac only. The hosted engine refuses the refresh switch (`nightly.py:114-116`).
- **#263** (credits): static publisher data. Links are selectable `Text`, and there is no `openURL` anywhere in `ios/ModelRanking`. `credits_for` raises on a missing credit, which gives a generic 500.
- **#270**, **#277**: registry rules, refresh reporting, licence notices. No new sink, route or fetch.

## Baseline walk (`origin/main:docs/security-baseline.md`, against the head)

| # | Item | At the head | Evidence |
|---|---|---|---|
| 1 | No plaintext creds / default admin | No credential exists: the surface is public read-only data. gitleaks is clean over the tree and over the range's history. | `make secrets` green; gitleaks over `81af5ba..HEAD` with project and default rules: no leaks |
| 2 | Server-side authz on mutating routes | No mutating route: five GETs (`main.py:1381,1470,1536,1579,1623`). The FastAPI docs, redoc and openapi routes are off (`main.py:773-775`). | `tests/unit/test_api_v1.py:517` `test_no_mutating_route_exists` (INV-30) |
| 3 | CORS allowlist, never `*` + credentials | Off unless `MODEL_RANKING_CORS_ORIGINS` is set. `fly.toml` does not set it. `*` is refused at boot (`main.py:404`). `allow_credentials=False` and GET only (`main.py:809-810`). | `tests/unit/test_api_config.py:35,109` (INV-31) |
| 4 | Validate config at startup, fail prod | Unset or unknown `APP_ENV` is strict. Missing database, missing build stamp, a bind beyond loopback with no Host list, the refresh switch and an unreadable rate limit each refuse boot (`main.py:635-729`). | `tests/unit/test_api_config.py:72,82`, `tests/unit/test_nightly_refresh.py:448`, `tests/unit/test_rate_limit.py:186` (INV-32) |
| 5 | Creds/PII encrypted at rest | The engine stores no PII. The app keeps the typed question only in the gap register (complete protection, INV-67). `answers.json` holds the decoded answers and nothing the reader typed (`StandingsStore.swift` `keep`). Its default protection class is #323, open. | INV-66/67; `fix-issue-297-security.md` |
| 6 | Generic client errors | The 500 handler drops the exception text (`main.py:869`). Every error is JSON with `nosniff`. | `tests/unit/test_stage40_minors.py:143`, `tests/unit/test_api_v1.py:627` (INV-34) |
| — | Host list / DNS rebinding | Fly answers only `model-ranking.fly.dev` (`fly.toml:26`). The Host check runs before the limiter, so a refused Host is never counted. | `tests/unit/test_engine_host.py:46,117` (INV-26) |
| — | Fail direction | The rate limiter (fairness) **fails open** and warns once a minute (`main.py:816-842`). Host, CORS and startup (safety) **fail closed**. | `tests/unit/test_rate_limit.py:40,67,98` (INV-88) |
| — | Built ≠ wired | The limiter and Host check are `@app.middleware` on the live app and are tested through `TestClient`. The phone's address is chosen in `EngineClient.address` (`EngineClient.swift:221-224`), and `ENGINE_URL[config=Release]` comes after the local include (`Engine.xcconfig`, last line). | `ios/EngineTests/EngineClientTests.swift:810,820,844` (INV-73) |
| — | Transport | The Release build uses `https://model-ranking.fly.dev`, with `force_https` at Fly. The only ATS exception is `NSAllowsLocalNetworking`, which no Release address uses. `KeptAnswers.standsIn` (`KeptAnswers.swift:25`) does not cover `.insecureTransport`, so a cleartext refusal is never hidden behind an old answer. | `ios/EngineTests/KeptAnswerTests.swift:155,316-319` |

`docs/security-invariants.md`: compared with `origin/main`, the head changes three rows: INV-6 (tests added), INV-67 (rules added) and INV-73 (reworded for #288/#297, reviewed in `fix-issue-297-security.md`). None of them drops a negative test. The negative suite is green at the head (below).

## Gates passed
- [x] Secret scan green (`make secrets` on the head; gitleaks over the range's history, project config and default-only config: 0 findings)
- [x] `make deps` (pip-audit, every lock): "No known vulnerabilities found". No lock changes in the range.
- [x] `make slopsquat`: PASS, 20 declared, 0 suspect. `pyproject.toml` changes only ruff per-file ignores. No new `import` of a third-party package in `src/`.
- [x] Default-deny preserved for new external surfaces: no new route. The only new fields on `/v1/categories` are `boards` and `refined_board`, both static data.
- [x] Permission matrix not violated: no destructive op, no `.claude/`/`.githooks/`/workflow change in product commits.
- [x] Prompt-injection hygiene: fetched text is parsed as JSON, type-checked and never followed. The on-device model's verdict is one input to deterministic code (`Reading.swift`).
- [x] Auth/PII checks: no auth, payment or migration path in the range, so the §11 trigger does not fire. The PII sink is filed (#323, #314).
- [x] SAST: bandit 1.8.6 cannot parse under Python 3.14, so I ran its rule set through ruff (`ruff --select S`) on `src/` and the new scripts. Only S101 asserts used for type narrowing (`nightly.py:300`, `arena_slices.py:187`) and the reviewed `git` subprocess calls in `check_records.py`.

## Acceptance criteria evidence
- REQ-API-001 / INV-30 (read-only `/v1`) → `src/app/adapter/main.py:1381-1623`; `tests/unit/test_api_v1.py:517`
- INV-31 (CORS) → `src/app/adapter/main.py:387-415,809`; `tests/unit/test_api_config.py:35`
- INV-32 (strict boot) → `src/app/adapter/main.py:635-729`; `tests/unit/test_api_config.py:72,82`
- INV-34 (generic errors) → `src/app/adapter/main.py:869`; `tests/unit/test_stage40_minors.py:143`
- INV-26 (Host list) → `fly.toml:26`; `tests/unit/test_engine_host.py:46,117`
- INV-88 (#187 rate limit, fails open) → `src/app/adapter/main.py:279,816`; `tests/unit/test_rate_limit.py:40,67,98`
- INV-73 (#288 hosted over HTTPS) → `ios/ModelRanking/Engine/EngineClient.swift:208,221`; `ios/EngineTests/EngineClientTests.swift:810,844`
- D-202 cl. 5 (#288 kept answers stand in for unreachability only) → `ios/ModelRanking/Engine/KeptAnswers.swift:25`; `ios/EngineTests/KeptAnswerTests.swift:155,316`
- INV-6 (#279/#311 offline tests) → `ios/EngineTests/OfflineTestCase.swift:66`; `ios/EngineTests/OfflineTestCase.swift:201`

## What I ran (own worktree at `958458d`, own venv, `advisor.db` copied as allowed)
`make install`; `make secrets`; `make deps`; `make slopsquat`; `gitleaks git --log-opts=81af5ba..HEAD` with project and default configs; `make test` (3245 passed, 27 skipped); `make swift-test` (694 tests PASS); `make client-decls` (PASS, 4 configurations); `make review-need RANGE=...` on the uncovered segments; `ruff --select S`; an offline probe of `_in_submissions`; `git merge-tree` on every golden-night merge. I sent no request to the owner's launchd engine or to the hosted engine.

## Risks queued
- **R1** `src/app/adapter/main.py:279-296`: the limiter trusts `Fly-Client-IP`, and that trust is checked only by the runbook's manual check after the deploy (M20 closure S5; INV-88 "Partial"). Carried, not new: run that check on the first deploy of this release.
- **R2** `src/app/workflows/public.py:31`: under D-186 the hosted engine serves every source, CC BY-NC and unlicensed boards included, while the app is on TestFlight. D-186 settles the licences before production, and #265 is open. Before the app ships beyond TestFlight, that ruling must hold. Nothing gates it.
- **R3**: open and filed, context only, not re-filed: #314 and #323 (`answers.json` size check before the read; protection class), #322 (client-decls gaps), #309 (observer gap), and the guard and process items #283–#287, #305, #317–#321.
