---
record_type: review
id: m21-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 4 Tester Review (the controls)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code and none of its three review rounds)
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `origin/wave/m21-w3..f2b7d35` (`6a41d35..f2b7d35`, 39 commits, no merges). The worktree is
detached at `f2b7d35`.
**Risk tier:** HIGH (plan §2, `docs/plans/m21-plan.md:66`; the range changes `.claude/settings.json`)

Routing: the author and this seat are both Claude; no second family was available. The context is fresh.
This seat read D-192, the three review rounds, the commits, and the code and tests they touch. Its rules
came from the base, not from the diff. It read no `*_heldout_*` file.

## Verdict
MINOR

- The wave's tests pass, `make check-fast` passes, and `conformance/test-hook-claims.py` passes.
- Every red commit that this seat could run fails only on its own tests.
- `wave_check_all` passes on the real tree, and each close from M19-W1 to M21-W3 passes on its own.
- The four OWNER APPROVAL commits (`c3b8b9a`, `64b862a`, `36e74fa`, `bd55823`) hold only `.claude/` files.
  No other commit in the range touches `.claude/`, `.githooks/` or `.github/`.
- Of 21 planted faults, the wave's tests and the conformance file catch 10. This seat added 6 tests, 12
  conformance cases, and a text-only run of 29 existing cases. They pass on the shipped code and catch 10
  more. The last plant is an equivalent mutant (WD2).
- One real defect, M1. A merged close that a later branch edits is read again over the later wave's
  commits, and it fails falsely. The other findings are test gaps (closed here), test integrity, and a
  harness that crashes on a hung hook.
- Nothing blocks. Each issue in the wave has a test that asserts its behaviour. No test was weakened or
  deleted: the 16 renamed tests (#248) keep their bodies, byte for byte. Only #178's test changed its
  timing, and `match="deadline"` still tells a deadline apart from a hang-up.

## Findings

### BLOCKING
None

### MINOR

- **M1** `scripts/wave_check.py:461-462`, `:423`; `docs/decisions.md:4725`. Since round 3's M1, the range
  ends at the last commit that changes the close. A close counts as merged only when that same commit is on
  main. So when a later branch edits a merged close, the close is unmerged again, and its range grows to
  take in the later wave's commits.
  - **Failure (reproduced in a scratch repository with the test file's own helpers).**
    1. W1's MED close is committed and fast-forwarded into main.
    2. W2 branches from main and changes `src/app/adapter/main.py`, a glob.
    3. On W2's branch, a typo in W1's close is fixed.
    4. `history_problems` on W1's close now returns the HIGH-rule problem for W2's glob change.
    - Before step 3 it said SKIPPED (merged).
    - The same path would pin the closure's own ADRs on an earlier close.
  - **Why it will be hit.** The M19 closure did exactly this: `b5725db` edited `m19-wave-5-close.md` on
    `enhancement/m19-closure`. M21-W3's close and W4's close are dated inside the rules, so an M21 closure
    edit to either one would fail `make check` on the closure branch.
  - **Also.** The docstring at `:423` still says the end is "pinned to the commit that added the close".
  - **Fix.**
    1. Ask "merged" of the commit that added the close: `own = added[-1].split()[0] if added else None`.
       This seat ran that change in a scratch copy. All 75 tests in the three wave-check test files pass,
       round 3's M1 and M4 tests among them, and the reproduction above says SKIPPED.
    2. Say so in D-192 clause 2 and in the docstring.
    3. Add the reproduction as a test. It is not added here, because it fails on the shipped code.

- **M2** `scripts/wave_check.py:449-450`, `:516`, `:527`, `:587-588`; `scripts/check_records.py:1568`;
  `tests/unit/test_security_invariants.py:701`. Six clauses of D-192 that the code holds had no test. With
  each one broken, every test stayed green (plants WC1 to WC4, CR1, P1):
  - the process-log heading's date (clause 2, #203);
  - the range ending at HEAD while the close has edits not yet committed (clause 2);
  - "after no code commit of the range that cites it" for a plan-named ADR (#201);
  - row 8 giving both answers (clause 3);
  - the pointer back naming the ADR that amends (clause 1, #200);
  - #248's phrase check accepting a pointer to any row.

  **Failure.** Each plant above shipped green.

  **Fix (done in this review).** Each now has a test that fails with its plant and passes on the shipped
  code:
  - `tests/unit/test_wave_check_m21_rules.py:642`, `:654`, `:667`, `:682`, `:693`;
  - `tests/unit/test_security_invariants.py:732`.

- **M3** `.claude/hooks/bash_guard.py:75`, `:574-575`, `:602`; `.claude/settings.json:51`. The guard
  claims four things that no conformance case held. With each one broken, `conformance/test-hook-claims.py`
  passed:
  - `rm` given its long options (`--recursive --force`): plant G2;
  - `rm` behind a wrapper with split options: plant G8;
  - a shell given `-s` while it reads a pipe: plant G7;
  - the text reading itself (plant G9). Every one of the 137 MUST_BLOCK cases is blocked by the second
    reading alone, so deleting the text reading from the hook left the file green. The docstring and G-7
    describe the text reading as running first, unchanged.

  The fail-closed paths (an unclosed quote, substitution, backtick or `${`) and the allow paths of a
  harmless `bash -c`, a harmless shell here-document and a `case` also had no case.

  **Fix (done in this review)** in `conformance/test-hook-claims.py`:
  - **MUST_BLOCK** gains 9 ordinary spellings (`:361-366`): `rm -r -f`, `rm --recursive --force`,
    `sudo rm -r -f`, `cat setup.sh | bash -s -- --quiet`, and five unclosed forms.
  - **MUST_ALLOW** gains 3 (`:395-396`).
  - **A text-only run** (`:431-440`): each pre-#189 MUST_BLOCK case runs again with a second reading that
    allows everything, and must still block.

  G2, G7, G8 and G9 now fail the file. It passes on the shipped hook, and line and branch coverage of
  `bash_guard.py` by the file's own cases rose from 86% to 89%. No new evasion form was written (see "The
  guard" below).

- **M4** `tests/unit/test_wave_check_m21_rules.py:638` (at `f2b7d35`). `pytestmark = pytest.mark.needs("git")`
  marks all 42 tests as needing a git checkout of this repository.
  - What they really need:
    - 15 need no git at all: the #200 tests and the ledger tests;
    - the other 27 build their own repository, so they need only the git binary.
  - #249's own rule says such a test "runs in an extracted tree" (`tests/unit/test_needs_git.py:19`).
  - **Failure.** The red commit `a1283b9`, built from `git archive` as #249 describes, reports "14 skipped"
    and 0 failed. A seat checking red→green there sees nothing red. This seat had to add a git index and a
    commit to see the 14 failures.
  - **Fix.**
    1. Drop the module mark.
    2. Mark nothing on the 15 that need no git.
    3. For the 27, add a need for the git binary alone (`shutil.which("git")`, `in_ci` True), or let them
       run unmarked, since every host that runs the suite has git.

- **M5** `conformance/test-hook-claims.py:146`. `run_hook` calls `subprocess.run([bash, "-c", ...],
  timeout=60)`.
  - **Failure.** A hook that does not answer raises `TimeoutExpired` out of `main()`, so the file prints no
    FAIL list and no verdict line, only a traceback with exit 1. The guard's Python process outlives the
    killed `bash`.
  - **Measured.** At the red commit `ac4a0c8`, the brace-word case (round 2's M3) did exactly this. The
    file exited 1 with an empty stdout, so it hid the commit's other red cases. It left `bash_guard.py`
    running under PID 1, at 1.6 GB after 90 s. This seat stopped it with SIGKILL.
  - The shipped guard answers within its bound, so this bites only when the guard regresses, which is when
    the file is needed most.
  - **Fix.**
    1. Run the hook in a session of its own (`start_new_session=True` where the OS has it).
    2. On a timeout, kill the group and return a non-0/2 result, which the loop already reports as a
       failure with its label.

- **M6** `tests/unit/test_wave_check_m21_rules.py:80`.
  `assert not any("D-3" in m and "D-2 clause" in m for m in found)` cannot fail. No A1 message contains
  "clause": they read "D-n amends D-m, and ...". The `**applies**` case is held, but by the next test's
  `== []`, not by this line.
  - **Failure.** A reader takes this line for the `applies` guard. It is coverage theatre, and on a HIGH
    wave that is the pattern this seat is asked to flag.
  - **Fix.** Assert `not any(m.startswith("D-2 amends D-3,") for m in found)`. The new test at `:693`
    carries that assertion, so the line can be replaced or deleted.

## K.9 candidates spotted outside this wave's scope

- **K1** `docs/plans/m21-plan.md:86`. The security globs name `.claude/settings.json` but not
  `.claude/hooks/**` or `.githooks/**`.
  - **Failure.** The Bash hook now hands every command to `.claude/hooks/bash_guard.py`. A later wave that
    changes only that file, a weakening included, is not HIGH under #183's rule, and a MED close passes.
    This wave is HIGH only because it also changed `settings.json`.
  - **Fix.** The next plan's globs add `.claude/hooks/**` and `.githooks/**`. Or the template's default
    globs carry them.

## Risks queued to next M

- **R1** `ios/UITests/ScrollStep.swift`; `ios/EngineTests/OfflineTestCase.swift:131`. Two Swift red tests
  were not run red by this seat:
  - `0f20968` (#227, `bringIntoView`), because `make ui-test` and the simulator are out of bounds;
  - `17d023f`'s Swift half, because outside the profile its child would open a UDP socket.

  Both fixes were run green: the Engine suite ran 606 tests inside the offline profile in `make
  check-fast`, the new child test among them. `ScrollStep.swift` was not run at all here.
  - **What would show it is real:** the owner's next `make ui-test` failing or flaking on the coding
    screen's scroll.
  - **Fix:** the owner runs `make ui-test` once before the merge.

## How it was checked

- **The wave's tests.** 14 files, every one the range touches: 357 passed and 2 skipped (the two `offline`
  needs), in 19 s.
- **`make check-fast`, once.**
  - PASS in 107.8 s on 6 legs;
  - pytest: 2504 passed and 25 skipped;
  - Swift: 606 tests, plus SlowTierTests on a one-thread pool, 7 of 7;
  - client-decls: PASS.
- **`conformance/test-hook-claims.py`.** PASS before and after this seat's cases. `conformance/run-all.py`:
  PASS, 16 tests.
- **The real tree.**
  - `scripts/wave_check_all.py`: PASS, 67 records.
  - For each close from M19-W1 to M21-W3 (13 closes), these all pass:
    - `wave_check.main` passes;
    - `history_problems` returns `([], None)`;
    - `skip_ledger_problems` returns `[]`.
  - A W4 close drafted over `origin/wave/m21-w3...HEAD` passes as HIGH. As MED it is refused for
    `.claude/settings.json`.
- **Plants.**
  - Where they ran: in a scratch copy of the tree built from `git archive f2b7d35`, with a git index, so
    `.claude/` in the worktree was never touched.
  - How: one plant at a time. Each was an exact string replacement, checked to occur once.
  - The restore: by bytes, then the sha256 compared with the value from before the plant. All 21 restores
    matched. The scratch copy's six planted files are byte-identical to `f2b7d35`.
  - What ran:
    - gate plants: the five wave-check test files, or the plant's own test file;
    - guard plants: the whole conformance file, through the hook command.
- **Red commits.**
  - **Build.** Each was built from `git archive <sha>` into its own folder, with `git init -b main`, an
    index and one commit, so `needs("git")` tests ran.
  - **Run.**
    - pytest: the whole suite, `-n 8`, no artifact (79 skipped);
    - the hook claims: for the three commits that changed the conformance file.
  - **Check.** Each failure was matched to the test functions or cases that the commit's own diff adds or
    changes.

## Red→green on the red commits

| commit | suite | failed | all its own? |
|---|---|---|---|
| `a1283b9` | pytest | 14: every test it adds | yes |
| `fe3a27d` | pytest | 1: `test_every_test_that_runs_git_says_it_needs_git` | yes |
| `a6d2932` | pytest | 9: every test in `test_ci_needs.py` | yes |
| `116b371` | pytest | 1: `test_without_a_deadline_of_its_own_a_fetch_takes_four_timeouts_at_most`, which it changes | yes |
| `17d023f` | pytest | 2: both cases of `test_both_swift_legs_run_inside_the_offline_profile_on_macos` | yes; its Swift half not run (R1) |
| `0355ec7` | pytest | 2: both cases of the one-thread-pool test | yes |
| `c0fac4c` | pytest | 2: the two #248 tests | yes |
| `0f20968` | UI test | not run (`make ui-test` is out of bounds) | R1 |
| `1b20129` | hook claims | 36: its 35 new MUST_BLOCK cases and "second reading missing" | yes |
| `b920e9a` | pytest | 1: the merged-close test it adds | yes |
| `f3df6ea` | hook claims | 40: 33 of its MUST_BLOCK cases, 7 of its MUST_ALLOW cases | yes |
| `1702041` | pytest | 18: its 13 new tests, the session test it rewrites, and its 4 watchdog tests | yes |
| `ac4a0c8` | hook claims | crashed after 60 s on its brace-word case, with no list (M5) | its own case, but the rest is hidden |
| `26b6510` | pytest | 8: its 6 wave-check tests and 2 watchdog tests | yes |
| `26b6510` | hook claims | 0: its 2 cases pin `36e74fa`, which came first; plant G6 turns them red | n/a |
| `a804582` | pytest | 4: every test it adds | yes |

## Faults planted

"Wave" is the result with the shipped tests. "Now" adds this seat's tests and cases.

| # | where | the fault | wave | now |
|---|---|---|---|---|
| WC1 | `wave_check.py:527` | the process-log heading's date is not compared with the range | **green** | RED, `:642` (M2) |
| WC2 | `wave_check.py:449-450` | a close with uncommitted edits ends at its last commit, not HEAD | **green** | RED, `:654` (M2) |
| WC3 | `wave_check.py:516` | a plan-named ADR after a code commit that cites it passes | **green** | RED, `:667` (M2) |
| WC4 | `wave_check.py:587` | row 8 giving both `yes` and `no` is not refused | **green** | RED, `:682` (M2) |
| WC5 | `wave_check.py:579` | a skipped row is ledgered by any text in it (round 3's M2 undone) | RED, `test_a_skipped_row_is_ledgered_by_its_check_cell_only` | RED |
| WC6 | `wave_check.py:414` | a span `M30-W1 to W2` names only its first wave | RED, `test_a_stacked_range_from_the_previous_close_is_the_waves_base` | RED |
| WC7 | `wave_check.py:359` | `.claude/` and `.githooks/` are not code for #201 (round 3's M3 undone) | RED, `test_a_hook_committed_before_its_adr_is_refused` | RED |
| CR1 | `check_records.py:1568` | any `**Amended by` line counts as the pointer back | **green** | RED, `:693` (M2) |
| WD1 | `watchdog.py:42` | the watchdog lists only the command, not its descendants | RED, the grandchild and Ctrl-C tests | RED |
| WD2 | `watchdog.py:51` | SIGKILL goes to the groups only, not to each listed pid | **green** | **green**: an equivalent mutant (below) |
| CI1 | `tests/skips.py:107` (`ci_job_facts`) | the `offline` fact misses `unshare --net` | RED, `[offline-patch]` | RED |
| P1 | `test_security_invariants.py:701` | a record naming any `INV-n` answers every phrase | **green** | RED, `:732` (M2) |
| G1 | `bash_guard.py:75` | `fly` removed from GUARDED | RED, 6+ cases (`env fly deploy` among them) | RED |
| G2 | `bash_guard.py:574-575` | `rm`'s long options not read | **green** | RED, `rm --recursive --force build` (M3) |
| G3 | `bash_guard.py:265` | every here-document body read as quoted | RED, 5 round-2 B1 cases | RED |
| G4 | `bash_guard.py:265` | every here-document body read as unquoted | RED, 3 MUST_ALLOW cases | RED |
| G5 | `bash_guard.py:455` | the size bound removed | RED, the 32 769-character case | RED |
| G6 | `bash_guard.py:534` | a shell fed by a pipe or a file is allowed | RED, 6 stdin-shell cases | RED |
| G7 | `bash_guard.py:602` | a shell's `-s` not read | **green** | RED, `cat setup.sh \| bash -s -- --quiet` (M3) |
| G8 | `bash_guard.py:75` | `rm` removed from GUARDED (not read behind a wrapper) | **green** | RED, `sudo rm -r -f build` (M3) |
| G9 | `settings.json:51` | the hook's text reading removed, leaving only the second reading | **green** | RED, 29 "by the text reading alone" cases (M3) |

Counts: the wave's tests catch 10 of 21, and 20 of 21 with this seat's additions.

**WD2 is an equivalent mutant.** The watchdog starts the command with `start_new_session=True`. No
descendant can then join the watchdog's own group, so the group kills already reach every listed process,
and the per-pid SIGKILL is a second net.

No mutation runner is wired for this stack, so these hand plants stand in for a kill rate.

## The guard: test coverage, not new bypasses

This seat probed the guard only with the conformance file's own cases and ordinary project commands. It
wrote no new evasion form. Its added cases are the plainest spellings of what the docstring already claims
(split and long `rm` options, a wrapper, `-s`, unclosed quotes), and the guard blocks each one at
`f2b7d35`.

**Coverage**, measured with `coverage --branch` on `judge_text` over the file's MUST_BLOCK and MUST_ALLOW
lists:

| | MUST_BLOCK | MUST_ALLOW | line and branch coverage of `bash_guard.py` |
|---|---|---|---|
| shipped | 137 | 46 | 86% |
| with this seat's cases | 146 | 49 | 89% |

- `main()` runs only in the subprocess cases, so it is not counted.
- **Still not exercised:**
  - the 64-wrapper cap (`:499-500`);
  - the 5 s deadline handler (`:670`);
  - `fish -C` (`:594-598`);
  - `--command` (`:603-604`);
  - git's `-C` and option-only forms (`:624`, `:626`);
  - `${ }`'s quote handling (`:397-414`).
- **The second reading alone.**
  - It blocks all 146 MUST_BLOCK cases and allows all 49 MUST_ALLOW cases.
  - The text reading holds no case on its own, which is why G9 shipped green. The 29 pre-#189 cases now
    run against it alone.
- **What this does not show.** Whether forms outside the list are missed. The round-3 review's R2 still
  stands.

## Acceptance-criterion coverage

The plan's W4 row adds no REQ-ID (`docs/plans/m21-plan.md:28`). The issues stand in for criteria.

- #200 (D-192 cl. 1): `tests/unit/test_wave_check_m21_rules.py:72`, `:83`, `:91`, `:407`, `:495`, `:693` --
  GREEN.
- #183 (cl. 2, the range's diff): `:141`, `:200`, `:209`, `:231`, `:248`, `:310`, `:322`, `:331`, `:341`, `:356`,
  `:369`, `:448`, `:460`, `:471`, `:524`, `:539`, `:558`, `:623`, `:654` -- GREEN. The merged-close re-read is M1.
- #201 (cl. 2, ADR timing): `:155`, `:166`, `:385`, `:482`, `:571`, `:594`, `:606`, `:667` -- GREEN.
- #203 (cl. 2, process log): `:183`, `:192`, `:397`, `:642` -- GREEN.
- #202 (cl. 3, the ledger): `:268`, `:278`, `:288`, `:420`, `:429`, `:437`, `:502`, `:511`, `:585`, `:682`
  -- GREEN.
- #182: `tests/unit/test_ci_needs.py` (9 cases) -- GREEN.
- #249: `tests/unit/test_needs_git.py` -- GREEN (M4 is the mark's scope, not the check).
- #179, #181, R1 of round 1:
  - `tests/unit/test_offline_run.py:146`;
  - `tests/unit/test_swift_strict_pool.py:18`;
  - `tests/unit/test_swift_watchdog.py`, 7 tests;
  - the Engine suite in check-fast.

  All GREEN.
- #178: `tests/unit/test_fetch_bounds.py` -- GREEN.
- #248: `tests/unit/test_security_invariants.py`, the two #248 tests and `:732` -- GREEN.
- #227: `ios/UITests/ScreenPathTests.swift` -- not run here (R1).
- #189: `conformance/test-hook-claims.py`, 146 MUST_BLOCK cases, 49 MUST_ALLOW cases, the text-only run,
  and the bound and settings checks -- PASS.

## Mocks / contract tests

No external integration is added or changed: `src/` and `ios/ModelRanking/` are untouched by the range.
The workflow file is read by `ci_job_facts`, and its test plants real edits of `.github/workflows/ci.yml`.
No canonical mock is involved.

## Tests added/extended this review

- `tests/unit/test_wave_check_m21_rules.py`:
  - `:642`: the process-log heading's date (WC1);
  - `:654`: a close with uncommitted edits read to HEAD (WC2);
  - `:667`: a plan-named ADR after a code commit citing it, and the quiet case (WC3);
  - `:682`: row 8 giving both answers (WC4);
  - `:693`: the pointer back names the amending ADR, and `applies` is no amendment (CR1, M6).
- `tests/unit/test_security_invariants.py:732`: a pointer to another row does not answer the phrase (P1).
- `conformance/test-hook-claims.py`:
  - `:361-366`: 9 MUST_BLOCK cases;
  - `:395-396`: 3 MUST_ALLOW cases;
  - `:431-440`: the text reading run alone (G2, G7, G8, G9; M3).

Each fails with its plant and passes on `f2b7d35`. `ruff` is clean on both test files. The two files and
their neighbours (`test_needs_git.py`, `test_skip_budget_local.py`, `test_language_of_shipped_strings.py`):
76 passed. Nothing is committed.
