"""#387 (D-217): the hosted engine is refreshed and deployed each night by a GitHub Actions workflow.

`scripts/nightly_hosted.sh` is what the workflow's two jobs run:

    scripts/nightly_hosted.sh refresh <state>   the `refresh` job: no secret, fetches and builds
    scripts/nightly_hosted.sh deploy <state>    the `deploy` job: the gate, then the deploy script

The refresh is run with a stand-in interpreter that records how it was called. The deploy is run in a
scratch repository holding this tree's scripts, brief and fly.toml, with stand-ins for `fly` and `curl`
first on its PATH, so no request leaves this machine; its gate is the real one, reading verdicts the test
writes. The workflow itself is the owner's to apply (`.github/workflows/**`): the agent's proposal is
`scripts/ci/nightly-hosted.yml`, and its shape is held here.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from .test_api_v1 import _seeded_db

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "nightly_hosted.sh"
PROPOSAL = REPO / "scripts" / "ci" / "nightly-hosted.yml"
INSTALLED = REPO / ".github" / "workflows" / "nightly-hosted.yml"
_CLEAN_GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
_COPIED = (".gitignore", "fly.toml", "docs/project-brief.md", "scripts/nightly_hosted.sh", "scripts/deploy_hosted_engine.sh",
           "scripts/deploy_gate.py", "scripts/brief_fields.py")


def _git(*args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                          check=True, capture_output=True, text=True, env=_CLEAN_GIT_ENV).stdout.strip()


def _run(env: dict[str, str], *args: str, script: Path = SCRIPT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(script), *args], capture_output=True, text=True, timeout=120,
                          env=env, check=False)


# --- the refresh job -------------------------------------------------------------------------------------

def _refresh_env(tmp_path: Path, code: int) -> tuple[dict[str, str], Path, Path]:
    """A stand-in interpreter that records its arguments and APP_BUILD, and exits with `code`."""
    calls, output = tmp_path / "python-calls.txt", tmp_path / "github-output.txt"
    fake = tmp_path / "python"
    fake.write_text(f'#!/bin/sh\necho "APP_BUILD=$APP_BUILD FLY=${{FLY_API_TOKEN:-}} $*" >> "{calls}"\n'
                    f"exit {code}\n", encoding="utf-8")
    fake.chmod(0o755)
    env = {k: v for k, v in _CLEAN_GIT_ENV.items() if k not in ("FLY_API_TOKEN", "GITHUB_TOKEN", "GH_TOKEN")}
    env |= {"PYTHON": str(fake), "GITHUB_OUTPUT": str(output)}
    return env, calls, output


def test_the_refresh_runs_the_cycle_on_the_kept_state_stamped_with_this_release(tmp_path: Path) -> None:
    env, calls, output = _refresh_env(tmp_path, 0)
    state = tmp_path / "state"
    done = _run(env, "refresh", str(state))
    assert done.returncode == 0, done.stdout + done.stderr
    sha = _git("-C", str(REPO), "rev-parse", "--short=7", "HEAD")
    called = calls.read_text(encoding="utf-8")
    assert f"APP_BUILD=release-{sha} " in called, called
    assert f"-m app.workflows.refresh --db {state}/advisor.db --fetch-epoch" in called, called
    assert "outcome=published" in output.read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize(("code", "outcome", "passes"), [(1, "unchanged", True), (2, "failed", False),
                                                         (3, "refused", False), (4, "busy", False)])
def test_only_a_night_that_kept_its_data_passes_so_only_it_is_kept(tmp_path: Path, code: int, outcome: str,
                                                                    passes: bool) -> None:
    """D-217 clause 3: the workflow uploads the state only when the job passes; a failed night uploads
    nothing, so the last good state stands."""
    env, _calls, output = _refresh_env(tmp_path, code)
    done = _run(env, "refresh", str(tmp_path / "state"))
    assert (done.returncode == 0) is passes, done.stdout + done.stderr
    assert f"outcome={outcome}" in output.read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("secret", ["FLY_API_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"])
def test_the_refresh_refuses_to_run_beside_a_secret(tmp_path: Path, secret: str) -> None:
    """D-217 clause 2: the code that parses untrusted data never runs beside a token."""
    env, calls, _output = _refresh_env(tmp_path, 0)
    done = _run(env | {secret: "x"}, "refresh", str(tmp_path / "state"))
    assert done.returncode != 0 and secret in done.stderr
    assert not calls.exists()


@pytest.mark.parametrize("args", [[], ["refresh"], ["deploy"], ["publish", "x"], ["refresh", "x", "y"]])
def test_anything_but_one_mode_and_one_state_is_refused(tmp_path: Path, args: list[str]) -> None:
    env, calls, _output = _refresh_env(tmp_path, 0)
    assert _run(env, *args).returncode == 2
    assert not calls.exists()


# --- the deploy job --------------------------------------------------------------------------------------

def _verdict(name: str, head: str) -> str:
    return (f"---\nrecord_type: review\nid: {name}\nstatus: draft\nseat: independent\n---\n# {name}\n\n"
            f"**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\n\nPASS\n")


def _scratch(tmp_path: Path, *, stale: bool = False, health: str | None = None,
             data_by: str | None = None) -> tuple[Path, Path, Path, dict[str, str]]:
    """A scratch repository on its origin's main, with this tree's scripts and brief, and current release
    verdicts; `stale` commits a code change after them. `health` is what /health answers, by default the
    build fly was given; `data_by` names the release that built the state's data, by default HEAD's."""
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    _git("init", "-q", "--bare", "-b", "main", str(origin))
    _git("clone", "-q", str(origin), str(repo))
    for rel in _COPIED:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, repo / rel)
    _git("-C", str(repo), "add", ".")
    _git("-C", str(repo), "commit", "-qm", "scratch")
    head = _git("-C", str(repo), "rev-parse", "HEAD")
    for name in ("release-security", "release-tester"):
        (repo / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
        (repo / "docs" / "reviews" / f"{name}.md").write_text(_verdict(name, head), encoding="utf-8")
    _git("-C", str(repo), "add", ".")
    _git("-C", str(repo), "commit", "-qm", "the release verdicts")
    if stale:
        (repo / "scripts" / "unreviewed.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        _git("-C", str(repo), "add", ".")
        _git("-C", str(repo), "commit", "-qm", "code nobody reviewed")
    _git("-C", str(repo), "push", "-q", "origin", "main")
    state = tmp_path / "state"
    state.mkdir()
    _seeded_db(state / "advisor.db")
    built = data_by or f"release-{_git('-C', str(repo), 'rev-parse', '--short=7', 'HEAD')}"
    (state / "advisor.db.refresh.json").write_text(f'{{"served_built_by": "{built}"}}', encoding="utf-8")
    bin_dir, calls = tmp_path / "bin", tmp_path / "fly-calls.txt"
    bin_dir.mkdir()
    (bin_dir / "fly").write_text(f'#!/bin/sh\necho "FLY_API_TOKEN=$FLY_API_TOKEN $*" >> "{calls}"\n',
                                 encoding="utf-8")
    answer = (f'echo \'{{"status": "ok", "build": "{health}"}}\'' if health else
              f'build=$(tr " " "\\n" < "{calls}" | sed -n "s/^APP_BUILD=//p" | tail -1)\n'
              'echo "{\\"status\\": \\"ok\\", \\"build\\": \\"$build\\"}"')
    (bin_dir / "curl").write_text(f"#!/bin/sh\n{answer}\n", encoding="utf-8")
    for stand_in in ("fly", "curl"):
        (bin_dir / stand_in).chmod(0o755)
    env = {**_CLEAN_GIT_ENV, "PATH": f"{bin_dir}:{os.environ['PATH']}", "PYTHON": sys.executable,
           "DEPLOY_HEALTH_TRIES": "1", "FLY_API_TOKEN": "fly-test-token"}
    env.pop("MODEL_RANKING_REPO", None)
    env.pop("MODEL_RANKING_SERVED", None)
    return repo, state, calls, env


def _deploy(repo: Path, state: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return _run(env, "deploy", str(state), script=repo / "scripts" / "nightly_hosted.sh")


def test_a_night_with_current_verdicts_deploys_the_kept_state_and_checks_health(tmp_path: Path) -> None:
    repo, state, calls, env = _scratch(tmp_path)
    done = _deploy(repo, state, env)
    assert done.returncode == 0, done.stdout + done.stderr
    called = calls.read_text(encoding="utf-8")
    sha = _git("-C", str(repo), "rev-parse", "--short", "HEAD")
    assert "deploy " in called and f"APP_BUILD=release-{sha}-data-" in called and "--ha=false" in called, called
    assert "FLY_API_TOKEN=fly-test-token" in called
    assert (repo / "build" / "hosted" / "advisor.db").is_file()


def test_a_stale_gate_deploys_nothing_and_fails_the_night(tmp_path: Path) -> None:
    """D-217 clause 4: unreviewed code on main ships with no night's data."""
    repo, state, calls, env = _scratch(tmp_path, stale=True)
    done = _deploy(repo, state, env)
    assert done.returncode != 0
    assert not calls.exists()
    assert "deploy-check FAIL" in done.stdout + done.stderr
    assert not (repo / "build" / "hosted" / "advisor.db").exists()


def test_a_build_fly_already_serves_is_not_deployed_again(tmp_path: Path) -> None:
    """D-217 clause 5: a night deploys only what is new."""
    repo, state, _calls, env = _scratch(tmp_path)
    probe = _run(env, "deploy", str(state), script=repo / "scripts" / "nightly_hosted.sh")
    assert probe.returncode == 0, probe.stdout + probe.stderr
    live = re.search(r"APP_BUILD=(\S+)", (tmp_path / "fly-calls.txt").read_text(encoding="utf-8"))
    assert live
    (tmp_path / "fly-calls.txt").unlink()
    (tmp_path / "bin" / "curl").write_text(f"#!/bin/sh\necho '{{\"build\": \"{live.group(1)}\"}}'\n",
                                           encoding="utf-8")
    again = _deploy(repo, state, env)
    assert again.returncode == 0, again.stdout + again.stderr
    assert not (tmp_path / "fly-calls.txt").exists()
    assert "already serves" in again.stdout


def test_data_another_release_built_is_refused_whatever_the_environment_accepts(tmp_path: Path) -> None:
    """D-217 clause 5: the night never sets DEPLOY_ACCEPT_DATA_FROM, and drops one it was given."""
    repo, state, calls, env = _scratch(tmp_path, data_by="release-0000000")
    done = _deploy(repo, state, env | {"DEPLOY_ACCEPT_DATA_FROM": "release-0000000"})
    assert done.returncode != 0 and "release-0000000" in done.stdout + done.stderr
    assert not calls.exists()


def test_the_tree_the_gate_judged_is_the_tree_that_ships(tmp_path: Path) -> None:
    """The #387 security review's M2: MODEL_RANKING_REPO, passed through, pointed the deploy script at
    another tree than the one the night's gate had just judged."""
    repo, state, calls, env = _scratch(tmp_path)
    elsewhere = tmp_path / "unreviewed"
    elsewhere.mkdir()
    done = _deploy(repo, state, env | {"MODEL_RANKING_REPO": str(elsewhere)})
    assert done.returncode == 0, done.stdout + done.stderr
    assert calls.exists() and (repo / "build" / "hosted" / "advisor.db").is_file()
    assert not (elsewhere / "build").exists()


def test_a_deploy_with_no_kept_state_is_refused(tmp_path: Path) -> None:
    repo, state, calls, env = _scratch(tmp_path)
    (state / "advisor.db").unlink()
    done = _deploy(repo, state, env)
    assert done.returncode != 0 and not calls.exists()


def test_the_night_is_a_deploy_command_the_gate_judges() -> None:
    """D-217 clause 6: an agent that runs the night's deploy is judged as one that runs the deploy script."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import deploy_gate
    finally:
        sys.path.remove(str(REPO / "scripts"))
    assert deploy_gate.deploy_in([["scripts/nightly_hosted.sh", "deploy", "state"]], REPO)
    assert deploy_gate.deploy_in([["/abs/scripts/nightly_hosted.sh", "refresh", "state"]], REPO)
    # The #387 security review's M1: starting the workflow by hand is a deploy as well.
    assert deploy_gate.deploy_in([["gh", "workflow", "run", "nightly-hosted.yml", "--ref", "main"]], REPO)


def test_the_kept_state_is_public_so_it_may_hold_nothing_the_public_copy_leaves_out() -> None:
    """The #387 security review's M4: the repository is public, so any signed-in GitHub user can download
    the `hosted-state` artifact, the full artifact before `app.workflows.public` strips it. That is safe
    only while nothing is left out (D-186, D-193). A source put in LEFT_OUT fails this test until the night
    keeps only the public copy, or keeps the state somewhere private (D-217, revisit)."""
    from app.workflows.public import LEFT_OUT

    assert not LEFT_OUT, LEFT_OUT


# --- the workflow --------------------------------------------------------------------------------------

def _workflow() -> dict[Any, Any]:
    loaded = yaml.safe_load(PROPOSAL.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _steps(job: str) -> list[dict[str, Any]]:
    steps = _workflow()["jobs"][job]["steps"]
    assert isinstance(steps, list) and steps
    return steps


def test_the_workflow_runs_each_night_and_by_hand_one_at_a_time() -> None:
    flow = _workflow()
    on = flow.get("on", flow.get(True))  # YAML 1.1 reads a bare `on` as true
    assert on["schedule"] and all(re.fullmatch(r"[\d*/, -]+", s["cron"]) for s in on["schedule"])
    assert "workflow_dispatch" in on
    assert set(on) == {"schedule", "workflow_dispatch"}, "never on a push or a pull request"
    assert flow["concurrency"]["cancel-in-progress"] is False
    assert flow["permissions"] == {"contents": "read"}


def test_the_refresh_job_holds_no_secret_and_keeps_no_credential() -> None:
    """D-217 clause 2."""
    flow = _workflow()
    refresh = flow["jobs"]["refresh"]
    assert refresh["permissions"] == {"contents": "read", "actions": "read"}
    text = yaml.safe_dump(refresh)
    assert "secrets." not in text and "FLY_API_TOKEN" not in text
    for step in refresh["steps"]:
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False
        if "nightly_hosted.sh refresh" in str(step.get("run", "")):
            assert not step.get("env"), "the cycle runs with no token in its environment"
        if "GITHUB_TOKEN" in yaml.safe_dump(step):
            assert "nightly_hosted.sh" not in str(step.get("run", "")), "the token reaches only its own step"
    assert any("nightly_hosted.sh refresh" in str(s.get("run", "")) for s in refresh["steps"])


def test_only_a_night_that_kept_its_data_is_uploaded_for_ninety_days() -> None:
    """D-217 clause 3."""
    uploads = [s for s in _steps("refresh") if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(uploads) == 1
    upload = uploads[0]
    assert upload["with"]["name"] == "hosted-state" and int(upload["with"]["retention-days"]) == 90
    assert "if" not in upload or "always()" not in str(upload["if"]), "a failed night uploads nothing"
    outputs = _workflow()["jobs"]["refresh"]["outputs"]
    assert "outcome" in outputs


def test_both_jobs_run_only_on_main_and_the_token_is_an_environment_s_only_main_reaches() -> None:
    """The #387 security review's B1: a run dispatched on another branch ran that branch's scripts with
    the repository's token in reach. The token is the `fly-production` environment's secret, which the
    owner limits to main (docs/owner-actions.md), and neither job runs off main."""
    jobs = _workflow()["jobs"]
    for name in ("refresh", "deploy"):
        assert "github.ref == 'refs/heads/main'" in str(jobs[name]["if"]), name
    assert jobs["deploy"]["environment"] == "fly-production"
    assert "environment" not in jobs["refresh"]


def test_the_state_is_read_only_from_this_file_s_runs_whose_commit_is_on_main() -> None:
    """D-217 clause 3, and the #387 security review's R2: an artifact of the same name from a pull
    request's run, a fork's, another workflow's or a tag named `main` is never read."""
    fetch = [s for s in _steps("refresh") if "hosted-state" in str(s.get("run", ""))]
    assert len(fetch) == 1
    run = fetch[0]["run"]
    for held in ('.event == "schedule" or .event == "workflow_dispatch"',
                 ".head_repository.full_name == env.GITHUB_REPOSITORY",
                 '.path == ".github/workflows/nightly-hosted.yml"', 'compare/$sha...main',
                 "identical|ahead", '.expired == false', '"$GITHUB_RUN_ID"',
                 "advisor.db advisor.db.refresh.json"):
        assert held in run, held


def test_the_fly_binary_that_receives_the_token_is_pinned() -> None:
    """The #387 security review's M5: `setup-flyctl` installs the latest flyctl unless told."""
    setup = [s for s in _steps("deploy") if str(s.get("uses", "")).startswith("superfly/flyctl-actions/")]
    assert len(setup) == 1 and re.fullmatch(r"\d+\.\d+\.\d+", str(setup[0]["with"]["version"]))


def test_the_deploy_job_holds_the_token_and_runs_the_night_after_the_refresh() -> None:
    deploy = _workflow()["jobs"]["deploy"]
    assert deploy["needs"] == "refresh"
    assert "outcome" in str(deploy["if"])
    runs = [s for s in deploy["steps"] if "nightly_hosted.sh deploy" in str(s.get("run", ""))]
    assert len(runs) == 1 and runs[0]["env"]["FLY_API_TOKEN"] == "${{ secrets.FLY_API_TOKEN }}"
    for step in deploy["steps"]:
        if step is not runs[0]:
            assert "FLY_API_TOKEN" not in yaml.safe_dump(step)
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False
            assert step["with"]["fetch-depth"] == 0, "the gate compares the reviewed heads with HEAD"


def test_every_action_is_pinned_to_a_commit_and_nothing_is_allowed_to_fail() -> None:
    text = PROPOSAL.read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*(\S+)", text)
    assert uses and all(re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", u) for u in uses), uses
    assert "continue-on-error" not in text and "pull_request_target" not in text


def test_the_installed_workflow_is_the_proposal() -> None:
    """D-217 clause 7: the owner copies the proposal; once copied the two never drift apart."""
    if INSTALLED.exists():
        assert INSTALLED.read_bytes() == PROPOSAL.read_bytes()
    assert PROPOSAL.is_file()
