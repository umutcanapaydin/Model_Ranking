---
name: start-session
description: Use at the start of any session in an unfamiliar or resumed repository, and whenever asked where things stand, what happened last, or what to pick up. Also before touching anything in a repo you have not run today. Orients from files rather than memory, and establishes what green looks like here BEFORE changing anything.
---

**Continuity is a property of files, not of sessions.** Nothing carries between sessions except
what is written down. Treat that literally: do not reconstruct state, read it.

1. **Read the most recent handover.** It states which repositories, which heads, what merged, what
 was deliberately left open, and what is running in the background — and the answer to the last
 one should be "nothing". If there is no handover, that is the first thing this session is
 missing.
2. **Confirm which tree you are in.** Stale clones of the same remotes exist and their histories
 diverge; one project had two, whose decision log stopped eighteen entries behind the live one.
 Read an archive as an archive; never commit in it.
3. **Read the rules** — every file in `.agents/rules/`, then the entry document for the stack and
 its traps. From the files, not from what you remember about this project.
4. **`git status` and the last ten commits.** The default branch should be clean.
5. **Run the gates once, before changing anything.** This is the step that gets skipped and it is
 the one that pays: you cannot tell "I broke this" from "this was already red" unless you looked
 first. Run them by name and keep the output.
6. **Look at the live queue** — open issues, and one issue's full history including comments, to
 see the label flow as it is actually practised rather than as it is documented.
7. **For anything the code does not explain**, read the decision log, then the archive.

## When you run a state dump

Show the tool's output **raw**. Do not paraphrase it, do not summarise it, do not tidy it — a
state dump that has been through a narrator is no longer a state dump. Add exactly one sentence
afterwards: which item most warrants attention, and why.

## What you have when this is done

You know what green looks like, what is open, what was deliberately left, and which tree is real.
You do not yet know what to do — that comes from the issue, not from here.

And the rule that governs everything after it: **you open the draft; a human merges.**
