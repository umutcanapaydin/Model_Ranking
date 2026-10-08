---
record_type: review
id: m20-hotfix-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 hotfix Code Review, round 2 (D-186, D-187)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the hotfix and was not the first reviewer)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `origin/main..4023df2` (the first review's fixes: `e01db20` red tests, `4023df2` fix)
**Risk tier:** HIGH (the router)

The owner's rulings D-186 and D-187 are not argued here. This round checks whether the first review's
findings are fixed, and probes the rebuilt keyword list (`CategoryHints.surfaceWords`, `agentWords`,
`namedSurface`, `plain`) for collisions.

## Verdict
BLOCKING

## How it was checked

- `make check-fast` in the worktree: PASS in 113 s (lint, typecheck, records, test, client-decls,
  swift-test). The worktree is clean afterwards and still at `4023df2`.
- A scratch copy of the Swift package outside the worktree (since deleted) with a probe test. For
  each made-up question it printed `CategoryHints.namedSurface`, then `TieredRouter(model: nil).route`
  with the keywords on, then the same route with `namedSurface` turned off (a scratch-only switch).
  That shows the keyword tier's answer and what the English embedding would have said without it.
  About 135 questions, English and Turkish, written to cause collisions. They show that the misroutes
  happen, not how often.
- One planted fault in the scratch copy: the D-187 clause 4 branch (`Router.swift:814`) turned off.
  `testTheModelsDeclineOnASearchGoesToTheWordingTier` failed 3 assertions, so the new test holds it.
- Nothing under `scripts/router_probe/*_heldout_m19_*` was read.

## The first review's findings

| Id | Status | Evidence |
|---|---|---|
| B1 | **Fixed** | Time words and `google` are gone from `search` (`Router.swift:284-286`), `news` is a whole word, `şu an` is gone, and `coding` is read before `search`. Probed: `what is the best coding model right now` and `is google gemini good for coding` go to `coding`, `implement binary search in python` to `coding`, `write a newsletter for my team` names nothing, and `bu araştırma makalesini özetle` goes to `document`. Held by `KeywordRoutingTests.swift:100-119`. |
| B2 | **Mostly fixed** | `react`, `book`, `click`, `booking`, `express`, `awk`, `script`, `program`, `exception`, `sorgula`, `make updates`, `mantıklı`, `çizelge`, `responsiveness`, `best airline`, `ajanda` and the browser agent all route correctly now. Two lines B2 named still misroute: `which model can solve math problems by itself` and `user agent string parsing in python` both go to `agentic-coding`. They are carried in M1 below. |
| M1 | **Fixed** | `KeywordRoutingTests.swift:123-140` covers both cases (the decline on a search, and a doubt keeps the model's outcome), and the planted fault turns it red. |
| M2 | **Fixed** | `plain` (`Router.swift:295`) reads both spellings. `KeywordRoutingTests.swift:88-97` holds it. Probed in capitals and with a dotted `İ`: `KOD YAZAN YAPAY ZEKA`, `İNTERNETTE ARAMA YAPAN MODEL` and `TIBBİ SORULAR İÇİN MODEL` all route right. The folding made no two keywords equal that I could find. |
| M3 | **Fixed** | `Router.swift:438-440` returns the named surface. |
| M4 | **Partly fixed** | There is now a 20-line negative table (`KeywordRoutingTests.swift:100-119`). The order table asked for each pair of rules that both match one question; three lines were added (`:144-150`). `assertRoutes` still cannot tell a keyword match from an embedding match. Carried in M6 below. |
| M5 | **Fixed** | REQ-RTR-005, REQ-ASK-003 and REQ-IMG-003 (`docs/prd.md:468`, `:531`, `:550`), `docs/architecture.md:261-264`, the `unmeasuredHints` comment (`Router.swift:117-120`), the `_REMOVE_ALSO` comment (`public.py:41-42`) and INV-87's citations were all updated. |
| K1 | **Filed** | #205 (open). |
| R1 | **Stands** | No issue. D-187's "Revisit when" is the trigger it names. |

## Findings

### BLOCKING (must fix before the hotfix ships)

- **B1** `ios/ModelRanking/Engine/Router.swift:257-268` together with `:288-290`: the `coding` rule
  has `yazilim` but no English word for software or a developer. Meanwhile `everyday` matches the
  app's standard question form (`which model*`, `best model*`, `best ai`, `which ai`, `en iyi model*`,
  `hangi model*`, `yapay zek*`). So a common way to ask the app's main question gets a keyword match
  to the wrong board, labelled "matched on wording".
  Failure scenario, run through `TieredRouter(model: nil)`. Each of these went to `everyday` on a
  keyword match:
  `which model is best for software engineering`, `best model for software development`,
  `best ai for developers`, `best ai for a junior developer`, `which model is best for writing software`,
  `which llm is best for app development`, `which model is best for building an ios app`,
  `best model for mobile development`, `which model is best at swe-bench`, `best model for leetcode`,
  `best model for php`, `best model for c++`, `which model knows ruby on rails best`,
  `which model is best for next.js`, `mobil uygulama geliştirmek için en iyi model`,
  `uygulama geliştirmek için hangi yapay zeka`, `c++ için en iyi model`. Meanwhile
  `yazılım geliştirmek için hangi model` and `best model for programmers` go to `coding`. Without the
  keywords the embedding is no better here: it says `everyday` or `web-dev`. So this is not a
  regression. But the hotfix is meant to send coding questions to the coding board, and these are
  among the most common ways to ask one.
  Fix: in `coding`, add the stem `software`, and `developer` as a stem (`developers`,
  `developer's`). Add the phrases `app develop*`, `mobile develop*`, `ios app*`, `android app*`,
  `uygulama gelistir*`, `mobil uygulama*`, `swe`, `leetcode` and `php`. Match `c++`, `c#`, `f#` and
  a `.js` name such as `next.js` on the raw lower-cased text, because `wordsOf` splits them on their
  symbols. Leave out `rust`, `go` and `swift` as single words: each has a second reading (rust on a
  bike, "go", "a swift reply"). Use phrases (`in rust`, `rust code`, `go programming`, `swift code`),
  or leave them to the embedding. Add each line above to a positive table.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Router.swift:243-246`, `:304-312`: `agentic-coding` is read first.
  Several of its phrases need no coding word, against the commit's own rule ("agent only beside a
  coding word"). The `agentWords` pre-check also takes a "user agent" or "real estate agent" for an
  agent that codes when any coding word appears in the question.
  Failure scenario (all go to `agentic-coding`): `which model can solve math problems by itself` and
  `user agent string parsing in python` (both named in the first review's B2),
  `which ai can do my homework by itself`, `can a model learn on its own`,
  `kendi kendine ingilizce öğrenmek için hangi yapay zeka`,
  `kendi kendine yazılım öğrenmek için en iyi yapay zeka`, `kendi başına ödev yapan yapay zeka`,
  `explain how autonomous cars work`, `en iyi ajan filmleri hangileri` (`ajan` also means a spy),
  `write a python script for my real estate agent`. `kendi kendine` ("on one's own") is an everyday
  Turkish phrase.
  Fix: move `on its own`, `by itself`, `kendi basina`, `kendi kendine`, `autonomous`, `otonom` and
  the bare `ajan` words behind the same rule as `agentWords`: they name `agentic-coding` only with a
  coding word. In the pre-check, require the agent word next to the coding word (`coding agent`,
  `kod ajanı`, `agent` within two words of `code` or `repo`), not anywhere in the sentence.

- **M2** `ios/ModelRanking/Engine/Router.swift:247-256`: `computer-use` reads only narrow phrases,
  and `web-dev` reads any `website` or `site`. So the usual way to ask for computer use (an AI that
  operates a site for me) is read as building one. Here the keyword overrides an embedding that got
  it right. D-187 clause 1 gives "a click through a site before a web site" as its example.
  Failure scenario: `which ai can browse websites and buy things for me` goes to `web-dev` (the
  embedding said `computer-use`). `which model can log into a website and download my invoices`,
  `which model can fill forms on a website` and `an ai that can shop on websites for me` go to
  `web-dev`. `best model for automating tasks in my browser` goes to `everyday` (the embedding said
  `computer-use`). `which model can control my computer` and `which model can operate my mac for me`
  go to `everyday`.
  Fix: add to `computer-use` the phrases `for me` or `benim yerime` together with a site word, and
  `browse*`, `log into`, `fill* form*`, `shop on`, `buy * for me`, `control my computer`,
  `use my computer`, `operate my`, `automat* * browser` and `using a computer`. Add an order table
  for `computer-use`/`web-dev`.

- **M3** Turkish everyday words, `Router.swift:254`, `:257`, `:264`, `:273`, `:281`, `:284`. Each line
  below goes to the wrong board on a keyword match. Without the keywords, each is "not understood".
  - `["zeka", "soru*"]` (`abstract`) also matches the word after `yapay zeka`, the Turkish term for
    AI: `yapay zeka soru çözücü öner` and `yapay zeka sorularına en iyi cevap veren model` go to
    `abstract`. "AI question solver" is a common Turkish phrase.
  - `haber` (`search`) is also "let someone know" (`haber ver`): `toplantıya geç kalacağımı haber ver`
    and `müdürüme izne çıkacağımı haber veren bir mail yaz` go to `search`.
  - `jest` (a gesture) and `git` ("go!") go to `coding`: `sevgilime romantik bir jest öner`,
    `markete git ve alışveriş listesi yap`.
  - `site` is also a housing estate and `sitem` is "a reproach": `site yönetimine dilekçe yaz` and
    `arkadaşıma sitem eden bir mesaj yaz` go to `web-dev`.
  - `programla` is also "schedule": `bu haftaki toplantılarımı programla` goes to `coding`.
  - `olasilik` as a stem matches `olasılıkla`, "probably": `büyük olasılıkla hangi model daha iyi`
    goes to `mathematics`.
  Fix: skip `zeka soru*` when `yapay` comes before it. Read `haber` only with `son`, `güncel` or
  `bul`, or drop it. Make `jest` a phrase (`jest ile`, `jest test*`) and `git` a phrase (`git commit`,
  `git merge`, `git ile`). Drop `site` and `sitem`, which `web site*` and `sitesi` already cover.
  Make `programla` a phrase (`programlama dili`). Make `olasilik` whole words (`olasilik`,
  `olasiligi`, `olasiliklar`). Add each line to the negative table.

- **M4** English everyday words, `Router.swift:250-252`, `:255-258`, `:264-268`, `:275`, `:283`. Each
  goes to the wrong board on a keyword match:
  - The `code` and `kod` stems also read dress, tax, civil, zip and discount codes:
    `what is the dress code for a wedding`, `which ai knows the turkish tax code best`,
    `explain the civil code on inheritance` (the embedding said `expert`), `posta kodu nedir` and
    `indirim kodu nasıl kullanılır` go to `coding`.
  - `bug`, `pandas` and `query`: `i caught a stomach bug, which ai gives the best medical advice`,
    `how many pandas are left in the wild` and `i have a query about my phone bill` go to `coding`.
  - The `app*` ending of a phrase reads any word that starts with "app": `how to express appreciation
    to my team` goes to `coding`, and `how should i react appropriately when my boss yells` goes to
    `web-dev`.
  - `script that` and `a script to` read speech and video scripts: `write a script that i can read at
    my wedding` and `i need a script to pitch my startup to investors` go to `coding`.
  - `landing` is a stem: `was the moon landing faked` goes to `web-dev` (the embedding said
    `factuality`).
  - `book a`: `is this book a good read`, `summarise the book a colleague lent me` and
    `write python code to book a meeting room` go to `computer-use`, which is read before `document`
    and `coding`.
  - `fill in form*` reads `formulas`: `how do i fill in formulas in excel` goes to `computer-use`.
  - `law` reads `mother-in-law` (`wordsOf` splits on the hyphens), so a birthday message goes to
    `expert`. `document` reads `documentary` and `contract` reads `how do muscles contract`; both go
    to `document`.
  - `search` with no coding word: `explain how binary search works` goes to `search`.
  Fix: make `code` and `kod` name `coding` only when no `dress`, `zip`, `post*`, `posta`, `tax`,
  `civil`, `promo`, `discount`, `indirim` or `qr` comes before them. Use `app`, `apps`,
  `application*` in place of `app*`. Make `landing` the phrase `landing page*`. Make `book a` the
  phrases `book a table`, `book a flight` and `book a room`, or move `computer-use` below `coding` and
  `document`. Use `form`, `forms`. Skip `law` when the raw text has `-in-law`, or read it only in
  phrases (`the law`, `law firm`, `turkish law`). Make `document` the words `document`, `documents`,
  `documentation`. Add `binary search` and `search algorithm` to `coding`. Leave out `bug` (or keep
  `bugs` in code phrases only), `pandas` (keep `pandas dataframe` or `pandas ile`) and `query` (keep
  `sql query`). Add each line to the negative table.

- **M5** `ios/ModelRanking/Engine/Router.swift:271`: `make up`, `making up` and `makes up` send a
  request to *invent* something to `factuality`, the board that ranks models by how little they
  invent. Failure scenario: `make up a bedtime story for my kid`, `which model is best at making up
  stories`, `best ai to make up a name for my bakery` and `how do i make up with my friend after a
  fight` all go to `factuality`. (Without the keywords the embedding also sent the second one to
  `factuality`.) Fix: keep `make up` only with a subject that invents facts (`make up facts`,
  `make up sources`, `make up citations`, `makes things up`, `made up numbers`), and add the lines
  above to the negative table.

- **M6** `ios/EngineTests/KeywordRoutingTests.swift:18-26`, `:144-150`: the first review's M4 is half
  done. `assertRoutes` asserts `tier == .similarity`, which an embedding match also gives, so a
  positive line passes when the keyword is lost and the embedding happens to agree. The order tables
  for `computer-use`/`coding`, `agentic-coding`/`computer-use`, `computer-use`/`web-dev` and
  `web-dev`/`expert` were not written. Failure scenario: a word is dropped from the list in a later
  edit and the English positive tables stay green. Fix: in `assertRoutes`, also assert
  `CategoryHints.namedSurface(question, within: known) == surface` for lines meant to match on a
  keyword. Add the order tables, and the B1 and M1 to M5 lines.

## Risks queued to next M

- **R1** (carried from the first review): the keyword list is hand-written and is now read before
  the embedding.
- **R2** The `everyday` phrases (`Router.swift:288-290`) match the app's standard question form. For
  an English question that contains `which model`, `best model` or `best ai`, the sentence similarity
  now picks only the alternatives: the keyword names `everyday` first. D-187 clause 5's floor
  ("not understood") is reached only by a question that lacks those phrases. On the probes this was
  about as often right as the embedding (`which model is best at reasoning` goes to `everyday`, where
  the embedding said `abstract`; `best model for writing emails` goes to `everyday`, where the
  embedding said `web-dev`). But every gap in a more specific rule now shows up as a confident
  `everyday` (B1). Revisit with the owner's planned next step, the on-device model building the list.

## K.8 contract drift check

`RoutingOutcome`, `QuestionRouter`, `TieredRouter.read` and `public.derive` keep their signatures.
`CategoryHints.plain` and `agentWords` are new, and only `namedSurface` uses them. Verdict: OK.

## K.9 candidates spotted outside this wave's scope

None new.
