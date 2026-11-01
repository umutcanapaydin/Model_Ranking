---
name: start-session
description: Use at the start of every session — new, resumed, or after a compaction — before any change, and whenever asked where things stand, what happened last, what waits for the owner, or what to pick up.
---

**Continuity is a property of files, not of sessions:** do not reconstruct state, read it.

0. **`make doctor` first** — one line per check, by id. **A `session` FAIL: stop — tell the owner
   that no hook, profile or skill is registered in this session, and that it must be restarted from
   the repository root.** Do not ledger a skip row and carry on; one project ran 313 hours that way.
   The session that merged an install or upgrade cannot pass: after that merge, start a new one. Act
   on every other `warn` or `fail` line as it says. Then say the `mode`: **light** runs issues only;
   **heavy** runs waves as well (`.agents/rules/issues.md`, "Two working modes"). Every lane below
   follows it.
1. **Read where the work stands** — `make standup` (what needs the owner, the latest process-log
   entry, the ADRs awaiting a merge, the plans, the git state), then the current
   `docs/plans/m{N}-plan.md` (heavy; light has none — the triaged queue is its plan). **A `run` line
   naming an open run file means a run is in progress:** resume it (`/plan-run` §3.4): the `running`
   row names the wave branch — check it out, it exists, with the commits so far — unless the owner is
   here and says otherwise. A process log silent about the last session is the first thing missing.
2. **Confirm which tree you are in.** Stale clones of the same remotes diverge; read an archive as
   an archive, never commit in it.
3. **Read the rules** — `.agents/rules/practices.md` and `issues.md`, then the stack's own notes
   if the project keeps them (the brief or `environment.md` names them) — from the files, not from
   memory. `playbook-seeds.md` is reference: open it when a rule cites a seed.
4. **`git status` and the last ten commits.** The default branch should be clean.
5. **Run `make check-fast` and `make closes` once, before changing anything** — not the full gate: its network legs grade the
   manifest, not your change, and the push runs them. Without it you cannot tell "I broke this" from
   "this was already red". Run them by name and keep the output.
6. **Look at the live queue** — open issues, and one issue's full history with comments, to see the
   label flow as practised. Name every
   open issue with no `Triage verdict:` line in its body or its comments: no lane picks one up, so it is
   triaged (`/triage-issue`) before new work starts — and every one carrying `qa:failed` or
   `qa:blocked`, which goes back to triage the same way.
7. **For anything the code does not explain**, read the decision log, then the archive.

## When you run a state dump

Show the tool's output **raw** — never paraphrased, summarised or tidied. Add exactly one sentence
afterwards: which item most warrants attention, and why.

## What you have when this is done

You know what green looks like, what is open, what was deliberately left, and which tree is real;
what to do comes from the issue. And everything after it: **you open the draft; a human merges.**
