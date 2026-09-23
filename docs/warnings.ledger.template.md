---
record_type: warnings
id: warnings-ledger-template
status: draft
process_version: v6.4
date: 2026-09-23
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Warning ledger — copy to `docs/warnings.ledger.md` at Stage 0

> **Why this file exists.** A gate that warns and produces no consequence is indistinguishable from
> an absent gate. On a real project `gates SKIPPED: contract suite` appeared in **five consecutive**
> wave-close checklists; the rule said the same control skipped three times sends **the control**
> under review, and nothing counted. When the suite finally ran once it produced **six engine
> defects** no unit test could reach — every double modelled the engine the team believed in.
>
> A telemetry sink with no attached consumer is not telemetry. This file is the consumer, and
> `check_records.py` rules `C2a`/`C2b`/`C2c` are what make it one.

## The rule in one line

**A warning may not survive the close it was raised in.** It is FIXED, ACCEPTED with a reason and an
owning milestone, or ESCALATED. There is no fourth option and no silence.

A skipped or bypassed control is not a warning: it is a row in `docs/control-events.csv`, the one
ledger `make wave-check` counts.

## How to use it

1. A check WARNs → add a row **in the same session**, before the wave closes.
2. Give it an id (`W-001`, monotonic, never reused) and name the **rule that warned**, not the symptom
   — `C2b` counts by rule, so a re-coined name hides a repeat.
3. Set a status. `OPEN` is legal only for the wave you are currently in.
4. At wave close, every row is `FIXED`, `ACCEPTED` or `ESCALATED`. `check_records.py` fails otherwise.

| Status | Means | Requires |
|---|---|---|
| **OPEN** | raised, not yet dispositioned | legal only in the current wave |
| **FIXED** | the cause is gone | the commit or artifact that removed it |
| **ACCEPTED** | shipping with it, deliberately | **a reason AND an owning milestone.** `C2c` fails without both — *"accepted"* with no owner is how a warning becomes permanent |
| **ESCALATED** | the owner decides | the escalation record |

## The counter

**`C2b`: the same rule ACCEPTED three times fails the build.** Not the fourth time — the third.
When `C2b` fires, the answer is never a fourth acceptance: **review the control, or refuse it and
record the refusal** in `docs/refusals.md`.

## Not-yet-observed is not clean

If no warning has fired, the ledger carries a **dated line saying so**. An empty ledger and a missing
ledger look identical in a summary and mean opposite things. `M1` requires this file to exist in a
project; its emptiness must be a claim, not an absence.

---

## Ledger

| id | rule that warned | first seen | path | status | reason + owning milestone |
|---|---|---|---|---|---|
| — | — | — | — | — | *No warning observed as of `<YYYY-MM-DD>`. This line is the report; delete it when the first real row lands.* |

<!-- Example rows — delete these when you file your first real warning.

| W-001 | slopsquat | m1-wave-2 | pyproject.toml | FIXED | the new dependency was a typo of a real package (commit abc1234) |
| W-002 | contract-suite | m2-wave-0 | tests/contract/ | ACCEPTED | no engine in the sandbox; owner runs it at the M2 gate — owning milestone M2 |
| W-003 | coverage-floor | m2-wave-1 | scripts/ | ESCALATED | needs an infrastructure decision; owner ruling requested |

-->

## Cost line

~3 minutes per wave to file and disposition rows; `<0.1 s` to validate.
