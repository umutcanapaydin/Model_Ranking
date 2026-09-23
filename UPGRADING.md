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
- **Files the new version removed that you had changed** stay as conflicts: keep them as your own
  files or delete them. That is your decision, not the upgrade's.
- **Seed documents the project has filled** — `docs/decisions.md`, `docs/refusals.md`,
  `docs/watchlist.md` — are yours: where the new seed differs, keep your content.

## 4 · Then, as for any change

`make install` · `make hooks` (once per clone: it turns on the pre-push gate) · `make labels` ·
`make check` · `make gate` — all green — then one draft PR for the whole upgrade. A human merges.
If the project has no `docs/project-brief.md` yet, run `/setup-project` afterwards: the choices it
records decide how the new version runs.

## What changed for you

Read every entry newer than the version you had. Older than `v6.0.1`: compare the old and the new
`AGENTS.md` side by side after the upgrade.

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
  reader over block mappings where it is not, so it grades on every machine.
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
  version is graded by today's rules.
- **Paths quoted in records** — reviews, wave closes, closure reports, decisions — that no longer
  exist are counted as history, not failed. Records are evidence of what was true when written.
  Live documents (README, AGENTS.md, the rules, the templates, the skills) are still graded
  strictly.
