# Run — bug-night

Mode: light
Started: 2026-10-17
Ended: 2026-10-18 — stopped at control-change, nothing independent left
Integration branch: `integration/run-bug-night` · PR: #335
Plan PR: #334
Rulings: D-209

The queue in order (D-209): the two drafts already open (#333, #329), then the bugs by severity, then the enhancements. The owner-only files (`.claude/`, `.githooks/`, `.github/workflows/`) end as one owner patch, reviewed before handover (D-209 clause 2). Questions the run meets that are reversible and outside a ⛔ zone take their most conservative answer in `docs/plans/assumptions-bug-night.md`.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | e709a6b | issues | stopped |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-295 | fix/issue-295-task-before-ai | #333 | none | stacked |
| issue-326 | fix/issue-326-encoded-ref | #329 | none | stacked |
| issue-331 | fix/issue-331-main-clone-marker | #336 | none | stacked |
| issue-256 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-287 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-305 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-332 | fix/issue-332-mcp-json | #337 | none | stacked |
| issue-325 | fix/issue-325-ignored-documents | #338 | none | stacked |
| issue-330 | fix/issue-330-next-adr | #339 | none | stacked |
| issue-328 | fix/issue-328-guard-test-timeout | #340 | none | stacked |
| issue-341 | fix/issue-341-conflict-markers | #342 | none | stacked |
| issue-317 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-318 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-320 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-81 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-344 | owner/bug-night-bundle-v2 | none | none | stopped |
| issue-314 | fix/issue-314-answers-size | #343 | none | stacked |
| issue-322 | fix/issue-322-kept-answer-rules | #346 | none | stacked |
| issue-319 | fix/issue-319-policy-scripts | #347 | none | stacked |
| issue-309 | fix/issue-309-whole-test-observer | #345 | none | stacked |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-18 | issue-256 | control-change | Apply the owner bundle (the guard and the workflows for #256, #287, #305, #317, #318, #320, #344 and #81): one line, in docs/owner-actions.md; reviewed PASS WITH FINDINGS in four rounds | the rest of the queue |
| 2026-10-18 | issue-287 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-305 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-317 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-318 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-320 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-344 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |
| 2026-10-18 | issue-81 | control-change | In the owner bundle with #256: apply it with the one line in docs/owner-actions.md | the rest of the queue |

## For the owner

The run ended on 2026-10-18. Eleven PRs are stacked on #335, and the owner bundle is ready to apply. Nothing was deployed, and nothing went to TestFlight.

In the morning, in order:

1. **Merge #334**, the plan, which accepts D-209.
2. **Merge #335**, the integration PR, as a **merge commit, never a squash**. It carries #333 (#295, which accepts D-208), #329 (#326), #336 (#331), #337 (#332), #338 (#325), #339 (#330), #340 (#328), #342 (#341), #343 (#314), #345 (#309), #347 (#319) and #346 (#322). GitHub marks them merged, and `/post-merge` closes their issues.
3. **Apply the owner bundle** with the first open line in `docs/owner-actions.md`. It runs on `owner/bug-night-bundle-v2` (the red agent half, `f716219`), applies `build/owner-bug-night.patch` in your clone, pushes, and opens the bundle's draft.
   - It closes #256, #287, #305, #317, #318, #320, #344 and #81.
   - Its security review is `docs/reviews/run-bug-night-owner-bundle-security.md`: PASS WITH FINDINGS after four rounds, with no BLOCKING finding left.
   - Merge that draft, then start a new Claude Code session, which loads the new guard. Then run the second line: it drops the deleted `governance-contract` check from main's required checks.
4. **Before a deploy:** `make deploy-check` fails until the release Tester and the release security review run again on everything merged since `9217c6c`. Run them after step 3, since the bundle changes the guard.
5. **New issues tonight:** #341 (fixed), #344 (in the bundle) and #348 (a live-data smoke that failed once and passed on its rerun).
