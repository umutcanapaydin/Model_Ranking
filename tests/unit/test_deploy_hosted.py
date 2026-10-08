"""M19-W5 (#94, #88; D-185 clause 5, REQ-REL-003): `scripts/deploy_hosted_engine.sh`, the one way the
hosted engine is deployed.

The owner runs it; nothing here deploys. It is run against a scratch repository with stand-ins for
`fly` and `curl` first on its PATH, so no request leaves this machine: the `fly` stand-in records its
arguments, and the `curl` stand-in answers `/health` with the build that `fly` was given, or another.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from .test_api_v1 import _seeded_db

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "deploy_hosted_engine.sh"
_CLEAN_GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(*args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                          check=True, capture_output=True, text=True, env=_CLEAN_GIT_ENV).stdout.strip()


def _scratch(tmp_path: Path, health_build: str | None = None) -> tuple[Path, Path, Path, dict[str, str]]:
    """A committed scratch repository holding this tree's fly.toml, a served artifact beside it, and a
    bin of stand-ins. `health_build` is what /health answers; by default the build fly was given."""
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    _git("init", "-q", "--bare", "-b", "main", str(origin))
    _git("clone", "-q", str(origin), str(repo))
    shutil.copy(REPO / "fly.toml", repo / "fly.toml")
    (repo / "README").write_text("scratch\n", encoding="utf-8")
    _git("-C", str(repo), "add", ".")
    _git("-C", str(repo), "commit", "-qm", "scratch")
    _git("-C", str(repo), "push", "-q", "origin", "main")
    served = tmp_path / "served.db"
    _seeded_db(served)
    bin_dir, calls = tmp_path / "bin", tmp_path / "fly-calls.txt"
    bin_dir.mkdir()
    (bin_dir / "fly").write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\n', encoding="utf-8")
    answer = (f'echo \'{{"status": "ok", "build": "{health_build}"}}\'' if health_build else
              f'build=$(tr " " "\\n" < "{calls}" | sed -n "s/^APP_BUILD=//p" | tail -1)\n'
              'echo "{\\"status\\": \\"ok\\", \\"build\\": \\"$build\\"}"')
    (bin_dir / "curl").write_text(f"#!/bin/sh\n{answer}\n", encoding="utf-8")
    for stand_in in ("fly", "curl"):
        (bin_dir / stand_in).chmod(0o755)
    env = {**_CLEAN_GIT_ENV, "PATH": f"{bin_dir}:{os.environ['PATH']}", "MODEL_RANKING_REPO": str(repo),
           "MODEL_RANKING_SERVED": str(served), "PYTHON": sys.executable, "DEPLOY_HEALTH_TRIES": "1"}
    return repo, served, calls, env


def _deploy(env: dict[str, str], *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(SCRIPT), *flags], capture_output=True, text=True, timeout=120,
                          env=env, check=False)


def test_a_deploy_stamps_the_commit_ships_the_public_artifact_and_checks_health(tmp_path: Path) -> None:
    repo, _served, calls, env = _scratch(tmp_path)
    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    sha = _git("-C", str(repo), "rev-parse", "--short", "HEAD")
    called = calls.read_text(encoding="utf-8")
    assert called.startswith("deploy") and f"--build-arg APP_BUILD=release-{sha}" in called, called
    shipped = repo / "build" / "hosted" / "advisor.db"
    with sqlite3.connect(shipped) as conn:
        scored = {row[0] for row in conn.execute("SELECT DISTINCT source FROM scores")}
        priced = {row[0] for row in conn.execute("SELECT DISTINCT source FROM pricing")}
    # D-186: nothing is left out on TestFlight, so the shipped copy keeps the fixture's sources.
    assert {"swebench", "epoch_deepswe_external"} <= scored, scored
    assert priced == {"litellm"}, priced


def test_a_health_answer_from_another_build_fails_the_deploy(tmp_path: Path) -> None:
    _repo, _served, _calls, env = _scratch(tmp_path, health_build="release-0000000")
    done = _deploy(env)
    assert done.returncode != 0 and "release-0000000" in done.stdout + done.stderr


def test_an_uncommitted_tree_is_refused_before_anything_is_built(tmp_path: Path) -> None:
    repo, _served, calls, env = _scratch(tmp_path)
    (repo / "README").write_text("changed, not committed\n", encoding="utf-8")
    done = _deploy(env)
    assert done.returncode != 0 and not calls.exists()
    assert not (repo / "build" / "hosted" / "advisor.db").exists()


def test_a_dry_run_builds_and_checks_but_deploys_nothing(tmp_path: Path) -> None:
    repo, _served, calls, env = _scratch(tmp_path)
    done = _deploy(env, "--dry-run")
    assert done.returncode == 0, done.stdout + done.stderr
    assert not calls.exists()
    assert (repo / "build" / "hosted" / "advisor.db").is_file()


@pytest.mark.parametrize("source", ["pyproject.toml", "requirements/serve.lock", "requirements/build.lock",
                                    "src", "build/hosted/advisor.db"])
def test_the_build_context_carries_what_the_image_copies_and_little_else(source: str) -> None:
    """Fly's builder uploads the build context. With no `.dockerignore` it was the whole tree, the
    venv and the git history included. The allow-list keeps each path a COPY reads."""
    rules = [line.strip() for line in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    assert rules[0] == "*", "everything is left out first"
    assert any(rule.lstrip("!").rstrip("/*") == source for rule in rules if rule.startswith("!")), rules


# --- The M19-W5 review (docs/reviews/m19-wave-5-review-round-1.md) ----------------------------------------

def test_a_deploy_places_one_machine(tmp_path: Path) -> None:
    """M4: a first `fly deploy` places two machines by default, not the one the records cost."""
    _repo, _served, calls, env = _scratch(tmp_path)
    assert _deploy(env).returncode == 0
    assert "--ha=false" in calls.read_text(encoding="utf-8").split()


def test_the_build_stamp_names_the_data_as_well_as_the_code(tmp_path: Path) -> None:
    """M5: `release-<sha>` named the code only, so two deploys of one commit with different data,
    a refresh apart, carried one stamp. The stamp now ends with the public artifact's digest."""
    import hashlib

    repo, _served, calls, env = _scratch(tmp_path)
    assert _deploy(env).returncode == 0
    shipped = (repo / "build" / "hosted" / "advisor.db").read_bytes()
    digest = hashlib.sha256(shipped).hexdigest()[:8]
    sha = _git("-C", str(repo), "rev-parse", "--short", "HEAD")
    assert f"APP_BUILD=release-{sha}-data-{digest}" in calls.read_text(encoding="utf-8")


def test_a_commit_not_on_origin_main_is_refused(tmp_path: Path) -> None:
    """M5: the script deployed any committed HEAD; a release is what `main` holds."""
    repo, _served, calls, env = _scratch(tmp_path)
    (repo / "README").write_text("an unmerged change\n", encoding="utf-8")
    _git("-C", str(repo), "commit", "-qam", "unmerged")
    done = _deploy(env)
    assert done.returncode != 0 and "origin/main" in done.stdout + done.stderr
    assert not calls.exists()


def test_the_build_context_keeps_every_copy_source_and_the_dockerfile() -> None:
    """M3: the context list was written by hand beside the COPY lines, and it left out the Dockerfile,
    which Fly's reference says not to exclude. Each COPY source is read from the Dockerfile."""
    sources = []
    for line in (REPO / "Dockerfile").read_text(encoding="utf-8").splitlines():
        words = line.split()
        if words[:1] == ["COPY"] and not any(word.startswith("--from=") for word in words):
            sources += [word for word in words[1:-1] if not word.startswith("--")]
    rules = [line.strip() for line in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    kept = {rule[1:].rstrip("/") for rule in rules if rule.startswith("!")}
    assert sources and "build/hosted/advisor.db" in sources
    for source in [*sources, "Dockerfile"]:
        assert any(source.rstrip("/") == k or source.startswith(k + "/") for k in kept), (source, kept)


def test_the_build_context_leaves_out_what_git_ignores_under_src() -> None:
    """The M19 security review's S14: `!src` let a git-ignored file there (a `.env`, bytecode) reach
    Fly's remote builder."""
    rules = [line.strip() for line in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    after = rules[rules.index("!src") + 1:]
    for pattern in ("**/.env*", "**/__pycache__", "**/*.pyc", "**/*.pem", "**/*.key", "**/*.db", "**/*.sqlite*"):
        assert pattern in after, (pattern, rules)


def test_the_script_takes_no_argument_but_dry_run(tmp_path: Path) -> None:
    """The second W5 review's M1: `--dry-run-no` or `now --dry-run` reached `fly deploy`."""
    _repo, _served, calls, env = _scratch(tmp_path)
    for flags in (["--dry-run-no"], ["now", "--dry-run"], ["--dry-run=false"]):
        done = _deploy(env, *flags)
        assert done.returncode != 0, flags
    assert not calls.exists()


def test_only_the_tip_of_origin_main_deploys(tmp_path: Path) -> None:
    """The second W5 review's R5: the script never fetched, so an older main commit, or a stale
    origin/main, could be deployed. It fetches, and deploys only origin/main's tip."""
    _repo, _served, calls, env = _scratch(tmp_path)
    other = tmp_path / "other"
    _git("clone", "-q", str(tmp_path / "origin.git"), str(other))
    (other / "README").write_text("newer main\n", encoding="utf-8")
    _git("-C", str(other), "commit", "-qam", "newer")
    _git("-C", str(other), "push", "-q", "origin", "main")
    done = _deploy(env)
    assert done.returncode != 0 and "origin/main" in done.stdout + done.stderr
    assert not calls.exists()


# --- The W5 Tester seat (docs/reviews/m19-wave-5-tester.md) ------------------------------------------------

def test_an_untracked_file_is_refused_before_anything_is_built(tmp_path: Path) -> None:
    """The script's step 1: "The tree must be committed, untracked files included". An untracked file
    under `src/` goes into the image (`!src` in `.dockerignore`) but into no commit, so the stamp would
    name code the image does not hold. Only a changed tracked file was tested; `--untracked-files=no`
    (the Tester's D1) passed every test."""
    repo, _served, calls, env = _scratch(tmp_path)
    (repo / "not_committed.py").write_text("print('not in any commit')\n", encoding="utf-8")
    done = _deploy(env)
    assert done.returncode != 0 and not calls.exists(), done.stdout + done.stderr
    assert not (repo / "build" / "hosted" / "advisor.db").exists()


@pytest.mark.parametrize("served_state", ["missing", "unreadable"])
def test_a_derivation_that_cannot_run_stops_the_deploy_beside_an_older_artifact(
    tmp_path: Path, served_state: str
) -> None:
    """#88: the image ships what the derivation just wrote, never an older public artifact left in
    build/hosted. A derivation that fails must stop the deploy; `|| true` after it (the Tester's D2)
    passed every test, and so did the missing-artifact refusal removed (D7)."""
    repo, served, calls, env = _scratch(tmp_path)
    (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
    _git("-C", str(repo), "add", ".gitignore")
    _git("-C", str(repo), "commit", "-qm", "ignore build")
    _git("-C", str(repo), "push", "-q", "origin", "main")
    older = repo / "build" / "hosted" / "advisor.db"
    older.parent.mkdir(parents=True)
    _seeded_db(older)
    if served_state == "missing":
        served.unlink()
    else:
        served.write_bytes(b"not a database")
    done = _deploy(env)
    assert done.returncode != 0, done.stdout + done.stderr
    assert not calls.exists(), calls.read_text(encoding="utf-8")
    if served_state == "missing":
        assert "MODEL_RANKING_SERVED" in done.stderr, done.stderr


def test_the_image_is_built_on_flys_builder(tmp_path: Path) -> None:
    """The runbook (step 1.5) and the script's header: the deploy builds on Fly's builder, not on the
    Mac's Docker. `--remote-only` dropped (the Tester's D3) passed every test."""
    _repo, _served, calls, env = _scratch(tmp_path)
    assert _deploy(env).returncode == 0
    assert "--remote-only" in calls.read_text(encoding="utf-8").split()


def _dockerignore_keeps(path: str) -> bool:
    """Whether Docker's build context holds `path` under `.dockerignore`: the last rule that matches
    the path or a folder above it decides; `**` spans folders, `*` one name (moby's patternmatcher)."""
    import re

    def regex(pattern: str) -> re.Pattern[str]:
        out, i = "", 0
        while i < len(pattern):
            if pattern.startswith("**/", i):
                out, i = out + "(?:.*/)?", i + 3
            elif pattern.startswith("**", i):
                out, i = out + ".*", i + 2
            elif pattern[i] == "*":
                out, i = out + "[^/]*", i + 1
            elif pattern[i] == "?":
                out, i = out + "[^/]", i + 1
            else:
                out, i = out + re.escape(pattern[i]), i + 1
        return re.compile(out)

    rules = [line.strip() for line in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.strip().startswith("#")]
    parts = path.split("/")
    candidates = ["/".join(parts[: n + 1]) for n in range(len(parts))]
    kept = True
    for rule in rules:
        negated = rule.startswith("!")
        compiled = regex(rule.lstrip("!").strip("/"))
        if any(compiled.fullmatch(candidate) for candidate in candidates):
            kept = negated
    return kept


@pytest.mark.parametrize(("path", "kept"), [
    ("Dockerfile", True), ("pyproject.toml", True), ("requirements/serve.lock", True),
    ("requirements/build.lock", True), ("src/app/adapter/main.py", True), ("build/hosted/advisor.db", True),
    ("advisor.db", False), (".venv/bin/python", False), (".git/config", False), ("tests/unit/test_api_v1.py", False),
    ("docs/decisions.md", False), ("build/hosted/advisor.db.x1.deriving", False),
    ("src/app/.env", False), ("src/app/.env.local", False), ("src/app/__pycache__/main.cpython-311.pyc", False),
    ("src/app/stray.pyc", False), ("src/app/cert.pem", False), ("src/app/server.key", False),
])
def test_the_build_context_holds_what_the_image_copies_and_no_secret(path: str, kept: bool) -> None:
    """The M19 security review's S14 and the second W5 review's M6, read as Docker reads the list: the
    last matching rule wins. The wave's tests check that each pattern is present after `!src`, so a
    later `!` rule bringing a secret back (the Tester's K6; the second review's I3) passed every test."""
    assert _dockerignore_keeps(path) is kept, path
