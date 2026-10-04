---
record_type: review
id: m18-wave-3-rereview
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W3 Code Review, round 2: reading the question

**Reviewer:** a second Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or
records, and I am not the first reviewer.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `93040ac..53937c4`, 8 commits, 84 files. 54 of them are under
`docs/research/m18-w3-runs/`: 50 per-question run files, two copies of tuning sets and two scorers.
The fix round is `a35da0f..53937c4`: the fixes `55a1aef`, the fresh held-out sets `da48707` and the
fresh measure `53937c4`. `wave/m18-w3` is stacked on `wave/m18-w2`
(#116, head `93040ac`), so the range is W3's own change. It holds no merge.
**Risk tier:** HIGH (`docs/plans/m18-wave-3-plan.md:13-15`; `m18-plan.md` §3). D-172: no security
seat on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the base-ref policy, both
plans, D-169 with its amendment, D-126, D-147 and D-175, then the code diff and the research record,
and probed the code with my own inputs. Only then did I read the first review and the three fix-round
commit messages.

**Summary.** Most of round 1 is fixed, and the held-out discipline now holds:
- the `.venv` link is gone and gated (B1);
- the fresh sets landed after the last code change, no code that reads a question changed after them,
  and every number in the record's §2 to §5 re-scores exactly from the committed run files (B2);
- acronyms are words, and an instruction phrase is a doubt, not the note (B3);
- the reading enum is pinned, upper-case Turkish is read, and the held path is gated (M1, M2, M7).

Two things block:
1. **B4 (round 1), still open.** The image override still turns genuine coding, web-dev and
   image-reading searches into "not measured" and gap entries. Four of round 1's own 19 probe lines
   still do, among them one of the two it named in its summary. So does the held-out example it named,
   which now sits in a tuning set. Round 1's fix item 2, to override only a `vision` choice or a
   decline, was neither done nor dispositioned; my mutant of exactly that passes all 448 Swift tests.
   New classes fire too: Turkish `resmi` (official), Turkish `arka plan` with no verb, "draw a" and
   "turn a photo into".
2. **B5.** The records overstate what holds, and the owner's question will rest on them.
   - D-169's "Measured" bullet leaves out #113's second missed bar. Requests to read an image reached
     `vision` 8 and 8 times, against a bar of 9.
   - The record says "reading an image held" and "nothing measured got worse". In the run files, 3 and
     2 of those 8 now get the question back before any ranking.
   - The same model verdict asks 1 and 5 of the 80 genuine coding-set searches. No record reports
     either cost.

There are also seven MINORs (M9–M15), two K.9 candidates (K4, K5) and four risks (R1–R4).

**Policy.** I read `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md` from `93040ac`.
This is empty:
`git diff --stat 93040ac 53937c4 -- src .claude .agents .github AGENTS.md ios/ModelRanking/Engine/EngineClient.swift`.
`docs/decisions.md` only gains lines (0 removed). No commit in the range carries an attribution line, and all carry `GP-Task: M18-W3`.

**How I worked.** Everything ran in this seat's detached worktree at `53937c4`. The guard directory
was first on PATH, and Python ran with `PYTHONPATH` set to this tree's `src`.
1. **Gates at `53937c4`.** `make check-fast`: **PASS, rc 0**, six legs.
   - pytest: 1657 passed, 25 skipped.
   - lint, typecheck, records and `client-decls` (19 files, 4 configurations): PASS.
   - `swift test --parallel`: **448 tests**, exactly the manifest.
2. **Re-scoring.** I ran `score_reading.py` and `score_surfaces.py` on every run file against its set,
   then broke the fresh runs down by class, reading and `unmeasured` with a few lines of Python. I
   printed counts only. I opened neither fresh held-out set except through the scorers and the run
   files, and this file quotes no question from either.
3. **Probes.** A temporary Swift test of my own (`ZZReviewProbeCR2`, since deleted) did three things:
   - it ran 66 inputs of mine through the five signals;
   - it ran round 1's B3, B4, M7 and M8 probe lines through `TieredRouter`, with a scripted model that
     says "a model search" and names the right surface;
   - it counted which signals fire on the run files' questions, by class.

   A second temporary test ran the signals over the genuine rows of six tuning and off-topic sets.
4. **Mutants: 21,** each reverted by copying back the original and checked against the
   md5 sums I took before (`Reading.swift`, `Router.swift`, `ContentView.swift`, `ReadingTests.swift`,
   `.gitignore`, the three Python gates: all equal afterwards). The link mutant used a throwaway
   `GIT_INDEX_FILE`, so the real index was never touched. The table folds two `indirect` mutants into
   one row.

   | mutant | gate | result |
   |---|---|---|
   | a held-out question, quoted, in a test file | held-out gate | **caught** |
   | the same question inside a longer string | held-out gate | survives (**M13**) |
   | `await load()` in the held branch of `ask` | client contract | **caught** |
   | `routing = outcome` in the held branch | client contract | survives (**M9**) |
   | `ask`'s guard as `!= .notASearch` | client contract | **caught** |
   | `confirm` only hides the card | client contract | survives; UI test only (**M9**, R1) |
   | `confirm` without the in-flight guard | client contract | survives (**M9**) |
   | `decline` records a gap | client contract | survives (**M9**) |
   | `case said(String)` in `InputReading` | `test_router_hints` | **caught** |
   | `case unsure, said(String)` | `test_router_hints` | **caught** |
   | `indirect case said(String)` | `test_router_hints` | survives (**M10**) |
   | a computed `String?` on `RoutingOutcome`, or a static var on the enum | `test_router_hints` | survives; stores nothing, not a finding |
   | a tracked mode-`120000` `.venv` (temporary index) | `test_no_tracked_links` | **caught** |
   | `.venv` removed from `.gitignore` | `test_no_tracked_links` | **caught** |
   | image override removed from `TieredRouter.read` | Swift | **caught** (3 failures) |
   | small talk removed from the decision | Swift | **caught** |
   | the verdict generated first in the schema | Swift | **caught** (`x-order`) |
   | instruction phrases removed from `doubt` | Swift, full suite | survives, 448 of 448 pass (**M9**) |
   | override only when the tier chose `vision` or declined | Swift, full suite | 448 of 448 pass: round 1's B4 fix 2 breaks nothing (**B4**) |

5. **Not done, by this seat's rules:** no `xcodebuild`, `simctl` or simulator, so no `make ui-test`
   (**R1**). The on-device model was not run. No installer, `launchctl`, commit, push or GitHub write.
6. **Tree:** clean apart from this file. `git status --short` shows only it, and no tracked file
   differs from `53937c4`.

## Verdict
BLOCKING

**Two BLOCKING (B4 carried from round 1, B5 new), seven MINOR (M9–M15), two K.9 (K4, K5), four risks
(R1–R4).** B4 is the second BLOCKING verdict on the same finding; by `.agents/rules/practices.md`
("Three attempts, then stop"), a third would send it back to the owner. B5 is text plus one scorer
line, and the numbers it adds do not by themselves argue against shipping. After both, I would expect
a third review to pass with findings.

## Round 1, re-checked

| id | round 1 asked | at `53937c4` | evidence |
|---|---|---|---|
| B1 | untrack `.venv`; ignore a link; gate | **fixed** | `git ls-files -s` has no `120000` entry; `.gitignore:4`; `test_no_tracked_links.py:21`, `:27`, both caught by mutant |
| B2 | fresh held-out sets, run once; record corrected | **fixed** | sets in `da48707` (18:40) after the code in `55a1aef` (18:26); `git diff da48707 53937c4 -- ios/ModelRanking scripts/router_probe/*.swift` is empty; every §2 to §5 number re-scores exactly; record §4 restates the spoiled rows as tuning |
| B3 | acronyms are words; an instruction is a doubt; no skipped counter-example | **fixed**, with a residual (**M11**) | `Reading.swift:215`, `:240-247`; `ReadingTests.swift:66-71` has no `where`; round 1's acronym lines all read as a search through the tiers |
| B4 | narrow the image rule; override only `vision` or a decline; must-not-fire list of the 19 lines; report "image-other" | **not fixed** (**B4**) | items 1 and 4 done; item 2 not done and not mentioned in `55a1aef`; item 3 holds none of the 19 lines; 4 of the 19 still fire |
| M1 | pin `reading`'s type and the enum's bare cases | **fixed**, bypassable (**M10**) | `test_router_hints.py:295-306` |
| M2 | gate the held path; drive the override and the decide-alone path through the tiers | **partly** (**M9**) | held-branch pin `test_ios_client_contract.py:866-871`; override `ReadingTests.swift:238`; small talk `:230`; no instruction case through the tiers |
| M3 | guard `confirm`; a UI test that can fail; no "Showing" line while held | **fixed** in code | `ContentView.swift:876`, `:507-510`; `ScreenPathTests.swift:156-162` asserts the echo (not run here, R1) |
| M4 | REQ-ASK-005; carve-outs; tests cite it | **mostly** (**M15**) | `docs/prd.md:523-524`, `:544`; `ReadingTests.swift:1`; `ScreenPathTests.swift` cites no REQ-ID |
| M5 | plan amended; the owner asked in the pull request | **fixed** in the records | `m18-wave-3-plan.md:81`, `:112`; D-169 amendment, clause 6 bullet |
| M6 | verdict position; exemption reason; omitted rows; `nil` rows | **fixed**, one residual (**M14**) | `Router.swift:432-434`, `:549`; `RefinementBoundaryTests.swift:134`; `.language-allow`; record §5 rows 92, 95 |
| M7 | fold both ways | **fixed** | `Reading.swift:201-203`; my probe reads all four of round 1's upper-case lines |
| M8 | a noun before a colon is not a verb; the six lines must not fire | **partly** (**M12**) | five of six pass; "Best model to explain code: Claude or GPT?" is still asked |
| K1 | gate on tracked links | **done** | `test_no_tracked_links.py` |
| K2 | gate on held-out text and phrases | **half** (**M13**) | whole quoted questions only; the phrase half is neither built nor filed in any record I can see |
| K3 | commit per-question runs and scorers | **done** | `docs/research/m18-w3-runs/`: 50 run files and 2 scorers |
| R1–R3 | risks | carried, below | — |

## Findings

### BLOCKING (must fix before this wave closes)

- **B4** (round 1, still open) `ios/ModelRanking/Engine/Router.swift:708-711`;
  `ios/ModelRanking/Engine/Reading.swift:108-163`; `ios/EngineTests/ReadingTests.swift:112-117`,
  `:139-141`. **The image override still sends genuine coding, web-dev and image-reading searches to
  "not measured" and the gap register.**

  `TieredRouter.read` still replaces whatever the tier chose whenever `makesAnImage` fires, `coding`
  and `web-dev` included. Round 1's fix item 2 ("Override only when the tier chose `vision` … Never
  override `coding` or `web-dev`") is not in the code, and `55a1aef` does not say why. Round 1's 19
  probe lines, through `TieredRouter` with the model naming the right surface:
  ```
  which model can turn a photo of a receipt into a spreadsheet   vision  -> assistant, unmeasured, gap
  fix image upload in django                                     coding  -> assistant, unmeasured, gap
  remove duplicate photos with a python script                   coding  -> assistant, unmeasured, gap
  how to make a background image responsive in CSS               web-dev -> assistant, unmeasured, gap
  (the other 15: routed as chosen)
  ```
  The held-out example round 1 named, "how do i make images lazy load on my site so the page loads
  faster" (`web-dev|coding`), still fires. It now sits in `image_heldout_first_questions.json`, a
  tuning set. So P1's acceptance as amended, "none fires on a genuine question in the tuning sets"
  (`m18-wave-3-plan.md:112`), is not met. `testNoGenuineTuningQuestionTripsASignal` cannot see it,
  because its list (`ReadingTests.swift:139-141`) leaves out the image and not-a-search tuning sets.
  The must-not-fire list (`:112-117`) holds none of round 1's 19 lines verbatim. It holds variants
  of four that now pass, and none of the four that still fire.

  The narrowing also left whole classes. My probe, model naming the right surface:
  ```
  Hangi model resmi yazıları düzeltebilir?                  ("official texts")    -> unmeasured, gap
  React'te arka plan resmi nasıl eklenir                    (CSS background)      -> unmeasured, gap
  fotoğrafın arka planında ne yazıyor, hangi model okur     (reading a photo)     -> unmeasured, gap
  Which model can turn a photo into text?                   (OCR)                 -> unmeasured, gap
  Which model can draw a conclusion from survey data?                             -> unmeasured, gap
  fix the image upload in my Django app                                           -> unmeasured, gap
  create an image classification model in PyTorch / make my image classifier more accurate
  design a photo gallery page for my website / create a photo gallery website
  generate image descriptions for accessibility / Which model can generate image captions for my shop?
  Which model can draw a chart with matplotlib? / Hangi model matplotlib ile grafik çizebilir?
  ```
  The causes:
  1. **Turkish `resm`** (`:160`) is a prefix stem, so `resmi` ("official", one of the commonest
     Turkish adjectives) and `resmen` count as an image.
  2. **The Turkish background rule needs no verb** (`:113-118`). `arka` plus `plan…` plus any image
     noun fires. The comment above it says "A background removed or replaced", which is the English
     half's rule.
  3. **An image noun used as a modifier** ("image upload", "photo gallery", "image classifier",
     "image captions") counts as the object of a making verb (`:123-126`).
  4. **"draw" before "a", "me", "my" or "some"** (`:121`) is an idiom as often as a picture ("draw a
     conclusion", "draw some insights").

  The independent sets did not show these: across the 145 genuine questions of the three held-out
  sets, the rule fired on none (my count by class). The classes above are ordinary product input,
  though, and half of it is Turkish. Each one is told something false ("not measured") and is kept as
  a need to build. The rule also runs on the wording tier, so it reaches every device (R2).

  **The fix:**
  1. Do round 1's item 2: override only when the tier chose `vision` or declined. My mutant of exactly
     that passes all 448 Swift tests. On the fresh set's baseline runs, 14 and 13 of the 15 requests to
     make an image went to `vision`, so the catch should hold. `ReadingProbe.swift` records only the
     overridden surface; record the tier's own choice too, so the run files can show it.
  2. Require a verb of removing or changing beside `arka plan`, as the English half does. Drop the
     bare `resm` prefix, since `resmi` is also "official": match the forms of `resim` (`resmini`,
     `resimler`), and `resmi` only right before a making verb (`kedi resmi çiz`), or accept that miss.
  3. Do not count an image noun that modifies the next word ("image upload", "photo gallery", "image
     classifier"); a short list of such heads will do, and fix 1 already removes most coding and
     web-dev cases. Drop "draw a" and "draw some", and keep "draw me".
  4. Put round 1's 19 lines and the lines above in the must-not-fire list. Add the image and
     not-a-search tuning sets to `testNoGenuineTuningQuestionTripsASignal`, so the lazy-load question
     is seen.

- **B5** `docs/decisions.md:3359-3362` (D-169 amendment, "Measured");
  `docs/research/m18-w3-question-reading-probe-2026-10-04.md:91`, `:116-118`, `:132-133`;
  `docs/research/m18-w3-runs/score_surfaces.py`. **The records overstate what holds, and the owner's
  question will be asked on them.**

  D-169 clause 6, as amended, says that where a bar is missed, "the wave's pull request asks the
  owner one plain question, whether to ship what holds". What holds is therefore what the records
  say. Re-scored from the committed run files:
  1. **#113 misses both of its bars, not one.** The plan's bars are 11 of 15 made and 9 of 10 read
     (`m18-wave-3-plan.md:59-60`). The fresh runs give 10, 10 and 8, 8. The plan (`:77-78`) and the
     record's §5 table (`:91`) say so. D-169's "Measured" bullet gives only the first (`:3362`), and
     the record's §6 headline is "misses its bar by one" (`:116`).
  2. **A new cost on genuine searches is not reported.** The model's "something else" alone is a
     question back (`Reading.swift:244`). It asks genuine searches on every held-out set, not only the
     one the bound was counted on:

     | held-out set | genuine | asked, run 1 | asked, run 2 | source |
     |---|---:|---:|---:|---|
     | not a search (fresh) | 40 | 1 | 2 | record §5, as reported |
     | image (fresh): to read an image | 10 | 3 | 2 | `final2-image_heldout_m18_questions-*.json`, `reading: unsure`, all `model: not` |
     | image (fresh): only mentions images | 15 | 0 | 1 | same |
     | coding, at `4373dae` | 80 | 1 | 5 | `final-coding_heldout_m18_questions-*.json`, all `model: not` |

     The model's instructions are unchanged between `4373dae` and the head:
     `git diff 4373dae 53937c4 -- ios/ModelRanking/Engine/Router.swift` touches one comment and the
     `read` call. So the coding row stands for the head. It is the model's verdict, not the code's: my count of the code
     signals on all three sets' genuine questions at the head is zero.
  3. **So "reading an image held" (`:133`) and "Nothing measured got worse than the baseline"
     (`:132`) are not what the runs show.** All 8 of the baseline's image-reading answers came without
     a question. At the head, 5 and 6 of 10 are answered directly; 3 and 2 more reach `vision` only
     after "Did you mean to find a model for this?". `score_surfaces.py` counts a surface whatever the
     reading, which is how a question back scored as a ranking.

  In aggregate the asked rate is about 3 and 7 in 100 genuine searches (5 and 10 of 145), inside
  the 10 in 100 that the bound of 4 in 40 implies. So the numbers do not argue against shipping. What
  blocks is that the ADR, the record and the pull request would put a smaller cost before the owner
  than was measured.

  **The fix:**
  1. D-169's "Measured" bullet: add "requests to read an image reached `vision` 8 and 8 times against
     9, as at the baseline" and the asked counts above.
  2. Record §5: add an asked row per set (the table above), and split "reading `vision`" into
     answered and asked. §6: "#113 misses both bars". §7: replace "nothing measured got worse" with
     the trade as measured.
  3. Make `score_surfaces.py` print the asked and noted count per class, so every set is scored for
     the false-positive cost and not only the not-a-search set.
  4. The pull request's question names the asked cost beside the catch shortfall.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M9** `ios/ModelRanking/Engine/Router.swift:714`; `tests/unit/test_ios_client_contract.py:866-871`;
  `ios/ModelRanking/ContentView.swift:873-891`. **Round 1's M2, residual: three guarantees are still
  held by no gate that runs without a simulator.**
  1. **The instruction doubt through the tiers.** With `InputSignals.instructsTheApp(question)`
     removed from `doubt`, all 448 Swift tests pass. Round 1 asked for "a case for an instruction the
     model calls a search" in `ReadingThroughTheTiersTests`; small talk got one, the instruction did
     not. Only `ScreenPathTests.swift:169` holds it.
  2. **The held branch's pin forbids `load(`, `client.`, `gaps.`, `recordsGap`, `task =` and
     `apply(`, but not `routing = outcome`.** That mutant passes, and it would put the routed
     surface's notice and alternative buttons under the note (`ContentView.swift:531-555`), which is
     what D-169 clause 4 rules out.
  3. **`decline` and `confirm` are unpinned.** A `decline` that records the gap, a `confirm` without
     the in-flight guard, and a `confirm` that only hides the card all pass every Python gate. Only
     the last is caught, by a UI test no gate runs (R1).

  **The fix:** add the tier test; forbid any `routing =` other than `nil` in the held branch; pin
  `decline`'s body to the two assignments and `confirm`'s to its guard and `apply`.

- **M10** `tests/unit/test_router_hints.py:303`. **M1's enum pin misses `indirect` cases.** The
  pattern `^\s*case\s+(.+)$` does not see a line starting `indirect case`, so
  `indirect case said(String)` compiles and passes. **The fix:** match `^\s*(?:indirect\s+)?case\s+`, or refuse
  `indirect` and `(` anywhere in the enum.

- **M11** `ios/ModelRanking/Engine/Reading.swift:61-65`, `:73-81`. **The instruction phrases ask
  ordinary searches back, and the comment says they cannot.** The comment reads "Each phrase is
  specific: a search for a model that follows instructions well uses none of them". My probe asked
  back all of these:
  - "Which model follows your instructions best?" and "which model best follows your instructions"
    (round 1's B3 line);
  - "a model that remembers previous instructions in long chats";
  - "model that sticks to your system prompt";
  - "a model that doesn't forget everything after a few messages";
  - "which model can ignore your typos and still understand";
  - `Linux'ta bir sistem komutunu açıklayabilecek model hangisi`;
  - `uzun sohbetlerde önceki talimatları unutmayan bir model`;
  - `sistem istemini iyi takip eden model`.

  Each is a doubt (B3's chosen fix), so it costs a tap, and it counts against the bound of 4. The
  test's counter-examples (`ReadingTests.swift:67-69`) pick the forms that do not fire ("follows
  instructions well", the plural `sistem komutlarını`). **The fix:** tie the bare noun phrases ("your
  instructions", "previous instructions", "your system prompt", `sistem komutunu`,
  `önceki talimatları`) to an imperative beside them ("ignore", "forget", "print", `unut`, `yazdır`),
  or keep them and correct the comment. Either way, add these lines to the test as must-not-fire or as named
  doubts.

- **M12** `ios/ModelRanking/Engine/Reading.swift:44-59`, `:167-171`. **Round 1's M8, residual.** "Best
  model to explain code: Claude or GPT?" is still asked; it was one of M8's six lines, and the test
  holds forms of the other five. The same shape asks other searches back: "Best model to summarize: long
  PDFs", "Which model is best to translate: legal contracts or medical papers?", "I want a model to
  write: blog posts and newsletters". **The fix:** M8's option 2, a verb counts only where the text
  before the colon starts with it (after an optional `şunu`, `bunu`, "please" or "can you"). Add the
  four lines.

- **M13** `tests/unit/test_ios_client_contract.py:165-191`. **The held-out gate was weakened in
  `da48707`, and K2's other half is not accounted for.**
  1. It now matches only a whole quoted string. A held-out question inside a longer string passes (my
     mutant). The reason given is a chance overlap: one fresh question of 20 characters is the tail
     of a tuning example older than the fresh set (`ReadingTests.swift:61`). That overlap is a
     coincidence: the fresh question holds none of the signal phrases, so nothing leaked through it.
     It could be named in an allow-list by file and length instead.
  2. K2 also asked for a gate on "a phrase that occurs only in a held-out set", the form B2's leak
     took. It is neither built nor filed in any record in the range.

  **The fix:** substring match with a named allow-list; build the phrase check or file it.

- **M14** `docs/research/m18-w3-question-reading-probe-2026-10-04.md:19-26`, `:44-52`, `:96`, `:124-128`.
  **Record slips.**
  1. **Stale names.** §1 still lists `image_heldout_questions.json` and
     `notasearch_heldout_questions.json` as "Held out, run once at the end". Both were renamed and
     retired.
  2. **Variant F is missing.** §6 compares the fixes with variant E "on the tuning sets" without a
     number, and §3 stops at E. The `vF-*` runs show the following:
     - tuning: 22 and 23 caught (12 and 13 noted), 0 noted / 7 and 7 asked of 110;
     - images: 6, 6 made and 4, 4 read;
     - the retired first image set: 12, 12 made and 10, 10 read;
     - the retired not-a-search set: 27 and 24 caught, 1 and 0 asked.

     §6's "three variants were run per problem" also needs one line on F, the review's fix, as a
     fourth change to #66's and #113's code measured on tuning.
  3. **`nil` rows.** Every §3 tuning run has one genuine `assistant` row where the model answered
     nothing, scored as a search (C has an ambiguous one as well). §5 has none, and says so; §3 does
     not say it.
  4. **The fresh baseline.** "0, 0" for the not-a-search set (`:96`) is true of the note. But the
     baseline declined 5 and 7 of those 40 (chit-chat and injections), the measure the plan's own
     first baseline used (`m18-wave-3-plan.md:50`). Give both.

- **M15** `docs/prd.md:542` (REQ-IMG-003), `:460` (REQ-RTR-005); `ios/UITests/ScreenPathTests.swift`.
  **PRD rows the wave's measure touches.**
  1. REQ-IMG-003 says "The refusal half holds on its own: a request to make an image is answered as
     unmeasured". This wave measured that half at 0 of 15 at the baseline and 10 of 15 now.
  2. REQ-RTR-005, which the milestone's W3 row names (`m18-plan.md:32`), gains no evidence.
  3. Round 1's M4 asked `ScreenPathTests.swift` to cite REQ-ASK-005. The PRD row cites five of its
     lines, and the file cites no REQ-ID.

  **The fix:** restate REQ-IMG-003's note with #113's measure and its open state. Add the image rule's
  tier test (`ReadingTests.swift:238`) to REQ-RTR-005's evidence. Add the citation.

### PASS (what looks good)

- **The held-out discipline now holds, and the numbers are true.**
  - The fresh sets landed after the fixes. No code that reads a question changed after them.
  - The fresh sets are in the gate's live list.
  - The scorers reproduce every number in §2, §3 (A to E), §4 and §5 from the committed runs, including
    the class split (21 and 20) and the genuine-surface rows (28, 29 against 24, 26).
  - All 90 and 40 questions of each fresh run are rows of the set, none twice.
  - The signals fire on the fresh sets by class as follows:
    - instructions 4 of 10;
    - pasted content 5 of 10;
    - small talk or no word 3 of 10;
    - making an image 10 of 15;
    - genuine searches 0.

    That is the shape of an untuned set.
- **B1 and K1.** No tracked link; `.venv` ignored either way; both halves of the gate fail on their
  defect.
- **B3.** `noWord` reads acronyms as words (`Reading.swift:215`), and a single instruction phrase is a
  doubt (`:240-247`). Round 1's acronym lines, its "talimat" lines and "a model that can respond only
  with JSON" all read as a search. The `where` clause is gone.
- **M1, M3, M5, M6, M7.**
  - The reading's type and bare cases are pinned.
  - `confirm` waits for a question in flight, and no surface line shows while a reading is held.
  - The verdict's position is pinned by `x-order` (caught by my mutant).
  - Both case foldings work (`ÖNCEKİ TALİMATLARI UNUT`, `BANA BİR KEDİ ÇİZ`, `İYİ GECELER` all
    read).
  - The plan and D-169 describe the decide-alone signals and the owner's question.
- **D-126 holds.** The model's verdict is one closed field mapped only by `ModelOutputBoundary`
  (`Router.swift:590`). The note and the question are the app's own sentences
  (`Language.swift:672-693`). `/v1` is unchanged, and nothing typed reaches the engine.
- **Small and clean.** No `noqa` or `type: ignore` was added. The sort permit names one reversed
  keyboard row. The manifest grew by exactly the new Swift tests (448).

## Producers of hardened invariant(s)

| producer | invariant | citing test | gap |
|---|---|---|---|
| `ModelOutputBoundary.outcome(…, request:)` (`Router.swift:583-605`) | the verdict is one of two closed values; anything else is no verdict (D-126, D-169) | `ReadingTests.swift:179`; `RefinementBoundaryTests.swift:131-134` | none |
| `RoutingOutcome.reading`, `InputReading` (`Router.swift:49`; `Reading.swift:12-19`) | the outcome carries no text | `test_router_hints.py:295-306` | `indirect` cases (**M10**) |
| `TieredRouter.read`, decision (`Router.swift:712-715`), every tier (`:688`, `:691`, `:697`) | code signals decide on every tier | `ReadingTests.swift:193`, `:200`, `:207`, `:215`, `:221`, `:230` | the instruction doubt (**M9**) |
| `TieredRouter.read`, image override (`:708-711`) | a request to make an image is unmeasured (#113), and nothing else is | `ReadingTests.swift:238` (catch); `:103-119` (signal) | false positives on genuine searches (**B4**) |
| `ContentView.ask` held branch (`ContentView.swift:839-844`) | a held reading sends no request and keeps no gap (D-169 cl. 4, 5) | `test_ios_client_contract.py:866-871`; `ScreenPathTests.swift:132`, `:146`, `:169`, `:175` (local) | `routing =` (**M9**) |
| `confirm`, `decline` (`:873-891`) | the reader's tap answers as routed, or gives the note, and nothing else | `ScreenPathTests.swift:153` (local) | unpinned (**M9**, R1) |
| `recordsGap` (`FrontDoor.swift:338`) | only a search is kept | `ReadingTests.swift:252` | none |
| `InputSignals.*` (`Reading.swift:26-231`) | no genuine search trips a signal | `ReadingTests.swift:136` (six genuine sets) | image and not-a-search tuning sets unchecked (**B4**); residual classes (**B4**, **M11**, **M12**) |

## Acceptance criteria evidence

Per phase, against `m18-wave-3-plan.md:111-115`:
- **P0** → the plan, D-169 (`docs/decisions.md:3270`), the sets and the baseline
  (`m18-wave-3-plan.md:44-51`). Met. B1 is fixed.
- **P1 (#66)** → each signal tested on its own (`ReadingTests.swift:12`, `:20`, `:28`, `:42`, `:57`,
  `:74`, `:84`, `:91`, `:103`); the named colon exception (`:162`). **Not met as written:** a genuine
  tuning question trips the image rule, and the test that should see it leaves that set out (**B4**).
- **P2 (#66)** → the reading (`Router.swift:49`), the boundary (`:590`), the decision table
  (`ReadingTests.swift:123`), the screen (`ContentView.swift:175`, `:839`, `:873-918`), UI tests
  (`ScreenPathTests.swift:132-179`). Met in code, with **M9**; the UI half rests on R1.
- **P3 (#73, #113)** → `Router.swift:70-85` (descriptions), `:462-494` (instructions),
  `Reading.swift:108` (images). Variants A to E in §3; F unrecorded (**M14**).
- **P4** → record §4 and §5, re-scored.
  - #73: met, 34 and 30 of 40, on a clean set.
  - #113: both bars missed (**B5**).
  - #66: false-positive bound held on its set; catch bar missed.
- **Milestone W3** (`m18-plan.md:32`): REQ-ASK-005 exists (`docs/prd.md:524`) and is cited
  (`ReadingTests.swift:1`). REQ-ASK-003 has its carve-out. REQ-RTR-005 has no new evidence (**M15**).
  "Measured twice on a set written independently": now true for all three problems.

## Every file in the diff

`git diff --stat 93040ac 53937c4`, 84 files. I read every non-run file's diff in full. I read the run
files by script.
1. **Records (6).**
   - `docs/decisions.md` (**B5**).
   - The wave plan.
   - `docs/prd.md` (**M15**).
   - The research record (**B5**, **M14**).
   - `.language-allow`: each new path with its reason.
   - `.gitignore` (B1 fixed).
2. **Reviews (1).** `docs/reviews/m18-wave-3-review.md`, round 1, read last.
3. **The app (6).**
   - `Reading.swift` (**B4**, **M11**, **M12**).
   - `Router.swift`: hints, instructions, schema, boundary and `read` (**B4**). `:710` is a dead
     store, overwritten at `:712`.
   - `ContentView.swift`: held, ask, apply, confirm, decline and the card (**M9**).
   - `FrontDoor.swift`, `Language.swift`, `ScriptedRouting.swift`: as described.
4. **Swift tests (4).**
   - `ReadingTests.swift` (**B4**, **M11**).
   - `RefinementBoundaryTests.swift`: the field, its values and its order.
   - `ScreenPathTests.swift`: five paths. The instruction path was corrected to the question back in
     `53937c4`, after the measure; at `55a1aef` it still expected the note, where the code asks, so it
     would have failed there.
   - `test-manifest.txt`: +20.
5. **Python gates (3).**
   - `test_ios_client_contract.py` (**M9**, **M13**).
   - `test_router_hints.py` (**M10**).
   - `test_no_tracked_links.py`.
6. **Probe and sets (10).**
   - `ReadingProbe.swift` (**B4** fix 1).
   - The coding, image and not-a-search sets, three of them retired by rename.
7. **Runs (54).**
   - Baseline, variants A to F and the final runs.
   - `reading_tuning.json` and `coding_tuning_all.json`.
   - The two scorers (**B5**).

## K.8 contract drift check

`git grep -n` at `53937c4`, for the plan's symbols (`m18-wave-3-plan.md:117-124`) and the wave's
own:
```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:429:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:583:    static func outcome(
ios/ModelRanking/Engine/Router.swift:684:    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:12:enum InputReading: Equatable {
ios/ModelRanking/Engine/Reading.swift:26:enum InputSignals {
ios/ModelRanking/Engine/Reading.swift:240:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
ios/ModelRanking/Engine/FrontDoor.swift:338:func recordsGap(_ outcome: RoutingOutcome) -> Bool {
ios/ModelRanking/ContentView.swift:850:    private func apply(_ outcome: RoutingOutcome, typed: String, ticket: Int) async {
ios/ModelRanking/ContentView.swift:873:    private func confirm(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:887:    private func decline(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
```
- Since round 1, only `inputReading`'s parameters changed: `pasted:` and `certain:` became
  `smallTalk:` and `doubt:`. It has one caller (`Router.swift:712`) and one test.
- `RoutingOutcome` still gains one stored field, as D-169's amendment allows.
- No `/v1` change.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K4** `scripts/router_probe/offtopic_questions.json`, `offtopic_heldout_questions.json`.
  **The off-topic sets predate D-169.** They label "hello", "good morning" and "thanks" as
  `assistant|everyday~`. Under D-169 they now get the note, so a later probe that scores those sets
  will count a right answer as a miss. `offtopic_heldout_questions.json` was also run in M13 and M16,
  yet the held-out gate treats it as live. This is a bug in the sets' labels: relabel them, and move
  the file to the gate's retired list.
- **K5** this seat's worktree; D-174 clause 2. **A review seat's `.venv` is a link to another seat's
  virtual environment.** Here it points to the W2 tree's. D-174 says each seat has its own venv.
  Nothing broke, because `pyproject.toml` was backdated and no install ran. A reinstall, though, would
  have written into another seat's tree, the cross-seat effect D-174 exists to stop. This is an
  enhancement to the seat setup in `/close-wave`: give each seat its own venv, or make the link
  read-only.

## Risks queued to next M

- **R1** (round 1, carried) `ios/UITests/ScreenPathTests.swift:132-179`. **The screen's held paths
  rest on a UI run no seat has seen and no gate repeats.** `53937c4` says `make ui-test` passed (15
  tests); the instruction path's test still expected the note at `55a1aef`, which shows how this goes
  unnoticed. Four of my screen mutants (M9) pass every gate that runs without a simulator, and only one
  of them would fail a UI test. What would show it is real: the Tester runs
  `make ui-test` at the fixed head, and once with `confirm` reduced to `self.held = nil`.
- **R2** (round 1, carried) `Reading.swift`; `Router.swift:704`. **On a phone without Apple
  Intelligence the code signals are the whole reading,** and B4's override reaches it unchanged. What
  would show it is real: the genuine sets run through `TieredRouter(model: nil, …)`, with notes,
  questions back and overrides counted.
- **R3** (round 1, carried, sharpened) `Router.swift:485-494`. **The model's "something else" asks
  genuine searches on every set:** 1 and 2 of 40, 3 and 3 of 25, 1 and 5 of 80 (B5). On the fresh
  not-a-search set it said "something else" 13 and 15 times in 90, and only 12 and 11 of those were
  not-a-search inputs. What would show it is real: W6's stranger protocol (#91),
  run once at the head, with asked counts by class.
- **R4** `FrontDoor.swift:338`; `Router.swift:708-711`. **Every false image override is kept in the
  owner's gap register as a need to build** (B4). The register is what tells him which surface to add
  next, so a coding question misread as an image request is a wrong signal in his roadmap, not only a
  wrong screen. What would show it is real: the register on the owner's phone after a week, with its
  image entries read one by one.

*Filled by: Code-Reviewer seat, round 2 (independent) · Date: 2026-10-04 · Commit range: `93040ac..53937c4`*
