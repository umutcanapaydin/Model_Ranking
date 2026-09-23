"""REQ-REF-009, D-144 as ruled, D-156 -- a failed source keeps serving its last good data for 30 days.

The owner's ruling, translated from Turkish: "if its data does not arrive, its last data stays valid.
If the data is about a month old, the list drops. If the data updates within that month, nothing
happens and it joins the calculations." Every source carries forward, the required ones included
(ruled 2026-09-23). Age is measured from when the source last ARRIVED (the refresh's per-source
record), not from when the artifact was last published: an unchanged cycle publishes nothing, so
`observed_at` in the live artifact can be much older than the last good fetch.

Every test drives `build()`, the real entry point, against a real live artifact on disk.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pytest

from app.workflows.build import CARRY_MAX_AGE, BuildError, build
from app.workflows.schema import connect
from app.workflows.sources import RemoteSource

from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

NOW = dt.datetime(2026, 9, 23, 22, 0, tzinfo=dt.UTC)


def _iso(days_ago: float) -> str:
    return (NOW - dt.timedelta(days=days_ago)).isoformat(timespec="seconds")


def _live(tmp_path: Path) -> Path:
    """A real, fully built artifact on disk: what the refresh would be serving."""
    path = tmp_path / "advisor.db"
    conn = connect(str(path))
    build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
          minimum_models=2)
    conn.close()
    return path


def _rows(path_or_conn: Path | sqlite3.Connection, source: str) -> list[tuple]:
    conn = sqlite3.connect(path_or_conn) if isinstance(path_or_conn, Path) else path_or_conn
    return sorted(conn.execute(
        "SELECT raw_name, benchmark, metric, score, harness, effort, run_date FROM scores "
        "WHERE source = ?", (source,)).fetchall())


def _candidate(tmp_path: Path, live: Path | None, *, last_ok: dict[str, str] | None,
               name: str = "candidate.db", **sources: object) -> tuple[sqlite3.Connection, object]:
    conn = connect(str(tmp_path / name))
    report = build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML,
                   sources=sources.pop("source_list", None) or _sources(**sources),
                   minimum_models=2, carry_from=live, last_ok=last_ok, now=NOW)
    return conn, report


def test_a_failed_required_source_is_carried_instead_of_failing_the_build(tmp_path: Path) -> None:
    """Ruled 2026-09-23: every source carries, the required ones included."""
    live = _live(tmp_path)
    conn, report = _candidate(tmp_path, live, last_ok={"aider": _iso(2)}, aider=None)

    assert report.carried == {"aider": pytest.approx(2.0)}
    assert report.expired == {}
    assert _rows(conn, "aider") == _rows(live, "aider"), "the carried rows are not the live ones"
    assert _rows(conn, "aider"), "nothing was carried"


def test_the_carried_rows_join_the_calculations(tmp_path: Path) -> None:
    """ "...nothing happens and it joins the calculations": carried rows are reconciled like any
    other, so they reach a ranking rather than sitting unattributed."""
    live = _live(tmp_path)
    conn, _ = _candidate(tmp_path, live, last_ok={"aider": _iso(2)}, aider=None)

    unreconciled = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE source = 'aider' AND model_id IS NULL").fetchone()[0]
    reconciled_live = sqlite3.connect(live).execute(
        "SELECT COUNT(*) FROM scores WHERE source = 'aider' AND model_id IS NULL").fetchone()[0]
    assert unreconciled == reconciled_live


def test_a_source_older_than_a_month_is_not_carried(tmp_path: Path) -> None:
    """ "If the data is about a month old, the list drops." A required source whose last good
    data has expired fails the build, as it did before; nothing stale is served in its place."""
    live = _live(tmp_path)
    too_old = CARRY_MAX_AGE.days + 1
    with pytest.raises(BuildError, match="expired"):
        _candidate(tmp_path, live, last_ok={"aider": _iso(too_old)}, aider=None)


def test_an_expired_optional_source_drops_its_list_and_says_so(tmp_path: Path) -> None:
    live = _live(tmp_path)
    optional = tuple(
        RemoteSource(name=s.name, client=s.client, ingest=s.ingest, parse=s.parse,
                     minimum_rows=s.minimum_rows, required=s.name != "aider")
        for s in _sources(aider=None)
    )
    conn, report = _candidate(tmp_path, live, last_ok={"aider": _iso(45)}, source_list=optional)

    assert report.carried == {}
    assert report.expired == {"aider": pytest.approx(45.0)}
    assert _rows(conn, "aider") == []
    assert any(a.startswith("aider") and "expired" in a for a in report.required_operator_actions)


def test_a_fresh_fetch_replaces_the_carried_data(tmp_path: Path) -> None:
    """ "If the data updates within that month, nothing happens": no carry when the source answers."""
    live = _live(tmp_path)
    _, report = _candidate(tmp_path, live, last_ok={"aider": _iso(2)})
    assert report.carried == {} and report.expired == {}


def test_with_no_live_artifact_a_failed_required_source_still_fails(tmp_path: Path) -> None:
    """The first build on a machine has nothing to carry; W-024's rule stands unchanged."""
    with pytest.raises(BuildError, match="dependency unusable"):
        _candidate(tmp_path, None, last_ok=None, aider=None)


def test_without_a_per_source_record_the_age_falls_back_to_the_live_rows(tmp_path: Path) -> None:
    """No refresh record yet (the first cycle after this lands): the rows' own `observed_at` is the
    only evidence of age, and it can only OVERSTATE the age, never understate it."""
    live = _live(tmp_path)
    sqlite3.connect(live).execute("UPDATE scores SET observed_at = ? WHERE source = 'aider'",
                                  (_iso(40),)).connection.commit()
    with pytest.raises(BuildError, match="expired"):
        _candidate(tmp_path, live, last_ok={}, aider=None)
    _, report = _candidate(tmp_path, live, last_ok={"aider": _iso(1)}, name="second.db",
                              aider=None)
    assert report.carried == {"aider": pytest.approx(1.0)}


def test_a_carried_source_that_is_absent_from_the_live_artifact_is_not_invented(
    tmp_path: Path,
) -> None:
    """Nothing to carry is not the same as something carried: the source is reported missing."""
    live = _live(tmp_path)
    sqlite3.connect(live).execute("DELETE FROM scores WHERE source = 'aider'").connection.commit()
    with pytest.raises(BuildError, match="dependency unusable"):
        _candidate(tmp_path, live, last_ok={"aider": _iso(1)}, aider=None)


def test_pricing_is_carried_like_evidence(tmp_path: Path) -> None:
    """A price is data too: a LiteLLM outage keeps last good prices rather than failing the build."""
    live = _live(tmp_path)
    conn, report = _candidate(tmp_path, live, last_ok={"litellm": _iso(3)}, pricing=None)

    assert "litellm" in report.carried
    count = conn.execute("SELECT COUNT(*) FROM pricing WHERE source = 'litellm'").fetchone()[0]
    live_count = sqlite3.connect(live).execute(
        "SELECT COUNT(*) FROM pricing WHERE source = 'litellm'").fetchone()[0]
    assert count == live_count > 0


def test_the_cli_carries_through_the_same_path_the_refresh_uses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through `build.main`, the entry point the refresh calls: `--carry-from` and `--last-ok`."""
    import json

    from app.workflows import build as build_mod

    live = _live(tmp_path)
    record = tmp_path / "last_ok.json"
    record.write_text(json.dumps({"aider": dt.datetime.now(tz=dt.UTC).isoformat()}))
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources(aider=None))
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    out = tmp_path / "cand.db"
    code = build_mod.main(["--db", str(out), "--carry-from", str(live), "--last-ok", str(record)])
    # 3, not 0: no Epoch bundle is given here, so those surfaces are named as operator actions.
    # 2 would be the failure -- a required source down with nothing carried.
    assert code in (0, 3)
    assert _rows(out, "aider") == _rows(live, "aider")


def test_an_epoch_board_or_bundle_is_carried_when_its_directory_is_missing(tmp_path: Path) -> None:
    """The Epoch bundle and boards carry too (ruled: every source). With no bundle directory given,
    each Epoch source the live artifact holds serves its rows; the ones it does not hold are still
    reported missing."""
    live = _live(tmp_path)
    with sqlite3.connect(live) as db:
        db.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) VALUES ('gpt-5', 'GPQA diamond', '% correct', 80.1, "
            "'epoch-harness', 'unspecified', 'epoch_gpqa', 'https://epoch.ai', ?)", (_iso(3),))
    _, report = _candidate(tmp_path, live, last_ok={"epoch_gpqa": _iso(3)})

    assert report.carried == {"epoch_gpqa": pytest.approx(3.0)}
    assert not any(a.startswith("epoch_gpqa") for a in report.required_operator_actions)
    assert any(a.startswith("epoch_aime") for a in report.required_operator_actions), (
        "an Epoch board with nothing to carry vanished instead of being reported missing"
    )


def test_an_unreadable_arrival_falls_back_to_the_rows_own_stamp(tmp_path: Path) -> None:
    """A torn or future arrival record is not an age; the rows' `observed_at` is (review MINOR-2)."""
    live = _live(tmp_path)
    sqlite3.connect(live).execute("UPDATE scores SET observed_at = ? WHERE source = 'aider'",
                                  (_iso(4),)).connection.commit()
    for bad in ("last tuesday", _iso(-400)):  # unparseable, and 400 days in the future
        _, report = _candidate(tmp_path, live, last_ok={"aider": bad}, name=f"c{len(bad)}.db",
                               aider=None)
        assert report.carried == {"aider": pytest.approx(4.0)}, bad


def test_an_age_nothing_can_read_is_expired_and_the_report_stays_json(tmp_path: Path) -> None:
    import json

    live = _live(tmp_path)
    sqlite3.connect(live).execute("UPDATE scores SET observed_at = 'garbage' WHERE source = 'aider'"
                                  ).connection.commit()
    optional = tuple(
        RemoteSource(name=s.name, client=s.client, ingest=s.ingest, parse=s.parse,
                     minimum_rows=s.minimum_rows, required=s.name != "aider")
        for s in _sources(aider=None)
    )
    _, report = _candidate(tmp_path, live, last_ok={"aider": "last tuesday"}, source_list=optional)
    assert report.expired == {"aider": None}
    json.loads(json.dumps(report.as_json(), allow_nan=False))


@pytest.mark.parametrize("source", ["epoch_gpqa", "epoch_deepswe_external"])
def test_a_board_or_bundle_that_fails_with_its_directory_present_is_carried(
    tmp_path: Path, source: str
) -> None:
    """Review MAJOR-3: the realistic Epoch outage is a directory that is there with a file missing
    or broken, which takes the `except` path, not the no-directory one. A board (`epoch_gpqa`) and a
    bundle (`epoch_deepswe_external`) each carry there too. Red on the review's M18 and M19."""
    live = _live(tmp_path)
    with sqlite3.connect(live) as db:
        db.execute(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) VALUES ('gpt-5', 'b', 'm', 50.0, 'h', 'unspecified', ?, 'u', ?)",
            (source, _iso(3)))
    empty = tmp_path / "bundle"
    empty.mkdir()  # present, and holds none of the allowlisted files
    conn = connect(str(tmp_path / "cand.db"))
    report = build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
                   minimum_models=2, bundle_dir=empty, carry_from=live,
                   last_ok={source: _iso(3)}, now=NOW)
    assert report.carried == {source: pytest.approx(3.0)}
    assert not any(a.startswith(source) for a in report.required_operator_actions)


def test_a_carried_row_takes_its_model_id_from_this_build_not_the_live_one(tmp_path: Path) -> None:
    """Review MINOR-4 (M4): a carried row must be reconciled against the CURRENT registry; a stale id
    copied from the live artifact would survive `reconcile`, which only updates rows it matches."""
    live = _live(tmp_path)
    with sqlite3.connect(live) as db:  # a row today's registry no longer resolves, with an old id
        db.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, "
            "source, source_url, observed_at) VALUES ('stale-id', 'a-model-nobody-knows', "
            "'Aider Polyglot', 'pass_rate_2', 10.0, 'diff', 'unspecified', 'aider', 'u', ?)",
            (_iso(2),))
    conn, _ = _candidate(tmp_path, live, last_ok={"aider": _iso(2)}, aider=None)
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE raw_name = 'a-model-nobody-knows'"
                        ).fetchone()[0] == 1, "the row was not carried at all"
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE model_id = 'stale-id'").fetchone()[0] == 0


def test_rows_stamped_in_the_future_are_young_not_expired(tmp_path: Path) -> None:
    """Re-review MINOR-1: after a clock steps back, the arrival AND the rows are ahead of now. That
    is the clock's fault, not the data's age: the source carries at age 0 instead of expiring and
    failing the cycle. An arrival alone in the future still falls back to the rows (above)."""
    live = _live(tmp_path)
    sqlite3.connect(live).execute("UPDATE scores SET observed_at = ? WHERE source = 'aider'",
                                  (_iso(-1 / 24),)).connection.commit()
    _, report = _candidate(tmp_path, live, last_ok={"aider": _iso(-1 / 24)}, aider=None)
    assert report.carried == {"aider": 0.0}
    assert report.expired == {}


def test_a_carry_that_cannot_be_inserted_leaves_nothing_behind(tmp_path: Path) -> None:
    """Re-review NIT-1: the guard on the carried insert. A schema the carried rows no longer fit
    degrades to "nothing carried": no rows of the source, not in `carried`, and no stray `since`."""
    from app.workflows.build import Carry

    live = _live(tmp_path)
    conn = connect(str(tmp_path / "candidate.db"))
    conn.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                 "source_url, observed_at) VALUES ('stale', 'b', 'm', 1, 'h', 'unspecified', "
                 "'aider', 'u', 'z')")  # a failed fetch's partial row, committed ...
    conn.commit()
    conn.execute("DELETE FROM scores WHERE source = 'aider'")  # ... and reset, still pending
    conn.execute("CREATE TRIGGER no_carry BEFORE INSERT ON pricing WHEN NEW.source = 'aider' "
                 "BEGIN SELECT RAISE(ABORT, 'does not fit'); END")
    sqlite3.connect(live).execute(
        "INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, observed_at) "
        "VALUES ('x', 1, 1, 'aider', 'u', ?)", (_iso(1),)).connection.commit()
    carry = Carry(live=live, last_ok={"aider": _iso(1)}, now=NOW)

    assert carry.restore(conn, "aider") == "absent"
    assert _rows(conn, "aider") == []
    assert carry.carried == {} and "aider" not in carry.since


def test_rows_stamped_far_in_the_future_expire_rather_than_carry_for_ever(tmp_path: Path) -> None:
    """Third review MINOR-2: the age-0 reading is for a clock that stepped back, which is bounded.
    Rows more than the carry limit ahead are not a clock error the ruling can absorb: carrying them
    at age 0 would serve them until real time reached the stamp, and 30 days more."""
    live = _live(tmp_path)
    sqlite3.connect(live).execute("UPDATE scores SET observed_at = ? WHERE source = 'aider'",
                                  (_iso(-400),)).connection.commit()
    optional = tuple(
        RemoteSource(name=s.name, client=s.client, ingest=s.ingest, parse=s.parse,
                     minimum_rows=s.minimum_rows, required=s.name != "aider")
        for s in _sources(aider=None)
    )
    _, report = _candidate(tmp_path, live, last_ok={}, source_list=optional)
    assert report.carried == {}
    assert "aider" in report.expired
