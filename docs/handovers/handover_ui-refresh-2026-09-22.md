---
record_type: handover
id: handover-ui-refresh-2026-09-22
status: draft
date: 2026-09-22
---
# UI refresh continuation — 2026-09-22

The owner authorized continuing after quota interruptions and improving the iOS interface.
The visual integration is ready for owner inspection; no commit, push, deployment or milestone
closure was performed. The current M15-W2 implementation and its records are preserved.

## Delivered scope

- `ios/ModelRanking/ContentView.swift`: warm canvas, question composer, forest primary card,
  whole-card detail navigation, clearer ranking rows and fact-card detail layout.
- `ios/ModelRanking/Design.swift`: adaptive shared colors and decorative vendor marks.
- `ios/ModelRanking/Engine/Language.swift`: appended English/Turkish presentation strings.
- `tests/unit/test_ios_visual_contract.py`: evidence/disclosure retention and whole-card navigation.
- Separate plan and independent review: `docs/plans/m15-ui-refresh-plan.md` and
  `docs/reviews/m15-ui-refresh-review.md`. Acceptance evidence and source lines are in that review.

Integration started from a fresh owner-tree snapshot after detecting concurrent M15-W2 edits.
The earlier isolated detail prototype is not delivered. The current fact composer, models,
original tests, Makefile floor (257) and prior governance records remain unchanged.
Transfer uses a named-file allowlist and SHA-256 baseline checks; no original-repository Git use.

## Verification

The final integration ran in a separate local copy using the existing Python environment:

- Python lint and typecheck passed (33 source files).
- Python suite: 922 passed, 12 skipped; total coverage 88.72%.
- Coverage floor, record validation/selftest, install-check, wave-check-all and conformance passed.
  Install was skipped because dependencies were already present; no dependency change was made.
- Swift: 257 tests, zero failures. The existing 257-test floor was not altered.
- iPhone 17 Pro / iOS 26.5 Debug build succeeded; final whitespace-adjusted source rebuilt successfully.
- Independent combined reviewer: 25 focused contracts passed; four omission probes were rejected.
- Simulator: English question submission using Return and send; Mathematics response; primary-card
  detail; Turkish language; all-models list; list-row detail; manual category correction.
- Semantic fonts/adaptive colors were inspected in code. VoiceOver, large Dynamic Type and dark
  appearance have not been exercised on a device; no accessibility certification is claimed.

Evidence lives in the Codex task directory under `work/integration-gates.log`,
`work/integration-swift.log`, `work/integration-xcode-final.log`; final captures are
`outputs/app-home-tr.png` and `outputs/app-detail-tr.png`.

## Open observations and next work

- Runtime routing observation: in Turkish, entering "I want to write code" (owner language)
  selected Chat rather than Coding. Reproduce with the Turkish equivalent displayed in the saved
  home capture; manual Change > Coding worked. The classifier/request path is unchanged by this
  integration. Add a routing regression and investigate this separately; do not claim it fixed.
- Some inherited engine disclosures remain English when Turkish chrome is selected.
- W-112's detail-floor decision, W-111 governance and M15-W3 remain open; this handover does not
  supersede the other author's review/dispositions or close M15.
- No new ADR: this is presentation within the existing contracts. The owner retains commits.
