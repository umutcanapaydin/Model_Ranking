"""#182 (M21-W4): what CI's test job has is read from its workflow, not kept by hand beside it.

`tests/skips.py` marks each need `in_ci` or not, and the local count of CI's skips is only as right
as those marks. `ci_job_facts` reads the test job in `.github/workflows/ci.yml` (its runner, the
steps before `pytest`, the variables the step sets, the command that runs it) and says which needs
the job has; this test fails when a mark and the workflow disagree, as the owner's #122 patch will
make `offline` do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.skips import NEEDS, ci_job_facts

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
TEST_STEP = "      - name: Test (pytest + coverage)\n        run: pytest\n"
#: #122's patch for the owner, as posted on the issue: pytest in a network namespace, as the user.
OFFLINE_STEP = (
    "      - name: Test (pytest + coverage), offline (#122)\n        run: |\n"
    "          sudo unshare --net -- sh -c 'ip link set lo up && exec sudo --preserve-env -u \"$1\" env"
    " \"PATH=$2\" MODEL_RANKING_REQUIRE_OFFLINE=1 pytest' sh \"$USER\" \"$PATH\"\n"
)


def _marks() -> dict[str, bool]:
    return {name: need.in_ci for name, need in NEEDS.items()}


def _planted(old: str, new: str) -> str:
    assert WORKFLOW.count(old) == 1, old
    return WORKFLOW.replace(old, new)


def test_every_need_ci_marks_is_what_the_workflow_gives_its_test_job() -> None:
    assert ci_job_facts(WORKFLOW) == _marks()


@pytest.mark.parametrize(
    ("old", "new", "flipped"),
    [
        ("    runs-on: ubuntu-latest\n    timeout-minutes: 15\n",
         "    runs-on: macos-latest\n    timeout-minutes: 15\n", {"xcode", "macos"}),
        (TEST_STEP, TEST_STEP + '        env:\n          RUN_CONTRACT_TESTS: "1"\n', {"contract"}),
        (TEST_STEP, TEST_STEP + "        env:\n          EPOCH_DATA_DIR: /data/epoch\n", {"epoch"}),
        (TEST_STEP, OFFLINE_STEP, {"offline"}),
        (TEST_STEP, "      - name: Test (pytest + coverage)\n        run: sudo pytest\n", {"not_root"}),
        (TEST_STEP, "      - name: Build\n        run: make data && test -f advisor.db\n" + TEST_STEP, {"artifact"}),
        ("      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262  # v4\n"
         "      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5\n"
         "        with:\n          python-version: ${{ matrix.python-version }}\n",
         "      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5\n"
         "        with:\n          python-version: ${{ matrix.python-version }}\n", {"git"}),
    ],
    ids=["macos-runner", "contract-env", "epoch-env", "offline-patch", "sudo", "built-db", "no-checkout"],
)
def test_a_planted_change_to_the_test_job_flips_its_need_and_only_that(old: str, new: str, flipped: set[str]) -> None:
    """Shown red on each planted change: the facts move, so the comparison above would fail."""
    facts = ci_job_facts(_planted(old, new))
    assert {name for name, has in facts.items() if has != _marks()[name]} == flipped


def test_a_runner_the_workflow_does_not_name_is_not_guessed() -> None:
    planted = _planted("    runs-on: ubuntu-latest\n    timeout-minutes: 15\n",
                       "    runs-on: ${{ matrix.os }}\n    timeout-minutes: 15\n")
    with pytest.raises(ValueError, match="runner"):
        ci_job_facts(planted)
