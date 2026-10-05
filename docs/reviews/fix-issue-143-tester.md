---
record_type: review
id: fix-issue-143-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 143 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 3426626..f500497 (`55d351a` red test, `f500497` fix), branch
`fix/issue-143-proxy-variables`.
**Risk tier:** MEDIUM (the suite's no-network invariant, INV-6).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `3426626`. The
acceptance criterion is the issue body as the triage comment pins it: "`pytest_configure` removes the
proxy variables for the run unless a live contract test is lifting the guard, and a test plants one
and sees no proxy in a test's environment". Red: the tree of `55d351a` extracted with `git archive`
(its `tests/conftest.py` is byte-identical to the base) and run with this worktree's venv. Gate:
`make check-fast` at the head. Faults: one exact unique replacement per mutant in
`tests/conftest.py` or `docs/security-invariants.md`, the full suite run (`pytest -n auto`, artifact
required), the original bytes written back and the sha256 compared. Each mutant was run with no
proxy in the shell, as this shell, CI and the owner's runs have; the ones that survived were run
again with all six variables set to `http://127.0.0.1:9` (nothing listens there). Every planted proxy
named port 9 on this machine. The one network run: the live contract suite, below.

## Verdict
MINOR

The fix does what the issue asks in a serial run, and the restore for a live contract test is
proven. But no committed test proves the half the criterion names first: that `pytest_configure`
hides the variables. With that call removed the suite stays green, with or without a proxy in the
shell, because every teardown hides them again (T1). The missing test is written below and shown red
on that mutant and on the base code.

## Acceptance-criterion coverage
- The run hides a proxy variable from the tests: proven only by T1's test (below). The fix's
  `tests/unit/test_no_network.py:158` asserts no proxy is visible, which is vacuous when the shell
  holds none, and with one held it is satisfied by any earlier test's teardown.
- A planted variable is hidden by `_hide_proxies`: `tests/unit/test_no_network.py:161-164`.
- A live contract test gets the variables back for its own run, before its fixtures: `:181` (P2,
  P10 killed).
- The variables are hidden again after that test, and a unit test is never handed them: `:177`,
  `:182` (P3, P5 killed).
- Red to green: the fix's test is RED on `55d351a` with
  `AttributeError: module 'tests.conftest' has no attribute 'PROXY_VARS'`, GREEN at `f500497` (see
  R1). T1's test is RED on `55d351a` with `{'http': ..., 'https': ..., 'all': ...}` seen by the
  child's test, GREEN at `f500497`.
- Live contract run, once: `RUN_CONTRACT_TESTS=1 pytest tests/integration -v --no-cov` (the CI
  job's command) at `f500497`: 27 passed in 15.42s. The contract tests still reach their sources.
- The suite with all six variables set in the shell at the head: 1782 passed, 25 skipped.

## Suite result
- `make check-fast` at `f500497`: PASS, six legs; test leg 1782 passed, 25 skipped.

## Mutants

| ID | Fault (in `tests/conftest.py` unless named) | No proxy in the shell | Proxies in the shell | With T1's test |
|---|---|---|---|---|
| P1 | only the uppercase names hidden | KILLED | not run | KILLED |
| P2 | no restore for a live contract test | KILLED | not run | not run |
| P3 | never hidden again after a contract test | KILLED | not run | not run |
| P4 | the `_hide_proxies()` call in `pytest_configure` dropped | SURVIVED | SURVIVED | KILLED |
| P5 | the variables restored for every test | KILLED | not run | not run |
| P6 | hidden but not saved | KILLED | not run | not run |
| P7 | the restore in `pytest_unconfigure` dropped | SURVIVED | not run | SURVIVED |
| P8 | `HTTP_PROXY` dropped from the list | SURVIVED | KILLED (`test_fetch_bounds.py`) | KILLED |
| P9 | `https_proxy` dropped from the list | SURVIVED | KILLED (`test_a_planted_real_request_fails_the_test`) | KILLED |
| P10 | the contract restore moved after the fixtures | KILLED | not run | not run |
| P11 | `docs/security-invariants.md`: INV-6 cites a misspelt test | KILLED | not run | not run |

With the suite as committed and no proxy in the shell: 7 of 11 killed. With T1's test added: 10 of
11. P7 is outside the criterion: `pytest_unconfigure` gives the variables back to the process
pytest ran in, which a command-line run ends at once. No test is asked for it.

## Findings
- **T1** The configure half of the criterion has no test that fails without it. P4 survives even
  with the variables in the shell: the controller and each xdist worker skip the hide at configure,
  but the first teardown on each worker hides them, so only collection, code run at import, and
  each worker's first test see the proxy, and the fix's test is never first. Written this review:
  a child pytest inherits all six variables and its first and only test reads what httpx reads.
  RED on P1, P4, P8, P9 and on `55d351a`; GREEN at `f500497`; `ruff check` clean. It was removed
  again so the worktree holds only this record; the author adds it to the branch and cites it under
  INV-6. Full text, as `tests/unit/test_proxy_hidden_from_the_run.py`:

```python
"""Tester, #143: a proxy in the environment a run inherits reaches no test, the first one included."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROBE = """
import urllib.request


def test_the_first_test_of_a_run_sees_no_proxy() -> None:
    seen = urllib.request.getproxies_environment()
    assert not {k: v for k, v in seen.items() if k in ("http", "https", "all")}, seen
"""


def test_a_proxy_planted_in_the_runs_environment_reaches_no_test(tmp_path: Path) -> None:
    """#143: "`pytest_configure` removes the proxy variables for the run ... a test plants one and
    sees no proxy in a test's environment". The fix's own test plants after the run has started and
    calls `_hide_proxies()` itself, and every teardown hides them again, so with the call in
    `pytest_configure` removed the suite stayed green, a proxy in the shell or not. Here a child
    pytest inherits the variables, and its first and only test reads what httpx reads
    (`urllib.request.getproxies_environment()`, the `http`, `https` and `all` keys). Port 9 on this
    machine: nothing listens, and nothing is sent."""
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_probe.py").write_text(PROBE, encoding="utf-8")
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PYTEST_", "COV_"))
        and k not in ("RUN_CONTRACT_TESTS", "MODEL_RANKING_REQUIRE_ARTIFACT")
    }
    env["PYTHONPATH"] = str(root)
    for scheme in ("http", "https", "all"):
        env[f"{scheme}_proxy"] = env[f"{scheme.upper()}_PROXY"] = "http://127.0.0.1:9"
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
         "-p", "tests.conftest", "--rootdir", str(tmp_path), str(tmp_path / "test_probe.py")],
        cwd=tmp_path, capture_output=True, text=True, timeout=120, check=False, env=env,
    )
    assert done.returncode == 0, done.stdout[-2000:] + done.stderr[-2000:]
    assert "1 passed" in done.stdout, done.stdout[-2000:]
```

- **R1** The red commit's test failed on a missing name (`AttributeError` on `PROXY_VARS`), not on
  the symptom: on `55d351a` it never looked at a proxy. T1's test is the red that reproduces the
  symptom (the child's test sees all three proxies on the base code).
- **R2** Under xdist a live contract test never gets the shell's proxy back. The controller hides
  the variables in `pytest_configure` before it starts the workers, so the workers inherit none and
  have nothing to restore. Probe with `HTTPS_PROXY` set and `RUN_CONTRACT_TESTS=1`, one throwaway
  test under `tests/integration` (removed): serial, `HTTPS_PROXY` restored; `-n 2`,
  `assert None == 'http://127.0.0.1:9'`. CI's contract job runs serially, so the documented path
  holds; a contract run with `-n` behind a proxy would lose it. The author fixes it or files it.
- **K1** Out of the issue's scope, to be filed. On macOS `urllib.request.getproxies()`, which httpx
  0.28.1 reads (`get_environment_proxies`), is `getproxies_environment() or
  getproxies_macosx_sysconf()`: with every variable hidden it falls back to the System
  Configuration proxies, so a system proxy on this machine would carry a unit test's request out
  past the guard just as a variable did. None is set on this Mac now (`getproxies_macosx_sysconf()`
  returned no keys). One possible shape: the run sets `NO_PROXY=*`, which makes the environment
  non-empty (no fallback) and makes httpx drop every proxy.
- **K2** Out of the issue's scope, to be filed with K1. The six names are a hand-kept list beside
  urllib's rule, which takes any variable whose lowercased name ends in `_proxy`. Probe:
  `Https_Proxy=http://127.0.0.1:9` gave `get_environment_proxies()` =
  `{'https://': 'http://127.0.0.1:9'}`, and `_hide_proxies` leaves that name. Deriving the set from
  the rule (AGENTS.md section 3.5) closes it.

## Clean-up evidence
- Every mutant: original bytes written back, sha256 equal before and after (`tests/conftest.py`
  a6e9ae6e...0170d, `docs/security-invariants.md` 4f067b20...60aa2).
- `git hash-object` equals `HEAD:<path>` for `tests/conftest.py` (d4df668f),
  `tests/unit/test_no_network.py` (67df8f3d) and `docs/security-invariants.md` (6de3e9b5). T1's
  test file and the R2 probe file deleted. No checkout, restore, stash, reset or commit.
  `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's test, `tests/unit/test_proxy_hidden_from_the_run.py`, committed as written; it fails on the base code, so it is also the symptom-level red R1 asks for |
| R1 | answered by T1's test, above |
| R2 | fixed: the controller hands its hidden proxies to each xdist worker (`pytest_configure_node`), with a test; probed end to end with a contract test under `-n 2` |
| K1 | #150 |
| K2 | fixed here rather than filed: the hidden names are derived from urllib's rule (any `*_proxy` in any case but `no_proxy`), and the test plants `Ftp_Proxy` and keeps `NO_PROXY` |

The production change after this review (K2, R2) is read by the next Tester seat, with #139's.
