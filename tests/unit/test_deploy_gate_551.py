"""#551 (D-242): the starts D-239's mitigation left open refuse every deploy too.

D-239 refuses every deploy while a dispatched deploy workflow starts a file without writing its name, and named five
classes it did not read. The owner's ruling (2026-11-02, *translated*): "turn them all away".

1. A step whose shell is not a POSIX shell -- its `shell:`, or a `defaults: run: shell:` at workflow or job level
   (`pwsh`, `python`, `cmd`, a custom template), or a Windows runner, whose default shell is PowerShell.
2. A shell or interpreter that reads its program from standard input: a pipe, `-`, `bash -s`, a here-document or a
   here-string -- unless its `<` redirection names the file (D-239's reading).
3. More starters: `uv run`, `npx` and `poetry run` start the file their operand names; `make`'s targets' recipes,
   read from the Makefile, are read as run text in turn (a Makefile or target it cannot read refuses).
4. Code in an interpreter's own language (`python -c`, `perl -e`/`-E`, `node -e`, `ruby -e`).

Each refusing case fails before the fix; the quiet ones name what they run, and pass before and after.
# covers #551, D-242
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_522 import STEP, _reviewed_workflow
from .test_deploy_gate_549 import BRIEF, _deploy, _dispatched
from .test_deploy_gate_pin import Repo, _installed

#: A workflow whose steps are `{steps}`, with room for workflow-level and job-level keys.
WORKFLOW = "name: Release\non: workflow_dispatch\n{top}jobs:\n  a:\n{job}    steps:\n      - uses: actions/checkout@v4\n{steps}"
NAMED = "      - run: scripts/ship_it.sh\n"


def _planted(tmp_path: Path, workflow: str, files: dict[str, str] | None = None) -> Repo:
    """A repository whose `release.yml` is `workflow`, dispatched by the brief, with `files` beside it on main, both
    verdicts current at the commit that adds them: every deploy passes but for D-239 and D-242."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    for rel, body in (files or {}).items():
        repo.write(rel, body)
    _reviewed_workflow(repo, workflow)  # commits the files with the workflow
    repo.write("docs/project-brief.md", BRIEF)
    repo.commit("the brief dispatches the workflow")
    return repo


# --- clause 1: a step whose shell is not a POSIX shell ----------------------------------------------------------

SHELL_REFUSED = {
    "step-pwsh": WORKFLOW.format(top="", job="", steps="      - shell: pwsh\n        run: scripts/ship_it.sh\n"),
    "step-powershell": WORKFLOW.format(top="", job="", steps="      - run: scripts/ship_it.sh\n        shell: powershell\n"),
    "step-python": WORKFLOW.format(top="", job="", steps="      - run: print(1)\n        shell: python\n"),
    "step-cmd": WORKFLOW.format(top="", job="", steps="      - run: scripts\\ship_it.cmd\n        shell: cmd\n"),
    "step-bash-template": WORKFLOW.format(top="", job="", steps="      - run: scripts/ship_it.sh\n        shell: bash -e {0}\n"),
    "step-perl-template": WORKFLOW.format(top="", job="", steps="      - run: print 1\n        shell: perl {0}\n"),
    "step-quoted": WORKFLOW.format(top="", job="", steps="      - run: scripts/ship_it.sh\n        shell: 'pwsh'\n"),
    "step-expression": WORKFLOW.format(top="", job="", steps="      - run: scripts/ship_it.sh\n        shell: ${{ inputs.shell }}\n"),
    "workflow-defaults": WORKFLOW.format(top="defaults:\n  run:\n    shell: pwsh\n", job="", steps=NAMED),
    "workflow-defaults-python": WORKFLOW.format(top="defaults:\n  run:\n    shell: \"python\"\n", job="", steps=NAMED),
    "job-defaults": WORKFLOW.format(top="", job="    defaults:\n      run:\n        shell: cmd\n", steps=NAMED),
    "job-defaults-flow": WORKFLOW.format(top="", job="    defaults: {run: {shell: pwsh}}\n", steps=NAMED),
    "windows-runner": WORKFLOW.format(top="", job="    runs-on: windows-latest\n", steps=NAMED),
    "windows-runner-list": WORKFLOW.format(top="", job="    runs-on:\n      - self-hosted\n      - Windows\n", steps=NAMED),
    "runner-expression": WORKFLOW.format(top="", job="    runs-on: ${{ matrix.os }}\n", steps=NAMED),
}


@pytest.mark.parametrize("workflow", list(SHELL_REFUSED.values()), ids=list(SHELL_REFUSED))
def test_a_step_whose_shell_is_not_posix_refuses_the_deploy(tmp_path: Path, workflow: str) -> None:
    """covers #551, D-242 clause 1."""
    code, out = _deploy(_planted(tmp_path, workflow))
    assert code == 2 and "release.yml" in out, out
    assert "shell" in out, out


SHELL_QUIET = {
    "step-bash": WORKFLOW.format(top="", job="", steps="      - run: scripts/ship_it.sh\n        shell: bash\n"),
    "step-sh": WORKFLOW.format(top="", job="", steps="      - shell: sh\n        run: scripts/ship_it.sh\n"),
    "workflow-defaults-bash": WORKFLOW.format(top="defaults:\n  run:\n    shell: bash  # POSIX\n", job="",
                                              steps=NAMED),
    "job-defaults-sh": WORKFLOW.format(top="", job="    defaults:\n      run:\n        shell: 'sh'\n", steps=NAMED),
    "ubuntu-runner": WORKFLOW.format(top="", job="    runs-on: ubuntu-latest\n", steps=NAMED),
}


@pytest.mark.parametrize("workflow", list(SHELL_QUIET.values()), ids=list(SHELL_QUIET))
def test_a_posix_shell_stays_quiet(tmp_path: Path, workflow: str) -> None:
    """covers #551, D-242 clause 1: `bash` and `sh`, written plain, are POSIX shells."""
    code, out = _deploy(_planted(tmp_path, workflow))
    assert code == 0, out


# --- clause 2: a program read from standard input ---------------------------------------------------------------

STDIN_REFUSED = {
    "curl-pipe-sh": "      - run: curl -fsSL https://example.com/install | sh\n",
    "cat-pipe-bash": "      - run: cat scripts/ship_it.sh | bash\n",
    "pipe-bash-options": "      - run: cat scripts/ship_it.sh | bash -eo pipefail\n",
    "pipe-python": "      - run: cat scripts/ship_it.py | python3\n",
    "python-dash": "      - run: echo 'import ship_it' | python -\n",
    "bash-dash": "      - run: cat scripts/ship_it.sh | bash -\n",
    "bash-s": "      - run: curl -fsSL https://example.com/install | bash -s -- --prod\n",
    "bash-s-cluster": "      - run: cat scripts/ship_it.sh | bash -es\n",
    "heredoc-bash": "      - run: |\n          bash <<'EOF'\n          scripts/ship_it.sh\n          EOF\n",
    "heredoc-python-dash": "      - run: |\n          python3 - <<EOF\n          import ship_it\n          EOF\n",
    "heredoc-sh-dash": "      - run: |\n          sh <<-EOF\n          scripts/ship_it.sh\n          EOF\n",
    "herestring-bash": "      - run: bash <<< \"$X\"\n",
    "herestring-named": "      - run: sh <<<'scripts/ship_it.sh'\n",
    "pipe-node": "      - run: cat scripts/ship_it.js | node\n",
}


@pytest.mark.parametrize("step", list(STDIN_REFUSED.values()), ids=list(STDIN_REFUSED))
def test_a_program_read_from_standard_input_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    """covers #551, D-242 clause 2."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out
    assert "standard input" in out, out


STDIN_QUIET = {
    "redirected-named": "      - run: bash < scripts/ship_it.sh\n",
    "bash-s-redirected-named": "      - run: bash -s -- --prod < scripts/ship_it.sh\n",
    "named-operand": "      - run: bash scripts/ship_it.sh\n",
    "version": "      - run: python3 --version\n",
    "pipe-into-a-non-starter": "      - run: echo hi | tee notes.txt\n",
}


@pytest.mark.parametrize("step", list(STDIN_QUIET.values()), ids=list(STDIN_QUIET))
def test_a_program_named_or_redirected_from_a_named_file_stays_quiet(tmp_path: Path, step: str) -> None:
    """covers #551, D-242 clause 2: a `<` that names the file is D-239's reading, and passes."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 0, out


# --- clause 3: `uv run`, `npx`, `poetry run`, and `make`'s recipes ----------------------------------------------

RUNNER_REFUSED = {
    "uv-run-pattern": "      - run: uv run scripts/*.py\n",
    "uv-run-variable": "      - run: uv run \"$SCRIPT\" --prod\n",
    "uv-run-options-variable": "      - run: uv run --frozen --with httpx \"$SCRIPT\"\n",
    "uv-run-python-variable": "      - run: uv run python \"$SCRIPT\"\n",
    "uv-run-module-variable": "      - run: uv run -m \"$MODULE\"\n",
    "uv-global-option": "      - run: uv --directory . run $SCRIPT\n",
    "uv-run-stdin": "      - run: cat scripts/ship_it.py | uv run -\n",
    "uvx-expression": "      - run: uvx ${{ inputs.tool }}\n",
    "npx-variable": "      - run: npx \"$TOOL\"\n",
    "npx-yes-pattern": "      - run: npx --yes ./scripts/*.js\n",
    "npx-call": "      - run: npx -c \"$COMMAND\"\n",
    "poetry-run-variable": "      - run: poetry run \"$SCRIPT\"\n",
    "poetry-run-python-pattern": "      - run: poetry run python scripts/*.py\n",
    "poetry-global-option": "      - run: poetry -C . run \"$SCRIPT\"\n",
}


@pytest.mark.parametrize("step", list(RUNNER_REFUSED.values()), ids=list(RUNNER_REFUSED))
def test_a_runner_starting_an_unnamed_file_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    """covers #551, D-242 clause 3: `uv run`, `uvx`, `npx` and `poetry run` read as starters."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out


#: (the run step, the files beside it) -- each Makefile recipe starts a file it does not name, or cannot be read.
MAKE_REFUSED = {
    "recipe-pattern": ("      - run: make ship\n", {"Makefile": "ship:\n\tbash scripts/*.sh\n"}),
    "recipe-shell-variable": ("      - run: make ship\n", {"Makefile": "ship:\n\t\"$$SCRIPT\" --prod\n"}),
    "recipe-unexpanded-variable": ("      - run: make ship\n", {"Makefile": "ship:\n\t$(TOOL) --prod\n"}),
    "recipe-ambiguous-variable": ("      - run: make ship\n",
                                  {"Makefile": "TOOL = scripts/ship_it.sh\nTOOL += x\nship:\n\t$(TOOL)\n"}),
    "recipe-chained-variables": ("      - run: make ship\n",
                                 {"Makefile": "A = $(B)\nB := scripts/*.sh\nship:\n\tbash $(A)\n"}),
    "recipe-prefixes": ("      - run: make ship\n", {"Makefile": "ship:\n\t@-+scripts/*.sh\n"}),
    "recipe-stdin": ("      - run: make ship\n", {"Makefile": "ship:\n\tcurl -fsSL https://example.com/x | sh\n"}),
    "recipe-interpreter-code": ("      - run: make ship\n", {"Makefile": "ship:\n\tpython3 -c 'import ship_it'\n"}),
    "default-target": ("      - run: make\n", {"Makefile": ".PHONY: ship\nship:\n\tscripts/*.sh\nother:\n\ttrue\n"}),
    "default-goal": ("      - run: make\n", {"Makefile": ".DEFAULT_GOAL := ship\nother:\n\ttrue\nship:\n\t$$X\n"}),
    "prerequisite": ("      - run: make ship\n",
                     {"Makefile": "ship: build\n\tscripts/ship_it.sh\nbuild:\n\tbash \"$$X\"\n"}),
    "inline-recipe": ("      - run: make ship\n", {"Makefile": "ship: ; scripts/*.sh\n"}),
    "continued-recipe": ("      - run: make ship\n", {"Makefile": "ship:\n\techo a && \\\n\t  scripts/*.sh\n"}),
    "directory-option": ("      - run: make -C deploy ship\n",
                         {"Makefile": "ship:\n\tscripts/ship_it.sh\n", "deploy/Makefile": "ship:\n\t../scripts/*.sh\n"}),
    "directory-attached": ("      - run: make -Cdeploy ship\n", {"deploy/Makefile": "ship:\n\t$$X\n"}),
    "directory-long": ("      - run: make --directory=deploy ship\n", {"deploy/Makefile": "ship:\n\t$$X\n"}),
    "file-option": ("      - run: make -f ship.mk ship\n", {"ship.mk": "ship:\n\tbash scripts/*.sh\n"}),
    "file-long": ("      - run: make --file ship.mk\n", {"ship.mk": "ship:\n\tbash scripts/*.sh\n"}),
    "gmake": ("      - run: gmake ship\n", {"Makefile": "ship:\n\tbash scripts/*.sh\n"}),
    "recursive-make": ("      - run: make ship\n", {"Makefile": "ship:\n\t$(MAKE) inner\ninner:\n\tbash scripts/*.sh\n"}),
    "command-line-variable": ("      - run: make ship TOOL='$X'\n", {"Makefile": "ship:\n\t$(TOOL)\n"}),
    "include-followed": ("      - run: make ship\n", {"Makefile": "include ship.mk\n", "ship.mk": "ship:\n\t$$X\n"}),
    "make-under-a-wrapper": ("      - run: sudo -E make ship\n", {"Makefile": "ship:\n\tbash scripts/*.sh\n"}),
    "make-in-a-c-string": ("      - run: bash -c 'make ship'\n", {"Makefile": "ship:\n\tbash scripts/*.sh\n"}),
    # cannot be read: refuse (fail closed)
    "no-makefile": ("      - run: make ship\n", {}),
    "missing-file": ("      - run: make -f nope.mk ship\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
    "missing-target": ("      - run: make nope\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
    "variable-target": ("      - run: make \"$TARGET\"\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
    "variable-directory": ("      - run: make -C \"$DIR\" ship\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
    "missing-include": ("      - run: make ship\n", {"Makefile": "include nope.mk\nship:\n\tscripts/ship_it.sh\n"}),
    "non-posix-make-shell": ("      - run: make ship\n",
                             {"Makefile": "SHELL = python3\nship:\n\tscripts/ship_it.sh\n"}),
    "cd-before-make": ("      - run: cd deploy && make ship\n",
                       {"Makefile": "ship:\n\tscripts/ship_it.sh\n", "deploy/Makefile": "ship:\n\t$$X\n"}),
    "env-chdir-make": ("      - run: env -C deploy make ship\n",
                       {"Makefile": "ship:\n\tscripts/ship_it.sh\n", "deploy/Makefile": "ship:\n\t$$X\n"}),
    "eval-option": ("      - run: make --eval='ship: ; $$X' ship\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
}


@pytest.mark.parametrize(("step", "files"), list(MAKE_REFUSED.values()), ids=list(MAKE_REFUSED))
def test_a_make_recipe_starting_an_unnamed_file_refuses_the_deploy(tmp_path: Path, step: str,
                                                                    files: dict[str, str]) -> None:
    """covers #551, D-242 clause 3: `make`'s recipes are read as run text in turn."""
    code, out = _deploy(_planted(tmp_path, STEP.format(step), files))
    assert code == 2 and "release.yml" in out, out


RUNNER_QUIET: dict[str, tuple[str, dict[str, str]]] = {
    "uv-run-named": ("      - run: uv run scripts/ship_it.py \"$RUNNER_TEMP/state\"\n", {}),
    "uv-run-options-named": ("      - run: uv run --frozen --with httpx scripts/ship_it.py\n", {}),
    "uv-run-module": ("      - run: uv run -m scripts.ship_it\n", {}),
    "npx-named": ("      - run: npx --yes cowsay hi\n", {}),
    "poetry-run-named": ("      - run: poetry run python scripts/ship_it.py \"$1\"\n", {}),
    "python-module": ("      - run: python -m pip install x\n", {}),
    "make-named": ("      - run: make ship\n", {"Makefile": ".PHONY: ship\nship:\n\tbash scripts/ship_it.sh\n"}),
    "make-variable-named": ("      - run: make ship\n",
                            {"Makefile": "# the deploy\nSCRIPT ?= scripts/ship_it.sh\nRUN = bash $(SCRIPT)\n"
                                         "ship: check\n\t@$(RUN) \"$$RUNNER_TEMP/state\"\n"
                                         "check:\n\t-mkdir -p \"$$STATE\"\n"}),
    "make-default-named": ("      - run: make -j 4\n", {"Makefile": "ship:\n\tscripts/ship_it.sh\n"}),
    "make-directory-named": ("      - run: make -s -C deploy ship\n", {"deploy/Makefile": "ship:\n\t../scripts/ship_it.sh\n"}),
    "make-command-line-variable": ("      - run: make ship SCRIPT=scripts/ship_it.sh\n",
                                   {"Makefile": "ship:\n\tbash $(SCRIPT)\n"}),
    "make-recursive-named": ("      - run: make ship\n",
                             {"Makefile": "ship:\n\t$(MAKE) inner\ninner:\n\tscripts/ship_it.sh\n"}),
    "make-include-named": ("      - run: make ship\n",
                           {"Makefile": "-include absent.mk\ninclude ship.mk\n", "ship.mk": "ship:\n\tscripts/ship_it.sh\n"}),
}


@pytest.mark.parametrize(("step", "files"), list(RUNNER_QUIET.values()), ids=list(RUNNER_QUIET))
def test_a_runner_or_recipe_that_names_its_file_stays_quiet(tmp_path: Path, step: str, files: dict[str, str]) -> None:
    """covers #551, D-242 clause 3: a starter, a runner or a recipe naming its file passes."""
    code, out = _deploy(_planted(tmp_path, STEP.format(step), files))
    assert code == 0, out


# --- clause 4: code in an interpreter's own language ------------------------------------------------------------

CODE_REFUSED = {
    "python-c": "      - run: python -c 'import ship_it'\n",
    "python3-c-cluster": "      - run: python3 -Bc 'import ship_it'\n",
    "python-c-attached": "      - run: python3 -c\"import ship_it\"\n",
    "pypy-c": "      - run: pypy3 -c 'import ship_it'\n",
    "perl-e": "      - run: perl -e 'do \"scripts/ship_it.pl\"'\n",
    "perl-E": "      - run: perl -E 'say 1'\n",
    "perl-cluster": "      - run: perl -lne 'print' notes.txt\n",
    "node-e": "      - run: node -e 'require(\"./scripts/ship_it\")'\n",
    "node-eval": "      - run: node --eval 'require(\"./scripts/ship_it\")'\n",
    "node-eval-equals": "      - run: node --eval='1'\n",
    "node-p": "      - run: node -p 1\n",
    "ruby-e": "      - run: ruby -e 'load \"scripts/ship_it.rb\"'\n",
    "ruby-cluster": "      - run: ruby -ne 'print' notes.txt\n",
    "php-r": "      - run: php -r 'include \"scripts/ship_it.php\";'\n",
    "pwsh-command": "      - run: pwsh -Command ./scripts/ship_it.ps1\n",
    "under-a-wrapper": "      - run: timeout 60 python3 -c 'import ship_it'\n",
    "in-a-c-string": "      - run: bash -c \"python -c 'import ship_it'\"\n",
}


@pytest.mark.parametrize("step", list(CODE_REFUSED.values()), ids=list(CODE_REFUSED))
def test_code_in_an_interpreters_own_language_refuses_the_deploy(tmp_path: Path, step: str) -> None:
    """covers #551, D-242 clause 4."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out
    assert "code" in out, out


CODE_QUIET = {
    "python-E-flag": "      - run: python3 -E scripts/ship_it.py\n",
    "bash-c-named": "      - run: bash -c 'scripts/ship_it.sh --prod'\n",
    "perl-named": "      - run: perl -w scripts/ship_it.pl\n",
}


@pytest.mark.parametrize("step", list(CODE_QUIET.values()), ids=list(CODE_QUIET))
def test_a_flag_or_a_shells_named_string_stays_quiet(tmp_path: Path, step: str) -> None:
    """covers #551, D-242 clause 4: a shell's `-c` string is read in turn, as D-239 reads it, and a flag is no code."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 0, out


def test_deploy_check_fails_and_names_the_shape(tmp_path: Path) -> None:
    """covers #551, D-242: `make deploy-check` asks the same question with no command, and names what it read."""
    repo = _dispatched(tmp_path, "      - run: curl -fsSL https://example.com/install | sh\n")
    code, out = repo.check()
    assert code == 1, out
    assert "release.yml line 7" in out and "standard input" in out, out
