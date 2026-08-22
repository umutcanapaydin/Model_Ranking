# M9 Plan — The refresh: the product keeps itself current, unattended

**Status:** **SIGNED** by the owner on 2026-08-21. Wave dispatch is authorized.
**Date:** 2026-08-21 · **Risk tier:** **HIGH** overall (an unattended process that REPLACES what
users are served) · **Mode:** A0.5 + D-117 · **Process baseline:** GP v5.0 · **Review depth:** D-122
**Quarterly obligation:** M9 IS `M % 3 == 0` — `/quarterly-handover` generates
`docs/handovers/handover_q3.txt` at Stage 4.4.

---

## 0. Why this milestone exists

The owner's requirement, recorded as **W-034**: *the shipped product includes an agent that checks
the sources every 12 hours and rebuilds when something changed.*

Today nothing schedules anything. `python -m app.workflows.build` is a command a human types, and it
has been typed by a human every time this product's data has moved. **The evidence users see is as
fresh as the last time someone remembered.** For a product whose entire claim is "we tell you what
is true right now about AI tools", that is the gap between the pitch and the thing.

### What is already built, measured rather than assumed

Two thirds of this milestone's machinery exists, and one piece of it was verified **on 2026-08-21
by experiment rather than by reading**:

| Piece | State |
|---|---|
| A build that fails loud and never leaves a half-written artifact | **Done** (M7). Unique temp workspace, `replace()` only after read-back, cleanup under `except BaseException` |
| Abandoned-workspace cleanup for a killed run | **Done** (2026-08-21, W-028) |
| **Hot swap: a running engine picking up a replaced artifact** | **ALREADY WORKS.** Measured: `advisor.db` was atomically replaced with a modified copy under a live engine and the very next request returned the new data, with no restart. The adapter opens a read-only connection **per request**, so a swap is picked up immediately and an in-flight request keeps the inode it started on. This milestone must PIN that with a test, not build it |
| A scheduler | **Nothing.** |
| Change detection | **Nothing.** A build always publishes |
| A rule for what an unattended refresh may NOT do | **Nothing, and this is the dangerous gap** |

### The trap this milestone exists to avoid

**An unattended refresh can make the product worse without anybody noticing.** Every guard this
project has built assumes a human is watching the build output. Take that human away and the same
machinery becomes a hazard:

- A source blips for an hour. The build succeeds, reports the blind surface honestly per D-121 —
  and **publishes an artifact where a category that was answering an hour ago now says it has no
  evidence.** Every gate green, every disclosure correct, product degraded.
- An upstream renames a column. The build fails loud, correctly, and **nothing tells anyone**,
  because the thing that was listening was a person reading a terminal.
- A model roster shrinks by half for an upstream reason. Nothing today compares "what we are about
  to serve" with "what we are serving".

**The rule this milestone must establish: a refresh may only ever publish an artifact that is not
WORSE than the one it replaces, and any refusal to publish must be visible.** Loud failure is
already this project's doctrine; unattended operation is what turns "loud" into a design problem,
because there is no longer anyone in the room to hear it.

---

## 1. Acceptance criteria (REQ-REF-*, new — to be copied into `docs/prd.md` AT W1)

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-REF-001** | A single command performs one refresh cycle: build into a temporary artifact, compare it against the live one, and publish only if it should be published. It never leaves the live artifact in a worse state than it found it, including when killed mid-run | Fault injection at every stage boundary, including SIGKILL, with the live artifact verified byte-identical afterwards |
| 2 | **REQ-REF-002** | "Changed" is decided on the CONTENT THAT WOULD BE SERVED, not on file bytes or timestamps. An unchanged upstream produces no publish and says so | A cycle run twice against a frozen upstream publishes once; a citing test proves the second run discards its candidate |
| 3 | **REQ-REF-003** | **A refresh REFUSES to publish an artifact that is worse than the live one**: fewer surfaces answering, or materially less evidence behind any surface. The refusal is a first-class outcome with its own exit code, not an error | A candidate built with one source suppressed is refused; a citing test per degradation axis |
| 4 | **REQ-REF-004** | Every cycle leaves a durable record of what it did and why — published, unchanged, refused, or failed — with the numbers it decided on | The run log, asserted by a test that reads it back |
| 5 | **REQ-REF-005** | A refresh runs every 12 hours without a human, and a human can find out that it stopped running at all | The schedule, plus a staleness signal a person or a check can read. **Silence must not be indistinguishable from success** |
| 6 | **REQ-REF-006** | The running engine serves a replaced artifact without a restart, and a request in flight during the swap completes on consistent data | A test that swaps under load and asserts both |
| 7 | **REQ-REF-007** | Ingestion never runs on the serving host (D-116). The refresh produces an artifact and hands it over; it does not reach into a serving process | Review, plus a check that the refresh entry point has no dependency on the adapter |

**Criterion-to-wave map:** W1 owns 1, 2, 6. W2 owns 3 and 4. W3 owns 5 and 7. W4 closure.

---

## 2. Waves

### W1 — One refresh cycle, by hand (risk: **MED**)

`python -m app.workflows.refresh` — build to a temp artifact, fingerprint what it would serve,
compare, publish or discard. No scheduling, no policy beyond "did anything change". Ends with the
hot-swap behaviour PINNED by a test, because it is load-bearing for everything after it and
currently rests on one manual experiment.

The fingerprint is the wave's real design question: it must cover what a user would notice — the
surfaces, their ranked models, scores and prices — and must NOT cover things that move on every
build for no user-visible reason (row order in a table, an ingest timestamp). A fingerprint that
changes every run makes REQ-REF-002 vacuous.

### W2 — The refusal rule (risk: **HIGH**, and this is the wave that matters)

The degradation guard. This is the control that makes unattended operation safe, and it is the one
that can silently do the most damage if it is wrong in either direction:

- Too strict, and a legitimate refresh never publishes — the product freezes while every check
  reports healthy. **This is the failure that looks like success.**
- Too loose, and a bad upstream day degrades the served product automatically.

Under D-122 this gets full depth: it is the scoring path's supply line. Fault injection must include
a candidate that is better, one that is worse on each axis, and one that is different-but-equal.

### W3 — Unattended (risk: **MED**)

The 12-hour schedule, and the answer to *"how does a person find out this stopped?"* — which is the
half that decides whether any of this is real. A refresh loop nobody is watching, that fails
silently, is worse than no refresh loop, because the product now claims freshness it is not
maintaining.

### W4 — Closure + quarterly handover (risk: **LOW**)

M9 is `M % 3 == 0`, so `docs/handovers/handover_q3.txt` is generated at Stage 4.4.

---

## 3. Shared contracts (K.8)

**FROZEN:** the `/v1` payload (D-115, moved once by D-125 — **D-124's window is SPENT**, so no field
may be added in M9 without a new ADR), English query values (D-118), `schema migrate` exit codes
(D-120), and every engine invariant (D-104, D-105, D-109).

**Touched:** `app.workflows.build` (the refresh calls it and must not fork it), and the artifact file
itself, which is the handover surface between the two halves.

**To be grep-verified at W1 dispatch:** the exact publish sequence in `build.py`, because the refresh
must reuse it rather than reimplement it. Two publish paths would be two definitions of "safe to
serve", and this project has spent several milestones on what happens when a set has two definitions.

---

## 4. Definition of done

`make check` exit 0 · a refresh cycle demonstrated end to end against real sources · the degradation
guard proven on a deliberately-degraded candidate · every criterion in §1 with a citing test **proven
RED** (not merely present — the M8 lesson) · fresh-eyes review per D-122, and **on W2 that means an
independent seat, because M8 measured what three consecutive bypasses cost** · ADRs for the three
decisions in §5 · retrospective · dated EXPERIENCE entry · `note.txt` · `docs/closure-report-m9.md` ·
**`/quarterly-handover`**.

**Carried in and NOT blocking W1:** W-024 and W-027 (owner ruled 2026-08-21 to leave them while
nothing deploys), W-030/W-031 (unverifiable without a deploy), W-035..W-039, W-044, GPF-001..006.

---

## 5. Three decisions this milestone must make, in the abstract, before W2

**1. What exactly may a refresh refuse to publish over?** Fewer answering surfaces is obvious.
Fewer models on one surface is not — boards legitimately drop models. A threshold is a product
decision about how much silent shrinkage is tolerable before a human is asked.

**2. What happens on the SECOND consecutive refusal?** One refusal is an upstream blip. Two in a
row is a state the product should not sit in quietly, because the artifact is now a day old and
every surface still claims to be current.

**3. Where does the alert go?** There is no alerting channel in this project today, and the honest
options differ in cost: a file the owner's own `runner` reads (cheap, only works when he runs it),
a non-zero exit the scheduler surfaces (depends on the scheduler), or something that reaches him
without him asking. **This is the decision that determines whether REQ-REF-005 is real or
decorative**, and it should be made deliberately rather than defaulted to "we write it in a log".

---

## 6. What this milestone is NOT

- **Not a deploy.** D-123 remains undischarged and W-030/W-031 stay unverifiable. The refresh runs
  where the build runs today.
- **Not the arena fix.** W-024 has a diagnosed remedy and it touches a security finding's citing
  test; it is the owner's call and is not smuggled in here.
  **SUPERSEDED 2026-08-22 by D-131.** The owner authorised it in session on 2026-08-21 and the fix
  landed inside M9 — with the authorization living only in a chat log until a Stage-4.0 security
  seat returned BLOCKING on exactly that. The line above stayed true at HEAD while the code
  contradicted it, which is the state this note exists to end. The code was sound; the paperwork
  was the finding.
- **Not new categories or new sources.** The product's shape is settled at nine surfaces (D-127);
  this milestone is about keeping what exists true.
