---
name: plan-milestone
description: Use in HEAVY mode at the start of every milestone, when designs or requirements arrive and the work must be split into waves and tracked as issues.
---

**Heavy mode only.** `make mode` prints `light` → stop: a light project plans in its issues, one
`/fix-issue` or `/work-enhancement` at a time.

**A wave is one container issue plus its children.** The container holds the wave's plan — its
REQ-IDs, risk tier and tasks as a checklist — in its body; the children are the filed issues the
wave takes on, so the queue is part of the plan.

1. Read `docs/prd.md` (the REQ-IDs), the design notes you were given, `docs/decisions.md` and the
   latest `docs/process-log.md` entry. Ask for what is missing rather than inventing it.
2. Copy `docs/plan.template.md` to `docs/plans/m<N>-plan.md` and fill it — its `waves: <n>` line is how
   `make wave-check` knows the plan's last wave. Its sections: goal, REQ-ID acceptance criteria, risk
   tier, spike check (does any part need a throwaway `spike-*` branch? It is exempt from every gate but
   secrets scanning and NEVER merged — `docs/closure-checklist.md` §B.2 checks `git log`; to keep
   its result, rebuild it through the pipeline), **waves** (each wave: its
   REQ-IDs, its risk tier, tasks of ≤5 minutes of subagent scope), K.8 contracts with pasted
   `grep -n` output, token budget, issue inventory, closure tasks, and the security globs as one
   machine-readable line — `security-globs: <glob>, <glob>` or `security-globs: none` —
   which `make review-need` reads alongside the brief's `Paths that make a change HIGH:`. MED/HIGH: one alternative approach and its trade-offs. The
   acceptance criteria are frozen when the owner merges the plan; a later change is a plan
   amendment, never a silent edit.
3. **The GitHub milestone.** `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`. If
   `M<N>` is not there, create it:
   `gh api -X POST repos/{owner}/{repo}/milestones -f title='M<N>: <goal>'`.
4. **Read the open queue first**: `gh issue list --state open --json number,title,labels,milestone`.
   Every open issue — what earlier waves filed, what triage routed — either joins this plan's
   issue inventory or is named in the plan as left out, with the reason. Joining means its number
   is written into the plan; the issue itself is left as it is (step 5). An `out-of-scope` issue
   joins only after the owner lifts that label (`.agents/rules/issues.md`).
5. **One issue per unit of work, never two.** For each row of the issue inventory, search first,
   open and closed:
   `gh issue list --state all --search '<key words> in:title' --json number,title,state,milestone`
   - **A match exists** → write its number into the inventory and **leave the issue as it is** — no
     edited body, no new label, no milestone change — with one comment, its new routing:
     `Triage verdict: wave (M<N>-W<W>, #<container>)`, so `/fix-issue` and the CI agent leave it to its
     wave (the last verdict line wins). If it looks wrong for
     this plan, say so to the owner; do not fix it yourself.
   - **Nothing matches** → create it:
     `gh issue create --title '<title>' --body '<REQ-IDs · wave · acceptance criteria>' --milestone 'M<N>: <goal>' --label enhancement`
     (a `bug` gets `--label bug` and exactly one `severity:*`). Only labels from
     `.agents/rules/issues.md` — `make labels` creates them once per repository.
   - **Each wave gets its container issue**, created the same way — title `M<N>-W<W>: <goal>`,
     label `enhancement` — whose body is the wave's plan: REQ-IDs, risk tier, the tasks as a
     `- [ ]` checklist, and `Includes: #<child>, #<child>` for the queue's issues this wave takes.
     A child is named in the container; the child itself is left as it is.
   - Every issue this step creates — children and containers — ends its body with the line
     `Triage verdict: wave`: the plan triaged it, and `/fix-issue` leaves wave work to its wave.
   - Unsure whether two titles are the same work → ask: a duplicate costs more than a question.
6. Write every issue number into the plan: each wave's container and its children. The plan is
   the map from wave to issues; `/close-wave` reads it to list what the wave's PR resolves. A plan
   amendment is an appended row in the plan and, for a new unit, a new child in its container.
7. Branch `plan/m<N>`, commit the plan (`git add` the plan file by path), push the branch, open a
   **draft** PR. **The owner approves the plan by merging it** — no wave is dispatched before
   that. No AI attribution. Run `/pre-merge` (a plan PR owes no review: §5).
8. After the merge: each wave runs on its own `wave/m<N>-w<W>` branch from the default branch and
   ends with `/close-wave`.
9. **Inside a run** (`/plan-run`, only when the owner opened one): steps 1–6 per milestone, two to
   five of them; the plans commit on the run's `plan/run-<name>` branch, the owner's answers to the
   run's one decisions message start the waves, and the plan PR's merge comes in the morning.
