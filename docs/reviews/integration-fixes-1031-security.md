---
record_type: review
id: integration-fixes-1031-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — integration/fixes-1031 (delta review of the stacked fixes #537 #535, #538 #517, #539 #522, #540 #518)

**Reviewer:** Security-Reviewer subagent (light mode; `/pre-merge` §1a/§5: one delta review of the whole stack; the stacked verdicts `fix-issue-535-security.md` PASS, `fix-issue-517-security.md` MINOR, `fix-issue-522-security.md` BLOCKING then PASS stand and are not re-run)
**Independent:** yes. I wrote none of this code. I have not reviewed these branches before.
**Date:** 2026-10-31
**Release range:** 290557c..12567c3. `290557c` is main (PR #514). It has one first-parent merge, `12567c3`, of `fix/issue-518-reader-tests` (`6376571`). That branch carries, linearly, `01c0d53`..`bf3f0af` (#517), `ee14e1d`/`d29e91d` (#522), `c5bcebb` (#518), `c013b53`/`43e2d88`/`9ca56c4` (#517 review round, with #535's `3ba886f` merged in), `fcd1b2e`, `6d2e10d` (#522 round 1 fix) and `6a02cc3` (#522 round 2: R4/R5). There are 16 commits in all, and every one carries the owner's identity and a `GP-Task:` trailer.
**Reviewed head:** 12567c38a632ef21000fcd0aa399f6dc62b86534
**Risk tier:** HIGH (deploy-gate control changes, ruled tightening only by D-232 and D-233). The brief's `Paths that make a change HIGH:` is `none`, so the §11 senior-review trigger does not fire.

## Verdict
MINOR

The combination loosens nothing, and nothing rode in that the per-change verdicts did not see. Only one commit after a
per-change verdict changes code: `6a02cc3` (R4/R5, one regex). Its only loosening is the intended one, a lower-case `-c`,
which no `env` takes. Every spelling that round 2 refused is still refused at the head. The real nightly workflow's surface
is unchanged. `make check` is green serially on this exact tree, client-decls included. There are two MINOR findings,
neither in this diff's code: #535's own security verdict was never carried into the stack (M1), and four pre-existing
directory-change spellings still exempt what a dispatched workflow starts (M2).

I worked in my own worktree, `scratchpad/sec-1031`, at `12567c3` (detached). It had its own `.venv` from `make install`
and a copy of `advisor.db` (D-174). The probes ran in pytest `tmp_path` repositories, from a file kept in
`scratchpad/sec1031probe/`. I copied it into the tree only for the run and then removed it. The one mutant was restored
from a byte copy. `git status` was clean at the end, and the worktree has been removed.

## Findings

### BLOCKING
- none

### MINOR
- **M1** docs/reviews/ (missing `fix-issue-535-security.md`): #535's PASS verdict is commit `f311871`, on
  `fix/issue-535-date-compare` (PR #537) only. `git merge-base --is-ancestor f311871 12567c3` fails, so the stack
  carries #535's code (`3ba886f`, through `9ca56c4`) without its review record. If only #540 is merged, main gets
  `scripts/client_decl_gate.py:1391-1393` (a widened privacy-gate allowlist, D-180) with no verdict in the tree.
  The process-log entry for the stack still says "#535 PASS". It is MINOR because it is a record gap, not a code
  defect: the verdict exists, it is independent, and its reviewed head `3ba886f` is byte-identical in
  `scripts/client_decl_gate.py` to this head (`git diff 3ba886f 12567c3 -- scripts/client_decl_gate.py ios/` is empty).
  **Remedy:** merge `fix/issue-535-date-compare` (or cherry-pick `f311871`) into `integration/fixes-1031`. It is
  docs-only, so no code changes after this reviewed head.
- **M2** scripts/deploy_gate.py:523-526 (`_UNREAD_IN_WORKFLOW`), :541-547 (`_workflow_names`): four pre-existing
  spellings still change directory, or the command search path, without the gate reading it. Each leaves
  `scripts/ship_it.sh`, started by a dispatched deploy workflow, exemptible after an upgrade. The probe used the #522
  fixture (`--check` exit 0 = exempt):
  ```
  env --c=scripts ./ship_it.sh                 0  (GNU getopt_long: an unambiguous prefix of --chdir)
  env --chd scripts ./ship_it.sh               0
  env -S'-C scripts ./ship_it.sh'              0  (-S splits; the -C follows a quote, not a space)
  PATH="$PWD/scripts:$PATH" ship_it.sh         0  (also the common `echo ... >> "$GITHUB_PATH"` idiom)
  ```
  None of these is a regression. The round-2 regex and the head's regex both miss them (my regex comparison:
  `same old=0 new=0`), and at 290557c nothing a workflow started was on the surface at all. So the process log's
  "`env -C` in every spelling" claims too much. It is MINOR because the spelling has to sit inside a workflow file that
  is itself never exempt, and the nightly workflow has none of them. It is a bypass that stays green with no test,
  though, so it needs an issue now (Escalate NOW class, as #517's reviewer treated its M1/M2). **Remedy (a new issue):**
  refuse, as unread, a `PATH=` assignment, a write to `$GITHUB_PATH`, `env` with any `--c`/`--ch...` long-option
  prefix, and `env -S`/`--split-string`. Hold the four spellings above in `tests/unit/test_deploy_gate_522.py`'s
  parametrisation. These are the "hides what it starts" class D-232 clause 2 already names. Refuse the class rather
  than enumerating file names (R1 of the #522 verdict stays queued for built paths).

### PASS
- **`9ca56c4`, the one hand-made merge.** `git show --remerge-diff 9ca56c4` touches three files and nothing else:
  1. `docs/process-log.md`: the conflict was resolved by keeping both entries, #517's then #535's.
  2. `docs/reviews/fix-issue-517-security.md`: new, the round-1 verdict.
  3. `scripts/deploy_gate.py`: #517's M2 fix (D-233).

  `devflow_pins` (scripts/deploy_gate.py:402-413) gives one pin per protected base, or None when any base has no pin or
  an unverifiable one. `shipped_unchanged` (:416-437) exempts a file only when every pin's verified blob equals its
  bytes (:437). The list cannot be empty (`bases and all(found)`), so `all(...)` is never vacuous. A missing blob
  (`None != bytes`) is refused. #535's side (`3ba886f`) changes `scripts/client_decl_gate.py` by three lines (one
  entry and its reason) and the process log, nothing more. The other merges, `fcd1b2e`, `6376571` and `12567c3`,
  resolve only `docs/process-log.md`. `git diff 6a02cc3 12567c3` is the #518 test file and the process log.
  `scripts/brief_fields.py` changes only by `protected_bases` (:330-340), as #517's verdict reviewed it.
- **`6a02cc3` (R4/R5) loosens nothing round 2 refused.** I compared round 2's regex with the head's on 36 spellings.
  Every one is the same or tighter, apart from four:
  - `env FOO=1 bash -c ...` and `env -c s`: the intended R5. Neither GNU, BSD nor busybox `env` has `-c`.
  - `env --CHDIR=` and `env --Chdir`: getopt_long is case-sensitive, so `env` rejects both.

  It tightens `-Cscripts`, `-iC`, `-vC` and `-ivC`. Probed end to end at the head, every round-2 spelling is refused
  (exit != 0):
  - the runner spellings: `/usr/bin/make`, `./make`, `Make`, `MAKE`, `/usr/bin/Make`, `~/.cargo/bin/just`,
    `/usr/local/bin/gmake`, `\make` and `m''ake`;
  - the directory changes: `env -C`, `env --chdir=`, `env --chdir `, `ENV -C`, the R4 cluster and attached forms, and
    `working-directory:` on a step and under `defaults: run:`;
  - the checkout-anchored paths: `$GITHUB_WORKSPACE/`, `${GITHUB_WORKSPACE}/`, `${{ github.workspace }}/`, `"$PWD/`,
    `"$(pwd)/` and `"$(git rev-parse --show-toplevel)/`.

  The R5 control (`env FOO=1 bash -c 'echo hi'` with a plain tooling file) exits 0, as intended. Mutant: putting
  round 2's regex back makes `test_deploy_gate_522.py` fail 3 tests (`env-C-attached`, `env-C-in-a-cluster`,
  `test_a_lower_case_c_after_env_is_not_a_change_of_directory`, :78), so the new lines are held.
- **The nightly workflow's surface is unchanged.** `.github/workflows/nightly-hosted.yml` and
  `scripts/ci/nightly-hosted.yml` are unchanged in the range, and `_runs_unread` is False for both. `deploy_surface`
  on the head is the same nine files that rounds 1 and 2 printed: `.github/workflows/nightly-hosted.yml`, `AGENTS.md`,
  `requirements/build.lock`, `requirements/ingest.lock`, `runner`, `scripts/ci/nightly-hosted.yml`,
  `scripts/deploy_hosted_engine.sh`, `scripts/nightly_hosted.sh` and `tests/unit/test_nightly_hosted.py`.
  `devflow_pins` resolves (one pin, since main's tip is the merge-base).
- **#518 (`c5bcebb`) is tests only.** `tests/unit/test_deploy_gate_518.py` (:31, :54, :69, :84, :94). Every git
  call runs in a `tmp_path` repository, and none touches the real refs.
- **The process log** (`git diff 290557c 12567c3 -- docs/process-log.md`) adds six entries, each once: #517, #522,
  #518, #535, the review rounds and the integration entry. Nothing is lost or doubled, and no existing line was changed.
  #517's entry still says the pin "stays at the merge-base". The rounds entry corrects that (D-233), which is right
  for an append-only log.
- No protected path is touched in the range: `.github/`, `.claude/`, `.githooks/`, `Dockerfile`, `deploy/`,
  `pyproject.toml` and `requirements/` are all unchanged. There is no new import, dependency, endpoint, secret or log
  statement.

## Gates passed
- [x] Secret scan green (`make secrets` at 12567c3, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green (run by me: "No known vulnerabilities found")
- [x] `make slopsquat` green (run by me: "slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no new import)
- [x] Default-deny preserved for new external surfaces (there is no new surface; every code change only adds refusals, apart from R5's intended non-`env` `-c`)
- [x] Permission-matrix not violated (no protected path, workflow, hook or guard edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model; workflow text is read as data, by regex)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the HIGH paths are `none`)
- [x] SAST (bandit is not in the lock. I read the code delta by hand: one regex alternative with no nested quantifier,
  so it stays linear, and no subprocess or eval change.) Conformance at 12567c3, run by me inside `make check`:
  "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)"
- [x] `make check` serial at 12567c3, run by me: exit 0. "4902 passed, 37 skipped"; check_records PASS; wave-check-all
  PASS; swift-test PASS; "client-decls PASS: 23 client file(s) in 4 configuration(s)"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #535: `Date.<=` on the standings sink's list → scripts/client_decl_gate.py:1391-1393; `make client-decls` PASS at the head (4 configurations)
- #517 / D-232 clause 1: policy at the merge-base and the tip → scripts/brief_fields.py:330-340; tests/unit/test_deploy_gate_517.py:42, :55
- #517 M2 / D-233: every pin holds the bytes → scripts/deploy_gate.py:402-413, :437; tests/unit/test_deploy_gate_517.py:67
- #517 R2: the tip's workflow copies are read → tests/unit/test_deploy_gate_517.py:89
- #522 / D-232 clause 2, with R4/R5: scripts/deploy_gate.py:523-547; tests/unit/test_deploy_gate_522.py:34-61, :78
- #518: the verified reader's fail-closed paths → tests/unit/test_deploy_gate_518.py:31, :54, :69, :84, :94
- Tightening only across the stack: the remerge diffs above; the regex comparison; the end-to-end probes

## Risks queued
- **R1** scripts/deploy_gate.py:396-397: the D-233 comment line is 192 characters, against about 120 in the rest of the
  file. Lint passes. This is cosmetic, so wrap it the next time the file is touched.
