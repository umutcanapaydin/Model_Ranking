"""#522: a dispatched deploy workflow's run lines were read only for a bare recipe runner as their first word.

What a dispatched deploy workflow starts is code even when an upgrade shipped it byte for byte; but only the
workflow file was on the surface, and `_runs_unread` refused only a line whose first word was `make`, `gmake` or
`just`. A quoted line, `bash -c`, `xargs`, an expansion, and any line that started a script left that script
exemptible (the #501 security review's M2). D-232 clause 2: every file the workflow's text names is on the surface,
and a recipe runner anywhere, a `cd`, or a local `uses: ./` exempts nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_494 import _brief
from .test_deploy_gate_pin import Repo, _installed

STEP = "name: Release\non: workflow_dispatch\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n{}"


def _reviewed_workflow(repo: Repo, text: str) -> None:
    """The workflow on main, inside the reviewed head: both verdicts are rewritten at the commit that adds it."""
    repo.git("checkout", "-q", "main")
    repo.write(".github/workflows/release.yml", text)
    head = repo.commit("a deploy workflow")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts at the workflow")


@pytest.mark.parametrize("step", [
    '      - run: "make ship"\n',
    "      - run: bash -c 'make ship'\n",
    "      - run: ls | xargs make\n",
    "      - run: ${MAKE:-make} ship\n",
    "      - run: scripts/ship_it.sh\n",
    "      - run: python scripts/ship_it.sh\n",
    "      - run: |\n          cd scripts\n          ./ship_it.sh\n",
    "      - uses: ./.github/actions/ship\n",
    # The #522 review's B1 (each refused before #522, so a regression), and its M1.
    "      - run: /usr/bin/make ship\n",
    "      - run: ./make ship\n",
    "      - run: Make ship\n",
    "      - run: ~/.cargo/bin/just ship\n",
    "      - run: /usr/local/bin/gmake ship\n",
    "      - run: ./ship_it.sh\n        working-directory: scripts\n",
    "      - run: env -C scripts ./ship_it.sh\n",
    "      - run: env -Cscripts ./ship_it.sh\n",
    "      - run: env -iC scripts ./ship_it.sh\n",
    "      - run: $GITHUB_WORKSPACE/scripts/ship_it.sh\n",
    "      - run: ${{ github.workspace }}/scripts/ship_it.sh\n",
], ids=["quoted", "bash-c", "xargs", "expansion", "a-script", "an-interpreter", "cd-then-relative", "local-uses",
        "make-by-path", "make-dot-slash", "make-capital", "just-by-path", "gmake-by-path", "working-directory", "env-C",
        "env-C-attached", "env-C-in-a-cluster",
        "workspace-variable", "workspace-expression"])
def test_what_a_dispatched_workflow_starts_is_not_exempt(tmp_path: Path, step: str) -> None:
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/ship_it.sh", "echo ship\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ship_it.sh" in out, out


def test_a_workflow_of_setup_steps_still_leaves_a_plain_tooling_file_devflows(tmp_path: Path) -> None:
    """The control: checkout, an install, and the declared deploy script name nothing the upgrade shipped."""
    repo = _installed(tmp_path)
    steps = ("      - run: python -m venv .venv\n      - run: .venv/bin/python -m pip install -q -e .\n"
             "      - run: scripts/deploy_hosted_engine.sh \"$RUNNER_TEMP/state\"\n")
    _reviewed_workflow(repo, STEP.format(steps))
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code == 0, out


def test_a_lower_case_c_after_env_is_not_a_change_of_directory(tmp_path: Path) -> None:
    """The #522 review's R5: `bash -c` after an `env` on the same line is no `env -C`, so it does not empty the surface."""
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format("      - run: env FOO=1 bash -c 'echo hi'\n"))
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code == 0, out
