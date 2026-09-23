---
name: setup-project
description: Use once, when DevFlow is being installed into a project — a brand-new one or an existing one — before any code or plan. Asks the owner the setup questions, each with what it decides and its default, records the answers in docs/project-brief.md, and routes an existing project to the right path. Also when the owner asks to revisit those choices.
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
   that never used DevFlow — it is adopted: `docs/codex-audit.md` records what exists before any
   wave changes it. Default, derived from §1 — say which fact decided it: a recorded install version
   (`.gp/installed`, or the project's own DevFlow records) → upgrade; code beyond the starter →
   adopted; otherwise new.
2. **Milestone Quality Gate — off (default) or on?** On: every milestone close also writes a closure
   report (`docs/closure-report.template.md`) with the REQ-ID trace, coverage delta and token cost,
   and `make closes` grades it. Off: a milestone closes on its merged waves; each wave's Tester
   already requires a citing test for every criterion it touched. On costs time at every close; turn
   it on for customer-facing or regulated work.
3. **A retrospective when the work is done — no (default) or yes?** One short file at the very end
   (`/cycle-close`): what went right, where we got stuck, which controls earned their place. Never
   during the work.
4. **Which HIGH-risk areas does this project touch?** Authentication, payments, personal data,
   cryptography, irreversible migrations, regulated compliance, production deploy automation — or
   none. A wave touching one is HIGH: it also gets a security pass, and a named senior human
   reviews it. Default: none, until the first one appears.
5. **Who is the senior human reviewer for those areas?** A name and a contact. Default: the owner.
6. **Does the work end in a deploy, and where?** It decides whether Stage 5 (security review, then
   `/going-live`) applies and what it checks against. Default: decided at the first release.
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

The owner may answer "defaults" to any or all. Never invent an answer: an unanswered question takes
its default, written down as the default.

## 3 · Record and act

- Write the answers into `docs/project-brief.md` (copy `docs/project-brief.template.md` if it does
  not exist): every answer in its field, each default marked as one. Question 7's two lines keep the
  template's wording, with the placeholder replaced by the bare word `yes` or `no`:
  `GitHub Actions run here:` and `The default branch can be protected:`. `make bootstrap-check`
  reads them, and anything but `yes` counts as `no`.
- Question 9: write the stack, one line, to `.devflow-stack`. For a product in another language,
  add each path the owner names to `.language-allow`, one row each, with the reason:
  `design/   # the product's UI copy is Turkish; the design files quote it as it ships`.
- Commit these on a branch and open a draft PR; the owner merging it is the owner signing the
  choices. Without `gh`, push the branch and hand the owner the compare URL —
  `https://github.com/<owner>/<repo>/compare/<default-branch>...<branch>?expand=1` — to open it as
  a draft.
- Brand-new or adopted: the common steps in `INSTALL.md`, from naming the project in
  `pyproject.toml` to `make bootstrap-check`, in order, then `/plan-milestone`. Without `gh`,
  `make labels` prints the labels to create by hand and exits 2: hand the owner that table.
- An upgrade: `UPGRADING.md`, and nothing else from this list until it is done.
- A choice changes later: update the brief the same way. It is the one place the next agent reads.
