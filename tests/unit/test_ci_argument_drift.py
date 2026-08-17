"""M7-W1 — CI's command-line arguments still mean something to the code (REQ-ING-012).

**The defect this file exists because of.** D-118 made the budget vocabulary English in M6.
`contract-tests.yml` kept passing `sinirsiz`, `dusuk` and `orta` to `recommend` on three lines, all
of which `BUDGETS` would reject on sight. Nobody noticed for a milestone, because that workflow is
a Monday cron that has never fired: **an unrun step does not hold still, it rots.**

The general shape is the one M6 paid for four times. A workflow file is prose to every tool in this
repository — `ruff` does not read it, `mypy` does not read it, and `pytest` only ran it if the cron
ran. So the vocabularies are read from the CODE and the arguments are read from the YAML, and this
file asserts they agree. Neither list is typed out here; both are derived, which is the only form of
this check worth having.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest
import yaml

from app.workflows.categories import CATEGORIES
from app.workflows.recommend import BUDGETS

WORKFLOWS = sorted((pathlib.Path(__file__).resolve().parents[2] / ".github/workflows").glob("*.yml"))

_FLAG = re.compile(r"--(budget|task)[= ]+([A-Za-z0-9_-]+)")

VOCABULARIES: dict[str, set[str]] = {
    "budget": set(BUDGETS),
    "task": set(CATEGORIES),
}


def _run_scripts() -> list[tuple[str, str]]:
    """Every `run:` block in every workflow, as (file, script)."""
    blocks: list[tuple[str, str]] = []
    for path in WORKFLOWS:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job in (document.get("jobs") or {}).values():
            for step in job.get("steps") or []:
                script = step.get("run")
                if isinstance(script, str):
                    blocks.append((path.name, script))
    return blocks


def test_the_workflows_are_actually_parsed() -> None:
    """Guard against a derivation that finds nothing and passes everything."""
    assert WORKFLOWS, "no workflow files found — the glob is wrong"
    assert _run_scripts(), "no run: blocks parsed — the YAML walk is wrong"


def test_every_flag_value_ci_passes_is_one_the_code_accepts() -> None:
    """The citing test for the drift: CI may not name a value the vocabulary rejects."""
    offences: list[str] = []
    for name, script in _run_scripts():
        for flag, value in _FLAG.findall(script):
            if value not in VOCABULARIES[flag]:
                offences.append(
                    f"{name}: --{flag} {value!r} is not in {sorted(VOCABULARIES[flag])}"
                )
    assert not offences, "CI passes arguments the code rejects:\n  " + "\n  ".join(offences)


def test_the_check_can_fail() -> None:
    """V3C-02: a guard nobody has seen fail is a guard nobody knows works."""
    fabricated = "python -m app.workflows.recommend --db x.db --budget sinirsiz --task coding"
    found = _FLAG.findall(fabricated)
    assert ("budget", "sinirsiz") in found
    assert "sinirsiz" not in VOCABULARIES["budget"]


@pytest.mark.parametrize("flag", sorted(VOCABULARIES))
def test_each_vocabulary_is_non_empty(flag: str) -> None:
    """An empty vocabulary would make the drift check vacuous rather than strict."""
    assert VOCABULARIES[flag], f"{flag} vocabulary derived empty"


_MODULE = re.compile(r"python(?:3)? +-m +([A-Za-z_][A-Za-z0-9_.]*)")



def unresolvable_modules(blocks: list[tuple[str, str]]) -> list[str]:
    """Return one entry per `python -m app.*` invocation that does not resolve.

    Extracted from the test body deliberately. When the predicate lived inside the test, replacing
    it with `if False:` left the suite fully green — a guard that cannot fail, which is this
    project's most-repeated defect and which its own author reproduced here. As a named function it
    can be called with a known-bad input by a second test, so disabling it breaks something.
    """
    import importlib.util

    offences: list[str] = []
    for name, script in blocks:
        for module in _MODULE.findall(script):
            if not module.startswith("app."):
                continue  # stdlib and third-party entry points are not ours to pin
            if importlib.util.find_spec(module) is None:
                offences.append(f"{name}: `python -m {module}` does not resolve")
    return offences


def test_every_module_ci_invokes_actually_resolves() -> None:
    """The Tester's finding: this file checked flag VALUES and not whether the COMMAND exists.

    `python -m app.workflows.builder` — one letter off from a real module — would have sailed
    through every check in this repository and failed only on a cron that has never fired. The
    module names are read from the YAML and resolved against the installed package, so a typo is
    RED here rather than red in six days.
    """
    offences = unresolvable_modules(_run_scripts())
    assert not offences, "CI invokes modules that do not exist:\n  " + "\n  ".join(offences)


def test_the_module_check_can_fail() -> None:
    """V3C-02: drive the REAL predicate with a known-bad block and require it to complain.

    This is what makes the guard above falsifiable. It does not re-implement the check; it calls
    it, so `if False:` inside `unresolvable_modules` turns this red.
    """
    good = [("fake.yml", "python -m app.workflows.build --db x.db")]
    bad = [("fake.yml", "python -m app.workflows.builder --db x.db")]

    assert unresolvable_modules(good) == []
    offences = unresolvable_modules(bad)
    assert len(offences) == 1
    assert "app.workflows.builder" in offences[0]


def _build_step_script() -> str:
    """The one `run:` block that invokes the builder, straight out of the workflow."""
    for _name, script in _run_scripts():
        if "app.workflows.build " in script and "build-report.json" in script:
            return script
    msg = "the build step is no longer findable in the workflows"
    raise AssertionError(msg)


@pytest.mark.parametrize("exit_code", [0, 3])
def test_the_build_step_survives_its_own_exit_codes_under_bash_e(
    exit_code: int, tmp_path: pathlib.Path
) -> None:
    """EXECUTE the step under `bash -e`, because reading it is what missed the bug.

    All three review seats found the same defect and none of them could have found it from the
    YAML: the text was correct. GitHub runs `run:` blocks as `bash -e {0}`, and the previous
    version's `set -o pipefail` made a status-3 pipeline abort the script before its own exit-code
    handler — so the step stayed red on every run while claiming to tolerate exit 3.

    Exit 3 is the NORMAL outcome on a runner (D-101: no Epoch bundle there), so a step that cannot
    survive 3 is a step that never passes.
    """
    stub = tmp_path / "python"
    stub.write_text(
        "#!/bin/sh\n"
        'printf \'{"built": true, "required_operator_actions": ["stub"]}\\n\'\n'
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    script = tmp_path / "step.sh"
    script.write_text(_build_step_script(), encoding="utf-8")

    proc = subprocess.run(
        ["/bin/bash", "-e", str(script)],
        cwd=tmp_path,
        env={"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, (
        f"the build step exits {proc.returncode} when the builder exits {exit_code}; "
        f"under `bash -e` this step can never pass.\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    if exit_code == 3:
        assert "::notice::" in proc.stdout, "the degraded-build notice never printed"


def test_the_build_step_still_fails_on_a_real_failure(tmp_path: pathlib.Path) -> None:
    """Tolerating 3 must not have turned the step into one that tolerates everything."""
    stub = tmp_path / "python"
    stub.write_text("#!/bin/sh\nprintf '{\"built\": false}\\n'\nexit 2\n", encoding="utf-8")
    stub.chmod(0o755)
    script = tmp_path / "step.sh"
    script.write_text(_build_step_script(), encoding="utf-8")

    proc = subprocess.run(
        ["/bin/bash", "-e", str(script)],
        cwd=tmp_path,
        env={"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 2, "a real build failure must still fail the step"
