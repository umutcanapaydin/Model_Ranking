---
record_type: review
id: m19-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19-W4 Code Review, round 2: reading the question, a second round

**Reviewer:** Code-Reviewer subagent, a new seat with fresh eyes. I wrote none of this wave's code,
tests or records, and I was not the first reviewer.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..6c9ce17` (the whole wave, 12 commits; the answer to round 1 is `1e9a92a`
red tests, `671b305` fixes, `c4ce22e` records, `6c9ce17` the rename of round 1's file).
**Risk tier:** HIGH (`docs/plans/m19-wave-4-plan.md:13-15`). What the on-device model's output decides
(D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a security glob. By D-172 no
security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I read the profile and `.agents/rules/practices.md` from `origin/main`, then the
wave plan, round 1's review, the code at `6c9ce17`, the tests, and the records. I read the commit
messages after the code. I did not read any other seat's scratch files. Every probe line below is
made up for this review or is a tuning row; no held-out question is quoted or used.

**Summary.** Most of round 1 is fixed, and fixed red-first. The numbers in the record's §6 follow
from the committed runs. `make check-fast` passes. Round 1's four surviving mutants are now killed.

One finding must be fixed before the close. **B1:** round 1's MJ1 is fixed for its own thirteen
lines, not for the class.
- The new guard (`namesASiteOrADocument`) is a short word list. I wrote 31 new questions about an
  image in a website, a store or a document, each a web or document task. 24 of them are still told
  "not measured" and kept in the gap register, on both tiers.
- The guard also over-corrects. 8 of 19 new requests to make an image for a site are no longer
  caught on `web-dev`.
- The records say the class is closed (REQ-IMG-003, D-184 clause 3).

The rest is MINOR:
- **M1:** MJ2's named defects are fixed. The fact signal still reads most search phrasings whose
  topic or tool is not on its lists.
- **M2:** a Turkish name with the suffix `'i` is read as the English "I".
- **M3:** M6's fix makes the colon rule miss pasted content that mentions AI or opens with "which".
- **M4:** the new guard has the K2 case-folding gap ("App Icon").
- **M5:** three new rules have no test that holds them.
- **M6:** record drift, including a duplicate record id left by the rename.

## Verdict

BLOCKING

## Round 1's findings, one by one

| Round 1 | Fixed? | Evidence |
|---|---|---|
| **MJ1** image rule overriding site and document questions | **Partly. Open as B1.** | The 13 lines keep their surface (`ReadingTests.swift:631-650`). The Turkish modifier rule is in (`Reading.swift:260-266`, `:297`) and is killed by mutant m8. The class is open: 24 of 31 new lines are still overridden (B1). |
| **MJ2** fact signal reading genuine searches | **Yes, for what it named; the class is MINOR (M1).** | The exclusions now hold over every folding (`Reading.swift:163-173`): mutant m9 (Turkish fold only) is killed. AI tool names, tasks and Turkish stems were added (`:198-208`). "hangisi" is out (`:191-194`). |
| **M1** `sağlık` alone is small talk | **Yes.** | `eline sağlık` is matched as a phrase (`Reading.swift:131-146`). Tests: `ReadingTests.swift:670-679`. Mutant m13 is killed. |
| **M2** `nerede`, `öner` held only by the held-out set | **Yes.** | `nerede` is out of the list, and `öner` is matched as a stem (`Reading.swift:194`, `:208`). The record's §6 reports the cost (knowledge 6 → 5). D-184 clause 2 is corrected (`docs/decisions.md:4206-4211`). |
| **M3** ReplayProbe accepts a wording-tier run | **Yes.** | It refuses any row that has `tier` (`ReplayProbe.swift:26-30`). `ReadingProbe.swift` writes `tier` on every wording row and on no model row. |
| **M4** four mutants survive | **Yes for the four. The REQ-RTR-005 citation is only half done (M6).** | m1–m4 were replanted in a scratch copy and are killed by `ReadingSecondRoundReviewTests`. The new class cites REQ-RTR-005. The class whose test the PRD names for REQ-RTR-005 still does not (`ReadingTests.swift:515`). |
| **M5** record drift | **Mostly.** | Done: D-169 points to D-184 (`decisions.md:3411`); D-184 clauses 1–3 are rewritten; the coding guard that was not run and the variants that ran once are in record §3 (`:90-92`) and in the amendment (`m19-plan.md:234-242`); both comments in `Reading.swift` name D-184. Not done: REQ-IMG-003 now claims more than the code does (B1), and `Router.swift:702` still says "as amended at M18-W3" (M6). |
| **M6** "make"/"yap" widen pasted content | **Yes for its lines, but the fix over-corrects (M3).** | `Reading.swift:60-67`; tests `ReadingTests.swift:683-688`; mutant m11 is killed. |
| **K1** #117's matcher | **Filed** as #186 (open, `enhancement`). | `gh issue view 186`. |
| **K2** "AI" fold gap in `pastedContent` | **Fixed there** (`Reading.swift:54-59`). | The same gap appears in the new `namesASiteOrADocument` (M4). It is also in `makesAnImage` since M18 (K1). |
| **R1**, **R2** | Carried. | R2 is real while B1 stands. |

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `ios/ModelRanking/Engine/Router.swift:706-714`; `ios/ModelRanking/Engine/Reading.swift:298-330`
  (`namesASiteOrADocument` and its lists), `:245-258` and `:273-276` (the English branch reads
  "fix", "make", "remove" and "edit" as making an image); `docs/prd.md:550` (REQ-IMG-003);
  `docs/decisions.md:4212-4219` (D-184 clause 3); `ios/EngineTests/ReadingTests.swift:631-650`.
  **The fix for MJ1 holds round 1's thirteen lines and leaves the class open. Ordinary website,
  store and document questions that mention an image are still told "not measured" and kept in the
  owner's gap register. The records say this no longer happens.**
  - **Probe.** I wrote 31 new web and document questions. I ran each through `TieredRouter` in a
    scratch copy of `ios/`, with `ScriptedModelRouter` naming the surface a careful reader would,
    and again through a wording tier that answers that surface.
    - 24 of 31 came out `assistant`, `unmeasured: true`, `recordsGap` true, on both tiers.
    - At `3426ff3` (the code that ships), every one of the 31 kept its surface.
    - The sample, all routed to `web-dev` unless marked:
    ```
    fix the image alignment for my website          make images load faster for my website
    fix the broken image in my shopify store        make images load faster on my blog
    fix the hero image on my homepage               remove the image shadow in my squarespace theme
    make the logo bigger in the header of my blog   fix the images not showing in my next.js project
    make the avatar round with border radius        fix the logo position in the footer
    edit the image src with javascript              make the photos clickable in my portfolio
    blogumdaki resimleri düzelt, açılmıyorlar       sunumdaki resimleri küçük yap
    make the images smaller in my powerpoint (document)   fix the image placement in my word doc (document)
    ```
  - **Why it leaks:**
    1. Any word not on the list leaves the question open to the rule: blog, store, shop, homepage,
       theme, header, footer, project, portfolio, powerpoint, word, excel, `sunum`, `mağaza`.
    2. The new "for" exception (`Reading.swift:316`) is meant for "a logo for my website". It also
       excuses edit questions ("fix the image alignment for my website", "make images load faster
       for my website"). So the fix adds holes of its own.
  - **It over-corrects too.** Of 19 new requests to make an image that name a site, all 19 are
    caught at `ae2c528`, and only 11 at `6c9ce17`. The 8 that were lost keep `web-dev`: "design a
    logo to put on my website", "design an image for the header of my website", "generate a hero
    image to use on my landing page", "create a banner image for the homepage of my site",
    `web sitemde kullanmak için bir logo tasarla`, `sitemin ana sayfası için bir görsel oluştur`, and
    two more. The tuning sets did not show this cost (record §6: no request lost). I replayed the
    wording-tier tuning run through `6c9ce17`: 33 of 36, unchanged.
  - **Why the measure does not see it.** No question that only mentions an image was overridden in
    the held-out or tuning sets, at `ae2c528` or at `6c9ce17`. Their phrasings do not use "fix/make
    the image …" as a command. The M18 reviews' B4 lines and round 1's lines did, and so do mine. The
    must-keep test holds only round 1's lines, so it was fitted to the probe that found the defect.
  - **The records claim the class is closed.**
    - REQ-IMG-003 (`prd.md:550`): "after the code review it no longer overrides a question about an
      image in a website or a document".
    - D-184 clause 3 (`decisions.md:4214-4216`): "beyond `vision` a question about an image in a
      website, an app or a document is about that".
    - The comment at `Router.swift:709-711`.
    - The code holds this for a list of 25 English words and 4 Turkish stems.
  - **Why it blocks.** The M18-W3 reviews ruled this class (B4) BLOCKING twice, and round 1 ruled it
    MAJOR. Against the code that ships, the wave makes these questions worse: they kept their
    ranking at `3426ff3`. The owner reads the gap register to decide what to build (REQ-GAP-002), so
    each wrong override lands there as a false need (R2).
  - **Fix.** One way that needs no site vocabulary, offered as a starting point and not as the only
    one:
    1. Beyond `vision`, read only two kinds of request.
       - A new image: a making verb with an image that is new. That is "make me/a/an …",
         "generate/create/design/draw/illustrate/paint a(n) …", or "… of …". In Turkish, a bare image
         noun before `tasarla`, `oluştur`, `üret` or `çiz`.
       - A change to the asker's own image: "my/this/our photo, selfie, portrait or picture". In
         Turkish, a first-person possessive (`fotoğrafım-`, `fotom-`, `resmim-`) or `bu`.
       - "the image" or "images" after "fix", "make", "remove" or "edit" is about a site or a file,
         so it keeps its surface.
    2. By my count this keeps every off-`vision` catch in the tuning runs. On the model tier those
       are "make me a logo", "design a logo", "make me an app icon" and "… logo tasarla". On the
       wording tier they add "remove the background from my product photo" and "retouch this
       portrait". It frees all 24 of my lines, and it brings back the 8 lost requests.
    3. If the site guard stays, apply its "for" and `için` exceptions only to the making verbs, and
       decide its exceptions over every folding (M4).
    4. Add lines of both kinds to the tests. Any of the probe lines above may be used; they are made
       up. Then replay the tuning runs on both tiers, and correct REQ-IMG-003, D-184 clause 3 and the
       `Router.swift` comment to say what the code holds.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Reading.swift:174-205`; `docs/decisions.md:4198-4205`. **MJ2's
  named defects are fixed. But the fact signal still reads most ways of asking for a model when the
  topic or tool is not on its lists. D-184 clause 1 says it names "no task".**
  - **Probe.** I wrote 50 new searches. 42 read as a question of fact at `6c9ce17` (43 at
    `ae2c528`). Among them:
    ```
    what's good for python            who is the leader in reasoning      who's the top for rust
    who is most accurate on medical questions    who has the biggest context window
    matematikte kim önde              tıpta kim daha doğru cevap veriyor   hukuk sorularında kim daha güvenilir
    perplexity kaç para               when to use perplexity               where can you run qwen locally
    ```
  - **Cost.** A question back on every tier, and the note when the model also says "something
    else". Measured on the spent held-out set it is small: 1 and 0 of 40 genuine searches asked
    (record §6). That is why this is MINOR.
  - **The other side.** The widened exclusions now drop knowledge questions that use a tool's name as
    an ordinary word: "who painted water lilies, claude monet?", "when did the gemini program
    launch", "who composed opus 131", "who cracked the enigma code". 18 of my 28 knowledge questions
    are read, against 24 at `ae2c528`. Missing a knowledge question is the safe direction.
  - **Fix.** Make D-184 clause 1 say that the exclusions are lists, and give their measured cost.
    Or read the evaluative frame of a search as one: "good for", "the leader in", "the top for",
    `kim önde`, `kim daha …`. Add one such line per language to
    `testASearchThatNamesTheAskerAnAIOrATaskIsNoQuestionOfFact`.
- **M2** `ios/ModelRanking/Engine/Reading.swift:163-170`, `:201`, `:399-401`. **A Turkish proper
  name with the suffix `'i` is read as the English "I", so the question is excluded.** `wordsOf`
  splits at the apostrophe, and the lone `i` is in `factExclusions`. `Hamlet'i kim yazdı` and
  `Everest'i ilk kim tırmandı` are not read; `Mona Lisa'yı kim çizdi` is. This came in with the
  signal (`de8c3f8`) and misses in the safe direction. **Fix.** Drop a one-letter token that follows
  an apostrophe before the exclusion check. Add `Hamlet'i kim yazdı` to `testAQuestionOfFactIsRead`.
- **M3** `ios/ModelRanking/Engine/Reading.swift:60-67`. **M6's fix over-corrects. Pasted content
  after a plain order is no longer read if the text after the colon opens with "which"/"hangi" or
  mentions a model, "AI" or "LLM" anywhere.**
  - All 11 of my made-up pasted lines lost the signal (each had it at `ae2c528`):
    ```
    translate into turkish: which train goes to the airport?
    özetle: yapay zeka modelleri son yıllarda hızla gelişti ve birçok sektörü etkiledi
    summarize: the new AI act regulates high-risk systems across the EU
    make this shorter: the LLM landscape changed a lot in 2025
    ```
  - In an app about AI models, pasted text about AI is likely. Each line loses one doubt: from the
    note to a question back, or from a question back to a ranking.
  - **Fix.** Use the after-colon exemption only when the order before the colon is "make"/"yap" (the
    verbs M6 was about). Or use it only when the text after the colon is a short comparison
    question ("which is better", "hangisi daha iyi"). Add one pasted line of each kind as a positive
    case.
- **M4** `ios/ModelRanking/Engine/Reading.swift:303-319`. **The new `namesASiteOrADocument` has
  round 1's K2 case-folding gap.**
  - It returns true if *any* folding names a site, but it decides its exceptions separately in each
    folding. Turkish folding turns "Icon", "Image" and "Illustration" into `ıcon`, `ımage` and
    `ıllustration`, which `isImageNoun` does not know.
  - Through `TieredRouter`: "make me an app icon, flat style, green" (a tuning row) is told "not
    measured" on `web-dev`. "make me an App Icon, flat style, green" keeps `web-dev`.
  - `Web sitem İçin logo tasarla` misses the `için` exception the same way.
  - **Fix.** Excuse a site word if any folding excuses it. Or read English words only in the default
    folding. Add a capitalised "App Icon" line to `testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted`.
- **M5** `ios/ModelRanking/Engine/Reading.swift:315`, `:201`; `ios/ModelRanking/Engine/Router.swift:712`.
  **Three of the new rules have no test that holds them.** I planted 18 mutants in a scratch copy,
  ran the whole Swift suite, and restored each file (byte-compared). 13 were killed. These three
  survive:
  - m5: the `için` exception removed. `web sitem için logo tasarla` on `web-dev` is then not
    overridden, and no test sees it.
  - m10: `"i"` removed from `factExclusions`. Every "I" line in the tests also holds another
    excluded word ("llama", "opus", "coding").
  - m18: the site guard also applied on `vision`. The comment at `Router.swift:707` says `vision`
    keeps the rule "as M18 built it". No test sends a request to make an image that names a site to
    `vision`.

  Two more survivors are not counted: one equivalent mutant (m12) and one that is right for English
  (m14, M4). **Fix.** Add one line for each of the three.
- **M6** Record drift.
  1. `docs/reviews/m19-wave-4-review-round-1.md:3`. The rename at `6c9ce17` kept
     `id: m19-wave-4-review`, which is this file's id. `scripts/check_records.py` (R3) refuses a
     duplicate id. Every other round-1 file uses its file name as its id
     (`m19-wave-2-review-round-1.md:3`). Fix: `id: m19-wave-4-review-round-1`.
  2. `ios/EngineTests/ReadingTests.swift:515`. The PRD cites
     `testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` as REQ-RTR-005's evidence
     (`prd.md:468`), but its class cites only REQ-ASK-005 and REQ-IMG-003. Round 1's M4 asked for
     the id on this class; it went on the new class instead. REQ-RTR-005's row also does not cite
     the new keep-its-surface test.
  3. `ios/ModelRanking/Engine/Router.swift:702`: `read`'s doc comment still says "D-169 as amended
     at M18-W3". It should name D-184.
  4. `tests/unit/test_ios_client_contract.py:1584-1589`: the reason `_AFTER_MEASURE` says an
     exclusion or a modifier "can only lower its catches". That is not true in general:
     - an exclusion can stop a genuine search being asked about, which improves the score;
     - a modifier can let a request to read an image reach `vision`.

     I checked the five words. Without them, no row of either held-out set reads differently, in any
     run. So nothing was inflated. Write that measured fact as the reason, not the general claim.
  5. Issue #186 links to `docs/reviews/m19-wave-4-review.md` for round 1's K1. That path is now this
     file. It should be `-round-1.md`.

### PASS (what looks good)

- **The post-review numbers follow from the runs.** `score_w4.py` on the committed runs:
  - `review-notasearch` 1 and 2: not a search 24 and 26 of 50; knowledge 5 and 5; genuine noted 0
    and 0, asked 1 and 0; on surface 32 and 29.
  - `review-image` 1 and 2: make told 8 and 8; read reaching `vision` 10 and 9; other overridden 0
    and 0.
  - `revieww-*`: make 18; read 4; knowledge 5; genuine asked 0.
  - Tuning `review-reading`: 96 and 93 caught, knowledge 17 and 17 (from 18), genuine asked 15 and 8
    (unchanged). `review-image`: 32 and 31, read 21 and 21, other 0.
  - Each matches record §6 (`m19-w4-question-reading-probe.md:169-183`).
  - I replayed `finalw-*` (the wording tier) through `6c9ce17` with a replay that rebuilds manual
    rows. It matches the fresh `revieww-*` runs row for row (0 of 150 differ). So §6's wording
    figures are the code's.
- **Red first.** I built `1e9a92a` in a scratch copy. Its four new tests fail (47 assertions), and
  the other 41 `Reading*` tests pass. `671b305` turns them green.
- **The five `_AFTER_MEASURE` words came from round 1's text.**
  - `galerisi`/`yükleme` are in MJ1's fix.
  - "chatbot", "deepseek" and "gemini" are in MJ2's item 2.
  - They change no held-out row (M6.4). The check passes: `pytest -k "held_out or signal_word or
    heldout or retired"`, 5 passed.
- **No drive-by edits.** `git diff 3426ff3..6c9ce17 -- src/` is empty. The model's instructions,
  hints and schema are untouched (D-184 clause 4). There are no swallowed errors and no new import.
  There is no AI attribution in the commits. All 12 commits carry the owner's identity and the
  `GP-Agent` / `GP-Task` trailers.
- **The stopped runs and the coding guard not run are now stated** (record §3, the plan amendment).

## Producers of hardened invariant(s)

- **"A genuine search gets the note only when a code signal and the model's doubt agree, or when the
  text has no word or is only small talk"** (D-169 clause 4 as amended; D-184 clause 1).
  - Producer: `inputReading` (`Reading.swift:439-446`). Only `TieredRouter.read` feeds it
    (`Router.swift:718-723`), on every tier. The doubt is `pastedContent || instructsTheApp ||
    asksAFact`.
  - Citing tests: `ReadingTests.swift::testTheDecisionTable`,
    `::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote` (`:587`),
    `::testASearchThatNamesTheAskerAnAIOrATaskIsNoQuestionOfFact` (`:654`),
    `::testHealthAloneIsNoSmallTalk` (`:670`), `::testNoGenuineTuningQuestionTripsASignal`.
  - Gaps: the fact signal on unlisted searches (M1), Turkish `'i` (M2), the "I" exclusion has no
    test (M5).
- **"Only a request to make an image is overridden to unmeasured: never on code, and beyond
  `vision` never on a question about an image in a website, an app or a document"** (D-184 clause
  3).
  - Producer: `TieredRouter.read` (`Router.swift:712-716`) with `InputSignals.makesAnImage` and
    `namesASiteOrADocument`.
  - Citing tests: `::testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` (`:605`),
    `::testAQuestionAboutASiteOrADocumentThatMentionsAnImageKeepsItsSurface` (`:631`),
    `::testTheImageRuleNeverOverridesAnotherSurface` (`:321`).
  - Gaps: the class beyond round 1's lines (B1); the folding of the exceptions (M4); `için` and
    `vision` have no test (M5).

Gaps: B1, M1, M2, M4, M5.

## Acceptance criteria evidence

The W4 criterion (`docs/plans/m19-plan.md:41`, the wave plan's P1–P5,
`docs/plans/m19-wave-4-plan.md:96-102`):
- **P1 #177:** `5fe0793`, `tests/unit/test_ios_client_contract.py:210` (`RETIRED_HELD_OUT`). The
  held-out gates pass.
- **P2:** the bars were committed with the baseline at `a34453b`. Record §2 (`:50-63`) is unchanged
  since then.
- **P3 #66:** `Reading.swift:162-208`, `Router.swift:721`. Tests: `ReadingTests.swift:522`, `:587`,
  `:654`. Measured in record §4 and §6. Holes: M1, M2.
- **P4 #113:** `Router.swift:712-716`, `Reading.swift:221-330`. Tests: `ReadingTests.swift:577`,
  `:605`, `:631`. Hole: B1.
- **P5:** D-184 (`docs/decisions.md:4184`), REQ-ASK-005, REQ-IMG-003 and REQ-RTR-005
  (`docs/prd.md:532`, `:550`, `:468`). REQ-IMG-003's last clause overstates the code (B1).
- REQ-ASK-005 → `Reading.swift:162` + `ReadingTests.swift:522`, `:654` (classes at `:515` and
  `:623` cite REQ-ASK-005).
- REQ-IMG-003 → `Router.swift:712` + `ReadingTests.swift:605`, `:631` (both classes cite
  REQ-IMG-003).
- REQ-RTR-005 → `Router.swift:712` + `ReadingTests.swift:631` (`:624` cites it). The PRD's named test
  is at `:605`, in a class that does not cite it (M6.2).

## K.8 contract drift check

The wave plan's contracts (`docs/plans/m19-wave-4-plan.md:112-123`), `grep -n` at `6c9ce17`:

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:221:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:439:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:210:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:27:    func testProbe() async throws {
```

- The names and signatures are the same. The lines moved only because code was added above them.
- New internal symbols: `InputSignals.asksAFact` (`Reading.swift:162`) and
  `InputSignals.namesASiteOrADocument` (`:303`). Their only callers are `Router.swift:713` and
  `:721`.
- There is no `/v1` field or route, and no new closed field.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Reading.swift:251-256` (since M18). **The dotless-`ı` gap is also in
  `makesAnImage`'s exclusions.** "Turn This Receipt Photo Into A Spreadsheet" is overridden on
  `vision`: the Turkish folding turns "Into" into `ınto`, so the reading-"into" exclusion misses. In
  lower case it reaches `vision`. It is the same at `3426ff3`. This is a bug of low reach (title
  case). It finishes round 1's K2 audit: decide the exclusions inside `makesAnImage` over every
  folding.

## Risks queued to next M

- **R1** `ios/ModelRanking/Engine/Router.swift:718-723`. **Round 1's R1 stands, and M1 widens it.**
  On a device without Apple Intelligence (most devices), the fact signal asks about its own reading,
  with no model verdict to weigh it. `matematikte kim önde` and "who is the leader in reasoning"
  are asked there. The sign that it is real: a stranger's first-use set (#91), run with
  `PROBE_TIER=wording`, that asks about more than 4 of 40 genuine searches.
- **R2** **The M19 held-out sets are spent but are still registered as live** (record §7). Round 1's
  fixes were checked against them, and they now carry five `_AFTER_MEASURE` entries. The sign that it
  is real: a later wave citing a figure from `*_heldout_m19_*` as a held-out result instead of
  retiring them when a fresh set lands.

## Gates and probes run

- `make check-fast` at `6c9ce17`, with the guard-bin stubs on `PATH`: **PASS** in 60.1 s.
  - Lint, typecheck, records, client-decls.
  - Tests: 2071 passed, 25 skipped. `--derive` says "CI will skip 83 of 2096", within the budget of
    83.
  - swift-test-parallel: 480 tests, exactly the manifest.
  - Run before this file was written: with it, R3 will report the duplicate id until M6.1 is fixed.
- `pytest tests/unit/test_ios_client_contract.py -k "held_out or signal_word or heldout or retired"`:
  5 passed.
- `score_w4.py` on `final-*`, `review-*`, `revieww-*`, `kb-*`, `ic-*` and `fixw-*` (the PASS
  section).
- **Signals harness:** `Reading.swift` at `3426ff3`, `ae2c528` and `6c9ce17`, compiled with a small
  `main`. It ran 31 site and document questions, 19 requests to make an image, 50 searches, 28
  knowledge questions and 13 colon lines, all made up. A copy without the five `_AFTER_MEASURE`
  words was run over both held-out sets, by counts only.
- **`TieredRouter` probes:** a scratch test file in a copy of `ios/` (not in the repository), with
  `ScriptedModelRouter` and a fixed wording tier. It also replayed the wording-tier runs (`finalw-*`
  and `fixw-image_tuning_w4-1`) through `6c9ce17`.
- **Mutants:** 18, in the scratch copy. Each was restored and compared with the worktree's file
  (`cmp`). The results are in M5.
- No on-device probe was run: no `ReadingProbe` and no model call. No installer, `launchctl`,
  `simctl` or `xcodebuild` was run, and nothing that opens an app or a browser. No `os.abort()` was
  used. Nothing in the worktree was edited except this file; `make check-fast` wrote only its
  git-ignored logs. `git status` shows this file alone, and HEAD is still `6c9ce17`.

*Filled by: Code-Reviewer seat (independent, round 2) · Date: 2026-10-07 · Commit range: `3426ff3..6c9ce17`*
