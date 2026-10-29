"""SimpleBench from the leaderboard file its page loads (#379, D-219) — cite REQ-SRC-013.

SimpleBench publishes its board as one script its page loads, `static/js/leaderboard-data.js`: `leaderboardData`, one
object per row with its rank, model, AVG@5 score, organisation and the date the row was added, beside an open-ended
board of three models (`openEndedData`) and prices the page shows, neither of which is this board. The human
baselines carry no rank and are not models. SimpleBench publishes no licence on its site; its public numbers are used
under D-215 with its credit. The fixture is the file as published on 2026-10-22 (`tests/fixtures/simplebench/`).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import httpx
import pytest
import respx

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "simplebench" / "leaderboard-data.js"
SITE = "https://simple-bench.com/"
DATA = "https://simple-bench.com/static/js/leaderboard-data.js"


def _sb():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.simplebench")


def _raw() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _parse(raw: str):
    return _sb().parse_simplebench(raw, source="simplebench")


def _by_name(rows: list) -> dict[str, object]:
    return {row.raw_name: row for row in rows}


def test_each_ranked_model_is_a_row_at_its_avg_at_5_score_dated_by_the_day_it_was_added() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): 106 ranked models; the two human baselines are skipped and counted; the
    open-ended board is not read. A score is the AVG@5 percentage; a row is dated by the day it was added."""
    rows, skipped = _parse(_raw())
    assert (len(rows), skipped) == (106, 2)
    top = _by_name(rows)["Claude Opus 5.5"]
    assert (top.score, top.run_date, top.harness, top.source_url) == (88.4, "2026-09-24", "SimpleBench (AVG@5)", SITE)
    assert (top.benchmark, top.metric, top.source) == ("SimpleBench", "% correct", "simplebench")
    assert _by_name(rows)["Gemini 3.1 Pro Preview"].score == 79.6  # its MCQ row, not its open-ended 64.8
    assert not any(name.endswith("*") for name in _by_name(rows))


@pytest.mark.parametrize("change", [('score: "88.4%"', 'score: "high"'), ('score: "88.4%"', 'score: "188.4%"'),
                                    ('model: "Claude Opus 5.5"', 'model: ""')],
                         ids=["text-score", "above-100", "no-model"])
def test_a_row_that_is_not_a_usable_score_is_skipped_and_counted(change: tuple[str, str]) -> None:
    rows, skipped = _parse(_raw().replace(*change, 1))
    assert (len(rows), skipped) == (105, 3)
    assert "Claude Opus 5.5" not in _by_name(rows)


def test_a_row_with_no_date_is_undated_and_kept() -> None:
    rows, _ = _parse(_raw().replace('dateAdded: "2026-09-24"', "dateAdded: null", 1))
    assert _by_name(rows)["Claude Opus 5.5"].run_date is None


@pytest.mark.parametrize("raw", ["not the file", "const leaderboardData = [\n];\n", "const somethingElse = [];"],
                         ids=["no-board", "an-empty-board", "another-variable"])
def test_a_file_that_is_not_the_board_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-013: a broken payload is a failed night, carried, never an empty board."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


@pytest.mark.respx(assert_all_called=False)
def test_the_client_reads_the_file_from_its_own_host_with_no_token(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): one public file, no `Authorization` header, from the site's own host."""
    monkeypatch.setenv("HF_TOKEN", "stand-in-token-for-tests")
    site = respx_mock.get(DATA).mock(return_value=httpx.Response(200, text=_raw()))
    client = _sb().SimpleBenchClient()
    assert (client.name, client.url, tuple(client.hosts)) == ("simplebench", DATA, ("simple-bench.com",))
    rows, _ = _parse(client.fetch_raw())
    assert len(rows) == 106
    assert site.call_count == 1 and "authorization" not in site.calls.last.request.headers


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("answer", [
    httpx.Response(503, text="unavailable"),
    httpx.Response(302, headers={"location": "https://elsewhere.example.net/leaderboard-data.js"}),
], ids=["down", "redirected-off-the-site"])
def test_a_site_that_fails_fails_the_source_and_no_other_host_is_asked(
    respx_mock: respx.MockRouter, answer: httpx.Response,
) -> None:
    """covers REQ-SRC-013: no fallback; the refresh carries the previous night's rows (D-156)."""
    from app.clients.protocols import SourceError

    respx_mock.get(DATA).mock(return_value=answer)
    elsewhere = respx_mock.get("https://elsewhere.example.net/leaderboard-data.js").mock(
        return_value=httpx.Response(200, text=_raw()))
    with pytest.raises(SourceError):
        _sb().SimpleBenchClient().fetch_raw()
    assert not elsewhere.called


def test_the_source_is_declared_optional_and_its_floor_is_half_the_recorded_board() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): optional (D-121), floor half the board as recorded."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "simplebench")
    assert declared.client is _sb().SimpleBenchClient and declared.required is False
    rows, _ = declared.parse(_raw())
    assert declared.minimum_rows == len(rows) // 2


def test_everyday_adds_simplebench_after_its_other_boards() -> None:
    """covers REQ-SRC-013 (D-219 clause 3): SimpleBench stands in `everyday`; the primary stays."""
    from app.workflows import categories, families

    assert families.FAMILIES["everyday"] == ("epoch_eci", "arena", "epoch_mmlu", "livebench", "simplebench")
    assert categories.CATEGORIES["everyday"].primary_source == "epoch_eci"


def test_simplebench_is_credited_for_its_public_numbers_with_its_link() -> None:
    """covers REQ-SRC-013 (D-219 clauses 1 and 4): no licence on the site; public numbers attributed (D-215)."""
    from app.workflows import rank

    citation = rank.SOURCE_ATTRIBUTION["simplebench"]
    assert SITE in citation and citation in rank.ATTRIBUTIONS
    [credit] = rank.credits_for([citation])
    assert credit == {**credit, "url": SITE, "licence_url": None}
    assert "D-215" in str(credit["licence"])


def test_the_registered_ingest_stores_each_row() -> None:
    """covers REQ-SRC-013: through the build's own path, the store keeps the parser's rows."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "simplebench")
    conn = connect(":memory:")
    report = declared.ingest(conn, FakeRawSource(name="simplebench", url=DATA, payload=_raw()),
                             RunContext(observed_at="2026-10-22T00:00:00Z"))
    assert (report.stored, report.skipped) == (106, 2)


def test_a_model_listed_twice_keeps_its_first_row_and_counts_the_second() -> None:
    """covers REQ-SRC-013 (#379): the release Tester's fault SB2 (`model in seen` dropped) stayed green. A model the
    board lists twice is one row, the first as listed, and the repeat is skipped and counted, so a second score for
    the same model can neither replace the first nor rank it twice."""
    first = '{ rank: "1st",  model: "Claude Opus 5.5",            score: "88.4%",'
    repeat = ('  { rank: "2nd", model: "Claude Opus 5.5", score: "12.0%", organization: "Anthropic",'
              ' dateAdded: "2026-10-01" },\n')
    raw = _raw()
    assert raw.count(first) == 1, "the fixture's first row is where this test plants the repeat"
    end = raw.index("\n", raw.index(first)) + 1
    rows, skipped = _parse(raw[:end] + repeat + raw[end:])
    assert (len(rows), skipped) == (106, 3)
    assert [row.score for row in rows if row.raw_name == "Claude Opus 5.5"] == [88.4]


def test_a_board_with_no_closing_bracket_fails_in_linear_time() -> None:
    """#412 (the v0.1.0 release security review's M3): `\\n\\s*\\];` let `\\s*` re-scan every later newline at each
    candidate end, so 100k newlines took 12.6 s and a 32 MB file days, past the cycle's alarm. The board now ends at a
    newline followed by horizontal whitespace only, so a page that never closes it fails at once.

    #452 (the release v0.2.0 Tester's M2): timed at 25k and 100k newlines, interleaved, best of three; a linear
    reading takes about 4 times as long, the quadratic one 16 (12.6 s at 100k), and the floor keeps machine load
    from deciding the ratio."""
    import time

    from app.clients.protocols import SourceError
    from app.clients.simplebench import parse_simplebench

    def once(newlines: int) -> float:
        raw = "const leaderboardData = [ {" + "\n" * newlines + "x"
        started = time.perf_counter()
        with pytest.raises(SourceError):
            parse_simplebench(raw)
        return time.perf_counter() - started

    small = large = float("inf")
    for _ in range(3):
        small, large = min(small, once(25_000)), min(large, once(100_000))
    assert large < max(8 * small, 1.0), f"25k newlines: {small:.4f} s, 100k: {large:.4f} s"
