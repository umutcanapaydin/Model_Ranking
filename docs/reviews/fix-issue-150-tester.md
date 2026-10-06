---
record_type: review
id: fix-issue-150-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 150 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..d2078e2 (`2fad46b` red test, `d2078e2` fix).
**Risk tier:** MEDIUM (the suite's no-network invariant, INV-6).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `0198eb3`. The
acceptance criterion is the issue body: with the proxy variables hidden (#143), the macOS fallback
`getproxies_macosx_sysconf` must not hand a unit test a system proxy, and "a test plants a
system-level answer ... and sees no proxy reach a test"; a live contract test keeps the real answer.
The issue offers `NO_PROXY=*` as one shape; the fix replaces the fallback instead, which meets the
same criterion. Red: the base `tests/conftest.py` (`git show 0198eb3:tests/conftest.py`) written in
place under the red commit's tests (the test file is identical at `2fad46b` and `d2078e2`), run,
original bytes written back. Gate: `make check-fast` at the head. Faults: one exact unique
replacement per mutant, the original bytes written back and the sha256 compared; the planted proxy
is always `127.0.0.1:9`, where nothing listens. A Linux-shaped urllib (the macOS fallback and
`_get_proxies` deleted, `getproxies` = `getproxies_environment`) was loaded as a `-p` plugin from the
scratchpad, before the repository's conftest, for M4. The one network run: the live contract suite.

## Verdict
MINOR

The fix does what the issue asks, and every half of it has a test that fails without it but one: the
fix's test reads `urllib.request.getproxies()`, while httpx reads its own reference to that function,
taken at import. A fix that replaced `getproxies` instead of the fallback passes the whole suite while
httpx still takes the system proxy (M8). The missing test is written below, red on M8, M2 and the
base code, green at the head.

## Acceptance-criterion coverage
- A planted system proxy reaches no unit test: `tests/unit/test_no_network.py:215`
  (`test_a_system_proxy_reaches_no_unit_test`), plants `_get_proxies` below the fallback, asserts
  `getproxies() == {}` (M1, M2 killed). Through httpx: only T1's test (below).
- A live contract test keeps the real fallback: `tests/unit/test_no_network.py:227`
  (`test_a_live_contract_test_keeps_the_system_proxy`) (M1, M3, M6, M7 killed).
- Nothing is installed where there is no fallback: the macOS test skips under a Linux-shaped urllib
  and errors if the replacement is installed there (M4 killed, control M4c green).
- INV-6 cites both tests; `test_security_invariants.py::test_the_list_holds_together` holds the
  citation (M9 killed).
- Red to green: on the base conftest `test_a_system_proxy_reaches_no_unit_test` fails on the symptom
  (`assert {'https': 'ht.../127.0.0.1:9'} == {}`) and the second test on a missing name (R1); both
  pass at `d2078e2`.
- Skip budget 78 to 79: CI on `main` at `0198eb3` (run 37280620556) reported
  `1743 passed, 78 skipped`, exactly the old budget, and the new test skips off macOS, so 79 is
  required.
- Live contract run, once: `RUN_CONTRACT_TESTS=1 pytest tests/integration --no-cov` at `d2078e2`:
  27 passed in 20.98s. The contract tests still reach their sources.

## Suite result
- `make check-fast` at `d2078e2`: PASS in 79.4s, six legs; test leg 1798 passed, 25 skipped; swift
  leg 462 tests.

## Mutants

| ID | Fault (in `tests/conftest.py` unless named) | Run | Result |
|---|---|---|---|
| M1 | `system_proxies` answers the real fallback when the guard is not lifted | 3 proxy files | KILLED (both #150 tests) |
| M2 | the replacement never installed at configure | 3 proxy files | KILLED (`test_a_system_proxy_reaches_no_unit_test`) |
| M3 | a lifted live contract test gets `{}` | 3 proxy files | KILLED (`test_a_live_contract_test_keeps_the_system_proxy`) |
| M4 | installed on every platform (the `is not None` check dropped) | Linux-shaped urllib | KILLED (the macOS test runs and fails, `no attribute '_get_proxies'`) |
| M5 | no restore at `pytest_unconfigure` | whole suite | SURVIVED (R2) |
| M6 | the lifted path asks `urllib.request.getproxies_macosx_sysconf` (itself) | 3 proxy files | KILLED (`test_a_live_contract_test_keeps_the_system_proxy`) |
| M7 | the lift read from `RUN_CONTRACT_TESTS` instead of `_LIFTED` | 3 proxy files | KILLED (`test_a_live_contract_test_keeps_the_system_proxy`) |
| M8 | `urllib.request.getproxies` replaced by `getproxies_environment`, the fallback left | whole suite | SURVIVED; KILLED by T1's test |
| M9 | `docs/security-invariants.md`: INV-6 cites a misspelt #150 test | whole suite | KILLED (`test_the_list_holds_together`) |

"3 proxy files" is `test_no_network.py`, `test_proxy_hidden_from_the_run.py` and
`test_proxy_rule_and_workers.py`; "whole suite" is `pytest -n auto` with the artifact required
(1798 passed, 25 skipped on each survivor). As committed: 7 of 9 killed; with T1's test, 8 of 9.

## Findings
- **T1** The httpx path has no test that fails without it. The issue names httpx as the reader;
  httpx 0.28 calls `getproxies` imported into `httpx._utils` at import, so a check on
  `urllib.request.getproxies` alone is satisfied by replacing that one name (M8), which leaves
  httpx on the original function and its system proxy. Under M8 an httpx request went to the
  planted proxy (`httpx.ConnectError: [Errno 61] Connection refused` at `127.0.0.1:9`). Written this
  review and appended to `tests/unit/test_no_network.py`: RED on M8, on M2 and on the base conftest;
  GREEN at `d2078e2`; `ruff check` clean. Removed again so the worktree holds only this record; the
  author adds it to the branch and cites it under INV-6. Full text:

```python
@pytest.mark.skipif(not hasattr(__import__("urllib.request").request, "getproxies_macosx_sysconf"),
                    reason="macOS's System Configuration fallback (#150)")
def test_a_system_proxy_reaches_no_httpx_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """#150 (the fix Tester's T1): httpx reads proxies through its own reference to urllib's
    `getproxies`, taken when httpx was imported, so a check on `urllib.request.getproxies` alone
    passed with that function replaced and the fallback left in place. A planted system proxy must
    not carry an httpx request: it goes direct, and the guard stops it before anything is sent."""
    import urllib.request

    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    planted = {"http": "http://127.0.0.1:9", "https": "http://127.0.0.1:9"}
    monkeypatch.setattr(urllib.request, "_get_proxies", lambda: planted)
    with httpx.Client(timeout=1) as client, pytest.raises(NetworkReachedError):
        client.get("http://192.0.2.1/")
```

- **R1** The red commit's second test, `test_a_live_contract_test_keeps_the_system_proxy`, failed
  on a missing name (`AttributeError: ... has no attribute '_REAL_SYSTEM_PROXIES'`), not on a
  behaviour. The first test carries the symptom: on the base conftest it saw the planted system
  proxy. No action asked.
- **R2** M5 survives: nothing proves the fallback is put back at `pytest_unconfigure`. It is
  harmless here: the process ends after it, and no test runs pytest in-process (no `pytester`,
  `runpytest` or `inline_run` under `tests/`), the same as the network guard's own removal. No test
  asked.

## Clean-up evidence
- Every mutant and the red run: original bytes written back and sha256 compared
  (`tests/conftest.py` fa3328336b38..., `tests/unit/test_no_network.py` 54bfb82c553e...,
  `docs/security-invariants.md` 2bdd13e5c952...). No mismatch.
- `git hash-object` equals `HEAD:<path>`: `tests/conftest.py` d9b00ac9,
  `tests/unit/test_no_network.py` 4d74c424, `docs/security-invariants.md` aca57edd,
  `docs/skip-budget.txt` ce6533b3. The Linux-shaped urllib plugin lived in the scratchpad, never in
  the tree. No checkout, restore, stash, reset or commit. `git status --short` lists only this
  record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `test_a_system_proxy_reaches_no_httpx_client`, committed as written and cited under INV-6 |
| R1 | accepted: the first red test fails on the symptom; the second, which holds the lift, could only fail on its name before the fix |
| R2 | refused: the restore at unconfigure runs after the last test, so no test can see it; it puts back what the run changed and nothing reads it after |
