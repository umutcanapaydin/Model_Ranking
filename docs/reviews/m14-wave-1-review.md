---
record_type: review
id: m14-wave-1-review
status: ratified
seat: independent
date: 2026-09-18
---
# M14-W1 — Code-Reviewer seat

**How this record was produced.** A separate session with no context of the wave's authoring, given
the profile (`subagent-profiles/Code-Reviewer.md`), the plan, `AGENTS.md` §3/§5 and the
`registry.py` module docstring read from the repository rather than from the change (V4C-06). It
was given the author's five claims and told to verify or refute each by running code. It diffed
`src/app/workflows/registry.py` against `.registry_baseline.py`, loaded both registries side by
side, classified all 3,824 live alias and score names through both, ran the whole pipeline twice on
copies of `advisor.db`, and ran the four author-named mutants plus two of its own.

**Verdict: PASS-WITH-FINDINGS.** No BLOCKING. Four MAJOR, five MINOR, two NIT.

## Claims the seat refuted

| Claim | Verdict | What the measurement said |
|---|---|---|
| 19 aliases reconciled to **4** text models; **3** published an inflated price | **REFUTED in part** | 19 aliases and 5 tokens correct, and the three named price moves exact. But **six** families were affected (`+gpt-4o`, `+gemini-2.5-pro`, both price-neutral) and **four** medians moved: `deepseek-v4-flash` `0.105/0.21 → 0.1/0.2` was missed. Distinct pricing aliases is **2,661**, not 2,623. |
| **16** printed prices across 8 of 9 surfaces; order, picks, `eligible_count`, `frontier_size` unchanged | **REFUTED in part** | 8 of 9 correct; order, pick identity, counts and frontier sizes unchanged across all 27 answers — verified. But **21** ranking price cells moved, not 16, and the author's own re-measurement after the review put the full figure at **72 price cells and 50 sentence/fact fields across 16 of 27 answers**. `computer-use` Best Value: `cheaper_by_percent` 20 → 9. |
| The **three** new tests are red against baseline and green after | **REFUTED as stated** | Five tests, not three. Four go red, and only **one** is behaviourally red; the other three fail with `ImportError` on a symbol that did not exist yet, which proves a symbol is new, not that behaviour changed. |
| Four mutants killed | **VERIFIED** | Each dies on the test the author named. **But the seat's own M5 — `continue` in place of `return None` — SURVIVED the full 878-test suite.** |
| No model loses its price entirely | **VERIFIED** | `px_median` 72 → 72, zero models lost, zero un-drops, `models_registered` 74 → 74. |

## Findings and disposition

| # | Finding | Disposition |
|---|---|---|
| MAJOR-1 | The measurement written into the shipped comment was wrong — four models not three, six families not four, and the scope understated | **FIXED.** The comment now carries the seat's figures and says they are the seat's, and the author's error is ledgered at W-093 rather than quietly overwritten. |
| MAJOR-2 | The drop's reason was computed and discarded: 19 guard refusals went into the same flat list as 2,393 genuine registry blind spots, in a list whose purpose is finding drift | **FIXED.** `canonicalize_with_reason` returns the token; `ReconcileReport` carries `modality_drops` and a `drift_dropped` property that subtracts them. Tested through `reconcile()`, the real entry point. |
| MAJOR-3 | The guard compared the alias against the canonical id STRING, so it dropped an image model's own aliases unless a modality word happened to be in its name — `nano-banana-pro`, `seedream-4`, `flux-1-kontext` all fail. The test that claimed to prove future-proofing used `gpt-image-1`, the one fixture under which the bug is invisible | **FIXED.** `ModelRule` gains a declared `modality` field; the comparison is against what the rule states. The test is rewritten around a model named after a banana. |
| MAJOR-4 | `return None` vs `continue` was an unpinned choice; mutant M5 survived the entire suite | **FIXED.** `test_a_refused_alias_does_not_fall_through_to_a_later_rule` pins the choice with a deliberately mis-ordered table. M5 now dies. |
| MINOR-1 | `ruff format` / `black` reject the new token block | **FIXED.** `# fmt: off` / `# fmt: on`, matching `MODEL_RULES` above it. `ruff check`, `ruff format --check` and `mypy` all clean. |
| MINOR-2 | The guard is under-broad against its own rationale: `gpt-4o-search-preview` drops, `gpt-5-search-api` and `o4-mini-deep-research` do not | **ACCEPTED, claim narrowed.** No price effect measured today. The comment now states the boundary instead of implying coverage it does not have; a declared SKU axis is ledgered for M15. |
| MINOR-3 | `embed` cannot match `embedding`; `transcribe` cannot match `transcription` | **FIXED.** Both spellings added. |
| MINOR-4 | A refused alias was reported to REQ-CAN-005 as an "undeterminable effort", which is a different and untrue statement about it | **FIXED,** with a test that was red first. Zero live rows have the shape; the meaning is pinned rather than a behaviour that ships. |
| MINOR-5 | A live-data count sits in a test docstring with no assertion behind it | **ACCEPTED.** Reproduced exactly (2,661 + 1,163 = 3,824). It is context for the reasoning, not a pin. |
| NIT-1 | "stopped at the number a reader reads" understates the blast radius | **FIXED** — see MAJOR-1. |
| NIT-2 | `modality_mismatch` returns `str \| None` used as a boolean | **FIXED** by MAJOR-2: the token now has a real consumer. |

## Gaps the seat named, and what happened to them

Four of the six producers of the hardened invariant had no citing test, and none of the new tests
went through `reconcile()` — the real entry point (V4C-50). One is now covered
(`test_a_modality_refusal_is_counted_apart_from_registry_drift`). `reconcile_plans()` and the
roster path remain uncovered and are queued to W2.

## Carried to M15 (the seat's K.9 list)

- `BuildReport.as_json()` publishes no reconciliation drop count of any kind while `reconcile()`
  computes four; an operator cannot see a 2% collapse in `pricing_matched` from the artifact.
- The only reconciliation floor is `models_registered < 20`. `pricing_matched` and `scores_matched`
  have none.
- `ft:gpt-4o-2024-08-06` and `ft:o4-mini-2025-04-16` reconcile to their base families. Fine-tune
  SKUs are the same defect shape on a third axis, unaddressed and unnamed.
- `data/rosters.yaml`'s documented-drops mechanism is prose only; there is no machine-readable
  expected-drop list anywhere in the repo. That is the root cause of MAJOR-2.
