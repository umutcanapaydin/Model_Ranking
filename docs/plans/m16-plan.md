---
record_type: plan
id: m16-plan
status: draft
process_version: v5.0
date: 2026-09-22
---
# M16 Plan — one application, and numbers that follow one rule

**One sentence: M16 makes the product one thing the owner starts, which keeps itself current
without being asked, and pays the three data debts M15 closed with.** The engine takes over the 12-hour refresh (D-149); the
floors move onto the one rule the owner ruled (D-148); one upstream outage stops blanking a whole
cycle (D-144, W-116); and the detail screen gets the floor it was promised (W-112).

**Cap:** 5 waves, ~2k net lines (`docs/closure-checklist.md` §B.0 cadence). W4 is the one to drop if
the milestone runs long; it is a measurement and ships nothing.

---

## 0. What the owner rules before the wave that needs it

1. ~~D-150 clause 2 (K.8).~~ **Ratified 2026-09-22.** K.8 stays; W1 adds the plan-template line
   mapping every fact a new screen shows to the `/v1` field it comes from.
2. ~~How often a reader may press "update now".~~ **Ruled 2026-09-22: there is no button.** The
   boards move on the order of days, so the refresh runs once a night between 23:00 and 01:00, in
   the background, with nothing in the app waiting on it, plus one catch-up when the engine starts
   on an artifact more than a day old (D-151, amending D-149).
3. **Whether re-derived floors ship when they change a recommendation, before W3's second half.**
   Moving a floor can move a model into or out of a surface's Budget Pick. **Recommendation: W3
   prints a before/after table per surface, and you rule each surface that changes a pick,** the way
   D-146 handled the anchors.
4. **Which public prompt collections the project may read, after W4 lists them.** The gap register
   cannot tell us what people ask until strangers use the app (`docs/research/m15-gap-register-
   first-read.md`). Public collections of real prompts are the only instrument, and each has its own
   licence. W4 lists candidates with their licences; you choose.

---

## 1. What M16 inherits, with its evidence

| Debt | Where it came from | Owner ruling needed |
|---|---|---|
| One application: the engine refreshes itself, nightly and quietly | D-149 as amended by D-151 | no — build it |
| The floors re-derived under the board-ROWS rule | D-148 (accepted, clause 1 ruled 2026-09-22); W-094 | §0.3 |
| Per-source carry-forward, ~30-day drop | D-144 as amended; W-116 (planned for M15-W3, not built) | no — build it |
| The detail screen shows the surface's floor | W-112 (ruled 2026-09-22: publish, under its own ADR) | no — ADR in W1 |
| Every Swift test is on a committed list, and a listed test that does not run fails the check | W-111; D-150 clause 1 as amended | no — build it |
| The router's floor, re-measured under D-147's scoring; off-topic questions disclosed | W-118 (ruled 2026-09-22: M16-W1) | no — build it |
| The search call is not in the search surfaces' price, and they say so | W-119 (ruled 2026-09-22: state it, under an ADR) | no — ADR in W1 |
| K.8's third acceptance | D-150 clause 2 (proposed) | §0.1 |
| A script mode printing every W-094 row | `docs/reviews/m15-wave-1-review.md` M-2 | no |
| The router's speed on a phone | D-147's cost, never measured | the owner's device |
| REQ-IMG-002/003 and image pricing | W-105, W-113's history; `docs/plans/m14-wave-1-close.md` | not this milestone |

---

## 2. The waves

### W1 — Contracts and one gate (risk: **MED**)

Nothing a reader sees changes. Everything the later waves need written down first.

- **The `/v1` ADRs first, then the fields.** D-152: `/v1/categories` gains each surface's floor
  (`min_quality`) as its own field, beside `score_anchor`. D-153: the two search surfaces publish
  `price_excludes: "search_call"`, so the app can say what the price leaves out. Both fields ship
  here with their tests; the screens that render them are W2. D-151 removed the third ADR D-149
  asked for: with no button there is no request to design.
- **The Swift test list (D-150 clause 1 as amended).** A committed file lists every Swift test by
  name; `make check` fails when a listed test did not run, and when a test ran that is not listed.
  Verified red by deleting one whole test without touching the list.
- **The router's floor, re-measured (W-118).** D-147 changed the scoring and the 0.15 floor was
  never measured under it: nonsense scores above it, and "what time is it" routes to `vision`.
  Re-measure on a nonsense set and an off-topic set written BEFORE any change, add a general-question
  decline group if the floor alone cannot separate them, and move the held-out questions for the
  M15 surfaces into Swift tests (W3 review m-3, m-4). The owner's phone measures the router's speed
  in the same wave.
- **The privacy gate on resolved declarations (W-122).** Every declaration a client file references
  (`swiftc -dump-ast` or the index store) is checked against an allowlist, so no spelling, alias or
  backtick can reach the network, a share surface or shared storage. Before W2 adds a route.
- **The search price disclosure ADR (W-119)**, beside the two `/v1` ADRs: the search surfaces say
  that a search call is not in the price.
- If §0.1 is ratified: the plan template's shared-contracts section gains the field-mapping line.

### W2 — One application (risk: **HIGH**)

- **The engine owns the schedule (D-151).** One refresh a night, at a time inside 23:00–01:00, and
  one catch-up at startup when the artifact is more than a day old — both through `refresh.py`'s
  existing entry point and nothing else, so the lock, the safe publish and the refusal to publish a
  worse candidate stay the one definition of "safe to serve" (D-149 clause 2).
- **A failing or slow refresh cannot block or crash the server answering the app.** Shown by fault
  injection (a refresh that hangs, one that raises, one killed mid-publish), not assumed. With no
  button and no screen, a failed night is visible only in the log and `/health`, so this wave says
  what each of those reports (D-151's stated cost).
- **The app gets no refresh control and shows no refresh state** (D-151 clause 3). What it does
  gain, from W1's two fields: the floor on the detail screen ("we would not recommend below this")
  and, on the two search surfaces, the line saying the search call is not in the price — both in
  each language, composed in the Engine from facts the server sent.
  **K.8, fact by fact (D-150 clause 2)** -- `grep -n` against `src/app/adapter/main.py`:
  the floor line reads `/v1/categories` `min_quality` (`"min_quality": spec.min_quality`), scaled by
  the same entry's `score_anchor`; the price note reads `/v1/categories` `price_excludes`
  (`"price_excludes": spec.price_excludes`). Nothing else on either screen is new.
- **The launchd job retires.** `deploy/` is the owner's surface, so the wave writes the removal
  steps and the owner runs them; the plist stays in the repository until the owner has.
- HIGH, so D-141 applies: Code-Reviewer, Tester and a pulled-forward security pass on the slice —
  a refresh now shares a process with the server answering the app, and a scheduler that wakes at a
  chosen minute is the kind of thing that is only ever tested once.

### W3 — Numbers that follow one rule (risk: **MED**)

- **Carry-forward first (D-144, W-116).** When one source fails, the surfaces it feeds keep their
  last good rows, marked with their age, for up to ~30 days, and are then dropped. D-128 still
  refuses to publish a surface it cannot stand behind; the carry-forward changes what counts as
  standing behind it, and says so on the served data.
- **Then the floor re-derivation (D-148).** `scripts/survey_boards.py` gains the mode M-2 asked for
  (and a test of `parse_rate_board`'s keep-best branch, W4 review MINOR-5):
  every surface's floor under the ROWS rule, reproducibly. `document`, `factuality`, `vision`,
  `search` and `search_factuality` move from distinct models to rows; `agentic-coding` states which
  effort levels its board population includes. Before/after table per surface, §0.3 ruling, then
  the change. Anchors do not move (D-146).
- **The tie margins are checked against D-148 clause 2.** Clause 2 keeps M8's sizing for windows
  and tie margins; the three M15 surfaces were sized by the M14 overlapping-interval rule (and
  corrected at the M15 closure, W-113). The wave says which rule each surface's margin follows and
  whether that is the one clause 2 names.

### W4 — What people ask, from outside (risk: **MED**, droppable)

- List public collections of real prompts, each with its licence, size and date (§0.4).
- On the collections the owner allows: classify a sample against the fourteen surfaces and the
  decline groups, with the on-device router's own example questions, and report what share falls
  where. **The output is a record, not a surface.** D-142's direction ("cover what people actually
  ask") needs a number before it needs a board.
- Nothing typed by a reader of this app is read; the corpora are other people's published data.

### W5 — Closure (risk: **LOW**)

Stage 4.0 security seat, closure report, retrospective, EXPERIENCE, the M17 plan.

---

## 3. Shared contracts (K.8)

- **D-104, D-105, D-126 untouched.** A score is never blended across boards; nothing typed leaves
  the device; the router still may not say a model is good.
- **`/v1` may gain fields, not change them**, and each new field or route has its ADR written in W1,
  before the wave that serves it.
- `ios/ModelRanking/Engine/Uncertainty.swift` stays the only file allowed arithmetic on a served
  score (D-138).
- `refresh.py`'s entry point is the only way anything starts a refresh; the engine does not grow a
  second definition of a safe publish.

---

## 4. Definition of done

- `make check` exit 0 on the owner's machine, with every Swift test on the committed list.
- Every wave close is written AT the wave's close and cites an independent review dated after the
  code it reviews. (M15-W1 and W3 were closed three and one waves late; see the M15 retrospective.)
- The HIGH wave has its security pass before its commit, not at closure (D-141).
- The launchd job is retired on the owner's machine, or the closure report says why not.
- W-111, W-112, W-116, W-118, W-119 and W-122 end the milestone FIXED.
- The plan's §1/§2 table is diffed against the tree at EACH wave close, not only at closure (W-116:
  a planned item disappeared between two waves and nobody noticed until the closure).
