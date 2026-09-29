---
record_type: closure
id: closure-report-m17
status: draft
process_version: v6.6
date: 2026-09-29
---
# Closure Report — M17: lists nobody publishes, built on the phone

> **Read §0 first.** It is what needs you. Measured at `main` = `3f2e91d` plus the closure branch;
> `make gate` PASS at `00f9423`. From 2026-09-29 the agent proceeds on its own recommendations.

## 0. What needs the owner

1. **Use the app.** The engine service runs `main` (`release-3f2e91d`, deployed 2026-09-29), and the app
   is on the iPhone 17 Pro simulator. Type a task in your own words; a question about French or law
   shows the combined list, its chips and "Panolara bak".
2. **Tell the agent when a build is on your phone.** Then #61 (the combination) moves to `qa:ready`.
3. **Merge this closure PR, then the M18 plan's.** M18 covers the four areas you chose on 2026-09-29.
4. **Workflow edits are yours** (#81): `issue-agent.yml` cites a deleted file, and D-161 clause 4's
   change has no issue.
5. **Seeds** (§5): approve or refuse; the agent has not adopted any.

## 1. What shipped

| Acceptance criterion (from `docs/plans/m17-plan.md`) | Citing test | CI run | Status |
|---|---|---|---|
| W1: every floor is derived from the served board, every build (D-159) | `tests/unit/test_floor_served.py:50` | PR #11, #12 | ✅ |
| W2: Arena's category slices, each its own board (D-164, D-165) | `tests/unit/test_arena_slices.py:60`, `tests/unit/test_build_slices.py:56` | PR #23 | ✅ |
| W3: Epoch's own boards, the Agent Arena boards, accessibility, no ids from moving aliases (D-166) | `tests/unit/test_epoch_board.py:61`, `tests/unit/test_agent_boards.py:26`, `tests/unit/test_moving_aliases.py:21` | PR #43 | ✅ |
| W4: every board's standings on `/v1/boards` as positions; the phone keeps them daily (D-167) | `tests/unit/test_board_standings.py:218` | PR #62 | ✅ |
| #61: the combination, proved against an independent oracle (D-167 clause 3) | `ios/EngineTests/CombinePropertyTests.swift:79` | PR #65 | ✅ |
| W5: the question selects a surface plus declared refinements; the phone's own combined list (D-168) | `ios/EngineTests/AnswerPlanTests.swift:45`, `ios/EngineTests/RefinementBoundaryTests.swift:105` | PR #75 | ✅ |
| Closure: a stored date is a date, a score is finite, every reader opens read-only | `tests/unit/test_stored_scores_are_bounded.py:51`, `tests/unit/test_readonly_uri.py:136` | this PR | ✅ |

**Criteria diffs since plan approval:**
- **W5's intent schema** (task, domain, language, input size, constraints) became "surface plus a
  language or a domain" (owner, D-168).
- **The combination** left W4 at the three-attempts stop and returned as #65.
- **Moved to M18:** #66 (a question that is not a model search) and #73 (routing coding
  questions); each was measured and fell short (`docs/research/` on their branches).

## 1a. Per-wave table (close records: `docs/plans/m17-wave-{2,3,4,5}-close.md`)

| Wave | Risk | Seats (verdict first → last) | Findings | PR |
|---|---|---|---|---|
| W1 | MED | Code review BLOCKING, fixed in #12; **no close record** (K1) | fixed in #12 | #11, #12 |
| W2 | MED | Code BLOCKING → PASS-WITH-MINORS; four security rounds, BLOCKING ×3 → MINOR | #24–#27 filed | #23 |
| W3 | MED | Code PASS-WITH-MINORS; Tester BLOCKING → PASS-WITH-MINORS | #38–#42 filed | #43 |
| W4 | HIGH | Code BLOCKING → PASS-WITH-MINORS; Tester BLOCKING ×4 → stop; security PASS-WITH-MINORS | #51–#61 | #62 |
| W5 | HIGH | Code BLOCKING → PASS-WITH-MINORS; Tester, security PASS-WITH-MINORS | #66–#74 | #75 |

## 1b. Decisions made on your behalf

- **Your W5 rulings** are recorded as D-168 and its notes. Deploying `main` to your machine and
  proceeding without asking follow your instruction of 2026-09-29.
- **The per-milestone retrospective and security seat.** Both were retired by the D-161 amendment,
  but M17's plan still listed them. The seat was run (below); the retrospective was not written, and
  its content is in `docs/EXPERIENCE.md` and §5.
- **Which findings were fixed here** and which were filed follows the recommendation you told the
  agent to act on.

## 2. Git record

- Range `cf00ec7..3f2e91d`: 183 non-merge commits, 283 files, +25467/−6649. Code (`src/`,
  `ios/ModelRanking/`, `scripts/`) 57 files +4519/−893; tests 62 files +5843/−313; docs 66 files
  +11080/−1086.
- Mainline PRs:
  - **Waves:** #11/#12 (W1), #23 (W2), #43 (W3), #62 (W4), #65 (#61), #75 (W5).
  - **Fixes:** #29, #46, #47, #49.
  - **Process:** #18 (DevFlow v6.4), #19–#21, #30, #31 (branch protection), #34 (PRD statuses),
    #36 (the engine service, D-170).
- No AI attribution in any commit; the identity follows D-161.

## 3. Trust telemetry

| Task type | Post-closure fix rate | Churn (N-day) | Reverts | Findings (sec separately) |
|---|---|---|---|---|
| waves W1–W5 | 1 of 5 fixed after merge (W1, #12) | W4 S7 half-fixed, the rest #74 | 0 | 5 of 5 opened BLOCKING or had a BLOCKING round (sec: W2 ×3) |
| fix PRs | 0 of 4 | none measured | 0 | each had its own Tester |

**Agent self-report beside it:**
- **Seats caught what the author missed:** every wave's first review found something to block on.
- **The lead's slips:** a pushed red, a scripted edit reverted in place, a red commit with a lint error,
  and a skip budget only CI could see.
- **Two changes measured and not shipped:** #66 and #73.

## 4. Security & invariants

- **Gates at `00f9423`:** `make gate` PASS. pytest 1531 passed / 23 skipped; Swift 354 tests, each
  named in the manifest; conformance 16; gitleaks, pip-audit and slopsquat clean.
- **HIGH waves' passes:** `m17-wave-4-security.md` and `m17-wave-5-security.md`, both PASS-WITH-MINORS.
- **The closure seat** (`docs/reviews/m17-closure-security-review.md`): PASS WITH FINDINGS, 0/0/5/10.
  - Fixed here, each red first: MINOR-1 (INV-23 gate on every reader, `cc28d63` → `de2fc38`) and
    MINOR-2 (dates and finite scores where every client stores).
  - Filed: MINOR-3 (#85), MINOR-4 (#86); MINOR-5 moved W-125, W-126, W-130 and W-131 to M18.
- **Invariants list.** W-131: there is still no single list; the seat's §3 is the current one.
  **The Stage 5.1 release review is owed before any deploy.**
- ⛔-glob touches: none by the agent. `.github/workflows/**` edits are proposed in #81.

## 5. Ledgers

- **Skipped:** `docs/cost-log.md` (token spend is not visible); a deploy step (nothing deployed beyond
  the owner's Mac, tenth milestone); the seat's `deps`/`slopsquat` (no network; `make gate` ran both).
- **Bypasses:** W2's three-attempts waiver (owner); `strict` branch protection off (owner, 2026-09-27,
  recorded late); W1 merged under "review pending" (K1). Each is in `docs/control-events.csv` or here.
- **Milestone review** (`docs/reviews/m17-repo-review.md`), each finding fixed or filed:
  - **Fixed:** M1 (`cc28d63`), M3/M4/M6/M13-doc (`bd0869a`), M10 (`00f9423`), M16 (`6d57e5e`),
    M14/M15 (this commit).
  - **Filed:** M2 → #72, M5 → #76, M7 → #77, M8 → #78, M9 → #79, M11 → #68, M12 → #80,
    M13-owner → #81, K2 → #82, K3 → #83, K5 → #84.
  - **Recorded here:** K1 (W1) and K4 (#65 was HIGH through `/fix-issue`).
- **Found by the owner's first look:** `app.sh` installed on the wrong simulator (`f7a05d2` →
  `8383001`).
- **Seed candidates** (proposed, not adopted): measure the baseline before the bar; a text pin reads
  code, not comments; drive a screen change before its wave closes; an artifact-only test moves the
  skip budget in the same change.
- **Risks queued to M18:** #66, #73, #63, #69, the backlog issues, W-123, W-125, W-126, W-129, W-130,
  W-131.

## 6. Architecture delta

M17 moved the answer onto the phone. The engine still owns the data: it builds every board, derives each
surface's floor from the served rows (D-159), and now publishes every board's standings as positions, never
scores, on one parameterless route (D-167). The phone fetches that once a day, beside the answer and never
before it, keeps it, and does two new things. The on-device model reads the question into a closed schema:
a surface and at most one language and one domain from a declared table, checked again by
`ModelOutputBoundary` so no model text reaches a choice (D-168). And when that selects more than one
board, `Combine.swift` builds the product's own list: only the models every board ranks, ordered by summed
position, ties sharing a place. The detail says so, dates each board, and names the efforts (D-112).

What could break:
- **The on-device model's reading is the weak link, not its boundary.** Coding questions reach coding
  about a quarter of the time (#73), and it cannot yet tell a model search from a request to do the task
  (#66).
- **The standings payload** is about 500 KB a day, and a board with an undeclared metric used to take the
  whole route down; that is now gated.

What a maintainer must know:
- Positions are the only numbers the phone combines (D-105, D-160 clause 2), and only `Combine.swift`
  does arithmetic on them.
- Nothing the reader types leaves the device; the routed surface id is sent as `task`, as since D-126.
- The engine runs as a launchd service from a deployed release (D-170). A merge is not live until the
  installer runs again.

---
*Assembled from raw referents at closure. Owner sign-off: pending, by merging the closure PR (DevFlow: a human merges); the merge date is the sign-off date.*
