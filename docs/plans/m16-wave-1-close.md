---
record_type: wave
id: m16-wave-1-close
status: draft
process_version: v5.0
date: 2026-09-22
---
# Wave-Close Checklist — M16 Wave 1, contracts and two gates (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**Nothing a reader sees changed.** Three ADRs written before the code that will use them, the two
`/v1` fields they add, and the two gates M15 closed owing: the Swift test manifest (W-111) and the
privacy invariant checked against resolved declarations (W-122). The router's floor was re-measured
and did not move — the examples did (W-118).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m16-plan.md` §2 W1 "(risk: **MED**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every piece red-first: the two `/v1` fields on three mutants; the manifest on a deleted test, a deleted line, a rename and a short count; the declaration gate on 20 bypasses from the M15-W4 seats; the router on five question sets. After the review's fix round, `make check`: pytest 962 passed / 15 skipped, `swift-test PASS: 262` (each named in the manifest), `client-decls PASS` on 11 files in 4 configurations (1472 resolved declarations each) | ✅ |
| 3 | Review per tier: MED → independent Code-Reviewer | `docs/reviews/m16-wave-1-review.md` (`seat: independent`, 2026-09-22): **BLOCKING**, 3 BLOCKING / 4 MAJOR / 10 MINOR / 2 NIT, all in or around the declaration gate. The fix round was re-reviewed: `docs/reviews/m16-wave-1-rereview.md` (`seat: independent`, 2026-09-22): **BLOCKING**, 1 BLOCKING / 3 MAJOR / 7 MINOR / 0 NIT -- `CoreFoundation` allowlisted whole gave every client file a socket (R-B1). That round was verified: `docs/reviews/m16-wave-1-rereview-2.md` (`seat: independent`, 2026-09-22): **PASS**, 0 / 0 / 0 / 2 NIT (latent false positives on CoreGraphics geometry and on a `#if` line inside a multi-line string literal; neither fires on this tree, both err toward failing) | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | Not owed at MED (D-141), and the wave's security content is itself a gate: `scripts/client_decl_gate.py` re-runs both M15 seats' privacy bypasses. The HIGH wave is W2, where the refresh moves into the engine | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | Author: 20 privacy bypasses, 3 `/v1` mutants, 4 manifest mutants, each applied by script and hash-checked on restore. The author's count of 18 of 20 dying in this gate was wrong by one: the markdown link dies in the text gate, not here (W-122 correction). Independent seat: 32 bypasses, 11 manifest and 10 `/v1` mutants (`docs/reviews/m16-wave-1-review.md`); every survival is fixed and re-run red, or recorded open in W-122 and the gate's docstring | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-FLR-001 and REQ-PRC-001 in `docs/prd.md` §M16, both cited through `TestClient(adapter.app).get("/v1/categories")`. REQ-FLR-002 and REQ-PRC-002 are W2's and say so | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | D-126 gains a second, independent check: `scripts/client_decl_gate.py`, wired into `make check` as `client-decls`, verified red on the author's bypasses and, after the fix round, on the seat's B-1/B-2/B-3 and the six minors it made a rule for. The text gate (`tests/unit/test_router_hints.py`) is unchanged and still runs — two gates, neither claiming to be the whole check | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None. Mutants ran on the files in place and were restored from a byte copy with an md5 check | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Ways off the device, enumerated from what the COMPILER resolves rather than from the source text: module allowlist + capability rules in `scripts/client_decl_gate.py`, over 1472 declarations in 11 client files, in each of four build configurations; what file scoping cannot see (a relay through `main`, B19) is written into the gate's docstring | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: D-151, D-152, D-153, the two `/v1` fields, the manifest gate, the declaration gate, the router re-measurement and its three Swift tests, the K.8 clause in `AGENTS.md` (D-150 clause 2). **Changed by an owner ruling mid-wave:** D-151 removed the "update now" button D-149 had asked for, so the third ADR planned here was not needed and W2 shrinks. Deferred with a record: the router residual (W-123, M16-W4) | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | ~900 changed lines, roughly half records. **VARIANCE noted:** the wave carries two gates and a measurement record; the code in `src/` is 15 lines | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check (pytest 962/15, Swift 262, client-decls 4 configurations) · ruff/mypy clean · outcome: committed at the wave close, owner reviews at the milestone` | ✅ |

## What the measurement changed about the plan

The wave was planned to "re-measure the floor and update the pin" (W-118). The measurement said the
pin does not need to move: 0.15 and 0.20 answer all 86 questions identically, because nonsense and
weak-but-real matches overlap. What was wrong was the example questions, and fixing those moved the
held-out off-topic set from 3/16 to 8/16 with the probe and held-out sets unchanged
(`docs/reviews/m16-router-floor-measurement.md`). The residual is W-123, and it is owed real
evidence about what people ask rather than another round of guessing — M16-W4.

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-22 · Wave commit range:
`059b519..<this wave's commit>`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/adapter/main.py · src/app/workflows/categories.py
                ios/ModelRanking/Engine/Router.swift · ios/EngineTests/FrontDoorTests.swift
                ios/EngineTests/test-manifest.txt (new) · scripts/client_decl_gate.py (new)
                scripts/router_probe/{nonsense,offtopic,offtopic_heldout}_questions.json (new)
                tests/unit/{test_uncertainty_contract,test_swift_test_manifest}.py · Makefile
                AGENTS.md (K.8, D-150 clause 2) · docs/{decisions,prd,warnings.ledger}.md
                docs/reviews/m16-router-floor-measurement.md (new) · docs/plans/m16-plan.md
                docs/reviews/m16-wave-1-{review,rereview,rereview-2}.md (new) · note.txt

K.8 contracts:  /v1/categories gains `min_quality` (D-152) and `price_excludes` (D-153). Fields
                added, nothing reshaped. Every fact W2's screens will show now names its field:
                the floor line reads `min_quality`, the price note reads `price_excludes`.
```
