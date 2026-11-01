# Issues, labels and the verification pipeline

The skills **implement** this file: change it here and the skills follow, never the other way round.

## The one load-bearing rule

**The agent opens drafts; a human marks them ready and merges** (`AGENTS.md` §3, "Git authority";
the integration lane does not bend it). Everything below is downstream of it: the skills stop where
it stops them, and the gates exist because the human merging cannot read every line.

## Two working modes — the brief's `Working mode:`

**Light** (`/setup-project`'s default; a small product, one person merging): the issue skills run the
work — `/file-issue` → `/triage-issue` → `/fix-issue` or `/work-enhancement` — each a red test, the
change, `make gate`, one draft PR. **Heavy** (what a brief without a `Working mode:` line reads as):
the same issue skills, and waves on top. **A wave is one container issue plus its children** —
`/plan-milestone` opens it, `/close-wave` closes it; `/fix-issue` is a one-issue wave. Several slices
route to `wave`, never to `/work-enhancement`. `make mode` prints which; the owner chooses it in
`/setup-project`, and nothing switches it by itself.

**Who reviews, and when.** This table is the one statement of it; every other file points here.
`make review-need` computes the per-change rows, and the gates refuse a close or a deploy without the
rest.

| Review | Light | Heavy |
|---|---|---|
| Code-Reviewer | never | every wave (`/close-wave`) and a fix `make review-need` routes to it; the last wave's also reads the whole milestone |
| Security-Reviewer, per change | a change touching the brief's declared HIGH paths; its other signals wait for the release review | none — each range's signals are printed for the milestone review |
| Security-Reviewer, per milestone | — | once, on the plan's last wave, over the whole milestone (`docs/reviews/m<N>-security.md`) |
| milestone Tester | once per milestone, closed before a release, on everything merged since its last verdict (`docs/reviews/release-tester.md`) | once, on the plan's last wave (`docs/reviews/m<N>-tester.md`) |
| release and deploy | the Security-Reviewer on the whole release (`/going-live`); before every deploy, a delta since each verdict's reviewed head (the deploy gate) | the same; a current milestone security verdict stands for the release's |

**A run**, in either mode, is the owner's unattended lane, opened only by the owner: `/plan-run`.

## Where a finding goes — one queue, the issue list

An issue is where work waits. A review file, a ledger row or a process log records *why*; none of
them is a queue, because no lane reads them.

| Found | Goes | Skill |
|---|---|---|
| in the wave's own code, fixed before the wave closes | nowhere else — the wave fixes it | `/close-wave` |
| in a review, not fixed in the wave or the fix (MINOR, K.9, a queued risk) | an issue: `bug` + severity, or `enhancement` | `/close-wave` or `/fix-issue`, step 6 → `/file-issue` |
| outside what you are doing, any time | an issue | `/file-issue` |
| a failure still red after three attempts | a `bug` listing the three attempts | `.agents/rules/practices.md` → `/file-issue` |
| a finding still BLOCKING after the reviewer's third round | a `bug` for the reverted slice (wave), or the issue back to triage as `work-issue` (fix); the owner answers with an ADR or a `docs/refusals.md` row | `/close-wave` step 3 · `/fix-issue` step 6 |
| across the whole milestone, on its last wave | an issue, or a fix on that wave's branch | the last wave's Code-Reviewer (`/close-wave`) |

**Every filed issue is triaged** before anyone works it: `/file-issue` hands it to
`/triage-issue`, whose last line — `Triage verdict: …` — is the routing every lane checks.
`/plan-milestone` reads the open queue, so an enhancement nobody takes now reaches the next plan.
A bug the wave fixed before it merged gets no issue: an issue for code that never shipped is noise.

## The label vocabulary — and it is closed

Five groups, the whole set; `make labels` creates the missing ones once per repository. **Use one
that already exists.** If a new one is genuinely needed, ask before a skill relies on it: *a skill
keying on a label nobody created fails silently.*

| Group | Labels |
|---|---|
| **Type** | `bug` · `enhancement` · `documentation` · `question` · `duplicate` · `invalid` · `wontfix` · `good first issue` · `help wanted` |
| **Severity** | `severity:critical` · `severity:high` · `severity:medium` · `severity:low` |
| **Gate** (CI only) | `agent:triage` · `agent:fix` |
| **Verification** | `dev:done` · `qa:ready` · `qa:passed` · `qa:failed` · `qa:blocked` |
| **Scope** | `out-of-scope` |

**Gate:** the CI issue agent's two traps are in `.agents/rules/ci-traps.md`.

**Severity:** exactly one on a `bug`, chosen by **measured impact**, never the reporter's urgency.
It stays for the issue's whole life, after it closes too. Non-bug issues carry none.

**`out-of-scope`:** deliberately outside this release, by the owner's decision. The issue **stays
open** and keeps its type and severity: a deferral, not a rejection (`wontfix` means *never*);
removing the label puts it back in the queue. Applied only after triage, only on the owner's word,
carries no QA meaning, and never sits beside a `dev:`/`qa:` label.

**Area labels are deliberately absent:** *which component?* belongs in the diagnosis comment.

## The verification pipeline — only when `QA verification: on`

**Off, the default: a bug closes when its fix merges**, and the test that went red before the fix
and green after is its verification — the PR says `Closes #<n>`.

**On** — a person verifies on a deployed build: `.agents/rules/issues-qa.md`, read only then.

## What a skill never does

Anything `AGENTS.md` §3, "Git authority", forbids the agent — interactively **and** in CI.
