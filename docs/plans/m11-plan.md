---
record_type: plan
id: m11-plan
status: ratified
process_version: v5.0
date: 2026-08-22
---
# M11 Plan — the milestone where things RUN, and the reviewer is somebody else

> **SIGNED by the owner on 2026-08-22** — *"fine, let's run M11, go"* (owner, translated from
> Turkish). Four waves. No money is spent and nothing deploys.

## 0. The two owner rulings this plan is built on

**Ruling 1 — stay local and finish the testing first.** *(owner, translated from Turkish,
2026-08-22)* "Let's finish all the tests first, stay local — but know this too: when I say it's
done, when we are ready, we will first install it on my own phone and I will test it there, and
then of course we go to the App Store."

So M11 spends nothing. It is not a smaller version of the deploy milestone; it is the milestone
that makes a deploy *worth doing*, because today nothing in this product has ever been executed in
front of a person. The phone and the App Store are the trajectory, and this plan is written so
that neither is made harder: nothing here is throwaway scaffolding.

**Ruling 2 — K.7 gets amended to match reality.** The reviewer stays somebody else, but "somebody
else" is defined as a SEPARATE session rather than a second human. This closes W-055 by changing
the rule rather than by hoping the count stops rising.

## 1. Why this milestone exists

M10 answered M9's carried question against this project, twice. A telemetry counter fired at M8 and
nobody consumed it. A defect that returns a WRITABLE database handle from a call named `mode=ro`
survived a full milestone, a security review that found three real blocking findings, and every
gate — and was caught by typing the expression into a Python process.

The carried question from M10 is therefore this milestone's whole subject:

> What is the smallest amount of RUNNING this project could add to its close, and what does it
> cost? Not a tenth gate in `make check`.

**The measured answer, taken before this plan was written:** `ios/` holds **1,093 lines of Swift**.
`ios/ModelRankingTests/` is an empty directory that the project file does not reference — the
string `ModelRankingTests` appears **zero** times in `ModelRanking.xcodeproj/project.pbxproj`.
`runner` compiles the app and never runs it. **Every line of the router, the engine client and the
screen is unexecuted by anything in this repository** (W-038, open since M8-W2).

That is not a gap in coverage. It is the half of the product the reader actually touches, and it
has no gate at all.

### The two traps

**Trap 1 — building a test target that tests the easy half.** SwiftUI view code is expensive to
test and low-yield; the Engine layer (routing boundary, redirect refusal, decoding) is where a
defect changes what a reader is told. W2 targets the Engine and **says so in the record** rather
than reporting "iOS is now tested."

**Trap 2 — a Simulator session that becomes a screenshot.** Walking the app and declaring it fine
is the shape this project has already recorded five times (*a record that states the opposite of
the code*). W3's session produces a written list of what was ASKED and what came back, including
what looked wrong, and any defect found becomes a red test before it is fixed.

## 2. Acceptance criteria (new REQ-IDs — into `docs/prd.md` AT THE WAVE)

| REQ-ID | Criterion |
|---|---|
| REQ-REV-001 | K.7 is executable for a single-agent lane: the reviewing seat receives the diff and the base-ref rules, never the authoring session's context, and a wave-close record naming the same seat for both FAILS a gate. |
| REQ-IOS-001 | The Engine layer is executed by a gate. `Router`, `EngineClient` and their boundaries have tests that run from the command line and are wired into `make check` and `runner`. |
| REQ-IOS-002 | The router's boundary is proven IN SWIFT: no path yields an id outside the nine, every tier can be absent without blocking the screen, and an unmeasured question reaches the surface flagged as unmeasured. |
| REQ-IOS-003 | The 503 the client is required to render honestly can be PRODUCED on demand, so the branch that renders it is reachable by a test (discharges W-039). |
| REQ-RUN-001 | The product has been operated by a person against a running engine, and what was asked and what came back is written down — including anything that looked wrong. |
| REQ-RUN-002 | The 12-hour refresh has completed at least two unattended cycles on the schedule, and the status file it left is read back and reported (discharges W-054). |
| REQ-API-010 | `/v1` gives ONE account of a query: the `ranking` array and the `picks` array cannot disagree about what was ranked (discharges W-044). |

## 3. Waves

### W1 — The reviewer is somebody else (risk: **MED** — gate-definition change)
Closes **W-055**, and it is first so that everything after it is reviewed under the new rule.

- Amend `AGENTS.md` §4 and `.agents/rules/practices.md`: for the local single-agent lane, K.7 is
  satisfied by a review that runs in a **separate session** which receives the diff and reads its
  policy from the **protected base ref** (V4C-06), never from the authoring context.
- Ship the gate with the rule (V4C-49): `scripts/wave_check.py` fails a wave-close record whose
  review row does not name a review record, and whose review record does not declare a seat
  distinct from the author.
- Record the amendment as an ADR, because it changes what a green close MEANS.

### W2 — Swift gets executed (risk: **HIGH** — the only unexecuted half of the product)
Closes **W-038**. REQ-IOS-001, REQ-IOS-002.

- A local Swift package under `ios/` whose target `path` points at the existing
  `ios/ModelRanking/Engine` sources, so `swift test` compiles **the same files the app ships** and
  the `.xcodeproj` is not touched. No pbxproj surgery, no second copy of the sources.
- Tests for the boundary that matters: `Router` never yields an id outside `known`; each tier can
  be absent; `unmeasured` survives to the caller; `SameHostOnly` refuses a cross-host redirect;
  `EngineClient` decoding refuses a malformed payload rather than rendering a blank.
- Wired into `make check` and `runner` — a test nobody types is a test that does not run (W-032).
- **Stated limitation:** `ContentView` and SwiftUI rendering stay unexecuted, and the record says
  so instead of implying the iOS half is covered.

### W3 — In front of a person, and running unattended (risk: **MED**)
REQ-IOS-003, REQ-RUN-001, REQ-RUN-002, REQ-API-010. Closes **W-039**, **W-044**, **W-054**,
**W-053**.

- **The Simulator session.** The owner gets one CLI block: start the engine, open the app. Nine
  surfaces, the ask field, the budget switch, and the unbuilt-artifact path. Output is a written
  transcript of asked/returned, and every defect becomes a RED test before any fix.
- **W-039** — make the 503 producible so the honest-rendering branch is reachable.
- **W-044** — one account of one query: `ranking` and `picks` reconciled.
- **W-054** — `launchctl load` (the owner's one command), then two real cycles observed and the
  status file read back. This is the first time any refusal, lock or threshold runs unattended.
- **W-053** — the two MINORs, folded in here because they are minutes.

### W4 — Closure (risk: **LOW**)
Stage 4.0 under the **new** K.7 rule: the first Stage 4.0 in this project's history run by a seat
that did not write the code. Then 4.1, 4.2, 4.4. **4.3 does not run — nothing deploys.**

## 4. Shared contracts (K.8)

**FROZEN and not moved:** the `/v1` payload (D-115; D-124's window was spent by D-125 — REQ-API-010
reconciles the two accounts WITHIN the existing shape or it does not ship), D-104, D-105, D-109,
D-118, D-120, D-128, D-129, D-130, D-132, INV-23.

**Touched:** `AGENTS.md`, `.agents/rules/practices.md`, `scripts/wave_check.py`, a new Swift
package under `ios/`, `src/app/adapter/main.py` (REQ-API-010, REQ-IOS-003), `runner`, `Makefile`.

## 5. What this milestone is NOT

- **Not a deploy.** D-123, W-030 and W-031 stay open for a fourth milestone, by ruling, and the
  closure report will say so in section 0 rather than in a footnote.
- **Not the phone.** Installing on the owner's device needs an Apple Developer account and is the
  step AFTER this one, by his own sequencing.
- **Not W-035 or W-036.** W-035 needs a benchmark that can separate top models on two surfaces —
  a data problem, not a code one. W-036 is build-test architecture. Both stay ACCEPTED with their
  reasons and are named here so their absence is a decision rather than an oversight.
- **Not a tenth gate in `make check`.** M10's carried question specifically warned against that.
  W2 adds one command that RUNS code which has never run; W3 adds a person and a schedule. That is
  the answer being proposed, and W4's retrospective is where it gets judged.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22
