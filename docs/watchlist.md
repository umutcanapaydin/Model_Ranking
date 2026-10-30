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
| D-230 | D-126's client controls refused a URL made from a string, and `UIApplication`, in every client file but the engine client (INV-62 to INV-76, #107) | Relaxed for one file by the owner's ruling on #484: `SettingsDoor.swift` opens the system's Settings page, pinned whole by `SETTINGS_DOOR_SHA256` and its two expressions by `EGRESS_EXACT` | 2026-10-29 | 0 | 0 | 1: the door's file changes, or a second door is asked for |
| D-215 | Golden Rule 1 as D-210 wrote it, and D-101's provenance: a board or price served without an open data licence or its publisher's written permission (Epoch's WebDev copy, MMLU/HELM, SWE-bench under CC BY-NC) | Relaxed by the owner's ruling in #376: the app is free and non-commercial, so a public leaderboard's numbers are served when the publisher is credited with a link and its terms do not forbid non-commercial use | 2026-10-21 | 0 | 0 | 1: a publisher objects to being served, or the app takes payment (then SWE-bench's maintainers are written to first, D-215 clause 3) |
| D-220 | D-164 / D-179's board guards: an unlinked row compared by its raw name, so any re-spelling read as a row lost and new; and every row lost counted | Relaxed by the owner's ruling in #415: an unlinked row is compared by its spelling key (case and punctuation forgiven, letters, digits and `+` kept), and a cut the owner names row by row in `data/accepted-cuts.yaml` is not a loss | 2026-10-23 | 0 | 0 | 1: a night publishes two different models merged under one key, or a listed cut hides a loss the owner did not accept |
| INV-27 | The Mac engine's launcher (`scripts/engine_service.sh`) refused to start on any problem the startup check reported, a bind beyond loopback with no Host list among them (W-042, #86) | Retired with the launcher by the owner's ruling D-224: the hosted engine is the only engine (D-222), and the hosted engine's own startup check still fails closed (INV-25, INV-26) | 2026-10-25 | 0 | 0 | 1: a Mac engine again |
| INV-28 | Every way of starting the Mac engine bound loopback unless the owner opted in: one `--host` from `MODEL_RANKING_BIND`, the wrapper on loopback unless `--lan`, a reinstall keeping its mode and `--no-lan` closing it (D-171, #86) | Retired with the launcher, the installer and the home-network option by D-224 (D-222). `make run` still binds 127.0.0.1, and its test stays (`tests/unit/test_engine_service.py::test_make_run_binds_loopback`) | 2026-10-25 | 0 | 0 | 1: a Mac engine again |
| INV-29 | The Mac's launchd service ran only a deployed release of `origin/main`, touched nothing under `~/Desktop`, and its wrapper was the owner's alone, mode 700 (D-170, #36, #86) | Retired with the installer by D-224 (D-222); the hosted engine ships only main's tip through `deploy_hosted_engine.sh` (INV-90) | 2026-10-25 | 0 | 0 | 1: a Mac engine again |
| #284 | The Bash guard refused an agent's run of `scripts/install_engine_service.sh` (but its three printing modes, each alone) and any run of `scripts/remove_engine_service.sh`, in any case and through any wrapper: each changed the owner's launchd service | Retired by D-224: #427 deleted the installer and #461 the remover after the owner ran it, so the rule named only files that no longer exist. The owner's patch on `chore/retire-launchd-guard` removes it with its tests; `scripts/deploy_hosted_engine.sh` keeps its own case-insensitive rule | 2026-10-27 | 0 | 0 | 1: a launchd service, or any script that changes the owner's machine, again |
