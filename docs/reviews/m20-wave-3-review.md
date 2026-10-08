---
record_type: review
id: m20-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 3 Code Review (the question picks its family, #211)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `4df0cfc` (red), `7c12a7b` (fix), read with `git show`; the worktree is at `2e6bd28`
(W1 and W2 merged in, reviewed separately)
**Risk tier:** HIGH (plan §2 W3: `Router.swift` is a security glob)

## Verdict
BLOCKING

The two new functions do what their comments say, mostly. But nothing in the app calls either one, and
the one that reads words cannot be called by the routing tiers until D-168 clause 4, and the gate that
holds it, change. The PRD still says REQ-CMB-004 is **MET in the Engine**. So the wave's main criterion
is not met, and the record says it is (B1). The word list also reads many words with a second meaning
(M1 to M3). Five of seven planted faults pass every test (M4).

## How it was checked

- Read plan §1 (row W3), §2 W3, D-168 (`docs/decisions.md:3219-3313`) and D-188
  (`docs/decisions.md:4396-4461`), then the code.
- Copied `ios/` to the scratchpad, outside the worktree. The copy's `Refinements.swift` has the same
  sha256 as the worktree's (`9d1e629f…c7c5`). `swift test --filter QuestionFamilyTests`: 5 passed.
- Ran a scratch probe test that calls the real `Refinements.read` on 64 English and Turkish questions,
  and `familyBoards` on edge cases. The results are quoted below.
- Planted 7 faults in the copy's `Refinements.swift` with a Python script. The script restored each
  file by bytes and checked its sha256 after every plant; all 7 restores matched.
- `tests/unit/test_router_hints.py` and `tests/unit/test_refinements.py`: 52 passed.
- `grep -nE 'URL|EngineClient|client\.|fetch|Session' ios/ModelRanking/Engine/Refinements.swift`
  found nothing. The worktree has no changes (`git status --short` is empty). The scratch copy was
  deleted afterwards.

## Findings

### BLOCKING

- **B1** `ios/ModelRanking/Engine/Refinements.swift:98` and `:141`; `ios/ModelRanking/Engine/AnswerPlan.swift:130`;
  `docs/prd.md:613`; `docs/plans/m20-plan.md:44,82-91`. **Nothing calls the wave's code, and the
  record says the criterion is met.**
  - **Evidence.** `grep -rn 'familyBoards\|Refinements\.read'` over `ios`, `src`, `tests` and `scripts`
    finds only the declarations and `QuestionFamilyTests.swift`. `answerPlan` still builds its boards
    with `Refinements.boards(primary:…)` (`AnswerPlan.swift:130,134`). Every outcome the wording and
    similarity tiers build has no refinements (`Router.swift:526,552,611,622,635`).
  - **Why it cannot just be wired.** D-168 clause 4 (`docs/decisions.md:3244`) says that without the
    on-device model, the wording and manual tiers pick the surface alone. A gate holds that rule:
    `test_only_the_model_output_boundary_builds_an_outcome_with_refinements`
    (`tests/unit/test_router_hints.py:328-347`). D-188 says it "would amend D-168", but none of its five
    clauses mentions a refinement read from words. The plan gives this wiring to W3, the wave made HIGH
    by `Router.swift`. W4 is "screen code and its tests" (MEDIUM), and none of its bullets mention it.
    So nobody owns it.
  - **#206 was dropped.** It is in W3's plan (`m20-plan.md:89,165`) and is still open. Neither commit
    touches it, and the plan was not amended.
  - **Failure scenario.** The owner's phone has Apple Intelligence off. He asks "best ai to answer in
    french" and gets exactly what he got before this wave. The PRD row says "MET in the Engine". W4 then
    builds the screen on the PRD's word, and the gap only shows on the phone.
  - **Fix (either one).**
    - (a) Do what the plan says. Add one sentence to D-188 that amends D-168 clause 4: the wording tier
      may add the refinements `Refinements.read` names. Change the gate so it allows exactly that one
      producer. Set the wording-tier outcome's `refinements` from `read`, filtered through
      `ModelOutputBoundary.refinements(_:for:)` so the surface rule still applies. Wire `familyBoards`
      into `answerPlan`, or say in the plan that W4 does it. Deliver #206, or move it in the plan.
    - (b) Amend the plan and PRD to what was built. REQ-CMB-004 becomes "PARTIAL: the Engine functions
      exist; no question reaches them". Name the wave that wires them and record the D-168 clause 4
      amendment there.

### MINOR

- **M1** `ios/ModelRanking/Engine/Refinements.swift:118-125`. **English language names have a
  second meaning: the nationality or the country.** The comment at `:112-116` says the list takes
  "only words with one reading". The Turkish side keeps that rule, because "Almanca" is only the
  language: "Almanya hakkında" reads as nothing. The English side does not. Probe results:
  - "french fries recipe" → `french`
  - "german shepherd training tips" → `german`
  - "history of the korean war" → `korean`
  - "chinese economy news" → `chinese`
  - "spanish flu pandemic" → `spanish`
  - "russian roulette rules" → `russian`
  - "mandarin orange cake" → `chinese`
  - "write in Turkish about German cars" → `german`. The task's language here is Turkish, so this
    breaks D-168 clause 3.

  **Failure scenario.** Once B1 is wired, "chinese economy news" adds Arena's Chinese-prompts board to
  the `everyday` family, at equal weight (D-188 clause 4). That changes the coverage count and the
  order, and shows a "Chinese" chip the reader never asked for.

  **Fix.** Read English language names the way "polish" is read already: in phrases such as "in X",
  "into X", "X translation", "X text", "X language", "learn X", "translate … X". Add the probes above
  as negative tests.
- **M2** `ios/ModelRanking/Engine/Refinements.swift:123`. **The Turkish stem `lehce` also matches
  "lehçe", the word for "dialect".** "Lehçe" means Polish only when written with a capital letter, and
  `read` lowercases everything. The stem is matched as a prefix, so its endings match too:
  - "karadeniz lehçesi ile yaz" ("write in the Black Sea dialect") → `polish`
  - "bu lehçeyi anlayan yapay zeka" ("an AI that understands this dialect") → `polish`

  This is the "second reading" the comment says the list avoids.

  **Fix.** Drop the stem. Polish stays reachable through the English phrases and the on-device model.
  Or read it only next to a translation word ("lehçe çeviri", "lehçeye çevir"). Add both probes as
  negative tests.
- **M3** `ios/ModelRanking/Engine/Refinements.swift:126-135,150-152`. **Domain words with a second
  meaning, and a guard the commit claims but does not have.** The fix commit says "science fiction is
  no science". The guard at `:152` only handles the Turkish two-word spelling "bilim kurgu". Probe
  results:
  - "write a science fiction story" → `writing, science`
  - "bilimkurgu hikayesi yaz" (the one-word spelling, also common) → `writing, science`
  - "doktora tezi yazımı" ("doktora" means a PhD) → `medicine`
  - "which ai explains moore's law" and "law of large numbers explained" → `legal`
  - "my sister in law wants a recipe" → `legal`. The guard at `:151` needs the hyphens.
  - "kubernetes health check script" and "battery health of my phone" → `medicine`
  - "write user stories for my sprint", "a novel approach to sorting" and "best ai for writing code"
    → `writing`
  - "thin film solar cells" → `entertainment`
  - "fizik tedavi egzersizleri" ("physical therapy exercises") → `science`

  **Failure scenario.** As in M1, a refinement nobody asked for joins the family and changes the list.

  **Fix.** Apply the file's own rule and drop words that have a second meaning: `law`, `health`,
  `novel`, `story` and `stories`, `film` and `films`. Keep `legal`, `lawyer`, `medical`, `healthcare`,
  `novels`, `poem`. Turn the `doktor` stem into whole words (`doktor`, `doktorlar`, `doktoru`). Guard
  "science fiction" and "bilimkurgu". Add each probe as a negative test.
- **M4** `ios/EngineTests/QuestionFamilyTests.swift:28-36,49-55`. **The tests miss most planted
  faults.** Each plant was restored, and its sha256 checked, before the next one:
  - **P1.** `familyBoards` ignores the kind order and walks `chosen` backwards. *Survives.*
    `testAtMostTwoRefinementsAndNoneTwice` checks only `boards.count == 3`, and its `chosen` is already
    in language-first order.
  - **P2.** The "-in-law" guard is removed. *Survives.*
  - **P3.** The "bilim kurgu" guard is removed. *Survives.*
  - **P5.** The family is no longer deduplicated. *Survives.*
  - **P6.** A refinement already in the family counts toward the cap of two. *Survives.*
  - **P7.** "polish" becomes a plain word. *Caught.*
  - **P4** (the Turkish case fold dropped) also survives. But `CategoryHints.plain` makes it equivalent,
    so it is not counted.

  The PRD's "language before domain" and "none twice" are therefore not held by any test, and neither
  are the two guards the commit message names.

  **Fix.**
  - Assert the exact array with `chosen` given domain-first: `[legal, medicine, french, german]` on
    `assistant` must give `["arena", "arena_text_french", "arena_text_german"]`.
  - Assert that a refinement already in the family leaves room for two more.
  - Add a negative test for each guard and for each of the M1 to M3 probes.
- **M5** `ios/ModelRanking/Engine/Refinements.swift:98-110` against `:171-182`, and `:143` against
  `ios/ModelRanking/Engine/Router.swift:386-388`. **Copied code, and an empty family drops the
  primary.**
  - `familyBoards` repeats the loop in `boards(primary:surface:chosen:)` line for line.
  - `read` repeats Router's private `readings`.
  - Probe: `familyBoards(family: [], surface: "assistant", chosen: …)` returns
    `["arena_text_german", "arena_text_french"]`. That is a "family" made of slices only. The doc
    comment says an older engine's missing family "is the caller's primary board", but no caller
    exists to do that.

  **Failure scenario.** W4 wires `familyBoards` straight to `/v1/categories`' `boards`. Against an
  engine older than M20, the list is ranked by two language slices and no primary board.

  **Fix.** Give `familyBoards` the primary and fall back to `[primary]` when the family is empty. Have
  `boards(primary:…)` call it. Make `readings` internal and reuse it.
- **M6** `docs/plans/m20-plan.md:87-88`. **The plan's example cannot happen.** The plan says "`Türkçe`
  ('Turkish') … adds that language's board". There is no Turkish board: none in `Refinements.table`,
  and none in `src/app/workflows/families.py:49-58`. "Türkçe metin yaz" reads as nothing, which is
  right. But the plan was not amended, so the next reader expects a Turkish board.

  **Fix.** Amend the bullet to name the languages that exist (Chinese, French, German, Japanese, Korean,
  Polish, Russian, Spanish). Say that Turkish has no Arena slice.

## Privacy (D-126, D-160, D-167 clause 1)

Holds. `Refinements.swift` has no URL, client or fetch. `read` returns only rows of the declared table,
and `familyBoards` returns only board ids. `test_nothing_typed_by_the_reader_reaches_the_engine` and
the other router-hint gates pass (52 passed). If B1 is fixed by option (a), R1 applies.

## What looks good

- `read` matches English words exactly, so "polishing" and "germane" do not match. The Turkish side
  uses only the "-ca/-ce" language forms, and leaves out "iş", "tıp" and "roman", whose plain spellings
  are English words. Probes: "is plani yaz", "tip yazılımı", "bir roman yaz" and "tıp fakültesi" all
  read as no language and no false domain.
- Uppercase Turkish works ("ISPANYOLCA ÇEVİRİ", "ÇİNCE", "İŞLETME ÖDEVİ").
- Ruling A holds: `software` is not allowed on `coding`, and the test checks it
  (`QuestionFamilyTests.swift:21-26`).

## Hardened-invariant producers

- **Producers of "a refinement is on an outcome only through `ModelOutputBoundary`":**
  `ModelOutputBoundary.outcome` (`Router.swift:839`). The citing test is
  `test_only_the_model_output_boundary_builds_an_outcome_with_refinements`.
- **Gap:** the wave adds a second source of refinements (`Refinements.read`) and does not connect it
  to that invariant (B1, R1).

## Acceptance criteria evidence

- **REQ-CMB-004, "the surface brings its family; refinements after it, at most two":**
  `Refinements.swift:98-110`, tested at `QuestionFamilyTests.swift:13-36`. Partly held (M4). Not
  reached by any question (B1).
- **REQ-CMB-004, "with no model, the words choose the refinement":** `Refinements.swift:141-162`,
  tested at `QuestionFamilyTests.swift:39-55`. Not reached by any tier (B1). The words are not all
  one-reading words (M1 to M3).
- **REQ-CMB-004, "nothing leaves the phone":** held (Privacy above).
- **#206:** not delivered (B1).

## K.8 contract drift check

The wave changes no engine field and no shared type. `RoutingOutcome.refinements` and
`Refinement` are unchanged (`git show 7c12a7b --stat`: only `Refinements.swift`, the test and
`docs/prd.md`). Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- None

## Risks queued to next M
- **R1** `tests/unit/test_router_hints.py:334`. **The D-168 clause 4 gate reads only `Router.swift`.**
  If B1 is wired by calling `Refinements.read` from `AnswerPlan.swift`, `ContentView.swift` or a new
  file, the refinements reach the combined list with no boundary check, and the gate stays green.
  **What would show it is real:** a `Refinements.read(` call outside `Router.swift` while the gate
  still passes. **Fix:** make the gate scan `ios/ModelRanking/` for `Refinements.read(` and allow
  only the one declared producer.
