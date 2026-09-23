---
record_type: plan
id: m16-wave-4-plan
status: draft
process_version: v6.0
date: 2026-09-23
---
# M16-W4 plan — the updater keeps every list current

**Working plan for the `enhancement/m16-w4-lists-current` pull request.** DevFlow's
`/work-enhancement`: this document lives on the branch and is deleted before the owner merges.
Milestone plan: `docs/plans/m16-plan.md` §2 W4, which this wave REPLACES (owner, 2026-09-23, below).
The code phases start once M16-W3 (PR #3) is merged, because they touch the same refresh and build.

## Goal

A model that appears on the boards and in the price feeds reaches the lists without anyone editing
the code, and every board the product reads is fetched by the nightly refresh itself.

## Why this wave, and why now (measured 2026-09-23 on a copy of the served artifact)

- **Nine of nineteen sources are never fetched by the refresh.** The Epoch boards come from a
  bundle directory the owner downloads by hand (`MODEL_RANKING_EPOCH_DIR`); without it every night
  CARRIES them (D-156). They expire 30 days after their last arrival, and eight surfaces drop
  with them. The bundle is a public CC-BY download (`https://epoch.ai/data/benchmark_data.zip`,
  2.3 MB) that the Mac fetches fine; the owner-fetch rule dates from a sandbox that got HTTP 403.
  A fresh bundle grows AIME 238 → 291 rows, GPQA 263 → 313, ARC-AGI 168 → 213, DeepSWE 49 → 68,
  WebDev 102 → 124.
- **Epoch changed its layout.** `epoch_capabilities_index.csv` is now
  `epoch_capabilities_index/eci_scores.csv`, with its score column renamed (`ECI Score` → `eci`)
  and confidence intervals added. `everyday`'s primary board would be carried from the old file
  until it expires, and nothing says why.
- **Half of all score rows match no model: 1,450 of 2,834.** The registry is a hand-kept rule
  table (`src/app/workflows/registry.py`, REQ-CAN-001 "never guessed"). GPT-6 Astra has rows on
  Arena and five Epoch boards and prices on LiteLLM, and it is on no list. So are Claude Opus 5.5,
  Qwen 3.6/3.7, Kimi K3, Grok 4.3 and GLM 5.3.
- **A variant leak.** `claude-fable-5`'s rule matches `claude-fable-5-1`, so Fable 5.1's prices
  fold into Fable 5 (REQ-CAN-002's defect class).

## The owner's rulings this plan carries (2026-09-23, in session, translated from Turkish)

1. **Order.** W4 becomes "the updater keeps every list current"; the source expansion (Arena's
   category slices first) and the combined lists routed by Apple Intelligence are M17's subject.
   The old W4 ("what people ask", a droppable measurement) moves to M17 with them.
2. **"Never guess" is superseded.** *"'Never guess' was something like v1; we are maybe at v3 by
   now, and the app's main purpose has changed a little. If it is on a list, the list wins; but
   when we cannot give anything, I cannot call it guessing any more -- we will present the list we
   derived from the data as a result of measurements, our own list. Roughly you could call it an
   estimate, but that is what it is."* This wave applies it to the registry; D-157 records it.
3. **Data licences: keep, and record.** The research record found three sources whose terms may not
   allow a commercial product (below). The owner ruled to keep them for now and record the risk,
   to be resolved before a commercial launch. W-129.

## Scope

**In.**
- The refresh downloads the Epoch bundle itself, safely: HTTPS, a size cap, no path escapes
  (zip-slip), no archive bombs, into scratch beside the artifact, removed after the cycle.
- The ECI board reads the new layout. A declared board missing from a bundle that DID arrive fails
  loud as layout drift, instead of being carried silently.
- Registry derivation, under ruling 2: the curated rules still win. A name no rule matches is
  normalised by a fixed grammar and registered as a DERIVED model when the same derived id has
  both a price and a score. The derived id keeps every variant token, so a variant never merges
  into its parent by construction.
- The Fable 5.1 leak fixed in the curated table.
- `/health` and the build report count unmatched names and derived models, and list the top
  unmatched names, so the curation that remains is visible.
- Records: D-157 (supersedes REQ-CAN-001's "never guessed" clause), W-129 (data licences), the
  research record `docs/research/source-expansion-2026-09-23.md`, the amended M16 plan.

**Out.** New boards and new surfaces (M17). Arena category slices (M17 P1). The Apple Intelligence
routing taxonomy (M17). Anything the app shows (`/v1` is unchanged unless decision 2 says so).

## Decisions — ruled by the owner 2026-09-23, before any code (all three as proposed)

1. **The derivation threshold.** Ruled: a derived model needs at least one price row and at
   least one score row under the same derived id, which is exactly what it needs to rank. Nothing
   that cannot rank is registered.
2. **Whether a derived model says so to a reader.** Ruled: engine-side only, like D-156's
   carry: `/health` and the build report name derived models; `/v1` and the app do not change.
   The list IS the product's own derived list (ruling 2), so marking each row adds noise.
3. **The Epoch acquisition clock.** Ruled: the refresh record's `sources_last_ok` for
   `epoch-benchmark-data` becomes the acquisition clock, and `data/epoch-source.yaml` keeps only
   the URL. The CI staleness step for it then reads nothing hand-kept.

## Phases — one reviewable slice each, gates green after every one

- **P0 — records.** This plan; the research record; the M16 plan amendment; W-129; D-157
  (proposed). *Check:* `make check-records`, conformance.
- **P1 — the bundle is fetched by the refresh.** Red first: a cycle with no `--epoch-dir` fetches
  a fake bundle and ingests it; a zip with `../` members, an oversize member or a non-zip body is
  refused, and the boards carry. *Check:* the nine Epoch sources are in `sources_last_ok` after a
  cycle with no owner-fetched directory.
- **P2 — the ECI layout, and drift fails loud.** Red first: the new layout ingests; a present
  bundle missing a declared board reports drift by name. *Check:* `everyday` arrives, not carries.
- **P3 — the curated leak.** Red first: `claude-fable-5-1` resolves to Fable 5.1, not Fable 5.
- **P4 — derived registration.** Red first: GPT-6 Astra (price + score) registers as derived and
  ranks; a name with only a price does not register; `gpt-6-astra-mini` never merges into
  `gpt-6-astra`; every curated rule still wins over derivation. *Check:* unmatched score rows on a
  fresh build fall from 1,450 of 2,834, with the number recorded.
- **P5 — disclosure.** `/health` and the build report name derived models and the top unmatched
  names. *Check:* `test_nightly_refresh.py` reads them.

## Risk: HIGH

A registry change moves what every surface ranks, and P1 opens an untrusted archive from the
network. HIGH gets Code + Tester and a pulled-forward security pass on P1 (the archive handling).

## Research this plan rests on

`docs/research/source-expansion-2026-09-23.md`: the 80-file Epoch inventory, the licence findings
behind W-129, and the M17 candidates.
