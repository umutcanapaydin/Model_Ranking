"""M19-W5: the Stage 5.2 gates `make journey` and `make cold-start`, wired for the hosted engine.

`make journey URL=...` runs the black-box journey (`scripts/journey.py`) against the deployed engine;
`make cold-start` builds the image's `hosted` stage and boots it with nothing persisted, on loopback,
then runs the same journey against it. Run here with stand-ins for `docker` and for the journey's
python first on PATH, so nothing is built, run or fetched: each stand-in records how it was called.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _stand_ins(tmp_path: Path, docker_fails_on: str = "") -> tuple[dict[str, str], Path]:
    bin_dir, calls = tmp_path / "bin", tmp_path / "calls.txt"
    bin_dir.mkdir()
    fail = f'case "$1" in {docker_fails_on}) exit 1 ;; esac\n' if docker_fails_on else ""
    (bin_dir / "docker").write_text(f'#!/bin/sh\necho "docker $*" >> "{calls}"\n{fail}', encoding="utf-8")
    (bin_dir / "curl").write_text(f'#!/bin/sh\necho "curl $*" >> "{calls}"\necho ok\n', encoding="utf-8")
    python = bin_dir / "python3"
    python.write_text(f'#!/bin/sh\necho "python $*" >> "{calls}"\n', encoding="utf-8")
    for tool in ("docker", "curl", "python3"):
        (bin_dir / tool).chmod(0o755)
    served = tmp_path / "served.db"
    served.write_bytes(b"")
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "PYTHON": str(python),
           "MODEL_RANKING_SERVED": str(served), "COLD_START_WAIT_S": "1"}
    return env, calls


def test_the_journey_runs_against_the_url_it_is_given(tmp_path: Path) -> None:
    env, calls = _stand_ins(tmp_path)
    done = subprocess.run(["bash", "docs/journey.sh"], cwd=REPO, capture_output=True, text=True, timeout=60,
                          env={**env, "URL": "https://engine.example"}, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "python scripts/journey.py --base-url https://engine.example" in calls.read_text(encoding="utf-8")


def test_the_journey_refuses_to_run_without_a_url(tmp_path: Path) -> None:
    env, calls = _stand_ins(tmp_path)
    env.pop("URL", None)
    done = subprocess.run(["bash", "docs/journey.sh"], cwd=REPO, capture_output=True, text=True, timeout=60,
                          env=env, check=False)
    assert done.returncode != 0 and not calls.exists()


def test_a_cold_start_boots_the_hosted_image_on_loopback_and_journeys_it(tmp_path: Path) -> None:
    env, calls = _stand_ins(tmp_path)
    done = subprocess.run(["bash", "docs/cold-start.sh"], cwd=REPO, capture_output=True, text=True, timeout=60,
                          env=env, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    lines = calls.read_text(encoding="utf-8").splitlines()
    derive = next(line for line in lines if line.startswith("python -m app.workflows.public"))
    assert "--to build/hosted/advisor.db" in derive, "the image's artifact is derived first"
    build = next(line for line in lines if line.startswith("docker build"))
    assert "--target hosted" in build and "APP_BUILD=" in build
    run = next(line for line in lines if line.startswith("docker run"))
    # Nothing persisted: no volume, no mount; the engine reached on loopback only.
    assert " -v " not in run and "--mount" not in run and "-p 127.0.0.1:" in run
    assert "MODEL_RANKING_ALLOWED_HOSTS=127.0.0.1" in run
    journey = next(line for line in lines if line.startswith("python scripts/journey.py"))
    assert "--base-url http://127.0.0.1:" in journey
    assert any(line.startswith(("docker rm -f", "docker stop")) for line in lines), "the container is removed"


def test_a_cold_start_that_cannot_build_stops_and_runs_nothing(tmp_path: Path) -> None:
    env, calls = _stand_ins(tmp_path, docker_fails_on="build")
    done = subprocess.run(["bash", "docs/cold-start.sh"], cwd=REPO, capture_output=True, text=True, timeout=60,
                          env=env, check=False)
    assert done.returncode != 0
    assert not any(line.startswith("docker run") for line in calls.read_text(encoding="utf-8").splitlines())
