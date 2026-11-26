# Later — LOW findings, one row each (D-257)

A LOW finding is a row here, not an issue (D-257 clause 4, the owner's ruling of 2026-11-26). A finding a user can
see is at least MEDIUM and stays an issue. A review's LOW finding is keyed by its verdict file and its id, and the
findings table of the PR that carries the verdict answers it `later`: `make findings-check` and wave-check accept
that only for a key this table holds. A row leaves this file when its fix merges, or when the owner promotes it to
an issue.

| finding | what | why later |
|---|---|---|
| `release-security.md R37` | A derived model served under its id has no length bound when no source spelling passes `_DISPLAY` (was #631) | LOW: no source has produced such an id; a user would see a long name, not wrong data |
| `release-security.md M28` | INV-52's "a name no addition lists still counts" has no surface-guard test, and the INV-52/54 rows are looser than the code (was #629, also R35) | LOW: the code is correct today; only the test citation is missing |
| issue #622 | Conformance `test-statusline` fails under load: a 3.1 s status-line read reads as hanging | LOW: a flaky check under load, no user sees it |
| issue #619 | `test_a_sigkilled_cycle_leaves_the_live_artifact_byte_identical` fails under load, passes alone | LOW: a flaky test under load, no user sees it |
