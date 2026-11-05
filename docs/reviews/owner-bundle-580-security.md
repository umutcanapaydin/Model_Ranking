---
record_type: review
id: owner-bundle-580-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-06
---
# Security Review — owner bundle for #580 (the nightly silent-sources notice)

**Reviewer:** Security-Reviewer subagent (an owner bundle owes a review before it is applied, `scripts/owner_bundle.py`), dispatched by run v100 (issue #594) with the release v1.0.0 security round
**Independent:** yes. This seat did not write the patch, the proposal, `scripts/silent_sources.py` or their tests. It extracted the patch with the proposal's own command, applied it to a scratch git repository made from `git archive 3b9b401` (the base on `main`, the patch on a branch), and ran the tests and the deploy gate's reader there.
**Date:** 2026-11-06
**Reviewed patch:** 9d89f61fc7184fb7aeda42f763c96b612c9abdc07cbf09933b547a32f4a7fb8d
**Reviewed head:** cb1117b7ead31cd92e56f037dd0e8b8742e16db0
**Risk tier:** HIGH. The patch changes the dispatched deploy workflow (`nightly-hosted.yml`, a brief `Deploy commands:` entry) and gives a new job a write-scoped token, `issues: write`. This file carries the bundle's verdict on its own, so that `scripts/owner_bundle.py:107-114`, which reads the first `**Reviewed patch:**` line of a file, accepts it. The same reading is in `docs/reviews/release-security.md`, "Release round v1.0.0 (run v100)" (b) and its "Round 2 (M20)".

## Verdict
MINOR

M20 is closed at `a241247`; the open items are risks, below. The patch's sha is unchanged by that fix, which is test-side only.

## What was read
- **The bytes.** `awk '/^```diff$/{f=1;next} /^```$/{f=0} f' docs/proposals/nightly-silent-sources.md` gives a file whose sha256 is the name above. It applies cleanly to `3b9b401` and to `cb1117b`, and changes `.github/workflows/nightly-hosted.yml` and `scripts/ci/nightly-hosted.yml` identically.
- **Job permissions.** The workflow default stays `contents: read`. `refresh` keeps `contents: read, actions: read` and gains only `outputs.silent`. `notice` holds `issues: write` and nothing else, runs no action and checks nothing out. `deploy` is byte-identical.
- **The title is fixed** (`title='Sources silent for 7 or more nights'`, `scripts/silent_sources.py`'s `TITLE`). Only the body comes from the refresh. `NOTICE` arrives through `env:`, never through `${{ }}` in the script, and `jq -r '.body'` writes it to a file passed with `--body-file`. There is no `gh api --input`, so code run in `refresh` cannot set a title, labels, assignees or a milestone. This closes owner-bundle-552's R2. The `issue list` lookup is pinned to `--author app/github-actions` and to the repository.
- **The deploy can never be skipped or widened by this patch.** `deploy` keeps `needs: refresh` and its `if:` (main, and outcome `published` or `unchanged`), which carries the implicit `success()`. The new step is `continue-on-error: true`, so its failure leaves `refresh` successful. It writes only `steps.silent.outputs.*`, and a newline in its JSON could at most add outputs to that one step, never `steps.night.outputs.outcome`. `notice` sits beside `deploy`, not before it, so its failure skips nothing. This closes owner-bundle-552's M1. M2 and M3 are held by `tests/unit/test_nightly_notice_580.py`.
- **The deploy gate reads the patched workflow.** On the patched scratch tree, `unnamed_starts` returns `[]` with 95 run commands counted (D-239, D-242, D-245).

## Findings

### BLOCKING
- none

### MINOR
- **M20** (closed) `tests/unit/test_nightly_hosted.py:473` at `3b9b401`: the shape test banned `continue-on-error` anywhere in the proposal copy, so the patch made the owner's PR red. Fixed at `a241247` (`:473-481`): the key is allowed only on the `refresh` job's step whose `id` is `silent`. A job-level key, the key on any other step, and the word anywhere else (a comment included) still fail. Re-verified below.

### PASS
- owner-bundle-552 M1, M3 and R2 are in the patch; M2 is held by `tests/unit/test_nightly_notice_580.py:57-68`.
- M20's red test `5566380` (`tests/unit/test_nightly_notice_580.py:88-97`) runs the shape test on the patched workflow, so the bundle and the rule cannot drift apart again while the bundle is unapplied.

## M20 re-verification (round 2, at `cb1117b`)
- **The owner's PR would now be green.** With the patch applied in the scratch repository and the two test files of `cb1117b` in place, `tests/unit/test_nightly_hosted.py` and `tests/unit/test_nightly_notice_580.py`: 51 passed. On the unpatched `cb1117b` tree: 51 passed.
- **The narrowing is safe.** Seven inputs, each run through the narrowed test with `PROPOSAL` pointed at a copy of the patched workflow. The unchanged copy passes. Each of these fails: `continue-on-error: true` on the night's deploy step; the key at the `refresh` job's level; the key spelled with a YAML escape (`"continue\x2don-error"`) on the deploy step and at the deploy job's level (the parsed checks catch what the word count cannot); a second step with `id: silent`; and the word in a comment. The parsed checks and the word count cover each other.

## Gates passed
- [x] The patch's sha256 matches its name; no binary hunk.
- [x] Permissions: `notice` only `issues: write`; `refresh` and `deploy` unchanged; no `pull_request_target`; every `uses:` pinned to a commit.
- [x] No secret in the patch; `GH_TOKEN` is `${{ github.token }}`.
- [x] The deploy job is unchanged and cannot be skipped by the new step or job.
- [x] `scripts/owner_bundle.py`'s `reviewed()` accepts this sha from this file (probed).

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #580 M1 → the patch's `silent` step (`continue-on-error: true`); `tests/unit/test_nightly_notice_580.py:71-73`.
- #580 M2 → `tests/unit/test_nightly_notice_580.py:57-68`.
- #580 M3 → `tests/unit/test_nightly_notice_580.py:83-85`.
- #580 R2 → `tests/unit/test_nightly_notice_580.py:76-80`.
- M20 → `tests/unit/test_nightly_hosted.py:473-481`; `tests/unit/test_nightly_notice_580.py:88-97`.

## Risks queued
- **R1** The silent step has no `timeout-minutes` of its own. A hang there would end in the job's 45-minute timeout, which fails `refresh` and skips the deploy; `continue-on-error` does not cover a job timeout. The script reads one small local JSON file, so this is unlikely. Revisit: `timeout-minutes: 2` on the step in the next workflow bundle. (The release verdict's R16.)
- **R2** owner-bundle-552's R1 still applies: names and stamps in the body are not checked for control characters or `|`. The writer is the token-free refresh job, and the body reaches only this repository's issues.
