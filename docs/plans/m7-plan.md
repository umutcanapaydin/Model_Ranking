# M7 Plan — Build the artifact, stop writing while serving, go live

**Status:** **SIGNED** by the owner on 2026-08-17. Wave dispatch is authorized.
**Date:** 2026-08-17 · **Risk tier:** HIGH (W2 touches the scoring path; W1 creates a new
production entry point — both auto-escalate under V3C-78)
**Mode:** A0.5 + **D-117** (the agent commits at wave boundaries under five conditions; the
milestone commit stays the owner's)
**Process baseline:** GP v5.0 (**D-113**)
**Quarterly obligation:** M7 is not `M % 3 == 0`. No quarterly handover is due; `note.txt` refresh
is still mandatory at 4.4.

---

## 0. Why this milestone exists

M6 gave the product a mouth. It cannot yet be fed, and nothing it says can reach a user.

Three facts, each verified at planning time rather than remembered:

**(1) No production code builds the evidence database.** The entire ingestion pipeline — five
remote sources, `plans`, `rosters`, `reconcile`, `reconcile_plans` — exists only as a ~30-line
heredoc inside `.github/workflows/contract-tests.yml:77-119`. It is not in `src/`, so `ruff`,
`mypy`, `pytest` and coverage have never seen it; it writes to `ci_advisor.db` and discards it; and
it runs on a Monday cron **that has never fired in this repository's history**. The product's data
production path is untested, ungoverned, unrun code embedded in CI configuration.

**(2) That is the root of W-023.** `advisor.db` and `owner_advisor.db` are pre-M5 schema because
nothing rebuilds them. The remedy recorded at M6's closure — one `schema migrate` command — is
necessary and **not sufficient**: migrating a schema does not populate `px_median`, and re-ingesting
rosters requires an ingestion entry point that does not exist as product code.

**(3) The engine still writes while serving.** `recommend()` calls `build_price_medians(conn)` at
`recommend.py:285`, which runs `DELETE FROM px_median` + `INSERT` (`rank.py:163-165`) on every
request. M6 could not fix this — the signed plan forbade engine changes — so it *contained* it by
copying the whole database into memory per unauthenticated GET (`main.py:391,803`). That
containment is **W-017**, measured at ~47,000x amplification, and **D-116 names it a CONDITION of
go-live, not a follow-up.**

The through-line: **(1) and (3) are the same defect seen from two ends.** The medians are computed
in Python and then persisted for the sole purpose of being JOINed back (`rank.py:225`). They are
persisted at *read* time because there is no *build* time to persist them at. Create the build
step and the write leaves the serving path on its own.

### What this milestone deliberately does NOT do

M6's retrospective asked whether M7 should spend a wave making "does this control actually execute"
mechanically checkable. **The owner ruled: no — focus on deploy, carry the question to M8.** The
reasoning is recorded because it should be re-examined and not silently inherited: this milestone
removes the most expensive reachability failure the project has (the snapshot, and the unrun
pipeline behind it) by *deleting the unreached code*, rather than by adding a control that watches
for it. Whether the general mechanism is worth building is a separate question with its own
evidence, and M8 owns it.

### The four traps this milestone must not walk into

**Trap 1 — Making `px_median` empty instead of stale.** The moment `build_price_medians` leaves the
serving path, an evidence database that was never built has an empty `px_median`. `rank.py:225`
JOINs it, so an empty table yields zero rows, `recommend()` returns `None`, and `/v1` answers **200
with zero picks**. That is a wrong answer served confidently — the exact failure mode W-023
described, arriving through a second door that this milestone opens itself. **Any wave that moves
the median build MUST, in the same wave, make the serving path fail LOUD on an unbuilt table.**

**Trap 2 — Lifting the heredoc without governing it.** Copying thirty lines of CI YAML into a file
under `src/` satisfies nothing by itself. The point is that `ruff`, `mypy --strict`, `pytest` and
coverage begin to see it, that it has citing tests through the real entry point (V4C-50: *every
load-bearing path needs at least one test through the real entry point*), and that the CI heredoc
is **deleted in the same change** rather than left as a second, divergent copy. Two implementations
of the pipeline is worse than one unrun implementation.

**Trap 3 — Believing the artifact because a command exited 0.** `make smoke-deps` reported PASS at
the M6 gate and was FAILING at the closing tree (W-024, arena on an upstream HTTP 500). The lesson
is already paid for: *configured is not working, and neither is measured-once*. Every claim about
the built artifact in this milestone is derived from the artifact at the moment of the claim —
row counts read back from the file, not printed by the builder that wrote it.

**Trap 4 — Deploying a healthy-looking corpse.** `/health` returned 200 with a correct build stamp
against a database that could not answer a single query. Stage 4.3 verifies deploys with `/health`.
**The go-live check in W4 must assert on a real answer's CONTENT, not on a 200** — `scripts/journey.py`
exists for exactly this (V3C-106) and has never been pointed at a live host.

---

## 1. Acceptance criteria (REQ-IDs)

New REQ-IDs are proposed here and must be copied into `docs/prd.md` §13 at W1, not at closure — the
F-1 drift the M4 gate raised came from criteria living only in a plan.

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-ING-012** (new) | A single runnable production entry point in `src/` builds the evidence database end to end: schema, `plans`, `rosters`, all five remote sources, `reconcile`, `reconcile_plans`, and the price medians. It is typed, linted and covered like the rest of `src/`. | A test that invokes the real entry point and asserts on the resulting file's contents |
| 2 | **REQ-ING-013** (new) | The builder fails LOUD and non-zero on a partial build. A source that returns nothing, a reconciliation that registers no models, or an empty `px_median` is an error, never a quiet success. | Fault injection: each failure mode forced, each must exit non-zero |
| 3 | **REQ-CAN-003** (existing) | Median reference price per canonical model is **unchanged, value for value**, after the build moves out of the serving path. | A parity test comparing every model's `in_m`/`out_m` before and after, on the same inputs |
| 4 | **REQ-API-007** (new) | The serving path performs **no write** to the evidence database and holds **no full-database copy**. `serving_snapshot` is deleted, not merely unused. | A test asserting the database file's mtime and size are unchanged across requests; grep proving the symbol is gone |
| 5 | **REQ-API-008** (new) | A serving process whose evidence database has an unbuilt or empty `px_median` **refuses to answer**, with the operator-facing remedy named. It does not return 200 with zero picks. | A test with a schema-valid but unbuilt database asserting a non-200 and the remedy string |
| 6 | **REQ-API-009** (new) | The deployed service answers a real query with correct CONTENT — both coding surfaces, neither leading (D-115, Ruling A) — from a host, over the network, unauthenticated. | `scripts/journey.py --base-url <host>`, exit 0 |
| 7 | **W-017** | Closed, not deferred: the amplification is **removed** rather than bounded. | The W4 security pass re-derives it and finds no snapshot to measure |
| 8 | **W-023** | Closed: the shipped artifact is produced by REQ-ING-012's entry point and serves real answers. | The deployed `/v1` returns picks |

**Criterion-to-wave map:** W1 owns 1, 2 and 8. W2 owns 3 and 5. W3 owns 4 and 7. W4 owns 6.

---

## 2. Waves

### W1 — The builder (risk: **HIGH**; new production entry point + untrusted network input)

Lift the pipeline out of CI YAML into `src/app/workflows/build.py` (name provisional) with a real
CLI entry point, then delete the heredoc.

1. `build.py` exposing one function and one `__main__` path: create schema → `ingest_plans` →
   `ingest_rosters` → the five remote sources → `reconcile` → `reconcile_plans` → **the price
   medians** (this is where `build_price_medians` lands in W2; W1 leaves the call in `recommend()`
   untouched so the two changes stay separately reviewable).
2. Loud failure on every partial outcome (REQ-ING-013). The heredoc's two existing assertions
   (`rr.stored > 0`, `rep.models_registered >= 20`) are the floor, not the ceiling — they become
   typed checks with named errors and exit codes, and the exit-code contract follows **D-120**
   (a distinct non-zero code for "operator action required" versus "failed").
3. Delete the heredoc from `.github/workflows/contract-tests.yml` and have the workflow invoke the
   real entry point. **A second copy is the failure this wave exists to end.**
4. Produce `advisor.db` with it and read the result back from the file (Trap 3) — **W-023 closes
   here or the wave does not close.**
5. Fault injection (V3C-72), pre-declared: each source made to return empty; `reconcile` made to
   register zero models; the rosters file made absent; `px_median` left unbuilt. Every one must be
   RED before its fix and killed after.

**Note on W-024.** The arena source is down on an upstream HTTP 500 and this wave will hit it. The
builder must **fail** on it rather than skip it. If the outage persists, the owner rules whether a
build without arena is acceptable for a first deploy — that ruling becomes an ADR, not a `try/except`.

### W2 — The medians leave the read path (risk: **HIGH**; scoring path, D-104/D-105/D-109)

1. Move `build_price_medians(conn)` out of `recommend()` (`recommend.py:285`) into W1's builder.
2. `recommend()` — or the layer above it — **refuses** when `px_median` is unbuilt, naming the
   remedy (REQ-API-008, Trap 1). Refusal is the auth/safety fail direction (V3C-33/45): an evidence
   engine with no evidence fails CLOSED.
3. Parity proof (REQ-CAN-003): every model's median prices identical before and after, on identical
   inputs. **Not "tests still pass" — a value-for-value comparison**, because the M6 lesson is that
   a green suite is compatible with a control that never ran.
4. The 12 existing tests that call `build_price_medians(conn)` directly are fixture builders and
   stay legitimate; the ones asserting on `px_median` contents (`test_rank.py:86,177,226`) must now
   assert against the builder's output.

### W3 — The snapshot dies (risk: **HIGH**; V4C-50 — a fix inherits the risk class of its bug)

1. Delete `serving_snapshot` (`main.py:391`) and open the database read-only at the call site
   (`main.py:803`). With W2 landed, no write remains to contain.
2. **W-017 closes by deletion.** Remove the memory-budget machinery that existed only to bound the
   copy — `RSS_FACTOR`, `MEMORY_BUDGET_MB`, `PROCESS_BASELINE_MB`, `max_database_bytes()` — or state
   in the wave record why each survivor still earns its place. A ceiling for a copy that no longer
   happens is a control with nothing behind it.
3. `fly.toml`'s concurrency/memory arithmetic and its citing test change with it.
4. Prove the negative (REQ-API-007): the database file is byte-identical and mtime-unchanged across
   a run of requests, and `serving_snapshot` is absent from the tree.

### W4 — Go live (risk: **MED**, but gated by a BLOCKING Stage 4.0)

1. **Stage 4.0 security review runs before this wave deploys anything** — AGENTS.md §6 binds it to
   4.3, and this is the milestone where 4.3 finally happens. It re-derives W-017 and finds nothing
   to measure, or the wave stops.
2. Deploy per **D-116** (Fly.io, evidence database as a shipped artifact, no ingestion on the
   serving host). `Dockerfile` and `fly.toml` stop being proposals — the owner adopts them or rules
   otherwise (M6 closure report §0 item 4).
3. `curl /health | jq .build` == the intended tag/SHA (L.7 — restart is not rebuild).
4. **`scripts/journey.py --base-url <host>` exits 0** (REQ-API-009). This asserts content, not
   status codes, and is the only check in this milestone that a real user's question gets a real
   answer.
5. `make smoke-deps` exit 0, or the owner's explicit ruling on W-024.

---

## 3. Shared contracts (K.8) — grep-verified at planning time

```
### the serving path's write, and the table it writes
src/app/workflows/recommend.py:285:    build_price_medians(conn)
src/app/workflows/rank.py:163:        conn.execute("DELETE FROM px_median")
src/app/workflows/rank.py:165:            "INSERT INTO px_median (model_id, in_m, out_m) VALUES (?,?,?)",

### the JOIN that makes an empty px_median a silent zero-pick answer (Trap 1)
src/app/workflows/rank.py:225:        JOIN px_median p ON p.model_id = m.id

### the containment W3 deletes
src/app/adapter/main.py:391:def serving_snapshot(path: Path) -> sqlite3.Connection:
src/app/adapter/main.py:803:        conn = serving_snapshot(path)

### FROZEN by D-115 — this milestone may not change these (Ruling A)
src/app/adapter/main.py:58:CODING_INTENT: tuple[str, ...] = ("agentic-coding", "coding")
src/app/adapter/main.py:70:DECLARED_ROUTES: frozenset[str] = frozenset(
src/app/adapter/main.py:576:PUBLIC_ANSWER_FIELDS = frozenset(
src/app/adapter/main.py:599:PUBLIC_PICK_FIELDS = frozenset(

### the pieces W1 assembles, today reachable only from tests and a never-run cron
src/app/workflows/plans.py:169:def ingest_plans(conn, raw, run) -> SourceReport
src/app/workflows/rosters.py:120:def ingest_rosters(conn, raw, run) -> SourceReport
src/app/workflows/registry.py:256:def reconcile(conn) -> ReconcileReport
src/app/workflows/registry.py:228:def reconcile_plans(conn) -> PlanReconcileReport
.github/workflows/contract-tests.yml:77-119: the heredoc W1 replaces and deletes
```

**Frozen and out of scope:** the `/v1` payload shape (**D-115**), English query values (**D-118**),
`schema migrate` exit 3 (**D-120**), no LLM in the scoring path (**D-104**), no cross-scale
averaging (**D-105**), rounding at the output boundary only (**D-109**). A wave that needs one of
these to move stops and escalates.

---

## 4. Definition of done

`make check` exit 0 · `make gate` green except legs with a recorded reason · `gitleaks` clean ·
**`make smoke-deps` exit 0 or an owner ruling on W-024** · every criterion in §1 traced in
`docs/coverage-by-req.md` with a citing test shown able to fail (V3C-02) · fault injection run per
wave with every stay-green mutant given its mandatory test · fresh-eyes review per wave (K.7), with
separate Code-Reviewer + Tester on the HIGH waves (V3C-78) · Stage 4.0 security PASS **before** the
deploy in W4 · **W-017 and W-023 closed, not carried** · ADRs for the arena ruling and for adopting
the deploy files · retrospective answering M6's carried question about reachability with M7's
evidence, and posing the next · dated `docs/EXPERIENCE.md` entry · `note.txt` refreshed ·
`docs/closure-report-m7.md` generated.

## 5. Carried in, and what happens to each

| Item | Disposition in M7 |
|---|---|
| **W-017** snapshot amplification | **CLOSED in W3** by deletion |
| **W-023** pre-M5 artifact | **CLOSED in W1** by production, not migration |
| **W-024** arena HTTP 500 | Forced in W1; owner ruling if the outage persists |
| **W-025** local Python 3.14 vs CI 3.12/3.11 | W4, alongside the deploy toolchain pin (V3C-65) |
| **W-019** `L1` detects an alphabet | Carried to M8; no mechanical fix proposed on purpose |
| **GPF-001..005** | Already handed back to General_Pipeline; the conformance legs stay RED with their reason until GP rules |
| Coverage / roster-staleness CI legs, never run | W1 — the same class as this milestone's headline finding, and the builder change touches that workflow anyway |
| M6's carried question (reachability) | **Deferred to M8 by the owner's ruling**, reasoning recorded in §0 |

## 6. Token budget estimate

Four waves, three at HIGH tier with two review seats each. M6 spent roughly 2× its estimate because
three waves needed three review rounds; **that is the expected shape, not an overrun**, and this
plan assumes at least two rounds on W1, W2 and W3 rather than hoping for one.

---

## 7. Signature

The owner signs by changing **Status** at the top of this file to SIGNED with a date. Until then no
wave dispatches, per the standing rule that no wave starts without a signed plan.
