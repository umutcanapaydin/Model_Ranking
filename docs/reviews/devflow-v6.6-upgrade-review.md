---
record_type: review
id: devflow-v6.6-upgrade-review
status: draft
process_version: v6.6
date: 2026-09-23
seat: independent
---
# DevFlow v6.4 -> v6.6 upgrade (D-161 amendment): independent review

**Independent:** yes

**Seat:** independent (Code-Reviewer + Tester). I wrote none of this change. My policy came from
`git show main:subagent-profiles/Code-Reviewer.md` and `main:subagent-profiles/Tester.md`, not from
the branch. **Author family / reviewer family:** Claude / Claude, the same family. No second family
was available. The review ran in a fresh context that had not seen the authoring session.

**Subject:** branch `upgrade/devflow-v6.4`, commits `b569de5..e6a6919`:
- `c6ccbca`: the v6.6 apply
- `e49742e`: the fixes for the v6.4 review
- `e6a6919`: the D-161 amendment and the committed v6.4 review

**Base:** `main` = `e66a2b3`. DevFlow tags: `v6.4`, `v6.5`, `v6.6`.

**Method:**
- Fresh clone, with its own venv (`make install`).
- `advisor.db` copied read-only from the owner's tree. Its md5 was `214139e91c691e0273c21673e71d2ba4`
  before and after the copy.
- Exports of HEAD, `main`, `b569de5`, `v6.4` and `v6.6`, used for side-by-side runs.
- 12 in-place mutants plus one control. Each file was restored and its md5 checked.
- **Known red, changed in this clone only:** I deleted line 33 of
  `.github/workflows/issue-agent.yml` (the duplicate `pull-requests: write`) so the full gate
  could run. I put it back after the runs.

## Verdict

**PASS WITH FINDINGS** -- 0 BLOCKING, 2 MAJOR, 3 MINOR, 8 NIT.

The v6.6 apply is clean:
- Every v6.5/v6.6 change to a DevFlow-owned file is in HEAD, except where D-161 keeps the
  project's own version on purpose (`check_records.py`).
- `scripts/check_fast.py` is byte-identical to v6.6's.
- The `work-issue` skill is gone, and nothing points at it.
- `stack.mk` does what D-161 says.
- The coverage floor now runs inside the `test` recipe and is enforced by both `make check` and
  `make check-fast`, with no stale-file race.
- Every gate is green once the owner's workflow line is gone. Historical records stay green with
  no edits.

Of the v6.4 review's findings, MAJOR-1, MAJOR-3, MINOR-1, MINOR-2, MINOR-3 (moot under v6.6's
`check_fast.py`), MINOR-4 (in AGENTS.md) and MINOR-5 hold, and mutants M7, M8 and M10 are now
killed. The fix for MAJOR-2 holds for the case the last seat reproduced (M9). But it closes the
hole in a different way from `main`, and that way leaves two new gaps:
- **MAJOR-1:** a close with no `date:` line can still declare v5.0 and skip three fields. `main`
  refused it.
- **MAJOR-2:** after 2026-09-23, every close is graded by the newest rules, whatever version it
  declares. So the next DevFlow release that adds a wave-close field turns every close written
  from today on red.

Both are one-line fixes in `scripts/wave_check.py:319-321`.

## Findings

### MAJOR-1 -- A close with no `date:` line still declares its way out of three fields (the v6.4 review's MAJOR-2, reopened)

This is the new guard, `scripts/wave_check.py:319-321`:

```python
dated = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
if dated is not None and dated.group(1) > DEVFLOW_ADOPTED:
    version = None
```

It fails open: when there is no date, the declared version is trusted. `main`'s guard failed
closed. It skipped the three fields only when a record was **both** declared old **and** dated on or
before the adoption (`git show main:scripts/wave_check.py`, lines 266-271: `... and dated is not
None and dated.group(1) <= "2026-09-23"`).

*Measured (mutant M9b; scratch export of HEAD vs `main`).* I copied `m16-wave-4-close.md` to
`m17-wave-8-close.md`, declared `process_version: v5.0`, removed the `date:` line, and removed
`Mutant set author:`, `Observed RED:` and `Owner instruction:`.

| Gate | HEAD | `main` |
|---|---|---|
| `wave_check.py` | **PASS**, exit 0, 0 footprint findings | FAIL, exit 1, 3 findings |
| `wave_check_all.py` | PASS, 44 records validated | -- |
| `check_records.py --root .` | PASS (`date` is not required: `schemas/record.schema.json` requires only `record_type`, `id`, `status`) | -- |

The same record skips four more rules, because an undated v5.0 close gets none of them:
- the two review files (v6.0.1)
- `**Independent:** yes` (v6.5)
- the findings table and `Stopped at three attempts:` (v6.6)

*Failure scenario.* An agent closing M17-W2 from an old close as its model, or one that drops the
frontmatter date, gets a green `make check`. Yet it recorded no mutant author, no observed RED, no
owner instruction, and no review file. This is the shape the D-155 adoption review's MINOR-1
reported. The `e49742e` commit message says it cannot happen ("a close written later cannot
declare v5.0 to skip three fields").

The same guard also still trusts closes dated **on** 2026-09-23. M9c, the M9 record dated
2026-09-23, passes on both HEAD and `main`. That was `main`'s design too (NIT-7).

*Remedy:* trust a declared version only when a date is present and on or before the adoption,
which is `main`'s condition.

### MAJOR-2 -- A close dated after 2026-09-23 is graded by every future version's rules, whatever it declares

`version = None` makes `since()` true for every version, including versions that do not exist
yet. Today that equals v6.6. After the next DevFlow upgrade it will not. A close written on
2026-10-01 and stamped `v6.6` will then be asked for fields that did not exist when it was written.
That contradicts `UPGRADING.md` ("closes written earlier are graded by their version") and GPF-001,
which `wave_check_all.py` cites.

*Measured (probe, scratch copies only).* I added a hypothetical field introduced in `(6, 7)` to the
field table of both HEAD's and v6.6's `wave_check.py`. Then I ran each against a close stamped
`v6.6` and dated 2026-10-15:
- **HEAD:** 1 finding for the v6.7 field.
- **v6.6:** 0 findings.

v6.5 and v6.6 each added a `since()` rule (`**Independent:** yes`; the findings table and
`Stopped at three attempts:`), so the next release will probably add another.

*Failure scenario.* On the next DevFlow upgrade, `make wave-check-all` goes red on every close
written after today. The easy ways back to green are to edit historical records or to weaken the
guard. The Makefile, D-161 and GPF-001 all say neither should happen.

*Remedy:* distrust only a declared version that is **older** than the version that was current on
the record's date. For example, for a close dated after the adoption, use
`version = max(version, (6, 6))`, or `None` only when nothing is declared. This keeps what the
date guard is for, and also closes MAJOR-1 if an undated close is treated the same way.

### MINOR findings

- **M1** -- The restored `GP-Agent:` trailer check has no gate-run test.
  `conformance/test-commit-identity.py:266`, self-test case k (lines 109-110). Mutant Mu6
  disables the check:
  - `--self-test`: FAIL (1 wrong).
  - `make conformance`: **PASS**. The conformance runner calls `main()`. Nothing in the
    Makefile, CI or `tests/` runs `--self-test` (`grep -rn 'commit-identity' tests/ Makefile
    .github/workflows conformance/run-all.py` finds nothing).

  The wave_check fixes are guarded by `tests/unit/test_wave_check_versions.py`, which runs in
  `make test`; this one is not. *Failure scenario:* the next DevFlow upgrade takes v6.x's
  `test-commit-identity.py` verbatim, as the v6.4 step did. The check disappears, and every gate
  stays green. That is exactly how MAJOR-3 happened. *Remedy:* a `tests/unit` test that runs
  `--self-test` and asserts case k, or a `conformance` leg that runs it.
- **M2** -- Live documents still claim more for the trailer than the amendment concedes.
  - D-161's amendment (`docs/decisions.md:2845-2848`) says the trailer on owner-identity session
    commits is "a convention nothing can check".
  - `AGENTS.md:42` still says the trailers make it "so no agent commit reads as the owner's own"
    and that `test-commit-identity.py` "verifies the range".
  - `.agents/rules/git-authority.md:14-18` still says the tool "still verifies" that "no commit
    may be mistaken for the owner's".

  *Failure scenario:* an agent or reviewer reads AGENTS.md and trusts a green identity check on
  a branch of owner-identity commits that carry no trailer. *Remedy:* one clause in each saying
  the check is mechanical only for the machine identity.
- **M3** -- The ledger's owner rule has two answers in the live tree.
  - The project's C2c (`scripts/check_records.py:1007`) accepts only a milestone as the owner of
    an ACCEPTED row. I confirmed this: a reason naming only `#42` fails the regex.
  - `docs/warnings.ledger.md:14` says so.
  - The same file's table header, line 17, says "reason + owner (milestone or issue)".
  - `docs/warnings.ledger.template.md:24-25,43,62` (v6.6 verbatim) tells authors that an issue
    `#42` is the preferred owner and that "`C2c` fails without both".

  *Failure scenario:* a new warning row written from the header or the template, with an issue as
  its owner, turns `check-records` red. The result is safe but noisy. *Remedy:* make line 17 say
  "milestone" and note the difference in the template, or accept `#\d+` in the project's C2c.

### NITs

1. **D-161's validator numbers** (`docs/decisions.md:2839-2840`). The amendment says v6.6's
   validator reports "121 R2 findings (122 counting a record type this project added)". Measured
   with v6.6's `check_records.py --root <tree>`:
   - `main`: 121 findings = 120 R2 + 1 C2b.
   - `b569de5`: 122 = 121 R2 + 1 C2b.
   - HEAD: **124** = 123 R2 + 1 C2b.

   The committed `devflow-v6.4-upgrade-review.md` adds two: v6.6's list has no `record_type:
   review`, and it has no field `seat`. This review adds two more. The C2b finding
   (`docs/warnings.ledger.md`: the same control ACCEPTED 3x) is not R2, and the amendment's
   "therefore not checked here" list does not name it. v6.4's validator gives identical counts.
   Also, `slopsquat_check.py`'s difference from v6.6 is lint plus the project's own docstring (on
   `main` already), not lint alone.
2. **Mutant Mu5 survives.** `scripts/wave_check_all.py:83` accepts `v6.0.1`-style stamps through
   `(?:\.\d+)*`, but no test uses a three-part stamp
   (`tests/unit/test_wave_check_versions.py:46` has only two-part versions). Dropping the group
   stays green.
3. **Mutant Mu11 survives.** `tests/unit/test_check_fast.py:53-60` pins that the floor runs, and
   runs after pytest, but not that its failure fails the recipe. A `-` prefix on `Makefile:96`
   plus a failing floor: `make test` exit 0 ("Error 1 (ignored)"), and the unit test passes.
4. **The trailer match is a substring.** `conformance/test-commit-identity.py:266`
   (`AGENT_TRAILER not in body`). A machine commit whose subject says "... GP-Agent: nothing"
   passes, though git's trailer parser finds no `GP-Agent` trailer (measured). `main` had the same
   test.
5. **D-161 clause 2 was not amended** (`docs/decisions.md:2787-2788`). It still says the issue
   agent "commits as `gp-agent`", with `test-git-authority.py` as the enforcement. The v6.4
   review's MINOR-4 was fixed in `AGENTS.md:42` ("until then it commits as `gp-issue-agent`") but
   not here.
6. **"Five weeks" in the process-log** (`docs/process-log.md`, last entry). The duplicate key
   dates from `8152490`, on 2026-08-11. That is six weeks. `gh run list --workflow
   issue-agent.yml` shows 0-second failures on `push` events up to today, which fits "GitHub
   rejects the file".
7. **`DEVFLOW_ADOPTED` is inclusive** (`scripts/wave_check.py:270`). A close dated today can
   still declare v5.0 (M9c passes on both HEAD and `main`). The date is today, so this matters
   only for closes written today.
8. **A close with neither `process_version` nor `date:` is never graded by `wave-check-all`.**
   `scripts/wave_check_all.py:86-93` puts it in the out-of-scope ("legacy") set. This was
   already true on `main`; it is listed here because it is next to MAJOR-1.

### K.9 (outside this change)

- **K1** -- `conformance/test-ci-yaml.py` run with a Python that has no PyYAML (the system
  `python3` here) reports `NOT-EVALUABLE` on `ci.yml` and exits 2. v6.5's changelog says the line
  reader "grades on every machine". `make` uses the venv, which has PyYAML, so the gate is not
  affected. This is a DevFlow field finding.

## Focus questions

1. **The v6.6 apply** (`git diff v6.6 HEAD` on every path v6.4..v6.6 touched: 51 files).
   - 39 files are identical to v6.6. That includes `scripts/check_fast.py` (`cmp`: identical),
     `.claude/**`, `INSTALL.md`, `UPGRADING.md`, `test-ci-yaml.py`, `test-check-fast.py`,
     `test-hook-claims.py` and the conformance fixtures.
   - For the other 12, I checked every line v6.5/v6.6 added against HEAD. The only v6.5/v6.6
     lines missing are:
     - `check_records.py` (L1 unclosed fence, the issue-owned C2c): the project's validator is
       kept on purpose, and the amendment says so.
     - `docs/warnings.ledger.md:14` (the project's ledger, see M3).
     - README's hook sentence (the project's README).
     - AGENTS.md's K.7 line, which the project extended and did not lose.
     - `ci_liveness.py`'s two lint edits.
   - **No v6.5/v6.6 change was lost silently.** `scripts/wave_check.py` has every v6.5/v6.6 rule
     (Independent, findings table, `Stopped at three attempts`).
   - **Project controls kept:** W-015 (`bootstrap-check.sh:42`), `runner_verdict.sh` (manifest and
     README), K.7 `review_seat_problems`, the `check:` line (with `coverage-floor` moved into
     `test`), and the project's Done-Evidence section in `practices.md`.
   - `.claude/skills/work-issue/` is gone. `git grep work-issue` outside records finds only the
     verdict name in `fix-issue`, `triage-issue` and `pipeline-schema.html`, which is intended.
2. **stack.mk and the floor.**
   - `make check-fast-config` prints `own: client-decls swift-test` and
     `forms: swift-test=swift-test-parallel` (exit 0).
   - `--plan` prints six legs: `lint`, `typecheck`, `test`, `swift-test=swift-test-parallel`,
     `client-decls`, and `records` (`check-records check-records-selftest install-check
     harvest-context-check shell-dialect wave-check-all conformance`).
   - **W-041 is enforced** in both gates. As a control, I raised `FLOOR` to 95:
     - `make test`: exit 2.
     - `make check-fast`: exit 2, `test` leg FAIL ("aider.py is at 90%, below the 95% floor"),
       every other leg PASS.
   - **No stale-file race:** nothing in the `records` leg writes or reads `coverage.json` (grep of
     `conformance/`, `scripts/`, `tests/`), and the floor runs only after pytest has succeeded.
   - `PYTEST_ADDOPTS="-n auto --dist loadgroup"` plus the recipe's own `-n auto` is harmless. Both
     runs had 8 workers and 1202 items, and `tests/` has no `xdist_group` marker, so `loadgroup`
     acts like `load`.
   - The floor would still read an old `coverage.json` if someone ran pytest with `--no-cov`. That
     was already the case before this change.
3. **The fixes for the v6.4 review's findings.**
   - **MAJOR-1 holds.** M8 (m16-wave-4 re-stamped `v6.6`): `wave-check-all` reports "1 record(s)
     failed, **0 without the stamp**", graded under v6.6's rules. The P-005 half is settled by the
     owner's ruling, and no live document still states the risk tiers.
   - **MAJOR-2 partly holds.** M9 (v5.0, 2026-10-15, no fields) is killed on HEAD, with the 3
     footprint findings. But see MAJOR-1 and MAJOR-2 above.
   - **MAJOR-3 holds.** M10 (a `gp-agent` branch commit with no trailer, in a scratch clone):
     HEAD fails it, and so does `main`. With the trailer it passes. See M1 and M2 above.
   - **MINOR-1 holds.** M7 (a dangling `docs/reviews/` and `docs/plans/` path added to AGENTS.md):
     HEAD FAIL, 2 dangling, the same as `main`.
   - **MINOR-2 holds.** `AGENTS.md:112` points at `make closure-check FILE=...`, and the comment at
     `Makefile:319` is corrected.
   - **MINOR-4 holds** in `AGENTS.md:42` but not in D-161 (NIT-5).
   - **MINOR-5 holds:** it is stated in the amendment.
4. **Historical records.**
   - `make wave-check-all`: exit 0, 43 validated, 20 out of scope.
   - `check_records.py --root .`: PASS, 200 records. `--self-test`: 0 problems.
   - `git diff --name-status b569de5 HEAD -- docs/plans docs/reviews` shows only
     `A docs/reviews/devflow-v6.4-upgrade-review.md`.
   - The four changed `conformance/` fixtures equal v6.6's.
5. **D-161 amendment claims.**

| Claim | Reproduced? |
|---|---|
| `check_fast.py` byte-identical to v6.6 | yes (`cmp`) |
| `stack.mk` values | yes |
| v6.6's validator: 121 R2 (122) | no: 121 = 120 R2 + 1 C2b on `main`, 124 at HEAD (NIT-1) |
| five lint-fixed scripts + `ci_liveness.py` | yes: `coverage_floor`, `create_labels`, `gen_schema`, `slopsquat_check`, `write_install_marker`, + `ci_liveness` (NIT-1 on slopsquat) |
| `closes` fails the 20 pre-migration wave records | yes: 63 wave closes, 20 fail (all undeclared, dated 2026-08-11/15/16); closure reports 15 of 16 fail; `make closes` exit 2 |
| bootstrap-check C11 fails pending #13 | yes (below) |
| the duplicate `pull-requests` makes conformance red | yes: `test-ci-yaml` FAIL `issue-agent.yml:33` with the line present, exit 1 |
| date guard / trailer check / derived scope restored | yes, with MAJOR-1 and MAJOR-2 |

## Mutants (in place in the clone; each restored, md5 verified, `git status` showing only the known workflow edit)

| # | Mutation | Killing check | Result |
|---|---|---|---|
| Mu1 | `wave_check.py:320` `>` -> `<` | `test_wave_check_versions.py` | **RED** (2 failed) |
| Mu2 | `wave_check.py:321` `version = None` -> `pass` | same | **RED** (1 failed) |
| Mu3 | `DEVFLOW_ADOPTED` -> 2026-12-31 | same | **RED** (1 failed) |
| Mu4 | `wave_check_all.py:84` `(5, 0)` -> `(6, 0)` | unit test; `wave_check_all.py` | **RED** / **RED** ("40 without the stamp") |
| Mu5 | `wave_check_all.py:83` drop `(?:\.\d+)*` | unit test; `wave_check_all.py` | GREEN / GREEN -- **survived** (NIT-2) |
| Mu6 | `test-commit-identity.py:266` trailer clause -> `False` | `--self-test`; `make conformance` | **RED** / GREEN -- survives every gate (M1) |
| Mu7 | `stack.mk` drop `swift-test` from own legs | `test_check_fast.py`; `test-check-fast.py` | **RED** / GREEN |
| Mu8 | `stack.mk` `CHECK_FAST_FORMS =` (empty) | same | **RED** / GREEN |
| Mu9 | `stack.mk` typo `client-decl` | same | **RED** / **RED** |
| Mu10 | `Makefile:96` floor line removed | `test_check_fast.py` | **RED** |
| Mu11 | `Makefile:96` prefixed `-`, with `FLOOR` 95 | `test_check_fast.py`; `make test` | GREEN / GREEN (exit 0, "Error 1 (ignored)") -- **survived** (NIT-3) |
| Mu12 | `check_fast.py:125` own-leg validation off | `test_check_fast.py`; `test-check-fast.py` | **RED** / GREEN |
| Ctl | `FLOOR` 95 only (control) | `make test`; `make check-fast` | **RED** exit 2 / **RED** exit 2 |

**Result: 10 of 12 mutants killed by a gate, and Mu6 only by a self-test that no gate runs.**

**Scratch-copy mutants:**
- **M7:** killed.
- **M8:** graded, "0 without the stamp".
- **M9:** killed.
- **M9b** (no date): **survived** on HEAD, killed on `main` (MAJOR-1).
- **M9c** (dated 2026-09-23): passes on both (NIT-7).
- **M10:** killed.
- **Future-field probe:** HEAD 1 finding, v6.6 0 findings (MAJOR-2).

## Gate results (clone, macOS, Python 3.14 venv, owner's `advisor.db`, line 33 deleted)

| Gate | Exit | Result |
|---|---|---|
| `make install` | 0 | marker `v6.6 · manifest 1678c1de6740` |
| `make check-fast` | 0 | PASS in 41.9 s, 6 legs |
| `make check` | 0 | 1 min 20 s |
| `make gate` | 0 | 1 min 34 s: `gate PASS: check conformance falsify secrets deps slopsquat` |
| `make bootstrap-check` | 2 (script exit 1) | 1 fail / 2 warn, BLOCKING |

- **`make check-fast` legs:** lint 0.8 s, typecheck 9.1 s, records 12.4 s, test 12.9 s,
  client-decls 18.6 s, swift-test (parallel form) 41.8 s.
- **`make check`:**
  - ruff: clean
  - mypy: 36 files, no issues
  - pytest: 1187 passed, 15 skipped; coverage 90.24%
  - coverage-floor: PASS, 36 modules, inside `test`
  - check_records: PASS
  - self-test: 0 problems
  - install-check: PASS
  - shell-dialect: 11 scripts
  - wave-check-all: 43 / 20
  - conformance: 16 tests, 0 failing
  - swift-test: 268
  - client-decls: 11 files in 4 configurations
- **`make gate`:** as `make check`, plus gitleaks (no leaks), pip-audit (no known
  vulnerabilities), slopsquat (17 dependencies, 0 suspect), and falsify (SKIPPED: this is an
  installation).
- **`make bootstrap-check` findings:**
  - `[FAIL]` C11: no `core.hooksPath`, and the brief does not record Actions or branch protection.
    This is expected until the owner's issue #13.
  - `[warn]` license-review: none present.
  - `[warn]` ci-liveness: the last 2 CI runs started no step.
- **With line 33 present:** `test-ci-yaml` exits 1 on `issue-agent.yml:33`, so `conformance` and
  therefore `check` and `gate` are red. This is the known owner item.
