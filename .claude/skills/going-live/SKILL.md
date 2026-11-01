---
name: going-live
description: Use before any deploy, ship, release or publish command, in either mode, and before saying a change is deployed, live, shipped or ready for the customer, or demoing it. Also to verify a deploy, cut a release, or answer "is it out yet".
---

A green pipeline says the code compiles and the tests pass. It says nothing about the thing
that is running. Seven checks, each one a failure that reached a customer.

**The release lane.** A release's records ride on one branch, `release/<version>`, with its draft PR:
the release verdicts below, the release record (`docs/releases/<version>.md`, from
`docs/release.template.md`) and, in its body, the `make deploy-check` lines. The owner's merge is the
release's signature; the owner tags it and publishes it (`docs/owner-actions.md` carries the command).

**First, `make deploy-check`.** It asks, with no command, what the deploy gate asks of every
command the brief lists as `Deploy commands:`: is the security verdict
(`docs/reviews/release-security.md`) current for this checkout, and is the milestone Tester's —
`docs/reviews/release-tester.md` in light mode, the latest `docs/reviews/m<N>-tester.md` in heavy —
each with a `**Reviewed head:**` after which no code changed, working tree included. It prints one
line per verdict: paste both into the body of the pull request that carries the release verdicts.
A build only the team runs — an `internal` or `staging` class in the brief's `Deploy targets:` — owes the
Tester's verdict, the per-change security verdict `make review-need` asks for, and a line
`- <date>, <class>, <short HEAD>: <what changed> (unreleased)` in `docs/releases/unreleased.md`, not the
release security verdict: `make deploy-check TARGET=<class>`.
A `FAIL` means a review first, never a way round it — in this order, because the Tester may add tests
and a test can be code to the gate:

1. **The Tester** (`.claude/agents/Tester.md`, subagent type `tester`): light mode writes
   `docs/reviews/release-tester.md` over everything merged since its last `**Reviewed head:**` — on the
   first release, since the install commit; heavy mode's verdict is the release's last
   `docs/reviews/m<N>-tester.md`, and a stale one gets a delta over `<reviewed head>..HEAD`.
2. **Then the Security-Reviewer** (`.claude/agents/Security-Reviewer.md`, subagent type
   `security-reviewer`), at the Tester's head: the whole release when `docs/reviews/release-security.md`
   does not exist yet, else the delta since its reviewed head. Give it the signals `make review-need
   RANGE=<its range>` prints as its starting list: in light mode the ones that touched no declared
   HIGH path were never reviewed per change. Hand it the four gate lines (`make secrets`, `deps`, `slopsquat`, `conformance`) from the last `make gate`, not the whole log.
3. Commit both verdicts together: a security verdict without a Tester verdict turns `make closes`
   red. A BLOCKING from either → `/fix-issue`; nothing deploys. This is the one question that reaches a deploy
the Bash guard never sees: the owner's own terminal, a dashboard, a TestFlight upload. The deploy
command itself is refused by the same gate while either verdict is stale.

**Then, what git cannot see.** The gate compares the tree git tracks; a gitignored runtime config —
a plist of backend hosts, a `.env`, a values file — decides where the build's users go and ships
with no gate reading it. The brief's `Runtime config files:` line names every such file (`none`, or
a comma-separated list; add the line under question 6 if the brief predates it). Read each one
before the deploy: it exists; it names the target environment's hosts, not a placeholder or
localhost; it carries a key of the kind the client may ship, never a privileged one. Print what you
read (hosts and the kind of key, never the key) beside the `deploy-check` lines.

## 1 · Built is not wired

Every guard, limit and enforcement built this cycle must be reachable from the live request path,
proven by an end-to-end call — not by the component existing and being unit-tested.

Measured in five projects. The worked example: a prepaid-wallet guard, fully unit-tested, never
wired into the serving route.

## 2 · Which build is actually live?

The running app must be able to say what it is. Bake the image tag or git SHA in at build time
and surface it — one request should answer "which release is this?" (`curl <target>/health | jq .build`
equals the tag or SHA you meant to ship). Restart is not rebuild, and
an artefact rebuilt on disk while the process serves the previous inode is a thing that has
happened here.

## 3 · Every dependency, invoked once, for real

Call each external dependency — model, queue, store, callback — and inspect the result. Not the
config screen, not the health page's opinion of it. A dead dependency has passed a deploy here.
`make smoke-deps` runs the project's own script that does exactly this.

## 4 · Config reaches the process

Read each critical value back from INSIDE the running process. "Set in the values file" and "the
process sees it" are different sentences with an injection layer between them.

## 5 · One walkthrough at human speed

Drive the real human path end to end, as a person would, on the deployed thing. Five distinct
root causes reached the customer through this gap in one project, and the one that found them was
a partner's DevOps engineer reporting an SSO login failure. `make journey URL=<deployed>` runs the
project's recorded walkthrough against the deployed URL.

An automated tester that mints its own token is not the human path.

## 6 · Full regression, once, on the exact bundle

Not on the branch, not on a rebuild — on the artefact that is going out.

## 7 · Readiness must be able to say no

A health endpoint that returns 200 with the database absent is not a readiness probe, it is a
decoration. Check that it fails when the thing it reports on is broken: `make cold-start` boots the
real artefact against zero persisted state.

A target whose script the project has not written fails closed. The only two outs are written down
(`docs/closure-checklist.md` §E.2): a ledgered waiver row in `docs/control-events.csv`, or a written N/A
when the release ships no runnable surface at all.

## A hotfix — one fix after a release

`/fix-issue`, then the deploy gate's deltas (the Security-Reviewer and the Tester on `<reviewed
head>..HEAD`), then §2 and §3 above on the deployed build. A fixpack (`docs/fixpack.template.md`) is
for more than one fix shipped together, or a fix on a HIGH path — not for one ordinary fix.

## If the deploy fails

Run the brief's `Rollback command:` (it says `none` with the reason when there is none), read §2 back
to confirm the previous build is what runs, `/file-issue` the failure as a `bug` with its severity by
impact, and write what happened under the release record's "Rollback". Nothing is retried until that
issue's fix has its own red test.

## After the deploy: the release record

Fill `docs/releases/<version>.md` on the release branch: behaviour, not commits; the database line;
the dependency line; the verdicts and their heads. Then add the owner's step to
`docs/owner-actions.md` — `git tag -a <version> <sha> -m "<version>" && git push origin <version> &&
gh release create <version> --notes-file docs/releases/<version>.md` — and say it is there.

## Before you say it is live

State which of the seven you actually did and which you skipped, and paste the `make deploy-check`
lines and the runtime-config reading above them. A skipped one is a known risk with an owner, not an
omission — and "we will do it after the demo" has been said in this lineage before.
