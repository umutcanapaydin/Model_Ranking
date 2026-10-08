---
record_type: review
id: m20-hotfix-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 hotfix Code Review (D-186, D-187)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the hotfix)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `origin/main..adde1cc` (`5be3eb2` red, `a76d8fc` fix, `2bb39d6` red, `adde1cc` fix)
**Risk tier:** HIGH (the router, the hosted artifact's licence filter)

The two rulings (D-186, D-187) are the owner's and are not argued here. This review judges whether
the code does what they say, safely. Plan compliance: the hotfix is outside a wave plan; its scope is
the two ADRs at the end of `docs/decisions.md`.

## Verdict
BLOCKING

## How it was checked

- `make check-fast` in the worktree: PASS in 99 s (lint, typecheck, records, test, client-decls,
  swift-test). The worktree is clean afterwards.
- A scratch copy of `ios/` (not the worktree's) with a temporary probe test that prints, for made-up
  questions, `CategoryHints.namedSurface` and `TieredRouter(model: nil).route`. The English embedding
  has its assets on this Mac. A second scratch copy ran the same probe with `namedSurface` turned off,
  to see what the wording tier did without the keywords.
- One planted fault in the scratch copy (D-187 clause 4 removed), the whole Swift suite run on it,
  then restored by bytes; sha256 `5da39d58…186d` matches the worktree's `Router.swift`.
- The probe questions were written to test collisions. They are not a representative sample, and
  the counts below show that the misroutes happen, not how often.
- Nothing under `scripts/router_probe/*_heldout_m19_*` was read.

## Findings

### BLOCKING (must fix before the hotfix ships)

- **B1** `ios/ModelRanking/Engine/Router.swift:240-241`: `search` comes before every subject
  surface, and its rule uses words that only say *when* (`today`, `latest`, `güncel`, `bugün`,
  `right now`, `şu an`) or name a company (`google`). So the most common form of this app's question
  is ranked on the web-search board. D-187 clause 1 says the *more specific* surface wins. "Right
  now" is less specific than "coding".
  Failure scenario, run through `TieredRouter(model: nil)` (the owner's phone has no on-device
  model). Each of these went to `search` with `unmeasured = false`:
  `what is the best coding model right now`, `best model for coding today`,
  `which is the latest model that is best at math`, `which llm is best today`,
  `şu an kodlama için en iyi model hangisi`, `bugün matematik için en iyi model`,
  `güncel en iyi kodlama modeli`, `is google gemini good for coding`,
  `implement binary search in python`, `write a search function in javascript`. Without the
  keywords, the embedding routed the last two to `coding`.
  The phrase `şu an` is matched word by word on the start of each word, so `şu` matches `şunu`,
  `şuna` and `şu`, and `an` matches every word that starts with `an`: `anla`, `anlat`, `ana`,
  `analiz`. So `şunu anlamadım, e-posta yazmak için hangi model iyi` and
  `şu ana kadar en iyi yapay zeka hangisi` also go to `search`.
  The stem `news` matches `newsletter` (`write a newsletter for my team` goes to `search`; the
  embedding said `assistant`). The stem `araştır` takes `bu araştırma makalesini özetle` to
  `search` instead of `document`.
  Fix: take the time words and `google` out of `search`. If a time word stays, it decides only when
  no later rule matches: read the rules for the subject first and use the time word as a last
  resort. Make `news` a whole word. Match `şu an` as whole words (`şu`, then `an`, `anda` or
  `anki`). Keep `search` before `coding` only for an explicit web search (`search` together with
  `web`, `online` or `internet`). Test each scenario above.

- **B2** `ios/ModelRanking/Engine/Router.swift:231-271`: several stems and whole words are ordinary
  English or Turkish words that do not name a surface. Each sends a question to the wrong board
  before the embedding is consulted. In every English case below, the embedding alone (keywords
  off) chose the expected surface. With keywords on, all of them went to the wrong surface.
  - `react` (a whole word, `web-dev`): `how does the immune system react to a virus` and
    `which chemicals react with water` go to `web-dev`; the embedding said `expert`.
  - `book` (a whole word, `computer-use`, read before `document`):
    `summarise this book in five bullet points` goes to `computer-use`; the embedding said
    `document`.
  - `click`, `booking` (`computer-use`, read before `coding`):
    `my button click handler does not fire in javascript` and
    `build a booking system in django` go to `computer-use`.
  - `agent` (`agentic-coding`, first of all): `a browser agent that books flights for me` goes to
    `agentic-coding`, against D-187's own example ("a click through a site" is `computer-use`). So
    does `user agent string parsing in python`. The phrase `by itself` sends
    `which model can solve math problems by itself` to `agentic-coding`. `ajan` matches `ajanda`
    (a planner): `ajandamı düzenle` goes to `agentic-coding`.
  - In `coding`: `express` matches `expression`, so `simplify the expression 3x + 2x - 4` goes to
    `coding`, not `mathematics`. `awk` matches `awkward` (`help me reply to an awkward email`).
    `script` matches a video script (`write a script for my youtube video`). `program` matches a
    workout or a diet plan (`make a workout program for me`, `diyet programı hazırla`). `exception`
    matches `exceptionally`. `sorgu` matches `sorgula`, "to question": `bu iddiayı sorgula`
    goes to `coding`, not `factuality`.
  - `["make", "up"]` (`factuality`): `up` is matched on the start of the word, so it reads `update`,
    `upload` and `upgrade`. `help me make updates to my cv` goes to `factuality`.
  - `mantık` (`abstract`) matches `mantıklı`, "sensible", a very common word:
    `e-posta yazmak için en mantıklı model hangisi` goes to `abstract`. `çiz` (`vision`) matches
    `çizelge`, "a timetable": `haftalık çalışma çizelgesi hazırla` goes to `vision`.
  - `responsive` (`web-dev`) matches `responsiveness`, which is a speed question. `["best", "ai"]`
    matches `best airline`.
  Fix: make these whole words, or remove them: `react`, `book`, `express`, `awk`, `script`,
  `program`, `exception`, `agent`, `ajan`, `mantık`, `sorgu`, `çiz`, `news`. Where a word is only a
  coding word in context, require a second word with it (`click` with `button`, `event` or
  `handler`; `agent` with `coding`, `code` or `repo`). Read each phrase's last word as a whole word
  (`up`, `an`, `ai`). Move `agentic-coding` and `computer-use` below `coding` unless the question
  also names what the agent does. Test each line above (B1's tests and M4).

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Router.swift:764-769`: D-187 clause 4 (when the model says "none of
  these" on a question it read as a search, the wording tier answers) has no test. I replaced the
  condition with `if false, …` in a scratch copy, and all 501 other Swift tests passed. The one
  failure was a missing fixture path in the scratch copy. Every decline test uses `SilentTier`, so
  the new branch's answer is never checked.
  Failure scenario: the fallthrough is lost in a refactor. On a device with the on-device model,
  every question the model declines is "not measured" again, the bug the owner reported, and the
  suite stays green.
  Fix: a test where `DecliningModelTier` (or `ScriptedModelRouter` with the decline and
  `request = a model search`) is paired with a wording tier that answers. Assert the wording's
  surface, `unmeasured == false` and `tier == .similarity`. Add a second case where the request is
  "something else" (the reading is `.unsure`) and assert that the decline stands.

- **M2** `ios/ModelRanking/Engine/Router.swift:274-275`: `namedSurface` reads only Turkish written
  with Turkish letters. Turkish typed on an English keyboard names no surface, so it is "not
  understood" on the manual tier, the complaint D-187 answers. D-184 already reads such forms for
  the image rule. These made-up questions all came back `assistant`, manual, unmeasured:
  `yazilim gelistirmek icin hangi model`, `tibbi sorular icin en iyi model`,
  `uzun bir sozlesmeyi ozetleyecek model`, `olasilik sorusu icin hangi model`,
  `gorsel uretmek icin en iyi model`.
  Fix: add a third reading with the Turkish letters folded to ASCII (`ı→i`, `ş→s`, `ğ→g`, `ü→u`,
  `ö→o`, `ç→c`) and fold the stems the same way. Check B2's collisions again after folding, then
  test the lines above.

- **M3** `ios/ModelRanking/Engine/Router.swift:392`: when the embedding loads but
  `guard hints.count > 1, let query = vector(text)` fails, the method returns `nil`, and the named
  surface computed at :362 is dropped. The comment at :360-361 promises the opposite.
  Failure scenario: the embedding returns no token vectors for the question, or the engine serves
  one surface with examples. A question that names its surface then goes to the manual tier as
  "not measured".
  Fix: `else { return named.map { RoutingOutcome(categoryID: $0, tier: .similarity, unmeasured: false) } }`,
  as at :370.

- **M4** `ios/EngineTests/KeywordRoutingTests.swift:89-116`: the keyword tests hold the new
  behaviour weakly. Every positive line is built from a word on the list. The only negative test
  (`testAQuestionThatNamesNoSurfaceIsLeftToTheSimilarity`) has three harmless lines. The order test
  has three lines. Nothing checks that an everyday word is *not* read as a keyword, so B1 and B2
  pass all 500 Swift tests. `XCTAssertEqual(outcome.tier, .similarity)` cannot tell a keyword match
  from an embedding match.
  Fix: a negative table on `CategoryHints.namedSurface`: B1's and B2's questions must name nothing,
  or name the right surface. Add an order table for each pair of rules that can both match one
  question: `search`/`coding`, `computer-use`/`coding`, `agentic-coding`/`computer-use`,
  `web-dev`/`expert`.

- **M5** Records that disagree with the code:
  - `docs/prd.md:468` (REQ-RTR-005): the evidence still says a request to make an image routed to
    `vision` "is answered as unmeasured" and that "the rule stays on `vision`", next to a test
    named `…AnsweredFromVision`. Its *Missing* clause (W-123, "ordinary questions still reach a
    measured surface") is now the intended behaviour.
  - `docs/prd.md:531` (REQ-ASK-003): the same *Missing* clause.
  - `docs/prd.md:550` (REQ-IMG-003): it still says "The similarity tier declines a request to make
    an image" and "a rule in code answers one it routed to `vision` as unmeasured".
  - `docs/architecture.md:261-263`: "Only a question that names no surface and scores below the
    wording tier's floor is 'not understood'". This is false for a Turkish question that names no
    surface (`en iyi model hangisi` is never scored and goes to the manual tier), for a device
    without the embedding, and for the model's decline read as `.unsure`.
  - `ios/ModelRanking/Engine/Router.swift:114-136`: the comment on `unmeasuredHints` still says a
    question closer to a decline group "is unmeasured".
  - `src/app/workflows/public.py:41-43`: the comment on `_REMOVE_ALSO` still lists LiteLLM's
    `openrouter/` aliases, which moved to `_COPIES_OF`.
  - `docs/security-invariants.md:167` (INV-87): *Held by* cites
    `test_every_surface_answers_on_the_public_artifact`, which tests D-186 (every surface answers).
    It does not test the invariant.
  Fix: rewrite each line to match the code (the PRD rows' evidence and *Missing* clauses, the
  architecture sentence, the two comments). In INV-87, cite
  `test_the_public_artifact_keeps_every_source_and_every_openrouter_price` or nothing new.

### PASS (what looks good)

- **D-186 does what it says.** `src/app/workflows/public.py:31` `LEFT_OUT = {}`. The OpenRouter
  aliases are removed only while `openrouter` is left out (`_COPIES_OF`, :49-51, :82-83). The vendor
  plans still go (:44-47). The survivors check, the price-median rebuild, `VACUUM` and the atomic
  move are unchanged. The machinery is still tested on planted sources (the `planted` fixture,
  `tests/unit/test_public_artifact.py:24-27`). `test_the_hosted_engine_leaves_out_no_source_on_testflight`
  and `test_the_public_artifact_keeps_every_source_and_every_openrouter_price` (:35-50) hold the new
  state. `test_journey.py` plants every coding board to stay not vacuous.
- **Privacy (D-126, D-160, REQ-RTR-004).** `namedSurface` and `inRow` (`Router.swift:274-292`) are
  pure functions of the question and `known`. They make no I/O, keep no state and log nothing. The
  only thing the router hands on is still a surface id from `known` (`where known.contains(rule.id)`,
  :276), and the image branch checks `known.contains("vision")` (:460). `test_router_hints.py` and
  the client-decls gate pass. Nothing derived from the question leaves the device beyond the
  surface id, which was always sent.
- **The decline groups.** The image group goes to `vision` only when it beats every surface and the
  other two groups (:458-463). Sound, video and speed fall through to the closest surface or the
  floor. #113's override is removed cleanly from `TieredRouter.read` (:786-797), and the reading
  signals still run on every tier.
- `CURRENT_PROJECT_VERSION = 2` (needed for a second TestFlight upload), `xcuserdata/` ignored, and
  the UI tests' `firstMatch` on the doubled "send" control are all correct and in scope.

## Acceptance criteria evidence

- D-187 clause 1 (keywords first, English and Turkish, no model or embedding needed):
  `Router.swift:362`, `:370`, `:449-452`; `KeywordRoutingTests.swift:28-62`. It holds for the words
  listed, with the misroutes in B1 and B2 and the gaps in M2 and M3.
- D-187 clause 2 (image job goes to `vision`): `Router.swift:458-463`;
  `FrontDoorTests.swift::testAnImageJobIsAnsweredFromTheImageBoard`,
  `KeywordRoutingTests.swift::testARequestToMakeAnImageIsAnsweredFromVision`.
- D-187 clause 3 (#113 retired): `Router.swift:786-797`;
  `ReadingTests.swift::testARequestToMakeAnImageRoutedToVisionIsAnsweredFromVision`.
- D-187 clause 4 (model's decline falls through): `Router.swift:764-769`. No test (M1).
- D-187 clause 5 (below the floor stays "not understood"):
  `FrontDoorTests.swift::testTheFloorDecidesAQuestionThatNamesNoSurface`,
  `RouterBoundaryTests.swift:150-158`.
- D-186 / REQ-REL-001 / INV-87: `public.py:31`, `:49-51`;
  `test_public_artifact.py::test_the_hosted_engine_leaves_out_no_source_on_testflight` and the
  `planted` tests.

## K.8 contract drift check

- `RoutingOutcome`, `QuestionRouter`, `TieredRouter.read`, `public.derive` and `public.LEFT_OUT`
  keep their signatures. `CategoryHints.surfaceWords` and `namedSurface` are new and are used only in
  `Router.swift:362`. The `derive` return dict keeps the `openrouter_aliases_removed` key (always
  present, 0 when nothing is left out). Verdict: OK.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/public.py:52-56`: `_SURVIVORS` does not count the `openrouter/` aliases
  that `_COPIES_OF` removes. Only `test_no_openrouter_price_rides_in_under_another_source` would
  catch a typo in `_COPIES_OF`'s key. This is an enhancement to do when `LEFT_OUT` is filled again
  before production (D-186 clause 3).

## Risks queued to next M

- **R1** The keyword list is hand-written and is now read before the embedding. Any word added to
  it can take a question from the surface the embedding would have chosen. A measured
  before-and-after on a fresh labelled set would show whether the list helps overall. The owner's
  next step (the on-device model building the list) is when to revisit it.
