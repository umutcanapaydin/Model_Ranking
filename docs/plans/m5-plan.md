# M5 Plan — Rescue the Coding Category (data depth, phase 2)

**Status:** **SIGNED** by the owner on 2026-08-16; factual and REQ-ING-011b meaning amendments
approved by owner choices 1 on 2026-08-16. Wave dispatch is authorized.
**Date:** 2026-08-15 · **Risk tier:** LOW-MED · **Mode:** A0.5 + D-106
**Process baseline:** GP v4.3.1 (D-108). Waves run without stopping (owner amendment, M3); the owner
runs the out-of-sandbox verification at the milestone gate. On 2026-08-16 the owner delegated the
remaining inter-wave decisions so the milestone can run unattended; the owner and agent test
together only at the milestone gate.

**Owner decisions locked 2026-08-15 (this session):**
- **Scope:** rescue the coding category with the Epoch data. NOT the HTTP API — that moves to M6,
  with Fly.io still the recorded deploy target.
- **Q1 effort policy: rank on ONE named effort level and disclose the range.** Effort is stored as
  data; comparisons happen at a single level so they stay fair; the output says what the model
  reaches at higher effort instead of hiding it.
- **Q2 primary benchmark: RESOLVED after measurement under delegated owner authority.** Keep Epoch
  SWE-bench Verified as the existing `coding` category's primary evidence and add DeepSWE at the
  single `high` effort level as a separate `agentic-coding` category/evidence surface. W1 produced
  the evidence before this choice. (Directly applying M4's retrospective lesson: a criterion that
  contains a number about live data gets a measurement task in the wave *before* it.)
- **2026-08-16 amendment:** the owner chose to correct the plan's Epoch freshness facts while
  retaining Q2's measure-first decision gate. The amendment does not pre-select the primary board.
- **2026-08-16 freshness ruling:** freshness is judged on the evidence row the engine actually
  selects for each plan, not the newest row anywhere in a source. Publish fresh / stale / undated /
  unscored plan counts together; a source-global `MAX(run_date)` cannot close REQ-ING-011b alone.
- **2026-08-16 unattended-wave ruling:** the owner instructed the agent not to ask questions between
  waves and delegated the pending board choice. The agent selected the W1 record's recommended
  option: Epoch primary plus a separate DeepSWE-high `agentic-coding` surface. This does not waive
  the milestone-end joint verification or any security/destructive permission boundary.

---

## 0. Why this milestone exists (the finding it answers)

M4 shipped the honest answer and then measured why it is thin: **the coding category can rank 1 of
10 curated plans.** Not because the linking is broken — M4 fixed that — but because the benchmark
behind the category stopped publishing. SWE-bench's newest entry is 2026-02-26; Aider's is
2025-10-03. Every ChatGPT and Claude plan is unrankable for coding, and the one plan that ranks does
so on evidence half a year old.

The owner then fetched the **Epoch AI benchmarking bundle** (CC-BY, ~79 CSVs, retrieved 2026-08-15).
Its real shapes are now on disk and measured — the FP-M2-2 rule is satisfied: nothing below is
written against an unseen shape.

**What the data actually says.** Every figure below was recomputed from the fetched CSVs on
2026-08-15. On 2026-08-16 the real registry + reconciliation + `coverage.plan_coverage` path found
that the first signed version had omitted roster-named **GLM 5.2**: Perplexity Pro and Max name it,
the registry canonicalises it to `glm-5.2`, and Epoch carries a 2026-06-25 evaluation. The
owner-approved corrected reading is:

| Board | Rows | Real evaluation-date column? | Newest eval date (whole board) | Newest eval date **for the models our plans name** | Which of our models |
|---|---|---|---|---|---|
| Epoch `swe_bench_verified.csv` | 35 | yes (`Started at`) | 2026-06-25 | **2026-06-25** | Gemini 3.1 Pro (preview-customtools), Gemini 3 Pro, **GLM 5.2** |
| `deepswe_external.csv` | 50 | **NO — `Release date` only** | — | — | **GPT-5.6, GPT-5.6 Sol, Claude Opus 5**, Gemini 3.1 Pro (preview) |
| `frontiercode_external.csv` | 25 | **NO — `Release date` only** | — | — | GPT-5.6 Sol, Claude Opus 5 |
| `terminalbench_external.csv` | 204 | yes (`Run date`) | **2026-05-15** | **2026-05-14** | Gemini 3.1 Pro, Gemini 3 Pro |
| `aider_polyglot_external.csv` | 77 | yes (`Date of evaluation`) | 2025-10-03 | — | none |

Two constraints fall out of that table, and together they are the milestone:

1. **No single board covers our plan surface.** The real engine measures Epoch SWE-bench at **5/10**
   plans, DeepSWE at **6/10**, FrontierCode at **3/10**, TerminalBench at **5/10**, and Aider at
   **0/10**. Epoch carries Gemini and roster-named GLM 5.2, but neither GPT-5.6 nor Opus 5; the
   boards that carry ChatGPT and Claude do not cover the whole Gemini/GLM surface.
2. **Coverage and freshness are a plan-level trade-off, not source-wide absolutes.** Epoch
   SWE-bench makes 5/10 plans scoreable, but only Perplexity Pro and Max select GLM 5.2's real
   **2026-06-25** evaluation (52 days old). Google AI Plus, Pro, and Ultra select Gemini 3.1 Pro's
   **2026-02-24** evaluation (173 days old). The honest Epoch baseline is therefore **2/10 fresh,
   3/10 stale, 5/10 unscored** — never "5/10 fresh". DeepSWE reaches 6/10 but publishes **no
   evaluation date at all**, only model release dates; FrontierCode is also undated. Ageing either
   one by a model's launch date would let a re-released model look freshly measured. The current
   source-global `source_health()` maximum is still useful source telemetry, but it can mask the
   age of a plan's selected row and cannot satisfy the amended criterion by itself.

That measured trade-off is why the primary-board choice was recorded as a decision rather than an
implementation detail. The 2026-08-16 unattended-wave ruling consumed the W1 gate only after the
shipped measurement was complete.

### The two traps this milestone must not walk into

**Trap 1 — the Gemini contradiction.** Gemini 3.1 Pro scores **0.756** on Epoch's SWE-bench
Verified and **0.118** on DeepSWE — a 6.4× gap on the same model family and the same task shape.
Neither row is the plain model: SWE-bench carries `gemini-3.1-pro-preview-**customtools**`, DeepSWE
carries `gemini-3.1-pro-preview` under `mini-swe-agent`. **Both are previews**, so "one is a preview"
explains nothing — the distinguishing token is `customtools`, i.e. the tool interface the model was
given. A range-read of the Epoch `.eval` journal confirms `inspect_ai` task `swe_bench_verified`,
agent `bash`, solver `bash_agent`, and edit tools `text_editor` + `apply_patch`; that establishes the
configuration difference but not its causal effect. The leading hypothesis is therefore a
tool-format mismatch under the default harness, and that is what W1 must test; it remains unverified.
Shipping either number without the
explanation would hand a user a verdict the evidence does not support — and it lands squarely on
Google AI Pro/Plus/Ultra, three of our ten plans.

**Trap 2 — effort is a scoring dimension we do not model.** Epoch reports the same model at
**five** levels — `max / xhigh / high / medium / low` (the first draft of this plan said four and
omitted `low`; the fresh-eyes pass caught it, and `low` is exactly where the spread's bottom sits).
The spread is not cosmetic: `claude-opus-5` runs 0.736 at max down to **0.581 at low**; `gpt-5.6-sol`
0.727 down to **0.454**. Today a score in this system is a **(model, harness)** pair. If the registry
canonicalises `claude-opus-5_max` → `claude-opus-5`, five different runs
collapse into one and `MAX()` silently publishes the best-case number — advertising a performance
level the buyer's plan may not even offer. **A score becomes a (model, harness, effort) triple in
this milestone, or the ingestion is not honest.**

Also observed and to be handled, not assumed: FrontierCode's `Reasoning effort` column and the
`_suffix` on `Model version` **disagree** on at least one row (`claude-opus-5_max` / effort
`medium`). The parser picks one, states which, and counts the conflicts.

---

## 2. Acceptance criteria (REQ-IDs)

| REQ-ID | Criterion | Closes |
|---|---|---|
| **REQ-ING-010** | Epoch AI is a first-class source: documented CSV bundle, provenance mandatory, loud-fail per source, own `last_verified` clock, staleness disclosed like every other source | M4 deferral |
| **REQ-ING-011b** | A fresher coding benchmark is INGESTED (not merely investigated), and freshness is published **per curated plan from the evidence row the engine actually selects**. Every plan is counted exactly once as fresh (<60 days), stale (dated, ≥60 days), undated (score exists but only a release date/no evaluation date exists), or unscored. Source-global newest dates may be reported as telemetry but cannot satisfy this criterion. For an undated board, release dates MUST be identified as release dates and MUST NOT be read as evidence age. The initial Epoch target is the measured **2/10 fresh, 3/10 stale, 5/10 unscored** distribution; silently promoting that to "5/10 fresh" fails the criterion | M4 deferral + owner meaning ruling 2026-08-16 |
| **REQ-CAN-005** | Reasoning effort is PARSED and STORED, never swallowed: `model_version` suffixes and effort columns resolve to an explicit effort value; a row whose effort cannot be determined is counted and disclosed, never defaulted | Trap 2 |
| **REQ-REC-011** | The coding answer states which effort level it ranked on and what the model reaches at higher effort (shipped string is Turkish, e.g. *"this model reaches 0.74 at max effort"*), per the owner's Q1 ruling | Trap 2 |
| **REQ-SUB-007** | Coding plan coverage is re-measured through the real engine before and after, and the delta is published as a number in the closure report — a promise is not a measurement | §0 |
| **REQ-LIC-001** | Epoch's CC-BY attribution ships **where the data is served**: the citation string in the recommendation payload's source list AND in the README, not only in a comment | Licence obligation |
| **REQ-REC-012** | The Gemini contradiction is resolved or DISCLOSED: either the investigation explains it and the record says how, or both numbers are carried with the disagreement stated. Silently picking one is a milestone failure | Trap 1 |

---

## 3. Waves

**W1 — Ingest what is safe, and MEASURE the rest (the decision wave)**
1. `EpochClient` + parser over the documented CSV bundle. One canonical fake + a contract test
   against the real file shapes now on disk (V3C-44).
2. Ingest **Epoch's SWE-bench Verified** first — same benchmark the project already carries, so it
   is the lowest-doctrine-risk step and it exercises the whole Epoch path end to end. It **is** a
   freshness win for two plans: roster-named GLM 5.2 gives Perplexity Pro/Max real 2026-06-25
   evidence, 52 days old on 2026-08-16. It does **not** freshen the three Google plans, whose
   selected Gemini evidence is 2026-02-24. Its value is honest 2-fresh/3-stale/5-unscored coverage,
   breadth (24 more models), Epoch's own `inspect_ai` harness recorded as a distinct harness (never
   merged into swebench.com's rows), and a working ingestion the later boards reuse.
3. **Investigate the Gemini contradiction** (REQ-REC-012) — the variable to test is `customtools`
   vs the default tool interface, NOT "preview vs release" (both rows are previews). Epoch's
   SWE-bench CSV carries `Log viewer` / `Logs` columns; use them. Write the verdict with evidence
   either way, and if it cannot be explained, carry both numbers with the disagreement stated.
4. **Measure, per candidate board, by actually running the registry and `coverage.plan_coverage`**
   — not by name-matching in a spreadsheet — and report BOTH numbers that matter: the coverage delta
   AND what the board's dates actually mean (evaluation date vs model release date). A board that
   fixes coverage but cannot be aged is a different trade than one that can; the owner signs with
   both numbers in front of him. Freshness is computed from each plan's selected row, not the
   board's newest linked row: TerminalBench, for example, has a 2026-05-14 linked row while the
   current MAX-score selection can carry a 2026-03-13 row. The pre-implementation baseline is Epoch
   SWE-bench 5/10 = 2 fresh + 3 stale, DeepSWE 6/10 undated, FrontierCode 3/10 undated,
   TerminalBench 5/10 with plan-specific selected dates to report, and Aider 0/10; W1 must reproduce
   it through the shipped ingestion + selection path rather than treating this planning measurement
   as the acceptance proof.
5. **Delegated decision gate:** the record ends with a recommendation. Under the owner's
   2026-08-16 unattended-wave instruction, the agent selected recommended option 1 and recorded the
   basis before W2 began.

**W2 — Effort becomes data (REQ-CAN-005, REQ-REC-011)**
1. Schema: `effort` on `scores`, with a migration (the M4 lesson: a new column needs `migrate()` and
   a citing test through a pre-wave database).
2. Registry rules for the effort suffix family, with the same self-defending table property tests
   W1 of M4 established — an effort suffix may never be swallowed into the base model rule.
3. Ranking policy: one named effort level, chosen in DATA (not code), with the range disclosed in
   the output. Includes the honest branch when a model publishes only one effort row.
4. Fault-injection targets stated up front: merge efforts → citing test RED; drop the range
   disclosure → citing test RED.

**W3 — Apply the signed board decision (REQ-ING-011b, REQ-SUB-007)**
1. Ingest the board the owner signed at W1 as the coding category's primary evidence (or, if he
   signs the two-category option, add the second category through the existing D-105 category
   contract — no new mechanism).
2. Re-measure coverage through the real engine; publish before/after.
3. Publish fresh/stale/undated/unscored counts from each plan's selected evidence row; keep
   source-global health explicitly labelled as source telemetry.
4. Update every disclosure string that names the coding benchmark, so no text still claims
   SWE-bench when the category no longer rests on it.

**W4 — Attribution, ledger, and the sources that fight back (REQ-LIC-001 + carried ledger)**
1. CC-BY attribution in the payload and README (REQ-LIC-001).
2. Epoch staleness leg in CI, matching the existing plan/roster staleness legs.
3. Ledger rows, in priority order: **W-007** (a 500 on Arena's filter endpoint drops the client into
   full pagination and it rate-limits itself — reproduced on the owner's machine 2026-08-15),
   **W-003** (roster staleness never disclosed), **W-004** (`migrate()` not wired to a command),
   **W-006** (the `dusuk` case never says how many plans the cap priced out).
   **W-002** and **W-005** stay ledgered for the API milestone, where their contracts are decided.

**Cap:** 4 waves. If W1's measurement says the board decision needs its own milestone, W3 becomes a
carry and this closes at 3 — close early, never stretch (A0.5).

---

## 4. Shared contracts (K.8)

Frozen: `plans` / `plan_models` / `plan_config` / `scores` / `pricing` schema **except** the additive
`scores.effort` column; the `RawSource` protocol; registry first-match semantics; CLI exit codes;
the D-105 category contract; D-109 rounding boundary; D-110 equivalence disclosure.
New shared surface: Epoch source name + its provenance columns, the effort field and its policy
value, the attribution string. `grep -n` output pasted at each wave's dispatch.

### M5 data-boundary invariants

- Epoch runtime ingestion reads only an explicitly local, unpacked, allowlisted CSV bundle. A URL,
  missing board, malformed provenance/date, malformed shape, or wholly unusable board fails that
  source loudly; `tests/unit/test_epoch_ingest.py` contains the negative cases.
- Release dates never become evaluation dates. An undated board remains `undated` and cannot look
  fresh through model-release metadata; `tests/unit/test_coverage.py` exercises the four-state
  partition and the 60-day boundary.

Effective wave review tiers: W1 **HIGH** (input parsing), W2 **HIGH** (migration + input parsing),
W3 **HIGH** (new board ingestion), W4 **LOW-MED** unless its final diff crosses an auto-HIGH
boundary. The milestone's overall product-risk label remains LOW-MED.

## 5. Token budget estimate

W1 ≈ 110k (investigation + measurement) · W2 ≈ 80k · W3 ≈ 70k · W4 ≈ 70k · reviews ≈ 110k
(**including a second fresh-eyes pass over every fix delta — M4's escaped-blocker lesson, now
budgeted rather than improvised**) · closure ≈ 60k → **≈ 500k**.

## 6. Issue inventory

**W-007 is NEW and is written into `docs/warnings.ledger.md` by this plan's commit** — it was found
during the owner's M4 verification run, after the M4 ledger was closed. The rest are carried in.
**Ledger reconciliation done here:** W-002 and W-005 were ledgered at M4 close with owning milestone
"M5 (API contract wave)" on the assumption that M5 would be the API. The owner then set M5 = coding
rescue, so both move to **M6 with the API**, and the ledger rows say so — the ledger is the truth,
and it now matches this plan.

| id | What | Wave |
|---|---|---|
| W-007 | Arena's filter endpoint 500s → client falls back to full pagination → self-inflicted 429 | W4 |
| W-003 | `plan_models.last_verified` written, never read — stale roster links undisclosed | W4 |
| W-004 | `migrate()` exists but no command calls it | W4 |
| W-006 | `dusuk` budget: three labels, one plan, no sentence saying five plans were priced out | W4 |
| W-002 | `equivalent_plans` loses group structure with 2+ groups | M6 (API contract) |
| W-005 | YAML alias-expansion guard | M6 (when an untrusted producer becomes possible) |
| W-001 | gitleaks false positive — **owner action**, survived M3 and M4 | owner |
| — | `scripts/` fails repo-wide ruff/black (gate scoped to `src tests`) — GP-upstream note | — |

## 7. Definition of done

`make check` green on all eight gates · every criterion in §2 has a citing test that was shown able
to fail · coding coverage published as a before/after number · the Gemini contradiction resolved or
disclosed with evidence · Epoch attributed where the data is served · security review PASS ·
closure report + retrospective (answers M4's carried question about models no benchmark covers).

---

*Owner signature: **APPROVED — Umut Can Apaydin, 2026-08-16.***
