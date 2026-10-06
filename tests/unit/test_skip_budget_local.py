"""#137: the skips CI will take, counted before a push.

`docs/skip-budget.txt` is checked by CI's test job (`scripts/coverage_floor.py --junit`). The owner's
Mac has the built `advisor.db` and Xcode, so it skips 25 tests where CI skips 81, and `make check-fast`
could not see a raise: three times in M18 and once in M19-W2 a PR opened red on it. The local check
derives CI's count from the tests' own `needs` markers, not from a second list, and compares it with
the budget.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _derive(*paths: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "MODEL_RANKING_REQUIRE_ARTIFACT"}
    return subprocess.run([sys.executable, "-B", "scripts/coverage_floor.py", "--derive", *paths],
                          cwd=ROOT, capture_output=True, text=True, timeout=600, env=env, check=False)


def test_the_local_check_counts_what_ci_will_skip_and_passes_on_the_tree() -> None:
    """#137 (REQ-CI-001): on the tree as committed, the count derived from the markers is the budget."""
    run = _derive()
    assert run.returncode == 0, run.stdout + run.stderr
    assert re.search(r"CI will skip \d+ of \d+", run.stdout), run.stdout


def test_a_planted_test_that_needs_the_artifact_fails_the_local_check(tmp_path: Path) -> None:
    """#137's done-when: one more artifact test, which CI would skip, fails the check before a push."""
    (tmp_path / "test_planted_artifact.py").write_text(
        'import pytest\n\n\n@pytest.mark.needs("artifact")\ndef test_planted() -> None:\n    assert True\n',
        encoding="utf-8",
    )
    run = _derive("tests", str(tmp_path))
    assert run.returncode == 1, run.stdout + run.stderr
    assert "docs/skip-budget.txt" in run.stdout, run.stdout


def test_a_budget_above_the_count_fails_too(tmp_path: Path) -> None:
    """#137, the other direction: a budget above what CI will skip is a ratchet left loose. The
    check names the count to lower it to."""
    budget = tmp_path / "skip-budget.txt"
    budget.write_text("100000\n", encoding="utf-8")
    run = _derive("--budget-file", str(budget))
    assert run.returncode == 1, run.stdout + run.stderr
    assert "fewer than the 100000" in run.stdout, run.stdout


#: A skip outside the `needs` marker: the local check could not count it (the meta-rule that keeps
#: the derivation whole). Spelled so that this line is not one.
RAW_SKIP = re.compile(r"\bpytest\.(?:skip\(|xfail\(|mark\.(?:skip(?:if)?|xfail)\b|importorskip\()"
                      r"|\bunittest\.(?:skip\w*\b|SkipTest\b)|\.skipTest\(|\bfrom\s+pytest\s+import\b[^\n]*\b(?:skip|mark|xfail)\b")


def test_every_skip_goes_through_a_needs_marker() -> None:
    """#137: a raw skip call, a `skipif` mark or an `importorskip` skips in CI where the local check
    cannot see it, so the count would be short. Only the plugin that applies the markers may skip."""
    tracked = subprocess.run(["git", "ls-files", "tests"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.split()
    files = [ROOT / name for name in tracked if name.endswith(".py") and name != "tests/skips.py"]
    assert files, "no test files listed; this check would pass vacuously"
    raw = [f"{path.relative_to(ROOT)}:{number}"
           for path in files
           for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
           if RAW_SKIP.search(line)]
    assert not raw, f"a skip the local count cannot see; use @pytest.mark.needs(...): {raw}"


def test_every_spelling_of_a_skip_is_refused() -> None:
    """The W3 review's M1: `xfail`, `unittest`'s skips and an imported `skip` or `mark` slipped past the
    pattern, and CI's report counts each as a skip."""
    py, ut = "pytest" + ".", "unittest" + "."  # so that this file's own lines are none of them
    spellings = [py + "xfail('x')", "@" + py + "mark.xfail(reason='x')", "@" + ut + "skip('x')",
                 "@" + ut + "skipIf(True, 'x')", "self." + "skipTest('x')", "from pytest " + "import skip",
                 "from pytest " + "import mark", "from pytest " + "import xfail", "raise " + ut + "SkipTest('x')"]
    assert [line for line in spellings if not RAW_SKIP.search(line)] == []
