# Wave 1 Code Re-review (m6) — the fix delta

**Reviewer:** Code-Reviewer subagent (same seat as `m6-wave-1-review.md`; authored no wave code and
no fix-delta code)
**Date:** 2026-08-17
**Reviewed base:** `4dc6f53` (the tree my original verdict covered)
**Fix delta:** uncommitted working tree — `git diff 4dc6f53 -- src tests docs`, three files,
+356/-32 (`src/app/adapter/main.py`, `tests/unit/test_api_v1.py`, `docs/decisions.md`)
**Risk tier:** MED per plan. V4C-50: **a fix inherits the risk class of the bug it fixes and is
re-tiered, never inherited** — this delta rewrites the guard for the milestone's signature contract
and adds a wall-clock control path, so I reviewed it as new code and re-ran the fault injection
myself rather than reading the author's mutant table.

`m6-wave-1-review.md` is untouched and remains the record of the original verdict.

## Verdict

**BLOCKING** — one finding, re-issued narrowed, with a bounded closure condition stated below so
this does not become an open-ended loop.

| | count |
|---|---|
| Original BLOCKING closed | **1 of 2** (BLOCKING-1, in substance) |
| BLOCKING re-issued | **1** (BLOCKING-R1, the narrowed remainder of BLOCKING-2) |
| Original MINOR closed | **6 of 10** (1, 2, 4, 6, 7, 9, 10 — seven items; 3, 5, 8 deliberately deferred, accepted) |
| New MINOR | **8** |

The delta is a real improvement and most of it is better than what I asked for — the author found a
CWD-relative-default defect I missed, the security pass found that the disclosure which shipped
failed OPEN, and both are now fixed with mutant-verified tests. The one thing I cannot sign is the
Trap 2 guard: it went from nine spellings to sixteen stems, which killed my mutant and not my
finding. `display_order`, `suggested` and `authoritative` all still pass, and `docs/decisions.md`
now states as ratified ADR text that the property *is* asserted.

---

## Disposition of my original findings

| Finding | Status | Evidence |
|---|---|---|
| **BLOCKING-1** — REQ-API-005 unhealthy-source case absent | **CLOSED in substance** (see MINOR-R6 on the criterion's wording) | `src/app/adapter/main.py:176-230` `_source_health_json`, wired at `:296` and serialized at `:274`; tests `tests/unit/test_api_v1.py:213`, `:237`. Mutant N8 (delete the `source_health` block) → **3 tests RED**. Mutant N7 (report every source fresh) → **RED**. |
| **BLOCKING-2** — Trap 2 guard was a spelling denylist | **PARTIALLY CLOSED → re-issued as BLOCKING-R1** | My M1b (`primary_surface` + `top_pick`) is now **RED** (`tests/unit/test_api_v1.py:158-163`). Four new precedence mutants still pass — see below. |
| MINOR-1 — mount-blind route walk | **CLOSED** | `_all_routes` recurses (`tests/unit/test_api_v1.py:264-282`). Mutant N9 (sub-app with `POST /sub/wipe`) → **2 tests RED**, where it was green before. |
| MINOR-2 — dead assertion, unchecked status | **CLOSED** | `tests/unit/test_api_v1.py:431-438`: status asserted, dead `app.state.db_path` line gone, and a WAL/journal sidecar check added that I did not ask for. |
| MINOR-3 — hand-mirrored serializers | **DEFERRED to W2, accepted** | Correct call; it is `m6-plan.md:139`'s work. Carried forward with one addition — see MINOR-R5. |
| MINOR-4 — publishes category policy, not the run | **CLOSED** | `src/app/adapter/main.py:273` reads `rec.ranking_effort` with the `spec` value only as the no-recommendation fallback, and the comment states why. |
| MINOR-5 — mixed-language payload | **DEFERRED to the owner, accepted** | Right call. It is a product decision, not a reviewer's. |
| MINOR-6 — D-115 unwritten | **CLOSED** | `docs/decisions.md:587-629`. Reviewed as a contract statement below; two observations, MINOR-R7 and MINOR-R8. |
| MINOR-7 — undeclared CWD-relative config surface | **CLOSED, and improved past my ask** | `src/app/adapter/main.py:130-138`: no default at all, unset is a fail-closed 503. Mutant N10 (restore `os.environ.get("MODEL_RANKING_DB", "pipeline.db")`) → `tests/unit/test_api_v1.py:380` **RED**. This is the delta's own stay-green fault, correctly given its mandatory V3C-72 test. |
| MINOR-8 — tier rationale | **RECORDED, not re-tiered, accepted** | My position is unchanged and does not block. |
| MINOR-9 — black | **CLOSED** | `black --check src tests` → 60 files unchanged. |
| MINOR-10 — dead condition | **CLOSED** | `src/app/adapter/main.py:361`. |

**Independently re-run gates:** `pytest` **292 passed / 12 skipped** (the claimed number, up from
271 at wave start and 284 at my first pass) · `ruff check src tests` clean · `mypy` clean ·
`black --check` clean · `check_records.py` PASS (29 records) · `check_records.py --self-test` PASS ·
`md5 src/app/adapter/main.py` = `68fdb1280422e1b53f69518a495da55b`, matching the delta's stated
before/after identity.

---

## BLOCKING-R1 — the precedence guard is still enforced by vocabulary, and D-115 now says it is not

`tests/unit/test_api_v1.py:35-39` replaces nine literal names with a sixteen-stem regex, and
`:44-53` adds a closed three-entry exemption set guarded by `test_the_precedence_exemptions_stay_
closed` (`:170`). That is a genuine strengthening: my M1b dies, and the exemption list cannot be
widened silently. It is still a vocabulary.

Measured on the fix delta, in a scratch copy of the tree (no repository file was modified). Each row
is a field that ranks one coding surface above the other:

| mutant | added to the payload | result |
|---|---|---|
| N11 (my original M1b) | `"primary_surface": "coding"`, `"top_pick": "coding"` | **RED** — fixed |
| **N1** | `"display_order": 0 / 1` on each answer | **21 passed — STAYS GREEN** |
| **N2** | `"suggested": True / False` on each answer | **21 passed — STAYS GREEN** |
| **N3** | `"authoritative"` + `"canonical_answer"` on each answer | **21 passed — STAYS GREEN** |
| **N4** | no key change; `ORDERING_NOTE` rewritten to *"Use the coding answer; agentic-coding is supplementary evidence only."* | **21 passed — STAYS GREEN** |

N1 is not a hypothetical spelling. It is Trap 2's **first** listed vector — "an array whose order is
stable and therefore read as precedence" (`m6-plan.md:57-58`) — written down as a field. N2 is a
plain synonym of `recommended`, which the pattern does contain. N4 is Trap 2's fourth vector
("documentation whose every example shows `coding` first") applied to the one field whose entire job
is to say the order carries no meaning: `tests/unit/test_api_v1.py:154` asserts only that
`ordering_note` is truthy, so the envelope's disclaimer can be replaced with its opposite and every
gate stays green.

**What makes this BLOCKING rather than a MINOR I would wave through on a second pass:**

1. REQ-API-002's text is "Citing test asserts two members AND asserts that no field ranks them"
   (`m6-plan.md:112`). With N1 admissible, a field that ranks them is admissible, so the criterion
   is not asserted — permission-matrix §11, "REQ-ID unmet".
2. `docs/decisions.md:596-598` now states, as **ratified** contract text: "no ranking key — **under
   any spelling.** The prohibition is on the property, not on a list of words. **A citing test
   asserts the property.**" and `:620-624` repeats it in Mitigation. That last sentence is not true
   of the shipped test. AGENTS.md §5 / V4C-49 is explicit that writing a rule is not installing its
   gate; an ADR that claims a gate exists is worse than one that admits it does not, because the
   next reviewer will read the ADR and stop looking. This is the one place the delta made the record
   less accurate than the code.
3. The complete formulation is already in this same file, twice. The author closed exactly this
   class for the exemption set (`test_the_precedence_exemptions_stay_closed`) and for the route set
   (`DECLARED_ROUTES`). The payload's key set is the one place the technique was not applied.

**Bounded closure condition — this is my whole remaining ask on Trap 2, and I pre-commit to
accepting it without further iteration:**

- Freeze the envelope key set and the answer key set exactly, the way the exemption set is frozen:
  `set(body) == FROZEN_ENVELOPE_KEYS` and `set(answer) == FROZEN_ANSWER_KEYS` in the test module, so
  that **any** new key — whatever it is called — is a deliberate test edit. Keep the regex as a
  second, cheaper net; it costs nothing and it documents intent.
- Assert `ordering_note`'s content, not its truthiness (e.g. it equals `adapter.ORDERING_NOTE` and
  that constant contains the "carries no meaning" / "neither ... leads" clause).
- Mutants N1, N2, N3 and N4 above must go RED. Nothing else.

Until then, either the test is completed or D-115 clause 2's final sentence and its Mitigation
paragraph must be softened to describe the guard that actually ships. **The code itself is correct —
no defect ships today. What is not met is the criterion that the contract be enforced rather than
intended, which is the entire reason this milestone exists.**

---

## New MINOR findings

- **MINOR-R1 — `DECLARED_ROUTES` is self-declaring; the route-set proof reads its expectation from
  the code it is testing.** `tests/unit/test_api_v1.py:305-309` asserts
  `shipped == set(adapter.DECLARED_ROUTES)` while its docstring says "the plan declares three
  routes". Mutant N5b: register a real `@app.get("/v1/purge")` that mutates *and* add `"/v1/purge"`
  to `DECLARED_ROUTES` (`src/app/adapter/main.py:64-66`) → **21 passed, stays green**, and the
  mutating-verb scan is untroubled because the verb is GET. Same class as BLOCKING-R1 and the same
  fix the author already used for the exemption set: literal the three paths in the test, or add
  `test_the_declared_route_set_stays_closed` mirroring `test_the_precedence_exemptions_stay_closed`.
  The route-set test is otherwise an excellent addition — it caught four undeclared routes the verb
  scan structurally could not.
- **MINOR-R2 — the new health control is one-sided: nothing can observe a HEALTHY source.**
  `stale` is asserted `is True` at `tests/unit/test_api_v1.py:227`, `:234`, `:242` and asserted
  `False` nowhere. Mutant N6 (`_source_health_json` reports every source stale unconditionally, by
  forcing the `health is None` branch) → **21 passed, stays green**. The fail direction is correct
  (V3C-33/45, toward disclosure) so this is not a repeat of the fail-open defect, but it means the
  wall-clock arithmetic itself — `age_days` against `SOURCE_STALE_DAYS` — is unproven: no test
  distinguishes "computed stale" from "hardcoded stale", and a permanently-stale notice is noise
  that trains a reader to ignore it. One test with fresh evidence asserting `stale is False` and a
  small `age_days` is what makes the positive case mean something.
- **MINOR-R3 — the only clock on the surface is local-time and has no seam, which is also why
  MINOR-R2 is hard to fix.** `src/app/adapter/main.py:296` calls `dt.date.today()`. Every other
  "today" in this project is UTC and injectable: `coverage.py:274`, `epoch.py:88`, `plans.py:295`,
  `rosters.py:199` all use `dt.datetime.now(tz=dt.UTC).date()` behind a `--today` override. The API
  is the one process that will run on a host whose timezone nobody chose, and its staleness verdict
  can differ by a day from the CLI coverage report over the same database. Route it through one
  `_today()` helper returning UTC; that single change fixes the drift and gives MINOR-R2 its seam.
- **MINOR-R4 — the symmetry test asserts something that is not a contract property, and will fire
  falsely.** `tests/unit/test_api_v1.py:196` asserts
  `[p["label"] for p in a["picks"]] == [p["label"] for p in b["picks"]]`. D-115 clause 5
  (`docs/decisions.md:602-603`) says the answers carry **identical key sets** — it does not say they
  carry identical picks, and `unavailable_reason` exists precisely because one surface can rank
  nothing while the other ranks. Demonstrated, not argued: on a database seeded with the SWE-bench
  board only — a legitimate state the wave's own design serves —
  `coding` returns `['best_quality', 'best_value', 'budget_pick']`, `agentic-coding` returns `[]`
  with its `unavailable_reason` set, key sets equal, contract satisfied, and that assertion is
  **False**. A future author gets a red test reporting a contract violation that has not occurred.
  Assert what D-115 says. Related, same lines: the `for key in ("picks", "source_health")` loop at
  `:193-195` is guarded by `isinstance(a[key], dict)`, so the `picks` half never executes — it reads
  as if pick shapes are compared and they are not.
- **MINOR-R5 — a field is renamed at the payload boundary, in the wave that has no serializer yet.**
  `coverage.SourceHealth.newest_run_date` (`coverage.py:65`) is published as
  `"newest_evaluation_date"` (`src/app/adapter/main.py:226`). It is null on the undated board today,
  so nothing false is currently served, and the new name is arguably the more honest one for a
  public payload. But a run date is not by definition an evaluation date, and asserting that
  equivalence at the boundary is the M5 BLOCKING-1 shape in miniature. Fold into MINOR-3's W2
  serializer work: one name, decided once, in one place.
- **MINOR-R6 — REQ-API-005's fourth case is now answered with a 200 disclosure, not the "error
  shape" the criterion words. This needs an owner ruling, and the fix must NOT be a 503.**
  The criterion (`m6-plan.md:115`, `docs/prd.md:339`) says all four cases "produce a stable,
  documented error shape that fails loud and closed". Unknown task, unknown budget and missing
  database do. An unhealthy source produces a `source_health` block inside a normal 200. **I think
  the implementation is right and the criterion's wording is wrong** — 503-ing a stale board would
  contradict REQ-REC-006 ("never hidden"), the honesty doctrine, and Ruling A itself, since it would
  drop a coding answer the owner ruled must always be present. But an implementer reinterpreting a
  signed acceptance criterion is exactly what a reviewer must surface rather than bless: this wants
  one line of amendment to `m6-plan.md` §2 and `docs/prd.md`, or a sentence in D-115, at the
  milestone gate. Flagged, deliberately not blocked, and explicitly **not** a request to return 503.
- **MINOR-R7 — the wave-close record now understates what ran.** `docs/plans/m6-wave-1-close.md` is
  unmodified by this delta (`git status --short` shows only `docs/decisions.md`,
  `src/app/adapter/main.py`, `tests/unit/test_api_v1.py`). Row 3 still reads "NOT RUN —
  NO-ENVIRONMENT" for the fresh-eyes review, row 4 the same for the pulled-forward security pass,
  row 9's run line still says 284 passed and lists both as SKIPPED gates, and `W-016` in
  `docs/warnings.ledger.md` is still ESCALATED — while both controls have now run and produced
  `docs/reviews/m6-wave-1-review.md` and `docs/reviews/m6-wave-1-security.md`. Under V4C-13 the
  friction ledger is the record of what was skipped; a record that reports a control as skipped
  after it ran is as wrong as one that reports it run when it was not. Refresh rows 3, 4, 9 and
  resolve W-016 before W1 closes.
- **MINOR-R8 — D-115's provenance conflates the owner's ruling with the wave's elaboration.** It is
  a good ADR — clauses 1-5 are contract terms, the rationale states the trade honestly, and
  "Revisit when" is real. But its status line reads "ratified — owner ruling 'A'", and only clause 1
  and the neither-leads principle are the owner's ruling. Alphabetical ordering (clause 3),
  structural symmetry (clause 5) and the spelling-independence framing (clause 2) are decisions this
  wave made. AGENTS.md §3.4 has an agent-authored ADR land as `proposed`. Either split the owner's
  ruling from the wave's elaboration, or mark the elaboration as pending the milestone gate.

## Carried, not re-raised

The security review's MINOR-3 (unauthenticated whole-database copy per request — my "risks queued"
item), MINOR-4 (fail-closed paths are silent, nothing logged) and MINOR-5 (the framework's 422/405
shapes coexist with the custom error shape) are unfixed by this delta and correctly owned by that
review with a Stage 4.3 gate on the first. I read them, I agree with the dispositions, and I do not
re-raise them here — two reviewers ledgering the same item twice is how one of them gets closed by
the other's fix note.

## Verification method

Fault injection re-run independently rather than read: 12 mutants against the fix delta in a scratch
copy of `src`/`tests` under `scratchpad/mut2`. **7 killed** (N7 always-fresh, N8 disclosure dropped,
N9 mounted POST, N10 CWD-relative default, N11 `primary_surface`+`top_pick`, N12 nosniff removed, N5
unregistered-route control), **5 stayed green** (N1 `display_order`, N2 `suggested`, N3
`authoritative`/`canonical_answer`, N4 prose precedence, N6 always-stale; plus N5b, the
self-declared route). I never modified any repository source or test file at any point in this
review, and I never ran `git commit`, `git push`, `git checkout`, `git restore` or `git stash`.
`git status --short` before and after this review shows the same three modified files.

> *Wording note (2026-08-17).* The sentence above originally read "no ... was run".
> `conformance/test-git-authority.py` flagged it: its NEGATION list recognises "never", "do not",
> "must not" and similar, but not the construction "no X was run", so a **record of non-action**
> read to it as an instruction. I restated it in the active voice — same claim, same evidence, and
> an attestation with a named actor is the better form anyway. **My agreement to reword is
> conditional on the checker defect being filed as GPF-004** and handed back to the pipeline: a
> gate satisfied by rephrasing, with the defect unrecorded, teaches the next agent to phrase around
> the checker instead of reporting it. With GPF-004 filed, the finding survives the green row. If
> it were not being filed, my ruling would be the opposite — leave the row red and ledger it.

**Consequence: BLOCKING → W1 does not close.** BLOCKING-R1's closure condition is bounded and
mechanical; MINOR-R1 is five lines and belongs in the same change. Everything else on this list can
ride to the milestone gate.
