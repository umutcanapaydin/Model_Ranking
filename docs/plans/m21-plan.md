---
record_type: plan
id: m21-plan
status: draft
process_version: v6.6
date: 2026-10-08
---
# M21 Plan — the open queue: the data, the reading, the phone's gates, the controls

**One sentence.** M21 takes the open issues M20 leaves: the data a reader sees, the reading of
questions that are not searches, the phone's compiled gates, and the project's own controls.

**The goal is the owner's.** On 2026-10-08 the owner asked for the open issues and enhancements to be
coded, in a milestone of their own, after M20's combined list. The owner approves this plan with
M20's, by merging its pull request. GitHub milestone: `M21: the open queue`. It runs after M20, or
beside it where a wave touches nothing M20 touches.

**Cap and order.** Four waves. W4 is the controls wave, so it is the one to drop. Each wave ends with
`/close-wave`. The milestone ends with one security seat and a repo review.

## 1. Acceptance criteria (REQ-IDs)

| Wave | REQ-IDs | Criterion |
|---|---|---|
| W1 | REQ-CAN-001, REQ-SRC-010, REQ-REL-001 | A release's later snapshot, a retired id and a fine-tune's price each stay with their own model (#163, #164, #165). The attributions match their publishers' terms (#124). `web-dev` reads LMArena's own CC-BY board (#185). The deploy names the release that built its data (#198), and the derivation refuses a missed copy of a left-out source (#205). |
| W2 | REQ-ASK-005 | A question of fact names no AI model the engine ranks as a doubt (#194). The held-out checks read the wording tier's sentences, and match a list entry as the app does (#180, #186). The replay harness and the probe's wording mode have tests (#193). The reading of non-searches is measured on #195's fresh set (#66). |
| W3 | REQ-GAP-001, REQ-APP-005 | The compiled gates follow a served number and the reader's text through the routes the reviews found open (#168 to #175, #188, #85). The held-reading logic moves into the Engine, where tests reach it (#132). Each closing gap is shown red on its planted mutant. |
| W4 | none new (controls) | The gates see what the reviews said they miss: ADR pointers and timing (#200, #201), skipped gates and the process log (#202, #203), the HIGH rule's diff (#183), CI's kept list (#182), the deadline and offline tests (#122, #178, #179, #181, #108). #189's guard change is in its own commits for the owner's approval. |

## 2. Waves

### W1 — The data a reader sees (risk: **HIGH**; #163, #164, #165, #124, #185, #166, #198, #205, #214, #216, #228)

`src/app/clients/**` and the registry change.
- **#163, #164, #165:** each in the registry's curated rules, with the maker's page as the source.
- **#185:** LMArena's WebDev board (CC BY 4.0) as `web-dev`'s source, beside Epoch's copy.
- **#166:** the first nightly refreshes since M19-W1, read against its simulation and recorded.
- **#198, #205:** the deploy stamp and the survivor check.
- **#214, #216** (from M20-W1's and M20-W2's reviews): the board tables read without the client, and one
  90-day line in the engine.

### W2 — Reading what is not a search (risk: **HIGH**; #66, #194, #180, #186, #193, #199, #218, #222, #226)

`Router.swift` and `Reading.swift`.
- **#194:** the exclusions come from the registry's model families, not eleven brands.
- **#180, #186, #193:** the held-out checks and the harness tests.
- **#66:** measured on #195's set (M20-W5) and closed or carried with its number.
- **#199** (from M20-W4, after its review): the UI target's scripted routing and the reading each test
  expects in one fixture an Engine test reads.
- **#218** (from M20-W3's second review): a short Turkish question with one word beyond model names
  is read as Turkish before the embedding.

### W3 — The phone's promises, held further (risk: **HIGH**; #85, #132, #168 to #175, #188, #219, #220, #223)

The privacy sinks and the arithmetic rule (D-180, D-181).
- **The gaps G-1 and G-2 narrow:** a default value, a static initialiser, a kept closure, `Any` and
  text (#171, #172); the operators and names the reviews found (#173); INV-64 on the compiled module
  (#174); a file read by a URL initialiser (#168); the standings date from the screen (#170); the
  text tripwire derived from the decoded types (#169); the budget argument (#188).
- **#175:** the gate on a Mac without Xcode's layout fails closed and says so.
- **#132:** the held-reading logic leaves `ContentView`.

**The one alternative:** stop at the routes a reader's text can actually take today. That is less
work, but the reviews found each of these routes by planting it.

### W4 — The controls (risk: **HIGH**; #122, #178, #179, #181, #182, #183, #108, #189, #200 to #203, #227)

Gate definitions change, so the owner reviews the wave (AGENTS.md §3).
- **#200 to #203:** `make check-records` and `make wave-check` read the ADR pointers and timing, the
  skipped gates and the process log.
- **#183, #182:** the HIGH rule reads the range's diff; CI's job list is derived, not kept by hand.
- **#122, #178, #179, #181, #108:** the offline and deadline tests.
- **#189:** the Bash guard's spellings and its loading. Hook changes go in their own commits marked
  OWNER APPROVAL.

## 3. Risk tiers and security globs

- **HIGH waves:** all four.
- **Security globs.** A diff touching any of these makes a wave HIGH (M20's list, and `Reading.swift`):
  - `src/app/adapter/main.py`, `src/app/clients/**`
  - `scripts/*engine_service*.sh`
  - `ios/ModelRanking/Engine/EngineClient.swift`, `Router.swift`, `StandingsStore.swift`,
    `FrontDoor.swift`, `Combine.swift`, `AnswerPlan.swift`, `Reading.swift`
  - `ios/ModelRanking/ContentView.swift` (added at M21-W3, #188: the screen builds the request's arguments)
  - `tests/conftest.py`
  - `.github/workflows/**`, `.claude/settings.json` (the owner's)
  - `.claude/hooks/**`, `.githooks/**` (the guards the hooks run; added at M21-W4, the Tester's K1)
  - `scripts/client_decl_gate.py`, `scripts/client_decl_fixtures/**`, `tests/unit/test_router_hints.py`, `tests/unit/test_ios_client_contract.py`, `scripts/offline.sb`, `scripts/wave_check.py`, `scripts/check_records.py`, `Makefile` (the gates that hold the invariants; added at the M21 closure, the repo review's M3)
  - the deploy surface: `Dockerfile`, `fly.toml`, `.dockerignore`, `scripts/deploy_hosted_engine.sh`,
    `src/app/workflows/public.py`, `ios/Config/**`

## 4. Spike check

None.

## 5. K.8 contracts

No `/v1` field changes. W1's source for `web-dev` is new data under an existing surface; W3 and W4
change gates, not contracts.

## 6. Token budget

About 2M tokens; not measured per wave.

## 7. Issue inventory

| Wave | Issues |
|---|---|
| W1 | #163, #164, #165, #124, #185, #166, #198, #205, #214, #216, #228 |
| W2 | #66, #194, #180, #186, #193, #199, #218, #222, #226 |
| W3 | #85, #132, #168, #169, #170, #171, #172, #173, #174, #175, #188, #219, #220, #223 |
| W4 | #122, #178, #179, #181, #182, #183, #108, #189, #200, #201, #202, #203, #227 |

**Left out:** #81, #115, #190: the owner's (CI workflow, the phone's prompt, the owner's settings).

## 8. Closure tasks

- `/repo-review` across the milestone, and the one closure security seat (D-172).
- Capture per `docs/closure-checklist.md` §B.2.
