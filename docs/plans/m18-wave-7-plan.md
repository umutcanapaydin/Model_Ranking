---
record_type: plan
id: m18-wave-7-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W7 plan — the issue backlog

**Working plan for `wave/m18-w7`**, deleted before merge. It is added to the milestone by the
owner's instruction of 2026-10-04: "if you will have time you can start with the open issues". The
milestone plan records it in its W7 amendment. The branch is stacked on `wave/m18-w6`.

**Risk: HIGH.** #104 touches `scripts/engine_service.sh`, a security glob (`m18-plan.md` §3). By
D-172 no security pass runs on the slice; the milestone closure's security seat reads it.

## Issues

The open issues triaged `fix-issue`, the reader-visible #112, and three small ones from W6 and W3.

| Issue | What | Phase |
|---|---|---|
| #102 | Whether a pick repeats the quality pick is decided by display name | P1 |
| #103 | The build's run reports keep the effort-unknown counts from before the reconcile | P1 |
| #104 | The launcher tells the operator to run a flag `build.py` does not have | P1 |
| #112 | Raw model ids reach the reader as names, and Claude names come in two word orders | P1 |
| #114 | Reloading `app.adapter.main` in one test file breaks another's `ConfigError` checks | P2 |
| #122 | No Python test fails when a unit test reaches the network | P2 |
| #123 | The launcher's refusal on a serving bound is not run as a script | P2 |
| #105 | No gate checks that a PRD evidence pointer still lands on its test | P2 |
| #119 | The held-out gate does not scan the probe's `.json` sets | P2 |
| #118 | The off-topic probe sets label greetings as searches, against D-169 | P2 |
| #121 | A gap-register save to something other than a file has no test that fails | P3 |
| #124 | Attribution: the Epoch citation's new title (the rest waits for the owner's #88 ruling) | P3 |
| #120 | D-174 does not say which artifact copy a review seat uses | P3 |

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan, and the milestone plan's W7 amendment |
| P1, engine | #102, #103, #104, #112 | Each red first. A repeat is decided by model id (two models sharing a display). The run reports carry one account of unknown efforts. The launcher's message names a command that runs (its `--help` exits 0). No served display equals its raw id where a product name is known, and Claude names have one word order, each held by a test over the served artifact's names |
| P2, tests and gates | #114, #122, #123, #105, #119, #118 | The two test files pass in either order. A planted real request fails the Python suite. The launcher refuses an artifact past a serving bound, as a script. Every PRD `file:line` lands on a test declaration, and the stale ones are corrected. A held-out question in a tuning `.json` set fails the gate. Greetings are labelled `NOT_A_SEARCH` in both off-topic sets, with each change listed |
| P3, small | #121, #124, #120 | A register save to a non-file URL fails a test. Epoch's citation reads "Capabilities & benchmarking". D-174 names the served artifact as the seat's copy |

**The valve.** #112 is the part to cut if the wave runs long: a display table for every raw id
needs each name checked against its maker's own spelling.

## K.8 contracts

No `/v1` field changes. #112 changes the values of `models.display`, which `/v1` already serves.
