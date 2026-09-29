---
record_type: wave
id: m17-wave-5-close
status: draft
process_version: v6.6
date: 2026-09-28
---
# Wave-Close Checklist — M17 Wave 5, the question selects the boards, and the combined list on the screen

**A question now selects the boards it is about, and when it selects more than one, the reader
gets the product's own combined list** (D-168). The on-device model fills a schema: a surface, and
at most one language (not English) and one domain from a declared table of 16 Arena slices.
`ModelOutputBoundary` keeps a value only when the table declares it for that kind and the chosen
surface allows it.
- **More than one board:** the main answer is `Combine.swift`'s list from the standings the phone
  keeps (D-167). It carries shared places for tied models, D-112's effort notice, and a detail
  naming each board with its labelled date and attribution. The detail states the shared count and
  says the list is the product's own.
- **One board:** today's cards.
- **Refinements** show as chips. A tap removes one on the device, and a removed one stays, to be
  restored.

**Nothing about the question leaves the phone beyond the routed surface id, as since D-126**
(D-160 clause 1 as amended by D-168 note 9). The only new request is the
parameterless `/v1/boards`, fetched at most once a day beside the answer and never awaited by it.

**The owner ruled eleven questions on 2026-09-28**, asked in Turkish:
- surface plus refinement; #54 exact; #53, both publishers count; the combined list only for more
  than one board;
- after the probe, refinements are a language or a domain;
- at the code review:
  - coding takes no refinement (Ruling A);
  - tied models share a place;
  - medical and legal questions are answered;
  - a question that is not a model search gets a note, filed as #66 for after this wave.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m17-plan.md:82` "W5 — The question, read on the device (risk: **HIGH**)", and the wave plan `docs/plans/m17-wave-5-plan.md:11`, deleted in this close as DevFlow requires. HIGH because the on-device model's output now selects what the reader sees, and the main screen changes | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first per phase: P1 `bb716b4`→`eb46b52`, P2 `131ff2f`→`189e6e1`, P3 `0951d52`→`6d6a105`, the kinds ruling `3a7dcd5`→`c506a4a`, the simulator's two defects `d10b3bd`→`d4d7e8c`, the first review `17ae833`→`6c5f14b`, the security pass `c34415b`→`bea72ff`. `make check-fast` PASS before every commit, with the exit code read, not piped; a red commit carried only its intended failures. The screen was driven on the iOS simulator against a W5 engine and the real on-device model, through a scratch XCUITest target, after each screen change (probe record; `d4d7e8c`, `6c5f14b`, `4039fd4`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m17-wave-5-review.md`: the second Code-Reviewer's **PASS-WITH-MINORS**, superseding the first seat's BLOCKING verdict (`6590ce8`: B1 effort and date disclosure, B2 software on coding, B3 `primary_board` in no ADR). `docs/reviews/m17-wave-5-tester.md`: **PASS-WITH-MINORS**. Every seat is `seat: independent`, and the seats ran one after another (#52) | ✅ |
| 4 | *(plan-tag)* HIGH slice: security pass on the slice | `docs/reviews/m17-wave-5-security.md`: **PASS-WITH-MINORS**, nothing exploitable in scope. Prompt injection is blocked as shipped: the encoded schema is closed, and the boundary returns table entries only. Nothing beyond the surface id (sent since D-126) leaves the device. S1 was fixed in `c34415b`→`bea72ff`: the schema is now held by its encoded form, the alternatives by a source pin, and the tap by a guard. S3 was fixed in `e32d77f` (owner ruling: correct the record). S4 and S5 were fixed in `bea72ff`. S2 is #74 | ✅ |
| 5 | Tester fault-injection, restore byte-identical | The Tester injected 73 faults and restored each in place, checked by SHA-256: 59 killed, 5 equivalent, 3 outside the suite by design (the on-device model call, measured by the probe instead), 2 in #60's class (SP4, SP6, evidence on #60), and 4 that stayed green (CB53, L6, L7, L8), each given its test in `96214aa`. Those four were replayed on `96214aa` in a separate copy: each is killed by its new test, and the restores match by SHA-256. The two Code-Reviewers ran 14 and 15 mutants of their own. The security seat's two-edit S1 mutant, which added a free-text field and routed it into `alternatives`, now fails `testTheModelsSchemaOffersExactlyTheDeclaredChoicesAndNothingElse` and the alternatives source pin. The author confirmed each new control goes red on its own mutant, with `Router.swift` restored byte-identical | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | P1: `tests/unit/test_refinements.py`, including the Ruling A rule derived from `CODING_INTENT` and every selectable board served by the artifact (D-163). P2: `ios/EngineTests/RefinementBoundaryTests.swift`, the schema pins and the source pin in `tests/unit/test_router_hints.py`, and `ModelRouter.schema(for:)` built for the served surfaces and read back, as encoded, to exactly its declared choices. P3: `ios/EngineTests/AnswerPlanTests.swift`, `CombineTests.swift` (places, #53), `CombinePropertyTests.swift` (the independent oracle), `LanguageTests.swift` (`CombinedListLanguageTests`). The route field: `tests/unit/test_uncertainty_contract.py` through FastAPI's client. P4: the probe record, reproduced by the second Code-Reviewer and the Tester from the raw runs | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | D-126 and D-168 clause 2: only a declared refinement of its own kind that the surface allows survives (negatives: a value outside the table, another kind's value, a value the surface disallows, a decline carrying one). `Refinement` is built only in the table. Only `ModelOutputBoundary` builds an outcome with refinements, and nothing assigns them later (both mutants red). The schema's closed sets are pinned to the code with comments removed (the old surface pin matched a comment), and held as encoded: three fields, fixed strings only, each with its way out. Only the wording tier builds an outcome with alternatives, and a tap makes only a listed surface the `task`. D-160 clause 1: the data-flow and egress gates are unchanged and pass | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None by any seat, each attested in its file. The author reverted one broken edit of `Router.swift` in place, by reversing the replacement, and checked it byte-identical against `HEAD` with `git hash-object` | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a refinement: the table (`Refinements.swift`, the only `Refinement(` construction) and `ModelOutputBoundary.refinements` (the only `RoutingOutcome(` with `refinements:`), both source-pinned. Producers of a board choice: `Refinements.boards`, which re-checks the surface. The wording and manual tiers produce none (`testTheManualTierNeverRefines`, and the source pin). Gaps are tracked: #60 (text pins match spellings) | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m17-w5`, issue #64: P0-P4 delivered. The plan was amended in place by the owner's kinds ruling (D-168 note). #53 and #54 are addressed as ruled in D-168. Deferred as issues: #66-#74, each triaged. The PR opens after the reviews and `/pre-merge`, as the owner asked | ✅ |
| 9a | Economy | `git diff --shortstat c02fe0d HEAD`: 28 files changed, 3177 insertions(+), 24 deletions(-). `src/`, `scripts/` and `ios/ModelRanking/`: 11 files changed, 768 insertions(+), 18 deletions(-); the rest is tests, the four review records, the plan, the probe record with its two question sets, and D-168. VARIANCE noted: a HIGH wave with a probe of the on-device model, a simulator verification, two Code-Reviewer rounds, a Tester and a security pass | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make wave-check · make gate · the on-device probe (two runs per configuration) · the simulator scenarios · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Bypass: none. `make check-fast` went red once on `test_fetch_bounds` (a race in `bounded_get`, filed as #71) and passed when re-run; that is a filed defect, not a skipped gate. CI's skip budget rose from 72 to 73 (`83069e3`) for the one new test that needs the built `advisor.db` (`test_every_board_a_question_can_select_is_served`), named in `docs/skip-budget.txt` with its reason; it runs on the owner's Mac | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-09-28 · Wave commit range: `c02fe0d..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M6 | #72 |
| review M7 | fixed `4039fd4` |
| review M8 | fixed `4039fd4` |
| review R4 | #73 |
| review R5 | fixed `4039fd4` |
| tester M1 | fixed `96214aa` |
| tester M2 | fixed `96214aa` |
| tester K1 | #71 |
| tester R1 | fixed `96214aa` |
| security S1 | fixed `bea72ff` (tests `c34415b`) |
| security S2 | #74 |
| security S3 | fixed `e32d77f` |
| security S4 | fixed `bea72ff` |
| security S5 | fixed `bea72ff` |

**The first Code-Reviewer's findings** (`6590ce8`):
- B1, B2, M1 and M4 were fixed in `6c5f14b` (red `17ae833`).
- B3 and M2 were fixed in `d1d2667`.
- M3 was fixed in `17ae833` and `6c6d7e2`.
- M5 was fixed in `17ae833` and `6c6d7e2`.
- R3 was fixed in `6c5f14b` and completed in `4039fd4`.
- K1 is #67, K2 is #68, R1 is #69 and R2 is #70.

**Filed from the security pass:** #74 (S2).

**Filed by the session:**
- #66: the owner's note for a question that is not a model search.
- #71: the flaky fetch test, found to be a race in the product.

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/Engine/{Refinements,AnswerPlan}.swift (new) · Router.swift ·
                Combine.swift · Language.swift · Models.swift · ios/ModelRanking/ContentView.swift
                src/app/adapter/main.py (/v1/categories primary_board)
                tests/unit/test_{refinements,router_hints,uncertainty_contract}.py
                ios/EngineTests/{Refinements,RefinementBoundary,AnswerPlan}Tests.swift (new) ·
                CombineTests.swift · CombinePropertyTests.swift · LanguageTests.swift · test-manifest.txt
                scripts/router_probe/{RefinementProbe.swift,refinement_questions.json,
                refinement_heldout_questions.json} (new) · .language-allow (two entries)
                docs/decisions.md (D-168 and two notes) · docs/research/m17-w5-refinement-probe-2026-09-28.md
                docs/reviews/m17-wave-5-{review,tester,security}.md
Mutant set author: the independent seats (two Code-Reviewers, the Tester, the security slice) and
                the lead agent (supporting evidence only)
Observed RED:   the Tester's CB53 (only the first board of a benchmark kept) turned
                testTwoBoardsOfOneBenchmarkBothCount red on 96214aa
Owner instruction: "Yüzey + ince ayar" ("surface plus refinement"), "Aynen kalsın" ("keep it
                exactly"), "İkisi de sayılsın" ("both count"), "Birden fazla pano varsa" ("when
                there is more than one board"), "Yalnız dil + alan" ("language and domain only"),
                "Kodlamaya eklenmesin" ("not added to coding"), "Aynı numara" ("the same number"),
                and medical and legal questions answered (2026-09-28, translated from Turkish)
K.8 contracts:  /v1/categories gains primary_board (additive; D-168 review note 1). RoutingOutcome
                gains `refinements` (D-126 field-set gate). CombinedEntry gains `place`.
Stopped at three attempts: none
Hand-kept lists: Refinements.table (16 entries, each with its reason; held against the artifact's
                served boards and the route's CODING_INTENT); UIText.refinementNames (held by
                testEveryRefinementHasANameInBothLanguages); two .language-allow entries
```
