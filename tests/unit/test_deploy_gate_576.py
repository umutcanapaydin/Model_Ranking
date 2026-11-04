"""#576: what the #553 security review's round 2 left in D-239's reader (`docs/reviews/fix-issue-553-security.md`).
None was a regression; each passed at the base too.

- M5: a double-quoted `run:` value's `\\n` escape is decoded into one line; shlex reads the newline as a blank, so the
  second command was never read as one.
- R1: `BASH_ENV` written to `$GITHUB_ENV` makes every later step's bash start that file.
- R3: `env -S "fly deploy"` and `nice -n 5 2>&1 fly deploy` were not seen as deploys, so their workflow was not read.
- R4: `perl -X`, `ruby -W` (no value for either) and `bash -oc pipefail '<cmd>'` (the `-c` string is the first
  operand after `-o`'s value) passed.
- R5: a folded value is read line by line and joined, so the evidence line counted its commands twice.
# covers #576, D-239
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_494 import _brief
from .test_deploy_gate_522 import STEP
from .test_deploy_gate_549 import _deploy, _dispatched, _reviewed_workflow
from .test_deploy_gate_556 import _d239_line
from .test_deploy_gate_pin import _installed

REFUSED = {
    "m5-decoded-newline": '      - run: "echo hi\\nbash scripts/\\x2a.sh"\n',
    "r1-bash-env-printf": "      - run: printf 'BASH_ENV=%s\\n' \"$F\" >> \"$GITHUB_ENV\"\n",
    "r1-bash-env-heredoc": "      - run: |\n          cat >> \"$GITHUB_ENV\" <<EOF\n          BASH_ENV=$F\n          EOF\n",
    "r4-perl-x": "      - run: perl -X scripts/*.pl\n",
    "r4-ruby-w": "      - run: ruby -W scripts/*.rb\n",
    "r4-bash-oc": "      - run: bash -oc pipefail 'scripts/*.sh'\n",
}


@pytest.mark.parametrize("step", list(REFUSED.values()), ids=list(REFUSED))
def test_576_each_shape_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    repo = _dispatched(tmp_path, step)
    code, out = _deploy(repo)
    assert code == 2 and "release.yml" in out, out


@pytest.mark.parametrize("deploy", ['env -S "fly deploy"', "nice -n 5 2>&1 fly deploy"], ids=["env-S", "redirect"])
def test_576_r3_a_wrapped_deploy_makes_its_workflow_a_deploy_workflow(tmp_path: Path, deploy: str) -> None:
    """Not dispatched by the brief: the workflow is a deploy workflow only because a line runs the declared command,
    so its pattern start refuses only once that line is seen as one."""
    repo = _installed(tmp_path)
    brief = (repo.root / "docs" / "project-brief.md").read_text(encoding="utf-8")
    assert brief == _brief("fly deploy"), "the control: the brief declares fly deploy and dispatches no workflow"
    _reviewed_workflow(repo, STEP.format(f"      - run: {deploy}\n      - run: bash scripts/*.sh\n"))
    code, out = _deploy(repo)
    assert code == 2 and "release.yml" in out, out


def test_576_r5_a_folded_value_counts_its_commands_once(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, "      - run: >\n          scripts/ship_it.sh\n          --now\n")
    _code, out = repo.check()
    assert "1 run command(s)" in _d239_line(out), out


def test_576_the_control_a_named_file_still_passes(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, '      - run: "echo hi\\nbash scripts/ship_it.sh"\n')
    code, out = _deploy(repo)
    assert code == 0, out
