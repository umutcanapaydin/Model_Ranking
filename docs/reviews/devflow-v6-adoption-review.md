---
record_type: review
id: devflow-v6-adoption-review
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# DevFlow v6.0 adoption (D-155): an independent review of the merge, its gates and its records

**Seat:** independent (Code-Reviewer + Tester; I wrote none of this change). **Base:** `main` at
5fc3f02. **Subject:** branch `enhancement/devflow-v6` (draft PR #1). The review was briefed on two
commits, 3ca3da0 and 071c956. Three more landed while I worked: f9c7bee, 9c9845c and df49bb5. My
findings are stated against **df49bb5**, and I say where an earlier commit behaved differently.
References used: the DevFlow v6.0 clone (tag `v6.0`, 6f4cf25) and the GP v5.0 base, both read-only in
the session scratch directory.

**Snapshot I graded** (md5 at df49bb5): `scripts/wave_check.py` `ef1f2f85...`,
`scripts/check_records.py` `57799175...`, `scripts/bootstrap-check.sh` `ac5fd47f...`,
`conformance/lib_record.py` `19ddded0...`, `conformance/test-git-authority.py` `45111f7e...`,
`.path-refs-allow` `7d554ce7...`, `.skill-refs-allow` `b70c695a...`, `.claude/settings.json`
`aafb4db3...`, `Makefile` `8dca5fbf...`.

**Hygiene.** I ran every mutant in a scratch copy of the tree (rsync, with `.venv` excluded) or in a
`git archive` export. After each mutant I restored the file from `git show` and compared it byte for
byte. I edited no repository file other than this one. I did not run `make install`. The
`make -n` expansion was run with `-o install`. I started nothing on :8080, and no process I started
is still running. The working tree and `.gp/installed` changed during the review. Both changes came
from the author's concurrent commits, not from me.

## Verdict

**PASS WITH FINDINGS — 0 BLOCKING, 5 MAJOR, 7 MINOR, 4 NIT.**

The three-way merge itself was done carefully. I checked every control file the branch touched
against 5fc3f02 and the GP v5.0 base, line by line:

- Of the lines removed from `AGENTS.md`, `permission-matrix.md`, `.agents/rules/*`, `pyproject.toml`,
  the workflows, `scripts/wave_check.py` and `scripts/check_records.py`, every one was GP base text
  except two. Both of those two were carried: the practices.md K.7 "separate session, writes a file"
  rule, and the check_records C901 ignore.
- `scripts/module_coverage_floor.py` is byte-identical to the old `scripts/coverage_floor.py`.
- No file the project never changed kept its old copy.
- The only DevFlow file not installed is `src/__init__.py`. I measured the reason: adding it gives
  mypy 113 errors.
- The new `.claude/settings.json` Bash hook is **strictly stronger** than the old one. It blocks
  every command the old one blocked, plus a push to `main`, `git checkout -- .` and a `git restore`
  without `--staged`.

The losses are somewhere else. The per-finding conformance wrapper was retired and replaced by
**exemptions by artifact class and by broad glob**. The class and glob exemptions cover far more than
the seven named lines they replaced. They hide:

- instructions in plans and templates;
- dangling source and test paths in live documents;
- a retired skill named in `AGENTS.md`.

The CI trailer check on `issue-agent.yml` was also removed, while four places still say it runs.
Separately, `bootstrap-check.sh` lost W-015 on `docs/decisions.md` and now crashes there.

**Gates run with this file present, at df49bb5:** `scripts/check_records.py --root .` PASS.
`conformance/run-all.py` PASS: 12 PASS and 2 NOT-EVALUABLE by design. A `git archive` export of
9c9845c, which has no ignored files, also passes both. **At 071c956 that export FAILED**: 10 dangling
paths, all gitignored files that exist only on the owner's machine. The author found and fixed this
from CI in f9c7bee while I was reviewing, so I do not count it.

## MAJOR

**MAJOR-1 — Record-class skipping removed plans, templates and `docs/decisions.md` from the git and
command checks.** Where: `conformance/test-git-authority.py:70` and
`conformance/test-documented-commands.py:48`, with `conformance/lib_record.py:25-37`.

- *How the rule works:* any `.md` whose first 400 characters contain `record_type:` counts as a
  record, and records are skipped. That covers **235 of 302 delivered documents**. Among them are
  `docs/wave-checklist.template.md`, `docs/closure-report.template.md`, every `docs/plans/m*-plan.md`
  and `docs/decisions.md`.
- *What 5fc3f02 did:* the same two checks ran on all of these files. The retired
  `scripts/conformance_gate.py` exempted exactly 7 named `file:line` findings, and it failed on any
  exemption that no longer fired.
- *Measured (copy, at df49bb5 against 5fc3f02):* I appended
  ``run `git push origin main` and then `gh pr merge --squash` `` to three files. In
  `docs/plans/m16-plan.md`, `docs/wave-checklist.template.md` and `docs/decisions.md`,
  `test-git-authority` now PASSes. At 5fc3f02 it FAILed on the plan and on the template. In a skill,
  it still FAILs.
- *Measured (same):* ``run `make pin-check` `` in `docs/plans/m16-plan.md` now PASSes
  `test-documented-commands`. At 5fc3f02 it FAILed.
- *Scale:* the command references graded fell from 580 to 194.
- *Remedy:* stop treating templates and plans as records here. Either exclude `*.template.md` and
  `docs/plans/*-plan.md` in `is_record`, or give these two tests back a named per-finding list (the 7
  old rows) instead of the class skip. Re-run the mutants above.

**MAJOR-2 — Allowlist rows broad enough to hide broken instructions in live documents.** Where:
`.path-refs-allow` lines 16, 36, 43, 44, 62 and 96-100, and `.skill-refs-allow` lines 38-39.

- *Why the path rows are too broad:* `fnmatch` lets `*` cross `/`. So `src/*` and `tests/*`, which
  DevFlow's comment calls field evidence from harvested projects, match every source and test path in
  **this** project.
- *Measured (copy):* I planted 15 dangling paths, each in `AGENTS.md` and in
  `.claude/skills/pre-merge/SKILL.md`. Examples: `src/app/adapter/gone_main.py`,
  `tests/unit/test_gone.py`, `docs/plans/m99-plan.md`, `scripts/checkpoint.sh`. **15 of 15
  passed.** A control path under docs/ with no matching row failed as it should.
- *What the rows hide today:* I deleted only the `src/*`, `tests/*` and `test_*.py` rows. That
  surfaced 14 findings: 6 in `.agents/rules/playbook-seeds.md` (the intended evidence) and 8 citing
  the deliberately absent `src/__init__.py`. So exact rows would cost 7 lines.
- *The skill rows:* `retrospect` and `quarterly-handover` are allowed everywhere, although their
  reason says "named in records". Writing "run `/retrospect`" into `AGENTS.md` or
  `.claude/skills/cycle-close/SKILL.md` **passes** `test-documented-skills`. The same test with a
  skill that has no row (fix-issue-implement, written with its slash) fails.
- *Remedy:* replace these rows with exact paths or per-citing-file rows. For skills, skip records by
  class in `test-documented-skills`, as `test-documented-commands` does, and delete the two rows.

**MAJOR-3 — The GP-Agent trailer control was removed, and four places still say it exists.**
Where: `conformance/test-git-authority.py:112-120`.

- *What changed:* at 5fc3f02 this check failed when `.github/workflows/issue-agent.yml` carried no
  `GP-Agent:` trailer. It no longer checks for the trailer.
- *Measured:* I deleted the trailer lines from `issue-agent.yml` in both copies. At 5fc3f02 the check
  FAILed (3 violations against a baseline of 2). At df49bb5 it PASSes.
- *Documents that still claim the check:*
  - `docs/decisions.md:2421` (D-155 clause 2) says the trailers "stay (V4C-64)".
  - `AGENTS.md:131` says an agent commit carries them.
  - `issue-agent.yml:90-91` still says "`conformance/test-git-authority.py` asserts it".
  - The `conformance/test-commit-identity.py:8` docstring still requires the trailer on branch
    commits. The code does not check it.
- *Remedy:* decide which is true. If the trailers stay, restore the `issue-agent.yml` assertion and
  check the trailer on `base..HEAD`. If they do not, amend D-155, `AGENTS.md:131`, the workflow
  comment and the docstring.

**MAJOR-4 — `bootstrap-check.sh` lost W-015 on `docs/decisions.md` and crashes there.** Where:
`scripts/bootstrap-check.sh:51-56`.

- *What changed:* the project-ADR scan has no inline-code `gsub`. D-155 clause 4 and field-findings
  C5 both say this script "also strips inline code spans (W-015)". The same scan also increments
  `ph_hits` before line 56 initialises it, and the script runs under `set -u`.
- *Measured (copy):* I appended a `## D-156` ADR containing ``Run `refresh --db <path>` ``. At
  5fc3f02, C1 said "no stray placeholders" and the script PASSed. At df49bb5 it prints the FAIL, then
  `ph_hits: unbound variable`, exits 1 and **never runs C2-C10**.
- *What still works:* prose placeholders in `docs/prd.md`, `docs/architecture.md`, `README.md`, a
  table cell and a project ADR all still FAIL. Inline code in `docs/prd.md` stays quiet.
- *Remedy:* add `{ gsub(/`[^`]*`/, "") }` to the line-52 awk, and move `ph_hits=0` above line 49.

**MAJOR-5 — A second workflow commit, outside the owner's recorded one-time exception.**

- *What the rules say:* `docs/decisions.md:2423` (D-155 clause 3) allows the workflow changes "in ONE
  separately marked commit, a one-time exception the owner chose". `AGENTS.md:45` says the agent
  "never touches `.github/workflows/**`".
- *What happened:* 9c9845c is a second agent commit to `.github/workflows/ci.yml`.
- *The PR body is also stale:* it still says "Two commits, reviewed differently", and that CI "runs
  when this PR is pushed".
- *Remedy:* before merge, record the owner's word for the second workflow commit in D-155, or in an
  amendment to it. Then bring the PR body up to date.

## MINOR

**MINOR-1 — The GPF-001 scoping trusts a self-declared version.** Where: `scripts/wave_check.py:267`.

- The three v5.1 fields are skipped for any record that declares `v5.0`, whatever its date.
- *Measured:* an M17 wave record dated 2026-10-15, declaring `v5.0`, citing a review of that date and
  lacking all three fields, PASSes both `wave_check.py` and `wave_check_all.py`.
- Positive direction, also measured: `v6.0` without the fields fails, and no `process_version` at all
  fails.
- *Remedy:* grant the skip only when the record is also dated on or before 2026-09-23.

**MINOR-2 — The `conformance` exemptions match by name, not by location.**

- `scripts/wave_check.py:354` skips `review_seat_problems` for a record under **any** directory named
  `conformance`. *Measured:* a copy of the M16-W2 close citing a missing review FAILs in `docs/plans/`
  and PASSes in a `conformance` subdirectory of `docs/plans/`.
- `scripts/check_records.py:1439,1457` drops any path segment that **starts with** `conformance`.
  *Measured:* a review record named conformance-note under `docs/reviews/`, with `status: bogus`,
  PASSes. The same `.git` prefix match also drops `.github`.
- *What still holds:* the review-seat rule still fires on a real record that cites a missing review.
  It also fires when every cited review says `seat: author`.
- *Remedy:* anchor both checks to the root-relative prefix `conformance/`.

**MINOR-3 — `.gp/installed` is a tracked file, and every make target rewrites it.**

- `install` runs `write_install_marker.py` (`Makefile:69`). `install` is a prerequisite of
  lint, test, typecheck, check and gate, and the post-edit hook runs `make gate`.
- The committed marker says `installed_from_commit: 071c956`, but HEAD is df49bb5. So the next
  `make check` dirties the tree.
- f9c7bee already committed one such rewrite. The marker also names the commit before the one that
  installed it.
- *Remedy:* gitignore it, or write it only from an explicit install target that nothing depends on.

**MINOR-4 — The identity half of `test-commit-identity` grades nothing on this machine.** Where:
`conformance/test-commit-identity.py:174`.

- "Owner" is read from `git config user.email`, which is `noreply@anthropic.com`. That is the same
  identity all five branch commits are authored under ("Claude"). The declared machine identity is
  `gp-agent@users.noreply.github.com`.
- So an agent commit is graded as the owner's: exactly the property D-999 says this control carries.
- *Remedy:* have the agent commit as the machine identity, and pass `--owner-email` explicitly from
  the Makefile and CI.

**MINOR-5 — The hook does not block the rest of D-999.** Measured by piping each command through the
hook command in `.claude/settings.json`:

- `gh pr merge 1`, `gh pr ready 1`, `git commit --no-verify` and `git push origin refs/heads/main`
  all exit 0.
- `git push origin main`, `HEAD:main` and `main:main` are blocked.

*Remedy:* add the four patterns, or say in D-999 that only branch protection enforces them.

**MINOR-6 — The records disagree with the tree in places.**

- `docs/decisions.md:2444` says "Four DevFlow defects". The findings record lists 24 (A1-A15, B1-B4,
  C1-C5).
- The PR body is stale, as described in MAJOR-5.
- `docs/research/devflow-v6-field-findings-2026-09-23.md` C5 claims inline spans are stripped in the
  Stage-0 scan. For `docs/decisions.md` that is false; see MAJOR-4.

*Remedy:* amend D-155 with a dated note (append-only), and correct C5.

**MINOR-7 — Live documents still name retired skills, in forms no check reads.** `METHODOLOGY.md:409`
and `:550`, `docs/closure-checklist.md:4`, and `pipeline-schema.html:322,342,402` name
quarterly-handover, retrospect and fix-issue-prepare/implement. They are not backticked or code-tagged,
so no check reads them. All of them come from DevFlow, and the field-findings record does not list
them. *Remedy:* add them to the findings for DevFlow, and fix the project's copies.

## NIT

- **NIT-1** `scripts/bootstrap-check.sh` C1: `/<!--/ { next }` drops a whole line that contains
  `<!--`, so a real placeholder beside a comment passes. The body lines of a multi-line HTML comment
  are still scanned, which is a false positive. Both measured; both come from DevFlow's GPF-003 code.
- **NIT-2** `docs/process-log.md:448` says "conformance 14/14", but the run is 12 PASS and 2
  NOT-EVALUABLE. `docs/decisions.md:2438` says "113 `import-untyped` errors", but the measured split
  is 105 import-untyped and 8 no-any-return.
- **NIT-3** `make harvest-context` appears in `make help` and fails with Error 2, because
  `scripts/gen_harvest_context.py` is not shipped. `harvest-context-check` guards for this case; this
  target does not.
- **NIT-4** `scripts/refresh_job.sh`, the launchd entry point, changed its shebang to
  `/usr/bin/env bash`. This is harmless under launchd's PATH, but it is a product file changed by a
  governance merge, and no record mentions it.

## Mutants and probes (copy or export; each file restored and compared byte for byte)

| # | Mutation | 5fc3f02 (n/a = not run there) | df49bb5 |
|---|---|---|---|
| W1 | M16-W2 close cites a missing review | n/a | **FAIL** (RED) |
| W2 | W1's record moved under a directory named conformance | n/a | **PASS** (MINOR-2) |
| W3 | M16-W2 close relabelled `v6.0`, no v5.1 fields | n/a | FAIL (RED) |
| W4 | New M17 close dated 2026-10-15 declaring `v5.0`, no v5.1 fields | n/a | **PASS** (MINOR-1) |
| W5 | M16-W2 close with no `process_version` | n/a | FAIL (RED) |
| W6 | All three cited reviews set to `seat: author` | n/a | FAIL (RED) |
| R1 | Review `status: bogus` | FAIL | FAIL (RED) |
| R2 | ...plus an exempt row that is the basename, a directory, a glob, or the exact path without a reason | n/a | FAIL (RED; exact-path matching and `.governed-records` both hold) |
| R3 | Retrospective `status: bogus`; `record_type: retrospectiv` | n/a | FAIL (RED) |
| R4 | Review record named conformance-note under `docs/reviews/`, `status: bogus` | n/a | **PASS** (MINOR-2) |
| L1 | Turkish prose in `METHODOLOGY.md`; in a skill; after an unbalanced fence; beside a double-backtick span; a long Turkish inline span | n/a | FAIL (RED) |
| L2 | A short Turkish word in an inline span | n/a | PASS (correct) |
| L3 | Turkish prose in `README.md` | n/a | PASS (file exempt in `.language-allow`; unchanged by this branch) |
| B1 | Prose placeholder in prd, architecture, README; in a table cell; in a project ADR | n/a | FAIL (RED) |
| B2 | Inline-code placeholder in `docs/prd.md` | n/a | PASS (correct) |
| B3 | Inline-code placeholder in a project ADR | PASS | **FAIL + crash** (MAJOR-4) |
| G1 | `git push origin main` + `gh pr merge` in a skill | n/a | FAIL (RED) |
| G2 | The same in a plan, the wave template, `docs/decisions.md` | FAIL (plan, template) | **PASS** (MAJOR-1) |
| G3 | `--no-verify` in a script | n/a | FAIL (RED) |
| G4 | `issue-agent.yml` without the `GP-Agent` trailer | FAIL | **PASS** (MAJOR-3) |
| C1 | ``make pin-check`` in a plan | FAIL | **PASS** (MAJOR-1) |
| C2 | ``make pin-check`` in a skill | n/a | FAIL (RED) |
| P1 | 15 dangling `src/`, `tests/`, `docs/plans/`, `docs/research/` and scripts paths in `AGENTS.md` and a skill | n/a | **15 PASS** (MAJOR-2) |
| P2 | A dangling path under `docs/` with no matching row | n/a | FAIL (RED) |
| S1 | `/retrospect` or `/quarterly-handover` in `AGENTS.md` or a skill | n/a | **PASS** (MAJOR-2) |
| S2 | A retired skill without a row (standup, fix-issue-implement) in `AGENTS.md` | n/a | FAIL (RED) |
| H1 | 19 commands through the old and new Bash hooks | 5 blocked | 11 blocked; none weaker (MINOR-5 for the gaps) |
| E1 | `git archive` export of 071c956 / 9c9845c, `run-all.py` | n/a | FAIL (10 dangling) / PASS |

`make -o install -n gate` expands every leg: ruff, mypy, pytest, `module_coverage_floor.py`,
check-records, its self-test, install-check, harvest-context-check, shell-dialect,
`wave_check_all.py`, conformance, swift-test, client-decls, falsify, gitleaks, pip-audit and
slopsquat. `check` still runs swift-test, client-decls, coverage-floor and wave-check-all.
`check_records.py --self-test`: PASS.

## What I did not check

- I did not run `make check` or `make gate` in full: both reinstall, and `install` rewrites
  `.gp/installed`. So I did not re-measure the "pytest 1015/15, Swift 268" claim. No Swift source
  changed on the branch.
- I did not trigger or read GitHub CI runs. My CI findings come from `git archive` exports run locally.
- I verified the field-findings record only by spot checks: A2, A3, A10, A11 and A12 are true of the
  DevFlow clone. I did not reproduce the others.
- I did not go through the 14 new skills, `METHODOLOGY.md` or `pipeline-schema.html` for content
  beyond retired-skill references. I did not review the CORS and destructive-default scans (C9, C10)
  beyond their baseline PASS.
- I did not check whether `docs/skip-budget.txt` (62) matches a real CI run.
- I did not check that `main` is protected, which is the owner's setting.
