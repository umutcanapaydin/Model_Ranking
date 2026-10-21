---
record_type: register
id: watchlist
status: ratified
process_version: v7.2
date: 2026-09-23
---
# Watch list — controls removed, and what brings each one back

A list of controls that only grows is not a policy, it is sediment. When this project removes a
control — one DevFlow shipped, or one the project wrote itself — or declines to adopt one, it gets a
row here: what it caught, why it went, and the count that brings it back. The row is how you learn
which controls earn their place and which were added for a one-in-a-million incident.

Retiring a control is also relaxing it to zero: the backtest rule in `docs/closure-checklist.md`
applies. A control you refuse outright goes in `docs/refusals.md` as well.

## Two counters

| counter | question it answers | counting rule |
|---|---|---|
| **`intra`** | *did bringing it back actually work?* | recurrences **since this row's `epoch`**, within this project, counted individually. Occurrences before the epoch are the case for the return, not against it. |
| **`cross`** | *is the failure mode general?* | **distinct projects** (or distinct repositories of this product) where the failure occurred since the epoch. |

`epoch` is the date the row last changed state — removed, or returned. A returned row's counters reset
at its return, because the question changes: before the return you ask *should this come back*, after
it *did the return fix anything*.

## How a row returns

A removed control comes back when `cross` reaches its `returns at`. It returns with the evidence and a
way to show it fires (plant the defect, run the check, see it refuse), or it does not return.

**A returned row is not a closed row.** `intra` keeps counting after the return; a mode that keeps
recurring after coming back is evidence about the *repair*, not about the mode.

If both counters stay at zero, that is a result too: the control was over-fitted to a single incident.

## What the counters do NOT mean

`intra` and `cross` are evidence about a failure MODE, not a score for a project or a person. **A
counter with no cited record is not a counter** — name the issue, commit or record that moved it.

## The list

| id | what it caught | why removed / declined | epoch | `intra` | `cross` | returns at |
|---|---|---|---|---|---|---|
| D-215 | Golden Rule 1 as D-210 wrote it, and D-101's provenance: a board or price served without an open data licence or its publisher's written permission (Epoch's WebDev copy, MMLU/HELM, SWE-bench under CC BY-NC) | Relaxed by the owner's ruling in #376: the app is free and non-commercial, so a public leaderboard's numbers are served when the publisher is credited with a link and its terms do not forbid non-commercial use | 2026-10-21 | 0 | 0 | 1: a publisher objects to being served, or the app takes payment (then SWE-bench's maintainers are written to first, D-215 clause 3) |
