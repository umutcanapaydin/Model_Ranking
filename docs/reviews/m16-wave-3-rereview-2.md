---
record_type: review
id: m16-wave-3-rereview-2
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16-W3 -- independent re-review of the second fix round (D-156 second amendment, commits ea41412..a061dfc)

**Seat:** independent (Code-Reviewer + Tester combined). I wrote none of this wave, its first fix
round or this one.

**Scope:** the second fix round `486b765..a061dfc`, three commits:
- `ea41412` and `fb88064` are the red tests.
- `a061dfc` is the fix. It also commits the re-review record itself.

I read the round against the findings of `docs/reviews/m16-wave-3-rereview.md` and against the
"Second amendment" at the end of D-156 in `docs/decisions.md`.

**Policy:** I read my policy only from `git show origin/main:subagent-profiles/Code-Reviewer.md`
and `.../Tester.md`. The diff touches no policy file (no `subagent-profiles/`, `AGENTS.md` or
`.agents/` path). Nothing in it tries to instruct a reviewer, so there is no injection-class
finding.

**Families:** the author is recorded as Claude, and this seat is also Claude. No second family was
available to me, so this is the fallback. My context was fresh: I did not see the author's session
or either earlier seat's session.

**Snapshot.** Every result below is against HEAD `a061dfc` and these md5s:
- `build.py` `88a7ea1c...`
- `refresh.py` `04c31a46...`
- `nightly.py` `70d0596d...`
- `test_refresh_carry.py` `95430c5c...`
- `test_carry_forward.py` `ac43c3dc...`
- `test_nightly_refresh.py` `d0e1bb2e...`

The owner's `advisor.db` and `advisor.db.refresh.json` were `ef9e48a9...` and `7e0355ed...` before
and after my work. I read the served artifact only as a copy in the session scratch directory.

**How I worked:**
- I did all work in a `cp -R` of the tree in the session scratch directory.
- In that copy, the editable install's `.pth` was repointed at the copy's own `src`. Without that,
  subprocess tests would have run the owner's code and not the mutant.
- `make` ran with `-o install`, because the copied `pip` shebang points at the owner's venv.
- I replayed the red commits from a `git archive fb88064` of the copy.

I ran no git command that changes state in the repository. I started nothing on :8080. The only
repository file I created is this one.

Three untracked files appeared in the owner's working tree during the review: the expected close
draft, and two files I did not create (an HTML page, and a Markdown note at the root). I left all
three untouched.

## Verdict

**PASS-WITH-MINORS: 0 BLOCKING, 0 MAJOR, 3 MINOR, 2 NIT.**

**What this round got right.** Both of the re-review's blocking-class findings are closed where
they act, through the real `refresh()`:
- **BLOCKING-1 is closed.** An expiry night is now a cycle test. Reverting the exemption (R1, R5),
  widening it to everything (R4) and widening it to arrived sources (R7) are each RED.
- **MAJOR-1 is closed.** The S5 night (an expired secondary source beside a fresh source that went
  blind) is now refused. That test failed before the fix for the right reason: "the served content
  changed", `assert 0 == 3`.

The new baseline `_served_without` is read-only, as INV-23 requires: `open_readonly`, `backup` into
`:memory:`, and deletes only in the in-memory copy. I measured it: the served file's bytes, its
mtime and the directory listing were unchanged. R8, which deletes from the served file itself, is
RED on 4 tests.

The count and budget guards are excused by exactly the expired rows. On this schema, the
`models`, alias and reconciliation state cannot over- or under-excuse: reconciliation maps each row
by its own name, `registry.py:380`, and the ranking joins `scores` and `px_median`.

**What remains.** Three MINORs:
- One guard is now weaker than before, and the amendment does not say so. The D-132 new-names and
  median check runs against a baseline that can be blind, so a roster can be replaced on an expiry
  night (MINOR-1). Today it is latent, and D-132's own "a surface returning" rule would admit the
  same roster one night later.
- The clamp for rows stamped in the future has no bound. Rows 400 days ahead carry for 400 + 30
  days (MINOR-2).
- Two state-transition claims are still unpinned. One of them sits behind a test whose name says it
  pins it (MINOR-3).

## Disposition of the re-review's findings

| Re-review | Disposition | Evidence I ran |
|---|---|---|
| BLOCKING-1 (the MAJOR-1 fix is not held by any cycle test; the exemption's scope is unpinned) | **CLOSED** | `test_refresh_carry.py:250` (publishes through the real cycle) and `:265` (the fresh source beside the expiry is still refused). Replayed at `fb88064` with the pre-fix `src`, both FAIL: `:250` with "coding's median price would move up 98%", `:265` with "the served content changed". Both are green at HEAD. The analogs of the old N5 and N15 are RED: R1 and R5 on 3 tests each, R4 on 2 and R7 on 1. |
| MAJOR-1 (an expiry excuses the whole surface) | **CLOSED** for the loss guards. The new baseline opens MINOR-1. | `refresh.py:918` builds the baseline, `:735-741` judges both guards against it, and `_served_without` is `:800-828`. S5 replay (my A1 control, and `:265`): exit 3, "coding answered with 2 models". R2 (scores only) and R3 (no `px_median` re-derivation) are each RED on `:333`. |
| MINOR-1 (future stamps expire; `/health` prints negative ages) | **CLOSED.** The fix opens MINOR-2 (no bound). | `build.py:226` and `:241`: rows ahead of now carry at 0.0. `nightly.py:182` prints `?d`. B1 is RED on `test_carry_forward.py:262`, B2 (the arrival clamped too) is RED on `:196`, and N1 is RED on `test_nightly_refresh.py:567`. All three tests FAIL at `fb88064`. |
| MINOR-2 (state transitions no test pins) | **PARTLY OPEN** (MINOR-3) | Closed: N13, now R10, is RED on `:322`, and the "no loss is excused" half of S7 is RED on `:285` (R12). The `write_status` half of N12 is pinned by `:313`. Still open: R9 (the cycle drops `carried` on an unchanged night) is GREEN. R11 (an unreadable report read as "everything arrived", the old N18) is GREEN although `:285` is named for it. R13 (a refused cycle records no `expired`, the old N17) is GREEN. |
| MINOR-3 (the floor gate holds code == record, never record == measurement) | **CLOSED-BY-RECORD** | W-128 in `docs/warnings.ledger.md` is ACCEPTED with a reason, an owner (the M16 closure) and a control. The reason is sound: a test pinned to one night's artifact would go red on the next refresh. |
| NIT-1 (the carried-insert guard has no test and is silent) | **CLOSED** | `test_carry_forward.py:274`. B4 (a stray `since`), B5 (no re-reset) and B6 (the guard removed) are each RED. The fix commit strengthened this red test: the stale row is now committed before the pending reset, so the rollback really does restore it. As first committed, the test could not see B5: I measured B5 GREEN against the `fb88064` version of it. Strengthening a red test in the green commit is a change in the right direction, not weakened-to-green. |
| NIT-2 (what `expired` means after a cycle that is not served) | **CLOSED-BY-RECORD** | D-156 second amendment, third bullet: `expired` means age, not presence. The failed-cycle case is pinned (`test_refresh_carry.py:157`). The refused-cycle case is not (R13, MINOR-3). |
| NIT-3 (`.sources` scratch leaks before the `try`) | **CLOSED-BY-RECORD** | W-124, which gains a paragraph with the same remedy and owner. The code is unchanged (`refresh.py:868-878` still precede the `try` at `:881`), as the record says. |

## Mutants

Every mutant was applied in place to the copy, one at a time. I ran the four carry and refresh test
files on it, and the full suite whenever those stayed green. Then I restored the file and
md5-checked it byte-identical (log below).

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| R1 | `refresh.py:918` `baseline = live`: no expiry excuse at all | RED, 3 (`:250`, `:123`, `:265`) |
| R2 | `_served_without` deletes `scores` only, not `pricing` | RED `:333` |
| R3 | `_served_without` does not re-derive `px_median` | RED `:333` |
| R4 | `_served_without` deletes EVERY source's rows (the N15 analog: excuse everything) | RED `:265`, `:333` |
| R5 | `:737` `degradations(live, …)`: count and budget not excused | RED, 3 (`:250`, `:123`, `:265`) |
| R6 | `:741` `upward_anomalies(live, …)`: median not excused | RED `:250` |
| R7 | the baseline also drops ARRIVED sources' rows | RED `:265` |
| R8 | INV-23 broken: the baseline deletes from the served file | RED, 4 |
| **R9** | **`:929` the unchanged record drops `carried` (N12, cycle half)** | **GREEN, 1062 passed** (MINOR-3) |
| R10 | `:579` `carried` not filtered against `expired` (N13) | RED `:322` |
| **R11** | **`:792` an unreadable report reads as "everything arrived" (N18)** | **GREEN, 1062 passed** (MINOR-3) |
| R12 | an unreadable report reads as "the source expired" | RED `:285`, plus 4 in `test_refresh.py` |
| **R13** | **`:945` a refused cycle records no `expired` (N17)** | **GREEN, 1062 passed** (MINOR-3) |
| *R14* | *judge against live whenever something is also carried* | *GREEN, 1062 passed* (NIT-2; contrived) |
| B1 | `build.py:226` no clamp: rows ahead of now expire | RED `test_carry_forward.py:262` |
| B2 | `:233` the arrival record is clamped too (no fallback to the rows) | RED `:196` |
| B4 | `:289` a failed carried insert keeps its `since` | RED `:274` |
| B5 | `:287-288` a failed carried insert is not re-reset | RED `:274` |
| B6 | the carried insert is unguarded (`except ZeroDivisionError`) | RED `:274` |
| N1 | `nightly.py:182` negative ages printed again | RED `test_nightly_refresh.py:567` |

**Totals:** 20 mutants, 16 RED and 4 GREEN. The fourth GREEN, R14, is a contrived mutant that I
report only as a coverage note.

**Killer tests.** I wrote two tests in scratch, not in the repository, for the MINOR-3 remedy. Both
pass on HEAD, and each kills its mutant: R9 is RED on the first, R11 on the second. I re-ran R1
beside them as a control, and it was still RED.

**The fix is red->green, replayed.** I ran the three red commits' tests against the pre-fix `src`
(`git archive fb88064`), in the copy's venv. **5 FAIL**, and they are exactly the tests this round
adds for the re-review's findings:
- `:250`
- `:265`
- `test_carry_forward.py:262`
- `test_carry_forward.py:274`
- `test_nightly_refresh.py:567`

All 5 are green at HEAD.

## Findings

### MINOR-1 -- the baseline can be BLIND, and D-132 treats a blind baseline as "a surface returning", so an expiry night can replace a whole roster unchecked

`upward_anomalies` now runs against the baseline (`refresh.py:741`), and it skips a surface that
was blind in its first argument (`:156`, `if not was: continue`). It also skips the median when
the "before" median is 0 (`:171`).

Suppose every live row of a surface came from sources that expire tonight. Then the baseline has
that surface empty. Whatever the candidate puts there is then treated as a surface RETURNING:
- The new-names check does not look at it.
- The median check does not look at it.

**Measured** (scenario A1: fakes, the real `refresh()` and `build.main`):
- **The set-up.** Live `coding` is served only by three `epoch_swe_bench_verified` rows. `swebench`
  then arrives with four names this artifact has never served.
- **Carry night** (the epoch rows are 10 days old): **exit 3**, "coding would be 4 of 7 models this
  artifact has never seen (57%)".
- **Expiry night** (the epoch rows are 45 days old): **exit 0**, "the served content changed". Live
  `coding` goes from {Claude 4.5 Opus, GPT-5, GPT-5 nano} to {Claude 4.5 Haiku, Claude 4.5 Sonnet,
  GPT-5 Pro, GPT-5 mini}.
- **Against the live artifact**, `upward_anomalies` still says "4 of 4 models this artifact has
  never seen (100%)". The whole-surface rule this replaces would have refused.

**Why MINOR and not MAJOR:**
- **It is latent in today's source set.** On a copy of the served artifact, 13 of 14 surfaces'
  primary boards are fed by exactly one source, and no other source writes those benchmarks.
  `coding` has two sources, but `swebench` is required, so its expiry fails the build before any
  comparison.
- **It moves an exposure that exists anyway by one night, rather than creating one.** After the
  expiry night publishes a blind surface, D-132's ruled "a surface returning" exemption admits any
  roster the following night.

What it does break is the amendment's own sentence, "excuses exactly the loss those rows account
for, on every guard". The new-names guard is excused beyond the loss. The case becomes reachable
the day a board gains a second source, or `swebench` becomes optional.

*Remedy (either one):*
- **Keep the "was blind" test and the new-names set on the LIVE summary.** Removing rows never adds
  new names, so the expiry needs no excuse there. Keep the MEDIAN on the baseline, falling back to
  live's median when the baseline surface is blind. The A1 expiry night becomes the test, and it
  must be exit 3.
- **Or state the cost in the amendment** for the owner to accept.

### MINOR-2 -- the future-stamp clamp has no bound: rows stamped D days ahead carry for D + 30 days

`Carry.age_days` clamps the rows' fallback stamp to age 0 (`build.py:241`, via `_age(..., clamp=True)`
at `:226`). The comment says this is "bounded by the clock's error, not by a stamp anyone can
write". That is true of the stamp's ORIGIN: `observed_at` is `RunContext`'s local
`datetime.now` (`ingest.py:52`). It is not true of the bound's SIZE, which is the size of the error.

**Measured** (scenario C). Take rows and an arrival written during a forward clock excursion of
400 days, then a correct clock and a failing source. The age is **0.0 on night 0, 0.0 on night 31
and 0.0 on night 60**, with or without an arrival record. `build()` reports `carried={'aider': 0.0}`,
`since` 2027-10-28. The source carries until real time reaches the stamp, and then for 30 more
days. For a 1-hour excursion the behaviour is right: it expires on night 31.

Before this round the same input expired at once, which was the re-review's MINOR-1 in the other
direction. That seat's remedy said "treat a future stamp as age 0" and gave no bound. The unbounded
carry follows from it, so the gap is partly the previous seat's.

Two docstrings are now false for this case:
- `Carry` (`build.py:202`): "can only overstate the age, never hide it".
- `_read_last_ok` (`build.py:612`): "the stricter age, never a laxer one".

The clamp can hide the age.

*Remedy:*
- Clamp only within a tolerance, for example `-CARRY_MAX_AGE < age < 0` gives 0.0. A stamp further
  ahead is `None` and expires. That bounds the worst case at twice the ruling.
- Add a test with rows 400 days ahead that expects `expired`.
- Correct the two docstrings.

### MINOR-3 -- two of the re-review's MINOR-2 state transitions are still unpinned, and the test named for N18 cannot fail on it

- **R11 (N18) is GREEN.** `test_refresh_carry.py:285` says it pins "never as 'everything
  arrived'". Its cycle is REFUSED, though, and a refused cycle never records arrivals
  (`refresh.py:561`, `served = code in (EXIT_PUBLISHED, EXIT_UNCHANGED)`). So
  `sources_last_ok == seeded` holds whatever the report is read as. The "excuses nothing" half is
  real (R12 RED). The "moves no clock" half is coverage theater (Tester profile §1). The code is
  right today (`:792` returns empty).
- **R9 (N12, the cycle half) is GREEN.** `:313` pins that `write_status` keeps `carried` when it is
  HANDED one on an unchanged cycle. Nothing pins that `_cycle` hands it (`:929`). That is the
  regression the re-review described: the carry erased from `/health` on every quiet night.
- **R13 (N17) is GREEN.** The amendment now says what `expired` means after a cycle that is not
  served. The failed case is pinned, and the refused case is not.

*Remedy.* These are two tests, both verified in scratch: each passes on HEAD, and R9 or R11 is RED
on it. The first is an unchanged cycle through `refresh()`:

```python
def test_an_unchanged_cycle_through_refresh_keeps_the_carry(tmp_path, monkeypatch):
    live = _first_cycle(tmp_path, monkeypatch)
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    assert refresh(live)[1] == EXIT_PUBLISHED
    carried = _record(live)["carried"]
    assert refresh(live)[1] == EXIT_UNCHANGED
    assert _record(live)["carried"] == carried
```

The second is the `:285` builder with a torn report on a PUBLISHED cycle, `swebench=None` and no
epoch rows. It asserts `sources_last_ok["swebench"] == seeded`. Add one assertion for R13, or record
that a refused cycle's `expired` is deliberately unpinned.

### NIT-1 -- `_served_without` runs outside the cycle's controlled failure paths

`refresh.py:918` calls it before the unchanged check. It is not guarded. A live artifact removed,
or replaced by a non-database, between `fingerprint_of` and this line raises `sqlite3.Error`. I
measured it on a missing path. `refresh()`'s catch-all then records "the cycle crashed" and
re-raises. This is safe (nothing is published), but it is the crash path rather than the
`UnreadableArtifact` refusal every other live read gets. The next line's re-read already handles
the replaced-artifact case properly. Moving the baseline after the unchanged check, and routing its
error to the existing refusal, would make the behaviour match.

### NIT-2 -- no cycle test has a carry and an expiry on the same night

R14 (judge against live whenever something is also carried) is contrived, but it is GREEN because
no cycle test combines the two. An Epoch bundle past 30 days on the same night as an Arena timeout
is exactly that night. One cycle test would cover it.

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant 1: on an expiry night, only the expired rows' loss is excused.**
- There is one producer of `expired`: `Carry.restore`, `build.py:274`, the only writer of
  `self.expired`.
- It is carried to the refresh by `sources_json` and read by `_read_build_sources`
  (`refresh.py:774-797`).
- There is one consumer: `refresh.py:918`.
- Citing tests: `test_refresh_carry.py:123`, `:250`, `:265`, `:285` and `:333`.
- Gaps: MINOR-1 (the new-names guard) and NIT-2.

**Invariant 2: INV-23, the served file is never written.**
- The new producer is `_served_without` (`refresh.py:812-816`, `open_readonly` then `backup`).
- Citing tests: R8 is RED on 4 tests, because writing the live file trips the pre-publish re-read.
- My scenario A3 checked the served file's bytes, its mtime and the directory listing before and
  after.
- Gaps: none found.

**Symbol check** (`grep -rn "_served_without\|_surfaces_fed_by\|excused" src tests scripts`):

```
src/app/workflows/refresh.py:779:    Empty is the safe reading: no arrival moves a clock, and no loss is excused."""
src/app/workflows/refresh.py:800:def _served_without(target: Path, sources: set[str]) -> ServingSummary:
src/app/workflows/refresh.py:918:        baseline = _served_without(target, set(expired)) if expired and live else live
tests/unit/test_refresh_carry.py:338:    from app.workflows.refresh import _served_without, fingerprint_of
```

`_surfaces_fed_by` and the `excused` parameter are gone, with no caller left behind. The PRD row for
REQ-REF-009 names `_served_without` in their place.

## Tester protocol on load-bearing paths (atomic log)

The load-bearing behaviours I chose:
- the baseline's three deletions and the re-derivation
- each guard's argument
- the read-only rule
- the clamp and its fallback order
- the carried-insert guard's three effects
- the record's state transitions
- the negative-age print

A mutation script in the session scratch directory did the following for each mutant:
1. Read the target file and took its md5.
2. Replaced exactly one unique string, refusing if it did not match exactly once.
3. Ran `pytest -n auto --no-cov` on the four carry and refresh files, and ran the full suite
   whenever those stayed green.
4. Wrote the original bytes back.
5. Asserted the md5 equal.

No restore failed. After the run, the copy's three source md5s matched the snapshot. The
repository tree was never mutated: `git status --short` showed the same entries before and after,
apart from this file and the two files named above, which were not mine.

## Gates

`make -o install -o .venv/bin/python gate` ran on the copy, with the close draft deleted there
only, and then `make -k` ran the legs after the first stop:
- **lint:** ruff "All checks passed!".
- **typecheck:** mypy "Success: no issues found in 34 source files".
- **test:** pytest **1062 passed, 15 skipped**, total coverage 90%. The touched modules are
  `build.py` 94%, `refresh.py` 96% and `nightly.py` 99%. Every line this round adds is executed:
  the uncovered spans are older code, and `build.py:278-290`, the guard the re-review found
  unexecuted, is now covered.
- **coverage-floor:** "PASS: 34 module(s)".
- **records:** `check_records` PASS and its self-test PASS; install-check passes.
- **shell-dialect:** PASS.
- **wave-check-all:** "PASS: 41 ... record(s)".
- **conformance: FAIL, 1 of 14.** `test-documented-paths` finds 3 dangling references to the close
  draft: `m16-wave-3-review.md:45` and `:320`, and `m16-wave-3-rereview.md:287`, which this round
  commits. That is only the deletion. With the draft present, conformance passes (0 dangling) and
  wave-check-all fails by design (V3C-69: the draft cites no review yet and 3 rows lack evidence).
  **The branch cannot be gate-green in either state until the close record is completed and
  committed.** That is expected, and it is not a finding against this round.
- **swift-test:** PASS, 268 tests, after removing the copied `ios/.build` cache, which is bound to
  its path.
- **client-decls:** PASS, 4 configurations.
- **falsify:** SKIPPED (an installation, not the distribution package).
- **secrets:** 2 generic-api-key hits, both in the untracked HTML page that appeared in the owner's
  tree during this review. It is not part of this branch. With it removed from the copy, gitleaks
  reports "no leaks found".
- **deps:** pip_audit "No known vulnerabilities found".
- **slopsquat:** PASS, 17 dependencies.

## What I did not check

- Any live network cycle, or the real Epoch bundle directory. Every cycle ran on fakes, or on copies
  of the served artifact.
- Whether a forward clock excursion of more than a day is plausible on the owner's Mac (MINOR-2's
  premise), or whether any upstream is expected to join a single-source board soon (MINOR-1's
  trigger).
- Whether `build_price_medians` today derives the same `px_median` the live artifact was built with.
  A change to that function between builds would move every baseline price, on expiry nights only.
- Plans and subscription tables. `serving_summary` does not read them, so the baseline cannot
  over- or under-excuse through them. That also means no refresh guard covers them; the gap
  predates this wave.
- Security aspects (Stage 4.0), the `/v1` contract (unchanged), and the owner's acceptance recorded
  in `486b765`.
