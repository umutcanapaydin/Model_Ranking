---
name: setup-project
description: Use once, when DevFlow is installed into a new or existing project, before any code or plan; also when the owner revisits the setup choices or upgrades DevFlow.
---

The choices below change how every later stage runs. Ask them once, up front, with the reason for
each — an agent that guesses them has made the owner's decisions for them.

## 1 · Read first, so you only ask what the repository cannot tell you

`pyproject.toml` (project name), `git remote -v` (host), `git config user.email` (whose commits are
the owner's), `.devflow-stack` (the stack recorded so far), and whether `gh` is installed
(`command -v gh`). Is this tree already on some version: `.gp/installed`, or the project's own
DevFlow records — a milestone plan in `docs/plans/`, an ADR from D-100 on. Does it hold code beyond
the starter, and in which language. Do not ask what you just read — state it and let the owner
correct it.

## 2 · Ask, in ONE message, numbered, each with what it decides and its default

1. **Where are we starting?**
   (a) a brand-new project · (b) an existing project that already runs an earlier DevFlow or General
   Pipeline — that is an **upgrade**: stop here and follow `UPGRADING.md` · (c) an existing codebase
   that never used DevFlow — it is adopted: `docs/adoption-audit.md` records what exists before any
   wave changes it. Default, derived from §1 — say which fact decided it: a recorded install version
   (`.gp/installed`, or the project's own DevFlow records) → upgrade; code beyond the starter →
   adopted; otherwise new. One exception: `.gp/installed` already at this version and no brief yet is
   an upgraded project writing its first brief — not another upgrade; ask on.
2. **Milestone Quality Gate — off (default) or on?** *(Heavy mode only — a project answering light to
   question 10 skips it.)* On: every milestone close also writes a closure
   report (`docs/closure-report.template.md`) with the REQ-ID trace, coverage delta and token cost,
   and `make closes` grades it. Off: a milestone closes on its merged waves; the milestone Tester
   already requires a citing test for every criterion. On costs time at every close; turn it on for
   customer-facing or regulated work. Heavy mode only (question 10): a light project has no
   plans and no closure report, and this stays `off`.
3. **A retrospective when the work is done — no (default) or yes?** One short file at the very end
   (`/cycle-close`): what went right, where we got stuck, which controls earned their place. Never
   during the work.
4. **Which HIGH-risk areas does this project touch?** Authentication, payments, personal data,
   cryptography, irreversible migrations, regulated compliance, production deploy automation — or
   none — and the paths that hold them, as globs (`src/auth/**, migrations/**`): `make review-need`
   reads them — light mode sends a change touching one to the Security-Reviewer, heavy mode names
   its signals to the milestone Security-Reviewer on the plan's last wave. Does the project wrap or
   fork an OSS engine (it makes `docs/license-review.md` required)? Default: none, until the first
   one appears.
5. **Who is the senior human reviewer for those areas?** A name and a contact. Default: the owner.
6. **Does the work end in a deploy, and where — and which commands deploy?** The commands (`fly
   deploy`, `./ios/install.sh`, `devicectl device install`) are what the deploy gate guards: each is
   refused until a security review, and the milestone Tester, have seen every code change since their reviewed heads. Default:
   decided at the first deploy; until then none is guarded. Also ask which files the deploy reads
   that git does not track (a gitignored plist, `.env.production`, a signing profile): the brief's
   `Runtime config files:` line, which `/going-live` opens before a deploy because no git-based
   gate can see them. Default: `none`. And how a deploy is undone — the brief's `Rollback command:`,
   which `/going-live` runs when a deploy fails. Default: `none`, with the reason.
7. **What can this repository enforce by itself?** Can it run GitHub Actions (a private repository
   on a free plan may have no minutes), and can the default branch be protected? If not, the gate on
   each developer's machine is the only enforcement: `make hooks` makes it run before every push, and
   `make bootstrap-check` fails a clone without it. Default: assume neither until someone checks.
8. **The CI issue agent — no (default) or yes?** A labelled issue triggers a headless agent that
   comments or opens a draft PR. It needs Actions and an API key in the repository secrets.
9. **The product: its stack (`python` default, or the name you bind in `stack.mk`) and the language
   of its user-facing copy (English default).** The stack decides what `make lint`,
   `make typecheck`, `make test` and `make deps` run; any stack but `python` binds its legs in
   `stack.mk` (`INSTALL.md`, "Binding another stack"), and an unbound leg fails. The repository
   stays English; a product in another language names the paths that hold its copy — design files,
   localisation strings — so the English-only rule does not refuse them.

10. **The working mode — light (default) or heavy?** Light: issues only — file, triage, fix; a red
    test, the change, `make gate`, one draft PR; no Code-Reviewer; the Security-Reviewer when a
    change needs it and before every deploy; the milestone Tester once before each release, on
    everything merged since its last verdict. For a small product one person merges. Heavy: waves as well — `/plan-milestone`, a Code-Reviewer per wave, the Tester
    and the Security-Reviewer once per milestone, on the plan's last wave. Switching later is a brief change; nothing switches it by itself.
11. **QA verification — off (default) or on?** Off: a bug closes when its fix merges, its red→green
    test the verification. On: a person verifies on a deployed build and the `qa:` labels track it
    (`.agents/rules/issues.md`).
12. **Which model do the reviewers run on?** Default: the session's own (no `model:` line). A
    smaller one (`sonnet`) for the Code-Reviewer, the Tester and the Explorer saves the token budget —
    two field projects set it by hand; the Security-Reviewer stays on the session's model unless the
    owner names one for it too.

The owner may answer "defaults" to any or all. Never invent an answer: an unanswered question takes
its default, written down as the default.

## 3 · Record and act

- Write the answers into `docs/project-brief.md` (copy `docs/project-brief.template.md` if it does
  not exist): every answer in its field, each default marked as one. Question 7's three lines keep the
  template's wording, with the placeholder replaced by the bare word `yes` or `no`:
  `GitHub Actions run here:`, `The default branch can be protected:` and `make hooks installed in
  every clone`. `make bootstrap-check` reads the first two, and anything but `yes` counts as `no`.
  Four more lines are read by `scripts/brief_fields.py` and two by `/going-live`, so they too keep
  the template's wording with the placeholder
  replaced: `Working mode:` (`light` or `heavy`), `QA verification:` (`off` or `on`),
  `Deploy commands:`, `Runtime config files:`, `Rollback command:` and `Paths that make a change HIGH:` (`none`, or a
  comma-separated list).
- `docs/EXPERIENCE.md` ships in place: fill its header (the first entry is written at the first
  milestone close, or the first release in light mode). An adopted codebase (question 1c): copy
  `docs/adoption-audit.template.md` to `docs/adoption-audit.md` and write it now — what exists, from `git ls-files` and one run of
  its tests, and which of it stays — before any issue is filed against it.
- The brief's `## 2.1 Repositories` table: one row per repository a customer reaches — this one from
  `git remote -v`, marked installed (`yes`); ask only about the others. `make bootstrap-check` C8
  fails while every row is a placeholder.
- Fill the project's own files, which `make bootstrap-check` C1/C3 read: `AGENTS.md` §1–§2, `docs/prd.md`
  (the requirements with their REQ-IDs), `docs/architecture.md`, the README's title, the `app` title in
  `src/app/adapter/main.py`, `.github/CODEOWNERS` (a one-person repository removes the lines naming
  other roles), and the `D-100` stub in `docs/decisions.md` (fill it or delete it). They ride on the
  setup branch.
- Question 12: a model other than the session's goes in as `model: <name>` in the frontmatter of each
  profile it covers (`.claude/agents/*.md`), and in the brief's `Reviewer model:` line.
- Question 9: write the stack, one line, to `.devflow-stack`. For a product in another language,
  add each path the owner names to `.language-allow`, one row each, with the reason:
  `design/   # the product's UI copy is Turkish; the design files quote it as it ships`.
- Commit these on a branch (`setup/devflow`) and open a draft PR, then run `/pre-merge`; the owner
  merging it is the owner signing the choices. Without `gh`, push the branch and hand the owner the compare URL —
  `https://github.com/<owner>/<repo>/compare/<default-branch>...<branch>?expand=1` — to open it as
  a draft.
- **After the owner merges an install or upgrade PR, start a new session from the repository
  root.** The session that installed the hooks predates them: `make session-check` cannot pass
  in it, and a skip row for that is noise (`/start-session`, step 0).
- Brand-new or adopted: the common steps in `INSTALL.md`, from naming the project in
  `pyproject.toml` to `make bootstrap-check`, in order, then the first work — heavy:
  `/plan-milestone`; light: `/file-issue` one issue per requirement in `docs/prd.md`, `/triage-issue` each, then the skill each verdict names. Without `gh`,
  `make labels` prints the labels to create by hand and exits 2: hand the owner that table.
- An upgrade: `UPGRADING.md`, and nothing else from this list until it is done — then the new
  session above. Run the upgrade's `make install` in the clone the owner works in too, not only in
  the temporary worktree the upgrade was made in: `.gp/installed` is gitignored, so every clone keeps
  its own marker, and the main clone stayed on v6.6 through three upgrades (#331).
- A choice changes later: update the brief the same way. It is the one place the next agent reads.
  A switch of working mode also re-triages the open issues whose verdict belongs to the other mode:
  light → heavy, a `work-enhancement` verdict; heavy → light, a `wave` verdict and the open
  container issues of an unfinished plan (their children go back to triage; the container closes
  as not planned).
