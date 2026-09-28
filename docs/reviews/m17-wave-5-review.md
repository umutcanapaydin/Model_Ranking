---
record_type: review
id: m17-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-28
---
# M17-W5 Code Review (re-review): the question selects the boards, and the combined list on the screen

**This verdict supersedes the BLOCKING verdict** committed in `6590ce8` (range `c02fe0d..d4d7e8c`).
That version stays in git history. The code comments and commit messages that cite "review B1" to
"B3", "M1" to "M5" and "R3" refer to it. My own findings are numbered from **B4**, **M6**, **K3** and
**R4**, so the two sets cannot be confused.

**Reviewer:** Code-Reviewer seat, fresh eyes. This is a new seat. I wrote none of this wave's code,
tests or records, and I am not the previous reviewer.
**Independent:** yes
**Date:** 2026-09-28
**Commit range:** `c02fe0d..d1d2667`: 20 commits, including the merge of `main` (`9979324`), whose
content is already on the base, and the previous verdict (`6590ce8`). Without the review file the
diff is 25 files, +1775 / -20. I read it as a whole, then read the review round `d4d7e8c..d1d2667`
(5 commits, 21 files, +590 / -55 without the review file) against the previous verdict.
**Risk tier:** HIGH (`docs/plans/m17-wave-5-plan.md:11`)
**Model routing (HIGH, advisory):**
- Author family: Claude (all 20 commits carry `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second family is available to this seat.
- Fresh context: this seat had none of the authoring context.

**What I read first.** `git diff --stat c02fe0d..d1d2667 -- .claude .agents AGENTS.md
permission-matrix.md` is empty, so the policy I applied is the base ref's. I read, in order:
- `.claude/agents/Code-Reviewer.md`, `AGENTS.md`, `.agents/rules/practices.md` and
  `permission-matrix.md` §11;
- the wave plan with its amendment note (`:73-74`), its K.8 addition (`:51-56`) and its
  fact-to-field map (`:58-69`), and `m17-plan.md` §W5 (`:82-88`);
- D-168 with both notes (`docs/decisions.md:3151-3237`), D-167 and its amendments (`:3088-3149`),
  D-160 (`:2771`), D-126 (`:1022`), D-115 (`:592`), D-112 (`:486`), D-104 (`:308`), D-147
  (`:2056`), D-150 (`:2192`), D-163 (`:2951`) and D-135 (`:1414`).

I read the code before the commit messages.

**How I worked.**
- **Gate.** `make check-fast` at `d1d2667` on a clean tree, with `PYTHONDONTWRITEBYTECODE=1`:
  **PASS** in 51.4 s.
  - lint, typecheck and records: PASS.
  - test: 1514 passed, 23 skipped. The 23 are the network contract tests and the tests that need
    the owner's Epoch bundle; the new artifact test ran.
  - swift-test: 347 tests, exactly the manifest.
  - client-decls: PASS, 15 client files in 4 configurations.
- **Mutants.** Each was applied in place and restored by copy from a scratch backup. Each restore
  was verified with sha256 against the pre-mutation hash:
  - `Combine.swift` 3e63eca5…, `AnswerPlan.swift` 06f5af5a…, `Refinements.swift` a5fc7a34…,
    `Router.swift` d107473c…, `Language.swift` 276b27b6…, `ContentView.swift` 4a8a5b7b…,
    `main.py` 04f1b87d….
  - **Killed (15).**
    - N1: a place is `index + 1`, so ties do not share one. Killed by
      `CombineTests.testTiedModelsShareAPlace` and the property test.
    - N2: dense places (1, 1, 2). The same two tests.
    - N3: the effort notice ignores `ranking_effort`.
    - N4: it counts every standing on the board, not only the listed models.
    - N5: one effort counts as a mix.
    - N6: no effort is ever named.
    - N7: a date the engine read is labelled as an evaluation date.
    - N8: a refinement's board keeps its internal label.
    - N9: the effort sentence names no effort.
    - N10: `software` refines `coding` again.
    - N11: a refinement field is a free `String` schema (the previous S10, which survived).
    - N12: the surface's closed set gains a value that is not in `known`.
    - N13: `primary_board` serves `primary_benchmark`.
    - N14: the manual tier carries refinements.
    - N15: the wording tier inserts a refinement after building its outcome
      (`.refinements.insert(contentsOf:…)`). Killed by `testTheWordingTierNeverRefines`, because the
      embedding assets load on this Mac. The source pin meant to hold this on every machine passes
      it (see the producers table).
  - **Survived (3), all in `ContentView.swift`.** Each passed the whole Python suite and
    client-decls:
    - V1: the main list's effort sentence is disabled (`if false && …`, `:304`);
    - V2: the place shown is the first board's position instead of `entry.place` (`:269`);
    - V3: the detail's date goes back to the unlabelled `evidence_date ?? observed_at` (`:1226`).

    These are the previous K1 and R1, as that verdict stated them (see below).
- **The records.** I recomputed every figure in the probe record and in D-168's review note from
  the raw run files in the scratchpad: `md-run{1,2}-surface.json`, `md-run{1,2}-v2.json`, `ld-*`,
  `final-*`, `main-surface.json` and `live-boards.json`. I did not re-run the model.
- **The served artifact.** I opened a copy of the worktree's `advisor.db` (sha256 005855fa…; the
  original is unchanged) through `TestClient` with `APP_ENV=test`. I read `/v1/categories` and
  `/v1/recommendations` for the seven surfaces a refinement can join.
- **Screens.** I read `ui-shots/sheets/w5-f.png` and `w5-g.png`, and the accessibility dumps
  `04-*`, `05-*` and `06-*` in the scratch `ui-shots/w5/`.
- **Network.** None. I did not call `build()`, did not set `RUN_CONTRACT_TESTS`, and touched neither
  the simulator nor the engine on port 8081.
- **Clean-up.** One `.pyc` that a `make` leg rewrote was deleted. The tree is clean apart from this
  file.

## Verdict
PASS-WITH-MINORS

**What the round resolved.**
- **B1, B2 and B3 are resolved.** Each fix is held by a test that fails when it is reverted: B1 by
  N3 to N7 and N9, B2 by N10, B3 by N13. The combined list now carries D-112's effort notice, and a
  date that says what it is.
- **The owner's rulings of 2026-09-28 are recorded and applied:**
  - (a) `software` does not refine `coding`;
  - (b) tied models share a place (1, 1, 3), computed in `Combine.swift`;
  - (c) medical and legal questions are answered;
  - (d) is #66, and is out of scope.
- **M1 to M5 are resolved.**
- **The previous R3 is resolved for the cards.** A residual is queued as **R5**.
- **The records' numbers now reproduce exactly from the raw run files.**

**Nothing blocks.**
- No gate was widened in this round.
- Ruling A holds on every path the code controls.
- The place rule agrees with D-167 clause 3, and with an independent oracle.
- The ADR was appended to, not edited.

**What remains.**
- **M6.** D-168's note 4 claims more parity with the cards than the code has. The staleness warning
  is not carried. This is latent on today's artifact.
- **M7.** The probe record and the plan's map still carry some imprecise statements.
- **M8.** The "product's own list" sentence has no citing test.
- **R4.** Ruling A can still be lost when the on-device model sends a coding question to `web-dev`
  or `document`.

## The previous verdict, finding by finding

| id | what was asked | what the round did | verified by | status |
|---|---|---|---|---|
| B1 | the combined list discloses efforts and dates | `CombinedView.mixedEfforts` (`AnswerPlan.swift:17-21`, `:57-66`), `boardDate` (`:40-44`), rendered at `ContentView.swift:304-307` and `:1226-1231` | `AnswerPlanTests.swift:143`, `:155`, `:164`, `:173`, `:180`; N3 to N7, N9 killed | resolved; rendering unpinned (V1, V3), as the previous K1/R1 said |
| B2 | Ruling A on a coding question | `software` refines `assistant`, `everyday`, `document`, `web-dev` (`Refinements.swift:76-80`); D-168 note 2 (`docs/decisions.md:3211-3214`) | `test_refinements.py:60-69`, derived from `CODING_INTENT` (`main.py:82`); N10 killed | resolved; residual through misrouting (**R4**) |
| B3 | an ADR names `primary_board` | D-168 note 1 (`:3208-3210`); plan K.8 addition (`m17-wave-5-plan.md:51-56`) | `test_refinements.py:121`, `test_uncertainty_contract.py:317`; N13 killed | resolved |
| M1 | tied models share a number, computed in `Combine.swift` | `CombinedEntry.place` (`Combine.swift:30`, `:84-90`); the view prints it (`ContentView.swift:269`); D-168 note 3 (`:3215-3216`) | `CombineTests.swift:30`; the oracle (`CombinePropertyTests.swift:60-68`) counts strictly lower averages by cross-multiplication, independent of the production index walk; N1 and N2 killed | resolved |
| M2 | the records' numbers, committed question sets, the fact-to-field map | record §1, §4 and §5 rewritten; D-168 note 7 (`:3227-3235`); both sets under `scripts/router_probe/`; map at `m17-wave-5-plan.md:58-69` | recomputed, see "The records" below; the sets are byte-identical to the scratch originals (sha256 24ae98fe… and c80844bf…) | resolved; smaller imprecisions remain (**M7**) |
| M3 | pin the schema; correct clause 2; reword the decline sentence | pin at `test_router_hints.py:120-141`, reading code with comments removed (`:31-34`); D-168 note 6 (`:3224-3226`); `Router.swift:444-447` | N11 and N12 killed. The wording tier's decline groups (`Router.swift:129-136`) never listed medical or legal questions, so the two tiers agree. No ADR required declining them | resolved |
| M4 | readers' board names, the count said once, the chip's control | `boardTitle` (`AnswerPlan.swift:48-53`); `sharedCount` removed; `.accessibilityLabel` (`ContentView.swift:338`) | `LanguageTests.swift:449`, `:458`; N8 killed; `06-en-0.txt` reads "Remove the German board"; `06-en-detail-0.txt:28` reads "Arena text · German" | resolved |
| M5 | four tests weaker than their names | artifact test on the served boards (`test_refinements.py:72-88`); vision guard says it checks nothing (`:91-94`); manual tier test (`RefinementBoundaryTests.swift:93`); a source pin for the tiers (`test_router_hints.py:147-166`) | the artifact test ran in the gate; N14 killed | resolved; the source pin reads spellings (producers table) |
| R3 | the answer waits for the standings | the standings step moved after the recommendation (`ContentView.swift:769-777`) | read | resolved for the cards; residual (**R5**) |

**The previous K1, K2, R1 and R2 stand as stated** and are to be filed at close, as the author
plans. Two notes for those issues:
- **K1 and R1 should carry V1 to V3 as evidence.** The visible half of the B1 fix and of M1 can be
  reverted with every gate green. The cheapest step is the one the `disclosures(` gate already takes
  (`tests/unit/test_ios_client_contract.py:94-120`): require that `UIText.combinedEffortNote(` and
  `UIText.boardDate(` are called in `ContentView.swift`. That would kill V3, though not V1.
- **R2 grows slightly.** The B1 fix adds one pass over each chosen board's standings on every render
  (`AnswerPlan.swift:57-66`).

**The author's own finding is confirmed.** At `c02fe0d` the old pin `anyOf:\s*known` matched only
the doc comment at `Router.swift:469` (`GenerationSchema(anyOf: known)`). The code read
`anyOf: ModelOutputBoundary.schemaChoices(for: known)`. N12 now fails the corrected pin.

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M6** `docs/decisions.md:3217-3219`, `ios/ModelRanking/ContentView.swift:149-150`, `:1226`.
  **D-168's note 4 says "the combined list discloses what the cards disclose", but it carries only
  two of the facts the cards carry. The staleness warning is not one of them.**

  **What the branch hides.** When the plan is `.combined`, the branch hides the surface's whole
  answer. That answer was loaded (`state = .loaded`), and it carries `stale_notice` and
  `source_health.notice`. `classifyDisclosures` (`Router.swift:915-945`) gives a stale source the
  `.state` weight: the orange warning that D-135 (`docs/decisions.md:1414`) keeps loud because it
  "became true and can become false". The combined path shows only "Newest evaluation: <date>", on
  the detail screen. So when a chosen board passes the engine's 90-day window
  (`recommend.py:49`, REQ-REC-006), the product's main answer stops warning, and REQ-APP-003
  ("every disclosure the API sends is visible", `docs/prd.md:387`) fails on that path.

  **It is latent today.** On the artifact, every primary board a refinement can join is dated
  within 25 days (the oldest is `epoch_gpqa`, 2026-09-02), and every Arena slice within 2 days. The
  two undated boards (`epoch_eci`, `epoch_webdev`) carry the undated notice, which the new
  "publishes no evaluation date" label states.

  `close_call` is also hidden. D-167's cost clause (`:3121-3123`) accepted that the phone cannot
  show distance, so I do not count it.

  **Why MINOR, not BLOCKING like B1.** Nothing is hidden on any combination today. The fix is small.

  **The fix, either of two.** Render the `.state`-weight items of the surface's own answer under the
  combined list; the function and the loaded answer are both at hand. Or narrow note 4 to the two
  facts it covers, and file the staleness half.

- **M7** `docs/research/m17-w5-refinement-probe-2026-09-28.md:17-18`, `:44-46`, `:112`, `:136`;
  `docs/plans/m17-wave-5-plan.md:63`, `:66`, `:113-114`; `ios/ModelRanking/ContentView.swift:769-771`.
  **The records' numbers now match the runs, but six statements around them do not.**

  **The baseline is one run.** The record says every figure is from at least two runs (`:17-18`).
  `main`'s 20 of 43 comes from one run (`main-surface.json`; `probe-main.log` executed once),
  against a spread of 5 between two identical shipped runs (25 and 30).

  **"More often on both" does not hold as shipped.** The sentence at `:44-46` holds for the
  configuration with kinds. As shipped, the gain is on the held-out questions (12 and 16, against
  `main`'s 7). On the tuning questions it is 13 and 14, against `main`'s 13.

  **A counter-example is left out.** "Turkish questions naming one ... got it" (`:112`) lists the
  Polish and Russian questions. It leaves out the Spanish birthday poem (held-out question 18), which
  got no language in either run. The 15 of 17 counts it; the prose does not.

  **The harness does not skip.** "Elsewhere it skips" (`:136`) is true only below macOS 26. On
  macOS 26 without Apple Intelligence, `ModelRouter.route` returns `nil` (`Router.swift:417`), and
  `RefinementProbe.swift` writes a file of `nil` rows. The committed harness is otherwise a faithful
  parameterised form of the scratch `ModelProbeTests.swift` that produced the files: its routing and
  row logic are the same line for line.

  **The plan's map predates M4's fix.** The map says a board's name is `boards[].benchmark` and a
  chip's name comes from `Refinements.swift` (`:63`, `:66`). Since M4's fix, a refinement board is
  named as the benchmark's text before `(` plus the chip's name (`AnswerPlan.swift:48-53`). That
  name comes from `UIText.refinementNames` in `Language.swift`, keyed by the table's value.

  **One comment overstates.** The plan (`:113-114`) and the comment at `ContentView.swift:769-771`
  say the kept standings answer offline. But an offline load fails the recommendation first, and the
  failure view replaces the whole home screen (`ContentView.swift:76-82`). The kept copy answers
  only when the boards fetch alone fails.

  **The fix:** a correction pass on the record, the plan's map and the comment.

- **M8** `ios/ModelRanking/Engine/Language.swift:547-554`. **D-160 clause 3's sentence, "the list is
  the product's own", has no citing test.** It is a P3 criterion (`m17-wave-5-plan.md:143-144`,
  D-168 clause 7). It is visible on both screens (`06-en-0.txt:194`, `06-en-detail-0.txt:22`).
  But `grep combinedNote ios/EngineTests` is empty, so the sentence can lose its count, its board
  count or its disclaimer in either language with every gate green.

  The other detail facts are held: the attribution by `CombineTests.swift:125`, the dates by
  `AnswerPlanTests.swift:180`, and the names by `LanguageTests.swift:449`.

  The Tester's citing-test rule makes this criterion BLOCKING at the next seat. **The fix:** a
  two-language test in the shape of `AnswerPlanTests.swift:173`, citing D-160 clause 3.

### PASS (what looks good)

- **Nothing the on-device model writes can reach a board or the screen except as a declared entry
  the chosen surface allows.**
  - The schema offers closed sets only (`Router.swift:424-436`). Both are pinned (N11, N12).
  - `ModelOutputBoundary.refinements` keeps a value only if it is the declared entry of its own
    kind that the surface allows (`:531-536`).
  - `Refinements.boards` checks the surface again (`Refinements.swift:102-113`).
  - `Refinement` is built only in the table (`test_router_hints.py:196-204`).
  - The round's new types carry payload data, never model text: `BoardEfforts` holds efforts from
    `/v1/boards`, and `boardTitle` uses the names table.
- **Ruling A holds on every path the code controls.**
  - No table entry names `coding` or `agentic-coding`, held by a test derived from the route's own
    `CODING_INTENT`.
  - A coding outcome can therefore reach neither `.combined` nor `.restorable`
    (`AnswerPlan.swift:92-103`), and its cards and ordering note are unchanged
    (`ContentView.swift:150-238`).
- **The effort notice follows the engine's rule.** `effort_mix_notice` (`recommend.py:362-383`)
  stays silent where the surface ranks at one effort, and otherwise names the distinct non-empty
  efforts when there are two or more. `AnswerPlan.swift:60-64` does the same per board, over the
  listed models.
  - The only difference is the order the efforts are named in. The engine sorts them. The phone
    keeps the board's order, to stay clear of the sort tripwire. That is presentation only.
  - On the artifact, the cards the combined branch hides carry `effort_mix_notice` on `assistant`,
    `document`, `factuality`, `web-dev` and `mathematics`. The combined list now says the same on
    screen (`06-en-0.txt:195`; the Turkish run in `05-coding-0.txt:332`).
- **The place rule is exactly D-167 clause 3 plus the owner's ruling.**
  - The order still breaks an equal sum by id (`Combine.swift:80-83`).
  - A place is one more than the models with a strictly lower sum. That is the same as the mean,
    since every model has one rank per chosen board.
  - The screens show 1, 1, 3 and 28, 28 (`w5-f.png`, `w5-g.png`).
  - `Combine.swift` stays the one file with position arithmetic. The position and sort tripwires
    pass unchanged.
- **The D-126 gates and the no-skip gate are untouched.**
  - `RoutingOutcome`'s fields are unchanged since the first round.
  - The only request is still the parameterless `client.boards()` (`ContentView.swift:774`).
  - No committed Swift test skips. `RefinementProbe.swift` lives under `scripts/`, outside the
    tests the gate reads, as `probe.swift` already did.
- **The records' numbers reproduce.**
  - §4's table, both runs: surface 26 and 28, language 37 and 37, domain 34 and 35, both 31 and 32,
    spurious 6 and 4, missed 3 and 4, clean 16 and 18 of 21, Turkish 15 and 15 of 17.
  - The "before" runs: 28 and 28, 33 and 33, 4 and 6, 17 and 17.
  - §2's rows: 20, 30-34, 27-29 and 25-30; agreement 35 of 43.
  - §4's with-kinds row: 18-20, 14-15, and 10-11 of 17.
  - §5: 15 and 12 lists, 32 to 189 models, median 98 in both runs, smallest on `document`.
  - D-168 note 7 matches the table.
- **The new `.language-allow` entries are justified and exact.**
  - Each names one file and gives a reason.
  - The counts in the reasons are right: 12 questions carry Turkish letters in set 1. In the
    held-out set, 17 are written in Turkish; an eighteenth is in English and names a Turkish place.
  - The task-language rule is measured on questions written in Turkish, so a translation would
    delete the evidence. JSON has no inline-code form that L1 exempts.
- **Red came first in the round.** `17ae833` holds tests only. `6c5f14b` adds one assertion and one
  test for the `efforts` helper it introduces; N6 kills that test. `6c6d7e2`'s tier tests pin
  behaviour that already held, which needs no red. `docs/decisions.md` gains 33 lines and loses none.
- **No drive-bys, no AI attribution.** Every file is in P1 to P4's scope. No commit in the range
  carries a `Co-Authored-By` or "Generated with" line.

## Producers of hardened invariant(s)

This wave hardens eight invariants:
1. only a declared refinement the surface allows reaches a board (D-104, D-126, D-168 clause 2);
2. nothing derived from the question leaves the device (D-160 clause 1);
3. `RoutingOutcome` carries no free text (D-126);
4. the wording and manual tiers never refine (D-168 clause 4);
5. one board keeps the cards, and several get the combined list (D-168 clause 7);
6. a coding request takes no refinement (D-115, D-168 note 2);
7. the combined list discloses mixed efforts and what its dates mean (D-112, D-168 note 4);
8. tied models share a place (D-168 note 3).

| producer | invariant | citing test | gap |
|---|---|---|---|
| `ModelOutputBoundary.outcome` / `.refinements` (`Router.swift:531-554`) | 1, 3 | `RefinementBoundaryTests.swift:16-79`; `test_router_hints.py:169` | none |
| `ModelRouter.route` schema (`Router.swift:424-436`) | 1 | `test_router_hints.py:120` | none (N11, N12 killed) |
| wording tier (`Router.swift:389`), manual tier (`:644`) | 4 | `RefinementBoundaryTests.swift:83`, `:93`; `test_router_hints.py:147` | The source pin reads Router.swift only, and bans `=`, `.append` and `+=`. N15's `.insert` passes it, and a builder placed between `ModelOutputBoundary` and the next type would be attributed to it. The Swift test caught N15 where the assets load. This is the class #60 already tracks. |
| `Refinements.table` / `.boards` (`Refinements.swift:42-113`) | 1, 6 | `RefinementsTests.swift:13-60`; `test_refinements.py:38-100` | none (N10 killed) |
| `answerPlan`, `mixedEfforts`, `boardDate` (`AnswerPlan.swift:40-108`) | 5, 7 | `AnswerPlanTests.swift:37-188` | none (N3 to N7 killed) |
| `combine` place (`Combine.swift:84-90`) | 8 | `CombineTests.swift:30`; `CombinePropertyTests.swift:79` | none (N1, N2 killed) |
| `ContentView` wiring (`:142-160`, `:254-310`, `:716`, `:769-777`, `:1212-1257`) | 2, 5, 7, 8 on screen | egress gates only (`test_router_hints.py:207`) | V1 to V3 survive: the previous K1 and R1 |
| `/v1/categories` `primary_board` (`main.py:1346`) | the first board | `test_refinements.py:121`; `:73` against the served artifact | none (N13 killed) |

## Acceptance criteria evidence

- **P0:**
  - D-168 → `docs/decisions.md:3151-3204`, with its code-review note at `:3206-3237`.
  - The plan → `docs/plans/m17-wave-5-plan.md`, with its amendment (`:73-74`), K.8 addition
    (`:51-56`) and map (`:58-69`).
- **P1:**
  - every entry names a served board → `tests/unit/test_refinements.py:46` (declared) and `:73`
    (served artifact, D-163);
  - surfaces exist and each has a reason → `:52`;
  - languages and domains only → `:38`, `ios/EngineTests/RefinementsTests.swift:56`;
  - primary first, then at most two refinements in the declared order →
    `RefinementsTests.swift:17`, `:25`;
  - the surface's restriction → `:34`;
  - no board twice → `:41`;
  - vision only on vision → `test_refinements.py:91` (a guard, stated as checking nothing today);
  - a coding request takes none → `:60`.
- **P2:**
  - an undeclared value, another kind's value and a value the surface disallows are each dropped →
    `ios/EngineTests/RefinementBoundaryTests.swift:24`, `:31`, `:39`;
  - `none` adds nothing → `:48`;
  - a decline carries none → `:56`;
  - an unknown surface is refused → `:64`;
  - the choices offered → `:69`, and the schema itself → `tests/unit/test_router_hints.py:120`;
  - the wording and manual tiers → `RefinementBoundaryTests.swift:83`, `:93`,
    `test_router_hints.py:147`;
  - nothing new is sent → `test_router_hints.py:207`, the client-contract gates and client-decls,
    all run PASS.
- **P3:**
  - one board shows the cards and several the combined list → `ios/EngineTests/AnswerPlanTests.swift:41`,
    `:45`;
  - the shared count → `:45`, `:116`;
  - a removal recombines, and a removed refinement stays to restore → `:68`, `:78`;
  - missing boards → `:85`, `:94`, `:101`, `:111`;
  - the effort notice → `:143`, `:155`, `:164`, `:173`;
  - the date → `:180`;
  - the board names → `ios/EngineTests/LanguageTests.swift:449`;
  - the attribution → `ios/EngineTests/CombineTests.swift:125`;
  - the "product's own" sentence → `ios/ModelRanking/Engine/Language.swift:547-554` and the
    screens, with **no citing test (M8)**;
  - tied places → `CombineTests.swift:30`.
- **P4:**
  - the probe → `docs/research/m17-w5-refinement-probe-2026-09-28.md` §2 to §4, which reproduces
    (imprecisions in **M7**);
  - the list sizes → §5, which reproduces;
  - the harness and sets → `scripts/router_probe/RefinementProbe.swift`,
    `refinement_questions.json`, `refinement_heldout_questions.json`;
  - the security pass → not in this range; the plan runs it before merge (`:12-13`).

## K.8 contract drift check

`grep -n` at `d1d2667`:
```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:207:protocol QuestionRouter {
ios/ModelRanking/Engine/Router.swift:488:enum ModelOutputBoundary {
ios/ModelRanking/Engine/Router.swift:507:    static func schemaChoices(for known: [String]) -> [String] {
ios/ModelRanking/Engine/Router.swift:517:    static func refinementChoices(for kind: RefinementKind) -> [String] {
ios/ModelRanking/Engine/Router.swift:531:    static func refinements(_ raw: [RefinementKind: String], for surface: String) -> [Refinement] {
ios/ModelRanking/Engine/Router.swift:538:    static func outcome(
ios/ModelRanking/ContentView.swift:682:    private func submit() {
tests/unit/test_ios_client_contract.py:171:SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}
tests/unit/test_ios_client_contract.py:176:POSITION_ARITHMETIC_PERMITTED: dict[str, str] = {"Combine.swift": "D-167"}
tests/unit/test_ios_client_contract.py:280:    ("Combine.swift", "common"): "D-167 clause 3: shared models ordered by their combined ranks.",
ios/ModelRanking/Engine/Combine.swift:30:    let place: Int
ios/ModelRanking/Engine/Combine.swift:47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
ios/ModelRanking/Engine/AnswerPlan.swift:19:    let mixedEfforts: [BoardEfforts]
ios/ModelRanking/Engine/AnswerPlan.swift:84:func answerPlan(
ios/ModelRanking/Engine/Refinements.swift:27:struct Refinement: Equatable, Hashable {
ios/ModelRanking/Engine/Refinements.swift:102:    static func boards(primary: String, surface: String, chosen: [Refinement]) -> [String] {
ios/ModelRanking/Engine/EngineClient.swift:200:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/Models.swift:65:    let primaryBoard: String?
src/app/adapter/main.py:82:CODING_INTENT: tuple[str, ...] = ("agentic-coding", "coding")
src/app/adapter/main.py:1346:                "primary_board": spec.primary_source,
tests/unit/test_uncertainty_contract.py:317:    "primary_board",
```
- **The plan's symbols are unchanged apart from line shifts.**
- **`/v1/categories` `primary_board`** is now named in the plan's K.8 addition
  (`m17-wave-5-plan.md:51-56`, lines exact) and in D-168 note 1.
- **`CombinedEntry` gains `place`, and `CombinedView` gains `mixedEfforts`.** Both are Engine-internal.
  Their only constructors are `Combine.swift`, `AnswerPlan.swift` and the property test's oracle.
- **`/v1` gains nothing in the round.**

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- none

## Risks queued to next M

- **R4** `ios/ModelRanking/Engine/Refinements.swift:78-79`; scratch `md-run1-surface.json`,
  `md-run1-v2.json`, `ui-shots/w5/05-coding-0.txt:46`, `:53`. **Ruling A holds only as far as the
  router is right.**

  `software` still refines `web-dev` and `document`, and the on-device model sends coding questions
  there. In the shipped runs, "my unit tests fail after upgrading pandas" went to `document` with
  `software` (surface probe, run 1), and the Rust borrow-checker question went to `web-dev` with
  `software` (held-out question 23, run 1).

  The simulator's own coding screen went the same way. It asked, in Turkish, "I want to write unit
  tests for a REST API I wrote in Python, which model?" *(translated)*, and got "Web development"
  plus the "Software and IT" chip. Each of these shows one combined list where Ruling A shows two
  coding answers.

  The echo names the surface, and "Change" corrects it (D-126), so no rule is broken. The owner's
  ruling (a) is met literally.

  It is real if the owner reads ruling (a) as "a coding question keeps both answers". The owner
  should see these three cases when the wave is presented.
- **R5** `ios/ModelRanking/ContentView.swift:696-716`, `:769-777`,
  `ios/ModelRanking/Engine/EngineClient.swift:151`. **The previous R3 remains for the echo and the
  combined list.**

  `ask()` awaits the whole `load()` when a question changes the surface, and `load()` now ends with
  the standings step. On the day's first such question, the send button stays locked, and the new
  surface's cards sit under the previous question's echo. The combined list then replaces those
  cards, until the download or its 10 s timeout ends. This also inverts the M13-W3 MINOR-8 rule
  ("never above the previous surface's ranking").

  It is real on a slow connection.
