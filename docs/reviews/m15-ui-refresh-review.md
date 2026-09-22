---
record_type: review
id: m15-ui-refresh-review
status: draft
date: 2026-09-22
seat: independent
process_version: v5.0
---
# M15 visual refresh: independent integration review

**Verdict: PASS for the visual integration code/test slice.** No blocking code finding.
This is not M15 closure, a replacement for the existing M15-W2 review, or certification of
unperformed device/accessibility checks.

## Scope and provenance

Combined Code-Reviewer and Tester, MED, Source A profiles. This fresh-context reviewer did
not author the UI or tests. Policy was read from protected base `855b44a`: `AGENTS.md`,
`permission-matrix.md`, `.agents/rules/practices.md`,
`subagent-profiles/Code-Reviewer.md`, and `subagent-profiles/Tester.md` (capitalized paths).
The plan is scope, not policy. Review frontmatter follows the protected-base validator.

Reviewed the final isolated integration at `work/integration`, comparing `ContentView.swift`
and `Engine/Language.swift` against the fresh owner-tree snapshots under `work/original-now`,
not their older Git base. Reviewed new `Design.swift`, `tests/unit/test_ios_visual_contract.py`,
and `docs/plans/m15-ui-refresh-plan.md`. The earlier isolated `ModelDetailView`,
`DetailPresentation`, and prototype tests are not this integration and are not certified here.

The current `Engine/Detail.swift` composer and `DetailSubject` contract belong to the owner's
separate work. This review checks preservation of their call sites, without reauthoring or
claiming their behavior as new work. No original-repository or simulator operations were made.

## Acceptance and preservation evidence

- REQ-DTL-001: `ContentView.swift:780` makes the card the existing detail link's label;
  `tests/unit/test_ios_visual_contract.py:19` checks the destination and model in its label.
  Both `ModelDetail` argument lists (`ContentView.swift:781`, `:984`) are identical to the
  fresh baseline after whitespace normalization. Subject, benchmark, language, anchor,
  close-call margin, secondary benchmark and age are all preserved. Existing exact-argument
  contract at `tests/unit/test_ios_client_contract.py:817` passed unchanged in the focused run.
- Detail evidence: `ContentView.swift:906` still calls only `detailFacts` with identical
  arguments; independent comparison confirmed the whole `facts` computed property unchanged.
  The new layout renders every fact label/value at `:933`/`:935`, optional note at `:939`,
  and the existing caveat at `:946`. It introduces no substitute floor, inferred date,
  price, higher-effort value, or score calculation. Missing-data behavior stays with the
  existing composer; no prototype missing-data rule was transplanted.
- REQ-CMP-001/002: card scale and familiar price remain beside the figures at
  `ContentView.swift:819` and `:820`. The new test at
  `tests/unit/test_ios_visual_contract.py:9` also checks why/evidence/trade-off rendering.
  Reviewer independently omitted scale, price, evidence and trade-off expressions from
  in-memory source strings: all four omissions failed this test; the original passed.
- REQ-CMP-004 and rank/anchor propagation: `ContentView.swift:809` and `:878` use the same
  `figuresLine` parameters as the baseline. Rank calculation still uses the complete ranking
  at `:1040`; filtering and scroll reset are unchanged. Existing source contract at
  `tests/unit/test_ios_client_contract.py:763` passed.
- REQ-ASK/REQ-GAP and disclosure invariants: independent text comparison confirmed the
  `submit`/`ask`/selection/load implementation region unchanged. The existing request gates,
  route correction, and local storage remain; privacy tests at
  `tests/unit/test_router_hints.py:125` and `:198` passed. The home classifier remains at
  `ContentView.swift:504`; its existing reachability check at
  `tests/unit/test_ios_client_contract.py:92` passed. No added URL/network operation appears
  in the changed presentation files.
- Localization/accessibility: the prior `Language.swift` content is an unchanged prefix;
  new chrome begins at `Engine/Language.swift:432` with English/Turkish branches.
  `Design.swift:5` uses adaptive colors; `:37` hides the decorative vendor initial.
  Semantic fonts and wrapping are used for model names and fact text; send retains its
  accessibility label and a 46-point frame. Runtime VoiceOver, large Dynamic Type, dark
  appearance, and Return-key behavior were not independently exercised.

## Independent checks

Executed in the isolated integration:

```text
PYTHONPATH=src /Users/umutcanapaydin/Desktop/ILGAR/model_ranking/.venv/bin/python -B -m pytest tests/unit/test_ios_client_contract.py tests/unit/test_ios_visual_contract.py tests/unit/test_router_hints.py --no-cov -q
25 passed, 1 warning in 0.31s
```

The warning is the existing Starlette/httpx deprecation. The original path supplies only
the Python interpreter; tests ran against the integration. No full Python coverage or Swift
suite was independently rerun for this visual-only integration. Root owns full 257-test
Swift, complete Python, Xcode build and simulator evidence. Previous prototype test counts
are not final integration evidence.

Read-only byte comparisons confirmed `Makefile`, `ios/EngineTests/DetailTests.swift`, and
the other author's `docs/reviews/m15-wave-2-review.md` match their fresh snapshots exactly.
The Makefile floor remains the owner's 257; the earlier prototype's 253 adjustment is not
part of this work. No new Swift tests or backend/API/dependency/build/CI change is introduced.
All four negative source probes were in memory; no implementation/test files were mutated.

## Limits and nonblocking follow-up

The question field changes from single-line to `axis: .vertical` at
`ContentView.swift:238`. Its submit handler and visible button remain, but source checks
cannot establish actual Return-key behavior; include Return and send in the controller's
UI smoke check. No new code-level failure was reproduced here.

The final plan preserves W-112's floor decision, W-111 governance, and M15-W3 as open.
This review does not change the other author's detail-requirement disposition. No new ADR,
commit, push, deployment, or milestone-close declaration was made. Only this new review
record was written by the reviewer.
