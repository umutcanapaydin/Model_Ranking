---
record_type: review
id: m20-hotfix-review-round-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 hotfix Code Review, round 3 (D-186, D-187)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the hotfix and was neither earlier reviewer)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `origin/main..9dc41c6` (this round's fixes: `dc18ea6` red tests, `28a7668` fix, `9dc41c6` docs)
**Risk tier:** HIGH (the router)

The owner's rulings D-186 and D-187 are not argued here. This round checks the second review's
findings and probes the rebuilt `CategoryHints.surfaceWords` for collisions.

## Verdict
MINOR

The common ways to ask about code, maths, images, documents, search and the other boards now reach
the right board on a keyword. The general phrases no longer act as keywords. The collisions left are
on less common phrasings, not on the common forms (`best ai for X`, `which model is best for X`,
`X için en iyi yapay zeka`, `X yapan yapay zeka`). Each is labelled "matched on wording" and fixed with
one tap. One of them (M1) is new in this round and costs one line to fix, so fix it before the build.

## How it was checked

- `make check-fast` in the worktree: PASS in 123.8 s (lint, typecheck, records, test, client-decls,
  swift-test). The worktree is clean afterwards and still at `9dc41c6`.
- A scratch copy of `ios/` outside the worktree (since deleted) with a probe test. For each made-up
  question it printed `namedSurface`, `generalSurface`, then `TieredRouter(model: nil).route` with the
  keywords on, and the same route with `namedSurface` turned off by a scratch-only switch. That shows
  the keyword's answer and what the English embedding (or the manual fallback) would have said
  without it. 220 questions, English and Turkish: the common forms of "which AI is best for X", the
  second review's failure lines, and lines written to cause collisions. They show that a misroute
  happens, not how often.
- Nothing under `scripts/router_probe/*_heldout_m19_*` was read.

## The second review's findings

| Id | Status | Evidence |
|---|---|---|
| B1 | **Fixed** | `Router.swift:256-280`: `software`, `developer`, `leetcode`, `php`, `ruby`, the app, mobile and SWE-bench phrases, and the `c++`/`c#`/`f#`/`node.js` marks on the raw text. Every B1 line is in `KeywordRoutingTests.swift:77-97`, and `assertRoutes` now asserts the keyword. Probed: `which ai is best for coding`, `best ai for programming`, `which model is best for python`, `best ai for vibe coding`, `which model is best for code review`, `Which AI is best for Coding?!`, `KODLAMA İÇİN EN İYİ YAPAY ZEKA`, `python öğrenmek için en iyi yapay zeka` and `yazılımcılar için en iyi yapay zeka` all go to `coding`. `best model for rust` and `which ai is best for swift` are left to the embedding, as the second review advised. |
| M1 | **Fixed** | `agentic-coding` reads only `agentic` and code-agent phrases (`Router.swift:254-255`), and an agent counts only within two words of a coding word and not after `user`, `estate` and the like (`:353-355`, `:413-420`). Probed: `which model can solve math problems by itself` goes to `mathematics`, `user agent string parsing in python` to `coding`, `kendi başına ödev yapan yapay zeka` to `everyday`. `explain how autonomous cars work` names nothing. Held by `KeywordRoutingTests.swift:165-171`. |
| M2 | **Fixed, with a new collision** | `Router.swift:281-290`. All six M2 lines route to `computer-use` (`KeywordRoutingTests.swift:134-143`), and the order table has a `computer-use`/`web-dev` line (`:153`). The second review asked for `benim yerime` "together with a site word". It went in alone, which is M1 below. |
| M3 | **Fixed** | `zeka soru*` is gone (`:324-326`), `haber` is gone (only `haberler*`, `:333`), `git` and `jest` are phrases (`:271-272`), `site`/`sitem` are only `site kur*`/`yap*`/`olustur*` (`:298-299`), `programla` is `programlama dil*` (`:279`), and `olasilik` is whole words (`:312`). All seven lines are in the negative table (`KeywordRoutingTests.swift:189-192`). Probed: `yapay zeka soru çözücü öner` goes to `everyday`. |
| M4 | **Fixed** | `notAfter` (`:341-348`) blocks dress, tax, postal and discount codes and `-in-law`. `bug`, `pandas` and `query` are gone, `app` is whole, the script phrases are gone, `landing page` and `book a flight`/`table`/`room` are phrases, `form`/`forms` are whole, and `document` and `contract` are words or phrases (`:266-290`, `:297`, `:314-317`). The lines are in `KeywordRoutingTests.swift:181-188`. What is left of this class is in M3 below. |
| M5 | **Fixed** | `make up` needs a fact, source, citation, number or statistic (`:304-307`), held at `KeywordRoutingTests.swift:172-174`. (`make up a bedtime story for my kid` names nothing now. The English embedding then sends it to `vision`; that is the embedding, carried in R1.) |
| M6 | **Fixed** | `assertRoutes` asserts `CategoryHints.namedSurface(question) == surface` (`KeywordRoutingTests.swift:23`). The order tables for `agentic-coding`/`coding`, `coding`/`computer-use`, `agentic-coding`/`computer-use`, `computer-use`/`web-dev` and `web-dev`/`expert` are at `:146-156`. |
| R2 | **Fixed** | The general phrases are in `generalWords` (`Router.swift:359-362`), outside `surfaceWords`. `generalSurface` is read only where the embedding cannot run (`:510`, `:536`), as D-187 clause 1 now says. Held at `KeywordRoutingTests.swift:202-210`. Probed: `which model is best at reasoning` names nothing and the embedding answers `abstract`; `en iyi yapay zeka hangisi` answers `everyday`. |
| R1 | **Stands** | Carried below. |

## Findings

### BLOCKING (must fix before the hotfix ships)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/Engine/Router.swift:289` (`benim yerime`), `:285` (`operate my`): these phrases
  name `computer-use` on their own. `benim yerime` ("for me", "in my place") is an everyday Turkish
  phrase, and it fits the app's own prompt, `Yapay zekânın ne yapmasını istiyorsun?`. This is new in
  this round: the second review asked for it only together with a site word.
  Failure scenario: each of these goes to `computer-use` on a keyword, where without the keyword it was
  `everyday`: `benim yerime ödev yapan yapay zeka`, `benim yerime mail yazan yapay zeka`,
  `benim yerime sunum hazırlayan yapay zeka`, `benim yerime işlerimi yapan yapay zeka`,
  `benim yerime ders çalışan yapay zeka`, `benim yerime düşünen yapay zeka`,
  `benim yerime cevap veren yapay zeka`. In English, `which ai helps me operate my small business` also
  goes to `computer-use`. Only three of the ten `benim yerime` probes were right (a site, the internet,
  a computer).
  Fix: drop `benim yerime` as a phrase. `bilgisayar kullan*`, `form doldur*` and `rezervasyon yap*`
  already cover the cases that are right. Or read it only when the question also has `site*`,
  `siteye`, `sitede`, `internetten`, `bilgisayar*` or `tarayici*`. Make `operate my` the phrases
  `operate my computer`, `operate my mac`, `operate my pc`, `operate my browser` and `operate my phone`.
  Add the lines above to the negative table.

- **M2** `ios/ModelRanking/Engine/Router.swift:264` (`software`, `developer`), `:259` (`yazilim`),
  `:275-276` (`mobile app`, `ios app`, `android app`), `:292` (`website`): these words also name the AI
  product the reader is choosing ("AI software", "an AI app", "an AI website", `yapay zeka yazılımı`),
  not a thing to build. So a question about a tool for another task goes to `coding` or `web-dev` on a
  keyword. Two of these entries came from the second review's B1 fix.
  Failure scenario, all on a keyword: `best ai software for video editing`,
  `best ai software for small business`, `which ai software is best for students`,
  `best ai software for writing`, `which ai has the best ios app`, `best ai android app`,
  `which ai has the best mobile app`, `best ai mobile apps for students`,
  `which company is the best ai developer`, `en iyi yapay zeka yazılımları hangileri` and
  `yapay zeka yazılımı öner` go to `coding`. `best ai agent software for small business` goes to
  `agentic-coding`. `best ai website for students`, `which ai website is best for homework`,
  `what is the best ai website`, `best free ai websites` and `best website for ai image generation` go
  to `web-dev`. Without the keyword the embedding said `everyday` or `web-dev`.
  Fix: in `notAfter`, skip `software`, `developer`, `website` and `yazilim` (as stems) after `ai`, `llm`,
  `zeka` and `zekasi`. Replace the bare `mobile app`, `ios app` and
  `android app` phrases with ones that say "build": `build* * app`, `build* an ios app`,
  `make * app`, `an ios app`, `app development`. `which model is best for building an ios app` still
  matches. Add the lines above to the negative table.

- **M3** `ios/ModelRanking/Engine/Router.swift:266` (`code`), `:263` (`algorithm`): `notAfter` reads only
  the word before, so `code of conduct` and a platform's feed algorithm stay keywords for `coding`.
  Failure scenario: `draft a code of conduct for my team`, `best ai for writing a code of conduct`,
  `our company code of ethics needs an update`, `how does the instagram algorithm work` and
  `best ai to grow on the tiktok algorithm` go to `coding`.
  Fix: add a check on the next word (beside `notAfter`), and skip `code`/`codes` before `of`. Add `instagram`, `tiktok`, `youtube`,
  `twitter`, `facebook`, `linkedin`, `google` and `feed` to a `notAfter` entry for `algorithm`. Add the
  lines to the negative table.

- **M4** Stems with a second reading, `Router.swift:328` (`scien`, `fizik`), `:330` (`bilim`), `:314`
  (`belge`, `makale`), `:332` (`internet`):
  - `scien` reads data science and computer science: `best ai for data science` and
    `best ai for computer science students` go to `expert`. (The embedding said `factuality` and
    `everyday`; `coding` is the closer board.)
  - `fizik` reads `fiziksel` ("physical"): `fiziksel aktivite planı hazırlayan yapay zeka` goes to
    `expert`. `bilim` reads `bilim kurgu` (science fiction): `bilim kurgu hikayesi yazan yapay zeka`
    goes to `expert`.
  - `belge` reads `belgesel` (a documentary, the Turkish form of the second review's M4 line):
    `belgesel önerisi yapan yapay zeka` goes to `document`.
  - `makale` sends writing an article to the board for reading one:
    `makale yazmak için en iyi yapay zeka`, `makale yazan yapay zeka` and
    `akademik makale yazmak için yapay zeka` go to `document`.
  - `internet` reads "without internet": `which ai works without internet`,
    `internetsiz çalışan yapay zeka` and `internet olmadan çalışan yapay zeka hangisi` go to `search`.
  Fix: add `computer science` and `data science` as `coding` phrases (`coding` is read first). Make
  `fizik` the words `fizik`, `fizigi` and `fizikte`. Skip `bilim` before `kurgu`. Make `belge` the words
  `belge`, `belgesi`, `belgeyi`, `belgeler*`. Read `makale` only with `ozet*`, `oku*` or a document word,
  and leave `makale yaz*` to `everyday`. Skip `internet` before `olmadan` and as `internetsiz`, and
  `internet` after `without`/`no`. Add the lines to the negative table.

- **M5** `ios/ModelRanking/Engine/Router.swift:315`, `:301`: two surface words miss common forms, so a
  later rule wins or nothing does. `pdfs` is not a `document` word, so `best ai to chat with pdfs` goes
  to `assistant` on `chat` (`best ai to chat with a pdf` goes to `document`), and `which ai can read
  pdfs` names nothing. The `cite` stem does not read `citing` or `citations`: `best ai for citing
  sources` and `which ai gives real citations` name nothing. Fix: add `pdfs` to the `document` words,
  and `citing`, `citation` and `citations` to `search_factuality` (`citation` begins `cita`, not
  `cite`). Add the lines to a positive table.

- **M6** `ios/ModelRanking/Engine/Router.swift:359-362`: `generalWords` has no model or product names,
  so on the Turkish path (no embedding) the commonest Turkish comparison is "not understood".
  Failure scenario: `chatgpt mi gemini mi daha iyi`, `gpt-5 mi gemini mi daha iyi` and
  `deepseek iyi mi` go to the manual fallback, marked unmeasured. This is no worse than before the
  hotfix, which refused every Turkish question. But D-187 clause 1 says a question about AI models in
  general is answered from `everyday` where the embedding cannot run, and these are such questions.
  Fix: add `chatgpt`, `gpt`, `claude`, `gemini`, `deepseek`, `grok`, `llama`, `mistral`, `copilot`
  and `qwen` to `generalWords.words`, and add the three lines to
  `testAGeneralQuestionIsTheEmbeddingsOrEverydaysWhereItCannotRead`.

### PASS (what looks good)

- The rule type (`SurfaceWords`, `Router.swift:244-251`) states each rule's reading in one place:
  whole words, stems, phrases, raw marks and `unless`. `notAfter` and `agentBesideCode` are small and
  readable.
- `vision`'s `unless` (`:323`) keeps "a script that resizes images" off `vision`
  (`KeywordRoutingTests.swift:237`).
- The negative table is a real guard. It asserts `!= wrong` on `namedSurface`, so the embedding cannot
  mask it.

## K.8 contract drift check

```
ios/ModelRanking/Engine/Router.swift:377:    static func namedSurface(_ question: String, within known: [String]) -> String? {
ios/ModelRanking/Engine/Router.swift:390:    static func generalSurface(_ question: String, within known: [String]) -> String? {
ios/ModelRanking/Engine/Router.swift:435:protocol QuestionRouter {
ios/ModelRanking/Engine/Router.swift:436:    func route(_ question: String, within known: [String]) async -> RoutingOutcome?
ios/ModelRanking/Engine/Router.swift:906:    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
ios/ModelRanking/Engine/Router.swift:932:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Router.swift:502:        let named = CategoryHints.namedSurface(question, within: known)
ios/ModelRanking/Engine/Router.swift:510:            return (named ?? CategoryHints.generalSurface(question, within: known))
ios/ModelRanking/Engine/Router.swift:536:            return (named ?? CategoryHints.generalSurface(question, within: known))
```

`QuestionRouter`, `TieredRouter.route`/`read` and `namedSurface` keep their signatures.
`generalSurface` is new, and only `SimilarityRouter.route` calls it. The edit to D-187 clause 1
(`9dc41c6`) changes a decision written in this same range, not one on `origin/main`. Verdict: OK.

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Router.swift:485-495` (`readsEnglish`): a short Turkish question made
  of model names is read as English ("undetermined stays in") and routed by the English embedding.
  `claude mu chatgpt mi` went to `document` on the probe. This rule predates the hotfix. Bug, low: it
  is rare, and it is labelled "matched on wording".

## Risks queued to next M

- **R1** (carried): the keyword list is hand-written and is read before the embedding. Each fix in this
  file adds a line to it. Where no keyword matches, the English embedding still misroutes some common
  questions: `make up a bedtime story for my kid` goes to `vision`, `best model for writing emails`
  and `best ai for creative writing` to `web-dev`, `best ai for translation` to `mathematics`, and
  `best ai for making videos` to `factuality`. D-187's "Revisit when" (the on-device model composing
  the list) is the trigger.
