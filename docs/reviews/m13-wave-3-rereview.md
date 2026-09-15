---
record_type: review
id: m13-wave-3-rereview
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W3 — Code-Reviewer seat, re-review of the fixes

**How this record was produced.** This is the same independent seat that wrote
`docs/reviews/m13-wave-3-review.md`, working under the same rules. It read its policy from the
protected base ref (`HEAD` = `10a521c`) and was read-only on the repository apart from this one new
file. It received the post-fix diff `m13-w3-r2.diff`: 1969 lines, 13 files, the whole W3 against
HEAD with `docs/reviews/` excluded. The diff was applied to a fresh `git archive 10a521c` export in
the session scratchpad, along with a copy of `advisor.db`. That tree was diffed file by file
against the first-round tree to isolate the fixes. Every probe and mutant ran on those private
copies, never on the working tree. Every `file:line` below is in the tree with the post-fix diff
applied.

**My first record was edited by the coordinator.** On line 84 of `m13-wave-3-review.md`, the probe
question is now wrapped in double quotes, so the documented-commands check no longer reads a line
starting with `make` as a target. I checked the record. It is still 293 lines, and every heading,
the verdict and every finding are unchanged. **I do not object.** The edit is formatting only and
changes no judgement. I also agree with not widening the gate's exemption list: that is a
gate-definition change, and it would need escalation.

## Baseline at the post-fix tree

| Check | Result |
|---|---|
| `pytest tests/unit` (with `advisor.db`) | **860 passed**, 7 skipped. The coordinator reports 869 for the working tree; the gap is in files outside this diff |
| `swift test` | **191 tests, 0 failures** |
| `black --check` on `test_ios_client_contract.py` | fails, but only on the nine hunks that predate the wave. The new block is clean |
| `ruff check` on the same file | clean |
| `check_records.py --root .` (with both W3 review records) | PASS, 83 records |
| `xcodebuild` | not re-run by this seat. The coordinator reports success |

## Verdict: PASS WITH FINDINGS

Both blocking findings are discharged in code, and each has a test that fails without the fix
(see the mutants). All three MAJOR findings are discharged, and REQ-ASK-001 is now recorded as
what it is: PARTIAL, with an owner action.

The BLOCKING-1 fix introduces one new MAJOR finding, NEW-1. The new decline hints turn three
questions that used to route correctly into unmeasured answers. The error runs in the honest
direction: the answer is labelled unmeasured and can be corrected. It does not block the wave, but
it should be calibrated before M13 closes.

---

## Disposition of each finding from the first review

### BLOCKING-1: DISCHARGED

`ios/ModelRanking/Engine/Router.swift:94-98` (`unmeasuredHints`) and `:234-242` (the decline test,
in the same centred space as the surfaces). Tests: `ios/EngineTests/FrontDoorTests.swift:184`
(`shipping = TieredRouter(model: nil, similarity: SimilarityRouter())`), `:187`, `:196`, `:205`,
`:214`.

- My three probe questions now go through the shipping tier, and the tests read them. Re-probed on
  the private copy, all three come back `assistant`, unmeasured:
  - "make my profile photo look better"
  - "which model answers fastest"
  - "which model has the longest context window"
- Mutant B1a (the hints never fire) fails the image, speed and context-window tests.
- Mutant B1b (the hints always fire) fails the M10 calibration test at `:214`, among 15 failures.
- The stub test is kept at `:234` and labelled as a test of the decline path. The prd row
  (`docs/prd.md:483`) now cites the shipping-tier tests.
- The hints cannot select a surface. They only send a question to the labelled fallback. That is
  the property that stops them from turning one measured surface into another.

See NEW-1 for what the hints cost.

### BLOCKING-2: DISCHARGED

`ios/ModelRanking/ContentView.swift:42` (`routingGate`), `:488` (ticket taken before
`await router.route`), `:490` (checked after routing), `:497` (checked after the load), `:499-500`
(echo set only after the load), `:508` (`select()` invalidates). The new method is
`FrontDoor.swift:40` (`invalidate`).

The sequence from the first review no longer overwrites anything. `select()` retires the question's
ticket, so `ask()` returns at `:490` before it touches `task`. If `select()` runs during `ask()`'s
load, that load is dropped by the load gate, and `ask()` returns at `:497`.

- `FrontDoorTests.swift:83` tests `invalidate()`. Mutant G1 (`invalidate` does nothing) fails it.
- The wiring is pinned at `test_ios_client_contract.py:608-619`. Mutant R2 (`select()` no longer
  invalidates) fails it.

Setting the echo after the load also discharges MINOR-8(a). It is pinned by
`test_ios_client_contract.py`: `routing = outcome` must come after the last `await load()`. See
NEW-2 for the one guard that is not pinned.

### MAJOR-1: DISCHARGED as a record. REQ-ASK-001 remains PARTIAL

`docs/prd.md:481` now reads **PARTIAL**. Focus is verified. The software keyboard, typing, Return
and the send button are **not** verified. The row names the Safari control and hands both keyboard
paths to the owner (plan §4). That is accurate. I accept the restart answer: `./ios/app.sh up`
booted the device fresh, with `ConnectHardwareKeyboard = 0` already set.

The criterion itself stays open until the owner verifies it. The W3 close must ledger it as
UNVERIFIED, with the owner action.

### MAJOR-2: DISCHARGED. One citation is imprecise (NEW-4)

`docs/prd.md:439` now reads **RETIRED at M13-W3**. It names the plan's authority, states that the
app asks every surface at `unlimited`, keeps `/v1/budgets` for other consumers, and keeps the old
evidence text marked "Was:". See NEW-4 for the citation.

### MAJOR-3: DISCHARGED

`tests/unit/test_ios_client_contract.py:555`. I re-ran all six of my mutants against the new
test, and **all six now fail it**:

| Mutant | Result |
|---|---|
| M1: guard after state change | caught, by the "directly above" check at `:636` |
| M2: `budget = "low"` | caught, `:580` |
| M3: ungated `reloading` | caught |
| M4: help shown only for the model tier | caught |
| M5: the routed surface never loads | caught |
| M6: the notice loses its orange | caught |

NEW-2 lists three new mutants that survive.

### MINOR and NIT findings

| First-review finding | Status | Evidence |
|---|---|---|
| MINOR-1 (a budget in the pick sentence) | **DISCHARGED** | `Language.swift:64` now reads "The highest score on X of all the models ranked here". The Turkish at `:69` is `Buradaki tüm modeller arasında …`. Both are true at `unlimited`: in round one, `eligible_count` equalled the ranking size on all ten answers |
| MINOR-2 (hand ordering hidden from the tripwire) | **DISCHARGED** | `ORDERED_BY_HAND` (`test_ios_client_contract.py:246`) gives the reason. `:255` fails on any unrecorded `.insert(…, at:)` and on a stale record |
| MINOR-3 (chips in REQ-RTR rows) | **DISCHARGED** | `docs/prd.md:418-419` now name the `Change` sheet. REQ-RTR-003 also records that "slow" is now enforced |
| MINOR-4 (one tap) | **ACCEPTED, recorded** | `docs/prd.md:482`: one tap on wording-tier matches, two taps otherwise. NEW-1 makes the two-tap case more common |
| MINOR-5 (wording of the unmeasured notice) | **DISCHARGED** | `FrontDoor.swift:130-137`: "Going by its wording…". "Best at conversation" is gone from every branch (`:138-145`). Tests: `FrontDoorTests.swift:245`, `:255` |
| MINOR-6 (no routing deadline) | **DISCHARGED** | `Router.swift:429` (`modelTimeout = 8`), `:444`, `:478-505` (`firstWithin`, `ResumeOnce`). Tests: `FrontDoorTests.swift:348`, `:360`, `:370`. Mutant T1 (no deadline) fails `:348`. See NEW-3 |
| MINOR-7 (question dropped with no surfaces) | **DISCHARGED in code** | `ContentView.swift:220` and `:247` disable send and `Change`; `:249-250` show the note; `:484` reloads before routing, which covers Return. The disables are unpinned (NEW-2) |
| MINOR-8(a) (the notice above the old ranking) | **DISCHARGED** | see BLOCKING-2 |
| MINOR-8(b) (the failure view hides the card) | **ACCEPTED**, queued to M14 | — |
| NIT-1 (`black`) | **DISCHARGED** | only the nine hunks that predate the wave remain |
| NIT-2 to NIT-4 | **ACCEPTED** | — |

---

## Findings the fixes introduced

| # | Severity | `file:line` | Finding | Remedy |
|---|---|---|---|---|
| NEW-1 | MAJOR | `ios/ModelRanking/Engine/Router.swift:94-98`, `:234-242`; `ios/EngineTests/FrontDoorTests.swift:214` | **The decline hints over-decline.** A question declines whenever any single decline hint beats the best surface. None of the seven calibration probes at `:214` contains a trigger word, so the test cannot see the cost. See the probe table below. Three questions that the first-round tree routed correctly now come back unmeasured, each with no alternatives. The error runs in the honest direction: each is labelled "Going by its wording…" and can be corrected in two taps. But a measured geometry problem told that it is not measured is a new false sentence on the front door, and REQ-RTR-001 no longer holds for these questions | Add the three regressions to the calibration test as assertions. Then either decline only when a decline hint beats the best surface by a calibrated margin, or put the top two surfaces up as alternatives on the decline path, which makes a false decline a one-tap fix |
| NEW-2 | MINOR | `ContentView.swift:497`, `:220`, `:247`; `test_ios_client_contract.py:555` | Three new mutants survive the structural test. R1 deletes the routing guard after `ask()`'s load, so a `Change` made during that load brings back the overruled route's echo above the reader's chosen surface. R3 and R4 drop the `categories.isEmpty` disables. The send-button pattern was loosened, and now matches `.disabled(!canSubmit(...` without the closing parenthesis | Pin the second guard, and pin `\|\| categories.isEmpty` on both controls |
| NEW-3 | NIT | `Router.swift:478-487` | `firstWithin` never cancels the losing call. The timer task sleeps its full eight seconds even after the model answers, and a model call that hung keeps running. There is no memory of a hung tier, so every later question pays the full deadline again | Cancel both tasks once one resumes. Optionally, skip the model tier for the rest of the session after one timeout |
| NEW-4 | NIT | `docs/prd.md:439`, `:382`, `:430` | The retirement cites "council ruling E". In plan §7, ruling E4 is the vendor-URL ruling. The budget-strip ruling is the E-series tally in `docs/second-opinion.md:166` (Q4: "Removing the strip itself: unanimous"). Separately, and predating W3: REQ-API-010 is defined twice in the prd (`:382` and `:430`) | Cite `docs/second-opinion.md` Q4. Queue the duplicate REQ-ID to K.9 |

**The probe for NEW-1.** The shipping `SimilarityRouter()`, all nine surfaces, and the same
questions on both trees:

```
question                                                  first round        post-fix
"solve this geometry problem about a picture frame"       mathematics        assistant, unmeasured
"click through a website and upload a photo"              computer-use       assistant, unmeasured
"a web app for streaming video"                           web-dev            assistant, unmeasured
"calculate the speed of a train that travels 120 km…"     everyday (wrong)   assistant, unmeasured
"explain how sound waves travel through air"              everyday (wrong)   assistant, unmeasured
"reduce the latency of my REST API"                       everyday (wrong)   assistant, unmeasured
"write a python script to resize images"                  coding             coding
"build a web page with a photo gallery"                   web-dev            web-dev
"prove a theorem"                                         mathematics        mathematics
```

The first three rows are regressions. The next three move from a wrong measured answer to a
labelled unmeasured one, which is the safer failure but still not the right surface.

## Mutants run this round

**Swift, on the post-fix copy**, filtered to the front-door, router and slow-tier classes (53
tests):

| Mutant | Result |
|---|---|
| B1a: decline hints never fire | caught, 7 failures |
| B1b: decline hints always fire | caught, 15 failures |
| T1: no deadline on the model tier | caught: `FrontDoorTests.swift:348` |
| G1: `invalidate()` does nothing | caught: `FrontDoorTests.swift:83` |

**Python structural test.** M1 to M6 and R2 are caught. R1, R3 and R4 survive (NEW-2).

## Per-criterion verdict

| REQ-ID | Verdict | Code | Citing test |
|---|---|---|---|
| REQ-ASK-001 | **PARTIAL**, recorded as such (`docs/prd.md:481`). Focus is verified; the keyboard paths are the owner's to verify | `ContentView.swift:194` (`questionCard`), `:467` (`submit`); `FrontDoor.swift:45` | `FrontDoorTests.swift:97`, `:101`, `:105`; `test_ios_client_contract.py:555` |
| REQ-ASK-002 | **PASS** (MINOR-4 recorded; NEW-1 widens the two-tap case) | `FrontDoor.swift:68-101`; `ContentView.swift:231` (echo row), `:288` (sheet); `Router.swift:252-255` | `FrontDoorTests.swift:115`, `:139`, `:145`, `:152`, `:167`, `:310`, `:331` |
| REQ-ASK-003 | **PASS** (NEW-1 is an over-decline, not an under-decline) | `Router.swift:94-98`, `:234-250`, `:455-456` (manual); `FrontDoor.swift:116-155` | `FrontDoorTests.swift:187`, `:196`, `:205` (shipping tier), `:214`, `:234`, `:268`; `RouterBoundaryTests.swift:59` |
| REQ-ASK-004 | **PASS** | `FrontDoor.swift:24-43`; `ContentView.swift:488-508`, `:515-547` | `FrontDoorTests.swift:47`, `:63`, `:83`; `test_ios_client_contract.py:608-619`, `:636` |

## K.8 contract drift check

The diff touches no Python source, and `/v1` is unchanged. `/v1/budgets` stays on the engine.
**OK.**
