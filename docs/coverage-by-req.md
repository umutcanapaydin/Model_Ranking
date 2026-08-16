---
record_type: register
id: coverage-by-req
status: ratified
date: 2026-08-16
---
# REQ-ID coverage trace — M5 Quality Gate (Stage 4.1)

**Scope:** every acceptance criterion in M5's signed scope, traced to its implementing code and to
the test(s) that would FAIL if the criterion were violated (V3C-02, BLOCKING). Criteria are quoted
from `docs/plans/m5-plan.md` §2 (lines 113-121), and — unlike M4 — they are also present in
`docs/prd.md` §12 (lines 277-316), so the F-1 drift the M4 gate raised did not recur.

**This register replaces the M4 trace.** The full M4 version — its eight criteria, its DEFERRED
disposition for REQ-ING-010 / REQ-ING-011b, the REQ-REC-009 restatement, and the closure-session
addendum that let M4 close — is preserved in git history at the M4 closure commit and is not
reproduced here. Nothing in it is retracted; M5 is the milestone that discharges the two ingestion
criteria it deferred.

**Evidence pinning.** Working tree at `828f623` plus the uncommitted closure fix-set for the M5
security review (10 files: `deepswe.py`, `epoch.py`, `coverage.py`, `rank.py`, `recommend.py`,
`subscribe.py` and their four test files). Test runs 2026-08-16, this gate, on that tree.

---

## 1. Trace table

| REQ-ID | Criterion (one line, from m5-plan.md §2) | Implementing file:line | Citing test(s) file:line | Verdict |
|---|---|---|---|---|
| REQ-ING-010 | Epoch is a first-class source: documented CSV bundle, provenance mandatory, loud-fail per source, own `last_verified` clock, staleness disclosed | `src/app/clients/epoch.py:62` (`EpochClient`), `:108` (`parse_swe_bench_verified`), `:46` (`validate_last_verified`); `src/app/clients/deepswe.py:39`, `:108`; `src/app/workflows/ingest.py:167` `ingest_epoch`, `:194` `ingest_deepswe`; `src/app/workflows/epoch.py:76` (clock CLI); `data/epoch-source.yaml:1`; CI leg `.github/workflows/contract-tests.yml:53` | `tests/unit/test_epoch_ingest.py:35`, `:52`, `:79`, `:93`, `:99`, `:113`, `:121`, `:128`, `:135` (real shape), `:158` (symlink escape); `tests/unit/test_epoch_workflow.py:39`, `:77`, `:120`; `tests/unit/test_deepswe_workflow.py:49`, `:64`, `:115`, `:127`; `tests/unit/test_epoch_staleness.py:19`, `:30`, `:48`, `:62`, `:73` | COVERED |
| REQ-ING-011b | A fresher coding benchmark is INGESTED and freshness is published per curated plan from the row the engine actually selects; four-state partition; source-global dates are telemetry only; release dates are never evidence age | `src/app/workflows/coverage.py:147` `plan_evidence_health` (reuses `subscribe.plan_ranking:132`), `:44` `PLAN_FRESH_DAYS`, `:235` `source_health` (kept separate), `:300` (separate JSON sections); `src/app/clients/deepswe.py:149` `run_date=None` | `tests/unit/test_coverage.py:230` (four states, 59/60 boundary), `:251` (source MAX must not mask a stale selection), `:276`, `:285`; `tests/unit/test_epoch_workflow.py:128` (real board 2/3/0/5); `tests/unit/test_deepswe_workflow.py:74` (release dates stay out), `:161` (real board 0/0/6/4 + CLI JSON) | COVERED — branch (a) and branch (b) both shipped; one narrowness, §2.2 |
| REQ-CAN-005 | Reasoning effort is PARSED and STORED, never swallowed; a row whose effort cannot be determined is counted and disclosed, never defaulted | `src/app/workflows/registry.py:163` `resolve_effort`; `src/app/workflows/schema.py:177` `_migrate_scores_effort`, `:240` `migrate`, `:368` `migrate` CLI, `EFFORT_LEVELS` + 6-column UNIQUE identity; `src/app/workflows/ingest.py:114-118` (domain check), `:44` `effort_unknown`; `src/app/clients/deepswe.py:130-141` (explicit column beats suffix, conflicts counted) | `tests/unit/test_effort.py:27` (suffix family, parametrised), `:38` (`qwen3.7-max` is not an effort), `:45` (precedence + unknown + conflict counts), `:63` (reaches the stored row), `:325` (category effort gates coverage), `:390` (real 50-row board); `tests/unit/test_schema.py:55` (pre-wave DB), `:94`, `:105`, `:249`, `:281`; `tests/unit/test_deepswe_workflow.py:74`, `:161` | COVERED — one under-count ledgered as W-010, §2.4 |
| REQ-REC-011 | The coding answer states which effort level it ranked on and what the model reaches at higher effort, per the owner's Q1 ruling | `src/app/workflows/categories.py:73` (`agentic-coding` `ranking_effort="high"` — DATA); `src/app/workflows/rank.py:117` `higher_effort_evidence` (same harness + same source only); `src/app/workflows/recommend.py:158` `effort_disclosure`, `:203` (model `_pick`); `src/app/workflows/subscribe.py:309` (plan `_pick`) | `tests/unit/test_effort.py:245` (model CLI), `:272` (subscription CLI), `:303` (D-109 boundary), `:401` (evidence effort, not policy — both engines) | **PARTIAL — see §2.1. COVERED for `agentic-coding`; NOT COVERED for the `coding` category, which ranks across mixed effort levels and discloses no higher-effort reach.** |
| REQ-SUB-007 | Coding plan coverage is re-measured through the real engine before and after, and the delta is published as a number in the closure report | `src/app/workflows/board_measurement.py:587` `main`, `:379-397` (`coverage.scoreable_plans` cross-checked against `plan_ranking`), `validate_baseline_snapshot`; `data/m5-swebench-baseline.json`; `src/app/workflows/coverage.py:103` `plan_coverage` | `tests/unit/test_m5_board_measurement.py:43` (before 1/10 + five candidates through the real registry/coverage/ranking), `:127` (baseline is complete and provenance-pinned, rejects truncation and content drift), `:163` (real CLI, D-109 once); `tests/unit/test_deepswe_workflow.py:161` (after: coding 5/10, agentic 6/10, union 6/10) | COVERED — with one closure obligation outstanding, §2.3 |
| REQ-LIC-001 | Epoch's CC-BY attribution ships where the data is served: the citation string in the recommendation payload's source list AND in the README | `src/app/clients/epoch.py:36` `EPOCH_ATTRIBUTION` (one constant, one spelling); `src/app/workflows/rank.py:48` `SOURCE_ATTRIBUTION`, `:76` `attributions_for` (raises on an unattributed source), `:303` (export); `src/app/workflows/recommend.py:339`; `src/app/workflows/subscribe.py:528`; `README.md:90` | `tests/unit/test_recommend.py:111` (payload + README, verbatim not paraphrase), `:141` (mirror: never claim a source not read), `:396` (secondary sources cited too); `tests/unit/test_categories.py:156` (export attribution is derived, not stamped); `tests/unit/test_deepswe_workflow.py:287` (real bundle, subscription CLI); `tests/integration/test_cli_e2e.py:114` (negative, through the real CLI) | COVERED |
| REQ-REC-012 | The Gemini contradiction is resolved or DISCLOSED; silently picking one number is a milestone failure | `src/app/workflows/board_measurement.py:150` `GeminiContradiction`, `:523`/`:532` (non-finite and missing-provenance refusals), `:545` (verdict string), `:581` (D-109 at the JSON boundary); `src/app/workflows/categories.py:62` (the two numbers are carried on two categories, never averaged); `docs/reviews/m5-w1-board-measurement.md:74-90` | `tests/unit/test_m5_board_measurement.py:94` (both rows, both harnesses, ratio, log id/URL, verdict `unresolved`, and the same artifacts asserted present in the decision record); `:163` (both numbers survive to the real CLI at one decimal) | COVERED |
| REQ-REC-013 / D-111 | Budget disclosure: `excluded_by_budget` counts scoreable plans removed by the price cap, narrated separately from unscored and equivalent plans (added by W4 beyond the signed plan) | `src/app/workflows/subscribe.py:321` `_budget_notice`, `:329` `BudgetShutout` (the all-excluded case), payload fields `excluded_by_budget` / `budget_notice`; `docs/decisions.md:457` D-111 | `tests/unit/test_subscribe.py:162` (six scoreable, five priced out, and the unlimited-budget negative), `:595` (budget that prices out EVERYTHING still says how many — through the real CLI); `tests/unit/test_deepswe_workflow.py:282` (real bundle, five excluded) | COVERED — D-111 is `proposed`, §2.5 |

---

## 2. Dispositions for everything not plainly COVERED

### 2.1 REQ-REC-011 — PARTIAL, and this is the gate's blocking finding

The criterion, in the signed plan's words: *"The coding answer states which effort level it ranked
on and what the model reaches at higher effort ... per the owner's Q1 ruling."* Q1 is *"rank on ONE
named effort level and disclose the range."*

The `agentic-coding` category does exactly this. `categories.py:73` sets `ranking_effort="high"` as
DATA, `rank.py:117` supplies the higher-effort comparable from the SAME harness and the SAME source,
and both live CLIs are pinned by `tests/unit/test_effort.py:245` and `:272`. Mutant M5 below proves
those tests fail if the range half is removed.

The `coding` category does not. `categories.py:32` leaves `ranking_effort` unset, so
`rank.category_ranking` keeps the `MAX(score)` selection across every effort level the board carries.
Reproduced this gate through the shipped subscription engine on the owner's real Epoch bundle:

| Label | Plan | Model | Score | Effort of the selected row | Higher-effort reach disclosed |
|---|---|---|---:|---|---|
| best_quality | Perplexity Pro | GLM-5.2 | 78.7 | `max` | none |
| best_value | Google AI Plus | Gemini 3.1 Pro | 75.6 | `unspecified` | none |
| budget_pick | Google AI Plus | Gemini 3.1 Pro | 75.6 | `unspecified` | none |

The stored Epoch effort distribution behind that answer is `high 4 / max 3 / medium 1 / xhigh 1 /
unspecified 24`. So a `max`-effort run is ranked above an `unspecified`-effort run and wins the
headline pick. That is Trap 2 of the signed plan in the shape the plan describes it — *"advertising a
performance level the buyer's plan may not even offer"* — surviving into the milestone's namesake
category. What the closure fix-set added is a disclosure, not a policy: the winning pick now carries
a sentence which translates as *"This category does not compare at a fixed effort level; this score
comes from a run at max effort."* The two `unspecified` picks carry `effort_note: null` and say
nothing at all.

**Why this is PARTIAL and not COVERED.** No test asserts that the coding answer names a ranked effort
level, and no test anywhere asserts a higher-effort reach on the coding surface: `grep -rn
higher_effort tests/` returns hits only in `tests/unit/test_effort.py`, and every one of them
exercises `agentic-coding`. The half of the criterion that is unimplemented is, necessarily, the half
with no citing test. Under V3C-02 that does not close on agent authority.

**This was seen before this gate and not carried.** The M5 security review's owner checklist, item 1,
second sentence, says: *"Separately decide whether `coding` should acquire a `ranking_effort`, which
is a one-field data edit to `categories.py` and is the only thing that makes the cross-model
comparison satisfy the Q1 ruling."* The closure disposition table records BLOCKING-1 as FIXED and is
silent on that second sentence. The fix that landed was the disclosure; the policy decision was not
taken.

**To clear (owner, at the milestone gate), either:**
1. **Set the policy.** Give `coding` a `ranking_effort` in `categories.py` (a DATA edit) and add the
   citing test that the coding answer names its ranked level and its higher-effort reach. Note the
   measured consequence before choosing: 24 of 33 Epoch rows are `unspecified`, so a strict level
   would drop most of the board — probe M11 below shows 57 existing tests move when the field is set,
   because the whole fixture corpus assumes no effort policy on `coding`. This is a real design
   choice, not a one-line patch, which is why it belongs to the owner.
2. **Or restate the criterion.** Ratify, as an ADR plus amended `docs/prd.md` text, that Q1's
   single-level ranking is discharged by the `agentic-coding` surface and that `coding` ranks
   best-available-effort with per-pick effort disclosure — and then land the citing test for THAT
   rule (today the `unspecified` branch is silent, so even the restated rule would need the note
   extended to every pick).

Either path is cheap. Neither is an agent's to take: the M4 gate blocked on precisely this shape
(REQ-REC-009 retired on agent authority) and the lesson is in the register above.

### 2.2 REQ-ING-011b — COVERED, both branches, with one narrowness recorded

The criterion forks and the shipped code took **both** branches, because the signed board decision
put one board on each side of the fork:

- **Branch (a) — a real evaluation date that drops the age below 60 days.** Epoch SWE-bench Verified
  carries a genuine `Started at` column. Perplexity Pro and Perplexity Max select GLM-5.2's
  2026-06-25 row: 52 days old on 2026-08-16, therefore `fresh`. The three Google plans select Gemini
  3.1 Pro's 2026-02-24 row: 173 days, therefore `stale`. Five plans are `unscored`. The published
  distribution is **2 fresh / 3 stale / 0 undated / 5 unscored** — the plan's measured target, not
  the "5/10 fresh" the criterion explicitly forbids. Citing test
  `tests/unit/test_epoch_workflow.py:128`, through the real engine on the real bundle.
- **Branch (b) — a release-date-only board must refuse to age on it and say the evidence is
  undated.** DeepSWE has only `Release date`. `deepswe.py:149` hard-codes `run_date=None` with the
  reason written at `:113-114`; every one of the 49 stored rows has a NULL `run_date`. The
  `agentic-coding` partition publishes **0 fresh / 0 stale / 6 undated / 4 unscored**, and source
  telemetry reports `newest_run_date: null, age_days: null, stale: true` — failing toward disclosure,
  not toward freshness. Citing tests `tests/unit/test_deepswe_workflow.py:74` and `:161`.

The **"must SAY so" half is delivered in the coverage report** — `status: "undated"` with
`evidence_date: null` and `age_days: null`, per plan, per category, printed by the `coverage` CLI
that CI runs. It is **not** delivered in the recommendation payload: the `agentic-coding` answer
returns `stale_notice: null` and three picks with `evidence_date: null` and no sentence naming the
board as undated. The M5 security review raised this as MINOR-5 and the closure disposition ledgered
it to M6 on the reasoning that *"the coverage report already carries the fact, and REQ-ING-011b's
branch (b) is satisfied at the source level."*

**This gate agrees with that verdict, narrowly.** The criterion's own text asks for freshness
*"published per curated plan from the evidence row the engine actually selects"* and defines the
four states — it never names the recommendation payload as the surface. Nothing false is stated
anywhere: no release date has become an evaluation date, which mutant M1 below independently
confirms. But the gap is real and is the same shape as M4's MINOR-2 (a control that is measured but
that the user never sees), so it is recorded here rather than left in a review appendix:
**proposed INV-24 — unknown evidence age is disclosed in the answer, not only in the report** — with
M6 as its owning milestone.

### 2.3 REQ-SUB-007 — COVERED, with one closure obligation outstanding

The measurement half is complete, runs through the real engine, and is defended by a
provenance-pinned before-snapshot that rejects truncation, commit drift and row-content drift
(`tests/unit/test_m5_board_measurement.py:127`). The published delta:

| Surface | Before | After | Delta |
|---|---:|---:|---:|
| `coding` (Epoch replaces the 180-row swebench.com extract) | 1/10 | 5/10 | +4 plans |
| `agentic-coding` (new, DeepSWE at `high`) | 0/10 | 6/10 | +6 plans |
| Unique plans covered by either coding surface | 1/10 | 6/10 | +5 plans |

The two numerators must not be added; the categories overlap on five plans and DeepSWE's single
unique addition is ChatGPT Pro.

**Outstanding:** the criterion says the delta is *"published as a number in the closure report"*, and
`docs/closure-report-m5.md` does not exist yet — it is Stage 4.2/4.3 work. This is the same
unfinished-step disposition the M4 gate recorded for REQ-SUB-005, listed here so it cannot be
forgotten. Not a gate failure; the numbers to carry are the three rows above.

### 2.4 REQ-CAN-005 — COVERED, with a counted under-count already ledgered

Effort is a first-class column with a migration, a six-value domain enforced by the schema, a
resolver with documented explicit-over-suffix precedence, and counters for unknown and conflicting
rows. Mutants M4 and M9 below prove the storage and the coverage predicate are both defended.

The narrowness, found by the closure live-data probe and ledgered as **W-010** (owning milestone M6):
`resolve_effort` infers a suffix effort only when the base name canonicalizes to the same model as
the full name — which is correct, and is exactly why `qwen3.7-max` is not read as an effort. The
consequence is that a row whose model has no registry rule loses its effort too. Four live Epoch rows
carrying a literal `_high` / `_medium` suffix were stored as `unspecified` while the ingest reported
`effort_unknown=0`. The criterion says an undeterminable effort is counted, so the counter
under-reports. No shipped answer is affected — those rows are also registry-dropped and never reach a
ranking — and the row is open with the remedy named, so the verdict stays COVERED.

### 2.5 REQ-REC-013 / D-111 — COVERED as a criterion; the ADR is still `proposed`

This criterion is not in the signed plan §2. It was added in W4 to discharge ledger row **W-006**
(the `dusuk` budget returns one plan under three labels and never says how many plans the cap priced
out). It is properly constituted: a REQ-ID in `docs/prd.md` §12, an ADR at `docs/decisions.md:457`
(D-111), an implementation with a single writer, and three citing tests including the all-excluded
case through the real CLI — which the W4 review found unfixed at its sharpest point while the ledger
already read FIXED. Mutant M7 kills all three.

D-111's status is `proposed`, so the CONTRACT is pending owner ratification even though the behaviour
is covered. That is the correct state for a criterion the owner has not signed; it is on the gate
agenda, not a defect.

### 2.6 Vacuous-test audit (the failure mode this project has now paid for three times)

The gate looked specifically for assertions that are true by construction. One was found and is
already fixed; two decorative-but-harmless lines are recorded so nobody mistakes them for coverage.

- **FIXED before this gate — the W4 "structural guard" against Trap 2.**
  `test_no_effort_free_category_can_see_more_than_one_effort_level` filtered
  `[spec for spec in CATEGORIES.values() if spec.ranking_effort is None]` and then asserted
  `spec.ranking_effort is None` on the result — the predicate it had just filtered on. It also
  asserted that SQLite ACCEPTS two clashing rows, which the test's own comment conceded. It passed
  unconditionally, and it passed for the entire time BLOCKING-1 was live in the shipped payload. The
  M5 security review caught it as MINOR-7; the closure fix-set replaced it with
  `tests/unit/test_effort.py:401`, which drives both real engines and fails on the real defect. Its
  docstring now records the tautology in place — the right thing to do with a burn of this class.
  This is the third instance of the pattern in this project's history and the second caught by a
  fresh-eyes review rather than by a gate.
- **Decorative, not load-bearing:** `tests/unit/test_coverage.py:234` `assert PLAN_FRESH_DAYS == 60`
  and the `sum(...) == 4` partition line in the same test are guaranteed by construction (the
  dataclass is built from the same counter dict, and `plan_evidence_health` already raises on a
  non-partition). They are harmless because the same test also asserts the exact 1/1/1/1 distribution
  and the per-plan statuses at ages 59 and 60, which mutants M2 and M3 kill.
- **Legitimate fixture precondition:** `tests/unit/test_effort.py:419`
  `assert spec.ranking_effort is None, "fixture assumes an effort-free category"` is the same SHAPE
  as the tautology above, but here it guards a fixture assumption and the test then asserts real
  behaviour (`pick.effort == "max"` on both engines). Kept, flagged, not counted as coverage.

No other assertion in the M5 test surface was found to be true by construction.

---

## 3. Independent verification — mutants run by this gate

Every mutant below was applied **in place** to the working tree, exercised with the owner's real
Epoch bundle mounted (`EPOCH_DATA_DIR`), then restored from a byte copy and verified md5-identical.
No git command was used to restore anything. Bytecode caches were cleared around every probe (the M4
gate's recorded tooling incident). Ten mutants: nine kills, one probe.

| # | Criterion | Mutation | Result |
|---|---|---|---|
| M1 | REQ-ING-011b (b) | `deepswe.py` maps `Release date` into `run_date` — the exact "a re-released model looks freshly measured" defect | **RED** — 4 tests: `test_ingest_publishes_effort_accounting_and_keeps_release_dates_out`, `test_real_board_reproduces_signed_coverage_and_undated_health`, `test_explicit_effort_wins_suffix_conflict_and_unknown_is_visible`, `test_real_deepswe_shape_has_one_disclosed_unknown_effort` |
| M2 | REQ-ING-011b | freshness window widened by one day (`age < window` to `age <= window`) | **RED** — `test_plan_evidence_health_partitions_every_plan_once`, `test_plan_evidence_health_uses_selected_row_not_source_max` |
| M3 | REQ-ING-011b | an undated selected row falls back to the source-global `MAX(run_date)` and reports `fresh` — the precise defect the criterion forbids | **RED** — `test_plan_evidence_health_partitions_every_plan_once`, `test_real_board_reproduces_signed_coverage_and_undated_health` |
| M4 | REQ-CAN-005 | the resolved suffix effort is dropped at the storage boundary (suffix swallowed into the base row) | **RED** — `test_suffix_effort_is_stored_through_existing_ingest_entrypoint`, `test_real_board_reproduces_signed_coverage_and_undated_health` |
| M5 | REQ-REC-011 | the higher-effort range half of `effort_disclosure` removed | **RED** — `test_live_recommendation_ranks_high_and_discloses_higher_effort`, `test_live_subscription_answer_carries_the_same_effort_contract` (both engines) |
| M6 | REQ-LIC-001 | Epoch's prescribed citation replaced by a paraphrase | **RED** — `test_req_lic_001_epoch_citation_ships_where_epoch_data_is_served` (payload AND README halves) |
| M7 | REQ-REC-013 | the priced-out sentence silenced | **RED** — `test_budget_notice_counts_only_scoreable_plans_excluded_by_price`, `test_budget_that_prices_out_everything_still_says_how_many`, `test_real_board_reproduces_signed_coverage_and_undated_health` |
| M8 | REQ-ING-010 | the DeepSWE acquisition clock made optional (defaulted instead of demanded) | **RED** — `test_workflow_requires_and_validates_the_independent_verification_clock` |
| M9 | REQ-CAN-005 | the category effort predicate in `plan_coverage` neutered, so max-only evidence makes a `high`-policy plan scoreable | **RED** — `test_coverage_entrypoint_requires_the_category_effort` |
| M10 | REQ-REC-012 | the Gemini verdict flipped to "resolved; customtools explains the gap" | **RED** — `test_gemini_contradiction_is_preserved_in_the_decision_record` |
| M11 | REQ-REC-011 (probe, not a kill) | `coding` given `ranking_effort="max"` | 57 tests move — but from **fixture coupling**, not from a criterion assertion: the fixture corpus stores `unspecified` scores, so any effort policy makes them unscoreable. This does NOT constitute a citing test for the coding half of REQ-REC-011; it is the evidence that the coding effort policy is unpinned in both directions. See §2.1. |

Restore integrity: every mutated file's md5 before and after is identical, verified per probe.

---

## 4. Reverse direction — code without a criterion

Every module M5 touched traces to a criterion: `clients/epoch.py`, `clients/deepswe.py`,
`workflows/epoch.py` and the `ingest_epoch` / `ingest_deepswe` loaders to REQ-ING-010;
`coverage.plan_evidence_health` to REQ-ING-011b; `registry.resolve_effort`, the `scores.effort`
column and its migration to REQ-CAN-005; `rank.higher_effort_evidence` and `recommend.effort_disclosure`
to REQ-REC-011; `workflows/board_measurement.py` to REQ-SUB-007 and REQ-REC-012;
`rank.attributions_for` to REQ-LIC-001; `subscribe._budget_notice` and `BudgetShutout` to
REQ-REC-013. **No orphan M5 code was found.** Two observations:

- **The M4 gate's F-1 did not recur.** All seven signed criteria plus REQ-REC-013 are indexed in
  `docs/prd.md` §12 with their citing test files and an explicit "pending M5 owner gate" status.
- **`rank.export_ranking` still has no production caller** (grep across `src/`, `scripts/`,
  `Makefile`, `.github/`). It is exercised only by tests. That is pre-existing, it is what keeps the
  security review's MINOR-2 (no attribution on the CSV half of the export) at MINOR, and it is
  ledgered to M6 with the export contract.

---

## 5. Wave-close and review status

All four wave checklists are filled and every row is ✅ or an explicitly reasoned WAIVED (row 9c in
W1/W2/W3: "no auth, tenancy, or money invariant changed"). What this gate carries forward:

| Wave | Item | Kind | Disposition |
|---|---|---|---|
| W1-W4 | Five opt-in network contract tests skipped in every local run | SKIPPED (standing rule) | Unchanged since M1; run in CI / on the owner's machine |
| W1-W4 | Seven `EPOCH_DATA_DIR`-gated tests skipped unless the owner's bundle is mounted | SKIPPED (by design) | **Material to this gate:** these seven include the strongest citing evidence for REQ-ING-011b, REQ-SUB-007, REQ-REC-012 and half of REQ-CAN-005. They are green here because the gate mounted the bundle; they are NOT green in CI, because the bundle is not in CI. Recorded, not waived — see §7 |
| W1-W3 | Mechanical mutation runner not wired (HIGH advisory) | SKIPPED | Manual fault injection ran instead, in every wave and again at this gate |
| W4 | The wave shipped as an unreviewed checkpoint and was closed by a second agent | Escaped-blocker tripwire FIRED | Three BLOCKING defects were sitting in it, all fixed before close. K.7 satisfied structurally |
| W4 | A live registry swallow (`kimi-k2.5` / `kimi-k2.6` both folding into `kimi-k2`) found while closing, not by the review | Live-data defect, fixed | Lesson recorded: a new SOURCE is a new corpus |
| Closure | M5 security review: 1 BLOCKING, 7 MINOR, 8 NOTE | Fixed / ledgered | BLOCKING-1 and four MINOR fixed in the closure fix-set with mutants; three MINOR ledgered to M6; one MINOR accepted with the reason written down. Verdict after disposition: PASS, conditional on the OWNER's own migration review (permission-matrix §11) — condition DISCHARGED at the 2026-08-16 gate, so the PASS is unconditional |
| — | `scripts/` fails repo-wide ruff/black; the gate is scoped to `src tests` | Pre-existing | GP-upstream note, unchanged across three milestones |

**Warnings ledger.** Ten rows. W-003, W-004, W-006, W-007 are **FIXED** in W4 with citing tests.
W-002, W-005, W-008, W-009, W-010 are **ACCEPTED** with owning milestone **M6** and a written reason
each. **W-001** (gitleaks `generic-api-key`, an ADR compliance label in English prose) is still
**ESCALATED** and has now survived M3, M4 and M5. The M5 security review additionally found the rule
firing at **two** paths while the ledger row names one; the second occurrence entered at the M4
closure commit, so M5 introduced no new finding. Not waived, not baselined, not suppressed — agents
may not. Owner action: land the scoped `.gitleaks.toml` allowlist, or extend and re-stamp the row.

---

## 6. Test and coverage evidence

`make check` on this tree, 2026-08-16 — **green, exit 0**, all gates:

| Gate | Result |
|---|---|
| `ruff check src tests` | All checks passed |
| `mypy src` | Success: no issues found in 27 source files |
| `pytest` | **270 passed, 12 skipped**, 131 warnings, 7.40s |
| `check-records` | PASS, no findings (7 records with frontmatter) |
| `check-records-selftest` | PASS, 0 problems (every rule probe fires) |
| `install-check` | PASS |
| `pin-check` | PASS, all workflow actions SHA-pinned |

Coverage on that run: **84%** (2312 statements, 329 missed; 556 branches, 73 partial).

With the owner's Epoch bundle mounted, the seven gated contract tests also run:
**277 passed, 5 skipped** (the 5 being the network contract tests), coverage **90%**. Both figures
are reported because the difference between them is exactly the evidence CI cannot see.

| Module | Cover (bundle mounted) | Module | Cover (bundle mounted) |
|---|---|---|---|
| `workflows/registry.py` | 98% | `workflows/coverage.py` | 94% |
| `workflows/subscribe.py` | 96% | `workflows/recommend.py` | 95% |
| `workflows/ingest.py` | 95% | `workflows/rank.py` | 94% |
| `workflows/schema.py` | 92% | `workflows/categories.py` | 100% |
| `clients/epoch.py` / `clients/deepswe.py` | high, negative paths covered | `workflows/board_measurement.py` | 41% without the bundle |

`board_measurement.py` is the one module whose coverage collapses without the bundle (41%); it is a
measurement producer, not a serving path, and its uncovered lines are the five per-board adapters.

---

## 7. Verdict

Seven of the eight criteria traced are COVERED by tests this gate independently showed able to fail.
Ten mutants were injected in place and killed by named tests; every file was restored md5-identical
without git. The two ingestion criteria M4 deferred are genuinely discharged: Epoch is a first-class
source with its own clock and loud per-source failure, and REQ-ING-011b's fork is satisfied on both
sides — real evaluation dates ageing to 2 fresh / 3 stale / 5 unscored on `coding`, and a
release-date-only board that refuses to age and reports 6 undated on `agentic-coding`. The
tautological guard the M5 security review found was replaced before this gate with a test that fails
on the real defect, and the pattern is recorded in place so the fourth instance is harder.

One criterion did not close at the time this register was written. It closed at the gate itself.

**VERDICT AFTER THE OWNER'S RULING (2026-08-16): PASS.** The owner ratified **D-112**, which settles
what REQ-REC-011 means for a category with no effort policy: `coding` keeps its board and DISCLOSES
the inequality rather than equalising it by shrinking. The citing tests for that rule are
`tests/unit/test_effort.py:401` (`test_pick_publishes_the_effort_of_its_evidence_not_the_category_policy`)
and `tests/unit/test_effort.py:493` (`test_comparison_across_unequal_effort_is_disclosed`), both
present and both shown able to fail by mutants at this gate. **D-111** was ratified in the same
session, discharging item 1 below; the owner's migration review discharged item 4. The original
BLOCKING verdict is preserved verbatim below, because the register's value is that it recorded the
block before it was resolved, not after.

**ORIGINAL VERDICT (pre-ruling): BLOCKING** — on **REQ-REC-011** alone. The `coding` category, the milestone's namesake,
does not rank on one named effort level and discloses no higher-effort reach; on the owner's live
bundle it ranks a `max`-effort run above an `unspecified`-effort run and the two losing picks say
nothing about effort at all. That is Trap 2 of the signed plan reaching the shipped answer, and the
half of the criterion that is unimplemented has, necessarily, no citing test. The remedy is an
owner decision, not an agent's: either set `coding.ranking_effort` in DATA and land the citing test,
or ratify the restatement that Q1 is discharged by the `agentic-coding` surface and land the citing
test for that rule instead. §2.1 states both paths and the measured cost of each.

Also on the owner's gate agenda, none of them blocking this register:

1. **D-111** is `proposed`; REQ-REC-013 is a criterion the owner has not signed.
2. **`docs/closure-report-m5.md`** must carry the REQ-SUB-007 before/after numbers (§2.3).
3. **W-001** has survived a third close and now fires at two paths against a one-path ledger row.
4. **The owner's own review of the migration path** (`schema.py:368-408` and `_migrate_scores_effort`)
   — permission-matrix §11 requires a human for a migration and no agent's pass substitutes.
5. **Proposed INV-24** — unknown evidence age belongs in the answer, not only in the report (§2.2).

No code change is required to clear item 1 through 5. Item 0 — REQ-REC-011 — requires either one
data edit plus one test, or one ADR plus one test.
