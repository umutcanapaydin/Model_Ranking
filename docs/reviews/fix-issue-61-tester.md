---
record_type: review
id: fix-issue-61-tester
status: draft
process_version: v6.6
date: 2026-09-26
seat: independent
---
# Issue 61 independent Tester review

**Reviewer:** Tester, separate session; did not author the implementation or original tests.
**Independent:** yes
**Date:** 2026-09-26
**Commit range:** cce2ced..eed4734, plus the two-line regression-fixture correction below
(integrated by the controller as 91288c9; production source unchanged).
**Risk tier:** HIGH

## Verdict
PASS

The independent generated oracle proves the restored historical rule. The explicit fourth-Tester
regression fixture initially failed to distinguish that rule; this review corrected its inputs
and independently demonstrated assertion red followed by green. No production changes were needed.
Policy and Tester profile were read from protected base cce2ced. Same model family as author;
a separate fresh-context Tester session supplies independence. No second family was requested.

## Acceptance-criterion coverage
- Shared population only, then competition ranks: `ios/EngineTests/CombinePropertyTests.swift:31`
  groups the shared rows by original position and advances by group size; `:74` compares complete
  results over 1,200 seeded cases. `:108` checks 300 transformations adding private rows, rescaling
  positions monotonically, and reversing board selection. D-167/#61 citation is at `:1`.
- Arithmetic rank aggregate, model-id ties: the grouped reference comparator at
  `ios/EngineTests/CombinePropertyTests.swift:55` compares rational averages; production uses
  counts and a summed-rank comparator. Historical explicit fixtures at
  `ios/EngineTests/CombineTests.swift:69`, `:78`, and `:105` distinguish best rank, display names,
  geometric mean and quadratic mean. File-level D-167 citation is at `:1`.
- Original positions, chosen-board order, metadata: complete `CombinedList` equality at
  `ios/EngineTests/CombinePropertyTests.swift:100`, with expected provenance assembled at `:60`;
  explicit historical assertions at `ios/EngineTests/CombineTests.swift:114` and `:127`.
- Ties, missing models, duplicate rows/choices and empty intersections: generated cases at
  `ios/EngineTests/CombinePropertyTests.swift:77` include all these; counters at `:102` prevent
  vacuous claims about the sampled cases. Invalid selections/model lookup are covered by
  `ios/EngineTests/CombineTests.swift:138`, `:146`, and `:167`.
- Historical restoration: `ios/ModelRanking/Engine/Combine.swift:43` is byte-identical to
  1398820. SHA256: `762693dba581da6b7c6121bef106e7f4c18c214cc3ee9fa7a092ae6c5ebeafc2`.
  Sixteen historical tests are restored unchanged; all three new tests remain in the discovered
  manifest. No earlier negative test was weakened or deleted.
- Narrow permissions: `tests/unit/test_ios_client_contract.py:176` names only Combine.swift for
  position arithmetic and `:280` names its `common` receiver. The existing scanner assertions at
  `:210` and the client ordering test passed in the independently run complete Python suite.

## Red-to-green and fault injection

The exact red snapshot's source/test presence was reconstructed locally from 246e41f (test-only
probe present, shipping Combine and historical CombineTests absent). Full Swift suite: 290 tests,
130 assertion failures, all in the new generated-reference test; all other tests passed. This is
an executable symptom reproduction, not a compilation failure.

Review finding, now fixed: the old explicit fixture at
`ios/EngineTests/CombinePropertyTests.swift:70` had whole-board sums a=3, b=5, so both algorithms
returned a,b. It did not prove its comment. Changed it to x=a,b; y=b,u,v,a. Shared sums tie at 3,
so a,b is correct; whole-board sums a=5, b=3 select b,a. Injecting whole-board ranking into the
shipping source now makes this exact test fail with `XCTAssertEqual failed`. Restoration passes.

Independently injected nine further faults into shipping Combine.swift, running only the three
new property tests each time. Assertion failures: best rank 325; rank product 59; squared ranks
71; dense ranks 95; raw positions 223; reversed id tie-break 445; repeated chosen boards 1,200;
repeated rows 664; substituted re-ranked provenance 1,077. All nine were killed; together with
the whole-board fault, 10/10 tested faults were detected. This is advisory finite fault coverage,
not a claim that all possible wrong algorithms are excluded.

Each fault was applied to saved original bytes, executed, restored in a finally block, and
checked byte-identically. No intentional mutation remains. No author mutation logs were used
as proof. Local raw evidence: `tester-mutations.json`, `tester-red-snapshot.log`,
`tester-corrected-probe-red.log`, and individual `tester-*.log` files in the review clone.

## Suite results and coverage

- Independent stable full Python run: 1,505 passed, 23 skipped; 91.45% overall coverage.
  `tester-pytest-final.log`. Artifact required, using a copied advisor.db and this clone's src.
  `scripts/module_coverage_floor.py`: PASS, 41 modules, 60% floor, one existing exemption.
- Independent full Swift suite before correction: 306 passed, zero failures; `make swift-test`
  also passed its discovered-test manifest check (`tester-swift-final.log`).
- Corrected fixture: targeted whole-board mutant assertion RED, then full `make swift-test`
  GREEN, 306 tests and manifest matched (`tester-corrected-swift-green.log`).
- Measured shipping Combine coverage via `swift test --enable-code-coverage` and llvm-cov:
  68/72 executable lines (94.44%), 31/35 regions (88.57%), 15/19 functions (78.95%). The base has
  no Combine module to compare; uncovered defensive/default closures are not claimed covered.
- The first Python run hit four sandbox local-listener PermissionErrors. An escalated rerun
  overlapped the deliberate red snapshot and correctly failed three source/manifest controls;
  that contaminated run is not final evidence. After byte restoration and with no concurrent
  mutation, the entire Python suite passed. Swift required access to Xcode compiler caches.

## Mocks, limits and scope

No external integration or new mock was introduced. The rule is exercised through the shipping
combine entry point. Existing network/Epoch contract skips (23) remain explicit. No network,
service, original owner repository or production database was changed. A reused existing Python
environment was used without pip changes; this is not a new hermetic dependency-install proof.
Generated tests are finite seeded examples, not exhaustive proof; malformed duplicate model
metadata is outside their generator. The production module itself was restored, not redesigned.
The controller owns the final full gate on the integrated tree. No claim is made about inherited
issue #60, W5 UI integration, deployed verification or the phone runtime.

## BLOCKING
- None remaining.

## MINOR
- None remaining.

## Tests added/extended this review
- `ios/EngineTests/CombinePropertyTests.swift:70`: corrected the explicit fourth-Tester fixture
  so the claimed whole-board fault actually changes the result; independently red-to-green.

No new ADRs. No outstanding finding requiring a new issue; the fixture gap was fixed in scope.
