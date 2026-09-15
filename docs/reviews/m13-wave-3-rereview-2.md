---
record_type: review
id: m13-wave-3-rereview-2
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W3 — Code-Reviewer seat, confirmation pass on the re-review's open items

**How this record was produced.** This is the same independent seat that wrote
`m13-wave-3-review.md` and `m13-wave-3-rereview.md`, working under the same rules: read-only
apart from this new file, with policy read from `10a521c`. It received `m13-w3-r3.diff` (2031
lines, 13 files, `docs/reviews/` excluded) and applied it to a fresh `git archive 10a521c` export,
with a copy of `advisor.db`. It diffed that tree file by file against the r2 tree. Every probe and
mutant below ran on those private copies. The scope is the four open items and anything their
fixes introduced.

**Baseline at r3:**

| Check | Result |
|---|---|
| `pytest tests/unit` | **860 passed**, 7 skipped |
| `swift test` | **193 tests, 0 failures** |
| `black --check` on the contract test | only the nine hunks that predate the wave |
| `ruff check` | clean |
| `check_records` (with every W3 review record) | PASS |

## Verdict: PASS WITH FINDINGS

All four open items are discharged or accepted. I endorse the NEW-1 design choice. The fix
introduces one MINOR finding and three NITs, and none of them blocks the wave.

## The four dispositions

### NEW-1: ACCEPTED AS A DESIGN CHOICE, and the seat endorses it

`ios/ModelRanking/Engine/Router.swift:237-252`: a decline now carries the two closest surfaces,
excluding `assistant`, as alternatives. Tests: `ios/EngineTests/FrontDoorTests.swift:216` and
`:235`. Records: `docs/prd.md:482`, `:483`.

**The judgement.** Wording cannot separate a question about a photo from a task that involves one.
The coordinator's margins support that: the false decline "upload a photo" beats its surface by
0.248, while the genuine decline "which model answers fastest" beats its surface by only 0.041. So
some error is unavoidable, and the fix chooses which error to make:

- REQ-ASK-003 forbids answering an unmeasured question as if it were measured. That error costs the
  reader the truth.
- A false decline is disclosed and costs the reader one tap.

Choosing the second is the right call, and the prd row now states the trade-off in plain words.

**What I re-probed** on the shipping `SimilarityRouter()`: all four named regressions decline, and
each has its right surface as the **first** alternative.

| Question | Alternatives offered |
|---|---|
| "solve this geometry problem about a picture frame" | `[mathematics, everyday]` |
| "click through a website and upload a photo" | `[computer-use, web-dev]` |
| "a web app for streaming video" | `[web-dev, agentic-coding]` |
| "build a photo gallery website" | `[web-dev, coding]` |

Two more checks:

- When `known` lacks `assistant`, the decline returns `nil`, so the manual tier answers,
  unmeasured. That is correct.
- The test at `:216` holds whichever way a future hint change moves those four questions, which is
  the right shape for it.

### NEW-2: DISCHARGED

`tests/unit/test_ios_client_contract.py:679`, `:683`, `:688`. The three mutants that survived last
round are now caught:

| Mutant | Result |
|---|---|
| R1: no routing guard after `ask()`'s load | caught |
| R3: send enabled with no surfaces | caught |
| R4: `Change` enabled with no surfaces | caught |

### NEW-3: DISCHARGED, and the rest ACCEPTED as queued to M14

`Router.swift:491`, `:497`. When the deadline wins, the losing job is now cancelled. I accept
that the absence of a session circuit breaker is queued to M14: it needs state that
`TieredRouter` does not have, and the lock is released after each question.

### NEW-4: DISCHARGED

`docs/prd.md:439` now cites the 2026-08-31 council's ballot E. I verified it at the base ref:
`docs/handovers/handover_m13-start.md:294` is §6, whose tally has an E column, and `:320` reads
*"removing the strip — unanimous."* The row also cites second-opinion Q4. The duplicate
REQ-API-010 predates the wave, and the coordinator reports it ledgered.

## Findings these fixes introduced

| # | Severity | `file:line` | Finding | Remedy |
|---|---|---|---|---|
| R3-1 | MINOR | `Router.swift:248-250`; `ContentView.swift:263` (the `Or:` label) | **A genuine decline now offers unrelated surfaces under `Or:`.** Examples: "generate an image of a cat" offers `[abstract, web-dev]`; "make my profile photo look better" offers `[everyday, web-dev]`; "which model answers fastest" offers `[everyday, mathematics]`. The notice above still says the question is not measured, so nothing false is claimed. But `Or:` reads as "or you meant one of these", which a cat image did not. The first-round code avoided exactly this on the below-floor branch, and its comment says so | On the decline path, label the chips as what they are: the closest measured surfaces, not alternatives to the question. Keep the chips themselves |
| R3-2 | NIT | `FrontDoorTests.swift:216` | The one-tap guarantee holds for the four tested questions, not in general. Three questions this round declines without their surface among the alternatives: "calculate the speed of a train…" (mathematics), "explain how sound waves travel through air" (expert), and "reduce the latency of my REST API" (coding). All three were already misrouted to `everyday` before the fix, so this is not a regression | List them in the W3 close's probe ledger as known misses |
| R3-3 | NIT | the coordinator's disposition text; the W3 close | The measurement reports **one miss**: "compose a song" goes to chat as measured. The same disposition says the error REQ-ASK-003 forbids "stays at zero on the probe". Both cannot be true unless song-writing is ruled a measured chat task | In the W3 close, either record that ruling or record the miss as open |
| R3-4 | NIT | `Router.swift:497` | No test asserts that the losing job is cancelled. `SlowTierTests` passes with or without `job.cancel()` | Optional: have the hanging stub record cancellation, and assert it |
