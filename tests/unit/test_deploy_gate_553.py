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


# --- The #553 security review, round 1 (BLOCKING): what the first fix refused less than the reader before it. -------
# The value is now read both as before #553 and as now, and every start either reading finds refuses (R2).

REVIEW_REFUSED = {
    # B1: a `#` inside `${...}`, `$'...'` or backticks is no comment
    "hash-in-parameter-expansion": "      - run: script=${entry%% #*}; bash \"$script\"\n",
    "hash-in-ansi-c-quote": "      - run: echo $'it\\'s # ' ; bash scripts/*.sh\n",
    "hash-in-backticks": "      - run: echo `echo hi #x` ; bash scripts/*.sh\n",
    # B2: the digits before a redirection after whitespace were a value
    "timeout-duration-then-redirect": "      - run: timeout 60 >/dev/null scripts/*.sh\n",
    "nice-value-then-redirect": "      - run: nice -n 5 >log scripts/*.sh\n",
    "python-w-value-then-redirect": "      - run: python -W 2 >x scripts/*.py\n",
    # B3: `env -S`'s value is the command line
    "env-split-string-quoted": "      - run: env -S 'bash scripts/*.sh'\n",
    "env-split-string-variable": "      - run: env -S \"$CMD\"\n",
    # M1: YAML escapes decoded once, `\x` and `\u` included
    "escaped-tab-before-pattern": "      - run: \"bash scripts/\\\\t*.sh\"\n",
    "hex-escaped-star": "      - run: \"bash scripts/\\x2a.sh\"\n",
    "hex-escaped-dollar": "      - run: \"bash \\x24SCRIPT\"\n",
    # M2: perl's -X is a flag
    "perl-flag-cluster": "      - run: perl -wX scripts/*.pl\n",
    # M3
    "space-before-colon": "      - run : scripts/*.sh\n",
    "quoted-key-space-before-colon": "      - \"run\" : scripts/*.sh\n",
    "explicit-key": "      - ? run\n        : scripts/*.sh\n",
    "anchor": "      - run: &a scripts/ship_it.sh\n",
    "tag": "      - run: !!str scripts/ship_it.sh\n",
    "folded-more-indented": "      - run: >\n          echo a\n            scripts/*.sh\n",
    "bash-env-flow-mapping": "      - env: {BASH_ENV: \"${{ inputs.f }}\"}\n        run: bash -c true\n",
    "shell-option-cluster-o-first": "      - run: bash -oe pipefail scripts/*.sh\n",
    "named-descriptor": "      - run: bash {fd}>x scripts/*.sh\n",
}


@pytest.mark.parametrize("step", list(REVIEW_REFUSED.values()), ids=list(REVIEW_REFUSED))
def test_what_the_review_found_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    """covers #553 (its security review's B1-B3, M1-M3)."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out


REVIEW_QUIET = {
    # M4: `ENV` is read by an interactive sh only, and `ENV:` is a common workflow name
    "env-named-env": "      - env:\n          ENV: ${{ inputs.environment }}\n        run: scripts/ship_it.sh\n",
    "quoted-value-then-comment": "      - run: \"scripts/ship_it.sh\"  # the release\n",
}


@pytest.mark.parametrize("step", list(REVIEW_QUIET.values()), ids=list(REVIEW_QUIET))
def test_what_the_review_found_over_refused_stays_quiet(tmp_path: Path, step: str) -> None:
    """covers #553 (its security review's M4)."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 0, out


def test_env_split_string_still_names_a_deploy_workflow() -> None:
    """covers #553 (its security review's B3): `run: env -S fly deploy` is a deploy, as it was before #553."""
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("deploy_gate_553", root / "scripts" / "deploy_gate.py")
    assert spec and spec.loader
    gate = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root / "scripts"))
    spec.loader.exec_module(gate)
    text = "jobs:\n  a:\n    steps:\n      - run: env -S fly deploy --remote-only\n"
    assert gate._runs_deploy(text, [["fly", "deploy"]])
