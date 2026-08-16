---
record_type: wave
id: m6-wave-1-close
status: draft
process_version: v5.0
date: 2026-08-16
---
# Wave-Close Checklist — M6 Wave 1 (the /v1 envelope; Ruling A frozen)

> **STATUS: CLOSED 2026-08-17.** Both reviews ran, both returned BLOCKING, both re-issued BLOCKING
> on the first fix, and both are closed after a third round. `make check` exit 0, 296 passed /
> 12 skipped. W-016 is RESOLVED.
>
> **What this wave actually demonstrated.** The implementation was green, gated and fault-injected
> before any reviewer saw it, and it still carried two BLOCKING defects — one of them in the guard
> protecting the milestone's central contract, which turned out to be a nine-word denylist that a
> single rename walked past. The fix for it was *also* a vocabulary and was killed again. The
> security fix was worse than the defect it replaced for one round: it asserted `"stale": false`
> over 800-day-old evidence, where the original had only been silent. **None of that was found by
> the author, and none of it would have been found by the author.** K.7 is the wave's own evidence.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) — V3C-78 | `docs/plans/m6-plan.md` §3 W1 records **MED + a pulled-forward security pass**; §4 repeats the tier. The diff adds no authz, no secret handling, no crypto and no egress; it parses two query strings against closed vocabularies (`CATEGORIES`, `BUDGETS`) and opens SQLite read-only, so no auto-HIGH trigger fires | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) — V3C-68 | Acceptance tests written FIRST and confirmed RED (10 failed / 3 passed) before `src/app/adapter/main.py` existed in its new form; then implemented to green. Two self-review fixes: the read-only handle collided with the engine's write (see row 6) and an import-order lint error. Final: `.venv/bin/python -m pytest tests/unit/test_api_v1.py` → **13 passed** | ✅ |
| 3 | Review per tier: LOW/MED → ONE combined reviewer; HIGH → Code-Reviewer + Tester separately — V3C-78. **v3.3: reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation)** | **RAN 2026-08-17**, owner-authorized, fresh eyes (authored none of the code). `docs/reviews/m6-wave-1-review.md` → **BLOCKING**, 2 BLOCKING / 10 MINOR. `docs/reviews/m6-wave-1-rereview.md` → BLOCKING re-issued once, then **CLOSED**. It countersigned rows 5 and 6 and found BOTH overstated by this agent: row 5's "0 stayed green" described four hand-picked mutants rather than their fault class (three of the reviewer's own mutants in the same classes stayed green), and row 6's coverage half claimed four tests for REQ-API-005 when the fourth tested a different condition. Both rows are corrected below. Verdict after two fix rounds: **no blocker on the reviewer's line** | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE — V3C-68/F15 | **RAN 2026-08-17**, the plan-tagged pass. `docs/reviews/m6-wave-1-security.md` → **BLOCKING**: the wave's disclosure failed OPEN (a relative staleness proxy that cannot fire for a server process), 1 BLOCKING / 6 MINOR. Re-review re-issued BLOCKING on the FIX — the first remedy keyed health on an informational field and asserted `"stale": false` over 800-day evidence, and it made a latent CLI-only future-date fail-open network-facing. Both closed in round 3. Two of its gates had no runner and are recorded NO-ENVIRONMENT rather than passed: `pip-audit` (declared, not installed; this wave adds zero dependencies) and SAST (`bandit`/`semgrep` absent — substituted with a manual attack pass) | ✅ |
| 5 | Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test — V3C-72/F5 | **Three rounds, 24 mutants, 24 killed, 4 stayed green on first contact and each got its mandatory new test.** Round 1 (4 pre-declared in the plan §3 W1.4): all RED — but the reviewer's countersignature is right that four self-chosen mutants do not measure their fault class, and its own mutants in those same classes stayed green. Round 2, over the fix delta, ran the REVIEWERS' mutants: 10/10 after the CWD-relative-default mutant stayed green and got `test_an_unset_database_env_fails_closed_rather_than_guessing`. Round 3, over the second fix delta: 10/10 after the wrong-join-key and local-clock mutants stayed green and got `test_health_covers_every_source_behind_the_benchmark_not_just_the_declared_one` and `test_the_freshness_clock_is_utc`. Every round reverted in place and verified md5-identical; final `3b20e56b8341822f7f06301c3f9c2cf4`, independently reproduced by the reviewer. **The measured lesson: 8 of the 24 mutants that mattered were written by someone who had not written the code** | ✅ |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — V3C-02 + V3C-73/F6 ("built ≠ wired") | Every test drives `fastapi.testclient.TestClient(app)` over the real routes — no function is called directly except `open_readonly`, whose own test exists because the seam must be provable. REQ-API-001 → `test_no_mutating_route_exists`, `test_categories_endpoint_lists_the_registry`, `test_health_contract_is_untouched` · REQ-API-002 → `test_coding_returns_both_surfaces_and_nothing_ranks_them`, `test_explicit_single_surface_request_returns_that_surface_alone`, `test_ordering_is_documented_and_stable` · REQ-API-004 → `test_each_coding_surface_states_its_own_weakness` · REQ-API-005 → **corrected after the reviewer's countersignature, which found this row overstated.** The first version listed four tests and read as four cases; the fourth exercised an empty database and asserted 200, which is a different condition. The criterion's third case — an unhealthy source — had NO code path and NO test, and was BLOCKING. It now has both: `test_an_unhealthy_source_is_disclosed_on_a_wall_clock`, `test_an_absent_evidence_source_is_never_reported_healthy`, `test_fresh_evidence_reports_healthy_and_says_nothing`, `test_evidence_dated_in_the_future_is_not_healthy`, `test_health_covers_every_source_behind_the_benchmark_not_just_the_declared_one`, `test_the_freshness_clock_is_utc`, alongside `test_unknown_task_fails_closed_with_the_stable_shape`, `test_unknown_budget_fails_closed_with_the_stable_shape`, `test_missing_database_fails_closed_and_leaks_no_path`, `test_an_unset_database_env_fails_closed_rather_than_guessing`, `test_echoed_input_is_bounded`. **Note for the owner (MINOR-R6, both reviewers concur):** the criterion's wording says the unhealthy-source case produces the ERROR SHAPE; it is implemented as a 200 DISCLOSURE, because refusing to answer over stale evidence would contradict the honesty doctrine. Both reviewers read the wording as wrong and the behaviour as right. This is a criterion amendment for the milestone gate, and explicitly not a 503. All in `tests/unit/test_api_v1.py` | ✅ |
| 7 | New/changed security invariants added to the milestone invariants list with their NEGATIVE test — V3C-74/F7 | Three, each with a test that fails if the invariant is broken: **(a) no mutating route exists** — `test_no_mutating_route_exists` enumerates `app.routes` and asserts no POST/PUT/PATCH/DELETE, so V3C-12 is satisfied by proven absence rather than by claim; **(b) the serving path never writes the operator's database** — `test_the_api_never_writes_to_the_database` compares the file bytes across a request, and `test_read_only_handle_refuses_a_write` proves the handle itself rejects DDL; **(c) no filesystem path reaches an error body** — `test_missing_database_fails_closed_and_leaks_no_path`, mutant M3 confirmed RED | ✅ |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) — V3C-06/F17 | Fault injection wrote the original text back with `Path.write_text` and verified md5 identity; no `git checkout`, `git restore` or `git stash` was run at any point in this wave. The tree carried uncommitted work throughout, which is exactly the condition F17 names | ✅ |
| 9c | **Invariant hardening (v3.5, V3C-101):** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE with a citing test per producer | N/A — 2026-08-16. This wave hardens no auth, tenancy or money invariant; it adds a read-only projection over an existing engine. The money-adjacent fields (`blended_per_m`, `input_per_m`, `output_per_m`) are serialized verbatim from `Pick`, with no arithmetic in the adapter | N/A |
| 9b | **Scope & checkpoint (v3.3, V3C-90/OD-4):** scope row appended — planned vs delivered vs deferred vs the signed plan; owner's labeled checkpoint commit exists for this wave | **Planned** (m6-plan §3 W1): `/v1` routes over the existing engine, the Ruling A envelope, the error contract, declared fault-injection targets, a pulled-forward security pass. **Delivered:** routes, envelope, error contract, fault injection (4/4 killed). **Also delivered, ahead of plan:** REQ-API-004's `evidence_dating` (the plan permits W1 or W2) and the read-only serving handle (REQ-API-006's first clause, W3) — the latter was not optional once the wave found the write-during-read collision. **Deferred:** the security pass (row 4) and REQ-API-006's CORS and startup-validation clauses (W3, as planned). **Checkpoint commit:** none — under **D-114** the agent does not commit; the owner makes it | ✅ |
| 9a | **Economy (v3.2, V3C-85/86):** wave diff within ~≤400 changed lines OR variance noted; projected token spend within the milestone budget line | Wave diff `src/app/adapter/main.py` +216/−9 and `tests/unit/test_api_v1.py` +268 new = **~475 changed lines**, over the ~400 soft bar. Variance noted, not waived: ~57% of it is the acceptance-test file, written first by E.4, and the module's prose carries the Ruling A contract that a later agent must not re-derive. Plan budget for W1 ≈ 90k tokens; spend is within it | ✅ |
| 9 | **Skipped/waived/BYPASSED ledger + run summary (v4.1, V4C-13 + V4C-40-lite):** RUN LINE first, then every check that did not run | `gates run: lint · typecheck · black · mypy · test (296 passed / 12 skipped, was 271 at wave start) · check-records (29 records PASS) · check-records-selftest · install-check · conformance (6 of 7) · wave-check · fresh-eyes code review + 2 re-reviews · pulled-forward security pass + 1 re-review · fault-injection (3 rounds, 24/24 killed) · gates SKIPPED: pip-audit and SAST — NO-ENVIRONMENT, no runner installed in this environment; this wave adds zero dependencies and the security seat substituted a manual attack pass, recorded in its verdict rather than passed over · tokens/cost: over the ≈90k W1 line — three fix rounds were not budgeted; variance noted at the milestone gate · outcome: SHIPPED and CLOSED`. **No pressure bypass this wave.** The two controls that were unavailable at first draft (rows 3 and 4) were not waived to go faster — the wave was held open until the owner authorized a runner, and then both ran. Second occurrence for pip-audit/SAST as NO-ENVIRONMENT; under C2b a third sends the control itself for review, and that trigger is now one away | ✅ |

**Escaped-blocker tripwire (V3C-78):** none escaped — the wave has not closed.

## The finding this wave produced

**`recommend()` writes while serving a read.** `build_price_medians` runs `DELETE FROM px_median`
+ `INSERT` on every call (`rank.py:143-170`), so the engine cannot be driven from a read-only
handle. M5's closure security review already recorded this (NOTE-7 / MINOR-3) and correctly judged
`recommend.main`'s read-write handle appropriate for a CLI. **An HTTP surface changes that
judgement:** serving from a read-write handle would let an anonymous GET rewrite the operator's
table, and `schema.connect()` would migrate the file on top of it (W-009).

The signed plan says W1 makes **no engine change** and that a route needing different engine
behaviour is *a finding, not an implementation detail*. So the wave did not change the engine. It
opens the file read-only and backs it up into an in-memory copy per request
(`adapter/main.py:serving_snapshot`); the engine writes into the throwaway copy and the operator's
bytes are never touched.

**That contains the defect, it does not fix it,** and the containment has a cost that grows with the
database. The real fix — a median computation that does not write — is engine work. Ledgered as
**W-017**, owning milestone M6-W3, where W-009's two migration entry points are already being
reconciled.

## Wave footprint — RECORD ONLY, no rule attached (v5.0)

```
Touched:        docs/decisions.md · docs/gp-field-findings.md · docs/plans/m6-wave-1-close.md ·
                docs/reviews/m6-wave-1-{review,rereview,security}.md · docs/warnings.ledger.md ·
                src/app/adapter/main.py · tests/unit/test_api_v1.py
                (`git diff --name-only 1faaf77..f3c75b9` — 9 paths, 2 of them code)
K.8 contracts:  the `/v1` envelope, the `surface` field and its two coding values,
                `evidence_dating`, `source_health`, and the error body shape — ALL NEW, frozen by
                this wave under D-115. No existing shared interface was changed: the engine was not
                touched, verified by the reviewer two ways.
Closure rounds: not yet — filled at milestone closure.
```

### Where this wave actually got stuck, and for how long

Recorded because the owner asked for it and the template's three lines do not carry it. **The
elapsed figures are commit-to-commit wall clock**, not agent working time, and they include the
reviewers running in the background — they are an upper bound on the wave, not a cost of the code.

| | |
|---|---|
| Elapsed, first commit to close | **52 min** (`1faaf77` → `f3c75b9`) |
| Gate that consumed it | **row 3 / row 4 — the fresh-eyes review and the security pass** |
| Gates that cost minutes, not rounds | `lint` twice (import order, then an unused import), `typecheck` once (a template `src/__init__.py` I copied in by mistake broke the src-layout: 64 errors) |
| Gates that never failed | `test`, `check-records`, `install-check`, `wave-check` |

**The shape of the delay is the finding.** Implementation to first green took a small fraction of
the wave; the remaining time was three review rounds, and every round found something the previous
one had not. Nothing was slow because it was hard to write. It was slow because it was wrong in
ways the author could not see, twice.

Filled by: `Claude (lead agent, local lane under D-114)` · Date: `2026-08-16` · Wave commit range: `1faaf77..working tree, uncommitted — under D-114 the owner makes this wave's commit`
