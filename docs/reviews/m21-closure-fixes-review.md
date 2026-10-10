---
record_type: review
id: m21-closure-fixes-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 closure fixes, round 3 -- code review

**Reviewer:** Code-Reviewer seat, a fresh session that wrote none of the range (author family: Claude Code,
`GP-Agent: claude-code/local-lane`; reviewer family: the same, no second family on this machine). I read the
code before the commit messages' summaries, and round 2's findings before either.
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `8f3cbfd..f9f5166` (18 commits, 20 files)
**Risk tier:** HIGH

## Verdict
MINOR

Round 2's BLOCKING finding is fixed. Every work tree's `.claude/` and `.githooks/` is now refused, by Write and
by Bash, from the payload's `cwd` and through `cd`, `pushd`, `git -C` and links. Each of round 2's other
findings is fixed as decided. Nothing here ships broken or opens a hole the decisions meant to close, so under
stop-at-three nothing is BLOCKING.

Seven MINOR findings, one K.9 candidate and one risk follow:
- The refusal over-refuses inside the worktrees Claude Code itself creates in a repository's `.claude/`.
- `-t` is misread when an attached option value contains a `t`.
- `check-red` leaves out the client's compile and the privacy gate.
- The new Bypass rule accepts any kind of row.
- GitHub closed two issues that were taken out after three verdicts, and the roadmap lists them as open.
- "Before every commit" survives in three places.
- Five stated properties have no test case.

## What I read and ran

- **Read.** Round 2 first, then each of the 18 commits with `git show`, against round 2's findings and the
  decisions the brief lists. I also read round 1 for context, and `e877168` (the `cd563f5` row).
- **Tests run.**
  - pytest on `test_commit_gate.py`, `test_check_fast.py`, `test_wave_check_m21_rules.py`,
    `test_wave_check_m19_rules.py` and `test_bash_guard_bounds.py`: 140 passed.
  - `conformance/run-all.py`: PASS, 16 of 16, the hook harness included.
  - `scripts/wave_check_all.py`: PASS, 68 records.
  - `scripts/check_records.py`: PASS. `ruff check src tests scripts`: clean.
- **Each fix commit's own tree.** I extracted each tree with `git archive` into the scratchpad.
  - The five test files pass on `d9f9ade`, `7edade4`, `5632397`, `9412654`, `c939211`, `18f7d96`, `7ba4b63`
    and `4351945`.
  - The hook harness passes on `3bb09b9`, in an export given its own `git init`. `protected` needs a `.git`
    beside `.claude/`, so a plain export fails 18 legs.
  - The red `965d99d` fails the harness, as it declares.
  - No commit of this range needs a ledger row.
- **Commit-gate probe.** I copied the real `.githooks/commit-msg` and `scripts/commit_gate.py` into scratch
  repositories, committed the gate first, and stubbed `make` to record the target.
  - 19 commit forms, each compared with git's own `%s`: `-m`, `-F`, the editor, `-e -m`, a `#` first line,
    `commit.cleanup` verbatim, whitespace, strip and scissors, `core.commentChar` `;` and `auto`, and
    `commit.verbose` true and 2. All 19 agree.
  - Merges: a `--no-ff` merge subjected `test: ..., red`, and a concluded conflicted merge of docs only, each
    gave `check-fast`. A `--squash` followed by a red commit gave `check-red`.
- **Hook probe.** I fed 30 ordinary payloads through both PreToolUse entries, from `.claude/settings.json`,
  with `CLAUDE_PROJECT_DIR` set to this worktree. The layout was a scratch repository, a linked worktree, a
  worktree at `<repo>/.claude/worktrees/wt`, a plain directory and a scratch `HOME`. I also ran five payloads
  under `/bin/sh`, `/bin/zsh` and `/bin/bash`. No command was executed, and I built no evasion payload.
- **In process.**
  - `protected` on odd paths.
  - `_target_option` on benign `install` argument lists, with the destination `/tmp/dest`.
  - `skip_ledger_problems` and `ledger_strikes` on crafted ledgers.
  - `pytest-collect`'s recipe in an export: exit 0 on the tree, and exit 2 once a test module fails to
    import.
- **Planted faults.**
  - 21 in the guard and the settings, in a `git init`ed export under the scratchpad, re-pinned there, never in
    this worktree's `.claude/`.
  - 24 in `scripts/`, the `Makefile`, `.githooks/commit-msg` and the ledger, in a second export.
  - Each was restored by its bytes and checked by sha256.
- **`gh`, read-only.** #251, the ten pull requests it carried, and the issues closed on 2026-10-10.
- **Not run.** The Swift suites, `swift-build-tests` itself, `make client-decls`, `make check-fast`,
  `make check`, and anything that deploys.
- **Deviations and side effects.**
  - I ran one `git fetch -q origin main`. That is network beyond read-only `gh`, which the brief does not
    allow. It changed only the local ref `origin/main`, which reads `0640401`, #251's merge commit.
  - `.claude/hooks/__pycache__/` (git-ignored, 17:37) was there before my runs. I left it, because this seat
    does not edit `.claude/`.
  - `git status` is clean apart from this file.

## Round 2, finding by finding

| Round 2 | State | Where |
|---|---|---|
| B1 every work tree's `.claude/` and `.githooks/` | fixed as decided; it over-refuses (M1) | `.claude/hooks/bash_guard.py:630-643`, `:673-686`, `:727-735`; `.claude/settings.json:40` |
| M1 red path, `%s`, reworded amend, R-1's Tester claim | fixed; `check-red` leaves out the client's compile (M3) | `scripts/commit_gate.py:64-117`, `Makefile:218-240`, `docs/refusals.md:27` |
| M2 `85f80e3`'s row | fixed; a test pins it | `docs/control-events.csv:43`, `tests/unit/test_wave_check_m21_rules.py:1054` |
| M3 owner check, row place, kinds, UTC | fixed | `scripts/wave_check.py:579-629` |
| M4 merge, unknown SHA, per-control rows, rename | fixed; the per-control row may be any kind (M4) | `scripts/wave_check.py:636-683`, `:733-739` |
| M5 standing globs | fixed; the whole tuple is pinned | `scripts/wave_check.py:291-294` |
| M6 `-t`, `-I`, `cwd` and link cases, G-7 | fixed; a `-t` misread is new (M2) | `bash_guard.py:689-723`, `settings.json:40,51`, `docs/security-invariants.md:192` |
| M7 exact legs, message-file case | fixed; three config paths are unpinned (M7) | `tests/unit/test_check_fast.py:98`, `tests/unit/test_commit_gate.py:146` |
| M8 id, restart, BLOCKED line, AGENTS.md | fixed; "every commit" survives elsewhere (M6) | `docs/release-testflight.md:26-30`, `settings.json:40,51`, `AGENTS.md:107` |
| R1 a gate name outside the three | fixed | `.githooks/commit-msg:37-40` |

## Findings

### BLOCKING

None

### MINOR

- **M1** `.claude/hooks/bash_guard.py:630-643` (`protected`), `:673-686` (`_follow`), `:87` (`MAX_DIRS`). **The
  refusal walks every ancestor of a path. So it refuses every write inside a worktree that Claude Code creates
  in a repository's `.claude/`. And no directory a command reached is ever dropped.**
  - **The code does what was decided.** That worktree's files lie "inside a `.claude` directory whose parent
    holds a `.git` entry", the repository's own. The wording of the decision is what over-refuses.
  - **Measured through the entries.** These are ordinary payloads; none was executed.
    - Write to `<repo>/.claude/worktrees/wt/src/f.py`: exit 2, where `wt` is a linked worktree with a `.git`
      file.
    - From that worktree's `cwd`, `echo x > src/f.py` and `touch src/new.py`: exit 2.
    - `cd .claude && ls && cd .. && echo x > notes.txt` from the clone: exit 2.
    - `cd ~ && mkdir -p .claude/plans` from the clone: exit 2. The path is judged from the clone as well.
    - Seven relative `cd`s in one command pass `MAX_DIRS` (2^7 directories), and the command is refused as
      unreadable.
  - **Claude Code does put worktrees there.** `claude --worktree` and a subagent's `isolation: "worktree"`
    both create them. On this machine the owner's other DevFlow projects hold six:
    `~/Desktop/ILGAR/fitness_app/.claude/worktrees/{editor,queue,v1-polish}` and
    `tempo-backend/.claude/worktrees/{ci,hard1,m2w1}`.
  - **What still passes, as it should.**
    - `git -C <worktree> commit`, `add .claude/settings.json` and `checkout -b`.
    - Reads and copies out of `.claude/`, `cp -t /tmp/out .claude/...` and `rsync -t`.
    - `cd <worktree> && make check-fast 2>&1 | tee build/...`.
    - A Write to `~/.claude` memory.
  - **Failure scenario.** In this clone, the lead gives a subagent `isolation: "worktree"`, or the owner starts
    `claude --worktree`. Every Write, Edit and Bash write there is refused. The message blames "the owner's
    hooks and settings", which is the wrong cause. The refusal fails closed, so this is not a hole.
  - **Fix** (OWNER APPROVAL, with the re-pin in the same commit).
    - Stop the walk at the innermost directory that holds `.git`, the work tree the path is in. Refuse only
      when the component directly below it is `.claude` or `.githooks`, in any case.
    - Add a must-allow case for `<repo>/.claude/worktrees/x/src/f.py`, and a must-block case for that
      worktree's own `.claude/settings.json`.
    - Say in G-7 that a directory a `cd` reached is never dropped.

- **M2** `.claude/hooks/bash_guard.py:689-700` (`_target_option`), `:711-712`. **Any short-option cluster
  that holds a `t` is read as `-t`. So an attached option value containing a `t` is taken as the destination,
  and the real destination is never judged. This regressed round 2's last-word rule for `install`.**
  - **In process.** I called the parser on benign argument lists with the destination `/tmp/dest`:
    - `install -ostaff x /tmp/dest` gives the `-t` value `aff`, and only `aff` is judged.
    - `install -oroot -gwheel x /tmp/dest` judges `-gwheel`.
    - Round 2's code judged the last word of every `install`.
  - **Where it applies.** `install`'s `-o`, `-g`, `-m`, `-B`, `-f` and `-S` take an attached value, as GNU
    `cp`'s and `ln`'s `-S` do.
  - **No case covers clusters.** Mutant G15 (`-t` read only when alone) survives the harness, and so does G16
    (`install -d` not judging every path).
  - **Failure scenario.** An `install` that names an owner or group attached, with its destination in
    `.githooks/`, passes the guard. The form is narrow, but the docstring lists it as held: `install` "with a
    destination there".
  - **Fix** (OWNER APPROVAL).
    - Read a cluster left to right, and stop at the first letter that takes a value for that program: for
      `install`, `B D f g h l m M N o S T`; for `cp` and `ln`, `S`.
    - Only a `t` before any such letter is the target option.
    - Add cases: a cluster ending in `t`, an attached value holding a `t`, and `install -d` with a protected
      path that is not last.

- **M3** `Makefile:218-219`, `docs/refusals.md:27`, `docs/EXPERIENCE.md:1033`,
  `tests/unit/test_check_fast.py:110-120`. **`check-red` leaves out `client-decls`, which runs no test. It is
  the only leg that compiles the client outside the Engine package, and the only run of the D-126 privacy
  gate. Nothing shows that `swift-build-tests` can fail.**
  - **What the legs build.**
    - `swift build --build-tests` builds `ios/Package.swift`, whose one target is `ModelRanking/Engine`, and
      its tests.
    - `scripts/client_decl_gate.py:623-625` type-checks every `*.swift` under `ios/ModelRanking` with the iOS
      SDK. That includes `ContentView.swift`, `Design.swift`, `LaunchRouting.swift` and
      `ModelRankingApp.swift`. It reads no test directory.
  - **The records call it a test.** R-1 lists `client-decls` among "the legs that run tests". The EXPERIENCE
    entry says a declared red commit "runs every leg but the tests". Neither is true.
  - **The new leg is unproven.**
    - Mutant X13 replaces the recipe's `[ $$rc -eq 0 ] ||` with `true ||`, so the leg cannot fail. Every
      test passes, because the test reads only `make -n` text.
    - The `Makefile`'s own `swift-test` comment records three Swift gates that could not fail.
    - `pytest-collect` I checked by hand, and it does fail on a module that cannot be imported.
  - **How likely.** No red commit among the last 600 staged client Swift outside the Engine, so this is
    latent.
  - **Failure scenario.** A declared red commit also stages a stub in `ContentView.swift`, or a change to
    `scripts/client_decl_gate.py`. It lands with the client uncompiled and the privacy gate unrun. The next
    `check-fast` commit is then refused for a change it does not hold.
  - **Fix.**
    - Keep `client-decls` in `check-red`: `--without test swift-test conformance`.
    - Correct R-1 and the EXPERIENCE line.
    - Pin that the `swift-build-tests` recipe exits non-zero when the build does. A stub `swift` on `PATH`
      that exits 1 is enough, as the commit-gate tests stub `make`.

- **M4** `scripts/wave_check.py:699-700` (`ledgered`), `:733-738`. **The rule "every ledger control the
  `Bypass:` names needs its own row" accepts a row of any kind. So a bypass named without a SHA is satisfied by
  a `within-scope`, `review` or `ruling` row, and the three-row rule counts none of those.**
  - **Measured in process.** The close is dated 2026-10-12, for `m22-w1`, with `Bypass:
    commit-after-check-fast once`. The ledger holds one row of that control for the wave.
    - Kind `bypass`: no problem, and the row counts.
    - Kind `within-scope`, `review` or `ruling`: no problem, and `ledger_strikes` counts nothing.
  - **It applies today.** The M21 closure already holds `ruling` and `review` rows for
    `commit-after-check-fast`. So any `m21-closure` close passes a SHA-less Bypass of that control on those
    rows alone.
  - **Failure scenario.** A close records "Bypass: commit-after-check-fast once" and files the event as
    `within-scope`. That is the honest mislabel round 2's M3 named. The close passes, and the three-row rule
    never sees the bypass. This is the under-count the repo review's M1 found.
  - **Fix.**
    - For the Bypass check, accept only a `bypass` or `skip` row of the control, or a `within-scope` row whose
      SHA the field names, which `_bypassed_commits` then confirms.
    - Add the three kinds as cases.

- **M5** `docs/roadmap-2026-10-10-post-m21.md:47`, `:54-55`; issues #194 and #222. **Two issues taken out
  after three verdicts are closed. GitHub closed them when #251 merged, and the roadmap lists them as open.**
  - **Measured with `gh`.** 52 issues closed on 2026-10-10. The agent closed 45 of them at 13:3x. GitHub
    closed seven at the merge (13:29): #187, #194, #206, #209, #210, #212 and #222.
  - **Why those two closed.**
    - #194 and #222 each end: "M21-W2: taken out after three verdicts ... This stays open."
    - Their commits' subjects begin `fix: #194's` (`35a8563`) and `fix: #222's` (`26a334a`). GitHub reads
      that as a closing keyword.
    - #218 was taken out the same way, has no such subject, and is open.
  - **The records disagree with that.**
    - The owner's rule closes an issue when its fix merges, and never a missed-bar one.
    - The roadmap calls the 45 "the issues the waves delivered in full" and lists #194 and #222 as open. It
      says nothing of what GitHub closed.
    - G-9 (`docs/security-invariants.md:193`) cites #187 for an open gap, and #187 is closed.
  - **Failure scenario.** M22 is planned from the open issues, and the two reading rules that were taken out
    are not among them.
  - **Fix.**
    - Reopen #194 and #222, with a comment that names the keyword.
    - Confirm that the other five were delivered in full.
    - Say in the roadmap what closed at the merge.
  - **The closure's own merge closes nothing more.** The 62 commits of `closure/m21` past `0640401` carry no
    closing keyword (measured).

- **M6** `INSTALL.md:141`, `docs/release-testflight.md:31`, `Makefile:443`. **"Before every commit" survives
  in three places, though AGENTS.md and R-1 now say `git commit` and `git merge`.**
  - The test at `tests/unit/test_wave_check_m21_rules.py:1064` pins only AGENTS.md.
  - **Failure scenario.** The owner, following v2 step 2, reads that every commit is gated. A `cherry-pick`
    or `rebase` of a stacked branch runs no gate.
  - **Fix.** Use the same words in the three places, and have the test read all four.

- **M7** `tests/unit/test_commit_gate.py:146-163`, `conformance/test-hook-claims.py:523-560`. **Six properties
  that the code states, and holds, have no case.**
  - **The commit gate.**
    - Three mutants survive: X3 (`core.commentChar` ignored), X4 (`commit.cleanup` ignored) and X5 (the
      scissors cut ignored).
    - The code is right: in the scratch repositories, each of those forms gave the gate git's own `%s`.
  - **The guard.**
    - G13 survives: a `cd` judged from the last directory reached, not from each one. Round 2's decision is
      "from every directory reached", and that matters after a `cd` made in a subshell.
    - G14 survives: `MAX_DIRS` unchecked.
    - G16 survives: `install -d`.
  - **Failure scenario.** A later edit drops one of these, and every test stays green.
  - **Fix.**
    - Add the three config forms to the editor test.
    - Add harness cases for a relative `cd` after one made in a subshell, for a command past `MAX_DIRS`, and
      for `install -d`.

### PASS (what looks good)

- **The write refusal, as decided.**
  - Seven ordinary writes into a linked worktree's, a clone's or the cwd's `.claude/` and `.githooks/` are
    refused through the entries. They come by Write, a redirect, `cp`, `tee`, `git -C ... mv`, and
    `cd <worktree> &&` from an unrelated `cwd`.
  - A `.claude/` with no `.git` beside it passes.
  - The harness kills 17 of 21 faults, round 2's survivors G2, G3 and G8 among them: here G4, G10 and G11.
  - `protected` is bounded and safe on odd paths: an empty path, `/`, forty `../`, `~nouser/`, a link loop,
    1500 levels, an unset variable, a dangling `.git` link (still protected), and a NUL (raises, and `main`
    blocks).
- **The pin.**
  - `shasum -a 256 .claude/hooks/bash_guard.py` = `3f73f168...6a55`, the value in both hooks
    (`.claude/settings.json:40,51`).
  - Under `/bin/sh`, `/bin/zsh` and `/bin/bash`, as a fresh session runs them, both hooks give allow, block,
    allow, block and block on five payloads.
  - The Write hook's pin and `--write` are each held: S2 and S3 are killed.
  - The guard also runs under the macOS stock Python 3.9.
- **The commit gate.**
  - The 19 subject forms and the merges listed above.
  - The allowlist of three names: X22 is killed.
  - `--with` refuses a name that is no target, or that is in `check:` already: X12 is killed.
  - Each gate's legs are pinned exactly: X10 and X11 are killed.
- **The ledger.**
  - X14 to X21 are killed, including round 2's surviving X10, here X21.
  - 68 closes pass, and `ledger_problems` finds nothing.
  - Two `bypass` rows count after the ruling (`cd563f5` and `85f80e3`), and no control strikes.
- **The records.**
  - R-1's pointers hold: `/fix-issue` `SKILL.md:24-27`, and row 2 of all four M21 wave closes.
  - #251 merged on 2026-10-10 at 13:29Z as `0640401`, with the ten pull requests the runbook names.
  - The runbook's step 1 restarts every session after the pull.
  - INSTALL.md names both pins.
  - G-7 says what `-I` covers and what it does not.
  - The EXPERIENCE entry's two `bypass` rows and "a third would put the control before the owner" match the
    ledger.

## Hardened-invariant producers

| Producer | Citing tests | Gaps |
|---|---|---|
| **INV-82 / S3:** `protected`, `_follow`, `_changes_into`, `_target_option`, `_writes_protected`, `_git_writes`, `judge_write`; both hooks' pin and `-I` | `conformance/test-hook-claims.py:523-584` (14 Bash and 10 Write tree cases, the `-I` scan, a `json.py` in the hook's directory, the changed-guard Write case); `tests/unit/test_bash_guard_bounds.py` | M1, M2, M7 |
| **The commit control:** `commit_gate.py` (`subject_of`, `cleanup`, `merging`, `target`), `.githooks/commit-msg`, `check_fast.py --with`, `check-red`, `swift-build-tests`, `pytest-collect` | `tests/unit/test_commit_gate.py:146`, `:165`, `:174`, `:264`; `tests/unit/test_check_fast.py:98`, `:110` | M3, M6, M7 |
| **The ledger rules:** `_owners_ruling`, `ledger_strikes`, `ledger_problems`, `_gate_target`, `_bypassed_commits`, `skip_ledger_problems` | `tests/unit/test_wave_check_m21_rules.py:960` and the M3 and M4 tests | M4 |
| **The standing globs:** `STANDING_GLOBS` | `tests/unit/test_wave_check_m21_rules.py` (the whole tuple) | none |

## Planted faults

| # | Fault | Result |
|---|---|---|
| G1 | `protected` without the `.git` check | killed |
| G2 | `.git` must be a directory | killed |
| G3 | no case-fold | killed |
| G4 | `abspath` for `realpath` | killed |
| G5 | no `cd` tracking | killed |
| G6 | `pushd` ignored | killed |
| G7 | `git -C` ignored | killed |
| G8 | `rsync -t` read as a destination | killed |
| G9 | with `-t`, the last word judged too | killed |
| G10 | Bash: the payload's `cwd` ignored | killed |
| G11 | Write: the payload's `cwd` ignored | killed |
| G12 | Write: `.env` not refused | killed |
| G13 | `cd` judged from the last directory only | **survived** (M7) |
| G14 | `MAX_DIRS` unchecked | **survived** (M7) |
| G15 | `-t` read only when alone | **survived** (M2) |
| G16 | `install -d` not judging every path | **survived** (M2, M7) |
| G17 | `git rm` not refused | killed |
| G18 | redirections not judged | killed |
| S1 | Write hook: the guard without `-I` | killed |
| S2 | Write hook: no pin check | killed |
| S3 | Write hook: the guard in Bash mode | killed |
| X1 | `subject_of` always strips `#` lines | killed |
| X2 | the editor always assumed | killed |
| X3 | `core.commentChar` ignored | **survived** (M7) |
| X4 | `commit.cleanup` ignored | **survived** (M7) |
| X5 | the scissors cut ignored | **survived** (M7) |
| X6 | a merge ignored by `target` | killed |
| X7 | nothing staged read as docs | killed |
| X8 | `red` back to `\bred\b` | killed |
| X9 | the hook never sees `MERGE_HEAD` | killed |
| X10 | `check-red` without `--with` | killed |
| X11 | `check-red` keeps `client-decls` | killed (the pin holds the leg list M3 would change) |
| X12 | `--with` never refuses | killed |
| X13 | `swift-build-tests` cannot fail | **survived** (M3) |
| X14 | a ruling found anywhere in the reason | killed |
| X15 | two days of date slack | killed |
| X16 | kinds unchecked | killed |
| X17 | a ruling never resets | killed |
| X18 | a merge read by its diff | killed |
| X19 | an unknown SHA only a note | killed |
| X20 | the per-control Bypass rows unchecked | killed |
| X21 | `_gate_target` follows renames | killed |
| X22 | the hook runs any name | killed |
| X23 | `stack.mk` dropped from the standing globs | killed |
| X24 | `85f80e3`'s row made a `skip` | killed |

## K.9 candidates spotted outside this wave's scope

- **K1** `35a8563`, `26a334a` (subjects), `.claude/skills/pre-merge/SKILL.md`. **A subject that begins `fix:
  #N` closes issue N when it reaches `main`, because GitHub reads `fix:` followed by `#N` as a closing
  keyword.** This project writes taken-out and partial fixes that way, and that is how #194 and #222 closed
  (M5). Enhancement: before the owner merges a pull request, `/pre-merge` could list the issues its commits
  would close; or the subject form could keep `#N` away from `fix:`. Missed-bar issues would then stay open.

## Risks queued to next M

- **R1** `.claude/settings.json:40,51`, `docs/security-invariants.md:192` (G-7). **`-I` still runs the
  site-packages `.pth` files and `sitecustomize` of the interpreter it finds on `PATH`. G-7 calls those "the
  machine's", which holds only while that interpreter is not the project's `.venv`.**
  - On this machine the hooks find `/opt/homebrew/bin/python3`.
  - A session whose `PATH` puts `.venv/bin` first would take both the interpreter and its site-packages from
    the work tree, which `make install` and the Write tool reach.
  - **What would show it is real:** `command -v python3`, in a hook's environment, resolving into a work tree.
  - **Mitigation to weigh** (OWNER APPROVAL): add `-S` beside `-I` in both hooks. The guard imports only the
    standard library. Under `-I -S` it allowed `git status`, refused a redirect into `.githooks/` and refused a
    Write into `.claude/` (measured).

## Dispositions, at the closure

| finding | disposition |
|---|---|
| M1 | fixed `00d6bbc` (red `7db7553`; OWNER APPROVAL) and `f8e2d25`; a `.git` made inside `.claude/` is #256 |
| M2 | fixed `00d6bbc` (red `7db7553`) |
| M3 | fixed `92799ea` (red `7c73c2a`): the records give the fixture's reason; `swift-build-tests` keeps its status |
| M4 | fixed `f3cf507` (red `c99d4f5`) |
| M5 | #194 and #222 reopened, #187's closing explained on the issue; the roadmap lists them as open |
| M6 | fixed `f8e2d25` (red `c0a1e27`) |
| M7 | held by `7db7553` (the guard's cases) and `131ddf1` (the gate's cases, which pass as delivered) |
| K1 | #255 |
| R1 | fixed `00d6bbc` (red `7db7553`; OWNER APPROVAL): every hook python runs with `-I -S` |
