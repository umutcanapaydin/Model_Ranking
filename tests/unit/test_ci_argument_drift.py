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
