---
record_type: review
id: m20-repo-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 repo review -- the whole milestone, `bd273bc...d005135`

**Seat:** independent `/repo-review` across the whole of M20, as `docs/closure-checklist.md` §B.0
requires. I wrote none of M20's code, tests, reviews or fixes.
**Independent:** yes
**Range:** `git diff bd273bc...d005135`. `bd273bc` is `main`: the M19 closure and the M20 hotfix
(#207). `d005135` is the head of W5. The range holds:
- the M20 and M21 plans (#213);
- the five waves, each a stacked draft PR: W1 #215, W2 #217, W3 #221, W4 #224, W5 #225.

That is 65 files, +13,941/-91. Without the W5 probe runs, the reviews, the plans and the held-out
set, it is 33 files, +2,815/-91.
**Grounded in:** `.agents/rules/practices.md`, `.agents/rules/issues.md`, `permission-matrix.md` §11,
`docs/closure-checklist.md` §B.0, `AGENTS.md` §1 and §5, the M20 plan with its amendments, D-167,
D-168, D-169, D-184 to D-188, the five wave closes and their reviews, and the documents a reader is
sent to (`README.md`, `AGENTS.md`, `docs/architecture.md`, `docs/prd.md`,
`docs/security-invariants.md`, `docs/release-testflight.md`).
**Method:**
- I read the diff by area: the engine (`families.py`, `main.py`, `fly.toml`), the Engine layer
  (`Combine.swift`, `Refinements.swift`, `AnswerPlan.swift`, `Router.swift`, `Language.swift`), the
  screen (`ContentView.swift`), the gates and the records. I read the wave reviews for what they
  dispositioned.
- Tests, run in this worktree at `d005135`:
  - pytest on `test_families.py`, `test_rate_limit.py`, `test_router_hints.py`, `test_refinements.py`,
    `test_uncertainty_contract.py` and `test_ios_client_contract.py`: 158 passed, 1 skipped (it needs
    the built database). The coverage floor does not apply to a subset.
  - `make swift-test`: PASS, 579 tests, each one named in the manifest.
  - `make wave-check` on the five closes: PASS on all five. `make check-records`: PASS.
- A script checked every test the PRD rows REQ-CMB-001 to 005, REQ-APP-002, -005, -007, -008 and
  REQ-REL-004 cite: all 88 exist.
- **Probe (M1).** I read only the `boards`, `surface`, `entries` and `unmeasured` fields of W5's own
  run, `docs/research/m20-w5-runs/after-family.json`. I printed no question. No other held-out
  question was opened.
- `gh`, read only: the body of #208 and the open issue list. The API's rate limit then stopped
  further reads, so I did not read the PRs' closing references.
- No simulator, `xcodebuild`, Docker, `fly`, installer, `launchctl` or browser. No network beyond those
  `gh` reads, and no fault planted. I changed nothing but this file.

**Not raised again:** these are already filed: #199, #200 to #203, #206, #214, #216, #218 to #220,
#222 and #223. Where one is worse than filed, the finding says so (#200 in M3, #203 in M9).

## Verdict

MINOR

## Summary

Nine findings: one MAJOR and eight MINOR, none BLOCKING. Each wave was reviewed on its own; these
findings lie between the waves.
- **M1 (MAJOR)** is correctness. W3's refinements, as W4 wires them into W1's families, put a second
  board of Arena's text vote into 14 of the 54 lists W5's own run built from more than one board.
  D-188 clause 1 forbids exactly that, and no gate sees it.
- **M2** is the release path. The runbook gives no order for build 3, and a build archived before the
  M20 engine is deployed shows no family list and gives no sign of it.
- **M3 to M8** are drift: D-188's pointers, the dropped half weight, a revisit trigger nothing can
  measure, PRD rows, the architecture and #206.
- **M9** is process. M20 has no process-log entry, the third milestone in a row.

## The plan's criteria (`docs/plans/m20-plan.md` §1), against what shipped

| Wave | Criterion | State | Evidence |
|---|---|---|---|
| W1 | REQ-CMB-001: the engine names each surface's family; one table; a gate | **met** | `src/app/workflows/families.py:22-37`; `tests/unit/test_families.py:223` holds D-188's table equal |
| W2 | REQ-CMB-002, -003: coverage, mean percentile, every board the same, old boards named | **met** | `ios/ModelRanking/Engine/Combine.swift:146-187`; `FamilyCombineTests.swift` |
| W3 | REQ-CMB-004: the question picks its family; a refinement adds its slice | **met as worded**; see M1 | `Refinements.swift:99-111`, `:189-206` |
| W4 | REQ-CMB-005, REQ-APP-007, -008: the list is the default, the glow, one tap to the primary | **met**, except on one-board surfaces (M6) | `AnswerPlan.swift:196-223`; `ScreenPathTests.swift:102` |
| W5 | Build 3; a rate limit before external testers; the combination measured (#195) | **in code; not deployed**. The measurement cannot say which answer is better (M5) | `fly.toml:32`; `docs/research/m20-w5-family-probe.md:103-110` |

## Correctness

- **M1 -- MAJOR: the refinements put Arena's text vote into a family twice, which D-188 clause 1
  forbids, and no gate holds a family once a refinement joins it.**
  - **The rule.** A family holds at most one board of each source, because Arena's slices are facets
    of one vote and two of them "would let that source outvote the others" (`docs/decisions.md:4410`,
    `src/app/workflows/families.py:7-10`). `tests/unit/test_families.py:175-191` derives each Arena
    board's vote from its config and holds `FAMILIES` to it. W2 then dropped the stale half weight
    for the same reason: Arena alone would have decided five families (`docs/decisions.md:4448-4453`).
  - **The seam.** Every board in the refinement table is an Arena text slice
    (`ios/ModelRanking/Engine/Refinements.swift:42-93`). Seven of the surfaces it refines already hold
    a text-vote board in their family: `assistant` and `everyday` (`arena`), `expert`
    (`arena_text_expert`), `mathematics` (`arena_text_math`), `web-dev` (`arena_text_coding`),
    `document` (`arena_text_longer_query`) and `factuality` (`arena_factuality`, config
    `text_factuality`). `familyBoards` (`Refinements.swift:99-111`) appends up to two more, and
    `combineFamily` counts each as an independent board for both coverage and the mean
    (`Combine.swift:156`, `:161-174`). The gate reads `FAMILIES` only.
  - **Measured (probe).** In W5's own run on the wording tier (`after-family.json`), 14 of the 54
    lists built from more than one board hold two text-vote boards: `expert` 5, `mathematics` 4,
    `everyday` 3, `assistant` 1 and `factuality` 1. The `mathematics` case comes from almost any math
    question, because `math` and `matematik` name the `mathematical` domain (`Refinements.swift:154`),
    which `mathematics` allows (`:90-92`). Its family then holds `arena_text_math` and
    `arena_text_industry_mathematical`, two cuts of Arena's math prompts.
  - **What the reader gets.**
    - `expert` with a science word has four boards and a coverage of two. Arena's two text slices
      alone admit a model, and they place it, while `epoch_gpqa`, the primary, need not rank it at all.
    - `assistant` with "in Spanish" has two boards, both Arena, and a coverage of one. A model with no
      Spanish evidence is listed, placed by Arena's general board alone, under the chip that says
      Spanish was counted. Under D-168's intersection a refinement narrowed the list; under D-188 it
      adds a vote.
    - The note says "built from 4 boards" (`Language.swift`, `familyNote`), but two of those boards
      are one vote.
  - **Why no seat saw it.** W1 reviewed the families without refinements, and W3 reviewed the
    refinements without a combination. W4 wired the two together, and its reviews checked the screen.
  - **Fix.** This needs an owner ruling, recorded in D-188 clause 1 or 6. Either a refinement board
    replaces the family's board of its own vote (so `everyday` with Spanish reads `epoch_eci`,
    `arena_text_spanish`, `epoch_mmlu`), or the combination counts one vote once, both for coverage
    and in the mean. Either way, add a gate over every surface's family plus every refinement it
    allows, using `_arena_votes`, and a Swift test that `assistant` with Spanish does not list a model
    the Spanish board does not rank. File it as a `bug` with `severity:medium`, since it is the
    milestone's core rule (the owner's "our biggest strength").

## The release path

- **M2 -- MINOR: the runbook gives no order for build 3. A build archived before the M20 engine is
  deployed shows no family list, and nothing says so.**
  - The preamble still reads "Deploy only after you have merged the release's pull requests (M19-W4,
    M19-W5 and the M19 closure)" (`docs/release-testflight.md:12-14`). §2 step 3 says only "Product →
    Archive" (`:94`). The W5 close sends the owner to this file for both the deploy and build 3's
    upload (`docs/plans/m20-wave-5-close.md:11`).
  - **Failure.** The owner archives build 3 from the merged `main` before redeploying Fly. The hosted
    engine's `/v1/categories` then has no `boards`, `Category.boards` is nil
    (`ios/ModelRanking/Engine/Models.swift:66-68`), and `answerPlan` takes the D-167 path
    (`AnswerPlan.swift:167-189`): one-board cards on every wording-tier question. That is exactly the
    state M20 set out to end, and it shows no error. `make journey` (step 1.6) does not check `boards`.
  - **The forged-header check** (`:57-66`) assumes 250 sequential `curl`s land inside about two clock
    minutes. Above about 0.5 s a request (each one is a new TLS connection), no window passes 120. The
    check then reads "every one is 200" and tells the owner to stop sharing the app, even though Fly
    set the header correctly.
  - **Fix.** Add a "Build 3 (M20)" order: merge #213 and #215 to #225 and the closure; deploy; check
    `curl -s https://model-ranking.fly.dev/v1/categories | grep -c '"boards"'`; then archive. Retitle
    the preamble so it names the release. For the header check, time the loop and read it only if it
    finished within 120 s, or send the requests in parallel (`xargs -P`).

## Drift

- **M3 -- MINOR: D-188's pointers are incomplete, and its header understates what it reverses.**
  - `docs/decisions.md:4403`: "**Would amend** D-167 clause 3 and D-168". D-167 carries no
    Amended-by line for D-188; its last one is D-181's (`:3217`).
  - D-168's only pointer names clause 4 (`:3314`). D-188 clause 2 also reverses D-168 clause 6
    (`:3248`), an owner ruling (#54): "only the models every chosen board ranks, no threshold". D-188
    clause 5 reverses clause 7 (`:3250`): the combined list only with more than one board, and the
    cards otherwise.
  - D-188 clause 2's measured figures predate the W1 Tester's M1. "`search` and `search_factuality` 28
    (28, 27)" (`:4443`) was measured while `search` held both boards (`4f7fd8a` precedes `1389d7d`).
    Each family now holds one board.
  - **Failure.** A reader of D-167 or D-168 finds intersection and "no threshold" with no pointer.
    The owner, approving D-188, is not told that it reverses his #54 ruling. #200 is the gate for
    this, and M19's repo review (M10) found the same defect.
  - **Fix.** Add "Amended by D-188" to D-167 (clause 3, for families) and widen D-168's line to clauses
    4, 6 and 7. Name those clauses in D-188's header, with #54. Correct the search figures.

- **M4 -- MINOR: the dropped half weight survives in five places, including the text the owner
  approves.**
  - W2 dropped the half weight (`docs/decisions.md:4448-4453`). It survives here:
    - `docs/plans/m20-plan.md:11` ("weighs a stale board less"), `:53` ("the staleness weight") and
      `:107` ("it weighs half here");
    - both permission tables, `scripts/client_decl_gate.py:305` and
      `tests/unit/test_ios_client_contract.py:440` ("weighted mean percentile positions");
    - `ios/EngineTests/FamilyCombineTests.swift:5` ("the weighted mean");
    - #210's title ("with a staleness weight").
  - The plan's PR, #213, is the vehicle for approving D-188 ("approved ... with the M20 plan",
    `:4400-4402`). Its branch (`origin/plan/m20`, `a9a52d6`) still carries the first text: "and at least
    two do", and a half weight.
  - **Failure.** The owner merges #213 first and approves a rule the code does not implement. The
    "One sentence" of the plan he reads describes the same rule.
  - **Fix.** Rewrite the four in-repo sentences in place. Either bring #213's D-188 to the head's
    text, or have D-188's status say the owner approves the text as of the last wave's merge.

- **M5 -- MINOR: D-188's revisit trigger cannot be measured, by W5's own record, and no issue holds
  what it needs.**
  - D-188 is to be revisited when "the labelled set (#195) shows the combined list placing models
    worse than the primary board" (`docs/decisions.md:4475`). W5 measured it and found that the set
    "cannot say which answer is better ... No ground truth for 'the best model' exists here", and that
    the revisit condition "is not triggered" because it cannot be tested
    (`docs/research/m20-w5-family-probe.md:106-110`). The follow-up is "the owner's call, and none is
    planned yet" (`:121-123`), and no issue holds it.
  - **Failure.** M20's central rule ships with no way to learn that it is wrong. The labelled set
    shows that the list differs from the primary board's on half of its first places (`:103-105`),
    and nothing will ever read that again.
  - **Fix.** File an `enhancement`: a "best model" judgement set, the owner's sample of answers. Or
    amend D-188's revisit to something measurable, for example the owner's verdict on N family lists
    against the primary board's.

- **M6 -- MINOR: the PRD rows and D-188 clause 5 say more than the code does.**
  - REQ-CMB-005 (`docs/prd.md:615`) and D-188 clause 5 (`docs/decisions.md:4455`) say the combined
    list is the default "on every surface". `familyPlan` shows the cards whenever fewer than two
    boards remain (`AnswerPlan.swift:209-212`). So `vision`, `search` and `search_factuality` (one
    board, no refinement allowed) always show cards, and `assistant` does unless a language or domain
    is named. REQ-CMB-005 cites `ScreenPathTests.swift::testAQuestionThatSelectsOneBoardShowsTheCards`
    (`ios/UITests/ScreenPathTests.swift:102`) as evidence for "the list is the default".
  - REQ-APP-003 (`docs/prd.md:425`, MET) still cites
    `AnswerPlanTests.swift::testAStaleBoardIsSaidOnTheCombinedListAsLoudlyAsOnTheCards`
    (`ios/EngineTests/AnswerPlanTests.swift:182`). That holds only on the D-167 path, which an M20
    engine never takes. The default list drops the loud warning on purpose (`AnswerPlan.swift:220`,
    `staleness: nil`).
  - REQ-CMB-004 (`docs/prd.md:614`) says "Nothing about the question leaves the phone". D-168 note 9
    corrected that wording: the surface leaves as `task`.
  - **Fix.** Add the one-board exception to D-188 clause 5 and REQ-CMB-005. Have REQ-APP-003 say the
    family list names its old boards in a small note (REQ-CMB-003). Reword REQ-CMB-004 to "its text,
    its refinements and the reader's removals never leave the phone".

- **M7 -- MINOR: `docs/architecture.md`, `AGENTS.md` §1 and the invariant register describe the
  app before M20.**
  - `docs/architecture.md`:
    - "Only the model tier refines" (`:267-269`); since D-188 clause 6 the words do too.
    - Combination: "keeps only the models every chosen board ranks ... one board shows the cards, more
      than one shows the combined list" (`:287-296`), with no coverage, percentile mean or family.
    - The flow, step 4: "With no refinement kept, the screen shows the engine's cards" (`:346-347`).
    - "The hosted engine has no rate limit" (`:557`); W5 added one, and a 429 `rate_limited` that the
      routes table never mentions.
    - "FLY.IO, prepared and not yet deployed" (`:31`); it has served TestFlight since 2026-10-07.
  - `AGENTS.md:14` grounds the combination in D-160, D-167 and D-168 only, and calls it the
    alternative to "the engine's answer".
  - `docs/security-invariants.md` is unchanged in M20. The W3 and W4 closes (row 7) name a new
    invariant, the one word reader held by `test_router_hints.py:350-389`. W5's fail-open limiter is
    a control class `AGENTS.md` §5 names. Neither is a row in the register.
  - **Fix.** Rewrite those sections in place (practices: live documents), and add the two invariant
    rows with their tests.

- **M8 -- MINOR: #206's rule ahead of the embedding is recorded nowhere, and it narrows D-187
  clause 1.**
  - D-187 clause 1 says that "a question about AI models in general names no surface: the embedding
    reads it, and `everyday` answers it only where the embedding cannot". W3 sends a question made only
    of model names, tier names and Turkish particles to `everyday` before the embedding is tried
    (`ios/ModelRanking/Engine/Router.swift:399-411`, `:541-544`).
  - No ADR line, PRD row or architecture sentence names the rule. `#206` appears in none of
    `docs/decisions.md`, `docs/prd.md` or `docs/architecture.md`.
  - **Failure.** The next change to D-187 (M21-W2's #218, the same path) starts from a clause the code
    no longer follows.
  - **Fix.** Add an Amended-by line under D-187 clause 1 for #206, or a sentence under REQ-RTR-005, and
    name the rule in `docs/architecture.md`'s router section.

## Process

- **M9 -- MINOR: M20 wrote no process-log entry, the third milestone in a row, and its closes say
  nothing about the hooks.**
  - `docs/process-log.md` is not in the range, and it holds no M20 entry. Practices require three to
    ten lines a session. M18's repo review (M15) and M19's (M13) found the same gap. #203, the gate for
    it, is still open.
  - M19's closure recorded a ledger row because the repository hooks never loaded in sessions started
    outside the repo (`docs/control-events.csv`, `repository-hooks`). None of M20's five closes says
    whether they loaded (row 8 is silent), and `docs/control-events.csv` gains no row in the range.
  - **Fix.** Write the M20 entries at the closure, as §B.2 requires. Add a ledger row for M20's hook
    state, or say in each close that the hooks loaded. Raise #203 in M21-W4's order, since this is its
    third occurrence.

## Dispositions, at the closure

| finding | severity | disposition |
|---|---|---|
| M1 | MAJOR | to be fixed or filed at the closure |
| M2 | MINOR | to be fixed or filed at the closure |
| M3 | MINOR | to be fixed or filed at the closure |
| M4 | MINOR | to be fixed or filed at the closure |
| M5 | MINOR | to be fixed or filed at the closure |
| M6 | MINOR | to be fixed or filed at the closure |
| M7 | MINOR | to be fixed or filed at the closure |
| M8 | MINOR | to be fixed or filed at the closure |
| M9 | MINOR | to be fixed or filed at the closure |
