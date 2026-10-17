# Run — <name>

<!-- Copy to `docs/plans/run-<name>.md` (`<name>`: lowercase letters, digits, hyphens) when `/plan-run` opens a run, and keep it current: it is
     the ONE record of an unattended run. `make run-check` reads it, `make closes` grades every
     run file in the tree, and `/start-session` reads it first to resume the run after a new
     session or a compaction. Every table cell is read by `scripts/run_check.py`; keep the column
     order and the vocabularies below. Lines starting with `Mode:`, `Started:`, `Ended:`,
     `Integration branch:`, `Plan PR:` and `Rulings:` keep their wording. -->

Mode: <heavy | light>
Started: <YYYY-MM-DD>
Ended: open
Integration branch: `integration/run-<name>` · PR: #<n>
Plan PR: #<n>
Rulings: <D-<n>, D-<n> | none>

<!-- `Ended:` is `open` while the run runs. When it ends: `<YYYY-MM-DD> — <why>`, where why is one
     of `all milestones closed`, `owner stopped`, `stopped at <class>, nothing independent left`.
     `Rulings:` lists the ADRs the owner's answers to the run's decisions message became
     (`/log-decision`, each with its `Owner ruling:` line); `none` when every question took its
     default. -->

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | M<N> | none | docs/plans/m<N>-plan.md | queued |

<!-- Base: the integration-branch sha the milestone's first wave was cut from (`none` until it
     starts); the milestone Tester and the last wave's cross-wave review take their range from it. Status: `queued` ·
     `running` · `closed` (every wave stacked; heavy: the milestone Tester's verdict beside the last
     wave's close and Stage 4 Capture done on the integration branch) · `stopped` (a wave of it
     stopped and no independent wave of it remains). Light mode: one row, Milestone `queue`, Plan
     `issues` -- the run works the triaged queue; `closed` when every issue row is stacked. -->

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| m<N>-w<W> | wave/m<N>-w<W> | #<n> | docs/plans/m<N>-wave-<W>-close.md | queued |

<!-- Wave: `m<N>-w<W>` (heavy) or `issue-<n>` (light, Close record `none`). Status: `queued` ·
     `running` · `stacked` (closed with `/close-wave`, merged into the integration branch, its
     draft PR open as the record) · `stopped` (a row in Stops names why). A `stacked` heavy wave
     names a close record that exists and passes `make wave-check`. -->

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|

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

<!-- What the morning needs, in order: the plan PR, the integration PR (merge commit, never a
     squash), each stop's question. Rewrite in place; this is a live document, not a log. -->
