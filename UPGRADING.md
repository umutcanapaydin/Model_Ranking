# Upgrading an existing project

Your project runs an earlier DevFlow — or the General Pipeline it grew out of — and a new version
ships. **Never copy the new tree over yours:** a copy deletes the controls your project grew and
silently overwrites any file of yours that the new version happens to ship under the same name.
Apply the *difference* between the version you installed and the new one, three-way, so your
changes survive and every collision is shown to you.

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

**Then start a new session.** `make session-check` cannot pass in the session that installs or
upgrades the SessionStart hook: the hook did not exist when the session began, so it wrote no marker
for it. In the field this produced skip rows in `docs/control-events.csv` and, in one project, the
three-skips lock. Do not record a skip for it: the leg stays red in this session by construction,
every other leg of `make check` and `make gate` is run by name for the upgrade PR, and the first
session started from the repository root after the merge passes it. **Push the upgrade branch from a
terminal outside Claude Code:** the pre-push hook runs `make gate`, whose first leg is that session
check, and outside a Claude Code session it has nothing to check and passes. The post-edit hook
reports the same red leg after every edit in the upgrade session; that is the same cause.

**An upgraded project writing its first brief:** `/setup-project` reads `.gp/installed` at the new
version and no brief — that is not another upgrade; answer the questions.

## What changed for you

Read every entry newer than the version you had. Older than `v6.0.1`: compare the old and the new
`AGENTS.md` side by side after the upgrade.

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
  the tag — `git checkout <tag> -- conformance/wave conformance/reviews conformance/closure
  conformance/run` — and delete any old-named copies; `conformance/test-fixture-ids.py` refuses a
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
