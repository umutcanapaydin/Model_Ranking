---
name: plan-milestone
description: Use at the start of every milestone (Stage 1), when designs or requirements arrive and the work must be split into waves and tracked as issues. Writes docs/plans/m<N>-plan.md, splits it into waves, and makes sure every unit of work has exactly one GitHub issue — reusing an existing one untouched, creating it only when none exists.
---

1. Read `docs/prd.md` (the REQ-IDs), the design notes you were given, `docs/decisions.md` and the
   latest `docs/process-log.md` entry. Ask for what is missing rather than inventing it.
2. Write `docs/plans/m<N>-plan.md` with these sections: goal, REQ-ID acceptance criteria, risk
   tier, spike check (does any part need a throwaway `spike-*` branch?), **waves** (each wave: its
   REQ-IDs, its risk tier, tasks of ≤5 minutes of subagent scope), K.8 contracts with pasted
   `grep -n` output, token budget, issue inventory, closure tasks, and the security globs (the
   paths that make a wave HIGH). MED/HIGH: one alternative approach and its trade-offs. The
   acceptance criteria are frozen when the owner merges the plan; a later change is a plan
   amendment, never a silent edit.
3. **The GitHub milestone.** `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`. If
   `M<N>` is not there, create it:
   `gh api -X POST repos/{owner}/{repo}/milestones -f title='M<N>: <goal>'`.
4. **One issue per unit of work, never two.** For each row of the issue inventory, search first,
   open and closed:
   `gh issue list --state all --search '<key words> in:title' --json number,title,state,milestone`
   - **A match exists** → write its number into the inventory and **leave the issue exactly as it
     is**: no edited body, no new label, no milestone change, no comment. If it looks wrong for
     this plan, say so to the owner; do not fix it yourself.
   - **Nothing matches** → create it:
     `gh issue create --title '<title>' --body '<REQ-IDs · wave · acceptance criteria>' --milestone 'M<N>: <goal>' --label enhancement`
     (a `bug` gets `--label bug` and exactly one `severity:*`). Only labels from
     `.agents/rules/issues.md` — `make labels` creates them once per repository.
   - Unsure whether two titles are the same work → ask. A duplicate costs more than a question.
5. Write every issue number into the plan. The plan is the map from wave to issue; `/close-wave`
   reads it to list the issues each wave's PR resolves.
6. Branch `plan/m<N>`, commit the plan (`git add` the plan file by path), push the branch, open a
   **draft** PR. **The owner approves the plan by merging it** — no wave is dispatched before
   that. No AI attribution.
7. After the merge: each wave runs on its own `wave/m<N>-w<W>` branch from the default branch and
   ends with `/close-wave`.
