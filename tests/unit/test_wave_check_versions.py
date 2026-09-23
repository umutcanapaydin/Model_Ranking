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
    assert "Mutant set author" in out, out


def test_a_close_written_before_the_adoption_keeps_its_declared_version(tmp_path: Path) -> None:
    out = _wave_check(_close(tmp_path, "v5.0", "2026-09-01"))
    assert "Mutant set author" not in out, out


@pytest.mark.parametrize("version", ["v5.0", "v6.0", "v6.4", "v6.6", "v7.1"])
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
