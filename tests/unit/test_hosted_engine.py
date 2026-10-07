"""M19-W5 (#94): the hosted engine, as the image and `fly.toml` declare it.

The serving image starts uvicorn on every interface, but the startup check reads the bind from
`MODEL_RANKING_BIND`, which the image never set: the check saw loopback, so an image with no Host
list booted and then refused every outside request with 400 (D-171). The image now says where it
binds, so the same check refuses to BOOT it without a Host list, and the hosted deployment names the
one Host it answers to. Nothing here deploys; the files are read as text.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from app.adapter import main as adapter

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"
FLY = ROOT / "fly.toml"


def _stages(text: str) -> dict[str, list[str]]:
    """Each stage's lines, by its name (`AS name`), or by its position when unnamed."""
    stages: dict[str, list[str]] = {}
    name = ""
    for line in text.splitlines():
        words = line.split()
        if words and words[0].upper() == "FROM":
            name = words[-1] if len(words) >= 4 and words[-2].upper() == "AS" else f"stage-{len(stages)}"
            stages[name] = []
        if name:
            stages[name].append(line)
    return stages


def _env(lines: list[str]) -> dict[str, str]:
    """The `ENV KEY=VALUE` settings of a stage, comments left out."""
    env: dict[str, str] = {}
    for line in lines:
        words = line.split(maxsplit=1)
        if len(words) == 2 and words[0].upper() == "ENV":
            for pair in words[1].split():
                key, _, value = pair.partition("=")
                env[key] = value.strip('"')
    return env


def _serving_stage(text: str) -> list[str]:
    """The stage that runs the engine: the one with the `CMD`."""
    stages = [lines for lines in _stages(text).values() if any(line.startswith("CMD ") for line in lines)]
    assert len(stages) == 1, "one stage runs the engine"
    return stages[0]


def _cmd_host(lines: list[str]) -> str:
    cmd = next(line for line in lines if line.startswith("CMD "))
    argv = json.loads(cmd[len("CMD "):])
    return str(argv[argv.index("--host") + 1])


def test_the_image_tells_its_startup_check_where_it_binds() -> None:
    """#94: the startup check reads the bind from MODEL_RANKING_BIND; the image must set it to the
    address its command binds, or the check judges a bind that is not the one in use."""
    serving = _serving_stage(DOCKERFILE.read_text(encoding="utf-8"))
    assert _env(serving).get(adapter.BIND_VAR) == _cmd_host(serving)


def test_the_image_refuses_to_boot_beyond_loopback_with_no_host_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """#94: in the image's own environment, with no Host list, the startup check fails closed at
    boot rather than serving 400 to every outside request."""
    from .test_api_v1 import _seeded_db

    db = tmp_path / "advisor.db"
    _seeded_db(db)
    env = _env(_serving_stage(DOCKERFILE.read_text(encoding="utf-8")))
    monkeypatch.setenv("APP_ENV", env["APP_ENV"])
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv(adapter.BIND_VAR, env.get(adapter.BIND_VAR, "127.0.0.1"))
    monkeypatch.delenv(adapter.ALLOWED_HOSTS_VAR, raising=False)
    monkeypatch.setattr(adapter, "APP_BUILD", "release-test")
    with pytest.raises(adapter.ConfigError, match=adapter.ALLOWED_HOSTS_VAR):
        adapter.validate_startup_config()
    monkeypatch.setenv(adapter.ALLOWED_HOSTS_VAR, "engine.example")
    adapter.validate_startup_config()


def test_the_hosted_engine_answers_to_its_own_name_and_is_checked_by_it() -> None:
    """#94: the deployment names the one Host it answers to, from its app name, and Fly's health
    check sends that Host (it reaches the machine by address, which the Host list refuses)."""
    fly = tomllib.loads(FLY.read_text(encoding="utf-8"))
    name = f"{fly['app']}.fly.dev"
    assert fly["env"][adapter.ALLOWED_HOSTS_VAR] == name
    checks = fly["http_service"]["checks"]
    assert checks and all(check["headers"]["Host"] == name and check["path"] == "/health" for check in checks)
    assert "checks" not in fly, "a top-level check reaches the machine with no Host header"
    assert fly["http_service"]["force_https"] is True
    assert fly["env"]["APP_ENV"] == "production"


def test_the_hosted_image_carries_the_artifact_the_deployment_serves() -> None:
    """M19-W5: the hosted stage copies the public artifact to the path the deployment serves, and the
    deployment builds that stage, with no volume left to start empty."""
    fly = tomllib.loads(FLY.read_text(encoding="utf-8"))
    hosted = _stages(DOCKERFILE.read_text(encoding="utf-8"))["hosted"]
    served = fly["env"]["MODEL_RANKING_DB"]
    assert any(line.startswith("COPY ") and line.split()[-1] == served for line in hosted), hosted
    assert fly["build"]["build-target"] == "hosted"
    assert "mounts" not in fly


def _user(stage_lines: list[str]) -> str | None:
    users = [line.split()[1] for line in stage_lines if line.split()[:1] == ["USER"]]
    return users[-1] if users else None


def _inv86_problems(text: str) -> list[str]:
    """What breaks INV-86 in a Dockerfile's text: the hosted engine run as root, an artifact the engine
    can write (a `--chown` or `--chmod` copy), or anything the hosted stage runs."""
    stages = _stages(text)
    hosted_user = _user(stages["hosted"]) or _user(_serving_stage(text))
    problems = []
    # The user before any group: `USER root:root` and `USER 0:0` are root too (the re-read's N3).
    if hosted_user is None or hosted_user.split(":")[0] in ("root", "0"):
        problems.append(f"the hosted engine runs as {hosted_user!r}")
    copies = [line for line in stages["hosted"] if line.startswith("COPY ")]
    if not copies or any("--chown" in line or "--chmod" in line for line in copies):
        problems.append(f"the artifact's copy: {copies}")
    if any(line.startswith("RUN ") for line in stages["hosted"]):
        problems.append("the hosted stage runs a command")
    return problems


def test_the_hosted_engine_runs_as_no_root_and_cannot_write_its_artifact() -> None:
    """The M19 security review's S4: the engine run as root, or its artifact made its own, passed the
    whole suite. The hosted stage inherits the serving stage's non-root user and takes the artifact
    as root's, unchangeable by the engine."""
    assert _inv86_problems(DOCKERFILE.read_text(encoding="utf-8")) == []


def test_the_hosted_stage_only_copies_and_points_at_its_artifact() -> None:
    """The second W5 review's M6: a `RUN chmod` in the hosted stage, or its MODEL_RANKING_DB line
    dropped, passed every test. The stage copies the artifact and names it, and runs nothing."""
    fly = tomllib.loads(FLY.read_text(encoding="utf-8"))
    hosted = _stages(DOCKERFILE.read_text(encoding="utf-8"))["hosted"]
    assert "the hosted stage runs a command" not in _inv86_problems(DOCKERFILE.read_text(encoding="utf-8"))
    assert _env(hosted).get("MODEL_RANKING_DB") == fly["env"]["MODEL_RANKING_DB"]


@pytest.mark.parametrize(
    "planted",
    [
        "USER root:root",
        "USER 0:0",
        "USER 00",  # a numeric id is not looked up: uid 0 (the release security review's K7)
        "user root",  # Docker reads an instruction in any case (K8)
        "USER $ROOT_USER",  # a user the text cannot name
        "copy --chown=appuser build/hosted/advisor.db /srv/advisor.db",
        "user root\nrun chmod 666 /srv/advisor.db\nuser appuser",  # K10
        "RUN chmod 666 /srv/advisor.db",
    ],
)
def test_inv86_holds_however_the_dockerfile_spells_it(planted: str) -> None:
    """The release security review's RS2: INV-86's checks read the Dockerfile as Docker does, an
    instruction in any case and a numeric root as root. Each line is appended to the hosted stage, the
    Dockerfile's last."""
    text = DOCKERFILE.read_text(encoding="utf-8").rstrip("\n") + "\n" + planted + "\n"
    assert planted.splitlines()[0] in _stages(text)["hosted"], "the plant is not in the hosted stage"
    assert _inv86_problems(text), planted


# --- The W5 Tester seat (docs/reviews/m19-wave-5-tester.md) ------------------------------------------------

def test_the_hosted_stage_builds_on_the_stage_that_runs_the_engine() -> None:
    """INV-86 is read from the serving stage (its `USER`, `ENV` and `CMD`), which the hosted stage is
    assumed to inherit. `FROM build AS hosted` (the Tester's K1) passed every test: an image that runs
    as root, with no engine command, no bind and no production lane."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    serving = _serving_stage(text)
    serving_name = serving[0].split()[-1]
    hosted_from = _stages(text)["hosted"][0].split()
    assert hosted_from[:1] == ["FROM"] and hosted_from[1] == serving_name, (hosted_from, serving_name)


def test_fly_reaches_the_port_the_engine_listens_on() -> None:
    """D-185 clause 1: Fly sends each request to `internal_port`; the engine listens on its command's
    `--port`. A mismatch (the Tester's K5, K7) passed every test and would fail only at the deploy."""
    serving = _serving_stage(DOCKERFILE.read_text(encoding="utf-8"))
    cmd = next(line for line in serving if line.startswith("CMD "))
    argv = json.loads(cmd[len("CMD "):])
    port = int(argv[argv.index("--port") + 1])
    fly = tomllib.loads(FLY.read_text(encoding="utf-8"))
    assert fly["http_service"]["internal_port"] == port
    assert any(line.split()[:2] == ["EXPOSE", str(port)] for line in serving), "the image exposes the port"


def test_one_machine_is_always_up() -> None:
    """D-185 clause 1 and the runbook's cost: one machine, always up ("a phone's first question should
    not wait for a cold start"). Scaling to zero (the Tester's K4) passed every test."""
    service = tomllib.loads(FLY.read_text(encoding="utf-8"))["http_service"]
    assert service["auto_stop_machines"] is False
    assert service["min_machines_running"] >= 1


def test_the_images_own_health_check_asks_by_the_deployments_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """#94: with a Host list set the engine refuses its own loopback address, so the image's
    HEALTHCHECK names the first listed Host. It is run here against a stand-in `urlopen`; with the
    header dropped (the Tester's K3) every test passed."""
    import urllib.request

    lines = DOCKERFILE.read_text(encoding="utf-8").replace("\\\n", " ").splitlines()
    check = next(line for line in lines if line.startswith("HEALTHCHECK "))
    code = json.loads(check[check.index('python -c "') + len("python -c "):])
    asked: list[urllib.request.Request] = []

    class _Answer:
        status = 200

    def _urlopen(request: urllib.request.Request, *args: object, **kwargs: object) -> _Answer:
        asked.append(request)
        return _Answer()

    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
    hosts = tomllib.loads(FLY.read_text(encoding="utf-8"))["env"][adapter.ALLOWED_HOSTS_VAR]
    monkeypatch.setenv(adapter.ALLOWED_HOSTS_VAR, hosts)
    with pytest.raises(SystemExit) as stopped:
        exec(compile(code, "HEALTHCHECK", "exec"), {"__name__": "__main__"})
    assert stopped.value.code == 0
    assert asked and asked[0].full_url == "http://127.0.0.1:8080/health"
    assert asked[0].get_header("Host") == hosts.split(",")[0]
