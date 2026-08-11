# HANDOVER — v4.1 provenance material (2026-07-30)

> Append-only provenance for the v4.1 increment, following `HANDOVER-v4.0-material.md`.
> Full record: `General_Pipeline/increment-11-ratification.md` · register **Increment 11**
> (`v4-candidate-register.md`, V4C-29..48). Research: `research/architecture/…-AI1/2/3.md`.

## Source — three architecture research passes, and then something better

Three independent research agents answered a NEW axis ("how is governance machinery BUILT, and what
does it cost at our scale") — AI1 ~90 URLs, AI2 72, AI3 10-weak. Convergence, 3/3: **do not build an
engine** (Temporal/Argo/Prefect class rejected on failure-ownership grounds; replay-based resume is
unsound because LLM steps are non-deterministic); **the field never built the validator** (AGENTS.md
at 60k repos, Spec Kit at 124.3k stars, Kiro — all zero machine enforcement; no project governs its
own process on an engine); **our gates are real, our records are unparsed prose.**

Then the 9-seat council did what no council here had done: **seven of nine seats audited the live
repo instead of the briefing** and found that several ratified controls did not work. That, not the
research, is the reason this cut exists.

## Council

9 seats blind-parallel: permanent 6 (Software, Quality, Security, DevOps, PM, Skeptic) + Architecture,
Platform/DX, Cost/Ops. **15 adopts · 1 GATE · 1 rejection · 3 deferrals.** Owner settled the split
(V4C-38 minimal), chose MINOR-with-repairs over a PATCH, and accepted the Skeptic's binding
cost-line condition. **The chair's own packet contained two factual errors — the gate streak (six,
not five) and the propagation evidence (one verified incident, not three) — both caught by seats
that checked.** Recorded in the ratification as the strongest argument in the batch for
machine-checked records.

## What v4.1 adds

**Repairs (Phase 0):** `check-templates` syntax error fixed and made fail-loud · `scripts/journey.py`
SHIPPED (stdlib, 4 QM-bar steps, unwired steps exit 2) · `cold-start` fails until wired · (GDF repo)
`gdf-check.sh` fail-open on `enabled: True` fixed.
**Records as data (Phase 1):** `scripts/check_records.py` (stdlib-only, zero deps) ·
`schemas/record.schema.json` · validated frontmatter on all root governance records ·
`conformance/` pass+fail fixtures with declared diagnostics · `make check-records`,
`make check-records-selftest` · **`.github/workflows/governance-contract.yml` — the FIRST GATE**
(repo root had no CI at all) · `docs/refusals.md` · schema-narrowness rule in AGENTS.md ·
mechanical propagation (P2 §0 heading, P3 file count) · wave-checklist row 9 gains the run line
(gates run / gates SKIPPED / cost / outcome).

## Caveats for the next maintainer

1. **The gate is not in force until the owner acts ONCE, outside the repo:** make
   `governance-contract` a REQUIRED check on the protected branch, bind it to the intended app,
   disable bypass, and protect the workflow path via CODEOWNERS. Until then it is advisory — and a
   validator a PR can weaken in the same PR is not a validator.
2. **`make check-records` in the PACKAGE scans the project's own records**, which are empty in the
   unfilled starter (that is correct: it reports "scanned 0 records"). The repo-level trail is
   validated by the copy at `General_Pipeline/scripts/check_records.py`. Two copies, one behaviour —
   if you change one, change both, or V4C-44's shared-workflow work becomes urgent.
3. **Blocking scope is the CURRENT package only.** Prior versions are FROZEN by the standing
   versioning rule; `--historical` surfaces their findings as information, never as failures.
   `general_pipeline_v3.3` still shows its missing §0 heading. That is history, deliberately left.
4. **Cost lines are binding (Skeptic's condition).** Any control added from here states
   minutes-when-it-fires, who may bypass, and where the bypass is recorded. A friction budget that
   is never spent is a decoration.
5. **Increment 12 is GATED:** no hearing until V4C-13 bypass telemetry and V4C-25 council telemetry
   report at least once. The measurement window for Phase 1 is one full MAJOR cadence
   (2026-07-30 → 2026-10-30); Phase 2 (V4C-33, 43, 44, 46, 38-minimal) does not start early.
6. **Skeptic's cadence dissent stands in advance:** no v4.1-follow-on CUT is triggered by a
   checklist reaching zero — a cut needs the owner's directive AND the measurement window.
7. **Still owed:** HCS EXPERIENCE.md rev 4 · v3.1 retirement count at the first v3.3+ retro ·
   V3C-104 full format at a second partner · GDF first pilot (now carrying V4C-05/09/10/48) ·
   quarterly differentiator-ledger review 2026-10-30.
8. **Deck REGENERATED this cut** (owner request, 2026-07-30 — superseding the standing
   "deck not regenerated" rule that held from v3 through v4.0). `GP-v4.1-presentation.html`
   replaces `GP-v3-presentation.html` — the deck is **versioned, not accumulated** (the same
   deliberate exception recorded in the repo README since v3). It is a **technical talk for
   developers**, bilingual TR/EN via a single toggle (`t` key or the top-bar buttons), 21 slides,
   self-contained (no CDN, no build step), print-to-PDF friendly. Slides 02–03 are a **glossary of
   our own notation** (V3C/V4C, P-00x, OD-x, GDF-00x, council/seat/chair, the
   doc<guardrail<template<gate hierarchy, A0/A0.5/A1/A2, wave/milestone, citing test, fresh-eyes,
   ⛔ glob, escalate-NOW, fixpack) because that notation is unreadable from outside this project.
   Slides 08–17 are the version-by-version record with real code and terminal output, including
   the four live defects this council found and the day-1 falsification run.
