---
record_type: wave
id: m14-wave-1-close
status: draft
process_version: v5.0
date: 2026-09-18
---
# Wave-Close Checklist — M14 Wave 1 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The licence, the board, and the population.** The wave was planned to answer two questions before
W2 is allowed to define a surface: may we serve this board, and how many of its models can this
product actually rank. Both are answered. A third thing was found on the way and fixed, and it is
the larger result.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m14-plan.md` §2 — "W1 — The licence, the board, and the population (risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first verified by swapping the baseline `registry.py` in: `4 failed, 12 passed`. **One of those four is behaviourally red** (`test_a_modality_variant_is_not_its_text_family`, listing the real leaks); the other three raise `ImportError` on a symbol that did not exist yet, and the seat was right to refuse that as red-green evidence. After the fix and the review round: `882 passed, 13 skipped` | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester separately | Code-Reviewer ran: `docs/reviews/m14-wave-1-review.md` (`seat: independent`, separate session, no authoring context, policy read from the repo and not from the diff), returning 4 MAJOR / 5 MINOR / 2 NIT, all dispositioned. **Tester seat NOT RUN — ledger row L2**, so this row is WAIVED and not green | WAIVED |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | **WAIVED 2026-09-18 — ledger row L3.** Under D-141 (`docs/decisions.md`, proposed at M13 and still unratified) a HIGH wave owes this pass whatever its author believes it touches. The slice is `src/app/workflows/registry.py` — no auth, PII, payment, crypto or migration surface — and the waiver is recorded here rather than argued away | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted byte-identical | **NO-ENVIRONMENT for the independent half (L2): no second reviewing session was convened for the Tester seat, and the author cannot supply fresh eyes on his own code.** The injection itself WAS performed, by the author, against `src/app/workflows/registry.py`, on copies, with the file restored byte-identical after each trial. Five mutants, five killed: guard disabled; blanket denylist ignoring the matched rule; token list reduced to `("image",)`; segment boundary replaced by substring; and `continue` in place of `return None`. **The last two are the ones that matter**: the substring mutant survived the first test set, and the `continue` mutant survived the seat's run of the entire 878-test suite. Both now die | WAIVED |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-SRC-010 — licence, no code. REQ-IMG-001 — measurement, recorded below. The correctness work is REQ-CAN-002's, and `test_a_modality_refusal_is_counted_apart_from_registry_drift` enters through `reconcile()`, the real entry point, after the seat found every new test calling `canonicalize` directly (V4C-50) | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None. This is a data-correctness control, and its negative half is `test_the_text_model_itself_still_reconciles` — the guard must not become a blanket drop | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None performed. Mutation trials ran on a staged copy of the tree, never on `src/app/workflows/registry.py` in place, and the file was rewritten from an in-memory original after each trial. No commit of any kind was made — see L1 | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | REQ-CAN-002 extended from the SIZE axis to the MODALITY axis. `canonicalize` is the sole enforcement point; `grep -rn canonicalize src/ scripts/ \| grep -v registry.py` returns nothing, so every consumer inherits it with no second implementation. Six producers enumerated by the seat; two now carry citing tests, and `reconcile_plans()` plus the roster path are queued to W2 | ✅ |
| 9b | Scope: planned vs delivered vs deferred | **Planned:** licence review, an ingest client for the image-editing board, and the ranked-population count. **Delivered:** the licence answer, the population count, and an unplanned correctness fix (W-092) with its review. **NOT delivered: the ingest client.** The plan's own stop condition in `docs/plans/m14-plan.md` §0 fired — see §"The measurement" — and writing a client for data the product cannot yet rank would have been building past a red light. Deferred to W2 with the owner's decision attached | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | Within. Two source files: `registry.py` +~90 lines, `tests/unit/test_registry.py` +~200 lines of tests | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 882 passed / 13 skipped (unit + integration), ruff check, ruff format --check, mypy, check_records (96 records, PASS) · gates NOT RUN: make check as a whole, swift-test, xcodebuild, ./runner, make lint over the full tree, conformance — see L4 · outcome: shipped to the working tree, uncommitted, unsigned` | WAIVED |

## The measurement this wave existed for

**REQ-SRC-010 — the licence. Clean, and cheaper than planned.** The image-editing board is not a new
source: `image_edit` is a config of `lmarena-ai/leaderboard-dataset`, the dataset
`src/app/clients/arena.py` already reads under CC-BY-4.0 through the documented Hugging Face
datasets-server, with attribution already carried into every export (REQ-ING-008, D-101). Its
columns are identical to the `text` config the project has parsed since M2. **No new licence review
is owed** — the Stage-0 gate for this dataset was passed at M2 and the grant covers every config.
The Artificial Analysis trap recorded as Finding 5 does not apply, because we are not reading them.

**And the dataset carries 22 boards, not one.** `agent`, `agent_steerability`,
`agent_tool_hallucination`, `document`, `image_edit`, `image_to_video`, `search`,
`search_factuality`, `text_factuality`, `text_to_image`, `text_to_video`, `video_edit`, `vision`,
`webdev` and their style-control variants. The project reads two of them. That is the cheapest
coverage this product will ever buy and it is recorded here because M15 should start there.

**REQ-IMG-001 — the ranked population. It is ZERO, and the plan's stop condition has fired.**

The `image_edit` board's `latest` split carries 97 rows over 55 distinct models. Of those 55:

- **0 reconcile to the registry.** The registry is 74 text models; it has no rule for `flux-2-pro`,
  `seedream-5.0-pro`, `nano-banana-pro`, `reve-2.1` or any other image model, and should not — a
  rule for a model that cannot rank is dead code by this table's own standard.
- **0 carry a price median.** `px_median` is `(in_m, out_m)` — per **million tokens**. An image
  model is priced per image or per pixel. The column cannot represent it.

So the surface cannot be defined over today's artifact, and the plan says to say so rather than ship
a ranking of four models.

**But it is not a dead end, and this is the number that decides M14.** The pricing source the
project already ingests carries the missing prices: LiteLLM's
`model_prices_and_context_window.json` holds **338 image-related entries** with
`output_cost_per_image`, `input_cost_per_image`, `input_cost_per_pixel` and `mode:
image_generation`. Matched against the board: **8 exact matches and about 11 more under loose
matching** (excluding two false positives — `kling-image-o1 ~ o1` and
`gemini-2.0-flash-preview-image-generation ~ gemini-2.0-flash`, both of which are the W-092 defect
shape in reverse and must not be allowed to reconcile).

**A ranked population of roughly 17–19 of 55 is achievable**, and what stands between here and there
is two pieces of work, neither of which is a benchmark problem:

1. **Registry rules for image models**, declaring `modality="image"` — the field this wave added.
2. **A price column that is not per-token.** `pricing` has `input_per_m` / `output_per_m` only, and
   the LiteLLM ingest filters image modes out before they reach it. This is a schema change and it
   reaches `px_median`, `rank.py`'s `blended_per_m`, the budget eligibility rule and every
   trade-off sentence. **It is larger than the surface it enables, and it is the owner's call.**

## Ledger rows

- **L1 — no commit was made for this wave.** `AGENTS.md` §3: an agent commit on main is A1 and needs
  an explicit owner ADR; none exists. The owner was asleep and had instructed the work to continue
  (the M13-W1 L2 precedent). The working tree carries the change; the milestone commit is his.
- **L2 — the Tester seat did not run, and the fault injection was done by the author.** K.7's
  requirement is a seat that did not write the code. The Code-Reviewer seat was genuinely
  independent and its findings are in the record; the Tester seat was not convened. **This matters
  more than usual here** because the author's own mutant set missed the one the seat found by
  running its own (`continue` vs `return None`), which is exactly what a second seat is for. Owning
  milestone: **M14**, and it closes in W2 or the milestone closes saying it did not.
- **L3 — the pulled-forward security pass was not run.** Under D-141 as proposed, a HIGH wave owes
  it. D-141 is unratified, which is itself an open M13 item. This is the fourth consecutive
  acceptance of V3C-78 in two milestones; under `C2b` the control is already under review and D-141
  is that review. Recorded so the count is honest.
- **L4 — `make check` was not run as a whole, and no Swift or iOS gate ran at all.** The session had
  no Xcode and no macOS shell: both available shells are Linux. The Python half was run in full
  (882 passed) with `ruff`, `mypy` and `check_records`; `swift-test`, `xcodebuild`, `./runner` and
  the conformance legs did not execute. **This wave changes no Swift and no iOS file**, so the risk
  is bounded — but "bounded" is a reasoned claim and not a measurement, and the owner's `make check`
  is what turns it into one.
- **L5 — the author's own measurement was wrong and the seat caught it.** Recorded as W-092/W-093 in
  `docs/warnings.ledger.md` rather than silently corrected, because the verification that produced
  the wrong number was a comparison that could not fail, which is this project's most-recorded
  defect shape.

## What this wave hands to W2

1. **A decision for the owner:** extend pricing to a per-image basis (schema change, reaches the
   budget rule and every trade-off sentence), or define the image-editing surface without price and
   amend the rule that the engine only ranks models somebody can buy. There is no third path.
2. A guard that is ready for image rules: `ModelRule.modality`, with a test written around a model
   named after a banana precisely so the next rule is not forced to spell a modality into its id.
3. Two uncovered producers — `reconcile_plans()` and the roster path — and a roster file whose
   documented-drops mechanism is prose only, which the seat named as the root cause of MAJOR-2.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-18 · Wave commit range:
`c0b71c6..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/workflows/registry.py
                tests/unit/test_registry.py (5 new tests)
                docs/warnings.ledger.md (W-092, W-093) · docs/decisions.md (D-142, D-143)
                docs/plans/m14-plan.md (new) · docs/plans/m14-wave-1-close.md (new)
                docs/reviews/m14-wave-1-review.md (new)
                docs/research/question-coverage-2026-09-18.md (new)
                docs/closure-report-m13.md (§0 item 1 discharged) · note.txt

K.8 contracts:  NONE moved. `/v1` payload untouched. One public symbol ADDED
                (`registry.modality_mismatch`); `ModelRule` gains a defaulted `modality` field, so
                every existing construction is unchanged. `canonicalize()`'s RETURN MEANING widened
                — `None` now covers a refused match as well as an unmatched name — and that is the
                change the seat asked an ADR for; it is recorded here and carried to W2 rather than
                written as one, because the reason-carrying accessor added in the same wave makes
                the two countable apart.
```
