---
record_type: wave
id: m6-wave-2-close
status: draft
process_version: v5.0
date: 2026-08-17
---
# Wave-Close Checklist — M6 Wave 2 (one serializer; the product speaks English)

> **STATUS: NOT CLOSED** — the fresh-eyes review returned **BLOCKING** and its fix delta is back
> with the same seat. Two BLOCKING, and both are the same lesson in different clothes:
>
> 1. **D-118 was not done, and the migration had followed the GATE rather than the policy.** Four
>    ASCII Turkish fragments were still shipping — one rendering a single sentence in two languages
>    — because `L1` detects an alphabet, and every string that carried a Turkish-specific letter had
>    been translated while every ASCII one had not. Three tests were left pinning the survivors in a
>    file whose exemption this wave had just removed. **This ADR's own "mitigation" paragraph claimed
>    a guard that does not exist**; it is corrected in `docs/decisions.md` and the gap is W-019.
> 2. **The subscription CLI rendering was the one path not routed through the new serializer**, so
>    deleting `equivalent_plans` from the shipped JSON left 308 tests green — the identical defect
>    the W1 review found in the adapter, reproduced one wave later in the sibling path, inside the
>    wave whose purpose was to make it impossible.
>
> **Scope variance, declared up front.** The signed plan's W2 was the serializer, W-002, W-010 and
> the two M5 security deferrals. The owner then ruled (D-118) that the payload and query vocabulary
> are English, which was not in the plan. It landed here rather than in a wave of its own because
> the serializer freezes user-facing strings into one contract, and freezing them twice — once in
> Turkish, once in English — would have been the more expensive order.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches authz/secrets/crypto/input-parsing/egress) — V3C-78 | `docs/plans/m6-plan.md` §3 W2 and §4 both record **MED**. The diff adds no authz, secret, crypto or egress path; it changes serialization and user-facing strings. The D-118 vocabulary change touches curated-data VALIDATION (`plans.py`), which is input parsing — but of a repo-committed file with no untrusted producer, the same boundary W-005 is ledgered against. Tier held at MED; the reviewer is asked to challenge that in row 3 | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) — V3C-68 | Parity tests written FIRST and confirmed RED on the real disagreement (`test_the_csv_export_carries_the_same_attribution_as_the_json`, `test_the_csv_metadata_does_not_corrupt_the_table`), then implemented to green. W-002 and W-010 each reproduced with a failing test before their fix — W-010's red state was `effort_unknown == 0` against a suffix-bearing row. Three self-review corrections, all caught by fault injection rather than by reading: a scaffold that masked dropped fields, an attribution test that compared the two halves to each other instead of to what the run owed, and a contract test that checked a field existed without checking it said anything | ✅ |
| 3 | Review per tier: LOW/MED → ONE combined reviewer; HIGH → Code-Reviewer + Tester separately — V3C-78. **v3.3: reviewer countersigns 2 randomly-chosen rows of THIS checklist against the actual artifacts (anti self-attestation)** | **RAN 2026-08-17** — `docs/reviews/m6-wave-2-review.md`, verdict **BLOCKING**: 2 BLOCKING / 8 MINOR / 3 K.9, tier confirmed MED. It countersigned rows 5, 6 and 9c and found row 5 partly overstated (the adapter re-enumeration mutant is RED only when the re-enumeration is INCOMPLETE — a complete hand mirror stays green), row 6 overstated on two of four claims (the CLI/API parity test never invokes the CLI; the `L1` fault injection proves the gate fires on a letter, not that the property holds), and row 9c **pessimistic** — the `cap_dusuk` mapping is covered by four tests, two through the live CLI, so W3 need not spend on it. Fix delta returned to the same seat. The CONTROL ran; the ROW is not satisfied until the re-review clears, so it is ledgered open as W-018 rather than marked done — the review returning BLOCKING is the control working, not the row passing | SKIPPED |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE — V3C-68/F15 | N/A — 2026-08-17. `docs/plans/m6-plan.md` §3 tags W1 ("MED + a pulled-forward security pass") and W3 ("HIGH, migration") for security passes and tags W2 for neither; W3 carries the migration and the untrusted-input guard. The Stage-4.0 closure review in `docs/closure-checklist.md` still covers this wave's surface. Recorded rather than left blank because F15 is the failure mode where a plan tag quietly disappears | N/A |
| 5 | *(countersigned — see row 3)* Tester fault-injection on the 1–2 most load-bearing behaviors: break → RED confirmed → reverted byte-identical (md5); every stay-GREEN fault got its mandatory new test — V3C-72/F5 | **8 mutants, 8 killed; 3 stayed green on first contact and each got its mandatory test.** The first three were named by the W1 reviewer as the CONDITION for accepting this work — *"its parity test must be shown RED on exactly these three deletions, not merely green afterwards"* — and all three are RED: dropping `stale_notice`, dropping `close_call`+`effort_mix_notice`, and re-enumerating fields in the adapter. Plus LIC-1/LIC-2 (CSV loses its attribution / cites the catalogue), W-010/W-010b (the counter goes silent / a suffix is falsely reported classified), REC-014 (`equivalent_to` emptied). **The three that stayed green are the interesting record:** (a) dropping two disclosures was invisible because a scaffold of `None`s replaced them — a default that hides a missing field is the mirror problem wearing a different hat, now removed; (b) the catalogue swap was invisible because the test compared the CSV to the JSON, and the mutant corrupted both identically — it now checks both against `attributions_for` computed independently; (c) `equivalent_to=""` was invisible because the test asserted the field existed, not that it meant anything. All files md5-identical before and after every round | ✅ |
| 6 | *(countersigned — see row 3)* Every acceptance criterion touched has a citing test entering through the LIVE entrypoint (not a unit shim) — V3C-02 + V3C-73/F6 ("built ≠ wired") | **REQ-API-003** → `test_every_recommendation_field_reaches_the_v1_answer`, `test_every_pick_field_reaches_the_v1_answer`, `test_the_cli_and_the_api_render_the_same_run_identically`, `test_a_present_disclosure_survives_serialization` — all through `TestClient(app)`, and all three field lists derived from `dataclasses.fields`, never hand-written. **REQ-LIC-002** → `test_the_csv_export_carries_the_same_attribution_as_the_json`, `test_the_csv_cites_exactly_what_the_json_cites_no_more`, `test_the_csv_metadata_does_not_corrupt_the_table`, `test_the_two_export_halves_carry_the_same_rows`. **REQ-REC-014** → `test_equivalent_plans_carries_group_structure`, `test_equivalence_members_name_their_plan_and_price`, `test_each_equivalence_group_names_the_pick_it_belongs_to`. **W-010** → `test_an_unclassifiable_effort_suffix_is_counted_not_silently_defaulted`, entering through `ingest_swebench`. **D-118** → the whole suite, plus the `L1` gate itself, fault-injected: a Turkish string in `recommend.py` makes `check-records` fail and the file restores md5-identical. All in `tests/unit/test_serializer_parity.py` unless named otherwise | ✅ |
| 7 | New/changed security invariants added to the milestone invariants list with their NEGATIVE test — V3C-74/F7 | One changed, none added: **an export cites the sources it carries, never the catalogue** (W4 BLOCKING-2's rule) now binds BOTH halves of `export_ranking`, with `test_the_csv_cites_exactly_what_the_json_cites_no_more` as the negative test — mutant LIC-2 RED. No auth, PII, crypto or migration path is touched by this wave | ✅ |
| 8 | No `git checkout`/`restore` was run on uncommitted work this wave (reverts were in-place + hash-verified) — V3C-06/F17 | Every fault-injection revert wrote the original text back with `Path.write_text` and asserted md5 identity per file, including across a multi-file run. No `git checkout`, `git restore` or `git stash` at any point. Two commits were made under **D-117** (scoped inter-wave authority, agent identity, green gates only) and pushed | ✅ |
| 9c | **Invariant hardening (v3.5, V3C-101):** if this wave hardens a shared invariant (auth/tenancy/money), the producer list is enumerated FROM CODE with a citing test per producer | Enumerated from code and the answer is partial, so it is recorded rather than claimed clean. The hardened invariant is the attribution obligation; its producers are the two halves of `export_ranking` (`rank.py`), both now covered. The MONEY-adjacent surface this wave touched is the budget vocabulary: producers are `data/plans.yaml`, `plans.py`'s validation, `subscribe.py`'s cap lookup, `recommend.py`'s `BUDGETS` and the `/v1` query — all migrated together, and `test_plans_ingest` covers the validation. **Tracked gap:** `plan_config`'s `cap_dusuk`/`cap_orta` columns still carry the old spelling behind the new vocabulary, deliberately (D-118), and nothing tests that the mapping between the two stays correct. Owning milestone: W3, where the migration is | ✅ |
| 9b | **Scope & checkpoint (v3.3, V3C-90/OD-4):** scope row appended — planned vs delivered vs deferred vs the signed plan; owner's labeled checkpoint commit exists for this wave | **Planned** (m6-plan §3 W2): extract the serializer with the parity test shown red first; `evidence_dating` into the payload; CSV attribution; `equivalent_plans` group structure; W-010 red-test intake. **Delivered:** all five. **Added by owner directive, not in the plan:** D-118, the English contract — three source files, five test files, the curated data file and the query vocabulary. **Deferred:** nothing from W2's plan. **Checkpoint commit:** made by the agent under **D-117**, which the owner ratified this session in place of the per-wave owner checkpoint V3C-90 assumes | ✅ |
| 9a | **Economy (v3.2, V3C-85/86):** wave diff within ~≤400 changed lines OR variance noted; projected token spend within the milestone budget line | `git diff f3c75b9..HEAD --stat` — **~370 changed lines across 12 files** for the serializer work, plus the D-118 migration which touched 20 files mechanically. Within the soft bar for the reasoned work; the migration is counted separately because a vocabulary rename is not design surface. Token spend is **over** the plan's ≈80k W2 line, driven by D-118 arriving mid-wave; variance carried to the milestone gate rather than absorbed silently | ✅ |
| 9 | **Skipped/waived/BYPASSED ledger + run summary (v4.1, V4C-13 + V4C-40-lite):** RUN LINE first, then every check that did not run | `gates run: lint · typecheck · black · mypy · test (308 passed / 12 skipped, was 296) · check-records (30 records PASS) · check-records-selftest · install-check · conformance (6 of 7) · wave-check · fault-injection (8/8 killed) · gates SKIPPED: fresh-eyes review (row 3) — PENDING, not waived, and the wave is held open for it; pulled-forward security pass — N/A by plan, not skipped; conformance test-documented-commands remains RED on three historical records, which is GPF-001 handed back to GP and is not this wave's · tokens/cost: over the ≈80k W2 line, see 9a · outcome: SHIPPED to review-pending, NOT closed`. **No pressure bypass this wave.** Nothing was skipped to go faster | ✅ |

**Escaped-blocker tripwire (V3C-78):** none escaped — the wave has not closed.

## What this wave changed about how the product is built

**There is no longer a second place to write a field name.** The `/v1` adapter used to enumerate all
nineteen `Pick` fields and all ten `Recommendation` fields by hand. It was correct on the day it was
written and structurally unable to stay correct — the W1 review proved it with one deletion. Now the
CLI and the API both call `serialize.recommendation_json`, which walks the dataclass, and the adapter
adds only what the engine cannot know: which surface this is, how fresh its source is on a wall
clock, whether its evidence carries dates, and why it has no picks.

The first attempt at that still had a mirror in it — a scaffold of `None`s built from the dataclass,
merged under the engine's output "for safety". Fault injection found it immediately: deleting two
disclosures from the serializer left every test green, because the scaffold supplied them as `null`
and a dropped field looks exactly like a null one. **A default that stands in for a missing value is
the same defect as a hand-written mirror, and it is harder to see because it reads as robustness.**

## What the review added, after the record above was written

The wave's own thesis — *no second place to write a field name* — was true of the two renderings it
looked at and false of the third. The subscription CLI kept its own `asdict` call, so the defect the
wave existed to remove survived in the sibling path, and all three REQ-REC-014 tests inspected the
in-memory object rather than the shipped text. Two of them were `dataclasses.fields` reflection that
would pass against an empty implementation.

The D-118 finding is the sharper one. **A migration will stop exactly where its gate stops**, and the
gate here detects an alphabet while the policy names a language. Nobody decided to leave four Turkish
strings in; the signal ran out and the work followed it. That is why W-019 accepts a residual gap
instead of claiming a fix: a word-list would be the denylist class this milestone has already been
caught by twice.

Also fixed from the review, and it is the robustness-as-concealment instance it asked me to hunt:
`read_export_csv` filtered EVERY line beginning with `#`, so a model named `#1 Model` would have
lost its row while the file, the JSON row count and every assertion stayed plausible. It now skips
only the leading metadata block, with a citing test.

Filled by: `Claude (lead agent, local lane under D-114/D-117)` · Date: `2026-08-17` · Wave commit range: `f3c75b9..working tree`
