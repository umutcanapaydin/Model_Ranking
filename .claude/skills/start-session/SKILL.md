---
name: start-session
description: Use at the start of every session — new, resumed, or after a compaction — before any change, and whenever asked where things stand, what happened last, what waits for the owner, or what to pick up.
---

**Continuity is a property of files, not of sessions.** Nothing carries between sessions except
what is written down. Treat that literally: do not reconstruct state, read it.

0. **`make session-check` first.** Claude Code loads this repository's guards, post-edit check,
   agent profiles and skills only when it was started in the repository root; started one level
   up, or from the home directory, they are all off and nothing else says so — a skill invocation
   answers "Unknown skill", a reviewer dispatches as a plain subagent, no deploy is refused. If it reports
   the settings did not load, **stop: tell the owner that no hook, profile or skill is registered
   in this session, and that it must be restarted from the repository root.** Do not ledger a
   skip row and carry on; one project ran 313 hours that way. One session cannot pass by design:
   the one that merged the install or upgrade predates its own hook — after that merge, start a
   new session. If it reports no pre-push hook, run `make hooks`. If `.agents/rules/environment.md`
   does not exist, copy it from `.agents/rules/environment.md.template` and fill it (gitignored:
   your machine, not the project's). Then
   `make mode`, and say it: **light** runs issues only; **heavy** runs waves as well
   (`.agents/rules/issues.md`, "Two working modes"). Every lane below follows it.
1. **Read where the work stands** — `make standup` first (one call: the latest process-log entry, the
   ADRs awaiting a merge, the plans, the hooks, the git state); then the open rows of `docs/owner-actions.md` (say which wait for the
   owner), the latest `docs/process-log.md` entry, the current
   `docs/plans/m{N}-plan.md` (heavy; light has none — the triaged queue is its plan), the open
   draft PRs (`gh pr list --state open`), and `make deploy-check`: in light mode a `FAIL` on the
   Tester line says a release is owed its milestone Tester before it ships. Before the first release
   (no `docs/reviews/release-security.md` yet) it fails in either mode: report "no release yet", not a
   defect. **A run file
   `docs/plans/run-*.md` whose `Ended:` is `open` means a run is in progress:** `make run-check
   FILE=<that file>`, then resume it (`/plan-run` §3.4): the `running` row names the wave branch —
   check it out, it exists, with the commits so far — unless the owner is here and says otherwise. Nothing else
   carries between sessions; if the process log is silent about the last session, that is the
   first thing this session is missing.
   **Merged but not cleaned up:** `gh pr list --state merged --author @me --limit 20 --json
   number,headRefName` — a PR whose branch still exists on origin was merged with nobody told: run
   `/post-merge` for it now (a plan's first wave, a milestone close or a release may wait behind it).
2. **Confirm which tree you are in.** Stale clones of the same remotes exist and their histories
   diverge; one project had two, whose decision log stopped eighteen entries behind the live one.
   Read an archive as an archive; never commit in it.
3. **Read the rules** — `.agents/rules/practices.md` and `issues.md`, then the stack's own notes
   if the project keeps them (the brief or `environment.md` names them). `playbook-seeds.md` is reference: open it when a rule cites a seed. From the files, not from what you remember about this project.
4. **`git status` and the last ten commits.** The default branch should be clean.
5. **Run `make check` once, before changing anything** — not the full gate: its network legs grade the
   manifest, not your change, and the push runs them. This is the step that gets skipped and it is
   the one that pays: you cannot tell "I broke this" from "this was already red" unless you looked
   first. Run them by name and keep the output. Then `make ci-liveness`, and report its one line
   as it is. It is advisory and never fails. A `WARN` means the latest CI runs started no step (a
   billing or runner limit?), so the local gate and pre-push are all that gates a push: tell the
   owner.
6. **Look at the live queue** — open issues, and one issue's full history including comments, to
   see the label flow as it is actually practised rather than as it is documented. Name every
   open issue with no `Triage verdict:` line in its body or its comments: no lane picks one up, so it is
   triaged (`/triage-issue`) before new work starts — and every one carrying `qa:failed` or
   `qa:blocked`, which goes back to triage the same way.
7. **For anything the code does not explain**, read the decision log, then the archive.

## When you run a state dump

Show the tool's output **raw**. Do not paraphrase it, do not summarise it, do not tidy it — a
state dump that has been through a narrator is no longer a state dump. Add exactly one sentence
afterwards: which item most warrants attention, and why.

## What you have when this is done

You know what green looks like, what is open, what was deliberately left, and which tree is real.
You do not yet know what to do — that comes from the issue, not from here.

And the rule that governs everything after it: **you open the draft; a human merges.**
