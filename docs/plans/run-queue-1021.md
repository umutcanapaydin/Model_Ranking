# Run — queue-1021

<!-- Copy to `docs/plans/run-<name>.md` (`<name>`: lowercase letters, digits, hyphens) when `/plan-run` opens a run, and keep it current: it is
     the ONE record of an unattended run. `make run-check` reads it, `make closes` grades every
     run file in the tree, and `/start-session` reads it first to resume the run after a new
     session or a compaction. Every table cell is read by `scripts/run_check.py`; keep the column
     order and the vocabularies below. Lines starting with `Mode:`, `Started:`, `Ended:`,
     `Integration branch:`, `Plan PR:` and `Rulings:` keep their wording. -->

Mode: light
Started: 2026-10-21
Ended: 2026-10-22 — stopped at control-change, nothing independent left
Integration branch: `integration/run-queue-1021` · PR: #394
Plan PR: #393
Rulings: D-218

<!-- `Ended:` is `open` while the run runs. When it ends: `<YYYY-MM-DD> — <why>`, where why is one
     of `all milestones closed`, `owner stopped`, `stopped at <class>, nothing independent left`.
     `Rulings:` lists the ADRs the owner's answers to the run's decisions message became
     (`/log-decision`, each with its `Owner ruling:` line); `none` when every question took its
     default. -->

The owner opened this run on 2026-10-21 to close the whole open queue before the first release: every issue below lands on one integration branch, the owner merges it, and then `/going-live` runs the release reviews and the deploys (nothing deploys in the run). The queue in order: #387 (its PR #388 is stacked as it stands), #389 on top of it, #391, #371, #378, #379; then the owner-only halves of #390 (the Bash guard) and #392 (`ci.yml`), each as an owner bundle with its patch under `build/`. Questions the run meets that are reversible and outside a ⛔ zone take their most conservative answer in `docs/plans/assumptions-queue-1021.md`.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | cd34b95 | issues | stopped |

<!-- Base: the integration-branch sha the milestone's first wave was cut from (`none` until it
     starts); the milestone Tester and the last wave's cross-wave review take their range from it. Status: `queued` ·
     `running` · `closed` (every wave stacked; heavy: the milestone Tester's verdict beside the last
     wave's close and Stage 4 Capture done on the integration branch) · `stopped` (a wave of it
     stopped and no independent wave of it remains). Light mode: one row, Milestone `queue`, Plan
     `issues` -- the run works the triaged queue; `closed` when every issue row is stacked. -->

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-387 | fix/issue-387-hosted-refresh | #388 | none | stacked |
| issue-389 | fix/issue-389-token-apart | #395 | none | stacked |
| issue-391 | fix/issue-391-repo-pin | #397 | none | stacked |
| issue-371 | fix/issue-371-generic-and-rebuilt | #398 | none | stacked |
| issue-378 | enhancement/issue-378-arena-media | #399 | none | stacked |
| issue-379 | enhancement/issue-379-new-boards | #402 | none | stacked |
| issue-390 | owner/run-queue-1021-bundle-v3 | none | none | stopped |
| issue-392 | owner/run-queue-1021-bundle-v3 | none | none | stopped |
| issue-400 | owner/run-queue-1021-bundle-v3 | none | none | stopped |

<!-- Wave: `m<N>-w<W>` (heavy) or `issue-<n>` (light, Close record `none`). Status: `queued` ·
     `running` · `stacked` (closed with `/close-wave`, merged into the integration branch, its
     draft PR open as the record) · `stopped` (a row in Stops names why). A `stacked` heavy wave
     names a close record that exists and passes `make wave-check`. -->

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-22 | issue-390 | control-change | Apply the owner bundle (the Bash guard, its pin and two workflows, for #390, #392 and #400): one line in docs/owner-actions.md; reviewed PASS WITH FINDINGS in four rounds | the rest of the queue |
| 2026-10-22 | issue-392 | control-change | In the owner bundle with #390: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-22 | issue-400 | control-change | In the owner bundle with #390: apply it with the one line in docs/owner-actions.md | the rest of the queue |

<!-- One row per stop, in order. Class is one of AGENTS.md §3's Escalate-NOW events --
     `secret` · `scanner-suppression` · `blocking-high` · `silent-fault` · `control-change` ·
     `dependency` · `security-test` · `zone-or-criterion` (a ⛔ zone, or the meaning of a
     criterion) · `scope-change` -- or `not-assumable` (a decision the owner reserved -- a
     `work-issue` verdict's flagged decision, an approval a skill asks for -- that the run's
     decisions message did not cover), `environment` (a gate leg or tool that cannot run here) or
     `owner` (the owner stopped the run).
     `Continued on`: the independent work the run went on with, or `nothing`. A stop never
     downgrades, self-answers or works around what it stopped on. -->

## For the owner

The run ended on 2026-10-22. Six PRs are stacked on #394, and the owner bundle is ready to apply. Nothing was deployed, and nothing went to TestFlight.

In the morning, in order:

1. **Merge #393**, the plan, which accepts D-218.
2. **Merge #394**, the integration PR, as a **merge commit, never a squash**. It carries #388 (#387, which accepts D-217), #395 (#389), #397 (#391), #398 (#371), #399 (#378) and #402 (#379, which accepts D-219). GitHub marks them merged, and `/post-merge` closes their issues.
   - Its delta security review is `docs/reviews/integration-run-queue-1021-security.md`. The latest round, round 3 at `1306071`, is PASS with nothing open. The committed file holds round 1; the auto-mode classifier refused the agent's commit of the later rounds, so that commit waits for your word.
3. **Apply the owner bundle** with its line in `docs/owner-actions.md`. It runs on `owner/run-queue-1021-bundle-v3` (local, the red agent half last), applies `build/owner-run-queue-1021.patch` after checking its sha256, pushes, and opens the bundle's draft.
   - It closes #390, #392 and #400. The patch changes `.claude/hooks/bash_guard.py`, the guard pin in `.claude/settings.json`, `ci.yml` and `contract-tests.yml`.
   - Its security review, on the bundle branch, is PASS WITH FINDINGS after four rounds, with no BLOCKING finding left.
   - Merge that draft, then start a new Claude Code session, which loads the new guard.
4. **Then `/going-live`** for `v1.0.0-beta.1`. The release Tester and the release Security-Reviewer run over everything merged since the last release verdicts. After that come the deploys: the `fly-production` environment and token, the nightly workflow copy, the first night, the Mac engine, TestFlight and the tag.
5. **New issues in the run:**
   - from the reviews: #396 (#371's counting loop, which needs a ruling on D-218 clause 4), #400 (in the bundle), #401 (the dispatch paths the gate cannot see), #403 (a media id meeting a priced text model) and #404 (tests for two OSWorld NIT fixes);
   - all triaged.

