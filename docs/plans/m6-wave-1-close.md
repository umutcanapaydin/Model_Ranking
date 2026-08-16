---
record_type: wave
id: m6-wave-1-close
status: draft
process_version: v5.0
date: 2026-08-16
---
# Wave-Close Checklist — M6 Wave 1 (the /v1 envelope; Ruling A frozen)

> **STATUS: NOT CLOSED.** Rows 3 and 4 have not run — this wave has had no fresh eyes on it, and
> K.7 is not negotiable. Everything else is done and green. See row 9 for the declaration, and
> `docs/warnings.ledger.md` W-016 for the owning entry. **W2 does not start until this closes.**

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) — V3C-78 | `docs/plans/m6-plan.md` §3 W1 records **MED + a pulled-forward security pass**; §4 repeats the tier. The diff adds no authz, no secret handling, no crypto and no egress; it parses two query strings against closed vocabularies (`CATEGORIES`, `BUDGETS`) and opens SQLite read-only, so no auto-HIGH trigger fires | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) — V3C-68 | Acceptance tests written FIRST and confirmed RED (10 failed / 3 passed) before `src/app/adapter/main.py` existed in its new form; then implemented to green. Two self-review fixes: the read-only handle collided with the engine's write (see row 6) and an import-order lint error. Final: `.venv/bin/python -m pytest tests/unit/test_api_v1.py` → **13 passed** | ✅ |
| 3 | Review per tier: LOW/MED → ONE combined reviewer; HIGH → Code-Reviewer + Tester separately — V3C-78. **v3.3: reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation)** | **NOT RUN — NO-ENVIRONMENT.** 2026-08-16. The lead agent authored every line of this wave, so it cannot supply fresh eyes (K.7). No second reviewing agent is available to it without the owner's authorization. Declared, not waived: ledgered as W-016 | SKIPPED |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE — V3C-68/F15 | **NOT RUN — NO-ENVIRONMENT.** 2026-08-16. The signed plan tags this wave for a pulled-forward security pass because it is the project's first network-facing surface. Same cause as row 3; same ledger entry W-016. Recorded here precisely because F15 is the failure mode where a plan-tagged security pass is silently skipped | SKIPPED |
| 5 | Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test — V3C-72/F5 | **4 mutants, 4 killed, 0 stayed green.** Targets were declared in the signed plan (§3 W1.4) BEFORE the code was written. M1 precedence field → `test_coding_returns_both_surfaces_and_nothing_ranks_them` RED · M2 one surface for the coding intent → same test RED · M3 filesystem path in the error body → `test_missing_database_fails_closed_and_leaks_no_path` RED · M4 evidence-dating disclosure dropped → `test_each_coding_surface_states_its_own_weakness` RED. Reverted in place; baseline and final md5 both `c7eeb711bf98bd2b0b80ab3aa446a36d`, verified identical | ✅ |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — V3C-02 + V3C-73/F6 ("built ≠ wired") | Every test drives `fastapi.testclient.TestClient(app)` over the real routes — no function is called directly except `open_readonly`, whose own test exists because the seam must be provable. REQ-API-001 → `test_no_mutating_route_exists`, `test_categories_endpoint_lists_the_registry`, `test_health_contract_is_untouched` · REQ-API-002 → `test_coding_returns_both_surfaces_and_nothing_ranks_them`, `test_explicit_single_surface_request_returns_that_surface_alone`, `test_ordering_is_documented_and_stable` · REQ-API-004 → `test_each_coding_surface_states_its_own_weakness` · REQ-API-005 → `test_unknown_task_fails_closed_with_the_stable_shape`, `test_unknown_budget_fails_closed_with_the_stable_shape`, `test_missing_database_fails_closed_and_leaks_no_path`, `test_a_surface_that_cannot_answer_is_disclosed_not_dropped`. All in `tests/unit/test_api_v1.py` | ✅ |
| 7 | New/changed security invariants added to the milestone invariants list with their NEGATIVE test — V3C-74/F7 | Three, each with a test that fails if the invariant is broken: **(a) no mutating route exists** — `test_no_mutating_route_exists` enumerates `app.routes` and asserts no POST/PUT/PATCH/DELETE, so V3C-12 is satisfied by proven absence rather than by claim; **(b) the serving path never writes the operator's database** — `test_the_api_never_writes_to_the_database` compares the file bytes across a request, and `test_read_only_handle_refuses_a_write` proves the handle itself rejects DDL; **(c) no filesystem path reaches an error body** — `test_missing_database_fails_closed_and_leaks_no_path`, mutant M3 confirmed RED | ✅ |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) — V3C-06/F17 | Fault injection wrote the original text back with `Path.write_text` and verified md5 identity; no `git checkout`, `git restore` or `git stash` was run at any point in this wave. The tree carried uncommitted work throughout, which is exactly the condition F17 names | ✅ |
| 9c | **Invariant hardening (v3.5, V3C-101):** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE with a citing test per producer | N/A — 2026-08-16. This wave hardens no auth, tenancy or money invariant; it adds a read-only projection over an existing engine. The money-adjacent fields (`blended_per_m`, `input_per_m`, `output_per_m`) are serialized verbatim from `Pick`, with no arithmetic in the adapter | N/A |
| 9b | **Scope & checkpoint (v3.3, V3C-90/OD-4):** scope row appended — planned vs delivered vs deferred vs the signed plan; owner's labeled checkpoint commit exists for this wave | **Planned** (m6-plan §3 W1): `/v1` routes over the existing engine, the Ruling A envelope, the error contract, declared fault-injection targets, a pulled-forward security pass. **Delivered:** routes, envelope, error contract, fault injection (4/4 killed). **Also delivered, ahead of plan:** REQ-API-004's `evidence_dating` (the plan permits W1 or W2) and the read-only serving handle (REQ-API-006's first clause, W3) — the latter was not optional once the wave found the write-during-read collision. **Deferred:** the security pass (row 4) and REQ-API-006's CORS and startup-validation clauses (W3, as planned). **Checkpoint commit:** none — under **D-114** the agent does not commit; the owner makes it | ✅ |
| 9a | **Economy (v3.2, V3C-85/86):** wave diff within ~≤400 changed lines OR variance noted; projected token spend within the milestone budget line | Wave diff `src/app/adapter/main.py` +216/−9 and `tests/unit/test_api_v1.py` +268 new = **~475 changed lines**, over the ~400 soft bar. Variance noted, not waived: ~57% of it is the acceptance-test file, written first by E.4, and the module's prose carries the Ruling A contract that a later agent must not re-derive. Plan budget for W1 ≈ 90k tokens; spend is within it | ✅ |
| 9 | **Skipped/waived/BYPASSED ledger + run summary (v4.1, V4C-13 + V4C-40-lite):** RUN LINE first, then every check that did not run | `gates run: lint · typecheck · test (284 passed / 12 skipped, was 271) · check-records (28 records PASS) · check-records-selftest · install-check · conformance (6 of 7) · fault-injection (4/4 killed) · gates SKIPPED: fresh-eyes review (row 3), pulled-forward security pass (row 4) — both NO-ENVIRONMENT, ~0 min cost to this wave and the reason W1 is NOT closed; conformance test-documented-commands remains RED on three historical records, which is GPF-001 handed back to GP and is not this wave's · tokens/cost: within the ≈90k W1 line · outcome: SHIPPED to review-pending, NOT closed`. **This is not a pressure bypass.** No control was skipped to go faster; two controls have no available runner, and the wave is being held open rather than declared done. First occurrence for both — under C2b a third would send the control itself for review | ✅ |

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

Filled by: `Claude (lead agent, local lane under D-114)` · Date: `2026-08-16` · Wave commit range: `1faaf77..working tree, uncommitted — under D-114 the owner makes this wave's commit`
