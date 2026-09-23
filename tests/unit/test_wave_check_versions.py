"""D-161: wave closes are graded by the version they declare -- but only when that declaration can
be believed, and every DevFlow version from v5.0 on is in scope.

The v6.4 upgrade review (docs/reviews/devflow-v6.4-upgrade-review.md) found both halves undone by
taking DevFlow's scripts: MAJOR-1, `wave_check_all` listed the versions it grades (v5.0, v6.0), so a
close stamped by today's template fell out of scope; MAJOR-2, `wave_check` trusted a declared
version alone, so a close written today could declare v5.0 and skip three fields.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _close(tmp_path: Path, version: str, date: str) -> Path:
    record = tmp_path / "m99-wave-1-close.md"
    record.write_text(
        f"---\nrecord_type: wave\nid: m99-wave-1-close\nstatus: draft\n"
        f"process_version: {version}\ndate: {date}\n---\n# A close with no footprint fields\n",
        encoding="utf-8")
    return record


def _wave_check(record: Path) -> str:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/wave_check.py"), str(record)],
                            cwd=ROOT, capture_output=True, encoding="utf-8", check=False)
    return result.stdout + result.stderr


def test_a_close_written_after_the_adoption_cannot_declare_its_way_out(tmp_path: Path) -> None:
    out = _wave_check(_close(tmp_path, "v5.0", "2026-10-15"))
    assert "a close written after 2026-09-23 declares v6.6" in out, out


def test_an_undated_close_cannot_declare_its_way_out(tmp_path: Path) -> None:
    """v6.6 upgrade review MAJOR-1: with no `date:` line, the first guard never fired."""
    record = _close(tmp_path, "v5.0", "2026-10-15")
    record.write_text(record.read_text(encoding="utf-8").replace("date: 2026-10-15\n", ""),
                      encoding="utf-8")
    out = _wave_check(record)
    assert "undated" in out, out


def test_a_later_close_is_graded_by_the_version_it_declares(tmp_path: Path) -> None:
    """v6.6 upgrade review MAJOR-2: a close stamped v6.6 and dated later is not graded by rules a
    future DevFlow adds -- and it IS asked for v6.6's own field."""
    out = _wave_check(_close(tmp_path, "v6.6", "2026-10-15"))
    assert "declares process_version" not in out, out
    assert "Stopped at three attempts" in out, out


def test_a_close_written_before_the_adoption_keeps_its_declared_version(tmp_path: Path) -> None:
    out = _wave_check(_close(tmp_path, "v5.0", "2026-09-01"))
    assert "Mutant set author" not in out, out


@pytest.mark.parametrize("version", ["v5.0", "v6.0", "v6.0.1", "v6.4", "v6.6", "v7.1"])
def test_every_version_from_v5_on_is_in_scope(version: str, monkeypatch: pytest.MonkeyPatch,
                                              tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A close dated after the v5.0 migration is graded, whatever DevFlow version stamped it --
    never reported as "without the stamp"."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("wave_check_all", ROOT / "scripts/wave_check_all.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    _close(plans, version, "2026-09-23")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "wave_check.py").write_text(
        "def main(argv):\n    return 0\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    assert module.main() == 0
    assert "1 v5.0-or-later record(s) validated" in capsys.readouterr().out


def test_the_trailer_check_on_agent_commits_holds_in_the_gate() -> None:
    """v6.6 upgrade review M1: the GP-Agent trailer check (D-161) was proven only by
    `--self-test`, which no gate ran, so disabling it left `make check` green. Running the
    self-test here puts it in `make test`."""
    result = subprocess.run([sys.executable, str(ROOT / "conformance/test-commit-identity.py"),
                             "--self-test"], cwd=ROOT, capture_output=True, encoding="utf-8",
                            check=False)
    assert result.returncode == 0, result.stdout
    assert "no GP-Agent trailer" in result.stdout, "the trailer case left the self-test"


def test_the_coverage_floor_failing_fails_make_test() -> None:
    """v6.6 upgrade review NIT-3: a `-` prefix on the floor's recipe line makes make ignore its
    exit status, and W-041 would pass while failing."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\ntest: ", 1)[1].split("\n\n", 1)[0]
    floor = next(line for line in recipe.splitlines() if "module_coverage_floor.py" in line)
    assert not floor.lstrip("\t").startswith(("-", "@-")), floor


# --- #17 ------------------------------------------------------------------------------------------


def test_a_close_with_no_version_and_no_date_is_graded_not_skipped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """#17 (2): a close with neither `process_version:` nor `date:` was filed as pre-migration
    and never graded. A record with no date cannot be assumed old."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("wave_check_all", ROOT / "scripts/wave_check_all.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "m99-wave-1-close.md").write_text(
        "---\nrecord_type: wave\nid: m99-wave-1-close\nstatus: draft\n---\n# no version, no date\n",
        encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "wave_check.py").write_text(
        "def main(argv):\n    return 0\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    code = module.main()
    out = capsys.readouterr().out
    assert code == 1, out
    assert "is undated" in out and "1 without the stamp" in out, out


def _machine_commit_verdict(tmp_path: Path, *paragraphs: str) -> subprocess.CompletedProcess[str]:
    """test-commit-identity on a branch holding one machine-identity commit with this message."""
    repo = tmp_path / "repo"
    repo.mkdir()
    env_base = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp_path),
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}

    def git(*args: str, email: str = "o@x", name: str = "O") -> None:
        env = {**env_base, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_EMAIL": email,
               "GIT_AUTHOR_NAME": name, "GIT_COMMITTER_NAME": name}
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    (repo / "f").write_text("a", encoding="utf-8")
    git("add", "f")
    git("commit", "-qm", "owner work")
    git("switch", "-q", "-c", "work/1")
    (repo / "f").write_text("b", encoding="utf-8")
    git("add", "f")
    message = [arg for p in paragraphs for arg in ("-m", p)]
    git("commit", "-q", *message, email="gp-agent@users.noreply.github.com", name="gp-agent")
    return subprocess.run([sys.executable, str(ROOT / "conformance/test-commit-identity.py"),
                           "--owner-email", "o@x"], cwd=repo, capture_output=True,
                          encoding="utf-8", env=env_base, check=False)


@pytest.mark.parametrize(("paragraphs", "refused"), [
    # #17 (1): a mention inside a sentence is not the trailer.
    (("agent", "see GP-Agent: notes somewhere in the body.", "Reviewed-by: nobody"), True),
    # Tester M1: a trailer with no value names no agent.
    (("agent", "GP-Agent:"), True),
    # Tester MAJOR-1: this project's own shape, GP-Agent in its own paragraph above another.
    (("agent", "GP-Agent: issue-agent", "GP-Task: #17"), False),
    (("agent", "GP-Agent: issue-agent\nGP-Task: #17"), False),
])
def test_a_trailer_is_read_as_a_line_not_a_substring(
    tmp_path: Path, paragraphs: tuple[str, ...], refused: bool
) -> None:
    result = _machine_commit_verdict(tmp_path, *paragraphs)
    assert (result.returncode == 1) is refused, result.stdout
    assert ("no `GP-Agent:` trailer" in result.stdout) is refused, result.stdout


@pytest.mark.parametrize("front", [
    'date: ""\n',          # Tester M3: quoted empty
    "date:\n",             # Tester M2: an empty date as the LAST field must not read `---`
])
def test_an_empty_date_is_undated_wherever_it_sits(
    front: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _wave_check_all_in(tmp_path, monkeypatch,
                                "---\nrecord_type: wave\nid: m99-wave-1-close\nstatus: draft\n"
                                f"{front}---\n# undated\n")
    assert module.main() == 1
    assert "is undated" in capsys.readouterr().out


def test_a_quoted_date_is_a_date(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                 capsys: pytest.CaptureFixture[str]) -> None:
    """Tester M3: `date: "2026-10-01"` was filed as pre-migration."""
    module = _wave_check_all_in(tmp_path, monkeypatch,
                                "---\nrecord_type: wave\nid: m99-wave-1-close\nstatus: draft\n"
                                'date: "2026-10-01"\n---\n# quoted\n')
    assert module.main() == 1
    assert "dated 2026-10-01" in capsys.readouterr().out


def _wave_check_all_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: str) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location("wave_check_all", ROOT / "scripts/wave_check_all.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "m99-wave-1-close.md").write_text(record, encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "wave_check.py").write_text("def main(argv):\n    return 0\n",
                                                         encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    return module
