"""#552, D-243 (D-240 clause 3): a source silent for 7 or more nights is named to the owner.

Each refresh cycle writes `silent` into its record: every source whose last arrival (D-156,
`sources_last_ok`) is 7 or more days before the cycle, with that arrival. `scripts/silent_sources.py`
reads it and prints the names, or the one issue the nightly workflow opens or comments on.

covers #552, D-243
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.workflows import refresh as refresh_mod
from app.workflows.refresh import (
    EXIT_FAILED,
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    EXIT_UNCHANGED,
    RefreshOutcome,
    status_path,
    write_status,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "silent_sources.py"
AT = dt.datetime(2026, 11, 2, 21, 30, tzinfo=dt.UTC).timestamp()
DAY = 86400.0


def _iso(days_before: float) -> str:
    return dt.datetime.fromtimestamp(AT - days_before * DAY, tz=dt.UTC).isoformat(timespec="seconds")


def _outcome(code: int, arrived: tuple[str, ...] = ()) -> RefreshOutcome:
    return RefreshOutcome(published=code == EXIT_PUBLISHED, reason="r", live_fingerprint=None,
                          candidate_fingerprint="", surfaces=1, arrived=arrived)


def _cycle(tmp_path: Path, last_ok: dict[str, str], code: int, arrived: tuple[str, ...] = ()) -> dict:
    target = tmp_path / "advisor.db"
    status_path(target).write_text(json.dumps({"sources_last_ok": last_ok}), encoding="utf-8")
    write_status(target, _outcome(code, arrived), code, at=AT)
    record = json.loads(status_path(target).read_text(encoding="utf-8"))
    assert isinstance(record, dict)
    return record


# --- the rule ------------------------------------------------------------------------------------------

def test_a_source_eight_days_silent_is_named_and_one_six_days_silent_is_not() -> None:
    """The issue's acceptance, on the rule itself."""
    silent = refresh_mod.silent_sources({"arena": _iso(8), "litellm": _iso(6)}, AT)
    assert silent == {"arena": _iso(8)}


def test_seven_days_is_named_and_a_second_less_is_not() -> None:
    """D-240 clause 3: 7 OR MORE days."""
    week = dt.datetime.fromtimestamp(AT - 7 * DAY, tz=dt.UTC).isoformat(timespec="seconds")
    under = dt.datetime.fromtimestamp(AT - 7 * DAY + 1, tz=dt.UTC).isoformat(timespec="seconds")
    assert refresh_mod.silent_sources({"a": week, "b": under}, AT) == {"a": week}
    assert refresh_mod.SILENT_DAYS == 7


def test_a_stamp_that_cannot_be_read_is_named() -> None:
    """Fail toward telling the owner: an arrival no one can date is not a recent one."""
    silent = refresh_mod.silent_sources({"arena": "not-a-date", "litellm": _iso(1)}, AT)
    assert silent == {"arena": "not-a-date"}


# --- through the real record writer ----------------------------------------------------------------------

@pytest.mark.parametrize("code", [EXIT_PUBLISHED, EXIT_UNCHANGED, EXIT_FAILED, EXIT_REFUSED])
def test_the_record_names_the_eight_day_source_and_not_the_six_day_one(tmp_path: Path, code: int) -> None:
    """The issue's acceptance, through `write_status`: on every kind of night, served or not."""
    record = _cycle(tmp_path, {"arena": _iso(8), "litellm": _iso(6)}, code)
    assert record["silent"] == {"arena": _iso(8)}
    assert record["sources_last_ok"] == {"arena": _iso(8), "litellm": _iso(6)}, "D-156 is unchanged"


def test_an_arrival_in_a_served_cycle_ends_the_silence(tmp_path: Path) -> None:
    record = _cycle(tmp_path, {"arena": _iso(8)}, EXIT_PUBLISHED, arrived=("arena",))
    assert record["silent"] == {}


def test_an_arrival_in_a_refused_cycle_does_not_end_it(tmp_path: Path) -> None:
    """D-156: a refused cycle's data is not served, so it is no arrival."""
    record = _cycle(tmp_path, {"arena": _iso(8)}, EXIT_REFUSED, arrived=("arena",))
    assert record["silent"] == {"arena": _iso(8)}


def test_the_record_names_an_unreadable_stamp(tmp_path: Path) -> None:
    record = _cycle(tmp_path, {"arena": "garbage"}, EXIT_UNCHANGED)
    assert record["silent"] == {"arena": "garbage"}


# --- the script the workflow runs --------------------------------------------------------------------------

def _script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          timeout=60, check=False)


def _written(tmp_path: Path, last_ok: dict[str, str]) -> Path:
    _cycle(tmp_path, last_ok, EXIT_UNCHANGED)
    return status_path(tmp_path / "advisor.db")


def test_the_script_lists_the_silent_sources(tmp_path: Path) -> None:
    record = _written(tmp_path, {"arena": _iso(8), "litellm": _iso(6)})
    done = _script(str(record))
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == [f"arena last arrived {_iso(8)}"]


def test_the_script_s_issue_names_each_source_and_its_last_arrival(tmp_path: Path) -> None:
    record = _written(tmp_path, {"arena": _iso(8), "swebench": _iso(30), "litellm": _iso(6)})
    done = _script("--issue", str(record))
    assert done.returncode == 0, done.stderr
    assert len(done.stdout.strip().splitlines()) == 1, "one line: the workflow passes it as a job output"
    issue = json.loads(done.stdout)
    assert set(issue) == {"title", "body"}
    assert issue["title"] == "Sources silent for 7 or more nights"
    body = issue["body"]
    assert "<!-- silent-sources -->" in body
    for name, stamp in (("arena", _iso(8)), ("swebench", _iso(30))):
        assert name in body and stamp in body
    assert "litellm" not in body


def test_the_script_says_nothing_when_no_source_is_silent(tmp_path: Path) -> None:
    record = _written(tmp_path, {"litellm": _iso(6)})
    for args in ((str(record),), ("--issue", str(record))):
        done = _script(*args)
        assert done.returncode == 0, done.stderr
        assert done.stdout == ""


@pytest.mark.parametrize("content", [None, "{not json", json.dumps({"sources_last_ok": {}}),
                                     json.dumps({"silent": ["arena"]})])
def test_a_record_the_script_cannot_read_is_an_error_not_a_quiet_night(tmp_path: Path,
                                                                       content: str | None) -> None:
    """Fail closed: a record with no readable `silent` is never read as "no source is silent"."""
    record = tmp_path / "advisor.db.refresh.json"
    if content is not None:
        record.write_text(content, encoding="utf-8")
    done = _script("--issue", str(record))
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.strip()
