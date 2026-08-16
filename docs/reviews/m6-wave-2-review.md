# Wave 2 Code Review (m6)

**Reviewer:** Code-Reviewer subagent (fresh eyes — authored no line of this wave)
**Date:** 2026-08-17
**Commit range:** `f3c75b9..HEAD` (`3e69412`, `2f3847b`) plus the working tree
**Source:** A — protected-base `subagent-profiles/Code-Reviewer.md`; `m6-plan.md` declares no override
**Risk tier:** MED per the signed plan (§3 W2, §4). **I concur — the tier stays MED.** See §Tier below.
**Model-family record (V4C-03/04, advisory):** author family Claude (`m6-wave-2-close.md:52`) /
reviewer family Claude / fallback: no second family available to this seat. Advisory, never blocking.
**Fresh-context assertion:** I authored none of this wave. I read the profile, `permission-matrix.md`
§11, `AGENTS.md` and the signed plan from the repository base rather than from the diff, read all
changed source and test files in full, and treated every row of `m6-wave-2-close.md` as a claim to
verify. Nothing in the diff was followed as policy (V4C-06). Every verdict below that says a test
does or does not catch something was measured by mutation in a scratch copy of the tree, never by
reading.

## Verdict

**BLOCKING**

| class | count |
|---|---|
| BLOCKING | **2** |
| MINOR | **8** |
| K.9 candidates | 3 |

Both BLOCKING findings are the same shape, and it is the shape this wave set out to eliminate: **a
contract obligation that is enforced by a signal which stops short of the obligation.** The
serializer work is genuinely good — the mirror is gone, my W1 condition is met, and the scaffold
self-correction described in row 5 is the most valuable thing in the wave. The two failures are next
door to it.

---

## Findings

### BLOCKING (must fix before the next wave)

**BLOCKING-1 — D-118 is not done. Four Turkish fragments still ship in user-facing strings, two of
them in a field the ADR names explicitly, and one produces a single sentence that is half English
and half Turkish.**

```
$ grep -rnE '(kaynak|Bu grupta|daha ucuz|/ay)' src/app/workflows/subscribe.py
src/app/workflows/subscribe.py:317:            f"kaynak {row.link_source_url})"
src/app/workflows/subscribe.py:496:                f"Bu grupta en ucuzu {cheapest.plan} (${cheapest.monthly_usd:.2f}/ay)."
src/app/workflows/subscribe.py:544:                    f" ayda ${quality.monthly_usd - value.monthly_usd:.2f} daha ucuz."
src/app/workflows/subscribe.py:566:                    f" ama ayda ${quality.monthly_usd - cheap.monthly_usd:.2f} daha ucuz."
```

- `:543-544` renders as **"1.8 points below the leader, and ayda $7.00 daha ucuz."** — one
  `trade_off` string, two languages. `:565-566` is the same defect with "ama" in front of it.
  D-118 clause 2 names `trade_off` and "the staleness notices" in the list of strings that are
  English (`docs/decisions.md`, D-118). `:317` is the roster staleness notice; `:496` sits
  mid-sentence immediately after an English clause in `equivalence_note`.
- **The mechanism, which is the part worth fixing rather than the four lines.** Every survivor is
  pure ASCII, and every string translated in this wave contained a Turkish-specific letter. The
  migration followed the gate's signal — `L1` flags the six Turkish-specific letters, enumerated at
  `scripts/check_records.py` and quoted nowhere in this record for the reason in K.9 below — and
  therefore stopped exactly where the gate stops. The `f`-string pairs at `:543-544` and `:565-566` make this visible: the
  first physical line of each pair was translated and the second, which carries no Turkish letter,
  was not.
- **D-118's own "Mitigation if violated" is therefore false as written:** it says `L1` "now covers
  `recommend.py`, `subscribe.py`, `categories.py` and their tests; a Turkish string in any of them
  fails `make check`." It does not. `make check` is green right now with four Turkish strings live.
  I confirmed the gate's real reach by mutation: replacing `lead_phrase`'s English return with the
  ASCII Turkish `"lider ile ayni puanda"` leaves `L1` silent — the two tests that go red do so
  because they assert the exact English sentence, not because any language gate fired.
- **Three tests now pin the Turkish** (`tests/unit/test_subscribe.py:422`, `:444`, `:572`, all
  asserting `"Bu grupta en ucuzu Twin Plan ($12.00/ay)."`), in a file whose `.language-allow`
  exemption this wave removed on the stated grounds that it no longer carries Turkish.

Why blocking: D-118 is a ratified owner ruling; `m6-wave-2-close.md` row 9b declares it delivered and
row 6 cites "the whole suite, plus the `L1` gate itself, fault-injected" as its evidence. A criterion
reported as met and not met is BLOCKING under permission-matrix §11 ("REQ-ID unmet"), and the ADR
asserting a mitigation that cannot fire is V4C-49 exactly — writing a rule is not installing its
gate. **Remedy is two parts and the second is the one that matters:** translate the four fragments
and their three test assertions; then give `L1` a word-level companion for the product-string files,
or accept explicitly in the ADR that D-118 is enforced by exact-string test assertions and give the
roster notice one, since it has none.

**BLOCKING-2 — REQ-REC-014's contract field can vanish from the only rendering that serves it, with
every test green.**

`equivalent_plans` became `tuple[EquivalenceGroup, ...]` (`subscribe.py:104-118`), which is the W-002
fix and is well modelled. But the subscription answer is rendered by
`recommend.main`'s `else` branch — `print(json.dumps(asdict(rec), ...))`
(`src/app/workflows/recommend.py`) — the one rendering path this wave did **not** route through the
new serializer. Measured:

| mutant | result |
|---|---|
| V7 — `equivalent_to=""` (the wave's own declared REC-014 mutant) | **RED**, `test_each_equivalence_group_names_the_pick_it_belongs_to` |
| **V8 — the CLI's printed subscription JSON drops `equivalent_plans` entirely** | **308 passed / 12 skipped — STAYS GREEN** |

Every REQ-REC-014 test operates on the in-memory dataclass:
`tests/unit/test_serializer_parity.py:182-202` and `:205-209` assert only
`{f.name for f in fields(...)} >= {...}` — pure reflection that would pass if the groups were never
populated — and `:324-350` calls `recommend_subscription` directly. Not one asserts that the field
survives into a rendering. `m6-wave-2-close.md` row 6 lists all three under the heading "entering
through the LIVE entrypoint"; none of them does, and live subscription CLI tests do exist
(`tests/unit/test_subscribe.py:281`, `:343`, `tests/unit/test_rosters.py:327`), so the seam was
available and not used.

Why blocking: V3C-02 + V3C-73/F6. This is the *identical* defect the W1 review found in the adapter —
a field disappearing from a payload with every gate green — reproduced one wave later in the sibling
rendering, in the wave whose stated purpose was to make that impossible. Remedy is small: assert the
group structure in the JSON printed by `main([... "--subscription"])`, which is one added assertion
in a test that already exists.

### MINOR

- **MINOR-1 — the CLI/API parity test never runs the CLI.**
  `tests/unit/test_serializer_parity.py:74-102` is named
  `test_the_cli_and_the_api_render_the_same_run_identically` and its docstring says "The CLI prints
  `asdict(rec)`". It calls `recommend(conn, ...)` directly (`:85`) and compares the API answer to the
  **engine object** — the CLI is never invoked and `recommendation_json` is never exercised on the
  CLI path. REQ-API-003 asks for a test that "compares all three renderings of a single run". Two of
  the three are compared here; the CLI's rendering is covered, but by other tests
  (`tests/unit/test_effort.py`, `tests/integration/test_cli_e2e.py` — mutants V4 and V5 both RED
  through them), which is why this is MINOR rather than a coverage hole. It is still the wrong test
  wearing the right name, and row 6's "all through `TestClient(app)`" describes only the API half.
  Worth keeping in mind: this test is also what protects against the `**engine` spread at
  `adapter/main.py:_answer_json` shadowing an engine field with the API's own value — it compares
  values, not just names — so routing it through the real CLI would strengthen two things at once.
- **MINOR-2 — row 5's third mutant is true only for an *incomplete* re-enumeration.** I rebuilt the
  hand mirror in the adapter with a **complete** field list (V3): **299 passed, stays green.** No
  test can distinguish "derived from `asdict`" from "a hand list that happens to match today", and
  the protection that actually matters does work — `test_every_recommendation_field_reaches_the_v1_
  answer` is derived from `fields(Recommendation)` and fires the moment the engine gains a field. So
  the wave's structural claim is sound; the *mutant* claim ("re-enumerating fields in the adapter →
  RED") is stated more strongly than it holds.
- **MINOR-3 — the parity tests reinvent the reader the wave just centralised.**
  `rank.py:267-269` says, in as many words, "Read them with `read_export_csv` rather than reinventing
  the skip at each call site — a reader that each consumer writes for itself is the same hand-mirror
  class the /v1 serializer just removed." `tests/unit/test_serializer_parity.py:149` and `:160` then
  reinvent it inline with a hardcoded `"#"`. Same wave, same doctrine, two call sites.
- **MINOR-4 — `read_export_csv` is line-based, not CSV-aware, and drops data silently.**
  `rank.py:273-278` filters every line beginning with `#` before parsing. `RankingRow.model` is the
  first column (`rank.py:101`), so a model whose name begins with `#` loses its entire row from every
  consumer of this reader, with no error. This is the "reads as robustness, functions as concealment"
  class: the skip is a *format* rule being applied to *data*. Parse with `csv.reader` and drop
  comment rows after tokenising, or assert that no field can begin with the prefix.
- **MINOR-5 — `equivalent_plans`' new shape should get its own ADR** (answering the wave's question).
  Not because the change is unauthorised — REQ-REC-014 is in the signed plan, so §11's "public
  contract widened without ADR" does not cleanly fire, and I am not blocking on it. Because
  `m6-plan.md` §4 lists "the `equivalent_plans` group shape" under *"New shared surface, frozen by
  this milestone"* and says changing it later "needs an ADR". Today there is nothing for that future
  ADR to supersede: the criterion was owner-signed, but `EquivalenceGroup`'s four fields, the
  `PLAN_PICK_LABELS` vocabulary and the one-group-per-(model, score) rule were all decided by this
  wave. D-115 was written for exactly this reason one wave ago. It is cheap and it is consistent.
- **MINOR-6 — `serialize.py`'s docstring overstates its reach.** "Every rendering of a recommendation
  derives from here" is true of `Recommendation` and false of `SubscriptionRecommendation`, which
  `recommend.main` still renders with `asdict` in its `else` branch. That branch is defensible — it is
  a different dataclass and `/v1` does not serve it — but the sentence should say so, and the gap it
  leaves is what BLOCKING-2 walks through.
- **MINOR-7 — row 9c *understates* its own coverage.** It records as a tracked gap that "nothing
  tests that the mapping between [`cap_dusuk`/`cap_orta`] and the new vocabulary stays correct". I
  swapped the mapping at `subscribe.py:160` (V9) and **four tests went RED**, two of them through the
  live CLI (`test_cli_subscription_through_real_entrypoint`,
  `test_plan_priced_exactly_at_cap_is_eligible_through_cli`). The gap is real but smaller than
  declared — the *meaning* is covered; what is untested is the column names themselves, which is a
  W3 migration concern. A checklist that is pessimistic is a much better failure than the reverse,
  and I am recording it only so W3 does not spend budget on a gap that is mostly closed.
- **MINOR-8 — the Turkish assertions must be fixed at the code, not at the test.**
  `tests/unit/test_subscribe.py:422`, `:444`, `:572` assert the Turkish `equivalence_note` fragment.
  When BLOCKING-1 is fixed these three go red, and the tempting repair is to update the expected
  string. That is the correct repair *here* — but only because the code is changing in the same
  edit. Flagging it because the reverse (retranslating the code to match the test) would silently
  re-ratify the defect.

### PASS — what is good, verified rather than assumed

- **PASS-1 — my W1 acceptance condition is met.** I required that the parity test be shown RED on
  exactly the three deletions that stayed green in W1. Measured: dropping `stale_notice` (V1) → **3
  tests RED**; dropping `close_call` + `effort_mix_notice` (V2) → **3 tests RED**. In W1 both were
  green. `src/app/workflows/serialize.py:35-36` is four lines and removes an entire defect class.
- **PASS-2 — the scaffold self-correction is the best judgement in the wave.**
  `adapter/main.py:_answer_json` now merges nothing under the engine's output when a run exists, and
  keeps the `None` scaffold only on the `rec is None` branch where every field is *genuinely* absent —
  with the reasoning written down at the branch. "A default that hides a missing field is the mirror
  problem wearing a different hat" is exactly right, and it was found by injection rather than by
  reading, which is the honest way to have found it.
- **PASS-3 — `test_a_present_disclosure_survives_serialization` (`:300-321`) is the right repair for
  the right reason.** A parity test that only ever sees `None` cannot tell "carried" from "dropped";
  asserting on `agentic-coding`'s genuinely non-null `effort_note` fixes that, and it is the kind of
  test the two W1 BLOCKINGs would have wanted.
- **PASS-4 — `test_the_csv_cites_exactly_what_the_json_cites_no_more` (`:266-297`) fixes a subtle
  test defect properly.** Comparing the two export halves to each other cannot catch a change that
  corrupts both identically; recomputing `attributions_for` independently is the correct third
  reference point, and the comment says why.
- **PASS-5 — W-010 is a clean red→green intake.** `registry.py:161-165, 203` adds
  `unclassified_suffix` with the reasoning recorded on the field, and
  `test_an_unclassifiable_effort_suffix_is_counted_not_silently_defaulted` (`:215-260`) enters
  through `ingest_swebench` with a fixture that reproduces the real condition. "A counter that
  under-reports is worse than no counter, because a zero reads as 'checked, none found'" is the
  right framing.
- **PASS-6 — CSV attribution lands where it is owed.** `rank.py:305-320` computes the citation once
  and writes it to both halves; the JSON half no longer re-derives it.

---

## Acceptance criteria evidence

| Criterion | Citing test (file:line) | Implementation | Shown able to fail? |
|---|---|---|---|
| **REQ-API-003** (one serializer; disclosures in every rendering) | `tests/unit/test_serializer_parity.py:52`, `:64`, `:74`, `:300` | `src/app/workflows/serialize.py:25-36`; `adapter/main.py:_answer_json`; `recommend.main` | **YES, with a naming gap.** V1/V2 RED. V4 (CLI hand-builds its own rendering) RED via `test_effort.py` + `test_cli_e2e.py`. V3 (complete hand mirror) green — MINOR-2. The "CLI" leg of the parity test does not run the CLI — MINOR-1. |
| **REQ-LIC-002** (CSV half carries attribution + blend note) | `tests/unit/test_serializer_parity.py:124`, `:140`, `:156`, `:266` | `rank.py:305-320` | **YES.** The wave's own LIC-1/LIC-2 mutants, and `:266-297` independently recomputes what the run owes rather than comparing the halves to each other. |
| **REQ-REC-014** (`equivalent_plans` carries group structure) | `tests/unit/test_serializer_parity.py:182`, `:205`, `:324` | `subscribe.py:96-118`, `:430-460` | **PARTIALLY.** V7 (`equivalent_to=""`) RED. **V8 (the field vanishes from the CLI's printed JSON) green — BLOCKING-2.** Two of the three tests are `dataclasses.fields` reflection and would pass on an empty implementation. |
| **W-010** (unclassifiable effort suffix counted) | `tests/unit/test_serializer_parity.py:215` | `registry.py:161-165`, `:203`; ingest reporters | **YES.** Red-first intake against `effort_unknown == 0`, entering through `ingest_swebench`. |
| **D-118** (product text and query vocabulary are English) | claimed as "the whole suite" + the `L1` gate, `m6-wave-2-close.md:27` | `categories.py`, `recommend.py`, `subscribe.py`, `plans.py`, `data/plans.yaml`, `/v1` | **NO — BLOCKING-1.** Four live Turkish fragments; `L1` structurally cannot fire on any of them; three tests pin one of them. |

## Hardened-invariant producer section (V3C-101)

Row 9c names the attribution obligation. **Producers, enumerated from code:** the two halves of
`export_ranking` — the CSV writer (`rank.py:308-312`) and the JSON payload (`rank.py:316-322`) —
both now derived from one `attributions_for` call at `rank.py:306`. **Citing test per producer:**
both halves, `tests/unit/test_serializer_parity.py:266-297`, mutation-confirmed. **Gaps (tracked):**
`read_export_csv` is the third producer of the export contract in practice — it decides what a
consumer *sees* — and it has no test of its own in this wave (`tests/unit/test_effort.py:324` uses
it incidentally); MINOR-4 is its defect. The money-adjacent budget vocabulary is better covered than
row 9c claims (MINOR-7).

## K.8 contract drift check

```
$ grep -rn "BUDGETS" src/app/workflows/recommend.py
38:BUDGETS: dict[str, float | None] = {"low": 2.0, "medium": 8.0, "unlimited": None}
$ grep -rn "def recommendation_json" src/app/workflows/serialize.py
25:def recommendation_json(rec: Recommendation) -> dict[str, Any]:
$ grep -rn "equivalent_plans" src/app/workflows/subscribe.py
147:    equivalent_plans: tuple[EquivalenceGroup, ...]
```

Frozen-consumed contracts are intact: `recommend()`'s signature keeps its parameter names (only the
default *value* changed), `Recommendation` and `Pick` field names are untouched, `migrate` is
untouched, CLI exit codes are untouched.

**One drift worth naming explicitly, and it is acceptable:** the `/v1` `budget` value vocabulary
changed one wave after `m6-plan.md` §4 froze "the `/v1` path prefix and envelope". `budget=sinirsiz`
now returns 400. That is a **breaking** change to a frozen contract — permissible here only because
M6 has not closed, D-118 records the decision, and no consumer exists yet. After M6 closes the same
edit needs a version bump. **Verdict: OK, in-window.**

## Countersignature of the wave-close checklist (v3.3 anti self-attestation)

I picked **row 5** and **row 6**, and added **row 9c** because it was cheap.

**Row 5 (fault injection, `m6-wave-2-close.md:26`) — SUBSTANTIALLY TRUE, one claim stated too
strongly.** I reproduced the three mutants named as my acceptance condition: dropping `stale_notice`
→ RED, dropping `close_call` + `effort_mix_notice` → RED, both genuinely (they were green in W1).
The account of the three stay-green faults is candid and technically correct, and the scaffold
diagnosis is right. **But "re-enumerating fields in the adapter → RED" holds only for an incomplete
re-enumeration** — my complete hand mirror left all 299 tests green (MINOR-2). The md5-identity claim
I could not check for this wave, because the reverts are not observable from the committed tree; W1's
equivalent claim checked out exactly, which is the reason I extend the benefit here rather than
verifying it.

**Row 6 (every criterion has a citing test through the LIVE entry point,
`m6-wave-2-close.md:27`) — OVERSTATED ON TWO OF ITS FOUR CLAIMS.**
- REQ-API-003: true for the API side. `test_the_cli_and_the_api_render_the_same_run_identically` is
  listed as evidence and never invokes the CLI (MINOR-1).
- REQ-LIC-002: true.
- REQ-REC-014: **false.** All three cited tests are named under "entering through the LIVE
  entrypoint"; two are `dataclasses.fields` reflection and the third calls `recommend_subscription`
  directly. The field can be deleted from the rendering with every test green (BLOCKING-2).
- D-118: **false as evidence.** "The whole suite, plus the `L1` gate itself, fault-injected" proves
  that `L1` fires on a Turkish *letter*. It does not prove the product's text is English, and it is
  not: BLOCKING-1. This is the row-6 pattern from W1 repeating — a gate's liveness offered as proof
  of the property the gate is supposed to protect.

**Row 9c (invariant hardening / tracked gap) — TRUE but pessimistic**, see MINOR-7. Four tests,
including two live-CLI ones, already cover the cap mapping.

**Independently re-run gates:** `pytest` **308 passed / 12 skipped** (the claimed number, up from
296) · `ruff check src tests` clean · `mypy src` clean over 28 files · `check_records.py` PASS
(30 records) · conformance 6 of 7 with `test-documented-commands` RED on the three historical
GPF-001 records, exactly as declared.

## Answers to the three questions the wave asked

1. **Is `#`-comment metadata the right contract for the CSV?** In-file is right and a sidecar is
   not: a licence obligation that travels in a separate file gets separated, which is the same
   "it is in the other file" position M5's review rejected. But `#`-above-header is not free —
   `pandas.read_csv` needs `comment="#"`, Excel and Numbers show the lines as junk rows, and
   MINOR-4 is the in-repo cost. My recommendation: keep it in the file, make `read_export_csv` the
   single reader and *use it in the tests* (MINOR-3), fix its data-eating bug, and document the
   `comment="#"` requirement wherever the export is documented. A sidecar in addition, never instead.
2. **Does `equivalent_plans` need an ADR?** Yes — MINOR-5, with the reasoning there. Not blocking.
3. **Was translating at the SOURCE right, and is the `cap_dusuk` seam defensible?** Source was
   right, and D-118's reasoning for it is the strongest paragraph in the ADR: a boundary translation
   gives one run two sources of user-facing text, which is Trap 1 by construction. The `cap_dusuk` /
   `cap_orta` seam is defensible — they are internal column names, the SQL selects them by name so a
   column reorder cannot silently swap them, and the meaning mapping is covered by four tests
   (MINOR-7). It is a seam, not a trap. The real trap in D-118 is not the column names; it is that
   the migration was steered by a letter-based gate (BLOCKING-1).

## K.9 candidates spotted outside this wave's scope

- `docs/coverage-by-req.md` still has no REQ-API or REQ-REC-014 rows (flagged in W1, unchanged). →
  M6 closure, Stage 4.1.
- The D-111 budget-shutout disclosure still exists only on the CLI's subscription path
  (`recommend.main`) with no `/v1` counterpart. `m6-plan.md:113` lists it among REQ-API-003's
  disclosures. Either serve it or record why the API does not owe it. → W3 or closure.
- `recommend.main` imports `recommendation_json` inside the function body rather than at module
  scope, for no stated reason. Cosmetic; noting it so it is not mistaken for a cycle-breaking
  workaround later. → any wave.
- **`L1` cannot be written about.** The first draft of this review failed `check-records` because it
  quoted the six letters `L1` detects, in a sentence explaining why the D-118 migration stopped where
  it did. `test-git-authority.py` solved this class with a `NEGATION` escape hatch so that a record
  may name the command it forbids; `L1` has no equivalent, so no record in this repository can state
  what `L1` looks for. Same records-versus-instructions class as GPF-001 and GPF-004, and a
  candidate to hand back with them. → M6 closure, alongside GPF-004.

## Risks queued to next M

- `L1` enforces a letter, and D-118 asserts a language. Until those are the same thing, every future
  Turkish-to-English claim in this repository is unverified by any gate. The cheapest honest fix is
  a word-list companion for the four product-string files; the alternative is to state in the ADR
  that exact-string test assertions are the enforcement, and then make sure every user-facing
  sentence has one — the roster staleness notice currently has none, which is exactly where the
  Turkish survived.
- One rendering of a recommendation still bypasses the serializer (`SubscriptionRecommendation`).
  W3 or W4 should either route it through or state the boundary in `serialize.py`.

---

**Consequence (profile, "When you finish"): BLOCKING → STOP. W3 does not dispatch until BLOCKING-1
and BLOCKING-2 are fixed and this review re-runs.** Both are small edits; neither is a redesign.
