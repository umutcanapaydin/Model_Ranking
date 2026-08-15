---
record_type: ratification
id: closure-report-m4
status: candidate
date: 2026-08-15
---
# Closure Report — M4: Make the Plan Answers Real

> Owner's A0.5 milestone-session review pack. Generated 2026-08-15 from committed artifacts
> (4 wave commits `0f840a9..20312a1` + this closure commit; wave checklists and review verdicts
> cited, not recalled). Owner amendment in force: no stops between waves; the agent ran every gate
> per wave (D-106); the owner runs the out-of-sandbox verification at THIS session.
>
> **Status: candidate — NOT closed.** The quality gate is BLOCKING on one signature. See §0.

## 0. The one thing that needs you (read this first)

M4's signed headline criterion was: *"live end-to-end proof that `--subscription` offers **≥3
distinct plans**"*. On live data that criterion **cannot be met honestly.** Measured 2026-08-15
from your Arena fetch plus the live sources:

| Plan | $/month | Ranks via | Score |
|---|---|---|---|
| Perplexity Max | 200.00 | Claude Opus 5 | 1507.8 |
| Google AI Plus | **4.99** | Gemini 3.1 Pro | 1479.6 |
| Google AI Pro | 19.99 | Gemini 3.1 Pro | 1479.6 |
| Perplexity Pro | 20.00 | Gemini 3.1 Pro (roster) | 1479.6 |
| Google AI Ultra | 99.99 | Gemini 3.1 Pro | 1479.6 |

Four of the five scoreable plans run the same model. Producing three "distinct" answers would have
meant preferring a $99.99 plan over a $4.99 plan across a difference of **zero** — the exact
dishonesty this product exists to refuse. So the criterion was **restated in the open**: the engine
now names the equivalence and points at the cheapest, with the spread. That decision is written as
**D-110** and the substitute behaviour is fully tested — but an agent may not retire a criterion the
owner signed, so the quality gate stays BLOCKING until you rule.

**What I need from you, in one line each:**

1. **Ratify D-110** (equivalence disclosure replaces "≥3 distinct plans") — or reject it, and I carry
   the original criterion to M5 unmet.
2. **Accept REQ-ING-010 + REQ-ING-011b as a criteria diff to M5** (Epoch / fresh coding benchmark —
   blocked by the sandbox proxy, unblock = one fetch on your machine; commands re-listed in §5).
3. **Rule on W-001** — the gitleaks false positive, now surviving its second milestone because an
   agent may never waive a scanner finding. The exact stanza to paste is in §5.

Everything else in this report is done, tested and committed.

## 1. What shipped (signed plan m4-plan.md §2 — criteria diffs: THREE, all named)

| Criterion | Citing test / gate | Status |
|---|---|---|
| REQ-CAN-004 registry expansion, self-defending rule table | test_registry.py: rule-table property tests + 41-entry live-name corpus | ✅ (W1) — plan-name drops **2 → 0** |
| REQ-ING-009 provider rosters as a second documented source | test_rosters.py (14) incl. CLI, tie-break pair, migration | ✅ (W2) — assistant coverage **3/9 → 5/9** |
| REQ-SUB-005 plan coverage measured and reported | test_coverage.py: counts, both failure buckets, CLI exit 1 on zero | ✅ (W3) |
| REQ-ING-011a source health computed, fails toward disclosure | test_coverage.py: window boundary, unparseable date, window parity | ✅ (W3) |
| REQ-ING-011b ingest a fresher coding benchmark **if one exists** | none — no code to cite | ⏸ **DEFERRED to M5** (§5) |
| REQ-ING-010 Epoch AI ingestion | none — no code to cite | ⏸ **DEFERRED to M5** (§5) |
| REQ-REC-009 ≥3 distinct plans | substitute (equivalence) covered by 5 tests, 4 mutants RED | ⚠ **RESTATED — needs your signature** (§0) |
| REQ-REC-010 boundary rounding, 1 decimal | 6 tests across both engines, 4 through the real CLI | ✅ (W4) — D-109 |
| REQ-SUB-006 Google AI Plus re-probe | test_sub_dollar_price_survives_the_seed_exactly + seed end-to-end | ✅ (W4) — entered at **$4.99** |

## 1a. Per-wave table

| Wave | Tier | Review | Findings found / closed | Test Δ | Escalations |
|---|---|---|---|---|---|
| W1 registry expansion | LOW | combined — FAIL→fixed | 4 BLOCKING + 3 MINOR / 7 | +18 | none |
| W2 rosters | LOW | combined — FAIL→fixed | 1 BLOCKING + 5 MINOR / 6 | +14 | none |
| W3 coverage + source health | LOW | combined — PASS | 3 MINOR / 3 | +9 | REQ-ING-010 blocked (evidence recorded, not hidden) |
| W4 rounding + equivalence | LOW | combined — FAIL→fixed, **then a second fresh-eyes pass on the fix delta** — FAIL→fixed | round 1: 2 BLOCKING + 5 MINOR; round 2: 1 BLOCKING + 6 MINOR / 11 closed, 3 ledgered | +23 | **escaped-blocker tripwire** (§3) |
| closure | — | Security **PASS** (0 BLOCKING, 6 MINOR) + Quality gate **BLOCKING** (§0) | 6 MINOR + 2 findings / 3 fixed, 5 ledgered | +2 | one signature (§0) |

## 1b. Decisions made on your behalf (assumption ledger)

- **Google AI Plus enters at $4.99.** M3's "dispute" ($4.99 vs $7.99) was not a disagreement: $7.99
  was the US launch price, cut to $4.99 on 2026-06-08, reported the same day by four independent
  outlets. The two trackers are dated either side of one price change. Its model list comes from
  Google's own page — an amount may be cross-checked against secondary sources, a model list may not.
- **ChatGPT Pro, Claude Pro/Max and ChatGPT Go still rank on nothing** and are disclosed as unscored:
  their pages and rosters name no model version. W2 closed every gap the published evidence allowed.
- **Coding coverage went 1/9 → 1/10** — not a regression: the denominator grew by one plan while
  SWE-bench has published nothing since 2026-02-26. That number is now printed on every run.
- **Rounding is 1 decimal** for both scales (Elo and % resolved). Chosen because no source publishes
  meaningful precision beyond it; one command changes it (`SCORE_DECIMALS`).
- **Read-only means read-only:** the coverage CLI now opens the database with `mode=ro`, so it cannot
  mutate your file even by accident.

## 2. File record (git = 4 wave commits + this closure commit, D-106 + V4C-64 trailers)

M4 net: **~2.0k added lines across 24 files** in the waves, plus this closure pass. New modules:
`rosters.py`, `coverage.py`; `data/rosters.yaml`; new records `m4-w1-registry-droplist.md`,
`m4-w3-source-health.md`, `m4-w4-equivalence.md`, `m4-security-review.md`, `coverage-by-req.md`.
Suite **152 → 193 unit + 5 gated**; total coverage **92%** (subscribe 98%, registry 100%,
recommend 95%, plans 93%, coverage 91%, rosters 85%).

## 3. Trust telemetry (first mechanically-computable milestone — M3 set the baseline)

- **Waves that produced review findings: 4/4.** 27 findings raised, 24 closed in-wave, 5 ledgered
  with owning milestones, 3 fixed at closure.
- **Fault injections: 18 mutants, 18 RED** after the fixes (2 STAYED GREEN when first probed — both
  are now covered; see the tripwire below).
- **Escaped-blocker tripwire: 1 (W4).** A fix written to close a review finding shipped with **no
  citing test**, and was caught only because the fix delta got a second fresh-eyes pass. Lesson
  adopted: *a fix authored in response to a review is new code and inherits the review obligation* —
  "it was written to close a finding" is not evidence that it works.
- **Control bypasses (V4C-13): 0.** Token spend exceeded the plan's W4 estimate (~60k) because of the
  second review round; recorded in the wave checklist rather than absorbed silently.
- Councils convened: 0.

## 4. Security & invariants

Stage 4.0: **PASS** — `docs/reviews/m4-security-review.md`, 0 BLOCKING, 6 MINOR, 4 NOTE.

- **gitleaks: 1 finding, 0 secrets** — the ledgered W-001 false positive (an ADR compliance label in
  prose). M4 added none and *cleared* one: 2 findings at M3 → 1 now.
- **pip-audit: no known vulnerabilities**, 0 advisories. No dependency was added in M4.
- **No new network surface at all** — `git diff -- src/app/clients/` for the milestone is empty. No
  URL is built from data; Artificial Analysis remains absent (D-101).
- **No security-invariant test was modified or deleted**; the test diff is +919/−16 and every removed
  line was replaced by a stricter assertion.
- All new SQL is parameterised; the two f-string query sites interpolate module constants only.
- Fixed at closure from the review: the coverage CLI's read-only claim is now a mechanism (`mode=ro`),
  and the equivalence sentence no longer overclaims what a plan page says (both with citing tests).
- Ledgered from the review: W-003 (roster `last_verified` written but never read), W-004 (`migrate()`
  built but not wired — a pre-W2 database fails CLOSED, exit 2), W-005 (YAML alias expansion can
  exhaust memory on a hostile curated file; no untrusted producer today, revisit with the M5 API).

## 5. Ledgers (nothing silent)

**Owner actions, exact text:**

1. **W-001 gitleaks allowlist.** Add to `.gitleaks.toml`, or tell me to and I will:
   ```toml
   [[rules.allowlist]]
   description = "ADR compliance label in prose (zero-entropy, not a credential)"
   regexes = ['''D-1\d\d-compliant''']
   paths = ['''docs/.*\.md''']
   ```
2. **Epoch AI + Terminal-Bench fetches** (unblocks REQ-ING-010 and REQ-ING-011b). Both are one
   command each on your Mac, writing into `terminal_output/model_ranking/`; the commands were
   delivered 2026-08-15 and are unchanged. Without them, both criteria carry to M5 as an accepted
   diff, with `docs/reviews/m4-w3-source-health.md` as the reason.
3. **First CI runs** of the coverage-report and roster-staleness legs are still yours to trigger
   (Actions tab), as with M3's plan-staleness leg.

**Carried to M5 (warnings ledger, each with an owning milestone):** W-002 `equivalent_plans` loses
group structure with 2+ groups (decide with the API contract) · W-003 roster staleness not disclosed ·
W-004 `migrate()` not wired to a command · W-005 YAML expansion guard · W-006 the `dusuk` case never
says that five plans were priced out (the sharpest remaining honesty gap, and a new output field).

**Standing debt, unchanged:** `scripts/` fails repo-wide ruff/black because the gate is scoped to
`src tests` — structurally invisible, GP-upstream note, third milestone running.

## 6. Architecture delta — PROSE

M3 built the plan answer; M4 made it true. The milestone's shape is a single argument: a
recommendation is only as honest as the link between a plan and the model it actually runs, so this
milestone spent itself on that link and on measuring it. The registry — the product's living IP —
became a table that defends its own ordering, and plan-name drops went to zero. Where a provider's
plan page names no model at all, a second documented source now speaks: the provider's own model
list, ingested as its own source with its own provenance and its own clock, never merged into the
plan page's claim, and the recommendation text says which of the two named the model. Coverage
stopped being something an owner discovers in a demo and became a number the pipeline prints on
every run, split into the two failure modes that have different fixes — a plan we could not link,
versus a plan we linked to a benchmark that has published nothing in six months. That second number
is the milestone's uncomfortable finding: the coding category rests on a source frozen since
February, and the product now says so out loud on every run rather than implying currency it does
not have.

The last wave turned that same discipline on the output itself. Scores reach the contract rounded
once, at the boundary, with every comparison upstream still running on raw values — and every
sentence about a gap computed from the numbers the user can actually see, so the prose can never
contradict the fields beside it. And when the evidence says four plans are the same engine wearing
four badges at four prices, the engine now says exactly that, names the cheapest, and quotes the
spread — $4.99 against $99.99 — instead of manufacturing three "choices". That sentence is the
clearest statement this codebase has yet made of what it is for. Break-glass for a future
maintainer: the equivalence claim is only as good as the group's construction (budget-filtered rows,
keyed on `plan_id`, provenance stated), and the coverage number is the early-warning system for the
day the underlying benchmarks stop being able to tell any two plans apart.

---
*Owner sign-off: **PENDING** — three items in §0. M4 is NOT closed until they are signed.*
