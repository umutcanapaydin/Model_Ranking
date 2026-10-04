---
record_type: plan
id: m18-plan
status: draft
process_version: v6.6
date: 2026-09-29
---
# M18 Plan — the app in the owner's hands, and ready for a first reader

**One sentence.** M18 puts the app on the owner's iPhone, makes the screen and the question-reading
hold up under use and measurement, clears the backlog M17 filed, and prepares what a first release
beyond the owner's Mac needs.

**The owner chose the four areas on 2026-09-29** (translated from Turkish): reading the question
(#66, #73), screen quality (#63, #69), the backlog, and first-release preparation. On the same day he
asked the agent to proceed on its own recommendations and to put the app in his hands first, so the
waves are ordered by that. The owner approves this plan, and freezes its criteria, by merging the
M17 closure PR that carries it. A later change is a plan amendment. GitHub milestone:
`M18: the app in the owner's hands, and ready for a first reader`.

**Cap and order.** Six waves: at the ~4–6 cap, so W5 is the one to drop if the milestone runs long.
Each wave ends with `/close-wave`, and each HIGH wave has a security pass on its slice before its
pull request opens. The pull request opens only after the reviews and `/pre-merge` (owner rule,
2026-09-23).

## 1. Acceptance criteria (REQ-IDs)

| Wave | REQ-IDs | Criterion |
|---|---|---|
| W1 | new REQ-DEV-001 (written by W1's ADR); REQ-GAP-001 kept | The app runs on the owner's iPhone against his engine on the home network. It is opt-in, and loopback stays the default. An exposed engine refuses a foreign Host. Nothing new leaves the phone. |
| W2 | REQ-APP-002/003/005 restated (#68); REQ-ASK-002 | The owner's UI findings (#63) are reproduced on the W5 screen and fixed or ruled out. A committed UI test drives the screen's state and branches (#69). |
| W3 | REQ-RTR-005, REQ-ASK-003; REQ-ASK-005 from the ADR on #66's branch | Input that is not a model search, and coding questions, are read better than today's baseline, by the bar set after that baseline. Both are measured twice on a set written independently. |
| W4 | REQ-ING-004, REQ-REF-009, REQ-CAN-001, REQ-API-001 | Every engine and data bug the waves filed is fixed red-first or ruled. |
| W5 | none new (controls and records) | Every gate gap filed is closed with a gate shown red, and the records drift is fixed. |
| W6 | Stage 5.1 prerequisites | One invariants list with a negative test per row. The licences are ruled. W-125, W-126 and W-130 are re-measured. A stranger's first use has a protocol. |

## 2. Waves

### W1 — The app on the owner's iPhone (risk: **HIGH**; #87, #86)

The engine listens beyond loopback for the first time, and the app talks to a host it did not before.
- **Opt-in exposure.** An installer option binds the engine to the Mac's LAN address, and an allowlist
  of Host values refuses DNS rebinding (closure security seat INFO I-4).
- **The app's engine address** is set per build (an xcconfig value read into the Info plist). The app
  declares local networking.
- **The service's safety** is tested by running the written wrapper and plist (#86).
- **The owner's steps** (Xcode signing with his Apple ID, the phone on the same network) are written as
  one short list.
- **ADR first:** a new ADR, which amends D-170.

**The one alternative:** a hosted engine the phone reaches from anywhere. It is more useful, but it
needs the licences ruled (W6) and the Stage 5 release review first; the home network needs neither.

### W2 — Screen quality (risk: **MED**; #63, #69, #67, #70, #72, #78)

- **#63.** Each of the owner's 14 findings from `cce2ced` is reproduced on today's screen. Those that
  still stand are fixed; the rest are closed with the screenshot that shows them gone.
- **#69.** A committed UI test target, driven against a stub router and a local engine fixture, holds
  the paths the W5 simulator runs found:
  - ask;
  - the combined list;
  - removing and restoring a chip;
  - the detail;
  - "Change".
- **#67.** Disclosures are held at the `AnswerPlan` level.
- **#70.** The plan is computed when its inputs change, not on every render.
- **#72.** A stale board (or a stale phone copy) is said on the combined list.
- **#78.** Accessibility becomes a reader filter ("models I can use") or stops being served. The
  recommendation is the filter, which is what W3 of M17 served it for.

### W3 — Reading the question, by measurement (risk: **HIGH**; #66, #73)

Both were measured in M17 and fell short. Their unmerged branches are the starting point:
`enhancement/issue-66-not-a-model-search`, which holds that ADR, and `fix/issue-73-coding-routing`.

This time:
1. **Fresh held-out sets first**, written independently, and a baseline on `main`, twice.
2. **Signals decided in code and tested:** pasted content (a colon then a long text, code, or several
   lines) and text with no word in any language. These are combined with the model's reading, and a
   **one-tap question back to the reader** ("Did you mean to find a model?") replaces a note the code
   is unsure of.
3. **The bar is set after the baseline.** By the owner's standing instruction, the agent sets it and
   records it. The M17 rule of three variants and then a stop still holds.

**The one alternative:** a stronger model (a larger on-device model, or a server-side one). It is
rejected for now: the phone has no larger model, and a server-side one would send the question off
the device (D-126).

### W4 — Engine and data backlog (risk: **MED**)

The issues, each fixed red first:
- #44 ties by display name;
- #45 effort_unknown overcounts;
- #48 `-latest` followed by a word;
- #57 size bounds only at boot, and the metric-direction half of the review's M1;
- #71 the `bounded_get` race;
- #74 quadratic `combine`;
- #55 `/v1/boards` rebuilt per request;
- #56 the phone's whole-response read;
- #39 guards compare display names;
- #42 no loss guard on accessibility;
- #77 unselectable boards;
- #79 contract tests for the W3 files;
- #76 the retired refresher's installer.

### W5 — Gates and records backlog (risk: **MED**)

**Gates**, each shown red:
- #51 the declaration gate's negative fixture;
- #58 decoded URLs;
- #59 Swift tests kept off the network;
- #60 tripwires by name;
- #82 a wave with no close record;
- #83 auto-HIGH for input parsing;
- #85 the privacy sinks by data flow;
- #52 one worktree per seat.

**Records:**
- #33 ADR drift;
- #68 PRD rows for M17's capabilities;
- #80 architecture and AGENTS.md §1;
- #84 when a wave gets a security pass.

### W6 — First-release preparation (risk: **HIGH**; #89, #88, #90, #91, #26, #35)

- **#89.** One invariants list, each row citing its negative test, held by a gate. It is the Stage 5.1
  prerequisite.
- **#88.** The licence table and options. The owner rules; the agent does not decide a licence question.
- **#90.** W-125, W-126 and W-130 re-measured, then fixed or ruled.
- **#26.** pyarrow off the serving image.
- **#35.** A lock file, so a deploy installs the tested versions (the closure seat's I-6).
- **#91.** A protocol for a stranger's first use, whose questions become W3's next held-out set.
- **#81** (workflow edits) is the owner's; the agent proposes the diff.

## 3. Risk tiers and security globs

- **HIGH waves:** W1 (a network surface), W3 (what the on-device model's output decides, D-126) and W6
  (release prerequisites).
- **Security globs.** A diff touching any of these makes a wave HIGH:
  - `src/app/adapter/main.py`
  - `scripts/*engine_service*.sh`
  - `ios/ModelRanking/Engine/EngineClient.swift`
  - `ios/ModelRanking/Engine/Router.swift`
  - `ios/ModelRanking/Engine/StandingsStore.swift`
  - `src/app/clients/**` (input parsing, #83)
  - `.github/workflows/**` (the owner's)

## 4. Spike check

- **W1:** one throwaway `spike-m18-lan` branch to confirm the phone reaches a LAN-bound engine through
  iOS local-network permission before the wave's design is final. It is never merged.
- **Other waves:** no spike.

## 5. K.8 contracts, grep-verified at `3f2e91d` plus the closure branch

```
ios/ModelRanking/Engine/EngineClient.swift:144:    static let localDefault = URL(string: "http://127.0.0.1:8080")!
scripts/engine_service.sh:73:exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host 127.0.0.1 --port "$PORT"
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:421:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:493:enum ModelOutputBoundary {
ios/ModelRanking/Engine/AnswerPlan.swift:86:func answerPlan(
ios/ModelRanking/Engine/Combine.swift:47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
src/app/workflows/ingest.py:117:def _store_scores(
src/app/workflows/schema.py:404:def open_readonly(path: str | Path) -> sqlite3.Connection:
src/app/workflows/standings.py:34:HIGHER_IS_BETTER = frozenset({"elo", "ips", "% correct", "% resolved", "% pass_rate_2", "ECI"})
```

`/v1` may gain fields and routes under an ADR written before the wave that serves them. No route
changes shape.

## 6. Token budget

Not tracked: token spend is not visible to the agent (as in M16 and M17). The wave cap above is the
budget.

## 7. Issue inventory

| Wave | Issues |
|---|---|
| W1 | #87 (new), #86 |
| W2 | #63, #69, #67, #70, #72, #78 |
| W3 | #66, #73 (both carry `out-of-scope` from M17; it comes off when W3 starts) |
| W4 | #44, #45, #48, #57, #71, #74, #55, #56, #39, #42, #77, #79, #76 |
| W5 | #51, #58, #59, #60, #82, #83, #85, #52, #33, #68, #80, #84, #92 |
| W6 | #89, #88, #90, #91 (new), #26, #35, #81 (owner) |

**Left out, with the reason:**
- #38, #40, #41 and #61 are `dev:done` and deployed (`release-3f2e91d`). They wait for the owner's
  verification, not for work.

## 8. Closure tasks

- `/repo-review` across the milestone.
- Capture per `docs/closure-checklist.md` §B.2: process log, EXPERIENCE, roadmap snapshot, AGENTS.md
  diet.
- The closure report, if the Quality Gate is kept on.
- The Stage 5.1 release security review only if the owner calls a release.

**Amendment (2026-10-04, the owner's choice).** W4 runs before W2, because W2 needs the simulator,
which the owner keeps off for now. #74 and #56, the app's code, move from W4 to W2: #74 lands with #70
there, as its triage asks. W4's decisions are recorded as D-173.

**Amendment (2026-10-04, W5's own valve).** #60 and #85, W5's compiler-level tripwires (its P4), move
to W6, beside the invariants list (#89): each is an invariant that list must cite a negative test for,
and each needs a design of its own. W5 closes on the rest of its scope.

**Amendment (2026-09-29, the owner's ruling, D-172).** No wave gets a security pass on its slice,
whatever its risk tier; §0's "each HIGH wave has a security pass" and §3's "HIGH waves" no longer
add one. A wave closes on its Code-Reviewer and its Tester. The closure adds one security seat on the
milestone's whole diff, before the closure pull request opens.

**Amendment (2026-10-04, W2's close).** W2 ran HIGH, not MED: it changed
`ios/ModelRanking/Engine/EngineClient.swift` (#56), a security glob, and added a Debug-only test
hook. It delivered its whole scope, #74 and #56 included, and #95 and #96 from W1's triage. #78
became the filter "Only models with an API or open weights" (D-175). It filed #112 (raw model names,
the engine's data), #113 (a drawing request read as image reading, for W3), #114 (a test-order
defect on `main`) and #115 (the Turkish permission prompt seen on a phone, for W6).
