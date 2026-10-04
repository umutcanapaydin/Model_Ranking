---
record_type: review
id: m18-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W3 Code Review, round 3: reading the question

**Reviewer:** a third Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or
records, and I am neither the first nor the second reviewer.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `93040ac..5f0937b`, 11 commits, 89 files. 58 of them are under
`docs/research/m18-w3-runs/`: 56 run files and two scorers. The new round is `a5c0875..5f0937b`: the
fixes `2d5f86a` and the records `5f0937b`. `wave/m18-w3` is stacked on `wave/m18-w2` (#116, head
`93040ac`), so the range is W3's own change. It holds no merge.
**Risk tier:** HIGH (`docs/plans/m18-wave-3-plan.md:13-15`; `m18-plan.md` §3). The diff touches
`ios/ModelRanking/Engine/Router.swift`, a security glob. D-172: no security seat on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the base-ref profile, the
milestone plan §2 W3, the wave plan, D-169 with its amendment, D-126, D-147, D-172, D-174 and D-175.
Then I read the code diff and probed it with my own inputs. Then I re-scored the research record.
Only after that did I read the two earlier reviews and the fix commits.

**Summary.** Round 2's two blockers are fixed in what they asked for:
- the image rule now overrides only a question routed to `vision`, and every probe line of both
  earlier reviews keeps its surface (B4);
- the records state both missed #113 bars and the cost of the question back, and every number
  re-scores exactly from the run files (B5).

The post-fix run files agree with the head's code row by row. The gates pass. Every one of my eight
Swift mutants on the reading is caught.

What is left is MINOR:
- the image rule still overrides some requests to READ a photo, in one English construction (M16);
- two code signals still fire on some genuine searches (M17, M18);
- part of the screen's held path is pinned by no gate (M19);
- one PRD number and 15 PRD citations are wrong (M20).

None of them shows a ranking as if it were measured. M16 shows the wrong ranking, but under a "not
measured" line, with "Change" on screen. M17 costs a tap. M18 shows the note, with "Change" on screen.
I judge each one MINOR on its merits, and say why under each.

**Policy.** I read `.claude/agents/Code-Reviewer.md` from `93040ac`; it is identical at the head.
`git diff --stat 93040ac 5f0937b -- src .claude .agents .github AGENTS.md CLAUDE.md Makefile
ios/ModelRanking/Engine/EngineClient.swift ios/ModelRanking/Engine/StandingsStore.swift` is empty.
`docs/decisions.md` only gains lines (0 removed). No commit carries an attribution line. No text in
the diff tries to change review policy.

**How I worked.** Everything ran in this seat's own worktree, detached at `5f0937b`, with its own
`.venv` (a real directory, built by `make install`). The guard directory was first on PATH.
1. **Gates.** `make check-fast`, output to a file, exit code read:
   - first run: the `test` leg exited at W-108, because the worktree had no `advisor.db`;
   - second run, with a copy of the owner checkout's `advisor.db` (2026-09-24): one failure,
     `test_every_board_a_question_can_select_is_served`; that artifact predates the refinement
     boards, and the wave touches neither `src/` nor that test (**K8**);
   - third run, with a copy of the served engine's artifact (2026-10-01): **PASS, rc 0**, six legs.
     pytest 1657 passed, 25 skipped (network and `EPOCH_DATA_DIR` only). `swift test --parallel`:
     **450 tests**, exactly the manifest. lint, typecheck, records and `client-decls`: PASS.
2. **Re-scoring.** I ran `score_reading.py` and `score_surfaces.py` on the baseline, `final`,
   `final2` and `postfix` runs against their sets, and broke the rows down by class, reading and the
   `model` field with a few lines of Python.
3. **Probes.** Five throwaway Swift tests (`ZZProbeCR3*`, each deleted after its run):
   - about 100 inputs of mine through the five signals;
   - 30 lines through `TieredRouter` with a scripted model;
   - every genuine row of seven sets through the signals;
   - each `postfix` and `final2` row recomputed with the head's code from its `model` field.
4. **Mutants: 17**, each restored with `git checkout`; `git status` was clean after each batch.
5. **Not done, by this seat's rules:** no simulator, so no `make ui-test` (**R1**). The on-device
   model was not run. No installer, `launchctl`, commit, push or GitHub write.

| mutant | gate | result |
|---|---|---|
| image rule on any surface (`vision` condition dropped) | Swift | **caught**, 4 failures |
| `recordsGap` without `reading == .search` | Swift | **caught** |
| model's doubt alone → the note | Swift | **caught** |
| boundary ignores `request` | Swift | **caught**, 4 tests |
| instruction removed from `doubt` (round 2's M9.1) | Swift | **caught** |
| model's verdict never read (`modelSaysNotASearch: nil`) | Swift | **caught** |
| `request` field dropped from the schema | Swift | **caught** |
| the "into" exception removed | Swift | **caught** |
| `indirect case said(String)` (round 2's M10) | `test_router_hints` | **caught** |
| a held-out question inside a longer string (round 2's M13) | held-out gate | **caught** |
| `routing = outcome` in the held branch (round 2's M9.2) | client contract | **caught** |
| `decline` records a gap | client contract | survives (**M19**) |
| `decline` calls `confirm(held)`: "No" answers anyway | client contract | survives (**M19**) |
| `apply` keeps the held card | client contract | survives; UI test only (**M19**) |
| `select` keeps the held card | client contract | survives; no test at all (**M19**) |
| a ranking under the held card | client contract | survives; UI test only (**M19**) |
| a control comment only | all | passes, as it should |

## Verdict
PASS WITH MINOR

**No BLOCKING; five MINOR (M16–M20); three K.9 (K6–K8); two new risks (R5, R6) and four carried
(R1–R4).** Round 2's B4 and B5 are fixed. The wave may go to the Tester.

**The owner's question (D-169 clause 6, as amended).** I was asked to judge whether it is honest and
sufficient.
- **Honest: yes, in the records.** D-169 (`docs/decisions.md:3361-3371`), the plan
  (`m18-wave-3-plan.md:77-86`) and the record (§5 to §7) say that #66's catch bar and both #113 bars are
  missed. They say what the question back costs and on whose word it asks. I re-scored every number.
- **Sufficient: only if the pull request's question carries the numbers for the code that ships.**
  "Whether to ship what holds" is one yes/no over three separate things. The question is not in the
  range yet, so I list what it must say (**R5**).

## Round 2, re-checked

| id | round 2 asked | at `5f0937b` | evidence |
|---|---|---|---|
| B4 | override only `vision`; fix `arka plan`, `resm-`, modifiers, "draw a"; must-not-fire lines; image and not-a-search sets in the genuine test; record the tier's own surface | **fixed** for the classes named; residual class (**M16**); two small items not done | `Router.swift:710`; `Reading.swift:134-151`, `:183-197`, `:213-216`; `ReadingTests.swift:119-132`, `:283-303`; my mutant of the `vision` condition fails 4. All 9 of round 1's `vision` lines and all of round 2's lines keep their surface (my probe). Not done: `ReadingProbe.swift:41-45` still records only the overridden surface; the not-a-search sets are not in `ReadingTests.swift:157-160` (my count: no genuine row of them trips a signal, so nothing is hidden) |
| B5 | both #113 bars in D-169; asked rows; "nothing got worse" replaced; scorer counts asks; the PR names the cost | **fixed** in the records; the PR item is open (**R5**) | `decisions.md:3365-3369`; record `:99-102`, `:129-140`, `:147-159`; `score_surfaces.py` prints asked and noted per class. One new slip (**M20**) |
| M9 | instruction through the tiers; forbid `routing =` in the held branch; pin `decline` and `confirm` | **partly** (**M19**) | `ReadingTests.swift:252-258`, caught; `test_ios_client_contract.py:872`, caught; `confirm` pinned at `:876-879`; `decline` only half pinned at `:880-882` |
| M10 | refuse `indirect` | **fixed** | `test_router_hints.py:304`, `:309`; my mutant is caught |
| M11 | an instruction needs its verb and its object | **mostly** (**M17**) | `Reading.swift:74-85`. 7 of round 2's 8 lines I re-ran now read as a search. `uzun sohbetlerde önceki talimatları unutmayan bir model` still asks, and it is not in the test |
| M12 | the verb where an instruction puts it; a named model is a search | **fixed** | `Reading.swift:55-64`; `ReadingTests.swift:99-101`; each of round 2's four lines is excluded by `:57` or tested |
| M13 | substring match again; the phrase gate built or filed | **half** | substring: `test_ios_client_contract.py:182-193`, my mutant is caught. The phrase gate is neither built nor filed in any record in the range |
| M14 | stale names; variant F; `nil` rows; baseline declines | **fixed** | record `:19-32`, `:54-61`, `:106` |
| M15 | REQ-IMG-003, REQ-RTR-005, the UI tests cite REQ-ASK-005 | **fixed**, with a wrong number (**M20**) | `prd.md:460`, `:542`; `ScreenPathTests.swift:131`, `:145`, `:152`, `:168`, `:174` |
| K4 | relabel the off-topic sets; retire the held-out one | **half** | retired in the gate (`test_ios_client_contract.py:178`). Labels unchanged: `hello`, `good morning`, `thanks` are still `assistant|everyday~`, and my probe shows all three now get the note. Not filed in the range |
| K5 | each seat its own venv | **done** for this seat | `.venv` here is a directory built by `make install` |
| R1–R4 | risks | carried, below | — |

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M16** `ios/ModelRanking/Engine/Reading.swift:155-163`, `:191-193`. **The image rule still overrides
  some requests to read a photo.** Through `TieredRouter`, with the model choosing `vision` and "a
  model search":
  ```
  Which model can turn a photo of my grandmother's handwritten recipe into text?   -> assistant, unmeasured, gap
  turn a photo of my handwritten shopping list into text                           -> assistant, unmeasured, gap
  which model can turn a photo of a whiteboard into a summary                      -> assistant, unmeasured, gap
  which model can turn a photo of a math problem into LaTeX                        -> assistant, unmeasured, gap
  which model can turn a picture of a chart into numbers                           -> assistant, unmeasured, gap
  turn a photo of a page into an editable document                                 -> assistant, unmeasured, gap
  turn this photo of a menu into a shopping list                                   -> assistant, unmeasured, gap
  ```
  `which model can turn a photo of a receipt into a spreadsheet` and `turn a photo of a table into a
  spreadsheet` keep `vision`. There are two causes:
  1. **The target list is short.** "into" counts as reading only before ten words (`:191-193`). LaTeX,
     numbers, a summary, a document or a list read as making an image.
  2. **The window is too short.** `tail` holds the eight words after the verb (`:158`), and the target
     must sit inside it (`:160`). With a longer description, "into text" falls outside the window.

  Each one tells the reader something false ("not measured here"), shows the chat ranking, and adds a
  need to the owner's gap register (R4). This is the same kind of defect as B4.

  **Why MINOR on its merits:**
  - The rule now reaches only `vision`.
  - On the independent set, no request to read an image was overridden: 8 of 10 reach `vision`
    after the fix, as at the baseline (`postfix-image_*`).
  - It is one English construction, the answer carries its disclosure, and "Change" corrects it.
  - The fix is a few lines.

  **The fix:**
  - Turn the test around. After an image noun, "into" means reading, unless a picture or style word
    follows (cartoon, painting, sketch, anime, watercolour, drawing, sticker). Look to the end of the
    text, not eight words.
  - Add the lines above as must-not-fire, through the tiers.
  - Let `ReadingProbe.swift` record the tier's own surface, so a run can count the overrides (round
    2's B4, fix 1).
  - If this is not fixed in this wave, file it on #113 with these lines.

- **M17** `ios/ModelRanking/Engine/Reading.swift:79-82`, `:89-93`. **Round 2's M11, residual: the
  instruction signal still asks some genuine searches.** Each of these asks the reader, even when the
  model says "a model search":
  ```
  which model won't ignore my instructions
  a model that does not forget my instructions in long chats
  which model is least likely to ignore the system prompt
  how do I make eslint ignore some rules
  uzun sohbetlerde önceki talimatları unutmayan bir model      (round 2's own line)
  kuralları unutmayan bir model
  verilerimi paylaşmak istemiyorum, yerelde çalışan model hangisi
  kodumu paylaşmak istemiyorum, hangi model yerelde çalışır
  komut satırı çıktısını gösteren bir script yazan model
  istemci tarafı kodunu gösteren model
  ```
  The Turkish verbs and objects are matched as bare prefixes (`:80`, `:82`):
  - `unut` matches the negative `unutmayan` ("that does not forget");
  - `paylaş` matches `paylaşmak`, and `göster` matches `gösteren`;
  - the object `istem` ("prompt") matches `istemiyorum` ("I don't want") and `istemci` ("client");
  - `komut` matches `komut satırı` ("command line").

  The English verbs do not see a negation. The doc comment (`:68-73`) and D-169's amendment
  (`decisions.md:3339-3340`) say the phrases are specific enough that a search about instructions
  does not use them. The amendment also says "each list is matched on whole words"
  (`decisions.md:3342`). These two lists are matched by prefix.
  - **Why MINOR:** each costs one tap, and on the held-out sets the code's doubts asked no genuine
    search. My count is 0 of the genuine rows of all three fresh sets.
  - **The fix:** read the Turkish verbs through `isTurkishVerb` (`:236`), which already accepts only
    request forms, so `unutmayan` and `gösteren` drop out. Match the objects by their forms
    (`talimat…`, `istemi`, `istemini`), not `istem…`. Skip a verb after "not", "n't" or "won't". Add
    the lines as must-not-fire.

- **M18** `ios/ModelRanking/Engine/Reading.swift:269-276`. **A plural acronym is "no word", which gives
  the note unasked.**
  - `CRDTs` reads as no word: it is mixed case, so it is not taken as an acronym (`:271`), and it is five
    letters with no vowel (`:276`). Through the tiers, with the model saying "a model search" and
    `coding`, the reading is the note. That is D-169's costliest class, bounded at 2 per run.
  - The code's own rule is "an acronym is a word" (`:29-30`).
  - The reverse also holds: `ASDF QWER`, `AAAAAAAA` and `SDFGHJ` read as acronyms, so nonsense typed in
    capitals escapes. That only costs catches.
  - **Why MINOR:** a whole search made of one such token is rare.
  - **The fix:** drop one trailing `s` before the capitals test, and run the repeated-letter and
    keyboard checks before it.

- **M19** `ios/ModelRanking/ContentView.swift:851`, `:887-891`, `:930`;
  `tests/unit/test_ios_client_contract.py:880-882`. **Round 2's M9.3, residual: part of the held path
  is pinned by no gate that runs without a simulator.**
  1. **`decline`** is checked only for `outcome.reading = .notASearch` and for no `apply(`. A `decline`
     that records the gap passes. So does one that calls `confirm(held)` and answers anyway. The
     gate's own message names that defect ("or answers anyway") and does not catch it.
  2. **`held = nil` in `select`** (`:930`) is pinned by nothing. No UI test drives "Change" from the
     note or the question back. Without that line, a surface chosen from the note loads behind the
     note and never shows. D-169's cost statement rests on "Change is always on screen to correct
     it" (`decisions.md:3321-3322`).
  3. **`held = nil` in `apply`** (`:851`) and **no ranking under the held card** (`:175-177`) are held
     only by UI tests (`ScreenPathTests.swift:153`, `:132-136`), which no gate runs (R1).

  **The fix:**
  - Pin `decline`'s body to its two statements.
  - Pin `held = nil` in `select` and in `apply`.
  - Add one UI path: the note, then "Change", then a surface, then its ranking shows.

- **M20** `docs/prd.md:542`, `:524`, `:544` and eight older rows;
  `docs/research/m18-w3-question-reading-probe-2026-10-04.md:131`, `:147-149`. **Records: one number
  is the old code's, and 15 citations point at the wrong lines.**
  1. **REQ-IMG-003** says the rule "on a held-out set … caught 10 of 15". That was the rule before
     B4's narrowing (`final2`). The code that ships caught 7 of 15 on the same set (record §6;
     `postfix`, 7 and 7). D-169 and the record give both numbers. The PRD gives only the higher one.
  2. **The record** says that some image-reading requests reach `vision` only after the question back
     (`:148-149`). After the fix, that was 6 of 8 in run 1 and 2 of 8 in run 2. §6 does not say that 3
     of the 15 requests to make an image now get the `web-dev` ranking as if it were measured
     (`postfix`, 3 and 3). Before the narrowing the rule caught them (`final2`, 0 on `web-dev`).
  3. **Citations.** Lines this wave inserted into two test files moved citations that were right at
     `93040ac`:
     - REQ-ASK-005: `ReadingTests.swift:103`, `:123`, `:230` (now `:110`, `:138`, `:261`);
     - REQ-GAP-001: `ReadingTests.swift:252` (the gap test is `:307`), `test_ios_client_contract.py:803`
       (now `:806`; the held-branch pin is `:869`), `test_router_hints.py:383` (now `:399`);
     - older rows that cite `test_ios_client_contract.py:204`, `:379`, `:446`, `:511`, `:770` (twice),
       `:973` and `:1110` (now `:236`, `:415`, `:482`, `:547`, `:806`, `:1034`, `:1171`): REQ-APP-001,
       REQ-APP-002, REQ-APP-004, REQ-APP-005, REQ-ASK-001, REQ-ASK-004, REQ-DTL-001 and REQ-PRC-002;
     - REQ-RTR-004's `test_router_hints.py:310` (now `:326`).

     Each now points into another test or into a test's body.

  **The fix:**
  - Give REQ-IMG-003 the shipped number, 7 of 15, on a spent set.
  - In the record, give 6 and 2 of 8, and the 3 requests on `web-dev`.
  - Re-point the 15 citations. **K7** is the gate that would stop this happening again.

### PASS (what looks good)

- **B4's core is fixed.** The rule overrides only `vision` (`Router.swift:710`). My mutant that drops
  the condition fails four tests. All of round 1's `vision` lines, and every line round 2 named, keep
  their surface through the tiers. The Turkish `resmi`, `arka plan` and `çizelge` cases no longer fire.
- **The records are true, and the post-fix runs are the shipped code.**
  - Every number I checked in §2, §4, §5 and §6 re-scores exactly. Examples: coding 34 and 30 against
    7 and 6; not-a-search 21 and 20 caught (4 noted, then 9 and 8 asked on the model's word, 8 and 8
    on the code's); after the fix 21 and 19, with genuine 0 noted, 3 and 2 asked; image 7 and 7 made,
    8 (6) and 8 (2) read.
  - The "5 and 10 in 145" sum is right.
  - Each `postfix` and `final2` run holds every question of its set once, with no `nil`.
  - Recomputed with the head's code from each row's `model` field, all 260 `postfix` readings match.
    No `vision` row is one the head would override. The §6 run was made with the code that ships.
- **No genuine row trips a code signal:** 0 of 199 genuine rows across the not-a-search tuning, M17,
  fresh not-a-search, fresh image (image rule on `vision` rows) and coding sets. Every genuine search
  that was asked was asked on the model's word alone, as the record says.
- **The held-out discipline holds.** The gate catches a held-out question inside a longer string
  again. The one 20-character overlap in the code (`bana bir fıkra anlat`) is an "ambiguous" row,
  which no bar scores, and its text is a common phrase.
- **D-126 holds.** The verdict is one closed field, mapped only at `Router.swift:590`. `reading` is a
  closed enum with three bare cases, pinned. The note and the question are the app's own sentences
  (`Language.swift:672-693`). The held branch sends nothing, and `/v1` is unchanged.
- **The screen's core path is sound.** A held reading sends no request (`ContentView.swift:839-844`).
  `confirm` waits for a question in flight (`:876`) and answers as routed. A gap is kept only for a
  search (`FrontDoor.swift:338-340`). Round 2's `routing = outcome` mutant is now caught.
- **#73 is met** on a set nobody tuned on. The model's wording did not change after that measure
  (`git diff 4373dae 5f0937b -- Router.swift` touches one comment and `read`).
- **Small and clean.** No `noqa`, no `type: ignore`, no drive-by edit outside the review fixes. The
  manifest grew by exactly the new Swift tests.

## Producers of hardened invariant(s)

| producer | invariant | citing test | gap |
|---|---|---|---|
| `ModelOutputBoundary.outcome(…, request:)` (`Router.swift:583-606`, `:590`) | the verdict is one of two closed values; anything else is no verdict (D-126, D-169) | `ReadingTests.swift:200`; `RefinementBoundaryTests.swift:131`, `:134` | none (two mutants caught) |
| `RoutingOutcome.reading`, `InputReading` (`Router.swift:49`; `Reading.swift:12-19`) | the outcome carries no text | `test_router_hints.py:297-309` | none (`indirect` caught) |
| `TieredRouter.read`, the decision (`Router.swift:714-716`), on every tier (`:688`, `:691`, `:697`) | code signals decide on every tier; the model's doubt alone asks | `ReadingTests.swift:214`, `:221`, `:228`, `:236`, `:252`, `:261` | none (three mutants caught) |
| `TieredRouter.read`, the image rule (`Router.swift:710-713`) | a request to make an image routed to `vision` is unmeasured, and nothing else is overridden | `ReadingTests.swift:269`, `:283`; signal `:110` | reading questions with "into …" (**M16**) |
| `ContentView.ask`, held branch (`ContentView.swift:839-844`) | a held reading sends no request and keeps no gap (D-169 cl. 4, 5) | `test_ios_client_contract.py:869-874`; `ScreenPathTests.swift:132`, `:146`, `:169`, `:175` (local) | none in Python |
| `confirm` (`:873-884`) | "Find a model" answers once, as routed | `test_ios_client_contract.py:876-879`; `ScreenPathTests.swift:153` (local) | none |
| `decline` (`:887-891`) | "No" gives the note and nothing else | `test_ios_client_contract.py:880-882`; `ScreenPathTests.swift:132` (local) | gap and answer mutants survive (**M19**) |
| `apply`, `select` clear the held card (`:851`, `:930`) | an answer, or a chosen surface, replaces the card | `ScreenPathTests.swift:153` for `apply` (local) | `select`: no test (**M19**) |
| `recordsGap` (`FrontDoor.swift:338-340`) | only a search is kept | `ReadingTests.swift:307`, `:278` | none |
| `InputSignals.*` (`Reading.swift:26-287`) | no genuine search trips a signal | `ReadingTests.swift:12-191` | residual classes (**M16**, **M17**, **M18**) |
| held-out gate (`test_ios_client_contract.py:165-195`) | no live held-out question in code or tests | itself; my mutant is caught | `.json` sets not scanned (**K6**) |

## Acceptance criteria evidence

**Milestone W3** (`m18-plan.md:32`: REQ-RTR-005, REQ-ASK-003, REQ-ASK-005):
- **REQ-ASK-005** → `docs/prd.md:524` (PARTIAL, honest). Evidence:
  - code: `Reading.swift:296-303`, `Router.swift:704-716`, `ContentView.swift:839-918`;
  - tests: `ReadingTests.swift:12`, `:57`, `:95`, `:110`, `:138`, `:214-:265`, all citing REQ-ASK-005
    at `:1`; `ScreenPathTests.swift:132-179`, each citing REQ-ASK-005;
  - gates: `test_ios_client_contract.py:869-882`.
- **REQ-RTR-005** → `prd.md:460` (PARTIAL). The image rule is at `Router.swift:710`, tested at
  `ReadingTests.swift:269` and `:283`.
- **REQ-ASK-003** → `prd.md:523`: the carve-out to REQ-ASK-005. The gap rule is at
  `FrontDoor.swift:338` and tested at `ReadingTests.swift:307`.
- **REQ-GAP-001**, D-169 clause → `FrontDoor.swift:338`; `ReadingTests.swift:307`;
  `test_ios_client_contract.py:872`. The PRD cites the wrong lines (**M20**).
- **REQ-IMG-003** → `prd.md:542` (OPEN). The number is wrong (**M20**).
- **"Read better than the baseline, by the bar set after it":**
  - #73 is met: 34 and 30 of 40, against a bar of 22 and a baseline of 7 and 6 (record §4, re-scored).
  - #66 is better than the baseline (0 noted before, 21 and 20 caught now) but misses its bar of 32.
    Its false-positive bounds hold: 0 noted, and 1 and 2 asked.
  - #113 misses both bars: 10 and 10 at the measure, 7 and 7 after the fix, against 11; reading 8 and
    8 against 9.

  D-169 clause 6 sends the misses to the owner (**R5**).
- **"Measured twice on a set written independently":** true for all three problems (§4 and §5; the
  sets are in `da48707`, after the code they measure).

**Wave plan phases** (`m18-wave-3-plan.md:115-121`):
- **P0:** met. The plan, D-169 (`decisions.md:3270`), the sets, and the baseline (§2).
- **P1:** met as written. Each signal is tested on its own (`ReadingTests.swift:12-107`). The one named
  colon doubt is at `:183-185`. The test covers eight genuine sets (`:157-160`), and my count adds the
  rest: 0 of 199 genuine rows of the not-a-search sets and the fresh sets trip a signal. Residuals
  outside the sets: **M16** to **M18**.
- **P2:** met in code. The reading is at `Router.swift:49`, the boundary at `:590`, the table at
  `ReadingTests.swift:138` and the screen at `ContentView.swift:175`, `:839`, `:873-918`. Its UI half
  rests on R1; **M19** covers what the gates miss.
- **P3:** met. Three variants per problem (record §3). F and the B4 narrowing are review fixes for
  false positives, and both lowered the scores.
- **P4:** #73 met; #66 and #113 missed and recorded. They go to the owner.

## Every file in the diff

`git diff --stat 93040ac 5f0937b`: 89 files. I read every non-run file's diff in full, and the run
files by script.
1. **Records (6).**
   - `docs/decisions.md`: D-169 as on the issue branch, plus its amendment. Only additions. The
     amendment reverses D-169's "alternative not taken" and clause 3, in an AMENDED block that names
     each clause. The owner-approved milestone plan (§2 W3, items 2 and 3) authorizes the direction.
   - `docs/plans/m18-wave-3-plan.md`: matches the code and the record.
   - `docs/prd.md` (**M20**).
   - The research record (**M20**; otherwise re-scored and true).
   - `.language-allow`: each new path has a reason.
   - `.gitignore`: `.venv` (round 1's B1).
2. **Reviews (2).** Rounds 1 and 2, read last.
3. **The app (6).**
   - `Reading.swift` (**M16**, **M17**, **M18**).
   - `Router.swift`: descriptions, instructions, schema, boundary and `read`. `:712` is a dead store,
     overwritten at `:714`; it is harmless.
   - `ContentView.swift`: held state, `ask`, `apply`, `confirm`, `decline`, the card and `select`
     (**M19**).
   - `FrontDoor.swift`: `recordsGap`.
   - `Language.swift`: the four strings. They use "sen", as D-175 finding 7 asks.
   - `ScriptedRouting.swift`: passes `request` through the boundary, as D-175 clause 3 asks.
4. **Swift tests (4).**
   - `ReadingTests.swift`: 22 tests in two classes.
   - `RefinementBoundaryTests.swift`: the field, its values and `x-order`.
   - `ScreenPathTests.swift`: five held paths; `5f0937b` changed only doc comments.
   - `test-manifest.txt`: +22.
5. **Python gates (3).**
   - `test_ios_client_contract.py` (**M19**, **K6**).
   - `test_router_hints.py`.
   - `test_no_tracked_links.py`: still catches a tracked link.
6. **Probe and sets (10).**
   - `ReadingProbe.swift` (**M16**: the tier's own surface).
   - Nine sets: three fresh held-out, two retired held-out, four tuning.
7. **Runs (58).**
   - 56 run files: baseline, variants A to F, `final`, `final2`, `postfix`, and two tuning copies.
   - The two scorers. Each prints no question unless asked.

## K.8 contract drift check

`git grep -n` at `5f0937b`, for the plan's symbols (`m18-wave-3-plan.md:123-130`) and the wave's
own:
```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:49:    var reading: InputReading = .search
ios/ModelRanking/Engine/Router.swift:429:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:583:    static func outcome(
ios/ModelRanking/Engine/Router.swift:684:    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:12:enum InputReading: Equatable {
ios/ModelRanking/Engine/Reading.swift:26:enum InputSignals {
ios/ModelRanking/Engine/Reading.swift:296:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
ios/ModelRanking/Engine/FrontDoor.swift:338:func recordsGap(_ outcome: RoutingOutcome) -> Bool {
ios/ModelRanking/ContentView.swift:850:    private func apply(_ outcome: RoutingOutcome, typed: String, ticket: Int) async {
ios/ModelRanking/ContentView.swift:873:    private func confirm(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:887:    private func decline(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
```
Callers of `ModelOutputBoundary.outcome(` outside the tests:
```
ios/ModelRanking/Engine/Router.swift:506:        return ModelOutputBoundary.outcome(
ios/ModelRanking/Engine/ScriptedRouting.swift:26:        return ModelOutputBoundary.outcome(for: answer["surface"], within: known, refinements: refinements,
```
- `outcome` gained `request: String? = nil`, an additive default.
- `RoutingOutcome` gained one stored field, the closed `reading`, as D-169's amendment allows.
- No symbol changed between `53937c4` and the head.
- No `/v1` change.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K6** `tests/unit/test_ios_client_contract.py:186-187`. **The held-out gate scans only `.swift` and
  `.py` files.** A held-out question copied into a tuning `.json` set passes it. The tests read those
  sets (`ReadingTests.swift:157-160`), and the probe tunes on them. This is an enhancement: scan
  `scripts/router_probe/*.json` too, leaving out each live set itself.
- **K7** `docs/prd.md`. **No gate checks the PRD's `file:line` evidence.** One wave moved 15 citations
  without anyone seeing it (**M20**). This is an enhancement: a records check that each cited line is a
  test's declaration, or lies inside one.
- **K8** D-174 clause 2; `/close-wave` seat setup. **"Its own copy of the artifact" does not say which
  copy.** This seat had none at first (W-108). The owner checkout's `advisor.db` (2026-09-24) then
  failed `test_every_board_a_question_can_select_is_served`, because it predates the refinement boards.
  The served engine's copy (2026-10-01) passed. A seat that copies the stale file sees a red gate the
  wave did not cause. This is an enhancement to the seat setup: copy the served artifact, and say so in
  D-174.

## Risks queued to next M

- **R1** (carried) `ios/UITests/ScreenPathTests.swift:132-179`. **No seat has seen the held paths run,
  and no gate repeats them.** `2d5f86a` changed `Reading.swift` and `Router.swift`, which the scripted
  UI routes pass through, after the last UI run reported (`53937c4`). Three of my **M19** mutants are
  held only by UI tests, and one by nothing. What would show it is real: the Tester runs
  `make ui-test` at `5f0937b`.
- **R2** (carried, narrowed) `Reading.swift`; `Router.swift:704`. **On a phone without Apple
  Intelligence, the code signals are the whole reading.** The image rule now reaches only `vision`
  there too, but **M16** to **M18** reach it unchanged. What would show it is real: the genuine sets
  run through `TieredRouter(model: nil, …)`, counting notes, questions back and overrides.
- **R3** (carried, sharpened) `Router.swift:485-494`. **The model's "something else" alone asks genuine
  searches.** After the fix it asked 8 of the 40 image-set questions in run 1, 6 of them requests to
  read an image, and 3 and 2 of the 40 genuine not-a-search-set questions. The code asked none. What
  would show it is real: W6's stranger protocol (#91), with asks counted by class and by whose word.
- **R4** (carried, narrowed) `FrontDoor.swift:338`; `Router.swift:710`. **A false image override is
  kept in the owner's gap register as a need to build.** Only **M16**'s class remains. What would show
  it is real: the register on the owner's phone after a week, with its image entries read one by one.
- **R5** `docs/plans/m18-wave-3-plan.md:86`; D-169 clause 6 (`decisions.md:3353-3357`). **The owner's
  one question may be asked on the wrong numbers.** The plan and the ADR say only "whether to ship what
  holds". For the owner to decide, the pull request should say, in plain words:
  - #73 is met.
  - #66: no genuine search got the note, and 1 to 3 of 40 were asked. 19 to 21 of 40 non-searches
    were caught, against 32. Knowledge questions are the gap.
  - #113, for the code that ships: 7 of 15 requests to make an image are told "not measured", and 3
    get the `web-dev` ranking as if measured. 8 of 10 requests to read one reach `vision`, as before,
    but up to 6 of them only after a question.
  - Every genuine search that was asked was asked on the model's "something else" alone. That is one
    lever the owner can pull: if the model's verdict alone did not ask, no genuine search would be
    asked, and about 8 or 9 of the 20 catches would be lost (record §5).

  What would show it is real: a pull request whose question omits these numbers, or gives 10 of 15.
- **R6** `Reading.swift:129-173`; #113. **The image rule reads orders, not searches.** It catches "draw
  me a cat" and "generate a picture of …". It misses the way a model search is usually written:
  - "which model is best at generating images";
  - "which AI creates the best logos";
  - `resim üreten model hangisi`;
  - `görsel oluşturan yapay zeka`.

  The model also now sends 3 of 15 requests to make an image to `web-dev`, where the rule does not
  reach. This is what keeps #113 open. What would show it is real: #91's questions, with requests to
  make an image counted by the surface they reach.

*Filled by: Code-Reviewer seat, round 3 (independent) · Date: 2026-10-04 · Commit range: `93040ac..5f0937b`*
