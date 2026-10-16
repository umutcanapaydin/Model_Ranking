# Upgrading an existing project

Your project runs an earlier DevFlow — or the General Pipeline it grew out of — and a new version
ships. **Never copy the new tree over yours:** a copy deletes the controls your project grew and
silently overwrites any file of yours that the new version happens to ship under the same name.
Apply the *difference* between the version you installed and the new one, three-way, so your
changes survive and every collision is shown to you.

## 0 · Read before the first command — what bites in every upgrade

What the field hit, in order of when it bites (two projects upgraded to `v7.1` on 2026-10-14/15,
one from `v7.0`, one from `v6.6`). Each is explained in its section below; this box exists so the
agent doing the upgrade meets them first.

1. **Start the upgrade session in the repository root, and keep its work out of the temp
   directory.** A session started anywhere else registers none of the repository's hooks, skills or
   profiles, and `make session-check` — a leg of `check-fast`, `check` and `gate` — refuses it. An
   upgrade branch checked out under `/tmp` or `/private/tmp` is lost at the next reboot: work in the
   clone, or commit early.
2. **The agent commits, pushes the upgrade branch and opens the draft PR; the owner merges** —
   from a terminal or the GitHub UI, as for every PR (§5). Never hand the owner the commit or the
   push. When `make session-check` cannot pass in this session — the upgrade installs or changes
   the SessionStart hook (from `v6.6` or older), or the session began outside the root — finish the
   tree, ask the owner **once** to restart Claude Code in the repository root, and continue there:
   the new session has the marker. Do not `--no-verify`; do not record a skip row for it.
3. **Commit the decision before the code.** Rules that read history (an ADR first appears before
   the code it governs) have nothing to read on a staged tree, so a tree green before the commit
   can still fail `make gate` at the push. Commit the upgrade ADR and the records' versions
   (`docs/decisions.md`, `docs/watchlist.md`) first, the rest second, and run the gate on the range
   after committing.
4. **A diverged installation is a merge of two designs, not a patch.** Before resolving, list the
   shipped files the project changed (`git diff <your-tag> HEAD --stat -- <shipped paths>`) and ask
   the owner once for every place where the project and the new version solved the same problem
   differently. A hunk that applied cleanly can still change a project rule with no conflict marker
   (`git apply -3` changed a project's finding regex outside the conflict): read the diff of every
   shipped file the project had changed, not only the conflicted ones.
5. **The ledger goes red on rows in other spellings** (`v7.1` below): `docs/control-events.csv`
   accepts `skip`, `bypass`, `review`, and a `review` row must cite `D-<n>`, `P-<n>` or `R-<n>`.
   Rewrite `rejected`, `ruling`, `within-scope` rows in place; a control that already holds three
   skips gets one `review` row citing the ADR that reviewed it. Keep
   `docs/warnings.ledger.template.md`: the legend is read from it. **Ask the owner before the
   rewrite:** Claude Code's auto mode refuses an in-place edit of the ledger as audit tampering. A
   row that recorded something that never ran has no kind of its own: say so in its reason when you
   give it one.
6. **A light project that has released goes red on `make closes`** (`v7.1` below): a
   `docs/reviews/release-security.md` with no `docs/reviews/release-tester.md` beside it is refused
   (`closure_check.py --release-records`). Run the release Tester inside the upgrade PR before
   pushing it, not after CI fails.
7. **The first deploy after the upgrade needs fresh verdicts.** The deploy gate counts `.claude/`,
   `scripts/`, `conformance/` and the `Makefile` as code, so the upgrade itself makes the security
   verdict stale: plan a security delta over it. A heavy project's `docs/reviews/m<N>-tester.md`
   written under `v7.0` has no `**Reviewed head:**`, and a project from `v6.6` or older has no
   milestone Tester verdict at all: `make deploy-check` and the deploy gate refuse every declared
   deploy until the Tester runs on the milestone and records its head. Plan both runs before the
   first deploy, not at it.
8. **After the owner merges, start a new Claude Code session from the repository root** (§5).
   The session that upgraded predates its own hooks; nothing registered in it is the new version's.
9. **`git remote add devflow`** leaves two GitHub remotes, and `gh` without `--repo` stops asking
   which one: run `gh repo set-default <owner>/<repo>` once, or the owner's next `gh pr merge` fails.
10. **A guard the project added rules to does not take a patch by `git apply -3`.** The shipped
   `.claude/hooks/bash_guard.py` changes in most releases; a project copy carrying its own rules
   conflicts in dozens of hunks (model_ranking's ran to twice the shipped length). Take the shipped
   file, port the project's rules onto it, keep the shipped guard tests, and ask the owner to re-pin
   it (`make guard-pin`). The shipped tests set `TMPDIR` themselves: a CI runner has none, and a
   project's own guard test that leaned on macOS's `TMPDIR` passed on the laptop and failed in CI.

Then `docs/project-brief.md`, `docs/decisions.md` and `docs/watchlist.md` take the new
`process_version:` (§4), or `make check` refuses the brief (`V1`).

## 1 · Which version you have

`.gp/installed` says, on its `gp_version:` line. An install older than that file: the
`process_version:` in `docs/decisions.md`, or the tag you copied from.

## 2 · Apply the difference, on a branch

**A DevFlow tag exists for your version:**

```bash
git switch -c upgrade/devflow
git remote add devflow https://github.com/SADCAIVibe/DevFlow.git   # once per clone
git fetch devflow --tags
git diff <your-tag> <new-tag> | git apply -3 --exclude='.github/workflows/*'
```

`git apply` refuses the **whole** patch when a path it touches is not in your index — git says
`<path>: does not exist in index`. That is a file you removed or renamed (a package `__init__.py`
you dropped, say), or a file the new version deletes that you had changed. Add one
`--exclude='<path>'` per path it names — `src/`, the product's own tests, anything you wrote under a
shipped name — rerun, and list the excluded paths in the upgrade PR.

**No tag for your version** — a General Pipeline package, or a version DevFlow never tagged
(`v6.0.1`, `v6.1`): the owner builds a two-commit scratch repository — commit 1 the files exactly
as your project installed them, commit 2 the new DevFlow tree — and you apply the difference between
them the same way:

```bash
git fetch /path/to/scratch main
git diff FETCH_HEAD~1 FETCH_HEAD | git apply -3 --exclude='.github/workflows/*'
```

**Workflow files are a human's part.** An agent never edits `.github/workflows/`, so the commands
above leave it out. A human applies it the same way, limited to that path:
`git diff <your-tag> <new-tag> -- .github/workflows | git apply -3`.

## 3 · Resolve what git shows you

- **Both sides changed a file:** `git diff --name-only --diff-filter=U` lists every one. Resolve
  each by hand; git has already merged whatever did not overlap.
- **A file you wrote that the new version now ships under the same name** shows as a conflict too.
  Keep yours under a new name and take the shipped one:
  `git show :2:<path> > <your-new-name>`, then `git checkout --theirs <path>`, and `git add` both.
- **`make install` refuses: "carries no `process_version`"** — add `process_version:` (the version
  those records were written under) to the frontmatter of `docs/decisions.md` and
  `docs/watchlist.md`.
- **Frontmatter `status:` values from earlier versions:** `proposed` becomes `draft`, `accepted`
  becomes `ratified`; the validator names them. This is the record's frontmatter only — an ADR's own
  `**Status:**` line in the body (proposed / accepted / superseded) keeps its vocabulary.
- **Files the new version removed that you had changed** make `git apply` refuse the whole patch
  (above): exclude them, then keep them as your own files or delete them. That is your decision,
  not the upgrade's.
- **Seed documents the project has filled** — `docs/decisions.md`, `docs/refusals.md`,
  `docs/watchlist.md` — are yours: where the new seed differs, keep your content.

## 4 · Update the records the upgrade touches

An upgrade changes the version the records declare, and nothing else rewrites them for you. Two
field projects ran `v7.0` with a brief that still said `v6.3` and `v6.6`; from `v7.1`, `make check`
(`check_records.py` rule `V1`) refuses a `docs/project-brief.md` whose `process_version:` differs
from the `gp_version:` in `.gp/installed`. In the same upgrade branch:

- **`docs/project-brief.md`** — frontmatter `process_version:` to the new version; then every setup
  question the new version added, answered (the template's numbered list is the source — for
  `v7.0`: `Working mode:`, `Deploy commands:`, `Paths that make a change HIGH:`, `QA verification:`;
  `v7.1`: `Runtime config files:`);
  and the answers that have changed since setup (`GitHub Actions run here:`, `The default branch can
  be protected:` — one project's brief said Actions did not run while CI graded every PR).
- **`docs/decisions.md` and `docs/watchlist.md`** — frontmatter `process_version:` to the new
  version. `make install` derives `.gp/installed` from these two, and refuses while they disagree.
- **`.github/workflows/ci.yml`** — the human's half (§2): take the new workflow when the entry
  below says it changed, and record in the upgrade PR that it was, or was not, taken.

## 5 · Then, as for any change

`make install` · `make hooks` (once per clone: it points `core.hooksPath` at `.githooks`, whose
pre-push hook runs `make gate`) · `make labels` · `make check` · `make gate` — all green — then one
draft PR for the whole upgrade. A human merges. If the project has no `docs/project-brief.md` yet,
run `/setup-project` afterwards: the choices it records decide how the new version runs.

**When the session cannot pass `make session-check`.** It cannot in the session that installs or
upgrades the SessionStart hook (the hook did not exist when the session began, so it wrote no
marker for it), nor in one started outside the repository root. In the field this produced skip rows
in `docs/control-events.csv`, in one project the three-skips lock, and in another an owner handed
the commit and the push. Do neither: do not record a skip, and do not hand the owner commands.
Finish the tree, run every other leg of `make check` by name, then ask the owner once to restart
Claude Code in the repository root and continue in the new session — it has the marker, so the
agent commits, pushes the upgrade branch through the pre-push `make gate` and opens the draft PR
itself. The post-edit hook reports the same red leg after every edit until the restart; that is the
same cause. A project that merged its own rules into `.claude/hooks/bash_guard.py` needs a new pin:
that one step is the owner's (`make guard-pin` from a terminal, `INSTALL.md` "Changing the Bash
guard"), because the guard is the safety floor — ask for it with the restart, in the same message. A session whose hook already existed before the upgrade
(`v6.7` or later), started in the root, passes the check and needs no restart until the merge.
**After the merge, start a new session** from the repository root.

**An upgraded project writing its first brief:** `/setup-project` reads `.gp/installed` at the new
version and no brief — that is not another upgrade; answer the questions.

## What changed for you

Read every entry newer than the version you had. Older than `v6.0.1`: compare the old and the new
`AGENTS.md` side by side after the upgrade.

**`v7.1.2`** — PATCH: the guard holes a heavy project's security review found, and heavy mode's
security review moved to the milestone's end (2026-10-16). No record changes shape and no stage
changes; take every file. From `v7.1.1`: `git diff v7.1.1 v7.1.2 | git apply -3`, then the three
records' `process_version:` to `v7.1.2` (§4), then `make install`, then restart the session (§5).
From `v7.1` take the `v7.1.1` entry first, or diff from `v7.1` directly.
- **Take the guard, `.claude/settings.json` and `scripts/deploy_gate.py` together.** The guard runs
  only its own project's deploy gate and asks it about other repositories with `JUDGE_PROTOCOL = 2`;
  a project that added its own rules to the guard ports them onto the new file and the owner re-pins
  it (`make guard-pin`, INSTALL.md "Changing the Bash guard") — `git apply -3` will conflict there.
- **What the guard now refuses that it passed:** `rm -r` without `-f` outside scratch (with no
  terminal it never prompts); `mv`, `rm -r`, `find -delete` and `git rm -r` of the repository, a work
  tree the command runs in, the home directory, or anything in `.git`; inside a worktree you work in,
  its own files (they are not scratch); a scratch target holding a git work tree; a git alias to a
  writing command set with `git config`, and code-running config keys judged as shell; `include.path`;
  `ssh host <command>` judged as the command; any deploy declared in another repository. An agent that
  hits one of these is meant to: remove files by name, use `git worktree remove`, or ask the owner.
- **Heavy mode: the Security-Reviewer runs once per milestone**, on the plan's last wave, over the
  whole milestone, writing `docs/reviews/m<N>-security.md` — `/close-wave` step 4. A wave no longer
  gets its own security review, and `make review-need` says so in heavy mode while it prints the
  signals. `make wave-check` asks for the file on the last wave of a plan whose close declares
  `v7.1.2`; closes written before are graded as they were (`--wave-security`). A milestone open
  across the upgrade: run the milestone security review on its last wave as the new rule asks.
- **Light mode is unchanged**, except `rm -r` above.

**`v7.1.1`** — PATCH: what the first two `v7.1` upgrades found (2026-10-14/15). No record changes
shape and no stage changes; take every file. From `v7.1`: `git diff v7.1 v7.1.1 | git apply -3`, then
the three records' `process_version:` to `v7.1.1` (§4), then `make install`.
- **The read-first box (§0) and §5 are rewritten** from the two upgrades: the agent commits, pushes
  the upgrade branch and opens the draft PR, and the owner merges; when `make session-check`
  cannot pass, the agent asks once for a restart in the repository root instead of handing the
  owner commands; commit the decision before the code; a diverged installation; the light
  `release-records` bite; fresh verdicts before the first deploy.
- **The conformance suite runs in an installation.** `test-process-version` grades only the files
  the manifest delivers (it graded every record in the project: 109 of 121 and 280 of 292 failed
  in the field); `test-placeholder-allow`, `test-make-targets` and `test-run-check` run in throwaway
  trees, so a project's own `.placeholder-allow` entries, ledger rows and a real `D-999` no longer
  fail them. Drop any local patch of these four tests and take the shipped ones.
- **`closure_check.py` decides history first:** a closure report that declares no version, or one
  older than `v6.0`, is graded by filename and id only and no longer needs `record_type: closure`.
  A project that kept `make closes` out of `make check` for its old reports can put it back.
- **`wave_check.py`: a wave close that declares no `process_version`** is history only when it is
  dated before `installed_on` in `.gp/installed`; one dated on or after it, or undated, is refused —
  a close written after DevFlow was installed declares its version. A tree with no `.gp/installed`
  is graded as before.
- **AGENTS.md §2a writes examples, not placeholders**, so a project that keeps it passes
  `make bootstrap-check` C1. Re-apply your §2a from the new text if you kept the section.
- **The Bash guard** follows `cd`, `pushd` and `popd` through the command: `cd <repo> && rm -rf src`
  from a temp directory or a `.claude/worktrees/` checkout is refused, and a declared deploy after a
  `cd` into another repository is judged by that repository's gate. It refuses every prefix of
  `--no-verify` (`--no-veri`), `--config-env` and `GIT_CONFIG_*` naming `core.hooksPath`,
  `git config core.hooksPath`, and a `push --delete` whose branch is a variable it cannot resolve
  (`m=main; git push origin --delete $m`). `$TMPDIR` is scratch only when it is set, and a path that
  climbs out of it with `..` is not. It refuses every deploy in a tree whose `scripts/deploy_gate.py`
  predates the guard's `--judge` question (a `v7.0` gate answered it with exit 0): upgrade that tree.
  The pin in `.claude/settings.json` changes with the guard — take both files.
- **The deploy gate** declares `JUDGE_PROTOCOL = 1`, the line the guard reads.

**`v7.1`** — the `v7.0` field measurement (DevFlow #16, three projects, 2026-10-12). Records change
shape in two places; no stage changes.
- **Start a new session after the upgrade merge** (§5): `make session-check` cannot pass in the
  session that installed the SessionStart hook, and its failure line now says so instead of
  inviting a skip row. The line also says what a session started outside the repository root
  loses: no agent profile, skill or hook of the repository is registered in it. A session in which
  git cannot name the work tree now FAILS the check instead of passing it.
- **The brief's `process_version:` is checked** against `.gp/installed` (`check_records.py` rule
  `V1`, §4). A tree with no `.gp/installed` is not graded for it, and the output says so.
- **`docs/process-log.md` session numbers must be unique**: `check_records.py` rule `S1` refuses a
  second `## S<n>` heading with the same number (two agents on one repository used S49–S52 twice).
- **`make review-need` reads the working mode**: in light mode it never answers `code-reviewer`
  and prints why; test-only files under a HIGH path or with a sensitive name no longer route a
  change to security on their own; the Go parsers `json.NewDecoder(` and `.Decode(` are signals;
  the stacked-branch range is documented in the script (`make review-need RANGE=...`).
- **`docs/control-events.csv` gains the row kind `review`**: when a control reaches three skip or
  bypass rows, the review the threshold demands is recorded as one `review` row whose reason cites
  the decision — an ADR (`D-<n>`, `P-<n>`) or a `docs/refusals.md` row (`R-<n>`) — and it restarts
  that control's count. A review row that cites nothing counts nothing, and fails the close. Every
  row's `kind` is validated against the legend in `docs/warnings.ledger.template.md` (`skip`,
  `bypass`, `review`), and the `wave` column against its shapes (`m<N>-w<W>`, `issue-<n>`,
  `release`, `upgrade-v<X.Y>`, `setup`): rows written in other spellings are findings at the next
  `make wave-check`. Rewrite them in place — the ledger's rows are the one record `git blame` keeps.
  A control that already has three skip or bypass rows, reviewed under `v7.0` as an ADR and not as
  a row, turns every wave close red until one `review` row citing that ADR is appended. Keep
  `docs/warnings.ledger.template.md` in the tree: the legend `make wave-check` validates against is
  read from it, and a tree without it fails closed.
- **The milestone Tester runs at every milestone close, in light mode too.** Heavy: unchanged,
  `docs/reviews/m<N>-tester.md` on the plan's last wave — now with a `**Reviewed head:**` line,
  which the deploy gate and `make deploy-check` read in heavy mode too: a `v7.0` verdict without one
  refuses every declared deploy until the Tester runs again on the milestone and records its head. Light: the close before a release, on
  everything merged since the Tester's last verdict, in `docs/reviews/release-tester.md` with a
  `**Reviewed head:**` line; `make closes` (`closure_check.py`) refuses a closure report declaring
  `v7.1` without it, or with code changed after that head — the deploy gate's currency rule — and,
  in both modes, refuses a tree where `docs/reviews/release-security.md` exists with no Tester
  verdict beside it (`closure_check.py --release-records`): a light project writes no closure
  report, so this and the deploy gate (`make deploy-check`) are what reach its release.
- **`.placeholder-allow`** (new file, ships empty): a named exception to `make bootstrap-check`'s
  placeholder check, `<path>: <text> -- <reason>` per line, for an append-only record that quotes
  placeholder-shaped notation. A stale, unreasoned or malformed entry fails the check. Two projects
  carried this patch locally; drop the local copy and take the shipped one.
- **The conformance fixtures are renamed** to milestone numbers no project reaches:
  `conformance/wave/m901-wave-{2,3}-close.md`, `conformance/reviews/m901-wave-2-*.md`,
  `conformance/closure/closure-report-m90{7,8,9}.md`. A rename in the patch is keyed by its NEW
  name, so if your tree no longer has the old fixtures (deleted, or renamed by hand), `git apply`
  refuses with "does not exist in index": exclude the new names (§2), then take the fixtures from
  the tag — `git archive <tag> conformance/wave conformance/reviews conformance/closure
  conformance/run | tar -x` (the Bash guard refuses `git checkout <tag> -- <paths>`, which discards
  uncommitted work) — and delete any old-named copies; `conformance/test-fixture-ids.py` refuses a
  fixture a project could reach, and `test-milestone-tester.py` refuses a tree with none.
- `make session-check`'s and `make bootstrap-check`'s PASS lines say what they checked
  (`core.hooksPath`), not what the hook file runs.
- **A run lane, `/plan-run`** (new skill, `docs/run.template.md`, `scripts/run_check.py`,
  `make run-check`): the owner's unattended lane — two to five milestones planned at once, every
  question asked up front, the work on `integration/run-<name>` without waiting for merges, a stop
  only for an Escalate-NOW event. Nothing changes for a project that does not open one;
  `make closes` grades `docs/plans/run-*.md` only where one exists.
- **The Bash guard refuses four more shapes** from `v7.1`: a skipped hook (`--no-verify`, `git commit -n`,
  `git -c core.hooksPath=`), a moved or deleted protected ref (`git update-ref`), a shell write to a
  secrets file (`> .env`, `tee`, `cp`, `mv` to `.env`, `.env.*`, `<x>.env`, `.envrc`), and `find …
  -delete` outside scratch; the Write/Edit guard matches the same names by basename, so
  a source file whose name merely contains the word is no longer refused. The post-edit hook is POSIX sh (it ran only under bash;
  on Debian and Ubuntu `sh` is dash, and every edit there died in `set -o pipefail`).
- **The Bash guard is a file, `.claude/hooks/bash_guard.py`, not a shell string** in
  `.claude/settings.json`. It reads the command as shell words — a quoted string, a heredoc body or
  a `-m` message is data, so a commit message that mentions a deploy command is no longer refused —
  and it is run only when its sha256 matches the pin in `settings.json`: after an intended change
  run `make guard-pin`, then **restart Claude Code** (hooks are read at session start). Every hook
  now carries `timeout` and `"onFailure": "block"`, which need **Claude Code 2.1.295 or later**
  (`INSTALL.md`); an older Claude Code ignores both fields and a hook that hangs lets the call
  through. Take the new `settings.json` whole — the `permissions.allow` entries are exact targets now
  (`make lint`, not `make lint:*`), and a guard you had patched locally (a lexer, scratch-path
  exemptions for `rm -rf`) is covered: `rm -rf` under the temp directory, a `mktemp` result or
  `.claude/worktrees/` passes; everything else stays refused.
- **The deploy gate** judges the checkout the command runs in (not the main checkout), resolves the
  repository from the command's cwd, refuses when `scripts/deploy_gate.py` is missing instead of
  skipping, catches `gh -R <repo> pr merge` and `gh api .../pulls/<n>/merge`, and counts
  `.claude/`, `.githooks/`, `scripts/`, `conformance/`, `.github/` and the `Makefile` as code
  whatever their extension — a reviewer profile or a skill edited after the security review's
  reviewed head now needs a delta review. It also requires the milestone Tester's verdict to be
  current (light: `docs/reviews/release-tester.md`; heavy: the latest `m<N>-tester.md`): a hotfix
  deploy needs a Tester delta as well as a security delta.
- **`make deploy-check`** (new): the gate's question with no command — are the release verdicts
  current for this tree? Run it before a deploy made from a dashboard or another shell; `/going-live`
  starts with it and `docs/closure-checklist.md` §E.1 pastes its two lines.
- **`Runtime config files:`** (new brief line under question 6; `/setup-project` asks it): the
  files a deploy reads that git does not track; `/going-live` opens each before a deploy.
- `AGENTS.md`: names the skill at every step; an optional §2a for a second agent tool; the
  integration lane for when the owner says not to wait for merges; the third BLOCKING ends a review
  loop. Take the new file and re-apply your project section (§1, §2, §2a if you keep a second tool).
- Nothing in `.github/workflows/` changed.

**`v7.0`** — MAJOR: the review structure changed. Read it before applying.
- **Two working modes.** Add `Working mode:` to `docs/project-brief.md` (template question 10;
  `make mode` reads it). Unset, a project is **heavy** — it keeps running waves, with the changes
  below. Light runs issues only, with no Code-Reviewer and no Tester — *the Tester half is superseded by
  `v7.1` above: the milestone Tester runs in light mode too, before a release.*
- **Reviews are computed, per change:** `make review-need`. A wave gets the Code-Reviewer; the
  Security-Reviewer when the range needs one; the Tester **once per milestone**, on the plan's last
  wave (`docs/reviews/m{N}-tester.md`). A fix gets what the line names. A wave close declaring
  `v7.0` needs `Review need:` and `Last wave of the plan:` lines; closes written earlier keep their
  per-wave Tester rule, so nothing is rewritten.
- **The deploy gate.** List the project's deploy commands as `Deploy commands:` in the brief; each
  is then refused until `docs/reviews/release-security.md` names a `**Reviewed head:**` with no code
  changed since. Until you list them, nothing is guarded.
- **Declared HIGH paths** go into the brief as `Paths that make a change HIGH:` and a plan's
  `security-globs:` line; `make review-need` reads both.
- **A bug closes when its fix merges** unless the brief says `QA verification: on`: the PR says
  `Closes #<n>`. Turn it on to keep the `qa:` pipeline.
- **Triage** writes `Triage verdict: wave` in heavy mode for work of several slices;
  `/work-enhancement` is light-only.
- **A wave is a container issue** from the next `/plan-milestone` on. A plan already open has none:
  its remaining waves close with the plan file standing in for the container, and need no
  `security-globs:` line (`make review-need` then reads the brief's paths alone).
- **Switching modes** re-triages the open issues whose verdict belongs to the other mode
  (`/setup-project`, "A choice changes later").
- Nothing in `.github/workflows/` changed.

**`v6.7`**
- **Start Claude Code in the repository root.** Its guards load only from there. A new SessionStart
  hook marks each session that loaded them, and `make session-check`, now a leg of `make check`,
  refuses a Claude Code session without the mark, and a clone with no pre-push hook (`make hooks`).
  Outside Claude Code it checks nothing, so CI and a human's push are unchanged.
- The Bash guard also refuses `gh pr merge`, `gh pr ready` and writes to branch protection or
  rulesets: those are the owner's.
- `make secrets` scans only the files git tracks (as they stand in the working tree) and redacts
  every match; an untracked note no longer fails the gate or prints its key.
- A wave close or closure report that declares no `process_version` is graded as history, and
  `closure_check` now grades by the declared version like `wave-check`. If you took `closes` out
  of `check:` because older closure reports could never pass, put it back.
- From `v6.7` a closure report's citations must exist: the cited file, at least that many lines.
- A finding's indented sub-bullets are no longer counted as findings of their own.
- Nested checkouts (a worktree under `.claude/worktrees/`) are skipped by the record checks.
- The triage verdict may end the issue body as well as a comment; `/file-issue` no longer writes
  a lane into the body.
- `make install` skips a Python that cannot build a venv (a Debian or Ubuntu system Python
  without python3-venv) and takes the next candidate. Pass `PYTHON=/path/to/python` to choose one.
- **`.github/workflows/ci.yml` changed** — apply it by hand (the upgrade command excludes
  workflows): every job reads its runner from the variable `DEVFLOW_RUNNER` (unset: `ubuntu-latest`)
  and runs in a `python` container instead of `actions/setup-python`; `secret-scan` runs the
  gitleaks binary, sha256-pinned, instead of gitleaks-action, which needs a paid licence for a
  repository an organisation owns; `install-and-governance` derives the owner for the
  commit-identity check. Job names are unchanged, so branch protection needs no change.

**`v6.6`**
- Review findings carry ids. The Code-Reviewer and Tester write every MINOR, K.9 and queued-risk
  finding as `**M1**` / `**K1**` / `**R1**`, and the wave-close checklist gains a findings table:
  each id fixed in the wave (`fixed <sha>`), filed (`#<n>`), or `refused — <why>`. It also gains the
  footprint line `Stopped at three attempts:` (`NONE`, or the bug issues). `make wave-check`
  requires both on a close declaring `v6.6`; closes written earlier are graded by their version.
- The `work-issue` skill is removed: `/fix-issue` has its "with a human in the loop" section, and the
  triage verdict `work-issue` still selects it. The upgrade deletes `.claude/skills/work-issue/`.
- A warnings-ledger row ACCEPTED may name its issue (`#42`) as its owner instead of a milestone.
- Nothing in `.github/workflows/` changed.

**`v6.5`**
- Every review verdict declares its independence: the wave's Code-Reviewer and Tester files, and
  the `/fix-issue` Tester file, carry `**Independent:** yes`, meaning the reviewer wrote none of the
  code. `make wave-check` refuses a wave close declaring `v6.5` or later whose verdict lacks the line
  or says `no`. An author review passes only as a waiver: the checklist's Code-Reviewer row WAIVED,
  with a row for the wave in `docs/control-events.csv`. It is a declaration, not a proof. Closes
  written earlier are graded by the version they declare, so nothing is rewritten.
- The Bash guard refuses every command when `grep` is not on PATH. Before, nothing matched and every
  command was allowed.
- A key written twice in one mapping of a workflow fails `conformance/test-ci-yaml.py`: YAML keeps
  the last one silently. It reads the file with PyYAML where that is installed, and with a line
  reader over block mappings where it is not, so the duplicate-key check grades on every machine.
  The file's other checks (the steps, the matrix) still need PyYAML and say NOT-EVALUABLE without
  it; `make conformance` and CI install it.
- In Markdown, a code fence that is never closed is an `L1` finding, where before the rest of the
  file went unread. Close the fence. Code spans of any backtick length are now read correctly.
- `make check-fast` takes a project's own legs: `CHECK_FAST_OWN_LEGS`, and `CHECK_FAST_FORMS` for a
  gate that runs in another form (a parallel test run). Both go in `stack.mk` (`INSTALL.md`).
- `make ci-liveness` says in one line whether CI's latest runs started any step, which catches a
  billing or runner limit that makes every run "fail". It is advisory: it exits 0 and no gate runs
  it. `/start-session` reports it, and `make bootstrap-check` turns a warning into a `[warn]`.

**`v6.4`**
- `CLAUDE.md` is a one-line file, `@AGENTS.md`, not a symlink: on Windows the symlink checked out as
  a 9-byte text file and Claude Code loaded no house rules. `conformance/test-claude-md.py` accepts
  that line or a symlink to `AGENTS.md`, nothing else — rules of your own in `CLAUDE.md` move into
  `AGENTS.md` §1–§2 before you take the new file.
- The post-edit hook runs `make check-fast`: the legs of `make check`, derived from its own line,
  side by side, every failing one named. `make check` stays serial and remains the merge gate. The
  tests run in parallel there (pytest-xdist, installed by `make install`): mark a test that must not
  run beside another — a shared database, a port, a rate-limited API — with
  `@pytest.mark.xdist_group("serial")`.
- `.devflow-stack` names the product's stack; it ships as `python`, which behaves as before. Any
  other stack binds lint, typecheck, test and deps in a `stack.mk` of its own (`INSTALL.md`), and an
  unbound leg fails with `BIND ME:`.
- A `scripts/check_fast.py` of your own, written before this version shipped one, fails
  `conformance/test-check-fast.py` until it answers `--plan`: take DevFlow's file, and move your own
  legs to `stack.mk` (`CHECK_FAST_OWN_LEGS`, `CHECK_FAST_FORMS` — the `v6.5` entry above).
- The hooks refuse when they cannot work: with no working `python3` or `python`, both guards block
  every call they guard instead of letting it through, and without `make` the post-edit hook says
  `make` is not installed.
- UTF-8 everywhere: the Makefile exports `PYTHONUTF8=1`, `.claude/settings.json` sets it for the
  hooks, and DevFlow's Python states `encoding="utf-8"` on every text read and write, held there by
  `conformance/test-text-encoding.py`. A non-UTF-8 console (cp1254, cp1252) no longer breaks a check.
- Two gates got stricter. `make bootstrap-check` fails a clone without `make hooks` unless the brief
  records that both GitHub Actions and branch protection work here. The commit-identity check fails
  a commit authored or committed by a known AI tool's address, whoever else is in the history.
- Installing, on Windows or macOS / Linux, and into an existing repository, is in `INSTALL.md`.

**`v6.3`**
- METHODOLOGY.md no longer ships. The method is `AGENTS.md` (the stage model), the skills,
  `docs/closure-checklist.md`, `pipeline-schema.html`, `docs/security-baseline.md` and
  `.agents/rules/practices.md`.
- The pre-commit configuration and the `governance-contract` workflow no longer ship. The local
  gate is `.githooks/pre-push` (`make hooks`, which also stops an earlier `pre-commit` hook from
  running). The required CI checks are the jobs listed in `docs/branch-protection.md`: if branch
  protection still requires `governance-contract`, remove it, or every pull request waits for a
  check that never reports.
- A skipped or bypassed control is one row in `docs/control-events.csv`, the only ledger a gate
  counts. Automated commits carry `gp-agent <gp-agent@users.noreply.github.com>`.
- The release security review writes its verdict to `docs/reviews/release-security.md`.

**`v6.2`**
- `/setup-project` asks the setup choices once and records them in `docs/project-brief.md`.
- `.githooks/pre-push` and `make hooks`: `make gate` runs before every push.
- Earlier records are graded by the version they declare, and paths quoted in records count as
  history (below).
- The commit-identity check grades what the branch adds, against everyone with a commit on the
  default branch plus the developer — a teammate's merged commits no longer fail it.

**`v6.1`**
- Nothing deploys at a milestone close. Stage 5 Release runs once, at the end: the security review
  (BLOCKING), then deploy and `/going-live`, then an optional retrospective. Maintenance is Stage 6.
- The milestone Quality Gate is optional and **off by default**. A project that relied on it turns
  it on in `docs/project-brief.md`.
- No handovers and no per-milestone retrospectives: `docs/handovers/`, `docs/retrospectives/` and
  note.txt are gone. `/cycle-close` is the optional retrospective at the end of the work; session
  state lives in `docs/process-log.md`.

**`v6.0.1`**
- The guards in `.claude/settings.json` block (they exit 2); before, a refused call still ran.
- `/plan-milestone` turns a plan into waves and one issue per unit of work; `/close-wave` runs
  Code-Reviewer, then Tester, on every wave, and `make wave-check` refuses a close without both
  review files, or with a BLOCKING one.
- `make labels` creates the issue labels; the subagents live in `.claude/agents/`; `make closes`
  runs inside `make check`.

## What you do not have to rewrite

- **Earlier records are graded by the rules of the version they declare.** A wave close written
  under an earlier version is not asked for fields that came later, and a record that declares no
  version is graded as history.
- **Paths quoted in records** — reviews, wave closes, closure reports, decisions — that no longer
  exist are counted as history, not failed. Records are evidence of what was true when written.
  Live documents (README, AGENTS.md, the rules, the templates, the skills) are still graded
  strictly.
