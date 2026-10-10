---
record_type: review
id: m21-closure-fixes-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 closure fixes -- code review

**Reviewer:** Code-Reviewer seat, a fresh session that wrote none of the range (author family: Claude Code,
`GP-Agent: claude-code/local-lane`; reviewer family: the same, no second family on this machine)
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `origin/wave/m21-w4..80f42a9` (24 commits, 36 files)
**Risk tier:** HIGH

## Verdict
BLOCKING

One BLOCKING finding: the pre-commit hook the owner's ruling installs refuses every red-test commit that
`/fix-issue` and the red-to-green rule require. Seven MINOR findings: the docs-only reading, R-1's premise,
the ledger's `review` kind and its dates, row 9's `Bypass:` matching, the plan's `**Base:**` line, the
guard's write blocks and pin, and the records. Most of the range is sound. M4, S5, S6, the M5 moves, the
version bump and most of the records do what their findings asked.

## What I read and ran

- I read each of the 24 commits with `git show`, against `docs/reviews/m21-repo-review.md` (M1 to M11),
  `docs/reviews/m21-closure-security-review.md` (S1 to S8) and the owner's ruling as the ledger records it.
- **Tests run:**
  - pytest on `test_commit_gate.py`, `test_wave_check_m21_rules.py`, `test_claude_code_version.py`,
    `test_error_codes.py`, `test_bash_guard_bounds.py`, `test_security_invariants.py` and
    `test_adr_citations.py`: 95 passed. The run exits 1, but only on the coverage floor of a partial run.
  - `conformance/test-hook-claims.py`: PASS (2 claims, 18 legs).
  - `scripts/client_decl_gate.py` (`make client-decls`), run once: PASS, 21 files in 4 configurations
    (2799 and 2804 declarations), 55 s.
  - `scripts/wave_check_all.py`: PASS, 68 records. `scripts/check_records.py`: PASS.
- **Not run:**
  - `test_data_release_stamp.py` and `test_deploy_hosted.py`, because they run the deploy script.
  - The Swift suites, and `make check-fast` or `make check`. The Swift side of M4 is judged from its code
    and from `test_error_codes.py`.
- **Probes.** None changed a tracked file.
  - The real `.githooks/pre-commit` and `scripts/commit_gate.py`, copied into a scratch repository with a
    recording `make` stub, as `test_commit_gate.py` does.
  - `wave_check` functions, run in process on crafted ledgers and closes.
  - The module's own git fixtures, for M2.
  - The Write hook and the guard, fed payloads through their entries. Only ordinary paths were used, and
    no evasion payload was built.
  - A timer-thread check outside the guard.
- **Faults planted.** One at a time, each restored by its bytes and checked by sha256 (table below).
  `git status` is clean apart from this file.
- **Side effect.** `test_bash_guard_bounds.py` starts the guard in a subprocess that writes bytecode. My run
  therefore created `.claude/hooks/__pycache__/bash_guard.cpython-314.pyc`, which git ignores. I left it
  there, because this seat does not edit `.claude/`.

## Findings

### BLOCKING

- **B1** `.githooks/pre-commit:17-26`, `scripts/commit_gate.py:31-33`, `.claude/skills/fix-issue/SKILL.md:12-17`,
  `docs/control-events.csv:31`, `docs/refusals.md:27`. **The pre-commit hook refuses every red-test commit,
  and an agent has no in-rule way past it.**
  - **What is wrong.**
    - Every commit that is not docs-only runs `make check-fast`, and the hook refuses the commit when that
      is red. A red-test commit is red by design.
    - `/fix-issue` step 3 says "Reproduce with a test first, and commit it alone": the test fails, and the
      fix comes after. Step 4 says "never `--no-verify`". AGENTS.md:54 makes red-to-green a gate.
    - Nothing decides this case: not the ruling (`control-events.csv:35`), not R-1, not the hook, not
      `commit_gate.py`.
  - **The ledger contradicts itself on this class.**
    - The closure records M20's `3c5954f`, a red-test commit, as a `bypass`, "which a red commit cannot
      pass" (`:31`).
    - It records none of M21's 49 `test: ..., red` commits, and none of this range's 7. Six of those 7 came
      after the ruling at `d912a76` (11:16): `0003573`, `df3a32e`, `facac24`, `1768cb5`, `5575a0a` and
      `efc0790`.
    - By the closure's own reading, the control reached three rows again within the hour the ruling reset
      it.
  - **Failure scenario.**
    - The owner runs `make hooks`, as the runbook's v2 step 2 says. The next `/fix-issue` writes its
      reproducing test and commits it. `check-fast` is red, so the hook refuses.
    - `--no-verify` is forbidden to the agent, and no Bash guard rule reads it.
    - There are two ways out within the rules, and both lose what the rule protects:
      - Write the fix first, and commit the test while the fix sits unstaged. The hook gates the working
        tree, not the commit, so the "red" commit was never red.
      - Commit the test and the fix together. That loses the order the Tester checks (`SKILL.md:26`).
  - **Fix.**
    - Decide red commits before `make hooks` is run. One way: a test-only commit (every staged path under
      `tests/` or `ios/EngineTests/`) runs the other legs and `check-records`, and passes the test leg only
      when its failures are in the staged tests. Another way: the owner rules red-test commits within scope
      in R-1, and the hook names that path.
    - Then make the ledger consistent. Either `3c5954f`'s row is `within-scope` too, or this range's seven
      red commits get rows.

### MINOR

- **M1** `scripts/commit_gate.py:40`, `:27-28`, `.githooks/pre-commit:17`. **A rename hides a code path from the
  docs-only rule, and the gate judges a commit that changes the gate itself.**
  - **What is wrong.**
    - `git diff --cached --name-only` detects renames by default and prints only the new name.
    - Measured through the copied hook: `git mv tests/unit/test_x.py docs/test_x.md` was committed after
      only `make check-records`.
    - The hook runs `scripts/commit_gate.py` from the working tree. So a commit that changes the gate is
      judged by the changed gate.
  - **Failure scenario.** A module or a failing test is moved out of `src/` or `tests/` as `docs/*.md`.
    `check-records` passes, the next code commit's `check-fast` is red, and no ledger row records it.
  - **Fix.**
    - Add `--no-renames`, so that both paths are listed.
    - Decide from `HEAD`'s copy of the gate (`git show HEAD:scripts/commit_gate.py`), or send any commit
      that stages it to `check-fast`.
    - Add a rename case and a no-`make` case to `test_commit_gate.py`.
  - **The fail-closed paths hold today.** With no `make` on PATH, the copied hook refused the commit (exit 1,
    no HEAD made). It said "make check-fast failed above", not that `make` was missing.

- **M2** `docs/refusals.md:27` (R-1), `scripts/commit_gate.py:9-11`. **R-1's reason is not true: `check-fast`
  legs read the Markdown that a docs-only commit gates with `check-records` alone.**
  - **What R-1 says.** The narrowing is for "text no leg reads but `check-records`".
  - **What reads that Markdown:**
    - `conformance/test-agents-cap.py` (AGENTS.md);
    - `test_claude_code_version.py` (INSTALL.md and G-7);
    - `test_security_invariants.py`, `test_prd_citations.py` and `test_adr_citations.py`;
    - `wave-check-all` and `wave_check.py` (the plans' globs and `**Base:**`, the closes);
    - `install-check` (INSTALL-MANIFEST.md).
  - **Measured.** Two docs edits were planted and restored by sha256: INSTALL.md's 2.1.295 changed to
    2.1.296, and AGENTS.md's cap changed from 150 to 100. For each, `commit_gate.target` printed
    `check-records` and `check_records.py` passed, while the `check-fast` leg failed.
  - **In this range.** `70eb084` changed the globs that `wave_check` reads from `docs/plans/m21-plan.md`,
    gated as docs-only.
  - **Failure scenario.** A docs commit breaks one of these legs and lands green. The next code commit's
    `check-fast` is then red for a reason its diff does not hold.
  - **Fix.**
    - Gate docs-only commits with `check-records` plus the legs that read Markdown. Or narrow docs-only to
      paths no leg reads.
    - Correct R-1's reason, so the owner's ruling rests on what is true.

- **M3** `scripts/wave_check.py:576-590` (`ledger_strikes`), `docs/control-events.csv:10`, `:36`. **A `review` row,
  or any future-dated row that resets the count, keeps a control green with no owner, and the closure used one on
  a control the owner did not rule on.**
  - **What is wrong.**
    - A `review` resets the count as an owner `ruling` does. It needs no owner's name and no refusal or ADR,
      and nothing limits how often it is written. So each third row can be answered with another review.
    - The date is free text, compared as a string. Measured: after a review row dated 2099-01-01, ten bypass
      rows strike nothing. Nothing checks a ledger date.
  - **The `repository-hooks` review is not a fair use** (`:36`).
    - It is the closure reviewing its own control. It was written in the commit that created the kind.
    - Its "fix in hand", `make hooks`, is the owner's step, and it is not taken (G-10).
    - That step does not reach the failure the three rows record. The Claude Code hooks (the guard, the
      Write refusal, the post-edit check) still load only in a session started in the repository (#142).
  - **Failure scenario.** M22's sessions start outside the repository, as M19's to M21's did. Two skips pass
    silently. At the third, the next closure writes another review. The control never reaches the owner.
  - **Fix.**
    - Only an owner's `ruling` resets the count, and it cites a `refusals.md` row or an ADR naming the owner.
      Record a `review` row, but count nothing from it.
    - Refuse a date that is not ISO, or that is later than the commit adding it.
    - Put `repository-hooks` before the owner.

- **M4** `scripts/wave_check.py:632-638`, `docs/control-events.csv:11`, `:33-34`. **Row 9's `Bypass:` is satisfied
  by any row of the wave naming any control the field mentions, and a `within-scope` row is never checked.**
  - **Measured in process.**
    - Take a `Bypass:` that names a code commit and `commit-after-check-fast`. It passes with only a
      `within-scope` row.
    - It also passes with no row for that control at all, when the field names `security-pass` and the
      milestone has a row for that. Every M21 close carries such rows.
    - The match is also case-sensitive, unlike row 9's other checks.
  - **What is honest.** Both M21 `within-scope` rows are: `commit_gate.target` gives `check-records` for
    `9613a2b` and `9cf8e12`.
  - **Mutants that survive `test_wave_check_m21_rules.py`:**
    - X4: the control match removed;
    - X5: `within-scope` resets the count like a ruling.
  - **Failure scenario.** A code commit made without `check-fast` is written as `within-scope`. The close
    passes, and the three-row rule never counts it. That is the repo review's M1 again, through the new kind.
  - **Fix.**
    - For each SHA the field names, require a row whose reason names that SHA: `bypass`, or `within-scope`
      only when `wave_check` confirms that SHA is docs-only by `commit_gate.target` (with `--no-renames`).
    - Add tests for both.

- **M5** `scripts/wave_check.py:405-410`, `:489-494`. **The plan's `**Base:**` line (M2's fix) lets a docs-only
  edit narrow a wave's range, and it reaches git unvalidated.**
  - **What is wrong.**
    - The latest candidate wins, and the plan's ref may be any text.
    - The ref is passed as an argument to `git merge-base`. The security seat's PASS said a record reaches git
      only inside `rev-parse --verify <x>^{commit}`.
  - **Measured with the module's own fixtures.**
    - A MED close whose range starts after a security-glob change is refused (#183).
    - Add one `**Base:**` line to the plan naming that start. It is a docs-only commit, gated by
      `check-records`. The same close then passes with no problem.
    - Mutant X6, with the line not read, survives.
  - **Failure scenario.** A wave's close reads only the tail of its range, past a glob change or an ADR that
    sits beside code, and closes MEDIUM.
  - **Fix.**
    - Drop the line: the closure-branch candidate covers M2, and X7 shows it is held.
    - Or accept the line only through `rev-parse --verify`, and only as an earlier base, never a later one.
      Add a planted test.

- **M6** `.claude/settings.json:40`, `:51`, `.claude/hooks/bash_guard.py:68`, `:607-624`, `:31-33`, `:716`,
  `tests/unit/test_bash_guard_bounds.py:5`, `docs/security-invariants.md:192` (G-7). **The write refusals take any
  `.claude` directory, hold none of case, links or option destinations, and the pin and the timer hold less than
  they claim.**
  - **It refuses too much.** Measured through the entries:
    - a Write to `/Users/someone/.claude/projects/.../memory/MEMORY.md` exits 2;
    - the guard blocks `mkdir -p ~/.claude/plans` and `cp notes.md "$HOME/.claude/CLAUDE.md"`.

    `~/.claude/` is Claude Code's default user-level directory.
  - **It holds too little.** Read from the code, with no payload built:
    - both checks compare the literal path, case-sensitively, and resolve no link, while macOS volumes are
      case-insensitive by default;
    - for `cp`, `ln`, `install`, `rsync`, `dd` and `ditto`, only the last word that is not an option is read
      as the destination;
    - G-7 names only "a program it does not list".
  - **The pin holds the guard's bytes, not its imports.** `"$py" "$g"` puts `.claude/hooks/` first on
    `sys.path`. A module beside the guard named `json`, `re`, `os` or `threading` changes what it does, and its
    sha256 does not change.
  - **The owner's edit flow is written nowhere but in the BLOCKED line.** A changed guard needs its new sha256
    in `settings.json` and a new session, because a running session keeps its snapshot. A session that is open
    when the owner pulls the v2 merges blocks every Bash call.
  - **The C-call claim is not true.** A 0.2 s `threading.Timer` that calls `os._exit(2)` fired at 3.83 s,
    when a 3.8 s regex returned. The guard and the test say it stops such a call. The test uses `time.sleep`,
    which releases the GIL.
  - **Failure scenario.**
    - An agent in a repository session is refused its own memory file.
    - A `.githooks/` write in another case, or through a link, changes the gates the ruling relies on.
    - Below Claude Code 2.1.295, a guard stuck in C is not bounded at 5 s.
  - **Fix.**
    - Compare the resolved, case-folded path with `$CLAUDE_PROJECT_DIR/.claude/` and `.githooks/`.
    - Read destinations given as options.
    - Run the guard with `python -I`, and refuse when `.claude/hooks/` holds any other file.
    - Document the re-pin flow in INSTALL.md and G-7.
    - Correct the C-call claim, or bound the reading in a child process.

- **M7** `AGENTS.md:105`, `:107`, `docs/control-events.csv:4`, `docs/plans/m21-plan.md:88`,
  `scripts/wave_check.py:502-503`. **The records do not name the pre-commit gate or the write refusal, and M3's
  globs went into a plan no later wave reads.**
  - **What is wrong.**
    - AGENTS.md lets a human bypass only "the pre-push gate". The hooks paragraph names neither the pre-commit
      gate nor the `.claude/` and `.githooks/` refusal.
    - The ledger header names only `git push --no-verify`, although the hook asks for a row after a
      `git commit --no-verify`.
    - `plan_globs` reads only the wave's own milestone plan. So M3's globs apply to M21 after the fact, and
      lapse at M22.
  - **Failure scenario.** M22's plan lists its own globs without the gates. A wave that weakens
    `client_decl_gate.py` then closes MEDIUM.
  - **Fix.**
    - Name both controls in AGENTS.md and in the ledger header.
    - Keep the gates' globs in a standing list that `plan_globs` always adds, or derive them from the
      invariant rows.

### PASS (what looks good)

- **M4.** The `unexpected` case at `Language.swift:832-835` takes the status. `test_error_codes.py` reads the
  phone's own codes from `EngineClient.swift`. Mutant X10 is killed.
- **S6.**
  - `ObjectiveC` is off both lists (`MODULES` at `client_decl_gate.py:92`, `SINK_MODULES` at `:832`). The fixture calls `sel_registerName`,
    and the committed dump expects both refusals.
  - `make client-decls` passes on the shipping client. Mutant X9 is killed.
  - G-12 names `@_silgen_name` as held by the text pin alone.
- **M5 moves.** I checked the 15 moved pointers: each now sits above its own ADR's closing `---`. Mutant X8
  (the placement rule off) is killed.
- **S5 and INV-90.**
  - A missing or unreadable record is refused at `deploy_hosted_engine.sh:79-83`. It is also refused by the
    name check at `:86`, so two independent checks hold it.
  - The hint names only `release-*` or `unknown`.
  - INV-90 lists the nine tests. I did not run them, since they run the deploy script.
- **The ledger rule.** The CSV parse and the rule counting only rows after a ruling hold (X3 killed). M2's
  closure-branch candidate is held (X7 killed).
- **The version.** 0.2.0 and build 4 are set in all four configurations (`project.pbxproj:239-298`).
- **The runbook's v2 order** is right for the owner, apart from B1's effect at step 2:
  - merge;
  - `make hooks` and `/hooks`;
  - `make check` on `main`;
  - a refresh that publishes, then the deploy;
  - `refined_board`, then `Fly-Client-IP`;
  - build 4, then the habits.

  Each step names its condition, and the first night under the new release publishes, because D-190 changes
  the data.
- **Other records.** INSTALL.md, G-10, the PRD caveat (M11) and the architecture bullet (M9) are accurate.
  The files the bullet names exist, and `test_model_families.py` holds them.

## Hardened-invariant producers

| Producer | Citing tests | Gaps |
|---|---|---|
| **INV-82:** the Bash hook's text reading, `bash_guard.py`, the sha256 pin, and the Write/Edit hook | `conformance/test-hook-claims.py` (8 new must-block cases, 4 must-allow, a changed byte, an exit-1 stub, 3 Write paths); `test_bash_guard_bounds.py` (2) | M6 |
| **INV-90:** `deploy_hosted_engine.sh:79-95` | `test_data_release_stamp.py` and `test_deploy_hosted.py` (9; not run here) | none found |
| **The new commit control:** `commit_gate.py` and `pre-commit` | `test_commit_gate.py` (17) | B1, M1 |

## Planted faults

| # | Fault | Result |
|---|---|---|
| X1 | docs-only ignores the code directories | killed (7 cases) |
| X2 | the gate reads the worktree, not the index | killed |
| X3 | rows after a ruling never count | killed |
| X4 | `Bypass:` satisfied by any row of the wave, whatever control it names | **survived** (M4) |
| X5 | a `within-scope` row resets the count like a ruling | **survived** (M4) |
| X6 | the plan's `**Base:**` not read | **survived** (M5) |
| X7 | the previous closure branch not read | killed |
| X8 | A1's placement rule off | killed |
| X9 | `ObjectiveC` back on `SINK_MODULES` | killed |
| X10 | the `unexpected` sentence dropped | killed |

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/check_records.py:1562-1571`, `docs/decisions.md:1602`, `:2660`. **A1 checks pointers in one
  direction only.**
  - **What it checks.** An `Amends` field must have a pointer in its target. It does not check the reverse:
    that a pointer's source names the ADR the pointer sits in.
  - **What that misses.** Two pointers fail the reverse check:
    - "Amended by D-176" sits in D-136, and D-176 has no `Amends` field;
    - "Amended by D-179" sits in D-156, and D-179 amends D-159, D-164 and D-173.
  - **Kind.** A bug of record drift: a reader takes D-136 and D-156 as formally amended. The reverse check
    is an enhancement.

## Risks queued to next M

- **R1** The protections this range adds under `.claude/` work only where the Claude Code hooks load: in a
  session started in the repository (#142). `onFailure` is still unverified (S8), and `make hooks` is not
  yet run on the owner's clone. The owner's `/hooks` check (runbook v2, step 2) and the next close's row 8
  would show whether this risk is real.

## Dispositions, at the closure

| finding | disposition |
|---|---|
| B1 | fixed `85f80e3` (red `e8d8ee1`) and `a024244` (OWNER APPROVAL): a commit-msg hook gates a declared red test commit by `make check-red`; row 31 is `within-scope` (`85f80e3`) |
| M1 | fixed `85f80e3` (red `e8d8ee1`): `--no-renames`, HEAD's copy of the gate, "make not found" |
| M2 | fixed `85f80e3` (red `e8d8ee1`): a docs-only commit runs `make check-docs`, every leg but the Swift ones; R-1 corrected |
| M3 | fixed `0b49f18` (red `a1c1724`): only an owner's ruling resets a count; dates checked; the owner's `repository-hooks` ruling is a row |
| M4 | fixed `e8ff620` (red `1773fb4`) |
| M5 | fixed `17a2a0b` (red `184a2c6`): the plan's `**Base:**` line is not read |
| M6 | fixed `cd563f5`, `42b62aa` (OWNER APPROVAL; red `34e667d`) and `1dd80e6`; `cd563f5` is a ledger bypass row (`e877168`) |
| M7 | fixed `048e59f` (red `83d9a3d`) |
| K1 | #253 |
| R1 | the owner's ruling on `repository-hooks` (sessions start in the repository) and the runbook's v2 step 2 (`make hooks`, `/hooks`) |
