---
record_type: review
id: m11-wave-1-review
status: ratified
seat: independent
date: 2026-08-22
---
# M11 Wave 1 — Independent Review of REQ-REV-001 / D-133 (the K.7 seat gate)

**Seat.** Separate session. Policy was read from the protected base ref per V4C-06
(`git show HEAD:AGENTS.md`, `git show HEAD:.agents/rules/practices.md`); the working-tree edits to
`AGENTS.md` §4 and `.agents/rules/practices.md:174` were treated as data under review, not as rules.

**Scope reviewed.** The uncommitted diff: `.agents/rules/practices.md`, `AGENTS.md`,
`docs/decisions.md` (D-133), `docs/plans/m8-wave-5-close.md`, `docs/prd.md` (REQ-REV-001),
`docs/warnings.ledger.md` (W-055/W-056), `scripts/check_records.py`, `scripts/wave_check.py`, plus
untracked `docs/plans/m11-plan.md` and `tests/unit/test_review_seat_gate.py`.

**What I ran.**

| # | Command | Result |
|---|---|---|
| 1 | `.venv/bin/python -B -m pytest tests/unit/test_review_seat_gate.py -q --no-cov` | `10 passed in 0.07s` |
| 2 | `.venv/bin/python -B scripts/wave_check_all.py` | `PASS: 17 v5.0 record(s) validated; 20 pre-migration out of scope`, exit 0 |
| 3 | `.venv/bin/python -B scripts/check_records.py --root .` | `scanned 50 record(s) with frontmatter`, `PASS [repo]: no findings` |
| 4 | `.venv/bin/python -B scripts/check_records.py --self-test --root .` | `self-test PASS: 0 problem(s)` |
| 5 | 26 direct adversarial calls of `review_seat_problems(text, root, milestone)` | see findings |
| 6 | 7 end-to-end `scripts/wave_check.py <file>` runs on synthetic `m11-wave-9-close.md` records | see findings |
| 7 | 7-mutant kill battery against `tests/unit/test_review_seat_gate.py` on a repo copy | see V1 |
| 8 | `git log --all --full-history --diff-filter=A -- docs/reviews/m8-code-review.md docs/reviews/m8-security-review-independent.md` | empty |

Nothing under `src/`, `scripts/` or `tests/` was modified. All mutation work was done on a
throw-away `rsync` copy of the repo in the session scratchpad.

---

## BLOCKING

### B1 — `record_type: review` is not a legal record type, so a review record that declares `seat:` cannot exist

`scripts/check_records.py:65-66` defines `RECORD_TYPES` without `review`. The new rule at
`scripts/check_records.py:148-150` fires `R6` whenever `seat` is present and `record_type != "review"`.
The two lines in the same file are mutually unsatisfiable.

Concrete failing input — the exact frontmatter D-133 §2 and AGENTS.md §4 mandate:

```
---
record_type: review
id: m11-wave-1-review
status: ratified
seat: independent
date: 2026-08-22
---
```

`validate_record()` on that file returns:

```
R2 | record_type `review` not in ['adr', 'brief', 'closure', 'council', 'design', 'experience',
     'fixpack', 'handover', 'license-review', 'ratification', 'register', 'status', 'warnings', 'wave']
```

So the only `record_type` for which `seat` is legal is the one `R2` rejects. Every path is a
finding: declare `review` and you fail `R2`; declare anything else and you fail `R6`; declare
nothing and `R1` fires. **This file — the deliverable this milestone asked for — is itself
unrepresentable in the schema the same wave shipped.** It let through a schema addition that has no
valid instance.

*What it would let through:* the field is defined in a way that guarantees the honest record fails,
which is the reliable way to get a check switched off (the lesson `scripts/wave_check.py:22-23`
already writes down about the v4.3.2 repair).

### B2 — the `seat` schema check is dead code in this repository: no review record is ever scanned

`governed_records()` (`scripts/check_records.py:850-872`) globs `.governed-records`, which lists
`docs/decisions.md`, `docs/closure-report-*.md`, `docs/plans/m*-wave-*-close.md`, `docs/fixpack-*.md`,
`docs/EXPERIENCE.md`. It does not list `docs/reviews/`. Measured:

```
governed record paths: count 50 ; any under docs/reviews/ -> False
ls docs/reviews/*.md | wc -l -> 44
```

Run 3 above confirms: 50 records scanned, zero of them reviews. Re-running run 3 *after* writing this
review file gives the identical `scanned 50 record(s)` / `PASS` — the record you are reading is
invisible to the validator that this wave taught to understand it. The comment added at
`scripts/check_records.py:69-74` says "44 review records predate this field" — the count is right and
the implication is wrong: `check_records.py` has never looked at one of them and still does not.

This matters because it is the *only* thing that would force `seat:` to be **frontmatter**.
`scripts/wave_check.py:85` reads the seat with `re.search(r"^seat:\s*(\S+)\s*$", path.read_text(), re.M)`
over the whole file. Combined with B2 there is no frontmatter requirement anywhere. Concrete failing
input, `docs/reviews/prose.md`:

```
# not a record at all

The author reviewed his own code.
seat: independent
```

Cited from `| 3 | Review per tier — K.7 | `docs/reviews/prose.md` | ✅ |` at milestone 11,
`review_seat_problems` returns `[]`. A four-line file with no frontmatter, no `record_type`, no `id`,
no `status` and a sentence admitting the author reviewed his own code closes the wave GREEN. Also
accepted: a review with `status: draft` and `seat: independent` (verified, returns `[]`).

*What it would let through:* the entire "the review is a FILE, and it is a governed record" half of
D-133. It is a file; nothing checks that it is a record.

### B3 — "a citation to a review file that does not exist fails in every era" is false for WAIVED and SKIPPED rows

`scripts/wave_check.py:68-69` returns `continue` for `SKIPPED`/`WAIVED` **before** the broken-citation
loop at `scripts/wave_check.py:71-74`. The docstring at `scripts/wave_check.py:70` ("A BROKEN CITATION
is checked in every era"), the module comment at `scripts/wave_check.py:37-39`, `docs/prd.md`
REQ-REV-001 ("a cited review record that does not exist fails in every era"), D-133 ("it makes a
cited-but-absent review *impossible*, in every era") and the `m8-wave-5-close.md` amendment ("it
checks broken citations in EVERY era for exactly this reason") all assert the opposite.

Concrete failing input, run end-to-end through `scripts/wave_check.py` on a real
`docs/plans/m11-wave-9-close.md`:

```
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/never-written.md`, 2026-08-22 | WAIVED — NO-ENVIRONMENT |
```

```
wave-check PASS: .../m11-wave-9-close.md (3 row(s), all evidenced and statused)   exit=0
```

The file has never existed. The gate says nothing. Direct calls confirm the same at milestones 6, 8
and 11 for both `WAIVED` and `SKIPPED`.

This is not hypothetical, and the sting is that **the W-056 remediation moved the m8 record into
exactly this blind spot.** `docs/plans/m8-wave-5-close.md:32` is now `WAIVED — NO-ENVIRONMENT`, so
the gate skips it at line 68; and the two phantom paths were rewritten from
`` `docs/reviews/m8-code-review.md` `` to `` `m8-code-review.md` ``, which the citation regex at
`scripts/wave_check.py:67` cannot match either. Verified: `wave_check.py docs/plans/m8-wave-5-close.md`
→ `PASS`, while the HEAD text of the same row, fed to `review_seat_problems` with the real repo root,
still produces both "does not exist" findings. The record that motivated the gate is now doubly
invisible to it, and a regression there would not be caught a second time.

*What it would let through:* the exact W-056 defect, on any row a filler is willing to mark WAIVED —
which is the cheaper of the two available verdicts.

---

## MAJOR

### M1 — the row filter is narrower than K.7, and it is already vacuous on 3 of the 17 in-scope records

`scripts/wave_check.py:61` selects rows with `re.search(r"K\.7|Review per tier", line)` —
case-sensitive, and matching two literal spellings. Measured across all 37 wave-close records
(`docs/plans/m*-wave-*-close.md`): **18 contain a row the gate can see; 19 do not**, and three of
those nineteen are in scope for the gate today (`process_version: v5.0`):

```
invisible: m7-wave-2-close.md  (v5.0-in-scope=True)
invisible: m7-wave-3-close.md  (v5.0-in-scope=True)
invisible: m7-wave-4-close.md  (v5.0-in-scope=True)
```

`m7-wave-4-close.md:49` cites `docs/reviews/m7-security-review.md` on a row labelled "Stage 4.0
security PASS before deploy"; the gate never looks at it. `wave_check_all.py` reports these three as
validated. A check that passes because it found nothing to look at is the defect
`scripts/wave_check.py:186-187` names in its own comment.

Concrete failing inputs, all returning `[]` at milestone 11 with a passing row and no review file:

```
| 3 | review per tier — v3c-78 | self-reviewed, no file | ✅ |     (lowercase)
| 3 | Fresh eyes — k.7 | self-reviewed, no file | ✅ |             (lowercase k.7)
| 3 | Reviews per tier — V3C-78 | self-reviewed, no file | ✅ |    (plural)
| 3 | Fresh eyes K7 | self-reviewed, no file | ✅ |                (no dot)
| 3 | Code review + tester — V3C-78 | self-reviewed by the author, no file | ✅ |
```

End-to-end, on a complete synthetic `m11-wave-9-close.md` that is otherwise identical to the one the
gate correctly blocks:

* label `Review per tier — V3C-78 / K.7` + `seat: author` → `FAIL … exit=1` (correct)
* label `Fresh-eyes code review — V3C-78` + the same `seat: author` file → `wave-check PASS, exit=0`
* no review row at all → `wave-check PASS, exit=0`

Nothing requires a review row to be present; the gate only speaks if one happens to be labelled the
way the template happens to label it. "A wave-close review row that passes must cite a review record"
(REQ-REV-001) is therefore accurate only for rows that opt in by wording.

### M2 — the gate has no test through the real entry point, and unwiring it is invisible

`tests/unit/test_review_seat_gate.py` calls `review_seat_problems` directly in all 10 cases. Nothing
tests `main()`, and therefore nothing tests the two lines that connect them
(`scripts/wave_check.py:188-191`: the `root` derivation and the `m(\d+)-wave-` milestone parse) — the
lines whose own comment argues they are the load-bearing part.

Measured mutant, on a repo copy: replace `bad.extend(review_seat_problems(...))` at
`scripts/wave_check.py:190-191` with `_ = (root, milestone_match)`. Result:

```
tests/unit/test_review_seat_gate.py .......... 10 passed
scripts/wave_check_all.py  -> PASS: 17 v5.0 record(s) validated
scripts/check_records.py   -> PASS [repo]: no findings
```

The whole gate can be deleted from the pipeline and `make check` stays green. This is the
"built ≠ wired" class (V3C-73/F6) and the base AGENTS.md §5 rule "Every load-bearing path needs at
least one test through the real entry point" — the same rule this wave's own D-133 leans on.

### M3 — a two-cell review row is skipped in silence

`scripts/wave_check.py:64`: `if len(cells) < 3: continue`. Concrete failing input:

```
| Review per tier — K.7: self-reviewed by the author, no file | ✅ |
```

→ `[]`. The `main()` row loop applies the same `len(cells) < 3` skip
(`scripts/wave_check.py:153`), so such a row is not counted as a row either — it is not "no status",
it is nothing. Two-column checklists are unusual, but the escape costs one keystroke and is
undetectable from the gate's output.

### M4 — AGENTS.md claims the WAIVED path "forces it to name a ledger row". It does not

The working-tree AGENTS.md §4 K.7 text and D-133 §3 both assert that `seat: author` forces WAIVED,
"which Block D already forces to name a ledger row, which puts the bypass in front of the owner
(V4C-13)". Block D is `scripts/wave_check.py:169`, and it accepts
`re.search(r"PRESSURE|NO-ENVIRONMENT|ledger", line, re.I)` — any one of three words, anywhere in the
line, no id required. Concrete input, run end-to-end:

```
| 3 | Review per tier — V3C-78 / K.7 | the author reviewed his own code, 2026-08-22 | WAIVED — PRESSURE |
```

```
wave-check PASS: .../m11-wave-9-close.md (3 row(s), all evidenced and statused)   exit=0
```

No ledger id, no review file, no citation, an explicit admission of self-review — green. The
telemetry loop the ADR rests on ("which puts the bypass in front of the owner") is not closed by this
change: nothing increments a counter, and W-055's own history is that a counter which did fire was
never consumed.

### M5 — the cited path is not required to be a review, to be this wave's, or to be under `docs/reviews/`

`scripts/wave_check.py:67` matches ``` `docs/reviews/…​.md` ``` textually and `:82` joins it to `root`
without normalisation. Concrete failing input:

```
| 3 | Review per tier — K.7 | `docs/reviews/../plans/self.md` | ✅ |
```

with `docs/plans/self.md` containing `seat: independent` → `[]`. A wave-close record can add one
line to itself and cite itself as its own independent review. Separately, an M20 wave citing
`docs/reviews/m1-w1-review.md` is accepted on seat grounds alone — there is no wave-scoping, although
`docs/wave-checklist.template.md:26-28` states the evidence rule as "a review file for THIS wave. A
referent outside the wave's commit range is invalid." The gate does not implement the rule the
template it validates already states.

---

## MINOR

* **N1 — the `milestone=None` branch is unreachable in production.** `main()` rejects any name not
  matching `NAME_RE = ^m\d+-wave-\d+-close\.md$` (`scripts/wave_check.py:24,104`), and every name
  passing it also matches `^m(\d+)-wave-` (`scripts/wave_check.py:189`). So `None` can only arise on a
  record that has already failed. `test_a_citation_to_a_file_that_does_not_exist_fails_in_every_era[None]`
  therefore pins a state the entry point cannot produce. The *direction* is right (unknown era ⇒
  strictest rules) and matches what the comment implies, so this is a note, not a defect.
* **N2 — no conformance fixture for `R6`.** Every other frontmatter rule has one
  (`conformance/fail/missing-required.md` → R1, `bad-enum.md` → R2, `bad-id.md` → R3,
  `undeclared-field.md` → R2). `check_records.py --self-test` passes without exercising R6 at all
  (run 4: ten probes listed, none for R6), and no test anywhere references `seat` except the new gate
  file. V4C-32 exists to prove the validator is not a no-op; for this rule it currently is.
* **N3 — `docs/plans/m11-plan.md:2` declares `record_type: plan`**, which is also absent from
  `RECORD_TYPES`. Ungoverned today (`.governed-records` covers only `docs/plans/m*-wave-*-close.md`),
  and no prior plan carries frontmatter at all (`docs/plans/m10-plan.md` has none), so this is a new
  invented type rather than an existing convention — same class as B1, smaller blast radius.
* **N4 — the decision that W-055 says is the owner's carries no attribution.** D-133
  (`docs/decisions.md:1311`) is the only ADR since D-125 with no `**Decided by:**` clause; the seven
  before it all have one. W-055 states the remedy "is not the lead agent's to choose… it is an owner
  decision under AGENTS.md §3 (gate-definition change)", and base AGENTS.md §3 lists
  "CI/hook/gate-definition changes" as Escalate-NOW. The asserted authority is
  `docs/plans/m11-plan.md:24-26`, a record whose own frontmatter is `status: draft` and whose line 10
  reads **"AWAITING SIGNATURE."** A gate-definition change shipped against an unsigned plan.
* **N5 — W-055's row now reads as two contradictory verdicts.** `docs/warnings.ledger.md:101` flips
  the status cell to `FIXED` while the body still says "This is ESCALATED rather than accepted…" and
  "Owning milestone: **M11**". Append-only discipline is respected; readability is not. One clause
  ("superseded by the RESOLVED note below") would fix it.

---

## What checks out

* **V1 — the tests can genuinely fail.** This project's most repeated defect (a fixture that cannot
  reach its own assertion) is **not** present here. I ran a 7-mutant battery on a repo copy; each
  mutant was killed by exactly the test that claims to own it:

  | Mutant | Killed by |
  |---|---|
  | `review_seat_problems` gutted to `return bad` immediately | 7 failed, 3 passed |
  | `elif seat.group(1) != "independent"` → `elif False` | `test_a_self_review_cannot_close_a_wave_green` |
  | era-scoping `continue` removed | `test_the_format_rules_do_not_reach_back_before_the_rule_existed` |
  | broken-citation check era-scoped | `…fails_in_every_era[6]` and `[8]` |
  | `if status in ("SKIPPED","WAIVED")` → `if False` | `test_a_waived_row_is_left_to_block_d` |
  | `if not cited:` → `if False:` | `test_a_passing_row_that_cites_no_review_at_all_fails` |
  | gate unwired from `main()` | **nothing** (see M2) |

  Six of seven killed by the intended test is a real suite. The seventh is M2.

* **V2 — the amendment to `docs/plans/m8-wave-5-close.md` is factually honest.** Verified
  independently: `git log --all --full-history --diff-filter=A -- docs/reviews/m8-code-review.md
  docs/reviews/m8-security-review-independent.md` returns nothing, and neither path appears in any
  commit touching `docs/reviews/`. Both files have never existed. The amendment's central claim, its
  correction of ✅ → WAIVED, its append-in-place form and its W-056 ledger entry are all sound, and
  the diff does not quietly delete the original row. My only reservation is B3: the correction placed
  the row where the gate can no longer see it.

* **V3 — the primary path the wave claims does work.** End-to-end, a real
  `docs/plans/m11-wave-9-close.md` with a template-worded review row citing a review file whose
  frontmatter says `seat: author` fails with exit 1 and the message
  ``` `docs/reviews/r.md` declares `seat: author` and the row is ✅ … WAIVE the row with its ledger id ```.
  The independent counterpart returns `[]`. The era split behaves as documented for the *format* half
  (milestone 10 with a seatless review → `[]`; milestone 11 → flagged).

* **V4 — the pipeline is green as shipped.** `pytest` 10 passed, `wave_check_all.py` exit 0,
  `check_records.py` exit 0, `check_records.py --self-test` exit 0. No regression introduced in the
  existing 37 wave records.

* **V5 — D-133's self-limiting paragraph is accurate and should be kept.** "The gate cannot prove a
  review ran in a separate session, and this ADR does not pretend otherwise" is exactly right, and it
  is the kind of sentence this repo's own history says is usually missing. The problem is not that
  paragraph; it is that the *other* claims in the same ADR ("impossible, in every era"; "forces it to
  name a ledger row") are stated with the same confidence and are measurably false (B3, M4).

---

## Verdict

**BLOCKING — 3 blocking, 5 major:** the wave ships a `seat` field with no valid instance (B1) and no
scanner that reads it (B2), and its headline "fails in every era" guarantee is void on precisely the
verdict — WAIVED — that the W-056 remediation just applied to the record the gate was built to catch (B3).

Touched: `docs/reviews/m11-wave-1-review.md` (this file only)
K.8 contracts: none changed by this review.

Filled by: independent reviewing seat (Claude, separate session; did not author the reviewed code) ·
Date: 2026-08-22 · Base ref reviewed against: `1069907`
