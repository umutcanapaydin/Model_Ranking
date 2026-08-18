---
record_type: wave
id: m7-wave-3-close
status: draft
process_version: v5.0
date: 2026-08-18
---
# Wave-Close Checklist — M7 Wave 3 (the snapshot dies)

> **STATUS: CLOSED 2026-08-18.** **W-017 is closed by DELETION, not by a bound** — the distinction
> is the whole wave. An amplification that is bounded still exists and still needs a number nobody
> can agree on; three security passes derived three different figures for this one.

## What the wave deleted, and why deletion was the fix

`serving_snapshot` copied the entire evidence database into memory for every unauthenticated GET.
It existed because `recommend()` wrote on every call and an HTTP surface cannot serve from a
read-write handle. M6 could not remove the write — its signed plan forbade engine changes — so it
contained it, and then spent a Stage-4.0 round deriving a memory ceiling for the copy: an RSS
factor, a VM budget, a process baseline, a concurrency cap, and a derived `max_database_bytes()`.

W2 removed the write. W3 removed the copy, **and every constant that existed only to size it**,
plus the boot-time database-size ceiling. Keeping them at comfortable values would leave a future
reader tuning a budget that governs nothing — and worse, the ceiling would refuse to boot on a
perfectly servable artifact for a cost the process no longer pays.

**Measured, not asserted:**

| | |
|---|---|
| Database | 0.93 MiB |
| Peak RSS after 1 request | 62.0 MiB |
| Peak RSS after 31 requests | 62.7 MiB |
| **Growth over 30 requests** | **0.64 MiB** |
| A copy per request would have added | **~28 MiB** |
| Database after serving | byte-identical |

| # | Check | Evidence | ✅ |
|---|---|---|---|
| 1 | Risk tier — D-122 | Serving path + a deleted security control ⇒ FULL depth (`docs/decisions.md` D-122; `src/app/adapter/main.py`) | ✅ |
| 2 | REQ-API-007 has a citing test able to fail | `test_api_config.py::test_w017_is_closed_by_deletion_not_by_a_bounded_copy` asserts the MECHANISM, not the name: it parses the adapter and fails on any `backup()` call or `:memory:` connection | ✅ |
| 3 | Fault injection — V3C-72 | `m7w3_lead_faultinject.py`: 5 mutants, 3 killed first pass, **5/5** after. A mutant that re-introduced the snapshot under a different name was killed by the mechanism assertion | ✅ |
| 4 | Deploy proposal follows the code | `fly.toml` no longer ties its VM size to a snapshot arithmetic; the concurrency declaration stays, because it is a real property of the server | ✅ |
| 5 | Gates green | `make check` exit 0 · 482 passed / 12 skipped | ✅ |
| 6 | W-017 closed in the ledger with its measurement | `docs/warnings.ledger.md` W-017 → FIXED | ✅ |

## What this wave should be remembered for

**I deleted a test that was still guarding a live control.**

Three tests guarded the memory-budget machinery, so they went with it. One of them ALSO guarded the
agreement between the process's concurrency cap and `fly.toml`'s edge `hard_limit` — a control with
nothing to do with snapshots, which survives the deletion and still matters: if the edge admits more
than the process runs, the surplus queues inside the app instead of being shed at the edge.

Two mutants walked straight through the gap: setting the cap back to AnyIO's unchosen default of 40,
and drifting the edge limit to 32. Both stayed green.

**The test I wrote to replace those three says, in its own docstring, that deleting a test quietly
is how a control disappears without anyone deciding it should.** I wrote that sentence and did the
thing in the same change. The guard is restored and both mutants are RED.

A smaller one worth keeping: I also wrote a limiter test that read the per-loop value from the test
thread — and a correct version further down the same file already warns about exactly that in its
docstring. Deleted as a worse duplicate rather than kept as coverage.

---

Touched: `docs/warnings.ledger.md`, `fly.toml`, `src/app/adapter/main.py`, `tests/unit/test_api_config.py`, `tests/unit/test_api_v1.py`
(5 files changed, 163 insertions(+), 190 deletions(-))

K.8 contracts: `adapter.serving_snapshot` REMOVED, with `RSS_FACTOR`, `MEMORY_BUDGET_MB`, `PROCESS_BASELINE_MB` and `max_database_bytes()`. `fly.toml` drops `MODEL_RANKING_MEMORY_BUDGET_MB`. `MAX_CONCURRENT_REQUESTS` kept and still tied to `fly.toml`'s `hard_limit`.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-18 · Wave commit range: `fb258f3..c68dcd6`

> Added at M7 closure after `scripts/wave_check.py` failed all four of this milestone's wave records
> on exactly these three lines. The gate exists, it works, and `make check` does not run it — the
> same shape this project has spent five milestones finding in its code, here in its records.
> Ledgered as **W-032**; wiring `make wave-check` into `make check` is a gate-definition change and
> therefore the owner's.
