"""#549 (D-239): a dispatched deploy workflow could start a tree file without writing its name.

D-237 (#541) puts on the deploy surface every tree file whose name a dispatched deploy workflow writes. A run step
that starts a file by a pattern (`scripts/*.sh`), by a name built at run time (`$X`, `$(...)`, a backtick,
`${{ ... }}`, `eval`, `xargs`), or through a symlink git lists whose target is the file wrote no name, so that file
stayed exempt from the staleness check. The owner's ruling (2026-11-01, *translated*): the gate refuses the deploy.
Every declared deploy is refused, `fly deploy` included, while such a step is in a dispatched deploy workflow, and
the refusal names the workflow, the line, the shape, and says to write the file's name.
# covers D-239, #549
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from .test_deploy_gate_494 import _brief
from .test_deploy_gate_522 import STEP, _reviewed_workflow
from .test_deploy_gate_pin import GATE, ROOT, Repo, _env, _installed

#: The brief every planted repository here carries: the plain deploy, and the dispatch that makes `release.yml` a
#: deploy workflow.
BRIEF = _brief("fly deploy", "gh workflow run release")

PATTERNS = {
    "program-star": "      - run: scripts/*.sh\n",
    "program-question": "      - run: scripts/ship_?t.sh\n",
    "program-bracket": "      - run: scripts/ship_[i]t.sh\n",
    "program-brace": "      - run: scripts/ship_{it,x}.sh\n",
    "bash-operand": "      - run: bash scripts/*.sh\n",
    "bash-option-then-operand": "      - run: bash -e scripts/ship*.sh\n",
    "source-operand": "      - run: source scripts/ship*.sh\n",
    "dot-operand": "      - run: . scripts/ship*.sh\n",
    "python-operand": "      - run: python3 scripts/*.py\n",
    "after-a-wrapper": "      - run: sudo -E timeout 60 scripts/*.sh\n",
    "in-a-block-after-if": "      - run: |\n          if true; then\n            scripts/ship*.sh\n          fi\n",
    "bash-c-string": "      - run: bash -c 'scripts/*.sh'\n",
}

RUNTIME = {
    "variable": "      - run: $SCRIPT\n",
    "braced-variable": "      - run: \"${SCRIPT}\" --prod\n",
    "variable-prefix": "      - run: scripts/ship_${WHICH}.sh\n",
    "substitution": "      - run: $(printf 'scripts/ship_%s.sh' it)\n",
    "quoted-substitution": "      - run: \"$(ls scripts/ship*)\"\n",
    "backtick": "      - run: \"`printf scripts/ship_%s.sh it`\"\n",
    "expression": "      - run: ${{ inputs.script }}\n",
    "bash-variable": "      - run: bash \"$SCRIPT\"\n",
    "python-module-variable": "      - run: python -m \"$MODULE\"\n",
    "source-variable": "      - run: source \"$SCRIPT\"\n",
    "dot-variable": "      - run: . \"$SCRIPT\"\n",
    "source-process-substitution": "      - run: source <(cat scripts/ship_it.sh)\n",
    "bash-stdin-variable": "      - run: bash < \"$SCRIPT\"\n",
    "exec-variable": "      - run: exec \"$SCRIPT\"\n",
    "eval": "      - run: eval \"$COMMAND\"\n",
    "sh-c-variable": "      - run: sh -c \"$COMMAND\"\n",
    "for-loop": "      - run: |\n          for f in scripts/ship*.sh; do\n            \"$f\"\n          done\n",
    "for-loop-bash": "      - run: for f in scripts/ship*.sh; do bash \"$f\"; done\n",
    "xargs": "      - run: ls scripts | xargs -I{} bash scripts/{}\n",
    "find-exec": "      - run: find scripts -name 'ship*' -exec {} \\;\n",
    "continuation": "      - run: |\n          \"$SCRIPT\" \\\n            --prod\n",
    "after-a-pipe": "      - run: echo go | $SCRIPT\n",
    # `<<` inside quotes opens no here-document, so the lines after it are read.
    "after-a-quoted-heredoc-mark": "      - run: |\n          echo 'a <<EOF'\n          $SCRIPT\n          EOF\n",
    "in-a-case-body": "      - run: |\n          case \"$X\" in\n            a) $SCRIPT ;;\n            *) true ;;\n          esac\n",
}


def _dispatched(tmp_path: Path, step: str) -> Repo:
    """A repository whose `release.yml` holds `step`, dispatched by a declared `gh workflow run release`, both
    verdicts current at the commit that adds it: every deploy passes but for #549."""
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    repo.write("docs/project-brief.md", BRIEF)  # a record: the verdicts stay current
    repo.commit("the brief dispatches the workflow")
    return repo


def _deploy(repo: Repo, command: str = "fly deploy") -> tuple[int, str]:
    """The gate by hand, on one command line, as `python3 scripts/deploy_gate.py "<command>"`."""
    done = subprocess.run([sys.executable, str(GATE), command], cwd=repo.root, capture_output=True, text=True,
                          env=_env(), timeout=120)
    return done.returncode, done.stdout + done.stderr


@pytest.mark.parametrize("step", list(PATTERNS.values()), ids=list(PATTERNS))
def test_a_pattern_in_what_a_step_runs_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    repo = _dispatched(tmp_path, step)
    code, out = _deploy(repo)
    assert code == 2, out
    assert "release.yml" in out and "pattern" in out, out


@pytest.mark.parametrize("step", list(RUNTIME.values()), ids=list(RUNTIME))
def test_a_name_built_at_run_time_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    repo = _dispatched(tmp_path, step)
    code, out = _deploy(repo)
    assert code == 2, out
    assert "release.yml" in out and "run time" in out, out


@pytest.mark.parametrize(("link", "target", "step"), [
    ("scripts/deploy_link.sh", "ship_it.sh", "      - run: scripts/deploy_link.sh\n"),
    ("tools", "scripts", "      - run: tools/ship_it.sh\n"),
], ids=["to-a-file", "to-a-directory"])
def test_a_tracked_symlink_the_workflow_names_refuses_the_deploy(tmp_path: Path, link: str, target: str,
                                                                  step: str) -> None:
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    (repo.root / link).symlink_to(target)
    _reviewed_workflow(repo, STEP.format(step))  # commits the link with the workflow
    repo.write("docs/project-brief.md", BRIEF)
    repo.commit("the brief dispatches the workflow")
    code, out = _deploy(repo)
    assert code == 2, out
    assert "symlink" in out and link in out, out


def test_the_refusal_names_the_workflow_the_line_the_shape_and_what_to_write(tmp_path: Path) -> None:
    repo = _dispatched(tmp_path, "      - run: scripts/*.sh\n")
    code, out = _deploy(repo)
    assert code == 2, out
    # STEP's seventh line is the step.
    assert "release.yml line 7" in out, out
    assert "a pattern" in out and "`scripts/*.sh`" in out, out
    assert "write the file's name" in out, out


def test_deploy_check_fails_on_such_a_workflow_as_well(tmp_path: Path) -> None:
    """`make deploy-check` asks the gate's question with no command (AGENTS.md section 6): it fails too."""
    repo = _dispatched(tmp_path, "      - run: $SCRIPT\n")
    code, out = repo.check()
    assert code == 1, out
    assert "release.yml" in out and "run time" in out, out


@pytest.mark.parametrize("step", [
    "      - run: scripts/ship_it.sh \"$RUNNER_TEMP/state\"\n",
    "      - run: |\n          mkdir -p \"$STATE\"\n          rm -f \"$RUNNER_TEMP/x.zip\" 2>&1\n"
    "          echo \"$RUNNER_TEMP/bin\" >> \"$GITHUB_PATH\"\n"
    "          case \"$X\" in identical|ahead) ;; *) exit 1 ;; esac\n"
    "          gh api repos/o/r --jq '[.a[] | select(.b)][0].id'\n"
    "          python -m pip install -q -e .\n          bash scripts/ship_it.sh \"$1\"\n",
    "      - uses: actions/upload-artifact@v4\n        with:\n          path: |\n            ${{ runner.temp }}/x\n"
    "      - run: scripts/ship_it.sh\n",
    "      - run: |\n          cat <<EOF > notes.txt\n          $SCRIPT scripts/*.sh\n          EOF\n"
    "          scripts/ship_it.sh\n",
], ids=["a-named-script-with-an-expanded-operand", "expansions-and-patterns-in-operands-only",
        "an-expression-outside-a-run-value", "a-here-document-body"])
def test_a_step_that_names_what_it_runs_is_not_refused(tmp_path: Path, step: str) -> None:
    """Stays quiet (writing-a-control section 2): an expansion in an operand, a pattern in a `case` or a `jq` filter,
    a redirection's target, a `with:` value and a here-document's body start no file, so the deploy passes."""
    repo = _dispatched(tmp_path, step)
    code, out = _deploy(repo)
    assert code == 0, out


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("deploy_gate_549", GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_real_nightly_workflow_stays_quiet(tmp_path: Path) -> None:
    """This repository's nightly deploy workflow, the one `gh workflow run nightly-hosted.yml` dispatches (the
    brief's `Deploy commands:`), planted as a dispatched deploy workflow: `fly deploy` passes."""
    text = (ROOT / ".github" / "workflows" / "nightly-hosted.yml").read_text(encoding="utf-8")
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write(".github/workflows/nightly-hosted.yml", text)
    head = repo.commit("the real nightly workflow")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.write("docs/project-brief.md", _brief("fly deploy", "gh workflow run nightly-hosted.yml"))
    repo.commit("verdicts and the brief")
    code, out = _deploy(repo)
    assert code == 0, out


def test_the_real_tree_has_no_unnamed_start() -> None:
    """The same, read in this repository itself: its brief, its dispatched workflows, both copies, at both bases."""
    assert _gate().unnamed_starts(ROOT) == []


def test_a_tree_git_cannot_list_refuses_the_deploy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails closed (D-239 clause 4, writing-a-control section 5): when git cannot list the tree, which symlink a
    workflow names cannot be told, so every deploy is refused rather than let through."""
    repo = _dispatched(tmp_path, "      - run: scripts/ship_it.sh\n")
    gate = _gate()
    assert gate.unnamed_starts(repo.root) == [], "the control: a named step, a tree git lists"
    assert gate.judge([["fly", "deploy"]], repo.root) == 0
    gate._UNNAMED.clear()
    gate._SURFACES.clear()
    monkeypatch.setattr(gate, "_files", lambda root: None)
    assert gate.unnamed_starts(repo.root) is None
    assert gate.judge([["fly", "deploy"]], repo.root) == 2
