"""#181 (M21-W4): a gate runs the deadline tests on a one-thread cooperative pool.

Since #149 the model-tier deadline tests hold the deadline against a plain timer started beside the
call. On the default pool a call that blocks a thread in the race goes unseen: another thread runs
the deadline. On a one-thread pool (`LIBDISPATCH_COOPERATIVE_POOL_STRICT=1`) it holds the only
thread, so the router is late while the control timer, which runs off the pool, is not. Both Swift
legs run `SlowTierTests` that way after the whole suite.
"""

from __future__ import annotations

import pytest

from tests.unit.test_offline_run import _swift_runs


@pytest.mark.parametrize("leg", ["swift-test", "swift-test-parallel"])
def test_both_swift_legs_run_the_deadline_tests_on_a_one_thread_pool(leg: str) -> None:
    strict = [run for run in _swift_runs(leg, "Darwin") if "LIBDISPATCH_COOPERATIVE_POOL_STRICT=1" in run]
    assert len(strict) == 1, _swift_runs(leg, "Darwin")
    assert "--filter" in strict[0] and "SlowTierTests" in strict[0], strict[0]
    assert "sandbox-exec -f ../scripts/offline.sb" in strict[0], "the strict run is a Swift run like the others (#179)"
