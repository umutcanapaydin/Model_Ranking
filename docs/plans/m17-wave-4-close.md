---
record_type: wave
id: m17-wave-4-close
status: draft
process_version: v6.6
date: 2026-09-26
---
# Wave-Close Checklist — M17 Wave 4, every board's standings to the phone

**The engine publishes every board's standings on one additive route, `GET /v1/boards`, and the
phone fetches them once a day and keeps them.** What reaches the phone is limited in two ways:
- **Positions only (D-167 clause 2).** The route carries positions and no scores, so no code on the
  phone can average two scales (D-105). Effort follows D-112 as every surface does.
- **Nothing about the question (D-160 clause 1).** The request carries no parameters, and the phone
  sends it the same way whatever the reader asks.

The combination of chosen boards (`Combine.swift`, D-167 clause 3) was built and then taken out of
the wave. Three Tester verdicts were BLOCKING on the proof of its ordering rule, although the code
agreed with an independent implementation on 6,241 real board sets. The owner ruled on 2026-09-26
to apply the three-attempts stop, and the combination is filed as #61. No screen changes: the
question and the screen come in W5.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m17-plan.md` §2 W4 "(risk: **HIGH**)", and the wave plan `docs/plans/m17-wave-4-plan.md`, which is deleted in this close as DevFlow requires. HIGH because the wave adds a `/v1` route, a second file allowed the file system, and (until the stop) a second file allowed arithmetic | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first per phase: P1 `b62f451`→`ed6c954`, P2 `60cf310`→`73fe0e8`, P3 `a1b0c87`→`d020a96` (removed at the stop, `6aa7aff`). Each review round was also red-first: `ee312f8`→`abf284b` and `c9ec11b`→`ebde1d6`. The Tester rounds added tests only: `4203673`, `f781cbd`, `1398820`, `aaafb5c`, `219aa48`. `make check-fast` PASS before every commit since `73fe0e8`, with the exit code read, not piped | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m17-wave-4-review.md`: a second Code-Reviewer's **PASS-WITH-MINORS**, superseding the first BLOCKING verdict (`cc31cd4`: B1, effort against D-112). `docs/reviews/m17-wave-4-tester.md`: the fifth Tester's **PASS-WITH-MINORS**, on the wave without the combination. The four BLOCKING Tester verdicts are in git (`b35eb3e`, `a5b85ec`, `1cff428`, `f3d513c`). Every seat is `seat: independent`. From the second round on, seats ran one after another (#52) | ✅ |
| 4 | *(plan-tag)* HIGH slice: security pass on the slice | `docs/reviews/m17-wave-4-security.md`: **PASS-WITH-MINORS**, nothing exploitable in scope. S1 (the store read any address), S2 (the size ceiling and the stored fields), S4 (the tripwire's spellings) and S7 (duplicates) were fixed in `abf284b`. S3 is #56, S5 is #55 and S6 is #57 | ✅ |
| 5 | Tester fault-injection, restore byte-identical | The five Tester seats injected 52, 52, 45, 28 and 31 faults, each restored in place and checked by SHA-256. The fifth, on the final scope: 29 of 31 killed, one equivalent, one fixed (`219aa48`). The author's mutants per round, all red, are listed in each commit message | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The route through FastAPI's client (`tests/unit/test_board_standings.py`: shape, D-112 effort, ties, rankable population, no score, dates, attribution, the boot refusals and bound, the closed 503s, the query string ignored). The payload against the Swift structs (`tests/unit/test_ios_payload_contract.py`). The fetch through `StubProtocol` (`ios/EngineTests/EngineClientTests.swift`). The store (`ios/EngineTests/StandingsStoreTests.swift`). The route set (`tests/unit/test_api_v1.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | D-126 holds for two new files. `StandingsStore.swift` is allowed the file system in `scripts/client_decl_gate.py` (`FILESYSTEM_FILES`), and the text gate allows its seven exact expressions (`tests/unit/test_router_hints.py`). Negatives: the store reads no address but a file, and stores only the fields the app decodes. The request carries no query and no header of its own. An oversized payload is refused. The position tripwire refuses arithmetic in every file (`tests/unit/test_ios_client_contract.py`) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, by the author or any seat; each seat attests it in its file (`docs/reviews/m17-wave-4-review.md`, `docs/reviews/m17-wave-4-tester.md`, `docs/reviews/m17-wave-4-security.md`). Mutants were reverted in place and checked by SHA-256, with `PYTHONDONTWRITEBYTECODE=1` after a same-size restore left a stale `.pyc` once | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | The files allowed the file system are the `FILESYSTEM_FILES` map (two entries, each with its reason). Arithmetic on served numbers is allowed only through `SCORE_ARITHMETIC_PERMITTED` (`Uncertainty.swift`) and `POSITION_ARITHMETIC_PERMITTED` (empty until #61). The payload's population is one query, `_ROWS` in `src/app/workflows/standings.py`, which the route and the boot bound share | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m17-w4`, issue #50. P1, P2 and P4 are delivered; P3, the combination, was taken out at the three-attempts stop (#61, owner ruling 2026-09-26). D-167 is accepted, with notes appended for the D-112 effort rule, the stored fields and the stop. The PR opens after the reviews and `/pre-merge`, as the owner asked | ✅ |
| 9a | Economy | `git diff --shortstat 7d7a9ac HEAD`: 20 files, +2519/−34. `src/`, `scripts/` and `ios/ModelRanking/` account for +482/−33; the rest is tests, the review records (nine verdicts across rounds), the plan, the research record and D-167. VARIANCE noted: two Code-Reviewer and five Tester rounds on a HIGH wave | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make wave-check · make gate · CI (py3.12, py3.14, live-contracts, secret-scan, dep-audit, governance) · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Bypass: none. The three-attempts stop was applied, not bypassed (#61) | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-09-26 · Wave commit range: `7d7a9ac..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M6 | fixed `ebde1d6` |
| review M7 | fixed `ebde1d6` |
| review M8 | fixed `c9ec11b` |
| review M9 | fixed `ebde1d6` (the test header); the `save()` guard's own test refused -- a write to a non-file address fails with or without it, so no offline test can tell them apart (confirmed by the second and fifth Testers) |
| review K1 | #51 |
| review K2 | #59 |
| review K3 | #58 |
| review K4 | #52 |
| review R1 | #53 |
| review R2 | #54 |
| review R3 | #55 |
| review R4 | #60 |
| review R5 | fixed `ebde1d6` |
| tester M1 | fixed `219aa48` |
| tester M2 | fixed `219aa48` |

The first Code-Reviewer's B1 and M1-M5 were fixed in `abf284b`. The four BLOCKING Tester verdicts'
findings were fixed in `4203673`, `f781cbd`, `1398820` and `aaafb5c`, except the ordering rule's
proof, which is #61.

## Wave footprint — RECORD ONLY

```
Touched:        src/app/workflows/standings.py (new) · src/app/adapter/main.py
                ios/ModelRanking/Engine/{EngineClient,Models}.swift · StandingsStore.swift (new)
                ios/ModelRanking/ContentView.swift (no change at close; a rename was undone)
                scripts/client_decl_gate.py · tests/unit/test_{board_standings,api_v1,
                ios_payload_contract,ios_client_contract,router_hints}.py
                ios/EngineTests/{EngineClientTests,StandingsStoreTests}.swift · test-manifest.txt
                docs/decisions.md (D-167) · docs/research/m17-w4-standings-payload-2026-09-25.md
                docs/reviews/m17-wave-4-{review,tester,security}.md
Mutant set author: the independent seats (two Code-Reviewers, the security slice, five Testers)
                and the lead agent (supporting evidence only)
Observed RED:   with `DELETE FROM px_median` and the route's require_price_medians removed,
                test_an_artifact_the_route_cannot_read_is_unavailable[empty_medians] failed
                (200 with no boards)
Owner instruction: "Hepsi, tek dosya, günde bir" ("everything, one file, once a day"), "Yalnız
                hepsinde olanlar" ("only models on every board"), "W4 görünmez altyapı" ("W4 is
                invisible infrastructure") (2026-09-25); "Kuralı uygula: çıkar" ("apply the rule:
                take it out") (2026-09-26) -- the combination left at the stop.
K.8 contracts:  /v1 gains GET /v1/boards (additive; the route set test lists five). The Swift
                models gain Standings, BoardStandings, Standing, StandingModel, FetchedStandings.
Stopped at three attempts: Combine.swift (P3, D-167 clause 3) -- filed as #61
Hand-kept lists: standings.HIGHER_IS_BETTER (the metrics' direction); FILESYSTEM_FILES; the text
                gate's EGRESS_EXACT entries for StandingsStore.swift; POSITION_ARITHMETIC_EXACT.
```
