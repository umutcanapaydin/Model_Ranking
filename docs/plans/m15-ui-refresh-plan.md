---
record_type: plan
id: m15-ui-refresh-plan
status: draft
process_version: v5.0
date: 2026-09-22
---
# M15 — visual refresh integrated with the current detail screen

**Goal:** make the question, model choices and evidence easy to read and navigate.
**Authorization:** continue and improve the app's interface (owner, translated from Turkish,
2026-09-21; continuation repeated after quota pauses).
**Risk:** MED, existing SwiftUI presentation and localized chrome only.

## Current state and integration

While this session was paused, the owner's tree gained an independently developed M15-W2
detail composer, tests, review fixes and governance records. The final work is based on a fresh
snapshot of that tree. Preserve those changes verbatim, including `Detail.swift`, `Models.swift`,
`DetailTests.swift`, both existing source-contract tests, the 257-test floor and all prior records.
The earlier isolated detail prototype is not delivered and its test results are not final evidence.

## Design

A warm adaptive canvas, forest accent, a clear question composer, and a prominent best-quality
card. Keep the other two pick labels and all evidence/uncertainty disclosures. The whole card opens
the existing `ModelDetail`. Full-ranking rows retain their exact destination facts. Detail facts
become readable cards, still composed exclusively by `detailFacts`.

Alternative: replace the front door with a category dashboard. Rejected because REQ-ASK makes a
single question the primary input. Respect Dynamic Type and dark appearance through semantic fonts
and adaptive colors; no image assets, dependencies, new network calls or score arithmetic.

## File scope and steps

- Update `ios/ModelRanking/ContentView.swift` layout and styles, preserving both detail invocation
  argument lists, request gates, ranking order, disclosures, correction and gap-register behavior.
- Add shared adaptive tokens in `ios/ModelRanking/Design.swift`.
- Append only presentation strings to `ios/ModelRanking/Engine/Language.swift`.
- Add `tests/unit/test_ios_visual_contract.py` for card evidence and whole-card navigation.
- Run existing/new Python contracts, the full Python gates, all Swift tests and a real iOS build.
- Independently review the integration; verify home/detail/navigation/languages in Simulator.
- Transfer only named edits after hash-checking the original files again. No commit or push.

## Boundaries

No API, backend, dependency, test floor, CI or deploy change. Existing M15 detail records are
preserved, not rewritten as this session's work. W-112's floor decision, W-111 governance and
M15-W3 remain open. No milestone/wave-close verdict is implied by the visual refresh.

The earlier prototype found that budget-pick `why_fact` conditionally contains a native floor
(`points`, `Elo`, `ECI`); that may inform W-112's next decision, but it is not silently substituted
for the current detail contract or for `scoreAnchor`.
