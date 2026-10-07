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


def test_the_hosted_engine_runs_as_no_root_and_cannot_write_its_artifact() -> None:
    """The M19 security review's S4: the engine run as root, or its artifact made its own, passed the
    whole suite. The hosted stage inherits the serving stage's non-root user and takes the artifact
    as root's, unchangeable by the engine."""
    stages = _stages(DOCKERFILE.read_text(encoding="utf-8"))
    serving_user = _user(_serving_stage(DOCKERFILE.read_text(encoding="utf-8")))
    hosted_user = _user(stages["hosted"]) or serving_user
    # The user before any group: `USER root:root` and `USER 0:0` are root too (the re-read's N3).
    assert hosted_user is not None and hosted_user.split(":")[0] not in ("root", "0"), hosted_user
    copies = [line for line in stages["hosted"] if line.startswith("COPY ")]
    assert copies and not any("--chown" in line or "--chmod" in line for line in copies), copies


def test_the_hosted_stage_only_copies_and_points_at_its_artifact() -> None:
    """The second W5 review's M6: a `RUN chmod` in the hosted stage, or its MODEL_RANKING_DB line
    dropped, passed every test. The stage copies the artifact and names it, and runs nothing."""
    fly = tomllib.loads(FLY.read_text(encoding="utf-8"))
    hosted = _stages(DOCKERFILE.read_text(encoding="utf-8"))["hosted"]
    assert not any(line.startswith("RUN ") for line in hosted), hosted
    assert _env(hosted).get("MODEL_RANKING_DB") == fly["env"]["MODEL_RANKING_DB"]
