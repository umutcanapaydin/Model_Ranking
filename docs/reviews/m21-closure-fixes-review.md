---
record_type: review
id: m21-closure-fixes-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 closure fixes, round 2 -- code review

**Reviewer:** Code-Reviewer seat, a fresh session that wrote none of the range (author family: Claude Code,
`GP-Agent: claude-code/local-lane`; reviewer family: the same, no second family on this machine)
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `4917806..e877168` (17 commits, 21 files)
**Risk tier:** HIGH

## Verdict
BLOCKING

One BLOCKING finding. M6's fix resolves a written path against `$CLAUDE_PROJECT_DIR` alone. As a result, the
write refusals no longer cover the `.claude/` and `.githooks/` of any other worktree of this repository, and
that is where this project's agents do all their commits. The previous literal pattern held those paths.
Eight MINOR findings and one risk follow.

Most of round 1 is fixed:
- B1: a declared red commit now has an in-rule gate, and `3c5954f`'s row agrees with it.
- M1: renames, HEAD's copy and a missing `make` are fixed.
- M2: R-1's premise is corrected, and the Swift legs read no Markdown.
- M5 is fixed.
- M3, M4, M6 and M7 are fixed in part.

## What I read and ran

- **Read.** Round 1 first, then each of the 17 commits with `git show`, against round 1's findings and the
  decisions the brief lists.
- **Tests run.**
  - pytest on `test_commit_gate.py`, `test_check_fast.py`, `test_wave_check_m21_rules.py`,
    `test_wave_check_m19_rules.py` and `test_bash_guard_bounds.py`: 110 passed.
  - `conformance/test-hook-claims.py`: PASS (2 claims, 18 legs).
  - `scripts/wave_check_all.py`: PASS, 68 records.
  - `scripts/check_records.py`: PASS before this file was written (see M8).
- **Each fix commit's own tree.** I extracted each tree with `git archive` into a scratch directory and ran the
  four changed unit-test files there.
  - `a024244`, `0b49f18`, `e8ff620`, `17a2a0b` and `048e59f` pass.
  - `85f80e3` fails 6 tests (M2).
- **Probes.**
  - The real `.githooks/commit-msg` and `scripts/commit_gate.py`, copied into a scratch repository with a
    recording `make` stub. I ran 10 commit shapes: the first commit, red, amend, merge, cherry-pick, an
    empty message, a `#` first line, and a changed gate. I also ran it in a linked worktree.
  - `wave_check` functions, run in process on crafted ledgers, on a scratch history with a merge, and on an
    unknown SHA.
  - Both PreToolUse hooks, fed payloads through their entries. I used only ordinary paths: reads, `~/.claude`,
    a payload `cwd`, and a path in another worktree. I executed no crafted command and built no evasion
    payload.
- **Planted faults.**
  - 16 in `scripts/` and the `Makefile`, in this worktree. Each was restored by its bytes and checked by
    sha256.
  - 9 in `.claude/` in a `git archive` export under the scratchpad, never in this worktree's `.claude/`. Each
    guard fault was re-pinned there, so it ran past the pin.
- **Not run.** The Swift suites, `make client-decls`, `make check-fast`, `make check`, and anything that
  deploys.
- **Side effect.** `test_bash_guard_bounds.py` left a git-ignored `.claude/hooks/__pycache__/` (15:33). I left it
  in place, because this seat does not edit `.claude/`. `git status` is clean apart from this file.

## Round 1, finding by finding

| Round 1 | State | Where |
|---|---|---|
| B1 red commits refused | fixed; the new gate is wider than a red commit (M1) | `scripts/commit_gate.py:51-56`, `Makefile:218-222` |
| M1 rename, HEAD's copy, missing make | fixed | `.githooks/commit-msg:22-36`, `scripts/commit_gate.py:65` |
| M2 R-1's premise | fixed; its test pins the legs by substring (M7) | `docs/refusals.md:27`, `tests/unit/test_commit_gate.py:163-177` |
| M3 review resets, dates | fixed in part (M3) | `scripts/wave_check.py:579-614` |
| M4 Bypass matching | fixed for a named SHA; the rest in M4 | `scripts/wave_check.py:624-666` |
| M5 plan's `**Base:**` | fixed (no reader left: `grep` finds only the docstring) | `scripts/wave_check.py:396-407` |
| M6 write refusals, pin, C call | fixed as asked, and opened B1; rest in M6 | `.claude/hooks/bash_guard.py:618-646`, `.claude/settings.json:40,51` |
| M7 records, standing globs | records fixed; the list is short (M5) | `scripts/wave_check.py:290-293`, `AGENTS.md:105,107` |

## Findings

### BLOCKING

- **B1** `.claude/hooks/bash_guard.py:618-631` (`_owners`), `.claude/settings.json:40` (the Write/Edit hook),
  `conformance/test-hook-claims.py:510`. **The write refusals now hold only `$CLAUDE_PROJECT_DIR`'s own
  `.claude/` and `.githooks/`. Every other worktree of this repository is open, and a worktree is where this
  project's agents commit.**
  - **What is wrong.**
    - Both checks resolve the path, then compare it with `$CLAUDE_PROJECT_DIR/.claude` and `.githooks` and
      with nothing else.
    - Under the owner's `repository-hooks` ruling (`docs/control-events.csv:40`), sessions start in
      `~/Desktop/ILGAR/model_ranking`. The work happens in `git worktree add` checkouts under the
      scratchpad. `git worktree list` shows more than ten.
    - `core.hooksPath` is the relative `.githooks`. So git runs each worktree's own `.githooks/commit-msg`,
      and an uncommitted edit to it applies at once. I measured this in a scratch repository's linked
      worktree: an edited copy printed its marker on the next commit.
    - Before this range, the literal pattern (`*/.claude/*`, `*/.githooks/*`; `OWNERS_PATH`) refused these
      paths wherever they were.
  - **Measured through the entries.** These are ordinary payloads, and none was executed.
    - Session in the main clone, a Write to `<this worktree>/.githooks/commit-msg`: exit 0.
    - The same for `<this worktree>/.claude/hooks/bash_guard.py`: exit 0.
    - Bash, project set to another copy of the repository, payload `cwd` the worktree:
      `cp notes.md .githooks/commit-msg` gives exit 0.
    - The harness enshrines the opening. Its case `/Users/x/repo/.claude/hooks/bash_guard.py` must be
      allowed (`:510`), and no case puts a worktree of this repository beside the project.
  - **The same change gave up a second set of paths the literal pattern held.** Paths are resolved against
    the payload's `cwd`, and the guard does not follow a `cd`, `pushd` or `git -C` inside the command. So a
    path like `../.githooks/x` after `cd ios &&` was refused before and is allowed now. G-7 lists "a
    directory the command changes into", but its example (`cd .claude && ...`) is a case that was never held.
  - **Failure scenario.** In M22 an agent edits `.githooks/commit-msg`, `.claude/settings.json` or the guard
    in its worktree with the Write tool, as an ordinary edit. Nothing refuses it.
    - A `commit-msg` edit changes the gate for every later commit in that worktree at once.
    - A settings or guard edit goes into the combined PR. The owner merges such PRs all at once.
    - Neither carries OWNER APPROVAL, which S3 requires.
  - **Fix.**
    - Refuse the literal pattern again (case-folded) everywhere except under Claude Code's own
      `Path.home()/".claude"`. That is the only over-refusal round 1 measured.
    - Or treat as the project's any directory whose `git rev-parse --git-common-dir` is the project's.
    - Keep the resolved check for links.
    - Add must-block cases: a worktree of this repository, and a payload whose `cwd` is a subdirectory.
    - Say in G-7 what the refusal covers.

### MINOR

- **M1** `scripts/commit_gate.py:46-56`, `:59-61`, `tests/unit/test_commit_gate.py:53`, `docs/refusals.md:27`,
  `.claude/agents/Tester.md:58-60`, `.claude/skills/fix-issue/SKILL.md:13,26`. **`check-red` takes any commit
  whose subject has the word "red" and that stages one test path, code included. A declared red commit must
  pass only lint, types and the record checks, and nothing checks that it is red.**
  - **The red path is wider than a red test commit.**
    - `any(path.startswith(TEST_DIRS))`, and the test asserts that a `src/` change passes `check-red` (`:53`).
      Of the 161 `test: ..., red` commits among the last 600, 38 staged non-test paths. They include shipping Swift
      (`ios/ModelRanking/Engine/*.swift`), `src/app/workflows/registry.py`, and the compiled gate
      `scripts/client_decl_gate.py`.
    - `check-red` drops `swift-test` and `client-decls`, so the Swift in such a commit is not compiled at
      all.
    - Measured through the hook:
      - `test: the red-to-green order holds` with `src/` and `tests/` gives `check-red`. The `\bred\b` regex
        reads "red-to-green" as a declaration.
      - `git commit -m "#241 wire e" -m "test: e, red"` gives `check-red`, and git records the subject
        `#241 wire e`. `subject_of` skips a `#` line that git keeps under `-m`, so the hook and `wave_check`'s
        `%s` disagree.
      - A reworded amend of a red commit to `fix:`, with nothing staged, gives `check-docs`. The hook judges
        an amend by its increment, so a Swift red commit then lands as `fix:` without `swift-test`.
  - **The check R-1 rests on does not exist as written.**
    - R-1 and `commit_gate.py:19-20` say the Tester "checks that each red commit fails only on its own tests".
    - The Tester profile (`Tester.md:58-60`) and `/fix-issue` step 6 check only that the red test fails before
      the fix and passes after.
    - "Every other test passes" (`/fix-issue` step 3) is now checked by nobody at the commit. Nothing lists a
      wave's declared red commits for the Tester either.
  - **Failure scenario.** A code commit is subjected `test: x, red` and stages a test file. No test runs and
    no Swift compiles. The review row (`control-events.csv:39`) says such commits need no ledger row. The
    next `check-fast` is red for a reason its own diff does not hold.
  - **Fix.**
    - Gate `check-red` on every staged path being under `TEST_DIRS` or docs-only. A red commit that needs a
      stub in code then runs `check-fast` without `test` only, so it still compiles.
    - Anchor the declaration to the forms in use: `, red` and `(red)`.
    - Read the subject as `%s` does, or refuse a first line that starts with `#`.
    - Write the "fails only on its own tests" step into `Tester.md`, or drop the claim from R-1 and the gate.
    - Say in R-1 that a red commit may carry code, so that the owner rules on what is true.

- **M2** `docs/control-events.csv:41`, commit `85f80e3`. **`85f80e3` was committed with its own tree red, like
  `cd563f5`, and has no ledger row.**
  - **Measured.** The commit removes `.githooks/pre-commit`, and its `commit-msg` arrives only in `a024244`.
    On `85f80e3`'s tree, `test_commit_gate.py` fails 6 tests: the `commit-msg` file is missing.
  - **The two records disagree.**
    - `85f80e3`'s message says "make check-fast ran on the tree holding both". That is the reason `:41` gives
      for `cd563f5`'s bypass row.
    - `cd563f5` got a row. `85f80e3` did not.
  - **Failure scenario.** The ledger counts one event since the ruling where there were two. It is the same
    under-count the repo review's M1 found.
  - **Fix.** Add the `bypass` row for `85f80e3`. That makes two `commit-after-check-fast` rows since the owner's
    ruling, the same day.

- **M3** `scripts/wave_check.py:586`, `:590-591`, `:597-614`. **Only a `ruling` resets now, but the owner check
  accepts the text every review row carries. A row appended after a ruling with an earlier date is never
  counted, and kinds are not validated.**
  - **Measured in process.**
    - A `ruling` whose reason is "the agent's application (not the owner's ruling; the owner may overrule
      it)" resets the count, and `ledger_problems` says nothing. `"the owner" in reason` matches the very
      phrase both `review` rows use (`:38-39`). A review mistyped as a ruling, the likeliest error, passes.
    - Three `bypass` rows appended after a ruling dated 2026-10-10, each dated 2026-10-09: no strike, no
      problem. Order is by date first, and nothing ties a new row's date to its place in the file.
    - Kinds `bypassed` or `by-pass` count nothing and raise nothing.
    - `today` is the checker's local date. A row the owner dates between 00:00 and 03:00 (UTC+3) fails CI's
      UTC clock until 03:00.
  - **Is the owner check proportionate?** A string check in an agent-written ledger cannot prove the owner,
    and need not. It should still catch the honest mislabel, and as written it cannot.
  - **Fix.**
    - Require the reason to start with `the owner`, as both real rulings do.
    - Refuse a `skip` or `bypass` row placed after a ruling but dated before it.
    - Refuse a kind outside the header's five.
    - Compare dates with a day of slack, or against the adding commit's date.

- **M4** `scripts/wave_check.py:624-637` (`_gate_target`), `:641-666`, `:709-717`. **Row 9's SHA check reads a
  merge as docs-only, takes an unknown SHA as written on a full history, and still passes a `Bypass:` that
  names no SHA on another control's row.**
  - **Measured on a scratch history.**
    - A `--no-ff` merge bringing in `src/f.py`: `git show --name-only` prints nothing for a merge (combined
      diff), so `_gate_target` gives `check-docs` and a `within-scope` row is accepted.
    - A SHA that no history holds, on a full clone: accepted with the same `SKIPPED` note that a shallow clone
      prints.
    - A `Bypass: commit-after-check-fast once; security-pass N/A` with only a `security-pass` row and no SHA:
      it passes. That is round 1's second X4 form.
  - **CI's shallow clone.** The CI test job checks out one commit (`.github/workflows/ci.yml:38`), so there
    every `within-scope` row is taken as written. The note says so, which is honest. Local `wave-check-all`
    (in `check-fast`) has the history and holds it.
  - **Mutant X10 survives.** With `--no-renames` dropped from `_gate_target`, every test still passes.
  - **Failure scenario.** A close names a merge or a mistyped SHA in `Bypass:` with a `within-scope` row, and
    passes on every machine.
  - **Fix.**
    - Read a merge's paths against its first parent (`git diff --name-only --no-renames <sha>^1 <sha>`).
    - On a full history, an unknown SHA is a problem, not a note.
    - Require every control the field names (any control in the ledger) to have its own row for the wave.
    - Add a rename case.

- **M5** `scripts/wave_check.py:290-293`, `docs/plans/m21-plan.md:86-88`, `docs/reviews/m21-repo-review.md:115-129`.
  **`STANDING_GLOBS` leaves out three of the gates the repo review's M3 named, and two that M21's plan lists.**
  - **Missing.**
    - From the repo review's M3: the text pins `tests/unit/test_router_hints.py` and
      `tests/unit/test_ios_client_contract.py`, and `scripts/offline.sb` (INV-6).
    - From M21's plan: `.github/workflows/**` (where CI runs the gates) and `tests/conftest.py`.
    - Also missing: `stack.mk`, which adds `check:` legs and sets `CHECK_FAST_OWN_LEGS`.
  - **Failure scenario.** M22's plan lists its own globs without these. A wave that loosens a text pin, the
    offline sandbox or a CI step closes MEDIUM, which is M7's scenario again for these files.
  - **Fix.** Add them, and pin the full tuple in the test.

- **M6** `.claude/hooks/bash_guard.py:625`, `:633-646`, `:2-21`, `.claude/settings.json:40,51`,
  `docs/security-invariants.md:192`, `conformance/test-hook-claims.py:442-512`. **The new resolution is
  half-tested, `-t` is read as a destination for every program, and `-I` reaches only one of the hooks'
  interpreters.**
  - **Mutants that survive the harness** (planted in a scratch export, re-pinned):
    - G2: the guard without link resolution (`abspath`);
    - G3: the guard ignoring the payload's `cwd`;
    - G8: the Write hook ignoring the payload's `cwd`.

    No harness payload carries a `cwd`, though Claude Code always sends one, and no Bash case writes
    through a link.
  - **`_destinations` refuses reads.** It takes the word after `-t` as a destination for every program.
    Measured through the hook:
    - `rsync -t .claude/settings.json /tmp/out` (`-t` keeps times) is blocked. It was allowed before this
      range.
    - `cp -t /tmp/out .claude/settings.json` is blocked. Its last word is a source.

    Both contradict "Reading them is not refused".
  - **`-I` reaches only the guard.**
    - The hooks' inline steps run `"$py" -c`, which puts the hook's working directory first on `sys.path`:
      the interpreter probe, the Bash text pre-filter, and the whole Write refusal (`import sys,json,os,re`).
    - The hook's working directory is the project, which an agent may write. That is round 1's import class,
      moved from `.claude/hooks/` (owner-only) to a directory the agent can write. I judged it from the code
      and built no shadow module.
    - G-7 says `-I` means "neither a changed guard nor a module placed beside it changes what runs". That is
      true of the guard file only.
  - **Fix.**
    - Add `-I` to every `"$py" -c` in both hooks (OWNER APPROVAL).
    - Read `-t` as a destination only for `cp`, `mv`, `install` and `ln`, and then skip the last-word rule.
    - Add harness cases for a payload `cwd` (a subdirectory with `../.githooks/x`) and for a Bash write through
      a link.
    - Say in G-7 which interpreters `-I` covers.

- **M7** `tests/unit/test_check_fast.py:82-89`, `scripts/commit_gate.py:59-61`. **The gates' leg lists are
  pinned by a substring, so the M2 guarantee is not held.**
  - **Mutant X16 survives.** `make check-docs` with `--without swift-test client-decls conformance` passes
    every test, because `dropped in printed` matches a prefix.
  - **What that allows.**
    - `check-docs` could drop `test` or `conformance`, the legs R-1 keeps because they read Markdown.
    - `check-red` could drop `lint`, `typecheck` or the record checks, the legs R-1 says a red commit must
      pass.
  - **Mutant X4 survives** (`subject_of` keeping `#` lines). No test gives the gate a message file with git's
    comment lines.
  - **Failure scenario.** A later edit widens a `--without` list. Every test stays green, and docs-only
    commits stop running the legs that read Markdown.
  - **Fix.**
    - Assert the exact `--without` list, or the exact `check_fast.py --plan` legs, for each target.
    - Add a message-file case with a template and comment lines.

- **M8** `docs/reviews/m21-closure-fixes-review-round-1.md:3`, `docs/release-testflight.md:23-34`,
  `.claude/settings.json:51`, `AGENTS.md:107`. **Four record problems: a duplicate record id, a missing restart
  step in the owner's order, a misleading BLOCKED line, and AGENTS.md's "every commit".**
  - **Duplicate id.** `9835520` renamed round 1's file but kept `id: m21-closure-fixes-review`. This record must
    carry that id. Measured with this file in place: `check_records FAIL [repo]: 1 finding(s)`,
    `[R3] duplicate id`. Every `check-fast`, `check-red` and `check-docs` fails until it is fixed. The
    precedent is `fix-issue-139-tester-round-1.md`, whose id carries the `-round-1` suffix.
  - **The re-pin flow is not in the order the owner follows.**
    - It is in `INSTALL.md:21-26` and G-7.
    - The runbook's v2 step 1 has the owner pull a new guard and a new pin. Any Claude Code session open in
      the clone then blocks every Bash call, and no step says to close or restart it.
    - The BLOCKED line says "until the owner pins it again". After a pull the pin is already right, and only a
      new session helps. The line does not point to `INSTALL.md`.
  - **"Gates every commit" is not true.** AGENTS.md says `commit-msg` "gates every commit". Git runs no
    `commit-msg` on `cherry-pick` or `rebase`, which I measured.
  - **Fix.**
    - Set round 1's id to `m21-closure-fixes-review-round-1`.
    - Add to v2 step 1: "close every Claude Code session in the clone before you pull, and start a new one
      after".
    - Make the BLOCKED line name the restart and `INSTALL.md` (OWNER APPROVAL).
    - Say "every commit made with `git commit` or `git merge`".

### PASS (what looks good)

- **The docs path.**
  - `check-docs` keeps every Python leg (`check_fast.py --plan`: lint, typecheck, test, the records,
    conformance).
  - The Swift tests and `client_decl_gate.py` name no Markdown file outside comments and docstrings, and a
    test holds that.
- **The hook fails closed.** It refuses with no Python, an unreadable HEAD copy, a gate that exits non-zero or
  prints nothing, or no `make`.
  - HEAD's copy decides a commit that changes the gate.
  - The first commit falls back to the working tree's copy and still gates (`check-fast`).
  - On a branch whose HEAD holds the pre-`85f80e3` gate, that gate reads `--message-file` as paths and
    answers `check-fast`, the strict side.
  - It works in a linked worktree.
- **The ledger.** `3c5954f` is now `within-scope`, consistent with the gate. The `repository-hooks` ruling is a
  row, and the header names `git commit --no-verify`. Mutants X6 to X9 and X11 to X14 are killed.
- **M5.** The `**Base:**` line is gone and its test holds (round 1's X6).
- **Guard, as far as it reaches.**
  - `~/.claude` passes: `mkdir -p ~/.claude/plans`, a redirect and the Write hook all exit 0.
  - Case and option destinations block. G1, G4, G5, G6, G7 and G9 are killed.
  - The C-call claim is corrected in the guard, G-7 and the test docstring.

## Hardened-invariant producers

| Producer | Citing tests | Gaps |
|---|---|---|
| **INV-82 / S3:** the Bash guard's `_owners` and `_destinations`, the Write/Edit hook, the pin and `-I` | `conformance/test-hook-claims.py` (5 new must-block, 2 must-allow, a `json.py` shadow, 4 Write paths); `test_bash_guard_bounds.py` | B1, M6 |
| **The commit control:** `commit_gate.py`, `commit-msg`, `check_fast.py --without`, `check-red` and `check-docs` | `test_commit_gate.py` (25), `test_check_fast.py` (2 new) | M1, M7, R1 |
| **The ledger rules:** `ledger_strikes`, `ledger_problems`, `_bypassed_commits` | `test_wave_check_m21_rules.py` (6 new) | M3, M4 |
| **The standing globs:** `STANDING_GLOBS`, `plan_globs` | `test_wave_check_m21_rules.py`, `test_wave_check_m19_rules.py` | M5 |

## Planted faults

| # | Fault | Result |
|---|---|---|
| X1 | `check-red` without the test-path condition | killed |
| X2 | `declared_red` without the `test:` prefix | killed |
| X3 | `staged()` without `--no-renames` | killed |
| X4 | `subject_of` keeps `#` lines | **survived** (M7) |
| X5 | `--without` drops nothing | killed |
| X6 | a `review` resets again | killed |
| X7 | future dates allowed | killed |
| X8 | `within-scope` always accepted | killed |
| X9 | any row of the wave satisfies a SHA | killed |
| X10 | `_gate_target` without `--no-renames` | **survived** (M4) |
| X11 | `plan_globs` without the standing list | killed |
| X12 | a non-ISO date accepted | killed |
| X13 | a ruling naming no owner accepted | killed |
| X14 | the SKIPPED path taken always | killed |
| X15 | `check-red` keeps `test` | killed |
| X16 | `check-docs` also drops `conformance` | **survived** (M7) |
| G1 | guard: no case-fold | killed |
| G2 | guard: no link resolution | **survived** (M6) |
| G3 | guard: payload `cwd` ignored | **survived** (M6) |
| G4 | guard: no option destinations | killed |
| G5 | guard: literal pattern with the project set | killed |
| G6 | Bash hook without `-I` | killed |
| G7 | Write hook: no case-fold | killed |
| G8 | Write hook: payload `cwd` ignored | **survived** (M6) |
| G9 | Write hook: no link resolution | killed |

## K.9 candidates spotted outside this wave's scope

None

## Risks queued to next M

- **R1** `.githooks/commit-msg:30-39`, `Makefile:213-222`, `scripts/check_fast.py:270-276`. **HEAD's copy picks
  only the target's name.**
  - **What runs instead of HEAD's copy.**
    - The working tree's `Makefile`, `stack.mk` and `check_fast.py` decide what that target runs. So a commit
      that widens a `--without` list or edits a `check-*` recipe is judged by its own change.
    - The hook runs whatever name HEAD's gate prints. A committed gate that printed `help` made the next
      commit pass on `make help` (probe).
    - Git runs no `commit-msg` on `cherry-pick` or `rebase`, so a restacked branch's commits are not gated.
  - **What would show it is real:** a commit that changes one of those files and passes its own gate, while
    HEAD's recipe would have failed it. Or a stacked branch rebased onto a moved base that carries a red
    commit not declared red.
  - **Mitigation to weigh.**
    - Refuse a target outside the three names.
    - For a commit that stages `Makefile`, `stack.mk` or `scripts/check_fast.py`, also run the target from
      HEAD's copies of those files.
