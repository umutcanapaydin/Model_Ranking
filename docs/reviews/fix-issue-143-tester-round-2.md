---
record_type: review
id: fix-issue-143-tester-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 143 independent Tester review, round 2

**Reviewer:** Tester, a new separate session; wrote none of the fix or its tests, and is not the
seat of the first record (`docs/reviews/fix-issue-143-tester.md`).
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** f500497..09fc6c3, the delta after the first Tester's MINOR, on branch
`fix/issue-143-proxy-variables` (whole fix `3426626..09fc6c3`).
**Risk tier:** MEDIUM (the suite's no-network invariant, INV-6).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `3426626`. The
acceptance criterion is the issue body as the triage pins it: "`pytest_configure` removes the proxy
variables for the run unless a live contract test is lifting the guard, and a test plants one and
sees no proxy in a test's environment". The delta: the names derived from urllib's rule
(`tests/conftest.py:137`), `pytest_configure_node` handing the hidden proxies to xdist workers
(`:157`) and the worker reading them (`:207`), and the first Tester's test
(`tests/unit/test_proxy_hidden_from_the_run.py`). Red: trees of `3426626` and `f500497` extracted
with `git archive` and run with this worktree's venv. Gate: `make check-fast` at the head. Faults:
one exact unique replacement per mutant in `tests/conftest.py` or `docs/security-invariants.md`,
the whole suite run (`pytest -n auto`, artifact required) with no proxy in the shell, the original
bytes written back and the sha256 compared; the survivors run again with eight variables in the
shell (`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, their lowercase forms, `Https_Proxy`, `Http_Proxy`)
and again with the tests written here. Every planted proxy named `http://127.0.0.1:9`: nothing
listens, nothing was sent. The one network run: the live contract suite, below.

## Verdict
MINOR

The delta does what the dispositions say: every name urllib reads is hidden, `NO_PROXY` stays, and a
live contract test on an xdist worker gets the shell's proxies back. The first Tester's test is RED
on the base and GREEN at the head. But both halves of the delta are proven by tests that cannot fail
on their faults: the rule is checked with itself (T1), and the hand-off is called by hand, never by
a run (T2). 5 of 15 mutants survive the suite as committed. Two tests are written below; with them,
14 of 15, the survivor outside the criterion.

## Acceptance-criterion coverage
- The run hides a proxy variable from every test, the first included:
  `tests/unit/test_proxy_hidden_from_the_run.py:20`. RED on `3426626` (the child's test sees
  `{'http': ..., 'https': ..., 'all': ...}`), GREEN at `09fc6c3`. D1, H4, H5 killed.
- Every name urllib reads, in any case, and not `no_proxy`: `tests/unit/test_no_network.py:150`
  plants `Ftp_Proxy` and keeps `NO_PROXY` (D4 killed), but checks with `conftest.proxy_names()`
  (`:166`), the rule under test. D2, D3 survive (T1).
- A live contract test gets the proxies back for its own run and loses them after; a unit test is
  never handed them: `tests/unit/test_no_network.py:150` (R1, R2, R3 killed).
- Under `-n`, a contract test on a worker gets them back (the first record's R2):
  `tests/unit/test_no_network.py:191` (H1, H3 killed). The worker's read at `tests/conftest.py:207`
  has no test: H2 and H4b survive (T2).
- INV-6 cites both new tests: `docs/security-invariants.md` (I1 killed).
- Live contract run, once each way, no proxy in the shell: `RUN_CONTRACT_TESTS=1 pytest
  tests/integration -v --no-cov` at `09fc6c3`, 27 passed in 16.27s; the same with `-n 2`, 27
  passed in 9.08s (13 on `gw0`, 14 on `gw1`). The contract tests still reach their sources.
- The whole suite with the eight variables in the shell, at the head: 1784 passed, 25 skipped.

## Suite result
- `make check-fast` at `09fc6c3`: PASS, six legs; test leg 1784 passed, 25 skipped.
- The two tests written here: 2 passed at the head; `ruff check` clean. On the tree of `f500497`
  both RED: the mixed-case names reach the child's test (`{'https': ..., 'http': ..., 'all': ...,
  'ftp': ...}`), and on the worker the contract probe gets nothing back
  (`assert None == 'http://127.0.0.1:9'`) while the unit probe sees `Http_Proxy`.

## Mutants

| ID | Fault (in `tests/conftest.py` unless named) | No proxy in the shell | Eight in the shell | With the tests written here |
|---|---|---|---|---|
| D1 | the rule takes uppercase names only | KILLED (`test_proxy_hidden_from_the_run.py:20`) | not run | not run |
| D2 | the rule back to the first fix's six names | SURVIVED | KILLED (`test_fetch_bounds.py`, 7 tests) | KILLED (both) |
| D3 | the rule takes the three httpx schemes in any case only | SURVIVED | SURVIVED | KILLED (T1 test) |
| D4 | `no_proxy` hidden too | KILLED (`test_no_network.py:150`) | not run | not run |
| D5 | a name ending in `proxy` without the underscore hidden too | SURVIVED | SURVIVED | SURVIVED (outside the criterion) |
| H1 | the controller hands nothing | KILLED (`test_no_network.py:191`) | not run | not run |
| H2 | the worker never reads what it was handed | SURVIVED | SURVIVED | KILLED (T2 test) |
| H3 | the worker reads another key | KILLED (`test_no_network.py:191`) | not run | not run |
| H4 | after the read, the saved proxies put back into the environment | KILLED (`test_proxy_hidden_from_the_run.py:20`) | not run | not run |
| H4b | a worker puts what it was handed into its own environment | SURVIVED | SURVIVED | KILLED (T2 test) |
| H5 | the hide at configure dropped (the first record's P4) | KILLED (`test_proxy_hidden_from_the_run.py:20`) | not run | not run |
| R1 | no restore for a live contract test | KILLED (`test_no_network.py:150`) | not run | not run |
| R2 | the proxies restored for every test | KILLED (`test_no_network.py:150`, `test_proxy_hidden_from_the_run.py:20`) | not run | not run |
| R3 | never hidden again after a contract test | KILLED (`test_no_network.py:150`) | not run | not run |
| I1 | `docs/security-invariants.md`: INV-6 cites a misspelt new test | KILLED (`test_security_invariants.py`) | not run | not run |

As committed, 10 of 15 killed with no proxy in the shell, 11 of 15 with the eight; with the tests
written here, 14 of 15. D5 hides more than urllib reads (a name like `GOPROXY`): it cannot carry a
request out, and the issue asks for nothing about other variables. No test is asked for it.

## Findings
- **T1** The derived rule, the first record's K2, has no test that fails without it.
  `tests/unit/test_no_network.py:166` plants `Ftp_Proxy`, hides, then asserts
  `not conftest.proxy_names()`: the rule checks itself, so a rule that misses a name misses it in the
  check too. D2 (the six names back) survives with no proxy in the shell, D3 survives with eight.
  Written: `test_a_proxy_urllib_reads_in_any_case_reaches_no_test`, a child pytest that inherits
  only mixed-case names, its test reading `urllib.request.getproxies_environment()`. RED on D2, D3
  and on `f500497`; GREEN at the head.
- **T2** The hand-off is tested in halves called by hand (`tests/unit/test_no_network.py:204-207`),
  and the worker's read in `pytest_configure` (`tests/conftest.py:207`) runs in no test: dropping it
  (H2) passes, proxies in the shell or not. H4b passes too: a worker that puts what it was handed into
  its own environment gives the shell's proxies to each worker's first tests, #143's defect through
  the fix's own channel. Written:
  `test_under_xdist_a_unit_test_sees_no_proxy_and_a_live_contract_test_gets_them_back`, the suite's
  conftest copied to a scratch root and a child pytest with `-n 1` running a unit probe, then a
  contract probe, on one worker. RED on H2, H4b, D2 and on `f500497`; GREEN at the head.

The two tests, in one file the author adds to the branch and cites under INV-6 (removed again here
so the worktree holds only this record). Full text, as
`tests/unit/test_proxy_rule_and_workers.py`:

```python
"""Tester round 2, #143: the derived rule and the xdist hand-off, each seen through a real run.

The committed tests check the rule with the rule (`assert not conftest.proxy_names()`), so a rule
that misses a name misses it in the check too; and they call the hand-off's two halves by hand, so a
worker that never reads what it was handed passes. Here a child pytest inherits the variables and
its tests read what urllib reads (`getproxies_environment`, the function httpx asks). Every proxy
names port 9 on this machine: nothing listens there, and no probe sends anything.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROXY = "http://127.0.0.1:9"

SEES_NONE = """
import os
import urllib.request


def test_a_test_sees_no_proxy() -> None:
    seen = urllib.request.getproxies_environment()
    assert set(seen) <= {"no"}, seen
    assert os.environ.get("NO_PROXY") == "localhost", "NO_PROXY is not a proxy: it stays"
"""

GETS_THEM_BACK = f"""
import os


def test_a_live_contract_test_gets_the_proxies_back() -> None:
    assert os.environ.get("HTTPS_PROXY") == {PROXY!r}
    assert os.environ.get("all_proxy") == {PROXY!r}
"""


def _env(tmp_path: Path, pythonpath: Path, proxies: dict[str, str], *, contract: bool) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PYTEST_", "COV_"))
        and k not in ("RUN_CONTRACT_TESTS", "MODEL_RANKING_REQUIRE_ARTIFACT")
        and not k.lower().endswith("_proxy")
    }
    env.update(proxies, PYTHONPATH=str(pythonpath), NO_PROXY="localhost")
    if contract:
        env["RUN_CONTRACT_TESTS"] = "1"
    return env


def _pytest(tmp_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
         "--rootdir", str(tmp_path), *args],
        cwd=tmp_path, capture_output=True, text=True, timeout=180, check=False, env=env,
    )


def test_a_proxy_urllib_reads_in_any_case_reaches_no_test(tmp_path: Path) -> None:
    """#143 and the fix Tester's K2: urllib reads any `*_proxy` in any case, so the run hides every
    one. Only mixed-case names are planted, so the six names of the first fix hide none of them."""
    (tmp_path / "test_probe.py").write_text(SEES_NONE, encoding="utf-8")
    proxies = {name: PROXY for name in ("Https_Proxy", "Http_Proxy", "All_Proxy", "Ftp_Proxy")}
    done = _pytest(tmp_path, _env(tmp_path, ROOT, proxies, contract=False),
                   "-p", "tests.conftest", str(tmp_path / "test_probe.py"))
    assert done.returncode == 0 and "1 passed" in done.stdout, done.stdout[-2000:] + done.stderr[-2000:]


def test_under_xdist_a_unit_test_sees_no_proxy_and_a_live_contract_test_gets_them_back(tmp_path: Path) -> None:
    """#143: "removes the proxy variables for the run unless a live contract test is lifting the
    guard", under `-n` (the fix Tester's R2). The suite's own conftest is copied to a scratch root,
    so `tests/integration` there is a live contract test's place, and a child pytest runs one unit
    probe, then one contract probe, on one xdist worker. The worker started after its controller hid
    the variables: the unit probe must see none, and the contract probe must get them back."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "integration").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(ROOT / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "unit" / "test_unit_probe.py").write_text(SEES_NONE, encoding="utf-8")
    (tmp_path / "tests" / "integration" / "test_contract_probe.py").write_text(GETS_THEM_BACK, encoding="utf-8")
    proxies = {"HTTPS_PROXY": PROXY, "all_proxy": PROXY, "Http_Proxy": PROXY}
    done = _pytest(tmp_path, _env(tmp_path, tmp_path, proxies, contract=True), "-n", "1",
                   "tests/unit/test_unit_probe.py", "tests/integration/test_contract_probe.py")
    assert done.returncode == 0 and "2 passed" in done.stdout, done.stdout[-2000:] + done.stderr[-2000:]
```

## Clean-up evidence
- Every mutant: the original bytes written back, sha256 equal before and after
  (`tests/conftest.py` 42ddb275...aedc5da, `docs/security-invariants.md` a136ec98...0116ca).
- `git hash-object` equals `HEAD:<path>` for `tests/conftest.py` (2240ed9a),
  `tests/unit/test_no_network.py` (6497772e), `tests/unit/test_proxy_hidden_from_the_run.py`
  (1f6f35fa) and `docs/security-invariants.md` (01745cb2). The written test file deleted. The red
  trees ran outside the worktree, in the session's scratch directory. No checkout, restore, stash,
  reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `test_a_proxy_urllib_reads_in_any_case_reaches_no_test`, committed as written |
| T2 | fixed: the seat's `test_under_xdist_a_unit_test_sees_no_proxy_and_a_live_contract_test_gets_them_back`, committed as written; the author shows it red on the worker that never reads its hand-off |
