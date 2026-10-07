---
record_type: review
id: m19-wave-4-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19-W4 Code Review: reading the question, a second round

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `3426ff3..ae2c528` (7 commits; 55 files, +48579 / -51, of which 41 files are probe sets
and run outputs).
**Risk tier:** HIGH (`docs/plans/m19-plan.md:96`, `docs/plans/m19-wave-4-plan.md:13-15`). What the
on-device model's output decides (D-126) is touched, and `ios/ModelRanking/Engine/Router.swift` is a
security glob. By D-172 no security seat runs on the wave.
**Verdict:** MAJOR
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`. Then I read the milestone plan (§1 W4, §2 W4, the W4
amendment), the wave plan, issues #66, #113 and #177, and D-169 and D-147. Then I read the diff. I
read the commit messages last. I did not read the author's scratch files.

**Summary.** The wave's measurement is sound. Every number in the record and in D-184 follows from the
committed run files through `score_w4.py`. The bars were committed with the baseline (`a34453b`)
before any variant ran, and they are applied as the plan's rules say. The red commit is red: on
`1ef5657`, the 7 new tests fail and the old ones pass. `ReplayProbe` is exact for a code-only variant
on model-tier runs. I replayed the reference runs through `ae2c528` and got the committed `kb-*` and
`ic-*` files back, row for row. The stopped second runs are stated in the record (§3). The held-out
sets were not fed into the tests: every new test string is a tuning row. `make check-fast` passes.

Two things should be fixed before the pull request goes to the owner. Both are about genuine
searches, which the owner ranks first.

1. **MJ1.** The image rule now reaches `web-dev` and `document`, but `makesAnImage` was only ever made
   safe for `vision`. Ordinary website and document questions that mention an image are now told
   "not measured" and kept in the gap register. This is the class the M18 reviews ruled BLOCKING
   twice (B4). The wave plan's own guard against it ("no website, page, app or code word") was
   dropped, and the test that claims to hold it cannot fail.
2. **MJ2.** The fact signal's exclusions do not hold what D-184 says. A capital "I" or "AI" escapes
   them under the Turkish case folding, and iOS capitalizes "I". Model names, "chatbot" and
   "assistant" are not excluded. The Turkish "hangisi" ("which one") reads a typical Turkish model
   search as a question of fact. Such searches are asked about on every tier, and get the note when
   the model also says "something else".

Six MINORs follow:
- M1: `sağlık` alone is small talk.
- M2: one held-out catch rests on a word no tuning row holds in the app's matching.
- M3: `ReplayProbe` accepts a wording-tier run.
- M4: four mutants survive.
- M5: record drift.
- M6: "make" and "yap" widen pasted content.

## Verdict

MAJOR

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MAJOR (fix in this wave, before the pull request opens)

- **MJ1** `ios/ModelRanking/Engine/Router.swift:710-714`; `ios/ModelRanking/Engine/Reading.swift:231-234`,
  `:268`; `ios/EngineTests/ReadingTests.swift:321-342`. **Since the image rule left `vision`,
  ordinary questions about a website or a document that mention an image are told "not measured"
  and kept in the gap register.**
  - The override now fires on every surface but `coding` and `agentic-coding` whenever `makesAnImage`
    is true. `makesAnImage` was narrowed at M18 for `vision` only.
    - Its English branch reads "fix", "remove", "change" or "make" followed by an image noun as making
      an image.
    - Its Turkish branch has no modifier rule. It now counts "yap" (do or make) as an image verb, in
      every request form (`yap`, `yapın`, `yapabilir`, `yapar mısın`), after any image noun within
      four words.
  - **Probe** (questions I made up). I ran them through `TieredRouter` in a scratch copy, with a
    scripted model that routes each one to the surface a careful reader would. All 13 came out as
    `assistant`, `unmeasured: true`, with `recordsGap` true:
    ```
    fix the broken image on my wordpress site        web-dev
    make images load faster on my website            web-dev
    change the background image of my website        web-dev
    remove the background image from my css          web-dev
    make the hero image full width in tailwind       web-dev
    fix the logo alignment in my navbar              web-dev
    remove the image border in my html               web-dev
    sitemdeki resimleri düzelt, yüklenmiyorlar       web-dev
    web sitem için resim galerisi yap                web-dev
    sitem için resim yükleme sayfası yap             web-dev
    react ile resim galerisi sayfası yap             web-dev
    fix the image placement in my latex document     document
    make the images in my pdf smaller                document
    ```
    At `3426ff3`, `makesAnImage` was already true on 10 of the 13. Only `vision` was overridden then,
    so each kept its ranking. The three "… yap" lines are new, through "yap".
  - **The precedent.** This is the M18-W3 reviews' B4 (`docs/reviews/m18-wave-3-review-round-1.md`
    B4; `m18-wave-3-rereview.md` B4). The reader is told the question is not measured, which is
    false, and the owner's register keeps it as a need to build. D-169's #113 paragraph
    (`docs/decisions.md:3385-3388`) still says "a question about code or a website that mentions an
    image is not overridden".
  - **The plan kept a guard; the build dropped it.** The wave plan's P4 (a) reads "where … no
    website, page, app or code word is in the question (the M18 reviews' B4 line)"
    (`docs/plans/m19-wave-4-plan.md:100`). The built rule replaces that with a test on the surface
    that protects only code (D-184 clause 3). No deviation is named.
  - **The test cannot fail on it.** At `ae2c528`, none of the `web-dev` lines in
    `testTheImageRuleNeverOverridesAnotherSurface` makes `makesAnImage` true (I ran each). A rule that
    overrides `web-dev` on any image noun passes them. The test's new comment says "a question about a
    website … that mentions an image is no request to make one". The code does not hold that.
  - **Why the measure did not see it.** The 20 held-out questions that only mention images had no
    override on either tier. The M18 sets did not show B4 either. The class is still ordinary input.
  - **Fix.**
    1. On surfaces other than `vision`, bring back the plan's guard. Override only when no
       site/page/app/css/html/navbar/document/pdf/latex word is in the question (with the Turkish
       site/sayfa/uygulama/belge), or when the image is a making verb's object with no "on/in my
       site".
    2. Give the Turkish branch the English modifier rule: an image noun followed by `galerisi`,
       `yükleme`, `bölümü` or `sayfası` is a modifier. Or narrow `yap` to the question form after an
       image noun, which is what D-184 clause 3 describes.
    3. Add lines of this kind, each from a tuning row or made up, to the must-not-override test with
       their surface named, so that the test is red on today's rule.

- **MJ2** `ios/ModelRanking/Engine/Reading.swift:143-160`, `:170`, `:174-179`. **The fact signal's
  exclusions do not hold what D-184 clause 1 says ("naming no model or AI, no asker"). So genuine
  searches are asked about on every tier, and get the note when the model also says "something
  else".**
  1. **Capital "I" and "AI" escape the exclusions under the Turkish folding.** `asksAFact` is true
     when either fold reads a fact (`folds(text).contains`, `:144`), and each fold checks its own
     exclusions. Turkish lowercasing turns "I" into `ı` and "AI" into `aı`. Neither is in
     `factExclusions`. iOS capitalizes "I" as the reader types. Probe at `ae2c528`:
     ```
     Where can I run llama locally                       fact     (with "i": not)
     When should I use opus instead of sonnet            fact     (with "i": not)
     How much should I pay for a coding assistant        fact     (with "i": not)
     Who has the most accurate AI for medical questions  fact     (with "ai": not)
     How much does an AI subscription cost               fact     (with "ai": not)
     ```
     The tests' one "asker" negative is lower-case (`ReadingTests.swift:542`), so no test sees this.
  2. **No model's name, and no word for an AI tool but "ai", "llm", "gpt" and "yapay zeka", is
     excluded.** "claude", "gemini", "chatgpt", "deepseek", "chatbot", "assistant", "asistan" and
     "bot" all pass.
  3. **The Turkish "hangisi" ("which one") alone makes a question of fact** (`:170`). In this app,
     `X için hangisi` and `en … hangisi` are how a Turkish reader asks for a model. Only "iyi",
     "iyisi" and "model…" exclude it.

  Of the 49 made-up searches I ran, 42 read as a question of fact at `ae2c528`, and none did at
  `3426ff3`. Among them:
  ```
  kodlamada en güçlüsü hangisi          çeviri için en uygun hangisi        ödev için hangisi
  tıbbi sorularda hangisi daha doğru bilgi veriyor                       kodlamada kim önde
  who leads in coding                   what is good for coding in rust     what's good for writing a novel
  what is the most accurate chatbot for medical questions                 how much does claude cost
  when to use opus vs sonnet            where to run llama locally          claude kaç para
  ```
  Through `TieredRouter` (scratch copy): with the model's "a model search", the reading is `unsure`
  (asked). With "something else", it is `notASearch`, the note. On the wording tier it is `unsure`.
  - The held-out set showed this once. One of the genuine searches asked was asked on the fact
    signal's "which one" (record §4). The bounds held there, but the classes above are the
    product's ordinary input, and half of that input is Turkish.
  - **Fix.**
    1. Decide the exclusions over every fold: a fact only if no fold holds an excluded word (or add
       `ı` and `aı`). Add a capital "I" negative and an "AI" negative to `testAQuestionOfFactIsRead`.
    2. Exclude the names of the AI tools people type. Take them from tuning rows, so #117's check
       stays quiet, or read them from the served registry's makers and families.
    3. Read "hangisi" only in a frame of fact, or drop it and keep `hangi yıl`. Re-score the reading
       tuning set (knowledge 18 of 22 today) to show the cost.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Reading.swift:134`. **`sağlık` ("health") is now a small-talk word,
  and small talk decides alone. A one-word search `sağlık` gets the note even when the model says "a
  model search".** Probe: `TieredRouter` gives `notASearch` with "a model search", with "something
  else", and on the wording tier. `sağlık ok` reads the same way. The word came in for `eline sağlık`
  ("thanks for your effort"). **Fix.** Match `eline sağlık` as a phrase in the small-talk
  check, as `rolePhrases` match phrases, and take `sağlık` out of the single words.
- **M2** `ios/ModelRanking/Engine/Reading.swift:170` ("nerede"), `:176` (`öner`);
  `docs/decisions.md:4205`; `docs/research/m19-w4-question-reading-probe.md` §4. **Two words the wave
  added are held, in the way the app matches them, only by a live held-out set. One held-out
  knowledge catch in every final run depends on one of them.**
  - The app matches both whole: `factWordsTurkish.contains` and `factExclusions.contains`.
  - "nerede" ("where") as a whole word occurs in one row of `notasearch_heldout_m19_questions.json`
    and in no tuning row. The tuning sets hold only "nereden" (in a retired M18 row).
  - `öner` ("recommend") as a whole word occurs in one held-out row. The tuning rows hold only
    `önerir`, `önermez` and `önerirsin`.
  - Both entered at `de8c3f8`, after the set was written (`5fe0793`). That is #177's pattern.
  - #117's check stays quiet because it matches every entry at a word's start, with any ending (K1).
  - Their origin is plausible. Each is the Turkish twin of an English word on the same list. But
    D-184 clause 2 and `de8c3f8`'s message say "Every word added is in a tuning row", and in the
    app's own matching that is not so.
  - **Effect, counted.** I recompiled `Reading.swift` without the two words and ran the signals over
    the held-out set. One knowledge row loses the fact signal, and it is one that every final run
    caught: `unsure` in both model runs (the model said "search") and in both wording runs. So the
    knowledge measure is 5 and 5 of 20 without "nerede", against the reported 6 and 6. Not-a-search
    is 24 and 26 of 50, against 25 and 27. No bar changes. `öner` changes no held-out row.
  - **Fix.** State this in §4 of the record and in D-184 (or drop "nerede" and report 5 and 5), and
    correct "every word added is in a tuning row". If they stay, write their origin into the record.
    `HELD_OUT_ONLY_REVIEWED` cannot hold them until K1 changes the matcher: the check refuses a
    reviewed entry it does not flag.
- **M3** `scripts/router_probe/ReplayProbe.swift:23-28`. **A replay is exact for a model-tier run,
  but the harness also accepts a wording-tier run, and there it is not exact.**
  - **Why it is exact for model-tier runs.** The model's prompt reads nothing that `Reading.swift`
    or `TieredRouter.read` defines (`InputSignals` is used only at `Router.swift:711-718`).
    `ModelOutputBoundary.outcome` (`Router.swift:583-605`) carries a surface, the tier, a decline
    and a reading of `.unsure` or `.search`. The replay rebuilds exactly those, and `read` uses
    nothing else. I checked it: replaying `v0-*` through `ae2c528` gives the committed `kb-reading`
    runs 1 and 2 and `ic-image` runs 1 and 2 with no row different in surface, `unmeasured` or
    reading.
  - **Where it is not.** A `PROBE_TIER=wording` run also has `routed`, `declined` and `model` on
    every row, so it passes the guard. Its manual-tier rows (`routed: "nil"`: 49 of 100 and 25 of 50
    on the held-out sets) are copied unchanged, with the old code's reading. The new signals never
    reach them.
  - The record ran the wording tier fresh, so nothing measured is affected.
  - **Fix.** Refuse a run whose rows carry `tier` or `model: "nil"`. Or rebuild a manual row as
    `RoutingOutcome(categoryID: unmeasuredFallback, tier: .manual, unmeasured: true)` and read it.
- **M4** `ios/ModelRanking/Engine/Router.swift:710`; `ios/ModelRanking/Engine/Reading.swift:148`,
  `:153`; `ios/EngineTests/ReadingTests.swift:515`. **Four mutants survive the Reading, RouterBoundary,
  FrontDoor and ScreenPath tests.** Each was planted in a scratch copy and restored byte-identical
  (sha256 checked):
  1. `agentic-coding` taken out of the override's exclusion.
  2. The act-verb exclusion taken out of `asksAFact`.
  3. `word.hasPrefix("model")` turned into `word == "model"`, so "models" and "modeli" no longer
     exclude.
  4. The openers matched anywhere in the question, not only at its start.

  Nine others were killed, among them the fact signal unwired from `read`, no `factExclusions`, the
  length bounds, "hangisi", "yap" and `sağlık`. Also, `ReadingSecondRoundTests` cites REQ-ASK-005 and
  REQ-IMG-003 but not REQ-RTR-005, although the PRD cites
  `testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` as REQ-RTR-005's evidence. **Fix.** One
  case each: an `agentic-coding` line that trips `makesAnImage` and keeps its surface, an act-verb
  negative, a "models"/"modeli" negative, and a question with "who" or "when" in the middle. Cite
  REQ-RTR-005 on the class.
- **M5** `docs/decisions.md:3303-3410`, `:4196-4210`; `docs/prd.md:550`; `docs/plans/m19-plan.md:234-239`;
  `ios/ModelRanking/Engine/Reading.swift:1`, `:361-366`. **The records say less than the code does,
  or more.**
  1. D-169 carries no "**Amended by D-184 (2026-10-07)**" line, and its #113 paragraph still reads
     as current. Amended ADRs in this file each carry one (e.g. `docs/decisions.md:688`, `:1079`).
  2. D-184 clause 1 lists the forms of a question of fact without "hangisi", the word behind the
     held-out question that was asked, and without "how much / long / far / old / big / high /
     tall". Clause 3 says "'make' asked as a question after an image", but the code reads every
     request form of "yap" (MJ1). Clause 2's "Every word added is in a tuning row" is M2.
  3. REQ-IMG-003 says the rule overrides "nothing else". What was measured is 0 of the 20 held-out
     questions that only mention images (MJ1).
  4. The plan's guard "coding, as a guard on any change to the model's instructions"
     (`m19-wave-4-plan.md:65`) owed a coding-set run for #66 (a) and (c) and #113 (b). None is in
     `docs/research/m19-w4-runs/`, and the record does not say so. None of the three was built, so
     nothing that ships is affected.
  5. The stopped second runs are stated in the record (§3), but not in the plan amendment, which
     says only "three variants were run per problem".
  6. `Reading.swift`'s header and `inputReading`'s comment still name D-169 as amended at M18-W3,
     with pasted content and an instruction as the only doubts.

  **Fix.** Add the pointer to D-169. Correct the three D-184 clauses and the REQ-IMG-003 phrase. Add
  one line each to the record and the amendment for the coding-guard runs not made and the stopped
  runs. Name the fact signal and D-184 in the two comments.
- **M6** `ios/ModelRanking/Engine/Reading.swift:294`, `:298`, `:53-66`. **"make" and "yap" as verbs
  of acting widen pasted content to searches typed with a colon.** Probes:
  ```
  make vs cmake: which is better for c++                pasted (asked)
  React ile todo uygulaması yap: hangi model en iyisi   pasted (asked)
  ```
  Both were plain searches at `3426ff3`. The model-word exclusion reads only the text before the
  colon. These are edge cases, and each costs one question back. **Fix.** Also skip the colon rule
  when the text after the colon names a model or opens with "which" or "hangi". Add one negative of
  each kind.

### PASS (what looks good)

- **The numbers follow from the run files.** I ran `score_w4.py` on every committed run.
  - Baseline: model 18 and 21 of 50 caught, knowledge 1 and 3, make-image 2 and 1, read reaching
    `vision` 10 and 9. Wording: 8 and 8, 0 and 0, 14 and 14, 4 and 4.
  - Variants: reference 69 and 67 of 109; (a) 76; (b) 97 and 94 (knowledge 18 and 18); (c) 93.
    Image: 24 and 23; 29 and 28; 35 (other overridden 7); 32 and 31. Wording 25 → 33 of 36.
  - Final: 25 and 27 of 50, knowledge 6 and 6, genuine 0 noted, 2 and 1 asked, on surface 32 and 29;
    make-image 8 and 8 (model) and 18 and 18 (wording); read 10 and 9 and 4 and 4; other overridden
    0. All match the record's §2–§4, D-184 and the PRD rows.
- **The bars are applied as the plan's rules say.** Each is computed from the lower baseline run:
  1 + ⌈2/3·19⌉ = 14 for knowledge and for make-image on the model tier; 14 + ⌈2/3·6⌉ = 18 on the
  wording tier; 28 − 2 = 26 and 14 − 2 = 12 for surface; 9 − 1 = 8 and 4 − 1 = 3 for read. They were
  committed at `a34453b`, with the baseline runs and `ReplayProbe`, before any variant run. The
  table did not change after.
- **Fresh runs, not replays, for the held-out measure.** `final-*` differs from `base-*` in the
  model's own answers (21–28 surfaces, 11–14 verdicts on the reading set). The `kb-*`, `ia-*` and
  `ic-*` runs carry `v0-*`'s answers exactly, as replays should. `ka-*`, `kc-*` and `ib-*` were fresh,
  as variants that change the model must be. The wording-tier runs are identical run to run.
- **The deviations are stated.** "(a) and (c) ran once", and "(b)'s … second was stopped" (record
  §3). The misses are read and listed only after the last measure (§4). `score_w4.py` refuses
  `--show` on a held-out set.
- **Held-out integrity.** No held-out question appears whole in code, tests or tuning sets. The only
  5-word overlaps with code and tests are stock phrases ("which model is best at") and two tuning
  rows that open the way a held-out row does. Every test string the wave added is a tuning row (I
  checked all 44). The 17 `HELD_OUT_ONLY_REVIEWED` entries are each in `Reading.swift` at
  `23a81da`, as their notes say. #117's check passes. On the
  three retired M18 sets, no genuine row trips the new fact or image signals; only 4 "ambiguous"
  rows read as a fact.
- **Red first.** On `1ef5657`, the 7 `ReadingSecondRoundTests` fail (38 assertions) and the 32 other
  tests of `ReadingTests`, `ReadingThroughTheTiersTests` and `ReadingFaultTests` pass. The stub
  `asksAFact { false }` keeps the build.
- **The decision of D-184 clause 4 is in the code.** The diff does not touch `requestGuidance`, the
  hints or the schema.
- **No drive-by edits.** `.language-allow` gains only the new Turkish sets and run folder. No
  swallowed errors, no new import, no AI attribution; all 7 commits carry the owner's identity and
  the `GP-Agent` / `GP-Task` trailers.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **"A genuine search gets the note only when a code signal and the model's doubt agree, or when the
  text is no word or only small talk"** (D-169 clause 4 as amended; D-184 clause 1).
  - Producer: `inputReading` (`Reading.swift:368-375`), fed only by `TieredRouter.read`
    (`Router.swift:715-719`), on every tier.
  - Citing tests: `ReadingTests.swift::testTheDecisionTable`,
    `::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote` (`:586`),
    `::testSmallTalkIsANoteWhateverTheModelSays`, `::testNoGenuineTuningQuestionTripsASignal`.
  - Gaps: small talk decides alone on `sağlık` (M1); the fact signal's exclusions (MJ2).
- **"Only a request to make an image is overridden to unmeasured, and never on code"** (D-184
  clause 3).
  - Producer: `TieredRouter.read` (`Router.swift:710-714`).
  - Citing tests: `::testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted` (`:604`),
    `::testTheImageRuleNeverOverridesAnotherSurface` (`:321`),
    `::testARequestToMakeAnImageRoutedToVisionIsUnmeasured`.
  - Gaps: website and document questions (MJ1); the `agentic-coding` half is held by no test (M4).

Gaps: MJ1, MJ2, M1, M4.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

The W4 criterion (`docs/plans/m19-plan.md:41`): "Knowledge questions and requests to make an image are
read better than M18's measure, on a fresh held-out set, measured twice, against bars set after the
baseline (D-169 clause 6)."

- **Fresh sets by an independent seat:** `5fe0793` (`scripts/router_probe/*_heldout_m19_questions.json`);
  M18's sets retired in the same commit (`tests/unit/test_ios_client_contract.py:210-214`). Seat
  independence is a declaration I cannot check. The commits show the order and the "unread" claim.
- **Bars after the baseline, before variants:** `a34453b`.
- **Read better, twice per tier:** knowledge 1 and 3 → 6 and 6 of 20; make-image 2 and 1 → 8 and 8
  (model) and 14 → 18 (wording). Bars missed and stated: knowledge 14, make-image (model) 14, catch
  40. Sent to the owner as the valve says (`docs/plans/m19-plan.md:234-239`).
- **REQ-ASK-005** → `ios/ModelRanking/Engine/Reading.swift:143-179` (`asksAFact`), `:129-136`,
  `:97`, `:116`, `:294-298`; `Router.swift:715-719`. Tests: `ReadingTests.swift:522`, `:548`,
  `:556`, `:567`, `:586` (the class at `:515` cites REQ-ASK-005). Holes: MJ2, M1, M6.
- **REQ-IMG-003** (the refusal half) → `Router.swift:710-714`; `Reading.swift:203-205`, `:268`,
  `:283`. Tests: `ReadingTests.swift:576`, `:604` (cites REQ-IMG-003). Hole: MJ1.
- **REQ-RTR-005** → `Router.swift:710-714`, `ReadingTests.swift:604`. The test does not cite the id
  (M4). Hole: MJ1.

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `ios/ModelRanking/Engine/Reading.swift` | `asksAFact`, its openers, Turkish words and exclusions; small talk, act verbs, instruction verbs and role phrases widened; image stems `yap`, `fotograf`, `degistir` | MJ1, MJ2, M1, M2, M6 |
| `ios/ModelRanking/Engine/Router.swift` | `read`: the override on every surface but code; the fact signal as a doubt | MJ1, M4 |
| `ios/EngineTests/ReadingTests.swift` | `ReadingSecondRoundTests` (7); two lines changed off questions of fact; `genuineQuestionsOfFact` | MJ1, M4 |
| `ios/EngineTests/test-manifest.txt` | the 7 tests | ok |
| `scripts/router_probe/ReadingProbe.swift` | `PROBE_TIER=wording`; `declined` | ok |
| `scripts/router_probe/ReplayProbe.swift` | new: a recorded run read again | M3 |
| `scripts/router_probe/notasearch_heldout_m19_questions.json`, `image_heldout_m19_questions.json` | the fresh sets | M2 |
| `tests/unit/test_ios_client_contract.py` | `RETIRED_HELD_OUT` +3; `HELD_OUT_ONLY_REVIEWED` rewritten (17 entries, each checked) | K1 |
| `docs/research/m19-w4-runs/score_w4.py` | the scorer | ok |
| `docs/research/m19-w4-runs/*_w4.json` (2) | the tuning sets: 306 and 82, deduplicated as the plan says | ok |
| `docs/research/m19-w4-runs/*-*.json` (39) | runs: baseline, final, variants, replays | ok (each scored) |
| `docs/research/m19-w4-question-reading-probe.md` | the record | M2, M5 |
| `docs/decisions.md` | D-184 | M2, M5 |
| `docs/prd.md` | REQ-ASK-005, REQ-IMG-003, REQ-RTR-005 | M5 |
| `docs/plans/m19-plan.md`, `docs/plans/m19-wave-4-plan.md` | the W4 amendment; the wave plan | MJ1, M5 |
| `.language-allow` | the Turkish sets and runs | ok |

## K.8 contract drift check

The wave plan's contracts (`docs/plans/m19-wave-4-plan.md:112-123`), `grep -n` at `ae2c528`:

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:192:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:368:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:210:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:27:    func testProbe() async throws {
```

- Same names and signatures. `makesAnImage` (148 → 192), `inputReading` (324 → 368),
  `RETIRED_HELD_OUT` (208 → 210) and `testProbe` (22 → 27) moved only because lines were added
  above them.
- No `/v1` field or route; `git diff 3426ff3..ae2c528 -- src/` is empty. No new closed field: the
  #113 (b) variant was not built.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_ios_client_contract.py:1639-1655`, `:1609`. **#117's check matches every
  entry at a word's start with any ending, while the app matches several lists whole.** So a whole
  word that only a held-out set holds, and whose stem a tuning row carries, goes unflagged:
  "nerede" (tuning "nereden") and `öner` (tuning `önerir`), M2.
  - The check also skips lists of one literal (`STRING_LIST` needs two or more, so the openers
    `["who"]`, `["when"]`, `["where"]` and `["whats"]` are unread).
  - It also skips inline literals (`"ne"`, `"zaman"`, `"hangi"`, `"yıl"`, `"model"` in
    `asksAFact`), as the W3 review's M8 said for the older ones.
  - An enhancement: take the match mode from how the app matches each list (whole word, phrase or
    stem), and read one-literal lists.
- **K2** `ios/ModelRanking/Engine/Reading.swift:53-66` (since M18). **The same fold gap as MJ2 in
  `pastedContent`'s search exclusion.** Typed "AI" folds to `aı` in Turkish, so the "ai" exclusion
  misses it. "Summarize PDFs with AI: which is best?" and "Translate with AI: which one is cheapest"
  read as pasted content at `3426ff3` and at `ae2c528`; in lower case they do not. A bug, low
  reach: audit every exclusion list for the dotless `ı` once MJ2's fix lands.

## Risks queued to next M

- **R1** `ios/ModelRanking/Engine/Router.swift:715-719`. **On a device without Apple Intelligence,
  the fact signal alone asks.** Every false positive of MJ2 is a question back there, with no model
  verdict to weigh it against. The held-out wording run asked 1 of 40 genuine searches. What would
  show the risk is real: a stranger's first-use set (#91), run with `PROBE_TIER=wording`, asking
  more than 4 of 40.
- **R2** `ios/ModelRanking/Engine/FrontDoor.swift` (`recordsGap`). **The owner reads the gap
  register to decide what to build (REQ-GAP-002).** Every website or document question overridden
  by MJ1 lands there as an unmet need. What would show it: register entries on the owner's phone
  whose text is about a site, a page or a PDF.

## Gates and probes run

- `make check-fast` with the guard-bin stubs on `PATH`: **PASS** in 110.3 s. Lint, typecheck,
  records, client-decls. Test: 2071 passed, 25 skipped; `--derive` "CI will skip 83 of 2096", the
  budget 83. swift-test-parallel: 476 tests, exactly the manifest. `git status` clean afterwards,
  HEAD unchanged.
- `pytest tests/unit/test_ios_client_contract.py -k "held_out or signal_word or heldout"`: 5 passed.
- `score_w4.py` on all 39 run files against their sets (the PASS section).
- **Red check:** `1ef5657` extracted to scratch. The Reading tests there: 7 fail, the rest pass.
- **Replays:** `ReplayProbe.swift` in a scratch copy at `ae2c528`, on `v0-reading` 1 and 2, `v0-image`
  1 and 2, and `base-notasearch-1` and `base-image-1`. The first four reproduce the committed `kb-*`
  and `ic-*` exactly (M3).
- **Signals harness:** `Reading.swift` at `ae2c528` and at `3426ff3`, compiled with a small `main`.
  It ran 141 made-up questions, the 34 lines of the M18 reviews' B4, the 210 rows of the retired M18
  sets, and the held-out set (counts only; no held-out text is quoted here). A variant without "nerede" and `öner` was compiled for M2.
- **`TieredRouter` probes:** a scratch test file (not in the repository) with `ScriptedModelRouter`,
  for MJ1, MJ2 and M1.
- **Mutants:** 13, in a scratch copy, each restored byte-identical (sha256). Four survived (M4).
- No on-device probe was run, no `ReadingProbe` model run, no installer, `launchctl`, `simctl` or
  `xcodebuild`, nothing that opens an app or a browser, no `os.abort()`. Nothing in the worktree was
  edited except this file.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-07 · Commit range: `3426ff3..ae2c528`*
