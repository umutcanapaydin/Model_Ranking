# M3 Retrospective (G.12 — first retrospective; M≥3 rule fires for the first time)

Date: 2026-08-15 · Scope: M3 (W0-W3, commits d703a77..HEAD) · Author: lead agent (fresh-eyes
verdicts cited from committed review artifacts, not memory).

## Discipline verdicts

| Discipline | Verdict | Evidence |
|---|---|---|
| Fresh-eyes per-wave review (K.7/V3C-68) | **PULLED-WEIGHT** | 4/4 waves produced findings (2 BLOCKING + 8 MINOR, all closed in-wave); the W0 `.gitignore` mitigation-clobber catch alone justified the milestone's review cost — third consecutive milestone where the reviewer caught what the author could not |
| install-check M1/M2 (v4.3.1) | **PULLED-WEIGHT** | 23 findings on first run against a repo that had closed two green milestones (m3-wave-0-close.md row 2) |
| Fault-injection incl. mutation probes (V3C-72) | **PULLED-WEIGHT** | 7 faults: 6 RED; the 1 stay-green (cap-boundary `<=`→`<`) forced its mandatory test — the exact failure mode the rule exists for |
| Warnings ledger C2a/b/c (v4.3.1) | **PULLED-WEIGHT** | W-001 routed a scanner false positive to the owner instead of a silent waive; C2c fault-injected RED at W0 |
| Wave-close checklists (V3C-69) | **PULLED-WEIGHT** | 4 filled + committed; the REQ-CAL-001 carry is VISIBLE in a ledger row rather than lost (the v4.3 five-silent-skips class avoided) |
| Curated-data loud-fail (new, D-107) | **PULLED-WEIGHT** | Disputed Google AI Plus price kept OUT of the table at entry; 23 parser tests |
| Live-probe-before-fixture (FP-M2-2 doctrine) | **PULLED-WEIGHT** | Applied to all 9 seed rows (probe date = entry date). The Arena distribution probe failed from this environment (4 attempts) — the doctrine held anyway: nothing was invented, the criterion stayed OPEN and visible until the owner ran the fetch, then closed on real data (docs/reviews/m3-elo-calibration.md). Environment limits changed WHO probed, not WHETHER |
| English rule L1 + .language-allow (V4C-79) | **PULLED-WEIGHT** | Repo-wide sweep at W0; the allowlist's failure mode (documented: proper nouns) was exactly what fired; product Turkish preserved deliberately |
| Council-instead-of-owner (M2 amendment) | **THEORETICAL** | 0 councils convened; the one candidate judgment call (disputed price) resolved by a data rule (exclude + record). Consistent with M2: most "owner questions" are primary-source questions |
| Trust telemetry (V3C-84) | **TOO-EARLY** | First multi-commit milestone; fix-rate/churn computable only AFTER this closure tag exists — M4 closure gets the first real table |
| D-106 agent git + V4C-64 trailers | **PULLED-WEIGHT** | 4 boundary commits, attributable identity + GP-Agent/GP-Task trailers; zero catastrophe-class ops |

## Carried question (posed by this retrospective, answer due M4)

M3's product surface could only SCORE 2 of 9 plans (Gemini links; GPT-5.6* absent from benchmark
sources, Claude/Perplexity pages name nothing). **Question: is the honest-but-thin answer
("7 plans unscored") acceptable product behavior for the iOS app, or does M4 need a
registry+benchmark expansion (and/or provider-page model-roster curation) before the
subscription answer is user-facing?** Owner input shapes the M4 plan.

## Numbers

4 waves · +45 tests (107→152) · 14 review findings closed (10 wave + 4 closure) · 0 criteria
carried — REQ-CAL-001 was carried into the closure session and CLOSED there from the owner's
live fetch · security close PASS (0 BLOCKING) · 0 escaped blockers · 0 tripwires.
