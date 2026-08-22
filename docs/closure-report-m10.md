---
record_type: ratification
id: closure-report-m10
status: draft
date: 2026-08-22
---
# Closure Report — M10: The app answers a question asked in the reader's own words

> **AWAITING THE OWNER'S SIGNATURE.** Section 0 is what needs him. Everything below it was
> measured at the closing tree rather than reported by the thing that produced it.

## 0. What needs the owner

1. **Run `./runner` and make the milestone commit.** Same as every milestone: the agent does not
   commit (AGENTS.md §3, local lane). `./runner` writes to
   `/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/runner/`.
2. **The iOS app has never been opened.** Every claim about the router below is from a unit test
   and a calibration probe against real hint text — **not from a phone or a Simulator**. The
   router's own record (`docs/reviews/m10-router-calibration.md`) says it scored 7 of 8 on the
   probe. Nobody has typed a question into the field.
3. **K.7 has now been bypassed four times** and the telemetry that exists to catch exactly this
   fired at M8 and was never consumed (W-055, ESCALATED). Either a single-agent session gets an
   environment where a second reviewing seat exists, or the rule is amended to describe what
   actually happens. This is a gate-definition change and therefore yours.
4. **The schedule is still not loaded, and D-123 is undischarged for a third milestone.** Nothing
   is on Fly.io; nothing bills. W-054 records that every security verdict in this milestone
   describes code rather than operation until the refresh runs unattended.

## 1. What shipped (from the signed plan)

| REQ-ID | Criterion | Citing test (able to fail) |
|---|---|---|
| REQ-RTR-001 | A question in the reader's own words opens the right surface | `tests/unit/test_router_hints.py`; `docs/reviews/m10-router-calibration.md` |
| REQ-RTR-002 | The router can only ever yield one of the nine ids | `ios/ModelRanking/Engine/Router.swift:209,227` — schema-constrained AND re-checked against `known` |
| REQ-RTR-003 | The router is never required | `Router.swift:247-260` — three tiers, manual fallback, no path where absence blocks the screen |
| REQ-RTR-004 | Nothing typed reaches the engine; nothing served is influenced by it | `ContentView.swift:261-279`, `EngineClient.swift:144-145` — `task` and `budget` go out, nothing else |
| REQ-RTR-005 | An unmeasured question routes to `assistant` and SAYS so | `Router.swift:169-171` — `unmeasured: true` reaches the surface as disclosure |
| REQ-GRD-001 | A refresh refuses evidence that moved upward implausibly | `tests/unit/test_refresh.py` — `upward_anomalies()`; D-132 |
| REQ-GRD-002 | Bounded aggregate allocation from an upstream | `tests/unit/test_arena_client.py` — `_MAX_MERGED_ROWS = 2_000` |
| REQ-GRD-003 | Environment assumptions are CHECKS | `tests/unit/test_refresh.py` — `environment_problems`, NaN-safe `write_status` |
| REQ-EVI-002 | The ranked population is named AND calibration calls it | `tests/unit/test_ranked_population.py` — five tests including the V4C-49 gate |

## 1a. Per-wave table

| Wave | Risk | Delivered | Record |
|---|---|---|---|
| W1 | HIGH | The three-tier router; two implementations measured and rejected before the third | `docs/plans/m10-wave-1-close.md`, `docs/reviews/m10-router-calibration.md` |
| W2 | HIGH | The upward-anomaly axis, with ordinary movement measured BEFORE the thresholds were written | `docs/plans/m10-wave-2-close.md`, `docs/decisions.md` D-132 |
| W3 | MED | Row bound, environment checks, the named ranked population and its gate | `docs/plans/m10-wave-3-close.md` |
| W4 | LOW | Stage 4.0 (returned BLOCKING), the one read-only definition, closure | `docs/plans/m10-wave-4-close.md`, `docs/reviews/m10-security-review.md` |

## 1b. Decisions made on your behalf

- **The router's hints were sharpened rather than its code changed** when the probe scored 5 of 8.
  Recorded because it is the cheaper fix and the one that could have been mistaken for tuning
  toward the test: the hint text describes the surfaces, and the probe questions were not edited.
- **`_MAX_MERGED_ROWS` is 2,000, not 5,000.** 5,000 is exactly `_MAX_PAGES * _PAGE` and therefore
  unreachable. Choosing a number that fires is a judgment call and is recorded as one.
- **The read-only construction moved to `app.workflows.schema`** rather than being duplicated or
  imported from the adapter. This resolves a collision between D-116's boundary rule and the
  single-definition rule in favour of moving the definition.
- **The page cap is kept even though it is now unreachable in normal operation.** Its test raises
  the row bound to reach it and says why, rather than being deleted or made to look live.

## 2. Git record

`97e77a0..HEAD` — 3 commits at agent hand-off plus this uncommitted closing tree.
**16 files changed, 1298 insertions(+), 144 deletions(-).** The owner makes the closing commit.

## 3. Trust telemetry

- Tests: **474 (M7 close) → 638 (M9 close) → 666 (M10 close).** 12 skipped, unchanged.
- Governed records: 38 (M7) → 48 (M10). `wave-check-all` validates 17 v5.0 records.
- Gates in `make check`: lint, typecheck, test, coverage-floor, check-records,
  check-records-selftest, install-check, wave-check-all, conformance-gate — **exit 0**.
- Fault injection this milestone: **12 mutants across W3 and W4, 12 killed.**
- **Control bypasses: K.7, fourth occurrence** (W-055). `C2b` fired at M8 and its follow-up did not
  happen.

## 4. Security & invariants

Stage 4.0 returned **BLOCKING**: `docs/reviews/m10-security-review.md`.

One blocking finding, **W-052**: `f"file:{path}?mode=ro"` returns a WRITABLE connection for four
measured path shapes, on the path where the refresh reads the LIVE artifact. Fixed by making
`app.workflows.schema.open_readonly` the single definition, with an `ast` gate that refuses the
string form anywhere in `src/` or `scripts/`.

**Invariants held:** D-104 (no LLM in the scoring path — the router is in front of the catalogue,
proven by REQ-RTR-004), D-105, D-109, D-115/D-125 (`/v1` frozen, not moved), D-116 (no adapter
import in the refresh — preserved by moving the definition to a workflows module), D-118, D-120,
D-128, D-129, D-130, INV-23.

## 5. Ledgers

**Closed this milestone:** W-037, W-050, W-051, W-052.
**Opened:** W-053 (MINOR, M11), W-054 (nothing has run unattended, M11), W-055 (**ESCALATED** —
K.7 bypass count, owner decision).
**Still carried:** W-030, W-031 (need a deploy), W-035, W-036, W-038, W-039, W-044.
**Not this project's:** GPF-001..006, handed back to General_Pipeline.

## 6. Architecture delta — prose

Before M10 the app asked its reader to choose one of nine surfaces from a list. That is a fair
interface for someone who already knows the vocabulary and a dead end for everyone else, because
the reader who most needs a recommendation is the one least able to name the category it belongs
to. M10 puts a router in front of the list: the reader types a question, and the app picks the
surface.

The architectural claim worth stating precisely is **where that router is not**. It is not in the
scoring path. It selects WHICH of nine questions the engine is asked; the engine's answer to that
question — the ordering, the thresholds, the picks, the disclosures — is byte-for-byte what it was
before the router existed, and D-104 stays true rather than becoming true-in-spirit. The proof is
mechanical rather than argued: the typed text never crosses the network boundary at all, and the
only thing the router contributes to a request is one of nine ids that the client re-validates
after the model has produced it.

It runs in three tiers, and the tiering is the honest part. `FoundationModels` gives a constrained
generation on iOS 26 and above; `NLContextualEmbedding` gives centred cosine similarity on
essentially every device the app supports; and below both there is the list the reader already
had. Nothing about the screen depends on a tier being available, which is what makes the feature
shippable on a target of iOS 18 when its best implementation needs 26.

The second delta is smaller and older. The refresh gained an upward-anomaly axis — until M10 it
could only refuse evidence that got worse, so a source that suddenly rated everything far higher
would publish silently. It also gained bounds on what an upstream can make it allocate, and checks
where it previously held assumptions about its own environment. And a construction that opens the
artifact read-only, which had been correct in one module since M6 and wrong in another since M9,
is now correct in one place with a gate that keeps it there.

## 7. The carried question, for M11

M10 shipped a feature whose best tier exists on hardware nobody has tested it on, behind an
interface nobody has opened. Every verdict in this report is about code.

**So: what is the smallest thing that would count as this product having been USED?** Not deployed,
not scheduled, not green — used. Answer it in the abstract before M11 plans anything, because
three milestones have now closed with `D-123` undischarged and each of them had a good local
reason.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Range: `97e77a0..HEAD`
