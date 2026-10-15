---
record_type: review
id: devflow-v7.1-upgrade-review
status: draft
process_version: v7.1
date: 2026-10-15
seat: independent
---
# DevFlow v6.6 -> v7.1 upgrade (D-199): independent Code-Reviewer seat

**Independent:** yes

**Reviewed head:** 18ebafda9017f40ba77eb98ddeb3243caba40ef1

**Seat:** independent Code-Reviewer. I wrote none of this change. My policy came from the protected base:
`git show main:.claude/agents/Code-Reviewer.md`, `main:.agents/rules/practices.md` and
`main:.agents/rules/review-seats.md`, never from the branch. The precedent for method and format is
`main:docs/reviews/devflow-v6.6-upgrade-review.md`. **Author family / reviewer family:** Claude / Claude, the
same family. No second family was available. The review ran in a fresh context that had not seen the
authoring session. The Security-Reviewer seat runs after this one, on the same range.

**Subject:** draft PR #281, branch `upgrade/devflow-v7.1`, commits `7bdb7c5..18ebafd`:
- `27d2022`: D-199 in `docs/decisions.md`, plus `docs/watchlist.md`
- `18ebafd`: the upgrade itself, 101 files

**Base:** `main` = `7bdb7c5`. DevFlow tags `v6.6`, `v7.0` and `v7.1` are local.

**Method:**
- **Own worktree.** A detached worktree at `18ebafd` in a `mktemp` directory, with its own venv
  (`make install`: marker `v7.1 · manifest a41de86d4696`). `advisor.db` was copied read-only from the author's
  tree, with md5 `495755d517aeb1e6943a8e3fb936658c` before and after. I did not touch the author's tree, the main
  checkout or the launchd service.
- **Faithfulness.** For each of the 99 paths `git diff v6.6 v7.1` touches, outside `.github/workflows/`, I
  compared v7.1 with HEAD. 67 are byte-identical. For the other 30, I checked every line v7.1 adds or removes
  against HEAD, then read each remaining hunk.
- **Guard differential.** I fed about 150 Bash and Write/Edit payloads through `main`'s whole hook commands
  (the settings' text guard plus the M21 guard) and HEAD's (the merged guard). Each ran from its own copy of
  the guard, with no brief, from the temp directory, from a fake work tree, and from `$HOME`. The commands were
  only judged, never run.
- **Old tests, new code.** I ran `main`'s versions of the three changed unit-test files against HEAD's code.
- **Mutants.** Eight mutants ran in place in the worktree. Five guard and settings mutants ran in a `git
  archive` export with no `.git` above it, because the hooks rightly refuse writes into a work tree's
  `.claude/`. Every file was restored, and its md5 checked.
- **Full gate.** `make check` in the worktree.

## Verdict

**BLOCKING** -- 1 BLOCKING, 1 MAJOR, 3 MINOR, 4 NIT.

**The apply is faithful.**
- Every v6.6 -> v7.1 hunk to a DevFlow-owned file is in HEAD, except `.github/workflows/**` (#278) and where a
  documented project rule keeps the project's version:
  - D-199 §5: §2a of AGENTS.md, W-015 in `bootstrap-check.sh`, and the fitted `test-placeholder-allow.py`
    and `test-process-version.py`;
  - D-185 / D-199 §3: the guard, `test-bash-guard.py` moved to `vercel`, and the Write hook;
  - D-161: `check_records.py`, `make closes` outside `check`, and the commit-identity text;
  - the W3 Tester's M9: `wave_check.py` keeps `^\s*` in `FINDING_ID`, stricter than v7.1, and says so at
    `scripts/wave_check.py:94-98`;
  - project text kept in `practices.md`, `issues.md` (D-178), `closure-checklist.md` ("PASS or MINOR", as on
    `main`), `INSTALL.md`, `permission-matrix.md`, the README, and the earlier adaptations in
    `test-commit-identity.py` and `lib_record.py`. Their diff against v7.1 is the same as `main`'s against
    v6.6.
- **No hunk was dropped silently.**

**The guard holds.**
- The pin is right: the sha256 of `.claude/hooks/bash_guard.py` is `e65bf212…0129`. It is the value in both
  PreToolUse hooks, and in both refusal lines (`.claude/settings.json:77,88`).
- `main`'s `tests/unit/test_bash_guard_bounds.py` passes on HEAD's guard.
- In the differential, HEAD refuses everything `main` refused, except:
  - commit-message and heredoc false positives, as intended;
  - `rm -rf` on scratch, by D-199 §3 (see MINOR-2);
  - `.env.example` through the Write hook (NIT-4).
- HEAD also refuses 21 calls that `main` allowed: `--no-verify`, `git commit -n`, `core.hooksPath`,
  `update-ref main`, `gh pr merge` and `gh pr ready`, protection APIs, `.env` shell writes, `find -delete`,
  `a=fly; $a deploy`, and `d=.claude; > $d/x`.

**The BLOCKING is in the ledger merge.** The project's three-row rule said that only the owner's ruling resets
a control's count, and that an in-scope event resets nothing (the owner's ruling of 2026-10-10, and the M21
fixes review's M3 and mutant X5). v7.1's `review` kind replaced that rule. The rows written as `review` now
reset the count, and so does any row that cites a decision-shaped string. The old assertions were deleted.

## Findings

### BLOCKING-1 -- An in-scope event, or any `review` row citing an ID, resets the three-row count (test-integrity; X5 reopened)

**Where:**
- `scripts/wave_check.py:888-890`: `if kind == "review": if DECISION_REF.search(reason): counts[control] = 0`
- `scripts/wave_check.py:68`: `DECISION_REF = re.compile(r"\b(?:D|P|R)-\d+\b")`
- `tests/unit/test_wave_check_m21_rules.py:876-915` and `:980-981`
- `docs/control-events.csv:31,33,34,36,37`

**What changed:**
- On `main`, `ledger_strikes` counted every `skip`/`bypass` after the control's last `ruling`, and a `ruling`
  counted only when its reason began `the owner, YYYY-MM-DD`. The test said so: `main` at
  `tests/unit/test_wave_check_m21_rules.py:855-880`.
  - `test_only_the_owners_ruling_resets_a_count` asserts that a `within-scope` row resets nothing (`:862`),
    nor does a `review`.
  - `test_a_ruling_that_names_no_owner_is_refused` asserts that a ruling which does not name the owner is
    refused.
- Both were deleted. Their replacements assert only that `ruling` and `within-scope` are no longer kinds. The
  property they held is now false:
  - The upgrade rewrote every former `within-scope` row, each an event *inside* a control (a docs-only or
    declared-red commit), as a `review` row that "cites R-1".
  - `_within` (`:980-981`) and `skip_ledger_problems` now **require** such a `review` row for every docs-only
    commit a Bypass names.
  - Each one resets `commit-after-check-fast`'s count.
- The legend itself defines `review` as "the review three skips or bypasses demand"
  (`docs/warnings.ledger.template.md:36`), not an in-scope event.
- Nothing checks that the cited decision exists.

**Measured, with HEAD's `ledger_findings` against the repository's legend:**

| Ledger | HEAD | `main` (`ledger_strikes`) |
|---|---|---|
| 4 bypasses of `commit-after-check-fast`, with one `review,"ccc3333, a docs-only commit (D-192)"` (the row `_within` writes) in the middle | `[]`, green | `['commit-after-check-fast']`, struck |
| 3 bypasses + `review,"agent looked at it (D-99999)"` | `[]` | struck (a review resets nothing) |
| 3 bypasses + `review,"cf. D-5"` | `[]` | struck |

The rewrite also turned two rows that say "(not the owner's ruling; the owner may overrule it)"
(`docs/control-events.csv:36,37`) into count-resetting rows, by appending "cites D-199" and "cites R-1".

**Failure scenario:**
- A control is bypassed in waves 1, 2, 4 and 5 of a milestone.
- Wave 3 makes a docs-only commit, and the gate demands its `review` row.
- The three-row rule never fires, and `make wave-check` is green. The control is never put under review.
- An agent can also clear any struck control by writing one `review` row that cites any `D-<n>`. The owner
  never sees it.

D-199 §4 records the row mapping. It does not record that this consequence was ruled on. The owner's choices
listed in D-199 are the guard merge, heavy mode and the deploy commands.

**Remedy:** one of these.
- **(a)** Add a fourth row to the legend table, ``| `within-scope` | an event inside a control as a decision
  re-scoped it | cite the decision |``. `ledger_kinds` derives the vocabulary from that table, and any kind other
  than `skip`/`bypass`/`review` counts nothing and resets nothing. Then:
  - restore the rewritten in-scope rows to that kind;
  - point `_within` and `skip_ledger_problems` at it;
  - restore the deleted assertions: an in-scope row resets nothing.
- **(b)** Also make a resetting `review` cite an ID that exists in `docs/decisions.md` or `docs/refusals.md`.
  That would also be a DevFlow field finding, K2.
- **(c)** Or the owner rules, in D-199, that v7.1's reset semantics replace the 2026-10-10 rule. That is the
  owner's call, not the agent's.

### MAJOR-1 -- One wave's skip row now satisfies every wave of its milestone, so repeated skips go uncounted

**Where:** `scripts/wave_check.py:744-746`
(`or re.fullmatch(re.escape(milestone) + r"-w\d+", row[1].strip())`), and its test
`tests/unit/test_wave_check_m21_rules.py:294-301`.

**What changed:**
- On `main`, a skip in wave `m30-w2` needed a row for `m30-w2` or for the milestone (`m30`).
- HEAD accepts a row for any wave of the milestone, an earlier or a later one.

**Measured (`skip_ledger_problems`, row 9 lists `make ui-test` as skipped, the ledger holds only
`ui-test,m30-w1,skip`):**
- HEAD: `[]` for `m30-w2` and for `m30-w3`.
- `main`: a finding for each.

**Failure scenario:**
- `ui-test` is skipped in W1, W2 and W3.
- One row is written. Every close is green.
- The ledger holds one row where it should hold three, so the three-row rule cannot fire (AGENTS.md §5,
  friction telemetry). D-199 §4 states the widening, but not this cost.

**Remedy:**
- Keep exact-wave matching for new closes.
- Accept a row for another wave only for the rows the upgrade rewrote (each carries
  `[rewritten at the DevFlow v7.1 upgrade, D-199: wave was ...]`). Alternatively, date-gate the widening to
  closes dated on or before 2026-10-15.

### MINOR findings

- **M1** -- The V1 and S1 wiring has no gate test. `scripts/check_records.py:2032-2033`.
  - Mutant Mu8 replaced `findings += version_rule(root)` with `[]`.
  - `check_records.py --self-test`: PASS, 0 problems. `--root .`: PASS. The self-test calls `version_rule()`
    directly, and nothing runs `main()` on a tree whose brief and marker disagree.
  - *Failure scenario:* a later merge drops the line, as the v6.4 step once dropped the trailer check
    (v6.6 review MAJOR-3), and a stale brief goes unseen.
  - *Remedy:* a `tests/unit` test that runs `check_records.py --root <tmp>` on a tree whose brief says v6.6
    and whose marker says v7.1, and asserts V1. The same for S1.
  - Upstream has the same shape (K3).
- **M2** -- `rm -rf` of a git work tree under the temp directory passes. `.claude/hooks/bash_guard.py:1074-1092`
  (`_temp_bases`: `/private/tmp` and `/var/folders` are scratch).
  - From `$HOME`, `rm -rf /private/tmp/claude-501/…/scratchpad/w-up-dry`, a live worktree with work on it: HEAD
    allows it, and `main` refused it.
  - This project keeps agent trees there: the author's tree, and D-174 seats under `.claude/worktrees/`.
  - D-199 §3 takes v7.1's rule by design, so this is MINOR, for the Security-Reviewer to weigh.
  - *Remedy:* treat a target that is, or contains, a `.git` entry as not scratch unless it is under
    `.claude/worktrees/<name>`.
- **M3** -- D-005 and D-006 were rewritten in place, and the record says they were not.
  `docs/decisions.md:83-93` and the D-006 body.
  - `27d2022` replaces D-005's Decision, Rationale and Mitigation, and D-006's category list.
  - D-005's status line still says "Decision body preserved below per B.2 (supersede, don't edit)". The new
    amendment says "the body above is kept as written". Neither is true after this commit.
  - This text is DevFlow's own: v7.1 made the same edit to its universal records.
  - *Failure scenario:* a reader trusts the record's claim that it is unedited. AGENTS.md §3.4 B.2.
  - *Remedy:* restore the v6.6 bodies and keep v7.1's text as the amendment, or strike the "preserved" and
    "kept as written" claims. Report it upstream (K4).

### NITs

1. **`README.md:1`** still says "(DevFlow v6.6)". Line 3 says v7.1.
2. **The ledger rewrite edits 13 rows of an append-only ledger in place.** Each is marked, and none
   vanished. The two "not the owner's ruling" rows gained a decision citation that changes how they count
   (BLOCKING-1).
3. **After the merge, `make deploy-check` fails:**
   - `release-security.md names no **Reviewed head:**`;
   - `there is no milestone Tester verdict (docs/reviews/m<N>-tester.md)`.

   So both deploy commands stay refused until a new release review and a milestone Tester exist. D-199's
   "Revisit when" anticipates this, and the owner should know before the next deploy.
4. **The Write hook now allows `.env.example`, `.env.sample` and `.env.template`.** `main`'s M21 guard refused
   them through `--write`. This is v7.1's and v6.6's rule, and is held at
   `tests/unit/test_bash_guard_bounds.py:200`, but D-199 does not mention it. The commit message also says
   "two shipped conformance tests are fitted", while four differ from v7.1: `test-bash-guard.py`,
   `test-run-check.py` with its fixture, `test-placeholder-allow.py` and `test-process-version.py`. Each is
   commented in place.

### K.9 (outside this change)

- **K1** -- The `.claude/` protection does not cover removing a parent of it. On `main` and HEAD alike, these
  pass: `rm -r .` in a repository root, `rm -r ..` from `ios/`, `rm -r ../repo`, and `mv ../repo ../gone`. Each
  deletes or moves the owner's `.claude/` and `.githooks/`. This predates the change.
- **K2** -- (DevFlow) `DECISION_REF` accepts IDs that do not exist (`D-99999`), so v7.1's "cite the decision"
  is a shape check, not a reference check.
- **K3** -- (DevFlow) `check_records.py` V1 and S1 are tested only through direct calls in `--self-test`, never
  through `main()`.
- **K4** -- (DevFlow) v7.1 edits D-005 and D-006 in place while claiming B.2.

### Risks queued

- **R1** -- The ledger semantics (BLOCKING-1, MAJOR-1) decide when a control goes under review. If neither is
  fixed or ruled, the first sign is a milestone whose closure shows four or more bypasses or skips of one
  control and no strike.

## Focus questions

1. **Faithfulness.**
   - 67 of 99 v7.1 paths are identical to v7.1. Every difference in the other 30 is covered by a documented
     project rule, listed under the verdict.
   - All v7.1 additions are present:
     - `check_records.py`: V1, S1, `_nested`, `_is_checkout`;
     - `wave_check.py`: the legend, `brief_fields`, the recomputed reviews, the milestone Tester;
     - `Makefile`: `session-check` first in `check`, plus `mode`, `review-need`, `deploy-check`,
       `guard-pin`, `run-check`, `secrets_scan.py`, `run_check` and `--release-records` in `closes`, and the
       `ensurepip` probe;
     - `settings.json`: SessionStart, `-I -S` everywhere, and the attribution;
     - `test-hook-claims.py`: every v7.1 case.
2. **Conflicted merges.**
   - `bash_guard.py`: every M21 rule survives, and `main`'s test passes on it. D-185 is now stricter: `fly`
     but its read-only subcommands, where it was `deploy|destroy` only.
   - `settings.json`: the pin matches.
   - `wave_check.py`: the review seat, the history rules, and the stricter finding parse are kept, but see
     BLOCKING-1 and MAJOR-1.
   - `check_records.py`: the project's validator, with V1 and S1 added.
   - `Makefile`: `closes` stays outside `check` (D-161).
   - `control-events.csv`: BLOCKING-1.
3. **Tests.**
   - `test_bash_guard_bounds.py`: additions only. 104 tests pass, and `main`'s version passes on HEAD.
   - `test_check_fast.py`: `session-check` added to RECORDS, which is correct.
   - The conformance fittings weaken nothing (`fly`->`vercel`, plus the D-185 cases).
   - `test_wave_check_m21_rules.py`: deleted assertions. `main`'s version fails 7 tests on HEAD. Five are the
     retired `ledger_strikes`, and two are real semantic losses (BLOCKING-1).

## Mutants

The `wt` mutants ran in place in the worktree. The `exp` mutants ran in the no-`.git` export. Each file was
restored, and the md5 matched the value before the mutation.

| # | Where | Mutation | Killing check | Result |
|---|---|---|---|---|
| Mu1 | wt | `session_check.py`: the fail-closed `return 1` -> `return 0` | `conformance/test-session-check.py` | **RED** ("closed: exit 0 (wanted 1)") |
| Mu2 | wt | `session_check.py`: the marker check -> `if False` | same | **RED** |
| Mu3 | wt | `review_need.py`: drop `and mode != "light"` | `conformance/test-review-need-mode.py` | **RED** |
| Mu4 | wt | `brief_fields.mode()` always `heavy` | same | **RED** |
| Mu5 | wt | `deploy_gate.py`: changed code after the head -> passes | `conformance/test-bash-guard.py` | **RED** (30 wrong verdicts) |
| Mu6 | wt | `wave_check.py:889`: the `review` reset no longer needs a citation | unit tests; `test-ledger-kinds.py` | **RED** (2 failed) / **RED** |
| Mu7 | wt | `wave_check.py:746`: drop the other-wave match | unit test | **RED** (1 failed) |
| Mu8 | wt | `check_records.py:2032`: drop the V1 call | `--self-test`; `--root .` | GREEN / GREEN -- **survived** (M1) |
| G1 | exp | guard: the D-185 `fly` rule off | `test_bash_guard_bounds.py`; `test-bash-guard.py` | **RED** / **RED** |
| G2 | exp | guard: the deploy-script rule off | `test_bash_guard_bounds.py` | **RED** |
| G3 | exp | guard `--write`: the `.claude/` protection off | same | **RED** |
| G4 | exp | guard `--write`: the `.env` refusal off | same | **RED** |
| G5 | exp | `settings.json`: the Write hook's pin -> zeros | same | **RED** |

**Result:** 12 of 13 mutants killed by a gate test. Mu8 survives every gate.

## Gate results (worktree, macOS, Python 3.14 venv, owner's `advisor.db` copied read-only)

`make check` exit 0:
- **session-check:** PASS. It read this session's marker in the repository's common git dir, and
  core.hooksPath.
- **ruff:** clean.
- **mypy:** no issues in 49 files.
- **pytest:** 3029 passed, 27 skipped. Coverage 92.19%.
- **coverage-floor:** PASS, 49 modules. The skip budget is 86, equal to the derived count.
- **check_records:** PASS. Self-test: 0 problems.
- **install-check:** PASS.
- **harvest-context:** SKIPPED, as in any installation.
- **wave-check-all:** 68 validated, 20 out of scope.
- **conformance:** 26 tests, 0 failing.
- **swift-test:** 637, plus SlowTier 7 of 7.
- **client-decls:** 21 files in 4 configurations.

`make review-need RANGE=7bdb7c5..18ebafd`: `code-reviewer+security`. `make mode`: `heavy`. `make deploy-check`:
FAIL (NIT-3). The worktree's `git status` was clean after every mutant.
