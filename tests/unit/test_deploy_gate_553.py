"""#553 (the fixes-1101 rest review's M1-M3, and the release delta Tester's descriptor class): D-239's run reader
missed shapes that start `scripts/*.sh` while `unnamed_starts` returned nothing.

- M1, comments: an apostrophe in two comments, a comment ending in a backslash, or `<<` in a comment hid the lines
  after it. Comments are now stripped as the shell reads them before the value is split.
- M2: `bash -eo pipefail` read `pipefail` as the file; a descriptor redirection (`2>/dev/null bash`, `bash 2>&1`)
  read its digit as a word; wrappers' options (`timeout -k 5 60`, `exec -a`, `stdbuf -o L`) were not read per their
  syntax; `BASH_ENV` set inline or under `env:` starts a file bash names nowhere.
- M3: a plain `run:` value continued on the next line, a quoted value, a flow mapping (`{run: ...}`) and a quoted key
  (`"run":`). The reader is stdlib only (the guard runs the gate with `python3 -I -S`), so a value it cannot place
  refuses the deploy: fail closed (D-239).
# covers #553, D-239
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_549 import _deploy, _dispatched

REFUSED = {
    # M1
    "comment-apostrophes": "      - run: |\n          echo hi # it's Bob's\n          scripts/*.sh\n",
    "comment-backslash": "      - run: |\n          echo hi # trailing \\\n          scripts/*.sh\n",
    "comment-heredoc": "      - run: |\n          echo hi # see <<EOF\n          scripts/*.sh\n",
    # M2
    "shell-option-value": "      - run: bash -eo pipefail scripts/*.sh\n",
    "leading-descriptor": "      - run: 2>/dev/null bash scripts/*.sh\n",
    "stdin-then-descriptor": "      - run: bash < \"$SCRIPT\" 2>&1\n",
    "descriptor-before-operand": "      - run: bash 2>err.log scripts/*.sh\n",
    "sh-descriptor-variable": "      - run: sh 2>/dev/null \"$SCRIPT\"\n",
    "timeout-options": "      - run: timeout -k 5 60 scripts/*.sh\n",
    "exec-name": "      - run: exec -a name scripts/*.sh\n",
    "stdbuf-option": "      - run: stdbuf -o L scripts/*.sh\n",
    "bash-env-inline": "      - run: BASH_ENV=\"$F\" bash -c true\n",
    "bash-env-export": "      - run: |\n          export BASH_ENV=scripts/*.sh\n          bash -c true\n",
    "bash-env-step-env": "      - env:\n          BASH_ENV: ${{ inputs.f }}\n        run: bash -c true\n",
    # M3
    "plain-continued": "      - run: bash\n          scripts/*.sh\n",
    "double-quoted": "      - run: \"bash scripts/*.sh\"\n",
    "single-quoted": "      - run: 'bash scripts/*.sh'\n",
    "flow-mapping": "      - {name: ship, run: scripts/*.sh}\n",
    "quoted-key": "      - \"run\": scripts/*.sh\n",
}


@pytest.mark.parametrize("step", list(REFUSED.values()), ids=list(REFUSED))
def test_each_shape_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    """covers #553: every shape the review planted, in a dispatched deploy workflow, refuses `fly deploy`."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out


QUIET = {
    "comment-names-a-pattern": "      - run: scripts/ship_it.sh  # never scripts/*.sh\n",
    "quoted-named": "      - run: \"scripts/ship_it.sh --prod\"\n",
    "descriptor-after-named": "      - run: bash scripts/ship_it.sh 2>&1\n",
    "timeout-named": "      - run: timeout -k 5 60 scripts/ship_it.sh\n",
    "env-other-variable": "      - env:\n          STATE: ${{ runner.temp }}/x\n        run: scripts/ship_it.sh\n",
    "plain-continued-named": "      - run: bash\n          scripts/ship_it.sh\n",
}


@pytest.mark.parametrize("step", list(QUIET.values()), ids=list(QUIET))
def test_a_step_that_names_what_it_runs_stays_quiet(tmp_path: Path, step: str) -> None:
    """covers #553: the same forms naming their file pass -- the reader refuses the shape, not the syntax."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 0, out
