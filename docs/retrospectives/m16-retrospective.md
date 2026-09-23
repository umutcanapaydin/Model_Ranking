---
record_type: retrospective
id: m16-retrospective
status: draft
date: 2026-09-23
---
# M16 Retrospective — the product keeps itself current, and the reviews kept finding the dangerous direction

## The carried question, answered

> M15 asked: once the reader can press "update now", freshness becomes something the product
> promises a person. What must be true before the app shows "last refreshed" as a claim about the
> data, and what should it say when a refresh ran but one source failed?

**The owner answered the first half by removing the premise.** There is no button (D-151). The
boards move over days, so the engine refreshes once a night and the app claims nothing about it:
the date a reader judges by is each board's own run date, which the detail screen already shows.

**The second half became D-156.** A source that fails keeps serving its last good data for 30 days
from its last arrival, and after that its surfaces drop. The engine says so (`/health`:
`refresh_carried`, `refresh_expired`, and from W4 `refresh_drift`); the app does not, on the
owner's ruling (D-151 keeps operations out of the app).

**What that leaves:** a reader cannot tell from the screen that a surface is serving month-old
data from a failed source. The ruled answer is that the board's own date shows the age of the
evidence, and that is true. It does not show that a price feed stopped answering. That is a product
decision the owner made knowingly, not a gap nobody saw.

## What went well

- **Every wave had an independent seat, and every seat found something no gate had.** W1: the
  privacy gate was still a list of spellings; it now reads what the compiler resolved (W-122). W3:
  two tests that could not fail, and an exemption that excused a whole surface. W4: a crafted zip
  that crashed the whole night's refresh, a name grammar that merged different models, and a
  launchd job that was the refresher actually running and that the wave had not touched. **Each of
  these was the dangerous direction:** silence, a false merge, or an untouched running process.
- **The updater's gap was found by running it.** A refresh on a copy of the served artifact, with
  live upstreams, showed 9 of 19 sources never fetched and the Epoch layout changed. Reading the
  code had not shown either.
- **Measure, then ask.** The floors table (D-148) and the derived-registry before/after tables went
  to the owner before any number shipped. Each ruling came back the same day, and one correction
  ("two labels" was three) went back with it.
- **Red first, mutated, every phase.** Each behavioural change had a failing test in its own
  commit, and the mutants that survived became tests: eleven of them this milestone.
- **DevFlow v6.0 (D-155) held.** Drafts, the owner merges, no AI attribution, and CI on every PR.
  `make check-fast` came from the owner's other project and cut the gate from 89 s to 33 s.

## What went badly

- **Merges ran ahead of the process twice.**
  - PR #3 (W3) and PR #6 (W4) were merged before their last `/repo-review` and `/pre-merge` ran.
    #6 was merged while its independent review was still out; the review came back BLOCKING a few
    minutes later, and the fix needed a round of its own (PR #8).
  - PR #5 was stacked on the W3 branch and merged into it after W3 had already merged, so its
    records never reached `main` until they were carried again (#6).
  - Both working plans reached `main`.

  The agent's PR bodies listed the pending steps, but not where the owner decides.
- **The lead's own tooling slipped five times.** Each slip was caught and repaired without
  `git checkout`, and each is recorded in its wave close:
  - an edit script duplicated a block of `registry.py`;
  - a mistyped command moved the owner's untracked file (put back at once);
  - `git add -u` swept a fix into a test commit;
  - copying a virtualenv into a worktree made `make install` rewrite the original's editable path;
  - a review seat overwrote a shared scratch script, and running it with the lead's arguments
    wrote junk files.
- **A claim outran its code again.** The first D-157 grammar was described, in the ADR, the code
  comment, the test docstring and the PR, as one that "never removes a date or a word". It removed
  `-vN` and everything after `:` or `@`. It is M15's lesson 5 in a new place.
- **The running refresher was not the one being changed.** W4 changed the nightly refresh inside
  the engine. The job actually refreshing the owner's artifact was a launchd wrapper, running
  whatever branch is checked out in the repository directory, and nobody asked which process
  runs until the review did.
- **A floor measured on a snapshot moves with the data.** D-148's rows rule is relative to the
  board, and the fresh bundle moved six floors. The floors are right for the day they were measured.

## Playbook seeds (proposed; the owner approves or refuses)

1. **Say where the owner decides.** A draft PR whose review or `/pre-merge` has not run carries
   "review pending, do not merge" as the first line of its body, and the agent removes it only when
   the review is in.
2. **Do not stack PRs across a merge the owner controls.** If one must be stacked, its base is
   retargeted before the base merges, never after.
3. **Before changing "the" scheduled job, list what actually runs.** Engine, launchd, cron: check
   the machine, not the repository. This is L.7 ("the running thing is the built thing") applied
   to schedulers.
4. **One scratch directory per seat.** A review seat writes only into its own new subdirectory,
   never into a path the lead uses.
5. **A normaliser ships with adversarial pairs.** Any code that makes two names one id is tested,
   in the same change, on pairs of different products that must stay apart.

**Control bypass (`control-bypass`):** `/pre-merge` did not run before PRs #3 and #6 were merged.
In each case the owner merged a draft whose remaining steps were listed in its body. W3's reviews
were complete; W4's was not, and its BLOCKING finding was fixed after merge (PR #8). Nothing wrong
was served: D-132 refused the derived roster in the nightly cycle, as designed.

**What was accepted rather than solved:**
- the floors on fresh data (W-128);
- six tie margins that follow a rule D-148 does not name (W-127);
- three data sources whose licences may not permit a commercial product (W-129, owner: keep and
  record);
- about thirteen derived ids on names the sources reuse (a curated rule's job);
- nothing deployed, ninth milestone.

**Carried to M17:** M17 builds lists no leaderboard publishes, by combining boards behind a question
Apple Intelligence reads. When the product answers with such a list, what must the reader see so
the list is honest about being the product's own — and what evidence would tell us that a
combination is wrong?
