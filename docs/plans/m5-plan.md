# M5 Plan — Rescue the Coding Category (data depth, phase 2)

**Status:** DRAFT — **UNSIGNED**, awaiting owner signature. No wave dispatches until it is signed.
**Date:** 2026-08-15 · **Risk tier:** LOW-MED · **Mode:** A0.5 + D-106
**Process baseline:** GP v4.3.1 (D-108). Waves run without stopping (owner amendment, M3); the owner
runs the out-of-sandbox verification at the milestone gate. **One planned mid-milestone touchpoint**
— see §2 Q2: the primary-benchmark choice is a criteria-meaning question and the escalate-now list
puts those with the owner, not the agent.

**Owner decisions locked 2026-08-15 (this session):**
- **Scope:** rescue the coding category with the Epoch data. NOT the HTTP API — that moves to M6,
  with Fly.io still the recorded deploy target.
- **Q1 effort policy: rank on ONE named effort level and disclose the range.** Effort is stored as
  data; comparisons happen at a single level so they stay fair; the output says what the model
  reaches at higher effort instead of hiding it.
- **Q2 primary benchmark: MEASURE FIRST, decide after.** W1 produces the evidence; the owner signs
  the board choice mid-milestone. (Directly applying M4's retrospective lesson: a criterion that
  contains a number about live data gets a measurement task in the wave *before* it.)

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

**What the data actually says** (measured 2026-08-15 from the fetched bundle):

| Board | Rows | Newest run | Harness column | Carries the models our plans name? |
|---|---|---|---|---|
| Epoch `swe_bench_verified.csv` | 35 | **2026-06-25** | no (implicit: Epoch inspect_ai) | Gemini 3/3.1 Pro only |
| `deepswe_external.csv` | 50 | 2026-07-24 | **yes** (mini-swe-agent) | **GPT-5.6, GPT-5.6 Sol, Claude Opus 5, Gemini 3.1 Pro** |
| `frontiercode_external.csv` | 25 | 2026-07-24 | **yes** (claude-code / codex / …) | GPT-5.6 Sol, Claude Opus 5 — no Gemini |
| `terminalbench_external.csv` | 204 | 2026-05-14 | **yes** (52 agents) | Gemini 3/3.1 Pro |
| `aider_polyglot_external.csv` | 77 | 2025-10-03 | edit-format only | none |

**No single board covers our plan surface.** That is the milestone's central constraint, and it is
why the board choice is a signed decision rather than an implementation detail.

### The two traps this milestone must not walk into

**Trap 1 — the Gemini contradiction.** `gemini-3.1-pro` scores **0.756** on Epoch's SWE-bench
Verified and **0.118** on DeepSWE. Same model family, same task shape, a 6× gap. At least one of
those numbers does not mean what a naive reading says (the DeepSWE row is a *preview* build run
under `mini-swe-agent`; a tool-format mismatch is the leading hypothesis, unverified). Shipping
either number without an explanation would hand a user a verdict the evidence does not support —
and it would land squarely on Google AI Pro/Plus/Ultra, three of our ten plans.

**Trap 2 — effort is a scoring dimension we do not model.** Epoch reports the same model at
`max / xhigh / high / medium`, and the spread is not cosmetic: `claude-opus-5` runs 0.736 (max) down
to 0.581; `gpt-5.6-sol` 0.727 down to 0.454. Today a score in this system is a **(model, harness)**
pair. If the registry canonicalises `claude-opus-5_max` → `claude-opus-5`, four different runs
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
| **REQ-ING-011b** | A fresher coding benchmark is INGESTED (not merely investigated), and the coding category's evidence age drops from 170 days to under 60 | M4 deferral |
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
2. Ingest **Epoch's SWE-bench Verified** first — it is the same benchmark the project already
   carries, so it is the lowest-doctrine-risk step: fresher rows, harness recorded as Epoch's own
   `inspect_ai` runs, disclosed as a distinct harness rather than merged into swebench.com's rows.
3. **Investigate the Gemini contradiction** (REQ-REC-012) — probe Epoch's per-run logs (the CSV
   carries a `Log viewer` / `Logs` column), compare run configuration, and write the verdict with
   evidence either way.
4. **Measure the coverage delta for each candidate board by actually running the registry and
   `coverage.plan_coverage`** — not by name-matching in a spreadsheet. Deliver a ratified record
   with the before/after numbers per board.
5. **Owner touchpoint:** the record ends with a recommendation; the owner signs the primary-board
   choice. Waves continue on everything not blocked by that signature.

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
3. Update every disclosure string that names the coding benchmark, so no text still claims
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

## 5. Token budget estimate

W1 ≈ 110k (investigation + measurement) · W2 ≈ 80k · W3 ≈ 70k · W4 ≈ 70k · reviews ≈ 110k
(**including a second fresh-eyes pass over every fix delta — M4's escaped-blocker lesson, now
budgeted rather than improvised**) · closure ≈ 60k → **≈ 500k**.

## 6. Issue inventory (carried in, with owners)

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

*Owner signature: ____________________  (unsigned — no wave dispatches until this line is filled)*
