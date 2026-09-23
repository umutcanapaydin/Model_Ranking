---
record_type: review
id: devflow-v6.4-upgrade-review
status: draft
process_version: v6.4
date: 2026-09-23
seat: independent
---
# DevFlow v6.0 -> v6.4 upgrade (D-161): independent review

**Verdict: PASS WITH FINDINGS** -- 0 BLOCKING, 4 MAJOR, 5 MINOR, 8 NIT.

The mechanical parts of the merge are sound. The `check:` line is byte-identical to `main`'s. The
82 encoding edits are all in the right calls. W-015, the K.7 review-seat gate and the project's
record validator came through. The numbers in D-161 reproduce, apart from one that is off by one.
The problems are where the upgrade quietly took v6.4's version of a control this project had
changed on purpose:

- **Wave-close grading.** It now contradicts D-161 and the version the tree declares (MAJOR-1).
- **Two fixes from the D-155 adoption review are undone.** The date guard on old-version stamps is
  gone (MAJOR-2), and so is the `GP-Agent:` trailer check on agent commits (MAJOR-3).
- **The Stage-0 gate went red.** It was green on `main`, and nothing records the change (MAJOR-4).

None of these goes wrong in a way that hurts the product. Two of them (MAJOR-2, MAJOR-3) are
silent: a gate that failed on `main` now passes. They should be fixed, or explicitly accepted in
D-161, before the owner merges.

**Seat:** independent. I wrote none of this change. **Subject:** branch `upgrade/devflow-v6.4`,
commits e973a05..b569de5, base `main` = e66a2b3. **Method:** I diffed against `main`, `v6.0` and
`v6.4`, ran every gate in a clean clone, and ran ten mutants. Each in-place mutant was restored
byte-identical (md5 checked) and `git status` was clean after each one. The rest ran in scratch
copies.

## Findings

### MAJOR-1 -- Wave-close grading contradicts D-161 clause 3 and the version the tree now declares

D-161 clause 3 says P-005's risk tiers stay: one combined reviewer on a LOW/MED wave, and a
security seat at every milestone close. The gate and every procedure document now enforce v6.4's
rule instead:

- **The template's stamp is refused.** `docs/wave-checklist.template.md:5` writes
  `process_version: v6.4`. But `scripts/wave_check_all.py:82` accepts only `{"v5.0", "v6.0"}`, and
  it fails any later-dated record with another stamp as "without the stamp".
- **Two review files are required at every tier.** `scripts/wave_check.py:387-402` requires both
  `docs/reviews/m<N>-wave-<W>-review.md` and `...-tester.md`, each with a `## Verdict` heading, on
  any record at v6.0.1 or later. A LOW/MED wave with ONE combined reviewer (AGENTS.md:77) cannot
  pass. Nor can the way this project writes reviews today: m16-wave-4, a HIGH wave, has one
  combined `m16-wave-4-review.md` and no `## Verdict` heading.
- **Every procedure document states v6.4's every-tier rule.** They contradict AGENTS.md:77:
  - `docs/wave-checklist.template.md:35` ("every wave, every tier")
  - `docs/closure-checklist.md:61`
  - `.claude/skills/close-wave/SKILL.md:3,18,23`
  - `.claude/skills/pre-merge/SKILL.md:72`
  - `permission-matrix.md:89`
  - AGENTS.md:34 and :36 (in the same file as :77)
- **The milestone security seat has no checklist step.** It survives only as the last sentence of
  AGENTS.md:77. `docs/closure-checklist.md` (taken verbatim from v6.4) dropped `main`'s "B.2a --
  Security review (Stage 4.0)" step.

*Measured (mutant M8).* I re-stamped `docs/plans/m16-wave-4-close.md` as `v6.4`, then:
- `wave_check.py` exits 1: "`m16-wave-4-review.md` carries no `## Verdict`" and "no Tester
  verdict at `reviews/m16-wave-4-tester.md`".
- `wave_check_all.py` exits 1: "declares process_version='v6.4'; ... without the stamp".

*Failure scenario.* M17-W1 is the current wave (`docs/plans/m17-wave-1-plan.md`). It will be closed
from the template, which stamps v6.4, and `make check` goes red. The only stamps the gate accepts
are v5.0 and v6.0. Both skip the two-review rule, and v5.0 also skips three footprint fields
(MAJOR-2). So the easiest way to go green is to back-date the record.

*Remedy.*
- Derive `wave_check_all`'s accepted set (for example, any declared version >= 5.0) instead of
  listing it.
- Either make the two-file rule depend on the plan's risk tier, or record in D-161 that P-005 is
  retired and delete AGENTS.md:77's first half.
- Put the milestone security seat back in `docs/closure-checklist.md`.

### MAJOR-2 -- Undoes the fix for D-155's adoption-review MINOR-1: a new record can declare an old version and skip three rules

`main`'s `scripts/wave_check.py` skipped `Mutant set author`, `Observed RED` and
`Owner instruction` only when a record declared an old version AND was dated on or before
2026-09-23. That date condition was the fix for the adoption review's MINOR-1
(`docs/reviews/devflow-v6-adoption-review.md:155`). HEAD takes v6.4's `since()`
(`scripts/wave_check.py:255-262`), which trusts the declared version alone. That is the exact hole
MINOR-1 reported. D-161 does not mention the change.

*Measured (mutant M9, scratch copy of HEAD).* I made a new `docs/plans/m17-wave-9-close.md`, dated
2026-10-15 and declaring `v5.0`. It lacks all three fields and cites a same-day
`seat: independent` review.
- HEAD `wave_check.py`: **PASS** (exit 0).
- HEAD `wave_check_all.py`: **PASS**, 44 records.
- `main`'s `wave_check.py`: FAIL, with three findings ("no `Mutant set author:` line", and the
  same for the other two fields).

*Remedy.* Put the date condition back into `since()` for records dated after the adoption.

### MAJOR-3 -- The `GP-Agent:` trailer on agent commits is no longer checked

The D-155 amendment (`docs/decisions.md:2482-2485`, adoption review MAJOR-3) and the owner's
ruling on item 2 (`docs/decisions.md:2511-2515`) made `conformance/test-commit-identity.py` fail
an agent commit on the branch that has no `GP-Agent:` trailer. HEAD's test is v6.4's, unchanged
(`git diff v6.4 HEAD -- conformance/test-commit-identity.py` is empty). It has no trailer check at
all, and it allows the machine identity (`MACHINE`, line 46) on a branch whether or not a trailer
is present.

*Measured (mutant M10).* In a scratch repo, a branch commit by
`gp-agent@users.noreply.github.com` with no trailer:
- HEAD's test: **PASS**, 0 violations.
- `main`'s test: FAIL, "an agent commit ... with no `GP-Agent:` trailer -- D-155 clause 2 keeps
  the trailer".

D-161 clause 2 (`docs/decisions.md:2785-2789`) says the trailer rule stands and names
`conformance/test-git-authority.py` as its enforcement. That test only checks that the text of
`issue-agent.yml` contains `GP-Agent:` (`conformance/test-git-authority.py:109`). The only such
text in that file is a comment (`.github/workflows/issue-agent.yml:93`), the one that itself says
"a policy that lives only in a comment is a policy nobody enforces".

Under D-161, session commits carry the owner's identity, so nothing tells an agent commit with no
trailer apart from the owner's own commit. That contradicts two statements:
- AGENTS.md:42: "so no agent commit reads as the owner's own"
- `.agents/rules/git-authority.md:14-18`: says `test-commit-identity.py` "still verifies"
  that no commit may be mistaken for the owner's

`.owner-identity` is now read by no script (`git grep owner-identity` finds only records): a
control file nothing reads.

*Remedy.*
- Put the trailer check back on v6.4's test, for machine-identity and `AI_EMAILS` commits in
  `base..HEAD`.
- Say in D-161 that on owner-identity session commits the trailer is an honour-system convention.
- Delete `.owner-identity`, or wire it to a check again.

### MAJOR-4 -- `make bootstrap-check` went from PASS on `main` to BLOCKING, and no record says so

v6.4 adds C11 (`scripts/bootstrap-check.sh:320-334`). It reads two answers from
`docs/project-brief.md`, "GitHub Actions run here:" and "The default branch can be protected:".
This project's brief was kept as it was, so it has neither. Hooks are not installed either.

*Measured.* On `main` (scratch export): `0 fail / 1 warn -- PASS`. On HEAD: `[FAIL] core.hooksPath
is not .githooks, and docs/project-brief.md records GitHub Actions: no, branch protection: no ...
RESULT: BLOCKING`. Script exit 1; `make` exit 2.

`docs/closure-checklist.md:22` requires `make bootstrap-check` to exit 0 at every milestone close,
and AGENTS.md:71 says it MUST be green. So M17's closure will stop on it. Neither D-161 nor the
process-log entry mentions it.

The red status also hides a regression in the W-015 strip. Mutant M4 turned C1 and C3 red, but
the exit code did not change, because C11 already fails.

*Remedy.* The owner records the two facts in `docs/project-brief.md`. CI runs here, and
`docs/branch-protection.md` names the required checks. Alternatively, record in D-161 that the
gate stays red until `make hooks`.

### MINOR-1 -- `docs/plans/*` and `docs/reviews/*` allowlist rows come back

`.path-refs-allow:12` and `:16` (from v6.4's section 1) excuse any path under either directory.
The D-155 amendment removed exactly this shape of row (`docs/decisions.md:2479-2481`, adoption
review MAJOR-2).

*Measured (mutant M7).* I appended references to
`docs/reviews/m17-wave-1-review-never-written.md` and `docs/plans/m99-plan-never-written.md` to
AGENTS.md. HEAD's `test-documented-paths.py`: PASS, 0 dangling. `main`'s: FAIL, 2 dangling.

A live document can now point at a review or plan that does not exist. The K.7 gate still catches
this inside wave-close records, but nowhere else.

### MINOR-2 -- The Quality Gate is routed to `make closes`, which fails on every older record

- AGENTS.md:113 says the owner review pack is "graded by `make closes`".
- D-161 clause 3 says a closure report is checked with `make closure-check`.
- `make closes` exits 2 on this tree. It checks 79 records: M1-M15's closure reports fail, and so
  do the 20 wave records from before the migration.
- The comment at `Makefile:298-300` still says `closes` is "Part of `make check`", which is not
  true in this project.

*Remedy.* Point AGENTS.md:113 at `make closure-check FILE=...` and correct the Makefile comment.

### MINOR-3 -- `check_fast.py --plan` and the real run are built separately; the conformance test reads only the plan

In `scripts/check_fast.py:113-121`, the plan and the `commands` dict come from two separate
expressions. v6.4 builds one `plan` dict and uses it for both.

*Measured (mutant M2).* I filtered the `client` leg out of `commands` only. Result:
`test-check-fast PASS: 13 check: prerequisite(s), each in exactly one of 4 leg(s)`, yet
`make check-fast` would no longer run `client-decls`.

*Remedy.* Build `commands` from the dict the plan prints.

### MINOR-4 -- The CI agent's identity is stated as something the tree does not do yet

AGENTS.md:42 and D-161 clause 2 say the CI issue agent commits as
`gp-agent <gp-agent@users.noreply.github.com>`. `.github/workflows/issue-agent.yml:47-48` sets
`gp-issue-agent@users.noreply.github.com`. This becomes true only after the owner applies the
proposed workflow diff. Until then, v6.4's `test-commit-identity.py` would report such a commit as
an unknown identity. Say "after the workflow change".

### MINOR-5 -- The post-edit hook no longer runs the full gate, and D-161 does not say so

`main`'s PostToolUse hook ran `make gate`; HEAD's runs `make check-fast`
(`.claude/settings.json`, v6.4 verbatim). So `secrets`, `deps` and `slopsquat` no longer run after
each edit. Until the owner runs `make hooks`, they run only at `/pre-merge`
(`.claude/skills/pre-merge/SKILL.md:104`) and in CI.

There is also a gain: the hook now exits 2, which does block, where `main`'s exited 1, which did
not. The change is reasonable, but it should be one line in D-161.

### NITs

1. **D-161 "121 findings".** At HEAD, v6.4's `check_records.py` reports 122. The extra one is this
   change's own `docs/research/devflow-v6.4-field-findings-2026-09-23.md`: its `record_type:
   field-findings` is not in v6.4's list of record types.
2. **D-161 "two DevFlow scripts carry small lint fixes".** Five differ from v6.4:
   `coverage_floor.py`, `write_install_marker.py` and `gen_schema.py` as well as the two it names.
   All five changes are lint-only (`noqa` removal, import sorting).
3. **D-161, the wave closes that `closes` "also grades".** `closes` grades all 63 wave records and
   fails the 20 from before the migration. `wave-check-all` scopes those out. This makes the case
   for dropping `closes` stronger than D-161 states it.
4. **`scripts/README.md` is v6.4's, verbatim.** It lost the project's `runner_verdict.sh` row, and
   that script is still in INSTALL-MANIFEST.md.
5. **The trailers are not in one block.** In this branch's commits, `GP-Agent:` and `GP-Task:` are
   separate paragraphs, so git's trailer parser (`%(trailers)`) sees only `GP-Task`.
6. **README's quick start tells every reader to run `make hooks`.** D-161 clause 4 leaves that to
   the owner's decision about untracked files.
7. **AGENTS.md:32 has an out-of-place line.** The GP-era harvest line ("**GP change**") sits
   under §3 Workflow, ahead of the stage list.
8. **Unreachable code (pre-existing, kept by the merge).** `scripts/wave_check.py:162-211` sits
   after `return bad` in `review_seat_problems`.

## Focus questions

1. **Project controls through the merge.**
   - **Kept:**
     - `check:` prerequisites are byte-identical to `main`'s.
     - `check-fast` derives its legs from `check:`: `--plan` prints `python: lint typecheck test
       coverage-floor`, `records: check-records check-records-selftest install-check
       harvest-context-check shell-dialect wave-check-all conformance`, `swift: swift-test` and
       `client: client-decls`.
     - Dropping `closes` is justified (reproduced below).
     - W-015 is kept (`scripts/bootstrap-check.sh:42`; mutant M4 killed).
     - K.7's `review_seat_problems` is kept and called (`scripts/wave_check.py:336`; mutant M5
       killed by 14 tests).
     - `lib_record.is_record` and the `test-documented-skills` record skip are kept.
     - `check_records.py` and its schema are the project's (the only change is encoding edits).
   - **Lost:** MAJOR-1 (P-005, milestone seat), MAJOR-2 (date guard), MAJOR-3 (trailer check),
     MINOR-1 (exact allowlist rows).
   - **Other Makefile changes, all improvements:**
     - `conformance`, `check-records` and `install-check` no longer run twice on a failure.
     - The scripts run with `SYS_PY` now. All of them import only the standard library; checked.
     - `deps` audits the declared dependencies (`pip_audit --strict .`).
     - A missing `gitleaks` exits 2.
2. **v6.4 fixes dropped by an "ours" resolution.**
   - Every DevFlow-owned path was diffed against v6.4. Apart from D-161's listed differences, the
     only deviations are MAJOR-2, MAJOR-3 and MINOR-3 above.
   - `.claude/`, `.githooks/` and the conformance tests other than the three project-patched ones
     are identical to v6.4.
   - Where the project had its own version (`branch-protection.md`, `closure-checklist.md`,
     `scripts/README.md`), the text was replaced by v6.4's. The only content lost is NIT-4 and the
     closure-checklist security step (MAJOR-1).
3. **Encoding edits.**
   - An AST scan of every changed `.py` file found 204 calls carrying `encoding=`:
     - `read_text`: 135
     - `write_text`: 54
     - `subprocess.run`: 14
     - `open`: 1
   - None opens in binary mode, none collides with a positional argument, and none is on an
     unexpected callee.
4. **AGENTS.md.**
   - 128 lines. `test-agents-cap` passes.
   - The stale-reference sweep of live documents found no reference to `METHODOLOGY.md`,
     `subagent-profiles/`, `governance-contract` or `handovers/` outside `UPGRADING.md`'s own
     changelog. `note.txt` is still in the tree, so the `Makefile:235` mention is not stale.
   - Wrong statements: MAJOR-1 (AGENTS.md:34/36 against :77), MAJOR-3 (:42), MINOR-2 (:113),
     MINOR-4 (:42).
5. **D-161 claims.** See the table below.
6. **Gates and mutants.** See the sections below.

## D-161 claims, reproduced

| Claim | Command | Result |
|---|---|---|
| `closure_check.py` fails all fifteen closure reports written before DevFlow | `python3 scripts/closure_check.py` on each `docs/closure-report-m*.md` | M1-M15 exit 1, M16 (v6.0) exit 0 -- **reproduced** |
| v6.4's validator reports 121 findings | v6.4's `scripts/check_records.py --root .` on a HEAD export | **122** (NIT-1) |
| the project's validator passes v6.4's self-test fixtures | `python3 scripts/check_records.py --self-test --root .` | `self-test PASS: 0 problem(s)`, including v6.4's new `condition-self-satisfying.md` -- **reproduced** |
| 82 text reads/writes in `src/`, `scripts/`, `tests/` | v6.4's `conformance/test-text-encoding.py` run on `main`'s source | 95 in total: 10 in v6.0 conformance files and 3 in `coverage_floor.py` (both replaced by v6.4), leaving 20 (`check_records.py`) + 3 (`rank.py`) + 59 (`tests/`) = **82 -- reproduced**. HEAD: 156 files, 0 |
| `check_fast.py` gains `--plan` for `test-check-fast.py` | `scripts/check_fast.py --plan`; `conformance/test-check-fast.py` | PASS, 13 prerequisites in 4 legs -- **reproduced** (see MINOR-3) |
| only lint fixes in two DevFlow scripts | `git diff v6.4 HEAD -- scripts/` | five scripts (NIT-2) |
| the trailer rule of clause 2 stands, via `test-git-authority` | mutant M10, and reading the test | the commit-level check is gone (MAJOR-3) |

## Mutants

| # | Mutation | Expected | Result |
|---|---|---|---|
| M1 | `check_fast.legs()` drops the last prerequisite | `test-check-fast` red | **killed**: "`client-decls` ... in no leg"; `make conformance` exit 2 |
| M2 | the run path drops the `client` leg; the plan is unchanged | red | **survived** (MINOR-3) |
| M3 | `swift-test` and `wave-check-all` removed from `check:` | some gate red | **survived**: `make conformance` PASS. Nothing pins what `check:` contains. This was already true on `main`; noted, not charged to this change |
| M4 | W-015 `gsub` removed from `live_lines` | `bootstrap-check` C1 red | **killed** (C1: `<path> <pkg> <tag>` in `main.py`, `<artifact>` in `prd.md`; C3 red), but the exit code does not change (MAJOR-4) |
| M5 | `review_seat_problems` returns early | red | **killed**: 14 tests in `tests/unit/test_review_seat_gate.py` fail |
| M6 | `GP-Agent:` removed from `issue-agent.yml` (scratch copy) | `test-git-authority` red | **killed**, but the text it matches is a comment (MAJOR-3) |
| M7 | dangling `docs/reviews/`, `docs/plans/` references in AGENTS.md (scratch copy) | `test-documented-paths` red | **survived** on HEAD, killed on `main` (MINOR-1) |
| M8 | m16-wave-4 close re-stamped `v6.4` | pass (the template's own stamp) | fails `wave_check` and `wave_check_all` (MAJOR-1) |
| M9 | new M17 close, `v5.0`, dated 2026-10-15, no footprint fields (scratch copy) | red | **survived** on HEAD, killed on `main` (MAJOR-2) |
| M10 | `gp-agent` branch commit with no trailer (scratch repo) | red | **survived** on HEAD, killed on `main` (MAJOR-3) |

After each in-place mutant (M1-M5, M8), the file's md5 matched the recorded one and `git status
--porcelain` was empty.

## Gate results (clean clone, macOS, Python 3.14 venv)

- **`make install`:** exit 0. Marker `v6.4 · manifest 1c6564a96010`.
- **`make check`, fresh clone:** exit 2 at `test`. W-108: `advisor.db` is gitignored and absent;
  `MODEL_RANKING_REQUIRE_ARTIFACT=1` refuses to run without it. This is expected.
- **The artifact built for the review.** I built `advisor.db` in the clone with
  `python -m app.workflows.build`. It exited 3: built but not servable, since there is no
  owner-placed Epoch bundle.
- **`make check`, with that artifact:** exit 2. 1 failed, 1181 passed, 15 skipped; coverage 90.24%.
  - The failure is `tests/unit/test_budgets_endpoint.py::test_the_published_blend_reproduces_each_rows_blended_price`
    ("the surface must publish a ranking on real data").
  - The same test fails the same way on a `main` export with the same artifact. It is caused by
    the environment, not by this change.
- **`make -k check`, every other leg green:**
  - ruff: all checks passed
  - mypy: 36 files, no issues
  - coverage-floor: PASS, 36 modules
  - check-records: PASS
  - self-test: 0 problems
  - install-check: PASS
  - harvest-context: SKIPPED (installation)
  - shell-dialect: 11 scripts
  - wave-check-all: 43 validated, 20 out of scope
  - conformance: 16 tests, 0 failing, 0 caller-liveness findings
  - swift-test: 268, all named in the manifest
  - client-decls: 11 files in 4 configurations
- **`make check-fast`:** exit 2 in 37 s.
  - `python` leg: FAIL (exit 2, on the same test)
  - `records`: PASS
  - `client`: PASS
  - `swift` (`swift-test-parallel`): PASS
- **`make bootstrap-check`:** exit 2 (script exit 1). C11 is BLOCKING (MAJOR-4); on `main` it is
  PASS.
- **`make closes`:** exit 2 across 79 records (see MINOR-2).

`advisor.db` (the degraded artifact) is left in the clone so these numbers can be re-run. It is
gitignored.
