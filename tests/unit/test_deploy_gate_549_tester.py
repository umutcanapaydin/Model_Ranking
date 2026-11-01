"""The release delta Tester of `integration/fixes-1101` (2026-11-01): D-239's shapes the range's tests do not reach.

Each case below is a run step that starts a file without writing its name, by a shape D-239 names; each stayed
green under the fault named beside it, on all 571 deploy-gate tests. Every one refuses the deploy at `eaee56b`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_522 import STEP
from .test_deploy_gate_549 import _deploy, _dispatched

CASES = {
    # F-U5b: the brace range `{1..3}` dropped from PATTERN (D-239 clause 2 names `{1..3}`).
    "brace-range": ("      - run: scripts/ship_{1..3}.sh\n", "pattern"),
    # F-U6: `parallel` dropped from RUNTIME_RUNNERS (D-239 clause 2: `xargs`, `parallel`).
    "parallel": ("      - run: ls scripts | parallel bash scripts/{}\n", "run time"),
    # F-U7: FIND_RUNS narrowed to `-exec` (D-239 clause 2: `-exec`, `-execdir`, `-ok`, `-okdir`).
    "find-execdir": ("      - run: find scripts -name 'ship*' -execdir {} \\;\n", "run time"),
    "find-ok": ("      - run: find scripts -name 'ship*' -ok {} \\;\n", "run time"),
    "find-okdir": ("      - run: find scripts -name 'ship*' -okdir {} \\;\n", "run time"),
    # F-U10: STARTER_VALUED emptied, so an option's value is read as the file (D-239 clause 3: "its first operand
    # that is not an option or an option's value").
    "bash-option-value": ("      - run: bash -o pipefail scripts/ship*.sh\n", "pattern"),
    "python-option-value": ("      - run: python3 -W error scripts/*.py\n", "pattern"),
    # F-U11: `-m` not read; `-m "$M"` apart is still an operand, but attached it is one option word (D-239
    # clause 3: "or the module `-m` names").
    "python-module-attached": ("      - run: python3 -m\"$MODULE\"\n", "run time"),
    # F-U14: `<<` read as a here-document wherever a word ends in it; a quoted `<<` opens none, so the line after
    # it is run (D-239 clause 1 sets aside a here-document's body only).
    "after-a-quoted-word-ending-in-heredoc-mark": (
        "      - run: |\n          echo 'x <<' EOF\n          $SCRIPT\n          EOF\n", "run time"),
    # F-U23: STARTER_SHELLS narrowed to `sh` and `bash` (D-239 clause 3 names `dash`, `zsh`, `ksh`, ...).
    "dash-operand": ("      - run: dash scripts/ship*.sh\n", "pattern"),
    "zsh-operand": ("      - run: zsh scripts/*.sh\n", "pattern"),
    "ksh-variable": ("      - run: ksh \"$SCRIPT\"\n", "run time"),
    # F-U26: a folded block scalar (`>`) not joined into one line, so its second line's option read as a program.
    "folded-block": ("      - run: >\n          python3\n          -m \"$MODULE\"\n", "run time"),
    # F-U27: a backslash continuation not joined (D-239 clause 1), so the next line's option read as a program.
    "continuation-to-an-option": ("      - run: |\n          python3 \\\n            -m \"$MODULE\"\n", "run time"),
}


# covers D-239, #549
@pytest.mark.parametrize(("step", "shape"), list(CASES.values()), ids=list(CASES))
def test_a_shape_d239_names_refuses_the_deploy(tmp_path: Path, step: str, shape: str) -> None:
    repo = _dispatched(tmp_path, step)
    code, out = _deploy(repo)
    assert code == 2, out
    assert "release.yml" in out and shape in out, out


# covers D-239 clause 1 -- stays quiet: an output redirection's target is set aside, only a `<` target is the file
# a starter with no operand runs. F-U20 (every target read as standard input) refused this; no range test held it.
def test_a_starters_output_redirection_is_not_the_file_it_runs(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, "      - run: bash < scripts/ship_it.sh > \"$RUNNER_TEMP/ship.log\"\n")
    code, out = _deploy(repo)
    assert code == 0, out


# covers D-239 clause 1 ("the tree's copy and each protected base's") -- F-U28 (only the first copy read) stayed green
def test_a_shape_only_the_protected_bases_copy_holds_refuses_the_deploy(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, "      - run: $SCRIPT\n")  # on main: the protected base's copy
    repo.git("checkout", "-q", "-b", "fix/named")
    repo.write(".github/workflows/release.yml", STEP.format("      - run: scripts/ship_it.sh\n"))
    repo.commit("the branch's copy names what it runs")
    code, out = _deploy(repo)
    assert code == 2, out
    assert "release.yml" in out and "run time" in out, out


# covers D-239 clause 1 -- the mirror of the case above: the base's copy names its file, the branch's does not
def test_a_shape_only_the_trees_copy_holds_refuses_the_deploy(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, "      - run: scripts/ship_it.sh\n")
    repo.git("checkout", "-q", "-b", "fix/unnamed")
    repo.write(".github/workflows/release.yml", STEP.format("      - run: $SCRIPT\n"))
    repo.commit("the branch's copy starts a name built at run time")
    code, out = _deploy(repo)
    assert code == 2, out
    assert "release.yml" in out and "run time" in out, out
