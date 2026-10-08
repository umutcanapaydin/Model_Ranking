---
record_type: plan
id: m20-plan
status: draft
process_version: v6.6
date: 2026-10-08
---
# M20 Plan — our own list for every question

**One sentence.** M20 makes the product's own combined list the default answer to every question.
For each task it reads every board that measures it, combines them by position, every board counting
the same (an older one named under the list), and says which boards it used. Today the default answer is one board.

**The goal is the owner's.** On 2026-10-08, after the first TestFlight build, the owner ruled that an
understood question is answered from the closest board, never "not measured" (D-187). The owner
also named the product's core: the app composes its own list per question from the hundreds of
models' results on many boards, using the on-device model where it runs and predefined methods
where it does not ("this is our biggest strength", owner, translated from Turkish). The owner
approves this plan, or changes it, by merging its pull request. GitHub milestone:
`M20: our own list for every question`.

**Where it starts.**
- **The engine.** It serves 63 boards on `/v1/boards`, positions only (D-167). For coding alone there
  are eight related boards: SWE-bench Verified (Epoch's and SWE-bench's own), Aider, DeepSWE,
  Terminal-Bench, Arena's coding slice, Arena's software-industry slice, and Arena WebDev.
- **The default answer** ranks one board per surface (`/v1/recommendations`; `primary_board` on
  `/v1/categories`, `src/app/adapter/main.py:1354`).
- **The phone's combined list** (`combine`, `ios/ModelRanking/Engine/Combine.swift:47`) needs the
  on-device model to pick a refinement. It keeps only the models every chosen board ranks (D-167
  clause 3), so with eight boards almost nothing would be left.
- **On the owner's phone, with Apple Intelligence off,** every answer is one board, and a board the
  publisher stopped updating shows a staleness warning the owner read as the app being out of date.

**Cap and order.** Five waves. W5 is the release wave, so it is the one to drop. Each wave ends with
`/close-wave` (Code-Reviewer, then Tester). The milestone ends with one security seat and a repo
review. A wave's pull request opens after its reviews.

## 1. Acceptance criteria (REQ-IDs)

| Wave | REQ-IDs | Criterion |
|---|---|---|
| W1 | REQ-CMB-001 | `/v1/categories` names, for every surface, its family: every board that measures that task, the primary first; the phone reads each board's date from `/v1/boards`, where it already is. The family is derived from one declared table in the engine, never kept by hand on the phone, and a gate compares the two. Additive; no field changes meaning. |
| W2 | REQ-CMB-002, REQ-CMB-003 | The phone combines a family into one list by position, never by score (D-105). A model ranked by at least half of the family's boards (rounded up, at least one) is placed by its mean percentile position across the boards that rank it. Every board counts the same, and one older than 90 days or undated is named under the list (D-188 clause 4 as the W2 review measured it). The rule is D-188 and holds on property tests, with ties shared and broken by model id. |
| W3 | REQ-CMB-004 | Every understood question chooses its family: the on-device model's surface, or the wording tier's keywords (D-187), or the closest board. A refinement (a language, a domain) adds its slice board to the family. The question still never leaves the phone. |
| W4 | REQ-CMB-004 (the wiring, amended after W3's review), REQ-CMB-005, REQ-APP-007, REQ-APP-008 | While Apple Intelligence reads the question, the field shows its glow and a small line says so (#208). The combined list is the default answer on every surface. It says "built from N boards" with each board's date, and a stale board is a small note on its own line, never a warning over the list. One tap shows where each board placed a model. The single-board ranking is one tap away. Ruling A holds for coding: two families, neither leading. |
| W5 | Stage 5.2 prerequisites | Build 3 goes to TestFlight against the hosted engine. The hosted engine has a rate limit before any external tester (#187). The combination is measured on a labelled set (#195) against the single-board answer. |

## 2. Waves

### W1 — Every board that measures a task, named by the engine (risk: **HIGH**; #209)

`src/app/adapter/main.py` changes, so the wave is HIGH.
- **D-188 first.** It records the families, the combination rule and how an older board is named (W2), for
  the owner's approval with this plan.
- **One declared table in the engine.** Each surface maps to its family of boards, with the primary
  first (`app.workflows.families`, a client-free module of its own). `/v1/categories` gains `boards` per
  surface, by id; each board's date is already on `/v1/boards`.
- **A gate** holds that every board in a family is served on `/v1/boards`, and that every board
  `/v1/boards` serves belongs to a family or is named as left out, with its reason.

**The one alternative:** the family list kept in the app. That is faster to ship, but it is a second
copy of a fact the engine owns, so it would drift.

### W2 — Many boards into one list (risk: **HIGH**; #210)

`Combine.swift` is the one file allowed arithmetic on positions (D-160 clause 2), so the wave is HIGH.
- **The rule (D-188, amending D-167 clause 3).**
  - A model needs coverage: at least half of the family's boards, rounded up, and at least one.
  - Its place is the mean of its percentile positions (position over board size) across the boards
    that rank it.
  - Every board counts the same; a board older than 90 days, or undated, is named under the list.
  - Ties share a place and are broken by model id. Positions only; no score is read (D-105).
- **Property tests:** permuting the boards changes nothing; a board added with no models changes
  nothing; a model better on every board is never below one worse on every board. (A fourth, about
  a stale board's half weight, went with the half weight: the W2 review measured it letting Arena decide
  five families.)

**The one alternative:** keep "every board ranks it" and use only the two or three boards most
models share. That is simpler, but a new model ranked by two boards out of eight would never appear,
and new models are what readers ask about.

### W3 — The question picks its family (risk: **HIGH**; #211, #206)

`Router.swift` is a security glob.
- The surface the question routes to brings its family. A refinement the on-device model chose adds
  its slice board, as D-168 does today.
- With no model on the device, D-187's keywords pick the surface, and a language word picks the
  language slice: "in French" or `Almanca` ("German") adds that language's board. Arena slices exist
  for Chinese, French, German, Japanese, Korean, Polish, Russian and Spanish; Turkish has none, so a
  Turkish task adds no board (the W3 review's M6).
- **Amended after the W3 review (B1).** W3 delivers the functions (`familyBoards`, `Refinements.read`)
  and their tests; W4's answer plan is what calls them, and D-188 clause 6 records the amendment to
  D-168 clause 4 with a gate on the one reader.
- #206: a short Turkish question made of model names is a general question.
- Nothing about the question leaves the phone: the family is read from `/v1/categories`, and
  `/v1/boards` is fetched as before (D-167 clause 1).

### W4 — The combined list is the answer (risk: **HIGH**, amended from MEDIUM after W3's review; #212, #199, #208, #211)

- **The home screen** shows the combined list by default on every surface: ten rows and the rest on
  request (D-175).
- **The wiring (amended after W3's review, B1 and M7).** The answer plan builds the family with
  `familyBoards`; where the outcome's tier is not the model's, it reads the refinements from the words
  (D-188 clause 6), the one reader a gate holds. `AnswerPlan.swift` joins the security globs while it
  hosts that amendment of D-168 clause 4, so W4 is HIGH.
- **"Built from N boards"** with their dates. A stale board is a small note on its own line ("SWE-bench
  has added no result since 25 June; it counts the same as the others here").
- **A row's detail** shows each board's position for that model.
- **The engine's single-board answer** (the picks, the price notes) stays one tap away, as "the
  primary board".
- **#199** (moved to M21 after W4's review, M1): the UI target's scripted routing and the reading each
  test expects move into one fixture that an Engine test also reads. The combined list came first, and
  the fixture changes every UI test's setup; it goes with M21's gate work.
- **#208** (the owner's ask, 2026-10-08): while Apple Intelligence reads the question, the question
  field gets Apple Intelligence's moving glow, and a small line under it says so ("Apple Intelligence
  enhanced"; where it is off, which tier answers instead). Reduce Motion gets a still border.
- `make ui-test` runs in the wave (D-175 clause 2).

### W5 — Build 3 on TestFlight, safely (risk: **HIGH**; #187, #195)

- **#187:** a rate limit on the hosted engine, per client, failing open (AGENTS.md §5). The owner's
  usage page note stays.
- **#195:** a fresh labelled set from an independent seat. It measures D-187's keywords and the
  combined list against the single-board answer, before and after.
- **The owner's steps:** the deploy and the build-3 upload, by `docs/release-testflight.md`.

## 3. Risk tiers and security globs

- **HIGH waves:** every wave, for the reasons each heading gives. W4 was MEDIUM (screen code and its
  tests) until W3's review moved the one word reader into `AnswerPlan.swift` (M7).
- **Security globs.** A diff touching any of these makes a wave HIGH:
  - `src/app/adapter/main.py`, `src/app/clients/**`
  - `scripts/*engine_service*.sh`
  - `ios/ModelRanking/Engine/EngineClient.swift`, `Router.swift`, `StandingsStore.swift`,
    `FrontDoor.swift`, `Combine.swift`, `AnswerPlan.swift` (added after W3's review, M7)
  - `tests/conftest.py`
  - `.github/workflows/**`, `.claude/settings.json` (the owner's)
  - the deploy surface W5 of M19 built: `Dockerfile`, `fly.toml`, `.dockerignore`,
    `scripts/deploy_hosted_engine.sh`, `src/app/workflows/public.py`, `ios/Config/**`

## 4. Spike check

None needed. W2's rule can be tried on the served `/v1/boards` payload in a scratch test before the
wave; it uses no new dependency.

## 5. K.8 contracts, grep-verified at `bd273bc`

```
$ grep -n "\"primary_board\"" src/app/adapter/main.py
1354:                "primary_board": spec.primary_source,
$ grep -n "^func combine" ios/ModelRanking/Engine/Combine.swift
47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
$ grep -n "struct BoardStandings" ios/ModelRanking/Engine/Models.swift
348:struct BoardStandings: Codable, Equatable, Identifiable {
$ grep -n "^ARENA_SLICES" src/app/workflows/board_tables.py
130:ARENA_SLICES: tuple[ArenaSlice, ...] = (
```

- `/v1/categories` gains `boards` per surface (additive; `primary_board` keeps its meaning).
- `combineFamily`, `FamilyList` and `FamilyEntry` are new beside `combine` (W2); `AnswerPlan.swift`
  calls them where the engine names a family (W4), and maps a family's entries to `CombinedEntry`.
- `/v1/boards` is unchanged: positions and `evidence_date`, no score (D-167).

## 6. Token budget

About 2.5M tokens: five waves of implementation, two review seats per wave, one Tester per wave,
the labelled-set seat, the closure's two seats. Not measured per wave.

## 7. Issue inventory

| Wave | Issues |
|---|---|
| W1 | #209 |
| W2 | #210 |
| W3 | #211, #206 |
| W4 | #212, #208, #211 (its wiring); #199 moved to M21 |
| W5 | #187, #195 |

**Left out, with the reason:**
- The rest of the open queue is M21's (`docs/plans/m21-plan.md`, the owner's ask of 2026-10-08):
  the gate and process enhancements, the data-identity bugs, the reading of non-searches, and the
  deploy items. The combined list comes first.
- #81, #115, #190: the owner's.

## 8. Closure tasks

- `/repo-review` across the milestone, and the one closure security seat (D-172).
- Capture per `docs/closure-checklist.md` §B.2: process log, EXPERIENCE, roadmap snapshot, AGENTS.md
  diet.
- The release security verdict (`docs/reviews/release-security.md`) is read again for the release
  surface W5 changes.
