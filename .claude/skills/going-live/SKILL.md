---
name: going-live
description: Use when asked to deploy, ship, release or publish — before running any deploy command, in either working mode — and before saying a change is deployed, shipped, live, delivered, or ready for the customer, and before a demo. Also when verifying a deploy, cutting a release, or answering "is it out yet". Covers what a green build does not prove: that the running thing is the built thing, that every dependency answers, that config arrived, and that a human path works end to end.
---

A green pipeline says the code compiles and the tests pass. It says nothing about the thing
that is running. Seven checks, each one a failure that reached a customer.

**First, `make deploy-check`.** It asks, with no command, what the deploy gate asks of every
command the brief lists as `Deploy commands:`: is the security verdict
(`docs/reviews/release-security.md`) current for this checkout, and is the milestone Tester's —
`docs/reviews/release-tester.md` in light mode, the latest `docs/reviews/m<N>-tester.md` in heavy —
each with a `**Reviewed head:**` after which no code changed, working tree included. It prints one
line per verdict: paste both into the release row of the closure checklist, and into the deploy
note. A `FAIL` means a delta review first — the Security-Reviewer on `<reviewed head>..HEAD`, the
Tester on the same range — never a way round it. This is the one question that reaches a deploy
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
and surface it — one request should answer "which release is this?". Restart is not rebuild, and
an artefact rebuilt on disk while the process serves the previous inode is a thing that has
happened here.

## 3 · Every dependency, invoked once, for real

Call each external dependency — model, queue, store, callback — and inspect the result. Not the
config screen, not the health page's opinion of it. A dead dependency has passed a deploy here.

## 4 · Config reaches the process

Read each critical value back from INSIDE the running process. "Set in the values file" and "the
process sees it" are different sentences with an injection layer between them.

## 5 · One walkthrough at human speed

Drive the real human path end to end, as a person would, on the deployed thing. Five distinct
root causes reached the customer through this gap in one project, and the one that found them was
a partner's DevOps engineer reporting an SSO login failure.

An automated tester that mints its own token is not the human path.

## 6 · Full regression, once, on the exact bundle

Not on the branch, not on a rebuild — on the artefact that is going out.

## 7 · Readiness must be able to say no

A health endpoint that returns 200 with the database absent is not a readiness probe, it is a
decoration. Check that it fails when the thing it reports on is broken.

## Before you say it is live

State which of the seven you actually did and which you skipped, and paste the `make deploy-check`
lines and the runtime-config reading above them. A skipped one is a known risk with an owner, not an
omission — and "we will do it after the demo" has been said in this lineage before.
