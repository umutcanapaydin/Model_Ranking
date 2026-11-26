# Later — LOW findings, one row each (D-257)

A LOW finding is a row here, not an issue (D-257 clause 4, the owner's ruling of 2026-11-26). A finding a user can
see is at least MEDIUM and stays an issue. A review's LOW finding is keyed by its verdict file and its id, and the
findings table of the PR that carries the verdict answers it `later`: `make findings-check` and wave-check accept
that only for a key this table holds. A row leaves this file when its fix merges, or when the owner promotes it to
an issue. Only a row whose reason starts `LOW` answers `later`, and a BLOCKING finding never does.

| finding | what | why later |
|---|---|---|
| `release-security.md M28` | INV-52's "a name no addition lists still counts" has no surface-guard test, and the INV-52/54 rows are looser than the code (was #629, also R35) | LOW: the code is correct today; only the test citation is missing |
| issue #622 | Conformance `test-statusline` fails under load: a 3.1 s status-line read reads as hanging | LOW: a flaky check under load, no user sees it |
| issue #619 | `test_a_sigkilled_cycle_leaves_the_live_artifact_byte_identical` fails under load, passes alone | LOW: a flaky test under load, no user sees it |
| `release-tester.md L18` | `wave_check.py`'s `later` branch has no end-to-end test; its helpers are pinned | LOW: heavy mode only, no user sees it |
| `release-tester.md L19` | `REGISTER_CITE` accepts a `tests/../..` path | LOW: it can only widen the code list, never open the gate |
| `enhancement-issue-639-process-light-security.md R2` | (release-security.md R40) Nothing checks why a row leaves this file | LOW: a row leaving shows in the PR diff the owner merges |
| `release-tester.md L20` | `_imported_tests` does not follow `from . import x`, `import tests.x` or `from tests import x` | LOW: no cited test, or module one imports, uses those forms; adding one changes a cited test, which re-opens the verdicts |
| `release-tester.md L21` | `from .. import c` yields a junk path, a directory with an empty module name | LOW: harmless, it names no file |
| `enhancement-issue-639-process-light-security.md R3` | (release-security.md R41) An uncited test runs in the cited tests' pytest process (and an uncited `*Tests.swift` in their Swift module), so its import-time code can patch what they use | LOW: D-257's mitigation accepts it; CI still runs the change |
| `enhancement-issue-639-process-light-security.md R4` | (release-security.md R42) The `LOW` reason check is a plain prefix, so `low-ish but MEDIUM` passes; the fix is `LOW\b` | LOW: the row and its reason are in the PR diff the owner merges |
