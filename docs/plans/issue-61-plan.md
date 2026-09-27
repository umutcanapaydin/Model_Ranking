---
record_type: plan
id: issue-61-plan
status: draft
process_version: v6.6
date: 2026-09-26
---
# Issue 61 — restore combination with independent ordering proof

Owner direction (translated, 2026-09-26): make the tests green before proceeding to the next stage.
Interactive work-issue; approved scope is combination proof/restoration, not W5 UI or routing.
Risk: HIGH, inherited from W4: product ordering and narrowly named client tripwire permissions.

## Contract and scope

D-167 clause 3 stands: intersect selected boards, competition-rank the shared population on each,
order by arithmetic mean (equivalently sum), tie-break by model id. Preserve original positions,
selected-board order and metadata. Preserve first-occurrence behavior for duplicate choices and
rows from historical `1398820`. No API/network/cache/score arithmetic changes or new dependencies.

Files: Engine/Combine.swift; EngineTests/CombineTests.swift and CombinePropertyTests.swift;
EngineTests/test-manifest.txt; tests/unit/test_ios_client_contract.py; this plan, review, process log.
Current contract: POSITION_ARITHMETIC_PERMITTED is empty; SORTING_PERMITTED names FrontDoor only.
Restore only Combine.swift's position permission and its `common` receiver, as accepted by D-167.

## Red, restoration, proof

1. Reproduce the fourth Tester's whole-board-rank mutant in a TEMPORARY test-target-only
   CombineRedProbe.swift derived from `1398820`, with the precise wrong rank expression. It is
   not product code and is removed by the restoration commit. Run the new tests against it,
   recording assertion failures, not a missing-symbol compilation error; commit that red probe.
2. Restore the historical product source byte-for-byte and its regression suite; remove the
   test-only probe. The new test assertions stay unchanged. Update test manifest by discovery.
3. Independent test reference: group shared entries by original position, assign cumulative
   group sizes + 1, compare rational arithmetic averages. Generate seeded small cases with ties,
   gaps, non-shared entries, duplicates, empty intersections, board and model ordering changes.
   Compare the complete result, not only the leading model.
4. Mutation checks: min rank, product, squares, whole-board counts, raw positions, dense ranks,
   display-name tie-break, repeated choices/rows, changed provenance. Require assertion failures
   and restore byte-identically. This checks that the new proof fails when it should.
5. Independent fresh Tester (protected-base policy), full `make gate`, draft PR, pre-merge.
   No merge or default-branch push. No W5 integration until this slice is green.

Alternative: bundle W5 routing and UI. Rejected because #61's proof is independently reviewable.
The generated reference must not reuse the production rank helper or sum/comparator implementation.
No new rule/permission is implied outside the named file. The existing tripwires continue to scan
all shipping client source and reject stale permissions; mutations test both allowed and forbidden
cases. Tests run on this branch's shipping Swift target, not on a copied production implementation.
