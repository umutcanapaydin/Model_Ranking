---
record_type: review
id: m18-wave-3-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W3 Code Review: reading the question

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `93040ac..6a8038e`, 4 commits, 25 files, +1421 / -22. `wave/m18-w3` is stacked on
`wave/m18-w2` (#116, head `93040ac`), so this range is W3's own change. It holds no merge.
**Risk tier:** HIGH (`docs/plans/m18-wave-3-plan.md:13-15`; `m18-plan.md` §3). The wave changes what
the on-device model may answer, `RoutingOutcome` (D-126) and the screen, and it touches
`ios/ModelRanking/Engine/Router.swift`, a security glob. D-172: no security seat on the wave; this
seat checked the fail direction of every gate the wave touched instead.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat)
**Fresh context:** I started with none of the authoring context. I read the base-ref policy first,
then both plans and D-169 with its amendment, then the code diff, then the research record. Only after
that did I read the issues and the last commit's message. The one-line commit subjects were visible in
`git log` from the start.

**Summary.** The plumbing is sound:
- the model's verdict is one closed field, mapped only by the boundary, and anything outside it counts
  as no verdict;
- the held reading's guard and the gap rule are pinned;
- #73's gain is measured on a clean held-out set.

Four things block:
1. **B1.** The range commits `.venv`, a link into the author's worktree. Merging it silently deletes
   the owner's virtual environment and breaks the engine deploy.
2. **B2.** The held-out measures for #66 and #113 are not held out.
   - `ReadingTests.swift` asserts three held-out questions word for word.
   - 11 of the 27 instruction phrases occur only in the held-out set.
   - Without the stems found only in the held-out set, the image rule catches 5 or 6 of 15 held-out
     requests. The bar is 11; the record reports 14.
3. **B3.** Two code signals give the note alone, with no question back, and both fire on genuine
   searches:
   - an instruction phrase anywhere, such as "talimat", "system prompt" or "stay in character";
   - any input whose words have no vowel, such as "HTML", "HTML CSS" or "GPT-4 vs GPT-5".

   The test lists the Turkish example `talimatları iyi takip eden bir model` and then skips it with
   `where !text.contains("talimat")`.
4. **B4.** The image override replaces whatever the tier chose, and its prefixes reach far:
   - "yap" matches "yapay", as in "yapay zeka";
   - "arka" matches every "arka-" word;
   - `çiz` matches `çizelge`.

   All 19 of my probes of genuine searches (reading an image, coding, web development) were told "not
   measured" and kept as gaps. Two examples: `fotoğraftaki yazıyı okuyan yapay zeka` and "how to make
   a background image responsive in CSS". The held-out set's own "image-other" group shows one such
   case, and the record leaves that group out.

There are also eight MINORs (M1–M8), three K.9 candidates (K1–K3) and three risks (R1–R3).

**Policy.** I read `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md` from `93040ac`,
and D-147 from `93040ac:docs/decisions.md`. `git diff --stat 93040ac 6a8038e -- src .claude .agents
.github permission-matrix.md Dockerfile fly.toml AGENTS.md ios/ModelRanking/Engine/EngineClient.swift`
is empty. `docs/decisions.md` only gains lines (88 added, 0 removed). D-169 is the issue-66 branch's
text, verbatim (I diffed the two), with an amendment appended.

**How I worked.** Everything ran in this seat's detached worktree at `6a8038e`. Python ran with
`PYTHONPATH` set to this tree's `src`, and the guard directory was first on PATH.
1. **Gates at `6a8038e`.** `make check-fast`: **PASS, rc 0**, six legs.
   - pytest: 1654 passed, 25 skipped; coverage floor PASS.
   - lint, typecheck and records: PASS.
   - `client_decl_gate.py`: PASS, 19 files in 4 configurations.
   - `swift test --parallel`, judged by the xunit gate: **444 tests**, exactly the manifest.
2. **Probes.** I wrote a temporary Swift test, `ios/EngineTests/CRProbeTests.swift`, and deleted it
   afterwards. It did three things:
   - it ran 49 inputs of my own through `TieredRouter`, with a scripted model that says "a model
     search" and names the expected surface;
   - it ran every question in `scripts/router_probe/*.json` through the five code signals;
   - it checked what the image override keeps.

   Results are under B3, B4 and M7. I reimplemented `makesAnImage` in Python (it gives the same 14 of
   15) to count what the rule catches without the held-out-only stems (B2).
3. **Mutants: 7 in-place edits in 5 runs,** reverted in place and checked against the md5 sums I
   took before.
   - **3 were caught.** `recordsGap` without `reading == .search` and the boundary mapping "something
     else" to `.search` fail five `ReadingThroughTheTiersTests`. `ask`'s guard as
     `!= .notASearch` fails the contract pin.
   - **4 survived, and they are findings:**
     - `InputReading` gaining `case said(String)` passes every gate (**M1**);
     - the held path calling `load()` and `gaps.record(typed)` passes every gate (**M2**);
     - the image override removed from `TieredRouter.read` and `certain:` forced to `false` there,
       run together: all 444 Swift tests pass (**M2**).
4. **The `.venv` link.** I reproduced it in a throwaway repository under the scratchpad, since
   deleted (**B1**).
5. **Read only:** issues #66, #73 and #113, and the branches `enhancement/issue-66-not-a-model-search`
   and `fix/issue-73-coding-routing`.
6. **Not done, by this seat's rules:** no `xcodebuild`, `simctl` or simulator, so no `make ui-test`
   (**R1**). The on-device model was not run. There was no installer, `launchctl`, commit, push or
   GitHub write.
7. **Tree:** clean apart from this file. `git status --short` shows only this file, and
   `git diff --quiet` passes.

## Verdict
BLOCKING

**Four BLOCKING (B1–B4), eight MINOR (M1–M8), three K.9 (K1–K3), three risks (R1–R3).** B1 is one
line to remove. B3 and B4 are word-list and rule fixes, each with a test. B2 is a record correction
plus a fresh held-out run, or the owner's explicit ruling to ship without one. After those, I would
expect a re-review to pass with findings.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `.venv` (added in `71ffe5f`, mode `120000`, target `../w18-2/.venv`); `.gitignore:2`;
  `scripts/install_engine_service.sh:114-118`. **The wave commits the author's virtual-environment
  link, and merging it destroys the owner's.**

  `.gitignore` says `.venv/`. The trailing slash matches only a directory, so a link is not ignored
  (`git check-ignore .venv` returns 1), and the P0 commit picked it up. It is not at `93040ac`.
  Two things break once it reaches `main`:
  1. **The owner's checkout.** I reproduced this in a scratch repository: an ignored `.venv/`
     directory holding `bin/python`, then a merge of a branch that adds this link. The result:
     ```
     merge rc=0
     after:  .venv -> ../w18-2/.venv
     ls: .venv/bin: No such file or directory
     ```
     Git treats ignored files as expendable, so the merge deletes the owner's environment without a
     word and leaves a dangling link. Every `make` target, `scripts/engine_service.sh:57`, `:75` and
     `scripts/ui_test.sh:21` then fail.
  2. **The deploy.** `deploy()` extracts `git archive origin/main` into the release folder, so the
     dangling link comes with it. It then runs `python -m venv "$rel/.venv"`. On an archive that
     holds the link:
     ```
     venv failed: FileExistsError [Errno 17] File exists: '.../rel/.venv'
     ```
     So the installer stops at "FAIL: the release's venv".

  It is also a drive-by outside the plan's P0 list (`m18-wave-3-plan.md:98`).

  **The fix:**
  1. `git rm --cached .venv`.
  2. Change the ignore line to `.venv` (no slash), so a link is ignored too.
  3. K1 covers a gate for this.

- **B2** `ios/EngineTests/ReadingTests.swift:3-4`, `:71`, `:74`; `ios/ModelRanking/Engine/Reading.swift:60-67`,
  `:99-109`; `docs/research/m18-w3-question-reading-probe-2026-10-04.md:19-26`, `:62-74`;
  `docs/decisions.md` (D-169 "As built and measured"). **The #66 and #113 held-out measures are not
  held out (D-147 clause 5).**

  D-147 clause 5 reads "the held-out set is never tuned against". Its 2026-09-22 amendment records
  the last breach: one example copied from a held-out set. The plan (`m18-wave-3-plan.md:35-41`,
  `:55`) and the record (`:19-26`) both say the three sets were held out and run once, at the end.
  The code and the tests show otherwise.

  1. **The not-a-search set, direct evidence.**
     - The test file's header says "The examples are the TUNING sets', never the held-out sets'".
       Yet `ReadingTests.swift:71` and `:74` assert three questions that occur in
       `notasearch_heldout_questions.json` and in no tuning set: "hey, how are you doing today?",
       "test test 123" and "thanks, that was really helpful!".
     - Of the 27 instruction phrases, 11 occur in the held-out set and in no tuning set or test.
       I checked every `.json` in `scripts/router_probe` except the three held-out sets. Each of
       the 11 matches one held-out injection row:

       | phrase | held-out | tuning |
       |---|---:|---:|
       | `your instructions`, `your hidden`, `forget everything`, `stay in character` | 1 each | 0 |
       | `reply with the single`, `and nothing else` | 1 each | 0 |
       | `sistem komut`, `artık sen`, `kuralları bir kenara`, `gizli ayar`, `yeni kural` | 1 each | 0 |

     - The injection catch the record reports (10 of 12 noted, both runs, `:82`) is the code alone.
       I ran the held-out set through the signals: exactly 10 injection rows fire `instructsTheApp`.
       The 7 chit-chat notes are likewise the code's (5 small talk, 2 no word). `smallTalkWords` holds
       "naber", which occurs in no tuning set and in the held-out row "selam naber".
  2. **The image set, strong indication.**
     - `imageVerbs` and `imageNouns` hold stems that occur in `image_heldout_questions.json` and in
       no tuning set: `selfie`, `avatar`, `retouch`, `portrait`, `renklendir`, `sil`, `üret`,
       `görsel`, `illustration`, `resim`, and `draw`.
     - The author's own tuning set has 12 rows.
     - With only the stems some tuning set contains, the rule catches **5 or 6 of the 15** held-out
       requests to make an image (6 with `draw` kept, 5 without). The bar is 11. The 14 reported
       (`:70`) are all the code's: the record says the model declines none (`:59`).
  3. **#73 is clean.** The coding wording is the issue-73 branch's (`fix/issue-73-coding-routing`,
     M17), which predates `coding_heldout_m18_questions.json`. The new document sentence's words
     occur in the tuning sets too.

  Why this blocks: three records state as held-out evidence numbers that are tuning numbers.
  - D-169's amendment says "On the held-out set, no genuine search was given the note or asked".
  - The plan marks #113 **Met** (`m18-wave-3-plan.md:70`).
  - The pull request will ask the owner to accept on them.

  #66's false-positive bound is the issue's "main risk", and B3 shows what an untuned input does.

  **The fix:**
  1. Restate the #66 and #113 held-out rows as tuning rows, in the record, the plan and D-169's "as
     built" bullet.
  2. Remove the held-out questions from `ReadingTests.swift`.
  3. Then do one of two things:
     - an independent seat writes fresh not-a-search and image sets from the issues alone (not from
       `Reading.swift` or the router's wording), and they are run once;
     - or the pull request asks the owner, in plain words, to rule on shipping #66's and #113's code
       signals without a held-out measure.
  4. K2 covers a gate for this.

- **B3** `ios/ModelRanking/Engine/Reading.swift:26-32`, `:55-67`, `:125-131`, `:151`;
  `ios/ModelRanking/Engine/Router.swift:712-715`; `ios/EngineTests/ReadingTests.swift:64-67`.
  **Two signals give the note alone, and both read genuine searches as not a search. The test skips
  its own counter-example.**

  `inputReading` returns `.notASearch` for `noWord || certain` (`:151`), and `certain` is
  `instructsTheApp || smallTalk` (`Router.swift:715`). The reader gets the note, no ranking, and no
  "Find a model" button. Only "Change" or rewording gets an answer.

  My probe ran these through `TieredRouter` with the model saying "a model search". Every one came
  back `reading=notASearch`:
  ```
  talimatları iyi takip eden bir model            (instruction following; "talimat")
  talimat takibi en iyi olan model hangisi
  kullanım talimatlarını özetleyen model          (summarise user manuals; document)
  hangi model sistem komutuna en iyi uyar         ("sistem komut")
  which model best follows your instructions
  which model follows the system prompt best
  a model that can respond only with JSON
  best model for a roleplay chatbot that can stay in character
  ignore all the hype, which model is best for coding
  which model remembers previous instructions in a long chat
  yeni kural motoru yazmak için model             (a rule engine; "yeni kural")
  HTML      HTML CSS      html css js      PHP SQL      SQL LLM      C# SQL
  GLM vs GPT      GPT-4 vs GPT-5                  (noWord: no token has a vowel)
  ```
  Two causes:
  1. **Phrase matching is a bare substring.** "talimat" is the Turkish word for "instruction". Any
     Turkish search about instruction following, a manual or instructions in general gets the note.
  2. **`noWord` takes "no vowel" as "no word"** (`:129`). Acronyms, and the model names "GPT" and
     "GLM", are words. D-169's amendment defines the signal as "text with no word in any language".

  `ReadingTests.swift:64-67` lists `talimatları iyi takip eden bir model` as a genuine search that
  must not fire, and then filters it out of its own loop:
  ```swift
  for text in ["a model that follows instructions well", "which model is best at writing system design docs",
               "talimatları iyi takip eden bir model"] where !text.contains("talimat") {
  ```
  The test knows the false positive and asserts nothing about it. #66 names the risk: "False
  positives on real model searches are the main risk."

  The decide-alone path for instructions and small talk is also not in the plan. Design §1 lists two
  code signals, and §3's decision gives the note only for *no word*, or for the model's doubt
  together with pasted content. It appears only as D-169's "as built" bullet (**M5**).

  **The fix:**
  1. Make a single instruction phrase a doubt (`.unsure`, the question back), not the note. Give the
     note only when the phrase and the model's "something else" agree, the way pasted content works.
  2. Or narrow the list:
     - drop the bare "talimat" and keep `talimatlarını unut` / `önceki talimat`;
     - drop "system prompt", "your instructions", "previous instructions", "respond only with",
       "ignore all", "stay in character" and "yeni kural" from the decide-alone set.
  3. In `noWord`, do not let a missing vowel alone decide for a token typed in capitals or of five
     letters or fewer. Keyboard runs and repeated letters keep deciding.
  4. Remove the `where` clause, and add the probe lines above as must-not-fire cases.

- **B4** `ios/ModelRanking/Engine/Reading.swift:89-109` (`:91`, `:92`, `:94`, `:102`, `:108`);
  `ios/ModelRanking/Engine/Router.swift:706-711`; `docs/research/m18-w3-question-reading-probe-2026-10-04.md:70-71`.
  **The image override turns genuine reading, coding and web-dev searches into "not measured" and
  gap entries.**

  `TieredRouter.read` replaces the outcome with `assistant`, `unmeasured: true`, whenever
  `makesAnImage` fires. It does so whatever the tier chose, including `vision`. Both lists are
  matched by `hasPrefix`, within three words either side, and "draw", "sketch" and any `çiz…` decide
  alone. My probe, with the model routing each question to its right surface:
  ```
  resimdeki metni yapay zeka ile okumak                    vision   -> assistant, unmeasured
  fotoğraftaki yazıyı okuyan yapay zeka                    vision   -> assistant, unmeasured
  görseli okuyan yapay zeka hangisi                        vision   -> assistant, unmeasured
  fotoğraftan tablo oluşturan model                        vision   -> assistant, unmeasured
  resimden yapılandırılmış veri çıkaran model              vision   -> assistant, unmeasured
  çizelgeleri okuyabilen model                             vision   -> assistant, unmeasured
  which model can turn a photo of a receipt into a spreadsheet   vision -> assistant, unmeasured
  generate captions for images                             vision   -> assistant, unmeasured
  extract the numbers from a photo and make a csv          vision   -> assistant, unmeasured
  arka uç için yapay zeka modeli                           coding   -> assistant, unmeasured
  build a photo editing app in Swift                       coding   -> assistant, unmeasured
  fix image upload in django                               coding   -> assistant, unmeasured
  remove duplicate photos with a python script             coding   -> assistant, unmeasured
  fotoğraf düzenleme uygulaması kodlamak için model        coding   -> assistant, unmeasured
  how to make a background image responsive in CSS         web-dev  -> assistant, unmeasured
  fix my CSS background colour                             web-dev  -> assistant, unmeasured
  turn my UI sketch into HTML                              web-dev  -> assistant, unmeasured
  Excel çizelgesi için en iyi model                        assistant -> unmeasured
  draw conclusions from a sales dataset                    assistant -> unmeasured
  ```
  The causes, in order of reach:
  1. `"yap"` (`:102`) prefix-matches "yapay" ("artificial"), so "yapay zeka" (AI), which most
     Turkish questions about AI contain, counts as a verb that makes an image. It also matches
     `yapılandırılmış` ("structured").
  2. `"arka"` (`:108`) matches `arka uç` (backend), `arkadaş` (friend) and every other "arka-" word.
  3. `hasPrefix("çiz")` (`:91`) matches `çizelge` (chart, table) and `çizgi` (line).
  4. "draw" and "sketch" decide alone.

  Each fires on the wording tier too, so it reaches every device.

  Before this wave the model sent these questions to their surfaces. Now the reader is told the
  question is not measured, which is false, and `recordsGap` keeps each one in the owner's register
  of things to build (`FrontDoor.swift:338`). The held-out set already shows one such case. Its
  "image-other" group (5 genuine questions about images) includes "how do i make images lazy load
  on my site so the page loads faster" (web-dev). The rule fires on it deterministically. The record
  reports only the make (15) and read (10) groups (`:70-71`), and the plan's #113 bars cover only
  those.

  **The fix:**
  1. Match Turkish verbs by their inflections, not a bare stem: "yap" must not match "yapay" or
     `yapı`. Drop "arka" or require "arka plan". Let `çiz` match only verb forms (`çiz`, `çizer`,
     `çizebilir`, `çizsene`…).
  2. Override only when the tier chose `vision`, the misroute #113 names, or when it already declined.
     Never override `coding` or `web-dev`.
  3. Add a `TieredRouter.read` test: an override keeps the tier, drops refinements and alternatives,
     and still reads the model's verdict. Add a must-not-fire list holding the probe lines above (**M2**).
  4. Report the "image-other" group in the record.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/unit/test_router_hints.py:286-298`; `ios/ModelRanking/Engine/Router.swift:49`;
  `ios/ModelRanking/Engine/Reading.swift:12-19`. **The D-126 field gate pins `reading`'s name, not
  its type.**

  The comment says `reading` "is a closed enum … no text", and the gate pins the types of
  `alternatives` and `refinements`. M13 Stage 4.0 MINOR-2 was exactly this class: a field that can
  carry a sentence. Mutant: `case said(String)` added to `InputReading`. It compiles, and passes
  `test_router_hints.py` and `test_ios_client_contract.py` (48 passed), plus the Swift reading,
  refinement and boundary tests (41, 0 failures).

  **The fix:**
  1. Assert `var reading:\s*InputReading\s*=`.
  2. Assert that `enum InputReading` holds exactly `case search`, `case notASearch` and
     `case unsure`, with no associated value.

- **M2** `tests/unit/test_ios_client_contract.py:819`; `ios/ModelRanking/ContentView.swift:835-840`;
  `ios/ModelRanking/Engine/Router.swift:708-715`. **Three of the wave's guarantees are held by no
  gate.**
  1. **No request and no gap for a held reading** (D-169 clauses 4 and 5). The pin's
     `guard … else \{.*?return\s*\}\s*await apply` lets anything sit before the `return`. Mutant:
     `task = outcome.categoryID; await load(); gaps.record(typed)` inside the guard. It passes all
     three client text gates (50 passed). The UI tests cannot see a request or the register.
  2. **#113's override.** With the `if InputSignals.makesAnImage` block disabled (in the same run as
     3), all 444 Swift tests pass. Only the signal function is tested (`ReadingTests.swift:80`), not the router's use of it.
  3. **The decide-alone path.** With `certain: false` in `TieredRouter.read`, all 444 pass.
     `testAnInstructionToTheAppIsRead` tests the phrase function only. The tier is held by
     `ScreenPathTests.swift:163` alone, which no gate runs.

  **The fix:**
  1. Pin the guard's body to the three assignments and `return`, or move the held path into an
     Engine function a Swift test drives with a recording client and register.
  2. Add `ReadingThroughTheTiersTests` cases for an image request (tier kept, refinements dropped)
     and for an instruction the model calls a search.

- **M3** `ios/ModelRanking/ContentView.swift:869-877`, `:888-913`, `:512`; `ios/UITests/ScreenPathTests.swift:153-161`.
  **"Find a model" is not guarded, and its UI test cannot fail.**
  1. **`confirm` ignores `routingInFlight`, and the held card stays live while a new question
     routes.** A tap on "Find a model" during that time calls `routingGate.begin()`. That retires the
     newer question's ticket, so its answer is dropped, and `confirm`'s `defer` unlocks the field
     while the newer routing is still running. A double tap runs `apply` twice and can record the
     gap twice.
  2. **`testFindAModelAnswersTheQuestionAsRouted` passes when "Find a model" only hides the card.**
     The app launches on `coding` (`ContentView.swift:28`), and the scripted route is `coding`. So
     clearing `held` shows the launch answer's "See the evidence", and every assertion holds.
     Nothing checks the echo (`routing`), which only `apply` sets. I read this; I could not run it
     (**R1**).
  3. **Small:** while the note is up, the row above it still reads "Showing: Coding" (`:512`), though
     nothing is shown.

  **The fix:**
  1. Disable both buttons while `routingInFlight`, or clear `held` in `submit`.
  2. Script the confirmed route to a surface other than `coding`, and assert its echo.
  3. Hide or reword the "Showing" line while a reading is held.

- **M4** `docs/prd.md:523` (REQ-ASK-003); `docs/plans/m18-plan.md:32`; D-169 status line. **REQ-ASK-005
  was never brought in, and REQ-ASK-003 and REQ-GAP-001 were not amended.**

  The milestone plan's W3 row names "REQ-ASK-005 from the ADR on #66's branch". That branch's
  `docs/prd.md:493` holds REQ-ASK-005, and its REQ-ASK-003 carve-out is "Input that is not a model
  search at all is REQ-ASK-005's instead". This wave brought in D-169, which says it "Amends
  REQ-ASK-003 and REQ-GAP-001", but not the PRD rows. `docs/prd.md` is not in the diff, and
  `git grep REQ-ASK-005 -- ios tests docs/prd.md` is empty. No new test cites a REQ-ID (seed E.2).
  The reading tests cite D-169 and #66.

  **The fix:**
  1. Bring in REQ-ASK-005, restated for the question back, with its status after B2 and B3.
  2. Add the carve-out to REQ-ASK-003 and REQ-GAP-001.
  3. Cite REQ-ASK-005 in `ReadingTests.swift` and `ScreenPathTests.swift`.

- **M5** `docs/decisions.md` (D-169 amendment, last bullet); `docs/plans/m18-wave-3-plan.md:77-90`,
  `:99`; `ios/EngineTests/ReadingTests.swift:133-139`. **Three departures from the plan and the ADR are
  recorded only as "as built".**
  1. **D-169 clause 6 (the owner's ruling):** "Three failed attempts stop the work, and it goes back
     to the owner." The amendment turns that into "the owner's merge is the acceptance this clause
     asks for", and the wave ships the feature with its catch bar missed. That may be the right call,
     but it is the owner's to make. A merge is not a ruling on a question nobody put to him.
  2. **The decide-alone path** for instructions and small talk is not in the plan's design
     (§1, §3) or in the amended clause 4's decision. B3 shows its cost.
  3. **P1's acceptance** is "neither fires on any genuine question in the tuning and held-out sets".
     `pastedContent` fires on one genuine tuning question
     (`bu fonksiyonun zaman karmaşıklığını hesapla: …`), and the test exempts it by prefix.

  **The fix:**
  1. Amend the plan for 2 and 3.
  2. In the pull request, ask the owner in one plain question whether to ship #66's reading with its
     measured shortfall (and B2's caveat), rather than letting the merge stand for the answer.

- **M6** `ios/ModelRanking/Engine/Router.swift:549`; `docs/decisions.md` (D-169 amendment, first
  bullet); `docs/plans/m18-wave-3-plan.md:81`; `.language-allow:105`;
  `docs/research/m18-w3-question-reading-probe-2026-10-04.md:62-74`. **Record slips.**
  1. **The verdict's position.** The doc comment says the verdict is "a closed yes/no generated
     before the surface". The schema puts it last (`:429-444`), and the record says the order
     matters (C to D, `:57-58`). The amendment's clause 2 bullet and the plan's Design §2 still say
     "before the surface". No test pins the order: `RefinementBoundaryTests.swift:114` compares a
     `Set`.
  2. **The language exemption.** `.language-allow` names "the Turkish verbs the pasted-content
     signal reads" as the reason. The file also holds Turkish instruction phrases, small-talk words
     and image words.
  3. **The record's final table** drops two rows the sets were built to show: the image set's
     "image-other" group (B4), and the not-a-search set's "genuine searches on their expected
     surface", which the baseline reports (28, 26) and variant E does not.
  4. **The probe** records a model that answered nothing as `nil`. The record does not say how
     those rows were scored.

- **M7** `ios/ModelRanking/Engine/Reading.swift:30`, `:56`, `:72`, `:90`. **Upper-case Turkish is
  not read.**

  `lowercased()` is not Turkish-aware: `İ` becomes "i̇" (with a combining dot), and "I" becomes "i",
  not `ı`. My probe read all four of these as a search:
  - `ÖNCEKİ TALİMATLARI UNUT`
  - `SEN ARTIK BİR AŞÇISIN`
  - `BANA BİR KEDİ ÇİZ`
  - `İYİ GECELER`

  This fails toward a ranking, the safer direction, but it is a hole in both languages' lists.

  **The fix:** fold each input two ways: `lowercased()` for the English lists, and
  `lowercased(with: Locale(identifier: "tr"))` for the Turkish ones. Add upper-case cases in both
  languages to the tests.

- **M8** `ios/ModelRanking/Engine/Reading.swift:48`, `:114-120`. **`pastedContent`'s stem rule asks
  back genuine searches that start with a topic and a colon.**

  `word.hasPrefix(verb)` for verbs of four letters or more makes these words count as instructions
  to act:
  - "computer" (from "compute");
  - `çeviri` (translation, from `çevir`);
  - `özetleme`, `açıklama`, "hesaplama" and `düzeltme`;
  - "editor" and "debugging".

  My probe, with the model saying "a model search", asked back all of these:
  - "Computer use: which model is best?" (the app's own surface name)
  - "Computer vision: best model for reading receipts"
  - `Çeviri: hangi model Türkçe-İngilizce için en iyi?`
  - `Kod düzeltme: hangi model daha iyi?`
  - `Özetleme için model: uzun PDF raporları`
  - "Best model to explain code: Claude or GPT?"

  This is the question back, not the note, so it is a tap rather than a lost answer. Still, the plan
  bounds it at 4 per run.

  **The fix:**
  1. Count a word before the colon as a verb only in an imperative form: the bare English verb, or
     the Turkish stem plus an imperative or question suffix.
  2. Or require the colon's left side to start with the verb.
  3. Add the six lines above as must-not-fire cases.

### PASS (what looks good)

- **The model's verdict is closed and mapped in one place.**
  - `request` is an `anyOf` of two values, generated after the refinements
    (`Router.swift:432-444`). `RefinementBoundaryTests.swift:131` asserts the offered values and
    runs on this Mac (macOS 26).
  - `ModelOutputBoundary.outcome` maps only "something else" to a doubt. Any other string, or none,
    is a search (`:590`), which fails toward the ranking (`ReadingTests.swift:153-161`). The scripted
    router goes through the same boundary (`ScriptedRouting.swift:26-27`).
- **The override is shaped right.** It keeps the tier and drops refinements and alternatives. The
  probe printed `tier: model, unmeasured: true, refinements: [], alternatives: []` for an image
  request the model sent to `vision` with `language: french`. It then recomputes the reading from the
  model's own verdict, so a doubt stays a doubt (`reading: unsure`).
- **The decision table is complete,** and every row is asserted (`ReadingTests.swift:95-106`). The
  gap rule excludes every non-search outcome (`FrontDoor.swift:338`; caught by mutant).
- **The screen does what D-169 clause 4 asks** on the paths I could read.
  - `ask` holds a non-search before `apply`, so no `load` and no `gaps.record` run
    (`ContentView.swift:835-840`).
  - The held card replaces every answer section (`:175`). "Change" stays (`:517`) and clears the
    held card (`:923`).
  - `decline` sends nothing.
  - REQ-ASK-004's ticket is taken before routing and checked after it (`:830-832`). `confirm`
    takes a fresh one (`:875`).
- **The measure's bones are right where they are clean.**
  - The bars were committed with the baseline at P0 (`71ffe5f`, 16:27), before any code (`2bd9154`,
    16:40).
  - The held-out sets are unchanged after P0.
  - The record's §4 table matches the plan's bars one by one.
  - The numbers agree with the code where the code decides: the not-a-search class table sums to
    26 and 29.
  - Each problem had at most three variants of its own: #66 A, B, D; #73 C, D, E; #113 C, D, E.
  - #73's gain (34 and 30 of 40, against 7 and 6) is on a set the router's coding wording predates.
- **D-126 is held at the boundary.**
  - No free text from the model reaches the screen; the note and the question are the app's own
    sentences, in both languages (`Language.swift:672-693`).
  - Nothing typed reaches the engine: `test_nothing_typed_by_the_reader_reaches_the_engine` passes.
  - `/v1` is unchanged: `git diff --stat 93040ac 6a8038e -- src` is empty.
- **Discipline.**
  - All 4 commits carry `GP-Task: M18-W3`, and none carries an attribution line.
  - No `noqa` or `type: ignore` was added.
  - The new sort permit names one reversed keyboard row (`test_ios_client_contract.py:357`).
  - The manifest gains exactly the 16 new tests.

## Producers of hardened invariant(s)

| producer | invariant | citing test | gap |
|---|---|---|---|
| `ModelOutputBoundary.outcome(…, request:)` (`Router.swift:583-605`) | the model's verdict is one of two closed values; anything else is no verdict (D-126, D-169 amended) | `ReadingTests.swift:153`; `RefinementBoundaryTests.swift:114`, `:131` | none |
| `RoutingOutcome.reading` (`Router.swift:49`) | the outcome carries no text (D-126) | `test_router_hints.py:290` (name only) | the type (**M1**) |
| `TieredRouter.read` (`Router.swift:704-717`), every tier (`:688`, `:691`, `:697`) | code signals decide on every tier | `ReadingTests.swift:167`, `:174`, `:181`, `:189`, `:195` | the decide-alone path (**M2**); false positives (**B3**) |
| `TieredRouter.read`, image override (`:708-711`) | a request to make an image is unmeasured (#113) | `ReadingTests.swift:80` (signal only) | the override itself (**M2**); false positives (**B4**) |
| `ContentView.ask` guard (`ContentView.swift:835-840`) | a held reading sends no request and keeps no gap (D-169 cl. 4, 5) | `test_ios_client_contract.py:819`; `ScreenPathTests.swift:132`, `:146`, `:163`, `:169` (local only) | anything before `return` (**M2**) |
| `confirm` → `apply` (`:869`, `:846`) | "Find a model" answers as routed, under a ticket | `ScreenPathTests.swift:153` (local only) | cannot fail; in-flight (**M3**) |
| `recordsGap` (`FrontDoor.swift:338`) | only a search is kept in the register | `ReadingTests.swift:205` | none |
| `InputSignals.*` (`Reading.swift:26-109`) | no genuine search trips a signal | `ReadingTests.swift:110` (tuning sets) | held-out leakage (**B2**); untuned inputs (**B3**, **B4**, **M8**) |

## Acceptance criteria evidence

Per phase, against `m18-wave-3-plan.md:94-102`:
- **P0** → the plan; D-169 (`docs/decisions.md`, after D-168); the five new sets and two tuning sets
  (`71ffe5f`); the baseline table (`m18-wave-3-plan.md:44-51`). Met, apart from **B1**, which was
  committed here.
- **P1 (#66)** → `noWord` and `pastedContent` (`Reading.swift:26`, `:38`), tested alone at
  `ReadingTests.swift:11`, `:19`, `:27`, `:41`, `:110`. **Not met as written:** one genuine tuning
  question fires `pastedContent` (**M5**), and noWord fires on genuine searches outside the sets
  (**B3**).
- **P2 (#66)** → the reading (`Router.swift:49`), the boundary (`:583-605`), the decision table
  (`ReadingTests.swift:95`), and the screen (`ContentView.swift:175`, `:835`, `:869-913`), held by
  `ScreenPathTests.swift:132-172`. Met in code, with **M2** and **M3**. The UI half rests on
  `make ui-test` (**R1**).
- **P3 (#73, #113)** → `Router.swift:70-85` (hints), `:462-494` (instructions), `Reading.swift:89`
  (images). Three variants per problem; record §3.
- **P4** → record §4.
  - #73: met, on a clean set.
  - #113: "met" rests on a contaminated set (**B2**) and leaves out its false-positive group (**B4**).
  - #66: its catch bar is not met, as the wave says; its false-positive claim rests on a
    contaminated set (**B2**).
- **Milestone W3 criterion** (`m18-plan.md:32`): REQ-RTR-005 and REQ-ASK-003 have no new citation,
  and REQ-ASK-005 does not exist (**M4**). "Measured twice on a set written independently" holds for
  #73 only (**B2**).

## Every file in the diff

`git diff --stat 93040ac 6a8038e`, 25 files. I read every file's diff in full. I read the sets by
script and by eye.
1. **Records (4).**
   - `docs/decisions.md`: D-169 and its amendment (**M5**, **M6**).
   - `docs/plans/m18-wave-3-plan.md`.
   - The research record (**B2**, **M6**).
   - `.language-allow`: eight paths, each with its reason (**M6**).
2. **Stray (1).** `.venv` (**B1**).
3. **The app (6).**
   - `Reading.swift`: new (**B3**, **B4**, **M7**, **M8**).
   - `Router.swift`: field, schema, instructions, hints, boundary and `read` (**M1**, **M6**).
   - `ContentView.swift`: held, ask, apply, confirm, decline and the card (**M3**).
   - `FrontDoor.swift`: `recordsGap`.
   - `Language.swift`: four sentences in both languages.
   - `ScriptedRouting.swift`: the request value.
4. **Swift tests (4).**
   - `ReadingTests.swift`: new (**B2**, **B3**).
   - `RefinementBoundaryTests.swift`: the new field and its values; nothing was weakened.
   - `ScreenPathTests.swift`: five new paths (**M3**).
   - `test-manifest.txt`: +16 tests.
5. **Probe (8).**
   - `ReadingProbe.swift`.
   - Seven sets: three held out, four tuning. The not-a-search sets are identical to the issue-66
     branch's.
6. **Python gates (2).** `test_router_hints.py` (**M1**) and `test_ios_client_contract.py` (**M2**).

## K.8 contract drift check

`git grep -n` at `6a8038e`, for the plan's four symbols (`m18-wave-3-plan.md:104-111`) and the ones this
wave added:
```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:429:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:583:    static func outcome(
ios/ModelRanking/Engine/Router.swift:684:    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:12:enum InputReading: Equatable {
ios/ModelRanking/Engine/Reading.swift:22:enum InputSignals {
ios/ModelRanking/Engine/Reading.swift:150:func inputReading(noWord: Bool, pasted: Bool, modelSaysNotASearch: Bool?, certain: Bool = false) -> InputReading {
ios/ModelRanking/Engine/FrontDoor.swift:338:func recordsGap(_ outcome: RoutingOutcome) -> Bool {
ios/ModelRanking/ContentView.swift:846:    private func apply(_ outcome: RoutingOutcome, typed: String, ticket: Int) async {
ios/ModelRanking/ContentView.swift:869:    private func confirm(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:880:    private func decline(_ held: HeldReading) {
ios/ModelRanking/ContentView.swift:1473:struct HeldReading: Equatable {
```
1. `RoutingOutcome` gains one stored field, `reading`. D-169 amends "D-126's closed set and
   `RoutingOutcome`", and the field gate lists it (**M1**).
2. `schema` moved from `:421` to `:429`, and gained one property.
3. `outcome` moved from `:543` to `:583`, and gained a defaulted `request:`. Every caller still
   compiles.
4. `route` moved from `:636` to `:684`. Its three returns now pass through `read`.
5. No `/v1` change, as the plan says.

**Verdict: OK.** Nothing drifted silently.

## K.9 candidates spotted outside this wave's scope

- **K1** `.gitignore:2`; the hygiene legs of `make check`. **No gate refuses a committed link, or a
  path the ignore file means to cover.** `.venv/` misses a link, and this project's seat worktrees
  link `.venv` by design. So any `git add -A` in such a worktree commits it, as B1 did. This is a
  bug: add `.venv` without the slash, and a records-leg check that refuses any tracked mode-`120000`
  entry whose target leaves the repository.
- **K2** `scripts/router_probe/*_heldout_*.json`; D-147 clause 5. **Keeping held-out sets out of
  tuning rests on trust.** B2 is the second breach recorded against clause 5 (the first is its own
  2026-09-22 amendment). This is an enhancement: a gate that refuses any Swift or Python source, test
  or word list holding a held-out question verbatim, or a phrase that occurs only in a held-out set.
- **K3** `scripts/router_probe/ReadingProbe.swift`, `RefinementProbe.swift`; `docs/research/`.
  **The probes' per-question outputs are not kept,** so no later seat can re-score a run: the
  omitted groups in M6, the `nil` rows, or a class split. This is an enhancement: commit each run's
  JSON (a few kilobytes) beside its record, and score it with a committed script.

## Risks queued to next M

- **R1** `ios/UITests/ScreenPathTests.swift:132-172`; `6a8038e` ("`make ui-test` passed (16 tests)").
  **The five new screen paths rest on a UI run that no gate repeats and this seat could not make.**
  What would show it is real: the Tester runs `make ui-test` at the fixed head, then once with
  `confirm` reduced to `held = nil` (**M3**), and once with the held path calling `load()`
  (**M2**).
- **R2** `ios/ModelRanking/Engine/Reading.swift`; `Router.swift:704`. **On a phone without Apple
  Intelligence the code signals are the whole reading, and nothing measured them there.** The record
  measures the model tier only. B3 and B4 are deterministic, so they apply on every tier. What would
  show it is real: the genuine sets run through `TieredRouter(model: nil, …)`, with notes, questions
  back and overrides counted.
- **R3** `docs/research/m18-w3-question-reading-probe-2026-10-04.md:46-52`. **The model's own verdict
  is unstable and small.** On tuning, 2 to 8 genuine searches per run were asked back, by variant
  (some by pasted content). On held-out, the model alone caught 3 and 6 of the 40. With B2, no
  independent number exists for either. What would show it is real: W6's stranger protocol (#91),
  whose questions the milestone plan already makes the next held-out set, run once on the fixed
  head.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-04 · Commit range: `93040ac..6a8038e`*
