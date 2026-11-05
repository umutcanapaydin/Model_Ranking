"""#580 (the security review of #552's owner bundle, `docs/reviews/owner-bundle-552-security.md`): the security claims
of the nightly's silent-sources notice, held by a test.

The workflow is the owner's to change, so until the owner applies the bundle these read the workflow the proposal's
patch makes -- applied to a scratch copy of the installed file --, and the installed file itself once it holds the
`notice` job. Either way the reading is never empty.

- M1: the refresh job's silent step never fails the job (`continue-on-error`), so it never skips the deploy.
- M2: only `notice` holds `issues: write`; it runs only on `refs/heads/main`; it checks nothing out and uses no action.
- M3: the header names the three jobs.
- R2: the title is fixed in the workflow, the script's; only the body comes from the refresh.
# covers #580, D-243
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
INSTALLED = REPO / ".github" / "workflows" / "nightly-hosted.yml"
PROPOSAL_DOC = REPO / "docs" / "proposals" / "nightly-silent-sources.md"
sys.path.insert(0, str(REPO / "scripts"))
import silent_sources  # noqa: E402


@pytest.fixture(scope="module")
def workflow_text(tmp_path_factory: pytest.TempPathFactory) -> str:
    installed = INSTALLED.read_text(encoding="utf-8")
    if re.search(r"^  notice:", installed, re.M):
        return installed
    patch = re.search(r"^```diff\n(.*?)^```$", PROPOSAL_DOC.read_text(encoding="utf-8"), re.S | re.M)
    assert patch, "the proposal carries no patch"
    scratch = tmp_path_factory.mktemp("nightly")
    for rel in (".github/workflows/nightly-hosted.yml", "scripts/ci/nightly-hosted.yml"):
        (scratch / rel).parent.mkdir(parents=True, exist_ok=True)
        (scratch / rel).write_text((REPO / rel).read_text(encoding="utf-8"), encoding="utf-8")
    done = subprocess.run(["git", "apply", "-"], cwd=scratch, input=patch.group(1), text=True, capture_output=True,
                          check=False)
    assert done.returncode == 0, done.stderr
    return (scratch / ".github/workflows/nightly-hosted.yml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def jobs(workflow_text: str) -> dict[str, Any]:
    found = yaml.safe_load(workflow_text)["jobs"]
    assert "notice" in found, "the reading is empty: no notice job"
    return found


def test_580_m2_only_the_notice_job_may_write_issues(jobs: dict[str, Any]) -> None:
    assert jobs["notice"]["permissions"] == {"issues": "write"}
    assert [name for name, job in jobs.items() if "issues" in (job.get("permissions") or {})] == ["notice"]


def test_580_m2_the_notice_job_runs_only_on_main(jobs: dict[str, Any]) -> None:
    assert "github.ref == 'refs/heads/main'" in str(jobs["notice"]["if"])


def test_580_m2_the_notice_job_checks_nothing_out_and_uses_no_action(jobs: dict[str, Any]) -> None:
    steps = jobs["notice"]["steps"]
    assert steps and all("uses" not in step for step in steps), steps


def test_580_m1_the_silent_step_never_fails_the_refresh_job(jobs: dict[str, Any]) -> None:
    silent = next(step for step in jobs["refresh"]["steps"] if step.get("id") == "silent")
    assert silent.get("continue-on-error") is True, silent


def test_580_r2_the_title_is_fixed_and_only_the_body_is_the_refreshs(jobs: dict[str, Any]) -> None:
    run = jobs["notice"]["steps"][0]["run"]
    assert f"title='{silent_sources.TITLE}'" in run, run
    assert "--input" not in run and "--body-file" in run, run
    assert "jq -r '.body'" in run, run


def test_580_m3_the_header_names_three_jobs(workflow_text: str) -> None:
    header = workflow_text.split("\nname:", 1)[0]
    assert "Two jobs" not in header and "Three jobs" in header and "notice" in header, header
