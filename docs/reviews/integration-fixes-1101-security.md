---
record_type: review
id: integration-fixes-1101-security
status: draft
seat: independent
process_version: v7.2
date: 2026-11-01
---
# Security Review — integration/fixes-1101 (delta review of #526 and #527, and the owner's guard patch for #533 and #529)

**Reviewer:** Security-Reviewer subagent (light mode; one delta review of the whole stack plus the guard-change review D-206 clause 9 asks for before a handover)
**Independent:** yes. I wrote none of this code or the patch. I have not reviewed these branches before.
**Date:** 2026-11-01
**Release range:** 74f8c07..f2835e4. `74f8c07` is main (PR #542). The range has 8 commits: D-234/D-235/D-236 (`4e8aee5`), #526 (`46c8e77` red, `9ed8629`, `099d3ee`, merged by `5be7337`) and #527 (`8a34d55` red, `d4acf7a`, merged by `f2835e4`). Every one carries the owner's identity and a `GP-Task:` trailer. Plus the owner's guard patch, `build/owner-guard-1101.patch`, sha256 `b9e185d4adaead236ee46a12d97306c59b61fff65c65f489b68f66ebe10dddea` (verified before applying). It is not in the range, because the owner applies it.
**Reviewed head:** 5fd1d2b4879e4798d62700b150530317071b6506 (round 3; round 2 was bad607decbf67d61d86f1ba4083821a1ba72386c, round 1 f2835e4b40086c854353afacbaedb079e158d77c), and the patch with sha256 b9e185d4adaead236ee46a12d97306c59b61fff65c65f489b68f66ebe10dddea, unchanged, applied to `git archive f2835e4`
**Risk tier:** HIGH (deploy-gate and Bash-guard control changes). The brief's `Paths that make a change HIGH:` is `none` (docs/project-brief.md:110), so the §11 senior-review trigger does not fire.

## Verdict
MINOR

(Round 1, at f2835e4: BLOCKING on B1. Round 2, at bad607d: MINOR on M2. Round 3, at 5fd1d2b: MINOR, M2 fixed; the open items are R2's environment note and R3, both queued, none blocking. See "Round 2" and "Round 3" below.)

The range and the patch only tighten. No refusal got weaker, the settings change is only the pin, and the patch is
safe to hand to the owner as it is. The verdict is BLOCKING because of one route that is older than this range (B1):
the deploy gate resolves its default branch by a short name. So an agent can still choose the policy it is judged by,
which is what #533 and D-236 set out to close. The tree does that today, and with the patch. The fix is in
`scripts/brief_fields.py`, which is agent code, so it needs no second owner patch. #526 leaves one entry point that
passes under a redirect (M1).

I worked in my own worktree, `scratchpad/wtsec1101`, at `f2835e4` (detached). It has its own `.venv` from
`make install` and its own `advisor.db` (D-174). The patch was applied in `scratchpad/guard-review-export`
(`git archive f2835e4`). No hook refused a write there. The probes ran in `scratchpad/probe1101/` and
`scratchpad/sec1101-other/`. `conformance/test-hook-claims.py` ran in `scratchpad/claims1101/{with,without}`, two
git-initialised copies. Nothing in the tree is changed but this file. Removed afterwards: one `coverage.json` that my
pytest run wrote into the export.

## Findings

### BLOCKING
- **B1** scripts/brief_fields.py:41, :334-338 (`DEFAULT_BRANCHES`, `protected_bases`): this route is older than the
  range, and the patch does not close it. The gate asks git for `merge-base origin/HEAD HEAD`, and for
  `origin/HEAD^{commit}`, by **short** name. git's resolution order puts `refs/<name>`, `refs/tags/<name>` and
  `refs/heads/<name>` before `refs/remotes/<name>`. So a ref that is not under `refs/remotes/origin/` can stand in
  for `origin/HEAD` (and likewise for `origin/main` and `main`). The guard allows both writes that make one, with and
  without the patch. Probe (`scratchpad/probe1101/probe.py`, old guard | patched guard):
  ```
  ALLOW | ALLOW | git tag origin/HEAD 0123abc
  ALLOW | ALLOW | git tag origin/main 0123abc        (also: git tag main, git tag -f origin/main)
  ALLOW | ALLOW | git fetch . 'refs/heads/*:refs/origin/*'
  ```
  The live guard let both writes run in a scratch clone (git 2.54.0). `c094a05` is HEAD~2, and the real
  `origin/HEAD` is `0b32743`:
  ```
  $ git tag origin/HEAD c094a05...            ->  merge-base origin/HEAD HEAD = c094a05 ("refname is ambiguous" on stderr only)
  $ git branch xHEAD c094a05...; git fetch . 'refs/heads/x*:refs/origin/*'
  brief_fields.protected_bases(clone)          ->  ['c094a05']      (git merge-base refs/remotes/origin/HEAD HEAD = 0b32743)
  ```
  Both pins (the merge-base and the tip, D-232/D-233) then name the planted commit. So the brief's
  `Deploy commands:`, `Working mode:` and HIGH paths are read from a commit the session chose. That is the attack
  D-236's rationale describes ("a session that can move it chooses the policy it is judged by"), reached without
  moving any ref the patch protects. Tags are shared across worktrees, so a tag planted from an agent session also
  changes the owner's own `make deploy-check` in the main checkout. `fly deploy` stays refused by the guard whatever
  the gate says (D-185), but `scripts/deploy_hosted_engine.sh` and `scripts/nightly_hosted.sh` are protected only by
  the declaration. OWASP A01 (broken access control: the policy reference can be swapped).
  **Remedy (a fix-issue, agent-side):** make `DEFAULT_BRANCHES` full ref names: `refs/remotes/origin/HEAD`,
  `refs/remotes/origin/main`, `refs/remotes/origin/master`, `refs/heads/main`, `refs/heads/master`. A full name
  matches git's first rule, so a tag or a `refs/origin/*` ref cannot shadow it. Keep the short form only in messages.
  Add a red test that plants `refs/tags/origin/HEAD` and `refs/origin/HEAD` at an older commit and asserts that
  `protected_bases` still returns the real tip. As an optional second layer, in the owner's next guard patch, refuse
  a `git tag`, or a refspec destination, whose short name is one of `DEFAULT_BRANCHES`, a pattern under `refs/`
  included.

### MINOR
- **M1** scripts/deploy_gate.py:1020-1021, :1070, :1083 (#526's command form). D-234 says a deploy given as the
  argument is refused while a `GIT_*` is set. But `judge` runs `deploy_in` with the caller's variables still in the
  environment (only the three `HARMLESS_GIT` names are popped, :124-125), and returns 0 on "not a deploy" before the
  `GIT_*` check at :1031. With `GIT_WORK_TREE` set to another repository, `toplevel` (:1070) returns that
  repository, its brief declares nothing, and the deploy passes:
  ```
  GIT_WORK_TREE=<other repo> python3 scripts/deploy_gate.py "fly deploy"   -> exit 0   (no variable: exit 2)
  ```
  `--check` still FAILs (the variable is appended at :1043 whatever the verdicts say), and `--judge` still refuses,
  because it reads the brief from its cwd. The command form has no production caller: the guard uses `--judge`
  (.claude/hooks/bash_guard.py:3459), and `make deploy-check` uses `--check` (Makefile:358). So this is MINOR. The
  tests point every variable at the same repository (tests/unit/test_deploy_gate_526.py:20-32), so this case is not
  held. **Remedy:** after `CALLER_GIT` is recorded (:123), pop **every** `GIT_*` the caller set from
  `os.environ`, not only the three, so `toplevel` and `deploy_in` read the real tree. The refusal still fires and
  still names each variable, so the owner's "refuse" ruling is kept. Add a test with `GIT_WORK_TREE` and with
  `GIT_DIR` pointing at a second repository, for all three entry points.

### PASS
- **#526, the three exceptions are harmless.** Each is popped from the gate's own environment (:124-125) before any
  git runs. `brief_fields` runs no git at import, and every later git (`brief_fields._git` :91, `open_batch` :125,
  `_PLAIN_GIT` :276, `toplevel` :1011) inherits the cleaned `os.environ`. None of them passes its own `env=`.
  - **`GIT_EXEC_PATH`** changes where git looks for its non-builtin helpers. It does not change which `git` runs
    (that comes from `PATH`), and it names no repository, index or object store. Popped, it reaches no git the gate
    starts. Probe: `GIT_EXEC_PATH=/nonexistent` gives the same refusals as no variable, on all three entry points.
  - **`GIT_EDITOR`**: no command the gate runs opens an editor.
  - **`GIT_REFLOG_ACTION`**: the gate writes no ref.

  `PATH` and `HOME` stay out of D-234's reach (R2).
- **#526, reachability.** The refusal is checked after the verdicts on every entry point. `judge` returns `refuse`
  for a failing verdict and otherwise reaches :1031. `check` appends the reason after the verdict loop (:1043). So
  neither entry point passes a deploy while a non-exempt `GIT_*` is set, M1's redirected root apart. Probes:
  `GIT_WORK_TREE=other` on `--check` gives FAIL naming `GIT_WORK_TREE`, and on `--judge` gives exit 2. `GIT_DIR=other`
  and `GIT_DIR+GIT_WORK_TREE=other` give exit 2 or 1 on all three entry points.
- **#527 / D-235.** The read is inside `#if DEBUG` (ios/ModelRanking/LaunchRouting.swift:21-28), beside
  `-UITestRouting`. `make client-decls` at the head, run by me, gives "client-decls PASS: 23 client file(s) in 4
  configuration(s) -- simulator, release: 3312; simulator, debug: 3324; device, release: 3312; device, debug: 3324".
  `DEBUG_ONLY` (scripts/client_decl_gate.py:3377-3384) refuses `ProcessInfo.arguments` in a Release build. The value
  feeds only `onDevice` (ContentView.swift:92, :160), which drives the caption, glow, prewarm, help text and the guide
  sheet (:560-813). The router is still `TieredRouter.forThisLaunch()`, and no board value is read from it, so D-104
  holds. TestFlight is an Xcode Archive, which is a Release build (docs/release-testflight.md:160-161).
- **The guard patch: no refusal got weaker.** Old and patched guard on 70 spellings: every change goes from ALLOW
  to BLOCK, and none goes the other way. The newly refused spellings:
  - `git branch -D main`, `git branch -m new`;
  - `git worktree add /tmp/w/MAIN`, `git worktree add -b origin/main`;
  - `git config -f .git/config remote.evil.fetch x`;
  - `git -C /tmp/other fetch origin 'refs/*:refs/*'`;
  - `git tag -m -l v1.0`, `git tag -ml v1`, `git tag --sort -l v1`, `git tag --format -l v1`, `git tag --trailer -l v1`.

  How the old checks carry over:
  - `_lands_on_gate` = `_unread_or_default` or `_lands`, a superset at every site it replaces (update-ref,
    symbolic-ref, fetch/pull, push).
  - `REMOTE_KEY` / `REMOTE_KEY_IN` widen `origin` to any remote.
  - `git branch -m a b` now checks the source as well as the destination. `git branch -m main old` was allowed
    before and is refused now.
- **#533, the remote-ref routes.** These are refused with the patch:
  - a refspec, a `--refmap`, `-c`/`--config-env`/`GIT_CONFIG_*`/`git config` `remote.<any>.url|fetch`;
  - `--rename-section remote.*`, `remote add --mirror`, `ORIGIN`, `origin/x`;
  - `branch -d/-D/-m/-M` and `-r` deletes, `worktree add -b/-B` or a bare `<dir>/main`;
  - `update-ref` under `refs/remotes/origin/`.

  `git fetch origin`, `git pull --ff-only`, `git fetch --prune origin` and `git fetch upstream` stay allowed.
  What still moves `refs/remotes/origin/*` is a fetch of origin from a URL rewritten by a config file the guard does
  not open, which the patch lists as not held. `include.path` itself is refused (probe). B1 is the route the patch
  misses.
- **#529, a tag option's value is never read as a flag.** In `_tag_words`, `mFu` take the rest of the word or the
  next word, and the long valued options take their value by `_unique` prefix. Every value-as-flag spelling is
  refused: `-m -l`, `-m-l`, `-ml`, `--mess -l`, `-F`/`-u`/`--cleanup`/`--local-user` followed by `-l`, `-n`, `-v` or
  `--contains`. The spellings still allowed (`-n -m x v1`, `-n5 -m x v1`, `-lm x v1`, `--edit -l v1`,
  `--cleanup=verbatim -l v1`, `-l -f v1`, `--contains HEAD -m x v1`, `-an -m x v1`, `-fn v1`) were each run by real
  git 2.54 under a non-`v` name. Each lists or exits with usage, and `git for-each-ref refs/tags` stayed empty
  afterwards.
- **What a session now loses.** These are newly refused, and none is a daily need:
  - `git branch -m <new>` alone (`git branch -m <old> <new>` stays allowed, probe);
  - `git branch -D/-d main`;
  - `git worktree add <dir>` whose last part is `main`, `master` or `trunk`;
  - an explicit `git fetch origin +refs/heads/*:refs/remotes/origin/*`.

  The guard's tests hold the allowed set, tests/unit/test_bash_guard_bounds.py (patched) `test_what_a_session_needs_of_its_refs_stays_allowed`.
- **settings.json is only the pin.** Both hook commands are byte-identical apart from the 64-character hash and its
  12-character prefix: a `diff` with the pins substituted is empty. The new pin
  `655f514ce7914d9d897a0feeb547531733b01725d227f8bb276b9cd6ff441485` is the sha256 of the patched
  `.claude/hooks/bash_guard.py`.
- **Tests, run by me on the patched export:** `tests/unit/test_bash_guard*.py`: 929 passed. The global coverage floor
  message is the partial run's, not a test failure. `conformance/test-bash-guard.py`: "PASS: 613 tool call(s) ...
  0 wrong verdict(s)". `conformance/test-hook-claims.py`, in git-initialised copies, PASS both with and without the
  patch ("2 enforcement claim(s) derived, 19 gate leg(s), 0 unbacked"). The author's report that it fails in a plain
  export is consistent with this: it needs a git work tree. In the worktree: `test_deploy_gate_526.py`,
  `test_intelligence_guide_527.py` and `test_ios_client_contract.py`: 98 passed.
- No new import, dependency, endpoint, secret, log statement or destructive operation. `.github/`, `.githooks/`,
  `Dockerfile`, `deploy/`, `pyproject.toml` and `requirements/` are unchanged in the range. `.claude/` is touched
  only by the owner's patch.

## Gates passed
- [x] Secret scan green (`make secrets` at f2835e4, from the dispatcher: "no leaks found")
- [x] `make deps` (pip-audit) green (from the dispatcher: "No known vulnerabilities found")
- [x] `make slopsquat` green (from the dispatcher: "PASS, 20 deps, 0 suspect"; no new import in the range or the patch)
- [x] Default-deny preserved for new external surfaces (no new surface; every control change adds refusals)
- [ ] Permission-matrix not violated: the guard patch is owner-applied (correct). B1 leaves the default-branch policy pin open
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model; the launch argument is Debug-only and selects a device state)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; HIGH paths are `none`)
- [x] SAST (bandit is not in the lock. I read the delta by hand: no new subprocess form, no `eval`, no `shell=True`. The new guard regexes have no nested quantifier.) Conformance at f2835e4 from the dispatcher: "PASS, 33 tests, 0 failing"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #526 / D-234 refusal on `--check` and `--judge` → scripts/deploy_gate.py:123, :1031, :1043; tests/unit/test_deploy_gate_526.py:53-67 (the command form under a redirect: M1)
- #526 three named exceptions, popped → scripts/deploy_gate.py:114-125; tests/unit/test_deploy_gate_526.py:86-112
- #527 / D-235 Debug-only read → ios/ModelRanking/LaunchRouting.swift:21-28; tests/unit/test_intelligence_guide_527.py:67, :80, :91; `make client-decls` PASS
- #533 / D-236 clause 1 (patched guard) → .claude/hooks/bash_guard.py `_lands`, `_worktree_made`, `_renames_remote`, `_moves_default`; tests/unit/test_bash_guard_bounds.py (patched) `test_the_default_branchs_refs_move_only_by_a_plain_fetch_or_pull_of_origin` (not met in full: B1)
- #529 / D-236 clause 2 (patched guard) → .claude/hooks/bash_guard.py `_tag_words`, `_moves_owner_ref`; tests/unit/test_bash_guard_bounds.py (patched) `test_a_tag_options_value_is_not_read_as_list_or_verify`, `test_a_refspec_that_may_land_under_refs_replace_is_the_owners`

## Risks queued
- **R1** scripts/deploy_gate.py:109: the comment says "Two named exceptions", but `HARMLESS_GIT` holds three
  (D-234 names three). Correct it with M1.
- **R2** scripts/deploy_gate.py:105-125: D-234 covers `GIT_*` only. The caller's `HOME` / `XDG_CONFIG_HOME` (global
  config, for example `core.excludesFile` or `status.*`) and `PATH` (which `git` runs) still shape the gate's git. The
  guard's "Not held" list names `core.excludesFile` (#317). This is not exploitable from an agent session that cannot
  set the owner's shell environment. Write it down in D-234's "Revisit when" so nobody reads D-234 as covering the
  environment as a whole.

## Round 2 — re-verification at bad607d (2026-11-01)

**Range:** f2835e4..bad607d (`3c10e7e` red and `f9f6489` fix for B1 as #545; `d340037` red and `55190fc` fix for M1;
merges `3baeaab` and `bad607d`). The guard patch is unchanged: sha256 `b9e185d4…dddea`, re-checked. I re-ran it in the
same seat (`scratchpad/wtsec1101`, now detached at bad607d, with its own `.venv`).

**Verdict: MINOR.** B1 and M1 are fixed, R1 and R2 are done, and one new MINOR finding (M2) is the narrower part of B1
that is left.

- **B1: fixed.** scripts/brief_fields.py:40-44 now lists `DEFAULT_BRANCHES` as full ref names, and
  scripts/review_need.py:129 and scripts/deploy_gate.py:206 read that one list. I re-ran the round-1 plant in a new
  scratch clone (`scratchpad/probe1101/r2/clone`), with three refs at HEAD~2 `c094a05`: a tag `origin/HEAD`, a tag
  `main`, and `refs/origin/HEAD` made by `git fetch . 'refs/heads/x*:refs/origin/*'`. Then
  `brief_fields.protected_bases(clone)` returned `['0b32743']`, the real tip (it returned `['c094a05']` in round 1).
  A full name that exists matches git's first rule, so it wins: `git merge-base refs/remotes/origin/HEAD HEAD`
  returns `0b32743` even with a tag `refs/remotes/origin/HEAD` planted, and git only warns that the name is ambiguous.
  The tests hold this: tests/unit/test_deploy_gate_545.py:34-43 (tag `main`, `refs/main`), :46-52 (tag
  `origin/HEAD`), :55 (review-need) and :64 (one list).
- **M1: fixed.** scripts/deploy_gate.py:126-127 deletes every `GIT_*` from the gate's environment after `CALLER_GIT`
  is read (:125) and before `GIT_NO_REPLACE_OBJECTS` is set. I re-ran the probe with `GIT_WORK_TREE`, `GIT_DIR`, and
  both together, each pointed at `scratchpad/sec1101-other`. The results:
  - the command form `"fly deploy"` exits 2; in round 1, `GIT_WORK_TREE` gave exit 0;
  - `--judge` exits 2;
  - `--check` exits 1 and names the variable;
  - `GIT_EXEC_PATH` and `GIT_EDITOR` are still not named, as D-234 intends.

  The test is tests/unit/test_deploy_gate_526.py:116-124: a second repository, all three entry points.
  `test_deploy_gate_526/545/517` and `test_review_need*` all pass: 56 passed.
- **R1: done.** The comment at scripts/deploy_gate.py:109-113 now counts three exceptions.
- **R2: done.** D-234's "Revisit when" now names `HOME`, `XDG_CONFIG_HOME` and `PATH`, and an "As built" line records
  M1 (docs/decisions.md, D-234).

### MINOR (new in round 2)
- **M2** scripts/brief_fields.py:337-341: a full name is still looked up with git's usual name resolution. When a
  full name does **not** exist, a tag of the same spelling stands in for it. In the r2 clone:
  - with a tag `refs/remotes/origin/master` planted, `git rev-parse --verify --quiet --end-of-options
    'refs/remotes/origin/master^{commit}'` returns `c094a05`;
  - `git show-ref --verify --hash refs/remotes/origin/master` says "not a valid ref".

  The guard allows `git tag refs/remotes/origin/HEAD <sha>` with and without the patch (probe). Today's live guard
  also allows `git branch -rd origin/HEAD origin/main`; the patch refuses it (probe: ALLOW | BLOCK). So until the
  owner applies the patch, a session can delete the real names and plant tags in their place: B1 by two steps. After
  the patch, this needs a checkout that never had `refs/remotes/origin/HEAD`. The main checkout has it (`git
  for-each-ref` there lists `refs/remotes/origin/HEAD -> refs/remotes/origin/main`).

  It is MINOR because the first step is the one D-236 refuses, and the patch goes to the owner with this stack. Until
  then, D-236's interim mitigation applies: the owner deploys from their own shell.

  **Remedy:** in `protected_bases` (and in `review_need.default_range`), resolve each name exactly first, with `git
  show-ref --verify --hash <full name>` or `git for-each-ref --format=%(objectname) <full name>`, which match exact
  names only. Skip a name that does not resolve, and give the sha to `merge-base` and the tip read. Add a red test that
  deletes `refs/remotes/origin/*` in a fixture and plants a tag `refs/remotes/origin/HEAD`.

### Risks queued (round 2)
- **R3** scripts/wave_check.py:441, :450, :524 still read the short names `origin/main` and `main`. This is record
  grading, not deploy policy, and it is noted on #545. A planted tag can still change which wave-close ADR order is
  graded. Move it to `brief_fields.DEFAULT_BRANCHES` when the file is next touched.

## Round 3 — re-verification of M2 at 5fd1d2b (2026-11-01)

**Range:** bad607d..5fd1d2b: `27cb587` is the red test and `cbf50e1` the fix, merged by `5fd1d2b`. The guard patch is
unchanged: sha256 `b9e185d4…dddea`.

**Verdict: MINOR.** M2 is fixed. Nothing BLOCKING is open. The verdict stays MINOR, not PASS, for the queued R3
(`scripts/wave_check.py` short names, record grading only).

- **M2: fixed.** `brief_fields.exact_ref` (scripts/brief_fields.py:324-331) reads a ref with `git show-ref --verify
  --hash <full name>`, which matches that exact ref only. `protected_base` (:337) and `protected_bases` (:350) skip a
  name that does not exist, and give the sha to `merge-base` and the tip read. The tip is now `<sha>^{commit}`, and
  git takes a 40-hex string as an object id, not as a ref name. `review_need.default_range` (scripts/review_need.py:130)
  does the same. I re-ran the probe in `scratchpad/probe1101/r2/clone`, where four tags are planted:
  `refs/tags/main`, `refs/tags/origin/HEAD`, `refs/tags/refs/remotes/origin/HEAD` and
  `refs/tags/refs/remotes/origin/master`. The results:
  ```
  exact_ref refs/remotes/origin/HEAD   -> 0b32743   (the real tip, through the symbolic ref)
  exact_ref refs/remotes/origin/master -> None      (rev-parse gave the planted c094a05 in round 2)
  exact_ref refs/heads/master          -> None
  protected_bases -> ['0b32743'], protected_base -> 0b32743
  ```
  The test is tests/unit/test_deploy_gate_545.py:73 (the deploy and review-need's range). `test_deploy_gate_545`,
  `526` and `517` and `test_review_need*` all pass: 57 passed.
