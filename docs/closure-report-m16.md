---
record_type: closure
id: closure-report-m16
status: draft
process_version: v6.0
date: 2026-09-23
---
# Closure Report — M16: the product keeps itself current

> **Read §0 first.** It is what needs you. Everything below it is evidence for the claims in it.
> Every figure was measured at `main` = `eee2faf` plus the closure branch.

## 0. What needs the owner

1. **Retire the launchd refresher.** The engine refreshes itself nightly (D-151, D-154).
   - Run `./ios/app.sh restart`, confirm that `curl -s localhost:8080/health` shows
     `"refresh": "scheduled"`, then run `scripts/retire_refresh.sh`.
   - Until then the installed wrapper passes the retired 2026-08-15 Epoch bundle, and it runs
     whatever branch is checked out in the repository directory.
   - M16's definition of done asked for this or a reason; the reason is that it is your machine.
2. **Publish the first artifact with derived models by hand, after step 1.** D-132 refuses it in the
   nightly cycle, which is correct for a change this large:
   - `assistant` would be about 124 of 189 names new, with its median price at $2.95 → $0.83;
   - the before/after for every surface is in `docs/research/m16-w4-derived-registry-2026-09-23.md`.
3. **Remove the CI step that ages `data/epoch-source.yaml`** (D-158 clause 4). This is a workflow
   change, so the agent proposes it and does not make it. The diff is in PR #6's body.
4. **Rule M17's four questions before its waves** (`docs/plans/m17-plan.md` §0):
   - the floors on fresh data (W-128);
   - the tie-margin rule (W-127);
   - how a combined list says it is the product's own;
   - what leaves the phone.
5. **Approve or refuse five playbook seeds** (`docs/retrospectives/m16-retrospective.md`). The first
   is the one this milestone paid for: "review pending, do not merge" as a PR's first line.
6. **Sign** at the bottom, and merge the closure PR.

## 1. What M16 shipped

| | |
|---|---|
| **The engine refreshes itself** | Once a night, inside 23:00-01:00, in a child process that is off by default and refused in production (W2, D-151, D-154). No "update now" button: the boards move over days. |
| **A failed source no longer blanks a surface** | Its last good data is carried for 30 days from its last served arrival. Past that its surfaces drop and the rest publishes (W3, D-156). An expiry night is judged against the artifact without the expired rows, so only their loss is excused. |
| **Every floor follows one rule** | The top third of the board's rows (W3, D-148). You ruled `agentic-coding` too, and one Budget Pick moved. |
| **Every board is fetched by the refresh** | The Epoch bundle is downloaded and unpacked as untrusted input (W4, D-158). Nine of nineteen sources used to be carried every night from a hand-downloaded folder. |
| **A changed upstream layout is loud** | Epoch moved its capabilities index. Such a change is now "drift" by name in the refresh record and `/health`, instead of a quiet carry. |
| **A model on the boards reaches the lists** | Under your "the list wins, the data derives the rest" (D-157). Unmatched score rows: 1,450 of 2,834 → 652 of 2,581. Models: 74 → 317. A closed list of decorations means the grammar can split one model into two spellings, but never merge two models. |
| **Contracts** | `/v1` publishes each surface's floor and what a search price leaves out, and the app shows both (W1-W2: W-112, W-119). The privacy gate reads the declarations the compiler resolved (W-122). Every Swift test is on a committed list (W-111). |
| **The process** | DevFlow v6.0 (D-155): drafts, you merge, no AI attribution, CI on every PR. `make check-fast` runs the same gates side by side, in 33 s against `make check`'s 89 s. |

## 1a. Per-wave table (close records: `docs/plans/m16-wave-{1,2,3,4}-close.md`)

| Wave | Risk | Review depth applied | Seats (verdict at first → last) | Merged |
|---|---|---|---|---|
| W1 | MED | combined + two re-reviews | BLOCKING → PASS (`docs/reviews/m16-wave-1-*.md`) | `acef579` |
| W2 | HIGH | Code + security | PASS WITH FINDINGS ×3 (`m16-wave-2-review.md`, `-rereview.md`, `-security.md`) | `5fc3f02` |
| W3 | MED | combined + two re-reviews | BLOCKING → PASS-WITH-MINORS (`m16-wave-3-*.md`) | #3 |
| W4 | HIGH | security on P1 + Code+Tester + re-review | BLOCKING → PASS-WITH-MINORS (`m16-wave-4-*.md`) | #5, #6, #8 |
| W5 | LOW | Stage 4.0 security seat | PASS WITH FINDINGS, 0/1/6 (`m16-closure-security-review.md`); the MAJOR and three minors fixed in the closure | the closure PR |

## 1b. Decisions made on your behalf

- The W4 grammar's decoration list, the vendor-family table, and the choice that the grammar may
  split one model into two spellings rather than merge two models (D-157 amendment).
- `make check-fast` keeps `make check` as the merge gate. The parallel Swift run reports a skipped
  test as passed, so check-fast scans the test sources for skips instead.
- AGENTS.md is back under D-003's 150-line cap (149). The git-authority history and the K.7/K.8
  reasons moved, unchanged, to `.agents/rules/git-authority.md` and `.agents/rules/review-seats.md`.
- W-123 (what people ask) moved to M17 with the W4 it belonged to.

## 2. Git record

- Range `059b519..eee2faf`, mainline: `89b9b3c`, `acef579` (W1), `5fc3f02` (W2), PR #1-#2
  (DevFlow), #3 (W3), #4 (plans re-verified), #5-#6 (W4), #7 (check-fast), #8 (W4 fix round).
- Diffstat: code (`src/`, `ios/`, `scripts/`) 43 files +4106/−389; tests 21 files +2682/−14;
  docs 56 files +6474/−1607; the rest is the DevFlow installation.

## 3. Trust telemetry

| | |
|---|---|
| Findings by independent seats | 8 of the 12 wave review records opened with a BLOCKING or MAJOR finding; every one is fixed or ledgered in its wave close |
| Findings after merge | One: PR #6 was merged before its review returned BLOCKING, and was fixed in PR #8. No wrong artifact was served (D-132 refused the candidate). |
| Reverts | none |

**Agent self-report beside it:** the lead's own tooling slipped five times this milestone (the
retrospective lists them). Each was caught and repaired before a merge, but the seats caught the
defects that mattered.

## 4. Security & invariants

- **Gates at the closing tree:** `make check` exit 0 on the owner's Mac: pytest 1172 passed / 15
  skipped, Swift 268 (each named in the manifest), conformance 14 PASS, client-decls PASS,
  check-records and wave-check-all PASS; `make closure-check` PASS on this report.
- Stage 4.0: **PASS WITH FINDINGS**, 0 BLOCKING / 1 MAJOR / 6 MINOR / 8 INFO
  (`docs/reviews/m16-closure-security-review.md`). gitleaks clean on the range, pip-audit clean, no
  new dependency. Fixed in the closure, each red first:
  - **MAJOR-1:** a derived model's served name came verbatim from upstream text (D-157 second
    amendment);
  - MINOR-1: `/health`'s unmatched names are bounded;
  - MINOR-2: a test now holds INV-23 on the carry; the seat's surviving mutant is RED;
  - MINOR-4: `ios/app.sh` no longer pins the hand-kept Epoch bundle, so the engine's own nightly
    fetches.

  Ledgered: MINOR-3 (W-130), MINOR-5 (W-131: the seat's 25-row table is the current invariants
  list), MINOR-6 (W-125 and W-126 move to M17).
- The untrusted-archive path had its own pass before merge (`docs/reviews/m16-wave-4-security-p1.md`,
  F1 BLOCKING fixed); W2's child process had `docs/reviews/m16-wave-2-security.md`.
- Invariants: INV-23 (read-only artifact) is kept by every new reader, including the expiry
  baseline's in-memory copy. The privacy invariant is now checked on resolved declarations (W-122).

## 5. Ledgers

- **Skipped:**
  - `docs/cost-log.md`: not kept by this project; token spend is not visible to the agent.
  - No deploy step (B.3): nothing deployed, ninth milestone.
  - `make journey`, `make cold-start`: written N/A, since there is no runnable surface beyond your
    machine.
- **Control bypass:** `/pre-merge` did not run before PRs #3 and #6 were merged (retrospective).
- **Seed candidates:** five, in the retrospective, for your approval.
- **Risks queued to M17:**
  - W-127 (margins), W-128 (floors on fresh data);
  - W-129 (data licences; kept and recorded until a commercial launch);
  - W-125, W-126 (the serving process's imports; a stuck child after a hard kill), W-130, W-131;
  - about thirteen derived ids on reused names.

## 6. Architecture delta

M16 moved the refresh from a job beside the product into the product. The engine starts
`refresh.py` as a child process once a night. The child builds a candidate artifact, and the
refresh publishes it only if what readers would see changed and nothing got worse (D-128, D-132).
Three new mechanisms sit inside that loop:
- **Carry-forward (D-156).** A source that fails serves its last good rows, copied read-only from
  the live artifact, until 30 days after its last served arrival. On the night one expires, the
  candidate is judged against the live artifact without that source's rows, so the guards excuse
  exactly that loss and nothing more.
- **The fetch (D-158).** The refresh downloads the Epoch bundle into scratch beside the artifact
  and unpacks it as untrusted input. Every refusal becomes a failed source that carries.
- **Derivation (D-157).** In the registry, a name no curated rule matches is normalised by a closed
  grammar and registered only when it has both a price and a score.

What could break:
- An upstream renames a file or a column. That is now drift on `/health`, not silence.
- An upstream reuses a name for a new release. The grammar cannot see that; a curated rule can.

What a maintainer must know:
- The guards (D-128, D-132) are the product's safety. They refuse legitimate large changes too, by
  design, and those are published by hand.
- The served artifact is only ever opened read-only (INV-23).

---
*Generated from raw referents at closure. Owner sign-off: pending -- the owner signs by merging the closure PR (DevFlow: a human merges), and the merge date is the sign-off date.*
