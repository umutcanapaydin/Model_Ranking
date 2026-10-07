---
record_type: review
id: m19-wave-4-review-round-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19-W4 Code Review, round 3: reading the question, a second round

**Reviewer:** Code-Reviewer subagent, a new seat with fresh eyes. I wrote none of this wave's code,
tests or records, and I sat in neither earlier review.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..199d529` (the whole wave, 16 commits). The answer to round 2 is `b2723f8`
(red tests), `ec5159e` (fixes) and `199d529` (the rename of round 2's file).
**Risk tier:** HIGH (`docs/plans/m19-wave-4-plan.md:13-15`). What the on-device model's output decides
(D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a security glob. By D-172 no
security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I read the profile and `.agents/rules/practices.md` from `origin/main`, then the
wave plan, both earlier reviews, the code at `199d529`, the tests and the records. I read no other
seat's scratch files. Every probe line below is one I made up for this review. I checked by script
that none matches or is close to a held-out question (0 of 137 within a 0.8 similarity ratio), and
no held-out question is quoted here.

**Summary.**
- **B1's class is still open.** The fix replaced round 2's site-word list with two new patterns: "my /
  this / our / these" before any image noun, and a making verb before "a / an" and an image noun.
  These patterns catch ordinary questions about the asker's own site, store, app, slides or phone.
  - I wrote 59 new questions of that kind, none sent to code or `vision`. At `199d529`, **54 of the
    59 are told "not measured"** and kept in the gap register, on both tiers.
  - The same 59 give 28 at round 1's fix (`671b305`), the code round 2 blocked, and 0 at the code that
    ships (`3426ff3`).
  - The fix also lost 6 of my 35 requests to make an image that `671b305` caught. One is
    `bir kedi resmi çiz` ("draw a cat picture").
  - The new test holds round 2's sixteen printed lines word for word. When I changed only "the" to
    "my", "this" or "our" in 14 of them, all 14 were overridden. So the fix was fitted to the probe
    that found the defect, as round 2 said of round 1's fix.
  - The records say the class is closed (REQ-IMG-003, D-169's pointer, record §6).
- **This is the third verdict in a row on this class, and none found it closed.** Round 1 ruled it
  MAJOR, round 2 BLOCKING, and this review BLOCKING. There have been three attempts at the same failure
  (`de8c3f8`, `671b305`, `ec5159e`). The M18-W3 reviews ruled the class (B4) BLOCKING twice before
  that. By "Three attempts, then stop" (`.agents/rules/practices.md`) and `/close-wave` step 3, **the
  slice comes out of the wave.** That slice is the image rule's reach beyond `vision`. B1 gives the
  measured cost of taking it out.
- **Every other round-2 finding is fixed:** M2 (apostrophes), M3 (the colon rule), K1 (Turkish folding
  in `makesAnImage`), M5's "I", and four of M6's five record items. M6.4 is half done (M1 below). I
  built `b2723f8` and its four new tests fail, 49 assertions, while every other Reading test passes.
  The `review2-*` runs are the code's own: I replayed them through `199d529` and 0 rows differ.

## Verdict

BLOCKING

## The earlier findings, one by one

Round 2 (`docs/reviews/m19-wave-4-rereview.md`):

| Round 2 | Fixed? | Evidence |
|---|---|---|
| **B1** image rule overriding site, store and document questions | **No. Open, as B1 below.** | Round 2's sixteen lines keep their surface (`ReadingTests.swift:704-723`). The class does not: 54 of 59 new lines are overridden at `199d529`, against 28 at `671b305` and 0 at `3426ff3`. |
| **M1** fact signal reads unlisted searches | **Yes, as the record.** | D-184 clause 1 now says the exclusions are lists, and that a search they do not name is asked about (`docs/decisions.md:4197-4206`). |
| **M2** Turkish `'i` read as English "I" | **Yes.** | `Reading.swift:166-168` drops a suffix after an apostrophe. My lines `Nutuk'u kim yazdı`, `Titanik'i kim yönetti`, `İstiklal Marşı'nı kim besteledi` and `Nutuk’u kim yazdı` are read; "I'm curious who wrote dune" is not. Test: `ReadingTests.swift:742-745`. The mutant is killed (m14). One residual with no practical reach: a model name in straight quotes ("who is the leader 'claude' or 'gpt'") loses its exclusion. iOS types a left single quote (U+2018) for an opening quote, and the pattern does not hold it. |
| **M3** colon rule lost pasted content about AI | **Yes.** | `Reading.swift:63-69`. "rewrite: the LLM era began with transformers", `kısalt: yapay zeka her yerde` and "translate into spanish: which is the best way to the station" are read. "explain: which model is better for math" is not. Tests: `ReadingTests.swift:748-753`. Mutants m15 and m16 are killed. Narrow residuals both ways: content that opens with "which" and names AI is not read ("fix this sentence: which ai do you think is smarter"), and `web sitesi yap: hangisi en iyi` ("make a website: which is best") is asked about. Both cost one tap at most. |
| **M4** site guard's folding gap | **Moot.** | The guard is gone. "make me an App Icon, flat style, green" on `web-dev` is read (my probe). |
| **M5** three untested rules | **Yes for "I"; the other two are moot.** | "Where should I start" (`ReadingTests.swift:744`) holds the "I" exclusion alone. The `için` exception and the guard on `vision` left with the guard. The new code has untested branches of its own (M2 below). |
| **M6** record drift | **Four of five.** | 1. The round-1 id is fixed (`m19-wave-4-review-round-1.md:3`); `check_records` passes. 2. The class cites REQ-RTR-005 (`ReadingTests.swift:515`). 3. `Router.swift:702` names D-184. 5. #186 links `-round-1.md` (`gh issue view 186`). 4. Half done: the reason string is now measured (`test_ios_client_contract.py:1589`), but the comment above it still says an entry "can only lower that set's catches" (`:1587`). That is M1 below. |
| **K1** the dotless `ı` in `makesAnImage` | **Yes.** | `Reading.swift:229-231`. "Turn This Menu Photo Into A Table" and "TURN THIS PHOTO INTO TEXT" are not read as making; "Turn My Photo Into A Cartoon" is. Test: `ReadingTests.swift:716`. Mutant m17 is killed. |
| **R1** fact signal without the model | Carried (R1 below). | Unchanged by the round. |
| **R2** spent M19 sets still live | Carried (R2 below). | They have now carried three rounds of replays. |

Round 1 (`docs/reviews/m19-wave-4-review-round-1.md`), as round 2 judged it, with this round's change:
**MJ1** is still open (it is the class of B1). **MJ2** is fixed, and its class is recorded (round 2's
M1). **M1–M4** and **M6** are fixed. **M5** is fixed but for one item: REQ-IMG-003 still claims more
than the code does (B1). **K1** is filed as #186 (open). **K2** is fixed.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `ios/ModelRanking/Engine/Router.swift:706-714`; `ios/ModelRanking/Engine/Reading.swift:307-350`
  (`asksForANewOrOwnImage` and its lists); `ios/EngineTests/ReadingTests.swift:602-620`, `:703-739`;
  `docs/prd.md:550` (REQ-IMG-003); `docs/decisions.md:3411` (D-169's pointer), `:4214-4222` (D-184
  clause 3); `docs/research/m19-w4-question-reading-probe.md:180-189` (§6).
  **Beyond `vision`, the image rule still tells ordinary questions about an image in a website, a
  store, an app, a document or a phone that they are "not measured", and keeps them in the owner's gap
  register. This is the M18 reviews' B4 class, round 1's MJ1 and round 2's B1. It is the third attempt
  at it, and it is not closed. So the slice comes out of the wave.**
  - **Probe.** I ran 98 made-up lines through `TieredRouter` in scratch copies of `ios/` at
    `3426ff3`, `671b305` and `199d529`. Each line went three ways:
    - with `ScriptedModelRouter` naming the surface a careful reader would;
    - with a wording tier answering that surface;
    - through the real wording tier (`SimilarityRouter`).
  - **The results:**

    | | `3426ff3` (ships) | `671b305` (round 1's fix) | `199d529` |
    |---|---:|---:|---:|
    | 59 site, store, app, document and phone questions about an image, told "not measured" (model tier; the fixed wording tier is identical) | 0 | 28 | **54** |
    | `web-dev` / `document` / `assistant` / `everyday` | 0/35, 0/10, 0/4, 0/10 | 14/35, 2/10, 2/4, 10/10 | 34/35, 8/10, 2/4, 10/10 |
    | the 18 of those the real wording tier ranks on a measured surface, overridden by the rule | 0 | 5 | **18** |
    | 35 requests to make or change an image, told "not measured" | 0 | 29 | 24 |

    Every one of the 54 keeps reading `search` and `recordsGap` true. On the other 41, the real wording
    tier declines by itself, gives no answer (every Turkish line falls back to manual), or picks code
    or `vision`, so the new reach changes nothing there.
  - **A sample.** Each line was routed to `web-dev` unless marked:
    ```
    make my logo bigger in the header of my blog      fix my images not showing on my shopify store
    make our logo link to the homepage                make these images fit the container in css
    make this picture the background of my landing page   fix my app icon not updating in xcode
    create a photo sharing app like instagram         make an image grid for my portfolio site
    make an icon button with tailwind                 create a picture element with srcset for responsive images
    fotoğraf düzenleme uygulaması yap                 sitemdeki fotoğrafım görünmüyor, düzelt
    remove this picture from my word document (document)   make our logo appear on every slide (document)
    bu görseli sunumdan sil (document)                edit this photo's alt text (assistant)
    fix my photos not syncing to icloud (everyday)    restore my deleted photos from icloud (everyday)
    make my photos private on instagram (everyday)    fotoğrafımı instagramdan sil (everyday)
    ```
  - **Why it leaks.** The fix (`ec5159e`) swapped a list of site words for two patterns. Each one
    describes the ordinary way of asking about a site or a device, too.
    1. *The asker's own* (`Reading.swift:326-328`) is any image noun (image, images, logo, icon,
       avatar, picture, photo, wallpaper…) after "my", "this", "our" or "these", within two words.
       A person asks about the logo on their own site, the picture on their own slide, or the photos
       on their own phone in exactly these words. Round 2's lines mostly said "the". I took 14 of the
       lines the new test holds and changed only "the" to "my", "this" or "our" ("fix my hero image on
       my homepage", "fix this broken image in my shopify store", "make my images smaller in my
       powerpoint", `blogumdaki fotoğrafımı düzelt, açılmıyor`). **All 14 are overridden**, on both
       tiers.
    2. *A new image* (`:318-325`) is a making verb with "a", "an", "some" or "new", then an image noun
       within three words. "Create a photo sharing app", "make an image grid" and "make an icon
       button" name a feature to build. The modifier heads (`:290-296`) know about forty words that
       end such a phrase, and "sharing", "grid", "button", "map", "element", "editor" and "cropper"
       are not among them. In Turkish, any bare image noun before `yap` or `oluştur` counts
       (`fotoğraf düzenleme uygulaması yap`, "make a photo editing app").
  - **It over-corrects as well.** 6 of my 35 requests that `671b305` caught are no longer read:
    "create the logo for my coffee shop", "make 3 logo options for my brand", "generate images of my
    dog as a superhero", `logomu yeniden tasarla`, `kedimin resmini çiz` and `bir kedi resmi çiz`.
    The last is M18's own test sentence without "bana" (`ReadingTests.swift:306`). Off `vision`,
    `çiz` now needs `bir` with an image noun, or one of six bare nouns (`Reading.swift:330-335`, `:349`).
    `resmi` and `resmini` are neither (`:373`).
  - **Why the measure cannot see it.** The questions that only mention images were overridden 0 of 20
    on the held-out set and 0 of 20 on the tuning set, at every commit of the wave. Neither set uses
    these phrasings. The probes are the only evidence on this class, and each fix has been fitted to
    the previous probe: `ReadingTests.swift:704-723` holds round 2's sixteen printed lines word for
    word.
  - **The records say the class is closed.**
    - REQ-IMG-003 (`prd.md:550`): "so a question about an image in a website or a file keeps its
      surface".
    - D-169's pointer (`decisions.md:3411`): "except a question about an image in a website, an app
      or a document". This still describes the site guard that `ec5159e` removed.
    - Record §6 (`:180-189`): "The review's thirteen website and document lines now keep their
      surface".
    - D-184 clause 3 and the comment at `Router.swift:706-710` say "fix the image" or "make images …"
      keeps its surface. That is true of those words only.
  - **Why it blocks.** Against the code that ships, the wave makes these questions worse: each one kept
    its ranking at `3426ff3`. Each wrong override also lands in the gap register as a false need, and
    the owner reads that register to decide what to build (REQ-GAP-002). The class has been ruled
    BLOCKING by the M18-W3 reviews twice, MAJOR by round 1, and BLOCKING by round 2.
  - **What taking the slice out costs, measured.** I replayed the committed runs through a scratch copy
    of `199d529` whose rule reaches `vision` only, with W4's Turkish forms and K1's folding kept. The
    replays are exact: the same harness gives `review2-*` and `review2w-*` back with 0 rows changed.
    Counts only:
    - Held-out requests to make an image told "not measured": **4 and 3 of 20** on the model tier
      (now 8 and 8; baseline 2 and 1; bar 14), and **14 of 20** on the wording tier (now 18; baseline
      14; **bar 18, so missed**).
    - Requests to read an image reaching `vision`: 10 and 9 (unchanged). Questions that only mention
      images, overridden: 0 (unchanged).
    - Tuning image set: 27 and 26 of 36 with the model, 25 without it.
    - The reading measures do not move: not-a-search 24 and 26 of 50; knowledge 5 and 5 of 20; genuine
      searches noted 0, asked 1 and 0.
    - So #113 then meets no bar. It stays open, as it already is, and the pull request's question to
      the owner (the valve) says so.
  - **Fix.**
    1. Take the reach beyond `vision` out of the wave:
       - `Router.swift:711-712` goes back to `outcome.categoryID == "vision"`.
       - Remove `asksForANewOrOwnImage` and its lists (`Reading.swift:307-350`).
       - Remove `ReadingTests.swift:725-739`, which holds the override beyond `vision`.
       - Keep the keep-its-surface tests (`:321-341`, `:629-650`, `:703-723`). They hold the shipped
         behaviour.
       - The Turkish forms, the modifier rule and K1's folding act on `vision` only, so they stay.
    2. Red first: turn `ReadingTests.swift:602-620`, its wording-tier half too, into a test that a
       request to make an image sent to `web-dev` keeps `web-dev`, as at `3426ff3`. It fails on
       `199d529` and passes once the reach is out.
    3. `/file-issue` a `bug` for the slice. Its body lists the three attempts, each with its probe:
       - `de8c3f8`: every surface but code. Round 1 found 13 lines overridden.
       - `671b305`: the site-word guard. Round 2 found 24 of 31 overridden.
       - `ec5159e`: the new-or-own patterns. This review finds 54 of 59 overridden.

       A next round should not start from another word list. One possible start: beyond `vision`,
       make the rule a doubt (the one-tap question back) and not an override, so a wrong reading costs
       one tap, not a false "not measured" and a false gap entry. Then measure it on a fresh set that
       holds questions about the asker's own site, slides and phone, written with "my", "this" and
       "a".
    4. Correct REQ-IMG-003, REQ-RTR-005, D-184 clause 3 and its "Measured" paragraph, D-169's pointer,
       record §4–§7 (with the replayed numbers above), the `m19-plan.md` amendment, and the comments at
       `Router.swift:706-710` and `Reading.swift:215-225`. Each says what the code then holds. The wave
       footprint's `Stopped at three attempts:` line names the issue.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `tests/unit/test_ios_client_contract.py:1586-1587`. **Round 2's M6.4 is half done.** The
  reason string `_AFTER_MEASURE` now states the measured fact (`:1589`). The comment above it still
  makes the general claim that a modifier or an exclusion "can only lower that set's catches", which
  round 2 showed is not true in general. **Fix:** say there what the string says: measured, the five
  entries change no row of either set.
- **M2** `ios/ModelRanking/Engine/Router.swift:711-712`; `ios/ModelRanking/Engine/Reading.swift:312-350`.
  **Most of the new reach is held by no test, including "never on code".** I planted 17 mutants in a
  scratch copy and ran the whole Swift suite on each. I restored each file from saved bytes and
  checked it by sha256 against the worktree. The four mutants of round 2's M2, M3 and K1 fixes are
  killed (m14–m17), and so are three in the new function (m1, m3, m7). These 10 survive:
  - m10 and m13: the `coding` and `agentic-coding` exemption removed. At `671b305` a B4 line such as
    "remove duplicate photos with a python script" reads as making an image, so the test that sends
    it to `coding` held the exemption. Since `ec5159e` no such line passes `asksForANewOrOwnImage`.
    So D-184 clause 3's "never on the two coding surfaces" is held by nothing.
  - m2: `our` and `these` dropped. m4: `some` and `new` dropped. m5: "draw" made to need an image
    noun. m6: the Turkish `bir` branch removed. m8: the Turkish possessive stems removed. m9: the
    Turkish `bu` branch removed. m11: K1's folding removed from the new function. m12: `yap` dropped
    from the new-image stems.

  **Fix:** this goes with B1's fix, which removes the function and the exemption. If any of the reach
  stays, give each surviving branch a test line, starting with a request to make an image that the
  tier sent to `coding`.

### PASS (what looks good)

- **Red first, again.** At `b2723f8` the four new tests fail with 49 assertions (12, 34, 1 and 2), and
  every other Reading test passes. `ec5159e` turns them green. The whole Swift suite passes at
  `199d529` in a scratch copy: 484 tests, 0 failures, exactly the manifest's 484.
- **The `review2-*` numbers are the code's.** I replayed `final-*` (model tier), `finalw-*` (wording
  tier) and the `v0-*` tuning runs through `199d529`. Every pair matched its committed `review2-*` or
  `review2w-*` run row for row (0 of 50, 50, 100, 100, 82, 82, 50, 100 and 82 differ). `score_w4.py`
  on them gives record §6's figures:
  - model tier: not-a-search 24 and 26 of 50, knowledge 5 and 5; make 8 and 8, read 10 and 9, other 0;
  - wording tier: make 18 of 20, and 33 of 36 on tuning;
  - tuning: reading 96 and 93 caught, knowledge 17 and 17; image 32 and 31.
- **Round 2's M2, M3 and K1 are fixed by small changes,** and a test holds each one (m14–m17 are
  killed).
- **No drive-by edits.** `git diff 3426ff3..199d529 -- src/` is empty. The model's instructions and
  schema are untouched. There is no new import and no swallowed error. No commit carries AI
  attribution; all 16 carry the owner's identity and the `GP-Agent` trailer.
- **The held-out gates pass**, and `check_records` passes with no findings.

## Producers of hardened invariant(s)

- **"A genuine search gets the note only when a code signal and the model's doubt agree, or when the
  text has no word or is only small talk"** (D-169 clause 4 as amended; D-184 clause 1).
  - Producer: `inputReading` (`Reading.swift:459-466`). Its only feeder is `TieredRouter.read`
    (`Router.swift:717-721`), on every tier. The doubt is `pastedContent || instructsTheApp ||
    asksAFact`.
  - Citing tests: `ReadingTests.swift::testTheDecisionTable`,
    `::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote` (`:587`),
    `::testASearchThatNamesTheAskerAnAIOrATaskIsNoQuestionOfFact` (`:654`),
    `::testAnApostropheSuffixIsNoAsker` (`:742`), `::testContentAfterAColonMayAskOrNameAI` (`:748`),
    `::testNoGenuineTuningQuestionTripsASignal`.
  - Gaps: R1 (no model to weigh the fact signal).
- **"Only a request to make an image is overridden to unmeasured: never on code, and beyond `vision`
  only a new image or the asker's own"** (D-184 clause 3).
  - Producer: `TieredRouter.read` (`Router.swift:711-714`) with `InputSignals.makesAnImage` and
    `asksForANewOrOwnImage`.
  - Citing tests: `::testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` (`:605`),
    `::testAQuestionAboutASiteOrADocumentThatMentionsAnImageKeepsItsSurface` (`:631`),
    `::testAQuestionAboutAnImageInASiteOrAFileKeepsItsSurface` (`:704`),
    `::testANewImageOrTheAskersOwnIsUnmeasuredWhereverItWasRouted` (`:726`),
    `::testTheImageRuleNeverOverridesAnotherSurface` (`:321`).
  - Gaps: the invariant does not hold (B1); untested branches (M2).

## Acceptance criteria evidence

The W4 criterion (`docs/plans/m19-plan.md:41`) and the wave plan's P1–P5
(`docs/plans/m19-wave-4-plan.md:96-102`):
- **P1 #177:** `5fe0793`; `tests/unit/test_ios_client_contract.py:210` (`RETIRED_HELD_OUT`). The
  held-out gates pass (5 passed).
- **P2:** the bars were committed with the baseline at `a34453b`. Record §2 (`:50-63`) is unchanged.
- **P3 #66:** `Reading.swift:164-213`, `Router.swift:717-721`. Tests at `ReadingTests.swift:522`,
  `:587`, `:654` and `:742`. Measured in record §4 and §6.
- **P4 #113:** `Router.swift:711-714`, `Reading.swift:226-350`. Tests at `ReadingTests.swift:577`,
  `:605`, `:631`, `:704` and `:726`. **Not met: B1.** The reach beyond `vision` comes out.
- **P5:** D-184 (`docs/decisions.md:4184`); REQ-ASK-005, REQ-RTR-005 and REQ-IMG-003 (`docs/prd.md:532`,
  `:468`, `:550`). REQ-IMG-003 and D-169's pointer overstate the code (B1).
- REQ-ASK-005 → `Reading.swift:164` + `ReadingTests.swift:522`, `:654`, `:742`. The classes at `:515`,
  `:626` and `:695` cite it.
- REQ-IMG-003 → `Router.swift:711` + `ReadingTests.swift:605`, `:704`, `:726` (classes at `:515`,
  `:626`, `:695`).
- REQ-RTR-005 → `Router.swift:711` + `ReadingTests.swift:605`. The class at `:515` now cites it
  (round 2's M6.2).

## K.8 contract drift check

The wave plan's contracts (`docs/plans/m19-wave-4-plan.md:112-123`), `grep -n` at `199d529`:

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:226:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:459:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:210:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:27:    func testProbe() async throws {
```

- Names and signatures are as planned. Only the line numbers have moved.
- There is one new internal symbol, `InputSignals.asksForANewOrOwnImage` (`Reading.swift:312`). Its
  only caller is `Router.swift:712`. `namesASiteOrADocument` is gone.
- There is no `/v1` field or route, and no new closed field.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Reading.swift:253-266` (since M18). **On `vision`, an image noun
  followed by the possessive "'s" counts as the verb's object.** `wordsOf` splits "photo's" into
  `photo` and `s`, and `s` is no modifier head. So "fix my photo's ocr errors", a reading question,
  is told "not measured" on `vision` (at `3426ff3` too). The same split makes "edit this photo's alt
  text" a request off `vision` (B1). This is a bug of low reach. **Fix:** read the word after the "s"
  as the head ("photo's ocr", "photo's alt") before the modifier check.

## Risks queued to next M

- **R1** `ios/ModelRanking/Engine/Router.swift:717-721`. **Rounds 1 and 2's R1 stands.** On a device
  without Apple Intelligence (most devices), the fact signal asks about its own reading, with no model
  verdict to weigh it. The sign that it is real: a stranger's first-use set (#91), run on the wording
  tier, that asks about more than 4 of 40 genuine searches.
- **R2** **The M19 held-out sets are spent but still registered as live** (record §7). Three rounds of
  fixes have now been replayed on them. The sign: a later wave citing a `*_heldout_m19_*` figure as a
  held-out result instead of retiring the sets when a fresh one lands.
- **R3** **No set measures B1's class.** The "only mention images" rows of every tuning and held-out
  set were overridden 0 times at every commit of three rounds, while each reviewer's probe found
  dozens. A next attempt at #113 measured only on such sets would pass its guard and still override
  these questions. The sign: a fresh set whose "other overridden" guard reads 0 while a probe written
  with "my", "this" and "a" finds overrides.

## Gates and probes run

- **Red check:** `b2723f8` extracted to scratch (`ios/` and `scripts/router_probe/`). `swift test
  --filter Reading`: only the four new tests fail (49 assertions).
- **Whole Swift suite** at `199d529`, in a scratch copy with `scripts/router_probe/` beside it: 484
  tests, 0 failures, 106 s.
- `pytest tests/unit/test_ios_client_contract.py -k "held_out or signal_word or heldout or retired"`:
  5 passed. `scripts/check_records.py`: PASS, no findings.
- **`TieredRouter` probes:** a scratch test file (not in the repository), copied into scratch copies of
  `ios/` at `3426ff3`, `671b305` and `199d529`. It ran 98 made-up lines through `ScriptedModelRouter`,
  a wording tier answering the named surface, and the real `SimilarityRouter`. It ran 14 more at
  `199d529`: round 2's lines with "the" changed to "my", "this" or "our". A second scratch file
  ran 25 made-up lines through the signals (M2, M3, K1).
- **Replays:** `ReplayProbe.swift` for the model-tier runs, and a scratch wording-tier replay that
  rebuilds the recorded pick and decline. Both ran through `199d529` (checked against `review2-*`: 0
  rows differ) and through a scratch vision-only copy (B1's cost). Scored with `score_w4.py`, counts
  only, never `--show` on a held-out set.
- **Mutants:** 17, in a scratch copy with `scripts/router_probe/` beside it, each against the whole
  Swift suite. Each file was restored from saved bytes in a `finally` and checked by sha256. Both files
  match the worktree's (`Reading.swift` 30507ab0…, `Router.swift` 9bb7e78c…). 7 were killed and 10
  survived (M2).
- `make check-fast` was not run: it depends on `make install`, and this seat runs no installers. Its
  legs were run directly: the Swift suite above, the held-out gates, and `check_records`.
- No on-device probe was run: no `ReadingProbe` and no model call. No installer, `launchctl`, `simctl`
  or `xcodebuild` was run, and nothing that opens an app or a browser. No `os.abort()` was used. The
  worktree is unchanged except this file (`git status`), and HEAD is still `199d529`.

*Filled by: Code-Reviewer seat (independent, round 3) · Date: 2026-10-07 · Commit range: `3426ff3..199d529`*
