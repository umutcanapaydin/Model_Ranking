---
record_type: review
id: m20-closure-security-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 closure security review, and the release re-read for build 3

**Independent:** yes. I wrote none of M20's code, tests or records, and sat in none of its wave seats.

> **Two jobs in one record.** This is the M20 closure security seat (D-172: one seat per milestone,
> at its close). It is also the release security re-read that `docs/plans/m20-plan.md` §8 asks for:
> does W5's change to the release surface change the verdict of record
> (`docs/reviews/release-security.md`, MINOR) before the owner deploys and uploads build 3?
>
> **Range.** `git diff bd273bc...d005135`: the M20 plans and the five waves (W1 #215, W2 #217,
> W3 #221, W4 #224, W5 #225). 65 files, +13,941/-91. I read every slice that touches a security
> glob of the plan's §3: `src/app/adapter/main.py`, `src/app/workflows/families.py` and its route,
> `Combine.swift`, `Router.swift`, `AnswerPlan.swift`, `fly.toml`. I also read `Refinements.swift`,
> `Language.swift`, `Models.swift`, `Notices.swift` and the screen code (`ContentView.swift`), since
> the word reader and the family list run through them.
>
> **Policy** was read from the profile (`.claude/agents/Security-Reviewer.md`),
> `docs/security-invariants.md` and `AGENTS.md` §5. None of them changes in the range.
>
> Nothing was deployed. The only repository file I write is this one, and I do not commit it.

## Verdict
MINOR

Nothing is BLOCKING and nothing is MAJOR. There are **4 MINOR** (S1 to S4) and **1 INFO** (S5).

**The release verdict stands for build 3: yes.** The release verdict of record stays MINOR. W5's
change to the release surface adds no route, no egress, no storage and no dependency. It holds
under the conditions in "The release re-read" below.

The scale is the M18 and M19 seats':
- **BLOCKING:** ships and can be exploited now, or the permission matrix §11 human-review trigger fires.
- **MAJOR:** not exploitable today, but a release control is weaker than its record says, in a way
  that would hide an exploitable state.
- **MINOR:** an invariant or a control that a code change could break with every gate green, or a
  claim wider than its test. Not exploitable in the current scope.
- **INFO:** checked and recorded; no action unless stated.

## Summary

- **The question still never leaves the phone.** The new word reader (`Refinements.read`, D-188
  clause 6) returns only values of the declared refinement table. It runs only in `AnswerPlan.swift`,
  and only adds boards to a list combined on the phone. The compiled gate passes in all four
  configurations, and the privacy pins pass. Two planted second readers were caught.
- **No new egress or storage.** `EngineClient.swift`, `StandingsStore.swift`, `FrontDoor.swift`,
  `ios/Config/**`, the `Dockerfile`, the deploy script and the locks do not change in the range. The
  app lines M20 adds use no network, file, logging, sharing or URL API.
- **Arithmetic on positions stays in `Combine.swift`** (D-160 clause 2). Its one new sort is
  allowed by name in both gates.
- **The rate limiter (#187) is a fairness control that fails open, as `AGENTS.md` §5 says.** Its
  table is bounded and its log names no address. It refuses a strict boot only on an unreadable
  value. Four weaknesses remain:
  - **S1:** as a cost control, it counts requests, not bytes.
  - **S2:** it runs before the Host check.
  - **S4:** it has no row in the invariant register.
  - **S5:** its trust in `Fly-Client-IP` rests on a check after the deploy.
- **S3** is the one finding on the phone: a broken engine payload can crash, or stall, the new
  family path.

## Findings

### BLOCKING
None.

### MINOR

**S1** `src/app/adapter/main.py:805` (the limiter counts every route alike), `fly.toml:32`,
`docs/release-testflight.md:44-51`. **As a cost control, the limit counts requests, not bytes, and
one person can be thousands of clients.**
- **What the record says.** The release record calls #187 "the cost control that is still owed
  before external testers" (`docs/reviews/release-security.md`, deploy answer, condition 5).
- **How it works today.** The limit is 120 requests a minute per client, on every route alike.
  `/v1/boards` answers about 0.5 MB without gzip (513,532 bytes measured; `EngineClient.swift:189-190`).
  `/v1/budgets` answers about 250 bytes, about 2,000 times less. The phone needs `/v1/boards` at
  most once a day (`StandingsStore.swift:32`, `maxAge = 86_400`).
- **Failure scenario.**
  - A scraper asks only for `/v1/boards`, without gzip. Each address it holds then draws about
    86 GB a day. The runbook says this.
  - The runbook does not say how cheap "many addresses" are. A client is one IPv6 /64. A free
    tunnel-broker /48 holds 65,536 of them (the W5 Tester's T2 notes this). A Fly app with a
    public service is normally given an IPv6 address (the W5 review's M1).
  - So one person can stay under the limit on every address. The bill is then bounded only by
    what the one `shared-cpu-1x` machine can send with the edge's 8 concurrent requests. Fly has
    no billing alert and no spending cap.
- **Why it is MINOR.**
  - It is not exploitable for data.
  - The runbook already says "the limit is per address, not a cap on the bill".
  - The owner's stop, `fly scale count 0`, still works.
- **Fix (before external testers).**
  - Give `/v1/boards` its own, much lower per-client limit, for example 4 a minute, or count each
    `/v1/boards` answer as many requests. A real phone asks once a day, so no reader is refused.
    The per-address worst case then falls from about 86 GB a day to about 3 GB.
  - Add a test: a client past the boards limit gets 429 on `/v1/boards` while `/v1/budgets` still
    answers 200.
  - In the runbook, say that one person with an IPv6 /48 is 65,536 clients. The real ceiling is the
    machine's throughput, and the usage page and `fly scale count 0` remain the controls.

**S2** `src/app/adapter/main.py:786-822`. **The limiter runs before the Host check, so INV-26 no
longer holds as written once a limit is set.**
- **Measured order.** Starlette makes the last middleware registered the outermost. I read the
  order from `app.user_middleware`: `_no_sniff`, then `_limited`, then `_known_host`.
- **Failure scenario.** The Host list is `model-ranking.fly.dev` and the limit is 3. One client
  sends five requests with the Host `evil.example`. They are answered `400, 400, 400, 429, 429`.
  - INV-26 says such a request "gets 400 `unknown_host` on every path, before any route runs".
  - Requests for a foreign Host are also counted, and they fill the table.
  - INV-26's tests (`test_engine_host.py`) run with no limit, so every gate stays green.
  - No route runs either way, so nothing is exposed.
- **Fix.**
  - Define `_limited` above `_known_host` in the file. The Host check is then outermost: it refuses
    foreign traffic first, and that traffic costs no table entry.
  - Add a test with the limit set: six foreign-Host requests from one client all answer 400, and
    `rate_window_count()` stays 0.

**S3** `ios/ModelRanking/Engine/Combine.swift:165`, `ios/ModelRanking/Engine/Refinements.swift:101`,
`ios/ModelRanking/Engine/AnswerPlan.swift:217`. **A broken or compromised engine payload can crash,
or stall, the new family path. The old `combine` was hardened against both.**
- **The crash.** `min(max(standing.position - 1, 0), …)` subtracts before it clamps.
  - A `/v1/boards` position of `-9223372036854775808` decodes into `Int`. I checked this with
    `xcrun swift`: `subtractingReportingOverflow(1)` reports an overflow.
  - So `position - 1` traps. `try? combineFamily` does not catch a trap.
  - The standings file keeps the payload for a day, so every question whose family holds that board
    crashes the app for up to a day.
- **The stall.** `familyBoards` removes repeats with `boards.contains` inside a loop over the family,
  which is quadratic. The family comes from `/v1/categories`, whose ceiling is 256 KiB, so a family
  of tens of thousands of ids is possible. The plan is built in the view's body, on the main thread.
- **Precedent.** The old `combine` was hardened for the same kind of input (M17-W5 security S2 and
  S7: a payload at the size cap froze the screen, and a model listed twice).
- **Why it is MINOR.** Only the engine can send such a payload: over TLS, through the same-host
  redirect rule, and the engine computes its own positions from 1.
- **Fix.**
  - Clamp before subtracting: `Double(min(max(standing.position, 1), board.standings.count) - 1)`.
  - Remove repeats in `familyBoards` with a `Set`, and refuse a family longer than a small bound
    (the largest served family has 4 boards).
  - Add two Swift tests: a position of `Int.min` returns a list, and a family of 50,000 ids returns
    promptly.

**S4** `docs/security-invariants.md:169` (the count, still 75 rows). **M20 adds a security control
and a privacy-side gate, and neither has a row.** No file in the range touches the register.
- The register is the closure seat's starting list. A control without a row is invisible to
  `test_security_invariants.py`: rename one of its tests and nothing fails.
- **Fix.** Add the two rows proposed under "New invariants" below: INV-88 for the limiter and INV-89
  for the word reader. Name S2 as INV-88's gap until it is fixed.

### INFO

**S5** `src/app/adapter/main.py:257-262`. **The client key trusts `Fly-Client-IP` from whoever sends
it.**
- **On Fly.** This is safe only if Fly's proxy overwrites the header. The W5 review raised this (R1),
  and the runbook now has the owner check it after the first deploy (`docs/release-testflight.md:57-66`,
  250 requests with forged headers; some must answer 429).
- **Off Fly.** A client chooses its own key. Today only `fly.toml` sets a limit, so nothing off Fly
  relies on it.
- **Release condition.** Run that check. If every answer is 200, stop sharing the app, as the runbook says.
- **Optional hardening.** Trust the header only when `FLY_MACHINE_ID` is set (Fly sets it in each
  machine's environment, by its documentation; not verified here), and otherwise key on the socket
  peer.

### PASS (observations)

- **D-126, D-160 and D-167 clause 1: nothing typed leaves the phone.**
  - `Refinements.read` maps the question to entries of `Refinements.table` and nothing else.
  - `familyPlan` uses them only to choose board ids for `combineFamily`, on the phone.
  - The question reaches `PlanMemo.Inputs` in memory only, and was already the view's state.
  - `make client-decls` (run as `scripts/client_decl_gate.py`) passes in all four configurations,
    on 19 files. `test_router_hints.py` passes, its two new gates included
    (`test_only_the_answer_plan_reads_refinements_from_the_words`,
    `test_no_other_name_reaches_the_word_reader`).
- **#206 and Ruling A add no request.**
  - `comparesModelsOnly` ends in `generalSurface`, a surface the engine served (INV-64, INV-70).
  - The paired surface comes from the engine's own answers.
- **No new egress or storage.**
  - The app lines M20 adds contain no `URL(`, `URLSession`, `FileManager`, `UserDefaults`,
    `@AppStorage`, `print`, `Logger`, `openURL`, `ShareLink` or pasteboard use.
  - `docs/research/m20-w5-runs/FamilyProbe.swift` reads and writes local files only. It is in neither
    the Xcode project nor the Makefile.
- **D-160 clause 2.** The new arithmetic (`combineFamily`, `isStale`) is in `Combine.swift`. The one
  new sort (`means.keys.sorted`) is allowed by name in `scripts/client_decl_gate.py:305-306` and
  `tests/unit/test_ios_client_contract.py:439-442`.
- **The engine's surface.**
  - `/v1/categories` gains `boards`, a static table with no input, and it is declared in the field
    allowlist (`test_uncertainty_contract.py:320-321`).
  - The five GET routes are unchanged (INV-30).
  - `families.py` imports nothing (INV-43).
- **The limiter fails open, as `AGENTS.md:98` asks.**
  - An exception serves the request and warns once a minute, naming only the exception's type.
  - A malformed Host does not break it: I sent `[model-ranking.fly.dev` and got 400, not 500.
  - The table is capped at 10,000 keys of at most 64 characters, a few MiB at most.
  - A refusal is logged once per client per minute, without the address, and a test holds it
    (`test_a_refusal_is_logged_once_a_minute`).
  - The new imports are standard library only (`ipaddress`, `time`).
- **The boot check is fail-closed in the right place.** A strict engine refuses only an unreadable
  limit. With no limit it warns. `fly.toml`'s `"120"` parses, and a test holds it
  (`test_the_hosted_engine_sets_its_limit`).

## New invariants (proposed rows for `docs/security-invariants.md`)

| INV | Invariant | Source | Negative test(s) | Gap |
|---|---|---|---|---|
| INV-88 | The hosted engine answers one client (an IPv4 address, an IPv6 /64) at most `MODEL_RANKING_RATE_LIMIT` times a minute, and `fly.toml` sets that limit. `/health` is never limited. A limiter that breaks serves the request and warns. Its table is bounded, and its log names no address. A strict engine refuses an unreadable limit. | #187; AGENTS.md §5 (fail open) | `tests/unit/test_rate_limit.py::test_a_client_past_the_limit_is_told_to_wait` (mutant: limit forced to 0, killed here)<br>`::test_the_hosted_engine_sets_its_limit`<br>`::test_the_limiter_fails_open`<br>`::test_the_window_memory_is_bounded`<br>`::test_a_full_table_keeps_counting_the_clients_it_holds`<br>`::test_a_refusal_is_logged_once_a_minute`<br>`::test_an_unreadable_limit_refuses_to_boot_in_production`<br>`::test_health_is_never_limited` | Partial: the trust in `Fly-Client-IP` is held only by the runbook's manual check after the deploy (S5, #187). The order against the Host check is not held (S2). |
| INV-89 | Refinements are read from the question's words in one place, `AnswerPlan.swift`. They are values of the declared table and reach no request and no stored file. The routing outcome carries refinements only from `ModelOutputBoundary`. | D-188 cl. 6; D-168 cl. 4 as amended; D-126 | `tests/unit/test_router_hints.py::test_only_the_answer_plan_reads_refinements_from_the_words` (mutants: a direct call and a closure value in `ContentView.swift`, both killed here)<br>`tests/unit/test_router_hints.py::test_no_other_name_reaches_the_word_reader`<br>`tests/unit/test_router_hints.py::test_only_the_model_output_boundary_builds_an_outcome_with_refinements`<br>`make client-decls` (INV-66's compiled sink rules) | None found. A generic over a protocol of the app's own survives the text gates, but it can reach `Refinements.read` only through `Refinements.self` or an extension in another file, and both are refused. |

## The release re-read (plan §8)

**What W5 changed on the release surface, read in full:**
- **`main.py`'s limiter.** One middleware, two module dictionaries, and a boot check. It adds no
  route, no outbound call, no file and no dependency. The findings are S1, S2, S4 and S5.
- **`fly.toml`.** One environment variable, `MODEL_RANKING_RATE_LIMIT = "120"`. It parses, so the
  strict boot accepts it. Nothing else in the file changes.
- **`docs/release-testflight.md`.**
  - The cost note now gives the fixed-window and per-address figures.
  - It adds a check after the deploy that Fly overwrites `Fly-Client-IP`. That check is a `curl` the
    owner runs, not the agent.
  - S1 asks for one more sentence.
- **The build number.** `CURRENT_PROJECT_VERSION` goes from 2 to 3 in the app's and the UI tests'
  four build configurations, and nothing else changes. `ios/Config/**` (the engine address, transport
  security), the privacy manifest and `EngineClient.swift` are unchanged, so the earlier S1 fix
  (the Release archive carries the HTTPS address) still holds.
- **Also public.** `/v1/categories` gains `boards`, board ids that `/v1/boards` already serves.
  `public.LEFT_OUT` and the public artifact's derivation do not change (INV-87).

**Does it change the verdict of record? No. The release verdict stays MINOR, and it stands for
build 3**, on these conditions:
1. Deploy only from `main` after M20's pull requests merge, by the runbook, as before.
2. Run the runbook's `Fly-Client-IP` check after the first deploy with the limit (S5). If every
   answer is 200, stop sharing the app.
3. Keep the earlier habits: `fly auth logout` after each deploy, the usage page while people test,
   and `fly scale count 0` to stop the cost at once.
4. Before external testers (Beta App Review), take S1's lower limit for `/v1/boards`. This narrows
   the release record's condition 5: #187 now exists, but as a cost bound it still needs S1.
5. Archive and upload as before: the `plutil` readback on the signed archive must say
   `https://model-ranking.fly.dev`.

## Gates run on `d005135`

| Check | Result |
|---|---|
| `gitleaks detect --no-git` on the tree | no leaks |
| `gitleaks detect --log-opts=bd273bc..d005135` | 66 commits, no leaks |
| `ruff check --select S` on `main.py` and `families.py` | clean. `BLE001` was also selected and flags only the limiter's intended fail-open catch (`main.py:809`) |
| `pytest` of `test_rate_limit`, `test_families`, `test_router_hints`, `test_security_invariants`, `test_hosted_engine` | 112 passed |
| `pytest` of `test_engine_host`, `test_api_v1`, `test_api_config`, `test_ios_client_contract`, `test_client_decl_gate`, `test_uncertainty_contract`, `test_security_surface`, `test_board_standings`, `test_public_artifact` | 277 passed, 1 skipped (needs the built database) |
| `scripts/client_decl_gate.py` (`make client-decls`, `xcrun swiftc -typecheck`) | PASS, 19 files, 4 configurations |
| `make deps`, `make slopsquat` | not run (they reach PyPI). No `pyproject.toml` or lock changes in the range, so INV-80's state is the release record's |

## Mutants

All were run in memory or on a scratch copy. The worktree was not written, and `git status` shows only this record.

| Mutant | Test | Result |
|---|---|---|
| The limit forced to 0 (`_rate_limit` returns 0) | `test_a_client_past_the_limit_is_told_to_wait` | killed |
| `Refinements.read(q)` called in a scratch copy of `ContentView.swift` | `test_only_the_answer_plan_reads_refinements_from_the_words` | killed |
| `let f: (String) -> [Refinement] = Refinements.read` in the same copy | same | killed |
| A generic over a new protocol with `static func read` in the same copy | both word-reader gates | survived. It cannot reach `Refinements.read` without a refused spelling (INV-89's note) |
| The limiter registered outside the Host check (the code as shipped) | INV-26's tests | not caught (S2) |

## Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| Swift unit tests, `make ui-test`, `xcodebuild` | Off limits to this seat | S3's crash is shown by an overflow check in `xcrun swift`, not by running the app. W4's and W5's Tester records ran the suites |
| `fly`, Docker, the deploy, a probe of `model-ranking.fly.dev` | Off limits | Fly's handling of `Fly-Client-IP` is unverified; the runbook's check covers it (S5) |
| The questions in `docs/research/m20-w5-runs/` and every held-out file | The dispatch forbids them | Only `FamilyProbe.swift`'s file and network calls were grepped |

**Network.** None. No `gh` call was needed. Every probe ran in process against a seeded scratch
database. No process of mine is still running, and none ended in SIGABRT.

## Dispositions, at the closure

| finding | disposition |
|---|---|
| S1 | fixed `1a8ebcf` (red `e1ae742`): a `/v1/boards` answer counts as thirty requests; the runbook names the /48 |
| S2 | fixed `1a8ebcf` (red `e1ae742`): the Host check runs before the limiter |
| S3 | fixed `1a8ebcf`: positions clamped, a family cut to 16 boards in one pass |
| S4 | fixed `1a8ebcf`: INV-88 and INV-89 in the register |
| S5 | gap G-9 under #187: the owner's header check after the deploy (`docs/release-testflight.md`) |
