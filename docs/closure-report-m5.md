---
record_type: ratification
id: closure-report-m5
status: candidate
date: 2026-08-16
---
# Closure Report — M5: Rescue the Coding Category

> Owner's A0.5 milestone-session review pack, generated 2026-08-16 from committed artifacts.
>
> **Status: candidate — NOT closed.** Two items need the owner (§0). Everything else is done,
> tested and committed.
>
> **This milestone had two agents.** The first planned and built W1–W4 and ran out of budget at a
> checkpoint commit labelled `wip: NOT reviewed`, with four files still uncommitted and no review of
> any kind having run. The second inherited it with no handover, reconstructed the state from the
> files, and closed it. That is worth stating plainly because it is the reason this report has an
> unusually large "found at closure" section — and because the handover the first agent left in the
> repository (wave-close checklists, review records, a W4 implementation plan) is what made the
> reconstruction possible at all.

## 0. What needs you (two items)

**1. Ratify D-112 — the effort-comparison rule.** This is the criterion-meaning question the
quality gate is blocking on, and it is yours by the escalate-now rule, not mine.

Your Q1 ruling was: *rank on ONE named effort level and disclose the range.* `agentic-coding` does
exactly that (DeepSWE publishes efforts; the category names `high`). `coding` cannot, and the cost
is measured, not guessed — 28 rankable models on your Epoch bundle:

| `coding.ranking_effort` | Rankable models |
|---|---|
| **(none — today)** | **28** |
| `unspecified` | 19 |
| `high` | 4 |
| `max` | 3 |

No level keeps the board. The measurement also found the reassuring half: **no model carries both
an unspecified and an explicit effort row**, so the engine never inflates a single model — Trap 2's
headline failure does not occur on this board. What does occur is a comparison between models run at
different efforts (Opus 4.7 at `max` = 83.5 above Opus 4.6 at an unstated level = 78.7), and until
this milestone nothing said so.

D-112 proposes: keep the 28, publish each pick's OWN evidence effort, and carry a notice whenever
the compared answers come from different levels. **Sign it, or rule that Q1 binds every category and
`coding` takes a level — in which case the board shrinks to 19 or fewer and that is your call.**

**2. Review the schema migration.** `permission-matrix.md` §11 makes a migration change BLOCKING
until senior human review. The security reviewer's pass cannot substitute for yours. The command is
`python -m app.workflows.schema migrate --db PATH`; it opens `mode=rw`, is atomic, idempotent,
refuses a database it cannot repair, and leaves no rebuild table behind — all probed against six
database shapes. Your review is a formality only in the sense that it is required.

Also non-blocking but yours: **W-001** (the gitleaks false positive) has now survived THREE closes
and fires at two paths against a one-path ledger row; **D-111** (budget disclosure) awaits
ratification with D-112.

## 1. What shipped

| Criterion | Status |
|---|---|
| REQ-ING-010 Epoch as a first-class source | ✅ 22 citing tests; CI staleness leg |
| REQ-ING-011b a fresher coding benchmark, INGESTED | ✅ **both fork branches** — Epoch carries a real evaluation date; DeepSWE refuses to age on a release date and reports its evidence undated |
| REQ-CAN-005 effort parsed and stored, never swallowed | ✅ (under-count of unclassifiable rows ledgered as W-010) |
| REQ-REC-011 the answer states its effort level and range | ⚠️ **BLOCKING on §0.1** — covered for `agentic-coding`, and for `coding` only in the form D-112 proposes |
| REQ-SUB-007 coverage re-measured through the real engine | ✅ before/after below |
| REQ-LIC-001 Epoch CC-BY attribution where the data is served | ✅ one constant, derived per payload, README + export + both payloads |
| REQ-REC-012 the Gemini contradiction resolved or disclosed | ✅ carried on both categories with `verdict: unresolved` and the log id pinned |
| REQ-REC-013 / D-111 budget exclusion counted and disclosed | ✅ including the all-excluded case |

**The number this milestone existed to move.** Coding plan coverage, measured through the real
engine, not asserted:

| Surface | Before | After |
|---|---|---|
| `coding` | 1/10 | **5/10** |
| `agentic-coding` (new) | — | **6/10** |
| Unique plans rankable on either | 1/10 | **6/10** |

The two numerators must not be added: the categories overlap on five plans, and the one plan DeepSWE
adds that Epoch cannot is ChatGPT Pro. The record says so where the numbers live.

**The board decision, resolved without breaking D-105.** `coding` stays on SWE-bench Verified;
DeepSWE becomes a SEPARATE `agentic-coding` category at effort `high`. No benchmark is mixed inside
a category — verified independently at the W4 review and again at the security review.

## 2. Found at closure — the part that matters

W4 arrived unreviewed. The fresh-eyes review found **3 BLOCKING + 9 MINOR**; the security review
then found **1 more BLOCKING + 7 MINOR**; and running the real bundle through ingest found one
defect neither review caught. Every one of these was live in the tree you were about to be handed:

1. **`schema migrate` printed success over a database it had not repaired.** A pre-M3 `plans`
   missing `observed_at` migrated with exit 0 — and the next `recommend --subscription` died with
   `no such column`, the exact symptom the command exists to remove, now behind a success message.
   The validator now derives its requirement from the shipped DDL, so this class cannot recur.
2. **`sources` claimed sources the answer never read.** An assistant answer, ranked purely on Arena
   Elo, also claimed SWE-bench, Aider and Epoch. `sources` is a provenance claim; it is now derived
   from the evidence actually used, and an unattributed source raises rather than dropping a CC-BY
   obligation silently.
3. **The Epoch acquisition clock existed twice** — CI checked the committed record while the ingest
   path carried a hardcoded date. Re-acquiring the bundle would have left the data stamped with the
   old date and every gate green.
4. **The picks published the effort POLICY instead of the effort EVIDENCE.** The live `coding`
   answer served a max-effort score with `effort: null` while the same run's CSV export printed
   `effort,max` — two artifacts of one run contradicting each other.
5. **A live registry swallow:** `kimi-k2.5` (73.8) and `kimi-k2.6` (76.7) both folded into
   `kimi-k2`, so `MAX()` published the newer model's score under the older model's name. This is the
   M4-W1 swallow class recurring on a new source, invisible to the rule table's own property tests
   because the live-name corpus had never met these names.
6. Plus: a read-only command that a `?` in the path could turn into a writing one; two bundle
   clients that followed symlinks out of the operator's directory; the budget notice silent in the
   one case that needed it most; a secondary benchmark served without its citation.

## 3. Trust telemetry

- **Fault injections: 22, all RED** after fixes. Two initially stayed green: one because the MUTANT
  was wrong (first-match-wins meant reverting a base rule could not reproduce the swallow), one
  because the citing test drove only one of the two engines. Both are the same lesson in different
  clothes — a green mutant means "your test did not test what you think", and the first question is
  whether the mutant is honest.
- **A tautological test was found and removed.** The W4 "structural guard" against Trap 2 filtered a
  list by a predicate and then asserted that predicate — it could not fail, and it stayed green
  through every gate while the defect it named was live in the payload. **Third instance of this
  class in this project.** A guard that cannot fail is worse than no guard, because it reads like
  coverage.
- Waves producing review findings: 4/4. Findings: 20 in-wave (previous agent) + 20 at closure.
- Control bypasses: 0. Escaped-blocker tripwires: 1 (W4 itself entered closure unreviewed).

## 4. Security & invariants

Stage 4.0: **PASS (conditional)** — `docs/reviews/m5-security-review.md`. 1 BLOCKING (fixed at
closure, §2.4), 7 MINOR (4 fixed, 3 ledgered), 8 NOTE. Conditional on your migration review (§0.2).

gitleaks: 2 findings, **0 secrets** — the same zero-entropy ADR-label false positive at two paths;
M5 introduced neither. pip-audit: **0 vulnerabilities**, no dependency added in M5. No new network
egress: both new clients read a LOCAL unpacked bundle and refuse a URL. Migration probed against six
database shapes: rows preserved, idempotent, atomic, refuses what it cannot repair. No
security-invariant test was weakened — the tests diff is +2400/−22 and the Arena tests each *gained*
an assertion.

## 5. Ledgers

Carried to M6, each with its reason in `docs/warnings.ledger.md`: **W-002** equivalent_plans loses
group structure · **W-005** YAML expansion guard · **W-008** the roster staleness window is borrowed
from the plan table (both 30 today; they will diverge silently) · **W-009** two migration entry
points + a read-time invariant · **W-010** the effort counter under-reports rows it cannot classify.
Still open and yours: **W-001**.

Deferred by the security review to M6: the CSV export half carries no attribution; the
`agentic-coding` answer does not say in the payload that its evidence is undated (the coverage
report does).

## 6. Architecture delta — PROSE

M4 made the plan answers real; M5 made the coding answer possible. The milestone's substance is that
it refused the easy version of its own goal twice. The first refusal was the board choice: the
obvious move was to swap the coding category onto the board with the best coverage, and the
measurement showed that board publishes no evaluation date at all — so the category kept its dated
source and the new board arrived as a SEPARATE category with its own effort policy, leaving D-105
intact and the two numbers un-addable on purpose. The second refusal was freshness: the plan's own
criterion promised the evidence age would drop below sixty days, and the data said the fresher
board's dates are model release dates. Rather than age evidence on a launch date — which would let a
re-released model look freshly measured — the ingestion records that the dates are undated evidence
and the coverage report says so. A criterion written before the data existed was rewritten by the
data, in the open, twice.

Underneath, a score stopped being a (model, harness) pair and became a (model, harness, effort)
triple, which is the schema change this milestone will be remembered for. It arrived with the
uncomfortable discovery that the effort dimension is not evenly published: one board names it
systematically, the other names it for nine rows in twenty-eight, and no single level keeps a board
worth ranking. The product's answer to that — visible in the payload rather than settled by a
default — is to publish the effort each score actually came from and to say out loud when the
answers being compared were not run at the same level. Break-glass for a future maintainer: the
attribution list, the effort fields, and the coverage numbers are all now DERIVED from the rows the
answer used, so adding a source without adding its citation, or a category without an effort policy,
will surface as a raised exception or a printed notice rather than as a quietly wrong claim.

---
*Owner sign-off: **PENDING** — two items in §0.*
