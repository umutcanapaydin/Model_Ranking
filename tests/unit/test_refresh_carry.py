"""REQ-REF-009, D-156 through the refresh -- the 2026-09-20 incident, replayed.

That night an Arena timeout made the candidate "worse", D-128 refused it, and fresh LiteLLM,
OpenRouter and SWE-bench data was thrown away with it. Under D-156 the failed source carries its
last good rows, the others publish, and the record says what is carried and since when.

Every cycle test runs the real `refresh()` with the real `build.main`, with fake upstreams. Rewritten
after the M16-W3 review: two tests could not fail (BLOCKING-1, -2); each is now shown red on the
mutant the review used.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pytest

from app.workflows import build as build_mod
from app.workflows.refresh import (
    EXIT_FAILED,
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    RefreshOutcome,
    _surfaces_fed_by,
    refresh,
    status_path,
    write_status,
)
from app.workflows.sources import RemoteSource

from .test_build import PRICING, _sources

MOVED_PRICING = PRICING.replace("1.25e-06", "1.5e-06")  # one real price move: the digest changes


def _ago(days: float) -> str:
    return (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=days)).isoformat(timespec="seconds")


def _use(monkeypatch: pytest.MonkeyPatch, sources: tuple[RemoteSource, ...]) -> None:
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", sources)
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)


def _record(live: Path) -> dict:
    return json.loads(status_path(live).read_text(encoding="utf-8"))


def _seed(live: Path, **arrivals: str) -> None:
    record = _record(live)
    record["sources_last_ok"].update(arrivals)
    status_path(live).write_text(json.dumps(record), encoding="utf-8")


def _optional(sources: tuple[RemoteSource, ...], name: str) -> tuple[RemoteSource, ...]:
    return tuple(
        RemoteSource(name=s.name, client=s.client, ingest=s.ingest, parse=s.parse,
                     minimum_rows=s.minimum_rows, required=s.name != name)
        for s in sources
    )


def _first_cycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Publish a first artifact, then age it by ten days: its rows and every recorded arrival. Real
    cycles are a night apart; a test whose cycles share a second cannot tell a clock that moved from
    one that did not (review BLOCKING-1)."""
    live = tmp_path / "advisor.db"
    _use(monkeypatch, _sources())
    _, code = refresh(live)
    assert code == EXIT_PUBLISHED
    earlier = _ago(10)
    with sqlite3.connect(live) as db:
        for table in ("scores", "pricing"):
            db.execute(f"UPDATE {table} SET observed_at = ?", (earlier,))
    _seed(live, **{name: earlier for name in _record(live)["sources_last_ok"]})
    return live


def test_a_source_that_arrives_is_recorded_as_arrived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = _first_cycle(tmp_path, monkeypatch)
    assert {"litellm", "swebench", "aider"} <= set(_record(live)["sources_last_ok"])


def test_the_2026_09_20_incident_publishes_the_fresh_data_and_carries_the_failed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = _first_cycle(tmp_path, monkeypatch)
    before = sorted(sqlite3.connect(live).execute(
        "SELECT raw_name, score FROM scores WHERE source = 'swebench'").fetchall())

    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    outcome, code = refresh(live)

    assert code == EXIT_PUBLISHED, outcome.reason
    after = sorted(sqlite3.connect(live).execute(
        "SELECT raw_name, score FROM scores WHERE source = 'swebench'").fetchall())
    assert after == before, "the failed source's last good rows were not carried"
    record = _record(live)
    assert set(record["carried"]) == {"swebench"}
    assert record["carried"]["swebench"] == record["sources_last_ok"]["swebench"], (
        "the carry is dated from the source's last arrival")


def test_a_carry_keeps_its_clock_and_an_arrival_moves_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Carrying is not arriving: the failed source's 30 days keep running from its last real
    arrival, or they would restart every night and the list would never drop. The sources that DID
    arrive move to now. Red on the review's M10 and M26."""
    live = _first_cycle(tmp_path, monkeypatch)
    seeded = _record(live)["sources_last_ok"]["swebench"]
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    refresh(live)
    arrivals = _record(live)["sources_last_ok"]
    assert arrivals["swebench"] == seeded
    assert arrivals["litellm"] > seeded and arrivals["aider"] > seeded


def test_an_expired_source_drops_its_surface_instead_of_freezing_the_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past 30 days the list drops (ruled). D-128 would refuse a candidate that blinds `coding`,
    which would freeze every other source; an EXPIRED carry is the one blinding it accepts."""
    live = _first_cycle(tmp_path, monkeypatch)
    _seed(live, swebench=_ago(45))
    _use(monkeypatch, _optional(_sources(pricing=MOVED_PRICING, swebench=None), "swebench"))
    outcome, code = refresh(live)

    assert code == EXIT_PUBLISHED, outcome.reason
    assert sqlite3.connect(live).execute(
        "SELECT COUNT(*) FROM scores WHERE source = 'swebench'").fetchone()[0] == 0
    assert set(_record(live)["expired"]) == {"swebench"}


def test_a_blinding_that_is_not_an_expiry_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The safety half of the exemption. The source is young and in the live artifact, but its rows
    cannot be carried this time (the live copy is unreadable to the carry), so `coding` goes blind
    for a reason that is NOT an expiry -- and D-128 refuses it. Red on the review's M11."""
    live = _first_cycle(tmp_path, monkeypatch)
    before = live.read_bytes()
    monkeypatch.setattr(build_mod.Carry, "restore", lambda self, conn, source: "absent")
    _use(monkeypatch, _optional(_sources(pricing=MOVED_PRICING, swebench=None), "swebench"))
    outcome, code = refresh(live)

    assert code == EXIT_REFUSED, outcome.reason
    assert "coding" in outcome.reason
    assert live.read_bytes() == before
    assert not _record(live).get("expired")


def test_a_required_source_past_its_age_fails_the_cycle_and_says_it_expired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is published, and the expiry the build found is still recorded (review MAJOR-2 E8):
    it used to appear only on the build's stderr."""
    live = _first_cycle(tmp_path, monkeypatch)
    before = live.read_bytes()
    _seed(live, swebench=_ago(45))
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    _, code = refresh(live)
    assert code == EXIT_FAILED
    assert live.read_bytes() == before
    assert "swebench" in _record(live)["expired"]


def test_a_failed_cycle_still_reports_what_is_served_as_carried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review MAJOR-2 E2: the carried rows are still live after a later cycle fails, so the record
    must still say so."""
    live = _first_cycle(tmp_path, monkeypatch)
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    refresh(live)
    carried = _record(live)["carried"]
    assert set(carried) == {"swebench"}

    monkeypatch.setattr(build_mod.Carry, "restore", lambda self, conn, source: "absent")
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))  # required, nothing to carry
    _, code = refresh(live)
    assert code == EXIT_FAILED
    assert _record(live)["carried"] == carried


def test_an_expired_source_stays_listed_until_it_arrives(tmp_path: Path) -> None:
    """Review MAJOR-2 E9: an expired source was listed for one night. It stays until a served cycle
    brings it back."""
    target = tmp_path / "advisor.db"
    at = dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp()

    def cycle(code: int, **kw: object) -> dict:
        write_status(target, RefreshOutcome(published=code == 0, reason="r", live_fingerprint=None,
                                            candidate_fingerprint="", surfaces=1, **kw), code, at=at)
        return _record(target)

    assert cycle(0, expired={"arena_vision": "2026-08-01T00:00:00+00:00"})["expired"]
    assert "arena_vision" in cycle(1, arrived=("litellm",))["expired"]
    assert "arena_vision" in cycle(3, arrived=("arena_vision",))["expired"], "a refused arrival"
    assert "arena_vision" not in cycle(0, arrived=("arena_vision",))["expired"]


@pytest.mark.parametrize(("code", "counts"), [(0, True), (1, True), (2, False), (3, False)])
def test_only_a_served_cycle_counts_as_an_arrival(tmp_path: Path, code: int, counts: bool) -> None:
    """A refused (3) or failed (2) cycle's data is not what is served, so its arrivals do not
    reset the 30 days; a published (0) or unchanged (1) cycle's do."""
    target = tmp_path / "advisor.db"
    status_path(target).write_text(
        json.dumps({"sources_last_ok": {"arena": "2026-09-01T00:00:00+00:00"}}))
    outcome = RefreshOutcome(published=code == 0, reason="r", live_fingerprint=None,
                             candidate_fingerprint="", surfaces=1, arrived=("arena",))
    write_status(target, outcome, code, at=dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp())
    seen = _record(target)["sources_last_ok"]["arena"]
    assert (seen == "2026-09-23T00:00:00+00:00") is counts


def test_an_expiry_excuses_every_surface_its_rows_fed_not_only_its_primary(tmp_path: Path) -> None:
    """Review MAJOR-1: `epoch_swe_bench_verified` feeds `coding` (SWE-bench Verified) without being
    its primary source, and its expiry refused every cycle. The excuse follows the benchmark."""
    from app.workflows.categories import CATEGORIES
    from app.workflows.schema import connect

    live = tmp_path / "advisor.db"
    conn = connect(str(live))
    conn.execute(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
        "source_url, observed_at) VALUES ('m', ?, '% resolved', 70, 'h', 'unspecified', "
        "'epoch_swe_bench_verified', 'u', '2026-08-01T00:00:00+00:00')",
        (CATEGORIES["coding"].primary_benchmark,))
    conn.commit()
    conn.close()
    assert "coding" in _surfaces_fed_by(live, {"epoch_swe_bench_verified"})
    assert _surfaces_fed_by(live, set()) == frozenset()


# --- M16-W3 re-review: the exemption is the expired ROWS' loss, never a whole surface -------------

EPOCH_CODING = "epoch_swe_bench_verified"


def _expired_secondary_rows(live: Path) -> None:
    """45-day-old `epoch_swe_bench_verified` rows on `coding`'s own board, for the one priced model
    `swebench` does not score -- so they are a third of `coding` and the only cheap model on it."""
    from app.workflows.categories import CATEGORIES

    spec = CATEGORIES["coding"]
    with sqlite3.connect(live) as db:
        model_id = db.execute("SELECT model_id FROM pricing WHERE alias = 'gpt-5-nano'").fetchone()[0]
        db.execute(
            "INSERT INTO scores (raw_name, model_id, benchmark, metric, score, harness, effort, "
            "source, source_url, observed_at) VALUES ('gpt-5-nano', ?, ?, ?, 70, 'h', "
            "'unspecified', ?, 'u', ?)",
            (model_id, spec.primary_benchmark, spec.metric, EPOCH_CODING, _ago(45)))
    assert _coding_models(live) == 3


def _coding_models(path: Path) -> int:
    from app.workflows.refresh import fingerprint_of

    summary = fingerprint_of(path)
    assert summary is not None
    return summary.surfaces["coding"]


def test_a_secondary_sources_expiry_publishes_through_the_real_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-review BLOCKING-1: the first review's MAJOR-1 symptom, as a CYCLE. The expired source is
    not `coding`'s primary, so an exemption keyed on primaries refuses this every night."""
    live = _first_cycle(tmp_path, monkeypatch)
    _expired_secondary_rows(live)
    _use(monkeypatch, _sources(pricing=MOVED_PRICING))
    outcome, code = refresh(live)

    assert code == EXIT_PUBLISHED, outcome.reason
    assert set(_record(live)["expired"]) == {EPOCH_CODING}
    assert _coding_models(live) == 2


def test_an_expiry_does_not_excuse_the_fresh_source_beside_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-review MAJOR-1 (S5): on the night a secondary source expires, `swebench` goes blind for a
    reason that is NOT an expiry. Only the expired rows' share of `coding` is excused; the fresh
    source's share is still guarded, so D-128 refuses."""
    live = _first_cycle(tmp_path, monkeypatch)
    _expired_secondary_rows(live)
    before = live.read_bytes()
    real = build_mod.Carry.restore
    monkeypatch.setattr(build_mod.Carry, "restore", lambda self, conn, source:
                        "absent" if source == "swebench" else real(self, conn, source))
    _use(monkeypatch, _optional(_sources(pricing=MOVED_PRICING, swebench=None), "swebench"))
    outcome, code = refresh(live)

    assert code == EXIT_REFUSED, outcome.reason
    assert "coding answered with 2 models" in outcome.reason
    assert live.read_bytes() == before


def test_a_cycle_whose_report_is_lost_moves_no_clock_and_excuses_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-review MINOR-2 (N18): an unreadable build report is read as "nothing arrived, nothing
    expired" -- the safe reading -- never as "everything arrived"."""
    live = _first_cycle(tmp_path, monkeypatch)
    _expired_secondary_rows(live)
    seeded = _record(live)["sources_last_ok"]

    def lose_the_report(argv: list[str]) -> int:
        code = build_mod.main(argv)
        Path(argv[argv.index("--report-out") + 1]).write_text("{torn", encoding="utf-8")
        return code

    _use(monkeypatch, _sources(pricing=MOVED_PRICING))
    outcome, code = refresh(live, builder=lose_the_report)

    assert code == EXIT_REFUSED, outcome.reason  # the expired rows' loss is NOT excused unreported
    assert _record(live)["sources_last_ok"] == seeded


def _write(target: Path, code: int, **kw: object) -> dict:
    write_status(target, RefreshOutcome(published=code == 0, reason="r", live_fingerprint=None,
                                        candidate_fingerprint="", surfaces=1, **kw), code,
                 at=dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp())
    return _record(target)


def test_an_unchanged_cycle_keeps_the_carry_it_reports(tmp_path: Path) -> None:
    """Re-review MINOR-2 (N12): unchanged is the ordinary state during an outage. Dropping `carried`
    there would erase the carry from /health on every quiet night."""
    target = tmp_path / "advisor.db"
    stamp = "2026-09-20T00:00:00+00:00"
    _write(target, 0, carried={"swebench": stamp})
    assert _write(target, 1, carried={"swebench": stamp})["carried"] == {"swebench": stamp}


def test_a_source_listed_as_expired_is_never_also_listed_as_carried(tmp_path: Path) -> None:
    """Re-review MINOR-2 (N13): an expired source's rows dropped; saying it is carried too would
    describe two states at once."""
    target = tmp_path / "advisor.db"
    stamp = "2026-08-01T00:00:00+00:00"
    _write(target, 0, carried={"swebench": stamp})
    record = _write(target, 2, expired={"swebench": stamp})
    assert "swebench" in record["expired"]
    assert "swebench" not in record["carried"]
