---
record_type: plan
id: m19-plan
status: draft
process_version: v6.6
date: 2026-10-05
---
# M19 Plan — what the reader sees is right, and what the phone promises is held

**One sentence.** M19 corrects what a reader sees (names, model identity, attribution), holds the
phone's privacy promises by what the code does rather than how it is spelled, makes the gates see
before a push what CI sees after, and reads the question a second time, with a first release
prepared only if the owner calls one.

**The goal is the agent's proposal.** On 2026-09-29 the owner asked the agent to proceed on its own
recommendations. The owner approves this plan, or changes it, by merging its pull request; the
criteria are frozen then, and a later change is a plan amendment. GitHub milestone:
`M19: what the reader sees is right, and what the phone promises is held`.

**Why these areas.** M18 ended with the app on the owner's phone and nothing deployed beyond it. What
it left open falls into five groups:
- reader-visible data defects (#112, #129, #130, #124);
- the three gaps in the phone's privacy and arithmetic gates (G-1 to G-3 in
  `docs/security-invariants.md`: #85, #60, #107, #110);
- gates that see too late (#137, #140, #122, #149);
- the two missed reading bars (#66, #113), which the owner shipped as measured (#134);
- the first release's prerequisites, most of them the owner's (#88, #141, #142, #147, #81).

**Cap and order.** Five waves, at the ~4–6 cap. W5 runs only if the owner calls a release, so it is
the one to drop. Each wave ends with `/close-wave` (Code-Reviewer, then Tester; D-172: no security
pass per wave). The milestone ends with one security seat and a repo review. A wave's pull request
opens only after its reviews and `/pre-merge` (owner rule, 2026-09-23).

## 1. Acceptance criteria (REQ-IDs)

| Wave | REQ-IDs | Criterion |
|---|---|---|
| W1 | REQ-CAN-001, REQ-CAN-002, REQ-SRC-010 | Every model the served artifact names is named in its maker's spelling, one release is one model, and an effort is never a model of its own. Each attribution the app shows matches its publisher's current terms, or waits on #88 by name. |
| W2 | REQ-GAP-001, REQ-APP-005, REQ-API-001 | Nothing derived from the question reaches a request or the standings file, by any route the compiler accepts, and no arithmetic happens outside the named files, however the value is named. Gaps G-1, G-2 and G-3 close, each shown red on its planted mutant. The engine's own sameness rule reaches the phone. |
| W3 | none new (controls) | A wave sees CI's skip count, its wave and tier gates, and a child process's network before it pushes. Each new check is shown red. |
| W4 | REQ-ASK-005, REQ-IMG-003, REQ-RTR-005 | Knowledge questions and requests to make an image are read better than M18's measure, on a fresh held-out set, measured twice, against bars set after the baseline (D-169 clause 6). |
| W5 | Stage 5.1 prerequisites | Only if the owner calls a release: every prerequisite on this plan's W5 list is done or ruled, then the Stage 5.1 review runs. |

## 2. Waves

### W1 — What the reader sees (risk: **HIGH**; #112, #129, #130, #124, #100, #101, #106)

`src/app/clients/**` and the registry are touched, so the wave is HIGH (#83).
- **#112:** the 68 models served under a lower-case spelling of their id, each named as its maker
  spells it, from the maker's own page, with the source written beside each name.
- **#129:** one release served under two ids is one model, with its evidence together.
- **#130:** `o3-mini-high` is `o3-mini` at high effort, not a model of its own (D-112).
- **#124:** the attribution strings that lag their publishers. The part that depends on the licence
  ruling waits on #88 by name.
- **#100, #101, #106:** the board guards compare model ids, not raw names; the subscription engine
  breaks ties by plan id; a moving `-latest-vN` alias never derives a fixed id.

**The one alternative:** take display names from an upstream catalogue (OpenRouter's) instead of the
hand-kept table. Fewer rows to keep, but its spellings are not the makers', and the table's test
already holds each row to its source.

### W2 — The phone's promises, held by what the code does (risk: **HIGH**; #85, #60, #107, #110, #132, #144, #138)

The Engine layer, `EngineClient.swift` and the client gates are touched.
- **#85 (G-1):** the privacy sinks (INV-66, INV-67) are held by the data that reaches them. The two
  M17 mutants that pass every gate today, a static relay onto `/v1/boards` and the typed question
  saved through `StandingsStore`, each fail one. The design question (a type that cannot carry the
  question, or a gate on the compiled module) is settled in the wave plan, red first.
- **#60 (G-2), #107 and #110 (G-3):** the arithmetic, URL-from-text and `#if false` holes, read from
  the compiler's view, not the spelling. #107 includes the unapplied `.init` form #131's Tester found.
- **#132:** the held-reading logic moves from `ContentView.swift` into the Engine layer, where
  `swift test` runs it.
- **#144:** the engine session sets no cookie and sends none.
- **#138:** each pick carries its model id on `/v1`, an additive field under an ADR written before
  the wave serves it, and the app's cards are keyed on it.

**The one alternative:** hold G-1 with a review rule instead of a gate. Cheaper, but the M17 mutants
show that review missed both routes once already.

### W3 — The gates see before the push (risk: **HIGH**; #137, #140, #122, #149, #117, #108)

Gate definitions change, so the owner reviews the wave (AGENTS.md section 3).
- **#137:** a local check derives the skips CI will take and compares them with the budget. It missed
  three times in M18 and once since.
- **#140:** the wave gates count waves added by amendment and read the plan's own security globs.
- **#122, its second half:** the option the owner chooses on the issue (the agent recommends B: the
  test run itself has no network on macOS, and the CI half is a patch for the owner).
- **#149:** the model-tier deadline test's one failure under load is read to its cause (a slow
  machine, or a blocked cooperative pool that would make the deadline late in the app too).
- **#117, #108:** a gate for signal words only a held-out set holds, and the `URLSessionConfiguration()`
  trap measured.

**The one alternative:** move these checks into CI only. They would then keep finding problems after
the push, which is the fault this wave exists to fix.

### W4 — Reading the question, a second round (risk: **HIGH**; #66, #113)

What the on-device model's output decides (D-126) is touched.
- **The held-out set:** questions from a stranger's first use, if the owner runs the session by
  `docs/research/stranger-first-use-protocol.md` (#91's protocol) before the wave; otherwise a
  fresh set written by an independent seat. Either way the author never reads it (D-147 clause 5).
- **#66:** knowledge questions, the gap M18 measured (1 of 10 caught).
- **#113:** requests to make an image, including those routed to `web-dev` and on the wording tier.
- Three variants per problem, then the bars, measured twice; a missed bar goes back to the owner as
  one question (D-169 clause 6).

**The one alternative:** stop at M18's measure and leave reading as shipped. That holds the
false-positive bound but leaves knowledge questions answered as if measured.

### W5 — A first release, only if the owner calls one (risk: **HIGH**; #88, #141, #145, #147, #94, #142, #81, #115)

Most items are the owner's decisions or files.
- **The owner's:** #88 (the six licence questions), #142 (the force-push guard, a hook), #81 (CI),
  #141 (the `Dockerfile` base by digest, K.10), #147 (his Mac's name in the public tree), #115 (the
  Turkish local-network prompt on his phone).
- **The agent's:** #145 (the launcher's preflight judged by its exit status), #94 (the Docker image
  with a Host list), and the Stage 5.1 security review on the whole release, BLOCKING before any
  deploy.

## 3. Risk tiers and security globs

- **HIGH waves:** all five, for the reasons each heading gives.
- **Security globs.** A diff touching any of these makes a wave HIGH:
  - `src/app/adapter/main.py`
  - `scripts/*engine_service*.sh`
  - `ios/ModelRanking/Engine/EngineClient.swift`
  - `ios/ModelRanking/Engine/Router.swift`
  - `ios/ModelRanking/Engine/StandingsStore.swift`
  - `ios/ModelRanking/Engine/FrontDoor.swift`
  - `src/app/clients/**` (input parsing, #83)
  - `tests/conftest.py` (the suite's network guard)
  - `.github/workflows/**` and `.claude/settings.json` (the owner's)

## 4. Spike check

- **W2:** one throwaway `spike-m19-g1` branch to try both G-1 designs on the two M17 mutants before
  the wave's design is chosen. It is never merged.
- **Other waves:** no spike.

## 5. K.8 contracts, grep-verified at `0198eb3`

```
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
src/app/workflows/registry.py:518:DISPLAY_NAMES: dict[str, str] = {
src/app/workflows/registry.py:561:def claude_word_order(name: str) -> str:
src/app/workflows/rank.py:38:ATTRIBUTIONS = (
src/app/workflows/rank.py:48:SOURCE_ATTRIBUTION: dict[str, str] = {
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:526:enum ModelOutputBoundary {
ios/ModelRanking/Engine/FrontDoor.swift:278:public struct GapRegisterStore {
ios/ModelRanking/Engine/AnswerPlan.swift:173:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
tests/conftest.py:204:def pytest_configure(config: pytest.Config) -> None:
```

`/v1` may gain fields only under an ADR written before the wave that serves them (W2's #138). No
route changes shape.

## 6. Token budget

Not tracked: token spend is not visible to the agent (as in M16 to M18). The wave cap is the budget.

## 7. Issue inventory

| Wave | Issues |
|---|---|
| W1 | #112, #129, #130, #124, #100, #101, #106 |
| W2 | #85, #60, #107, #110, #132, #144, #138 |
| W3 | #137, #140, #122, #149, #117, #108 |
| W4 | #66, #113 |
| W5 | #88, #141, #145, #147, #94, #142, #81, #115 |

**Left out, with the reason:**
- #125, #126, #127, #128, #131, #133 and #150 are delivered by open draft PRs #154 to #160; they close
  when those merge.
- No open issue is left without a wave.

## 8. Closure tasks

- `/repo-review` across the milestone, and the one closure security seat (D-172).
- Capture per `docs/closure-checklist.md` §B.2: process log, EXPERIENCE, roadmap snapshot, AGENTS.md
  diet.
- The Stage 5.1 release review only if the owner calls a release (W5).

**Amendment (2026-10-06, W1).** #162 joins W1: listing every served name for #130 found that the
GPT-5 mini, nano and chat rules took any minor version, so GPT-5 mini, GPT-5.1 Codex mini and
GPT-5.4 mini were served as one model, with one another's prices and scores. It is the same goal
as #129 (one release, one model), in the other direction.

**Amendment (2026-10-06, W1 close).** Naming #112's list against the makers' pages found more of
#129's defect, one release under two ids, each with part of its evidence: GPT-5 (its only snapshot,
`gpt-5-2025-08-07`), Mistral Small 3.1 (`mistral-small-2503` and its open weights) and Mistral Medium
3.5 (`mistral-medium-2604`). Each joins #129's fix, ruled from its maker's page. Mistral moved the
alias `mistral-medium-3` to Medium 3.5, so it joins D-166's moving aliases. Two findings that need
a ruling are filed rather than taken: #163 (whether a family rule may gather a release's later
snapshots) and #164 (an id its maker retired and reroutes to a newer model).

**Amendment (2026-10-06, W2).** #132 (the held reading into the Engine) leaves W2 by the wave plan's
own valve: it rewires the screen, which a dozen text pins hold as it is and only the UI target can
prove, and W2 already changes the answer screen's cards (#138). It goes to the next wave that works
on the screen. The compiler-level arithmetic check (D-181) found the price in pages, a conversion of
a served price REQ-CMP-002 requires, in two files no table named; D-181 names them.

**Amendment (2026-10-06, the W2 review).** The Code-Reviewer's two blocking findings were fixed in the
wave, each with a red test made from the review's mutants: B1 (arithmetic on a served number through
ordinary names) by following a served number through every name the compiler shows (D-181 as
amended), and B2 (a client built on a URL made from typed text) by keeping the client's address in
`EngineClient.swift` (D-180 as amended). The W2 criterion "however the value is named" holds except
through `Any` or text: the served facts reach the phone that way, so G-2 stays open for that
remainder only (#171). #144's test reads the shipped session's configuration, not a `Set-Cookie`
answer, because a `URLProtocol` stub bypasses the session's cookie handling (measured; the review's
M9). Filed from the review: #168 (K1), #169 (K2), #170 (R1).

**Amendment (2026-10-06, the second W2 review).** A second Code-Reviewer found more routes past the
rules of the day, the same kinds of hole as the first. The privacy routes are closed by rules that do
not grow by spelling (D-180 as amended): a kept type is built, extended and conformed only in its own
file, the store is built and saved to only in its own, no file touches memory unsafely, and the code a
sink runs elsewhere reads no shared mutable state. The arithmetic shapes are not chased a third time:
D-181 now names the operators, methods and names it holds. The W2 criterion is not met as worded,
because no check over the compiler's declarations proves "by any route the compiler accepts" or
"however the value is named". Its privacy half is met for every route the M17 closure and both W2
reviews planted, each refused; its arithmetic half for every shape the first W2 review planted and the
operators, methods and names D-181 lists, and not for the second review's B3 shapes. Gaps G-1 and G-2
stay open in part for the rest (#172; #171, #173).

**Amendment (2026-10-06, W3).** Two choices the plan left to the owner were taken on the standing
instruction of 2026-09-29: #122's option B (the test run offline at the operating system's level on
macOS; CI's half is a patch posted on #122 for the owner) and #117's matching (whole words, Turkish with
its suffixes). #108 is delivered by its guard only, under the wave's valve: the cause was read, not
measured, since measuring means trapping a process; the issue stays open. #117's check found four
signal words added after the M18 held-out sets that alone hold them (#177, before W4 measures on those
sets). A load-sensitive timing test was filed as #178.

**Amendment (2026-10-07, W4).** The owner had not run a stranger's session, so an independent seat
wrote the fresh held-out sets; the three M18 sets were retired to tuning (#177, taken on the standing
instruction). Three variants were run per problem, and the built one measured twice per tier: every
guard and bound held, #113's wording-tier bar was met at `de8c3f8` (the code that ships keeps neither of
#113's gains), and #66's and #113's model-tier bars and D-169 clause 6's catch bar were missed (`docs/research/m19-w4-question-reading-probe.md`, D-184). By the
valve, the pull request asks the owner whether to ship what holds; #66 and #113 stay open. Two
variants that changed the model ran once each, and #113's (b) once: their first runs settled them.
The coding-set guard owed to variants that change the model's instructions was not run, since none of
them was built. The code review's fixes cost one knowledge question on the spent set; after three review verdicts on
one class, the image rule's reach beyond `vision` came out of the wave (#191, record §6).

**Amendment (2026-10-07, W5).** The owner called the release ("we need to deploy the engine to a
real supabase or something and we need to go for testflight", owner, 2026-10-07). Supabase hosts
databases and functions, not a Python service, so D-116's Fly.io stands (D-185). #88 was ruled on
the standing instruction (D-185, a public artifact without seven sources; the owner may overrule),
and #141, #145, #147 and #94 were taken. #142's guard half was written in four commits marked OWNER
APPROVAL; its other half is #189. #81 (CI) and #115 (the phone's prompt) stay the owner's. The
TestFlight files were added beyond the list, as the release needs them. The Stage 5.1 review ran
(MAJOR), and its re-read after the fixes is MINOR; nothing is deployed or uploaded by the agent.
