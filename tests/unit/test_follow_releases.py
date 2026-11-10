"""D-250: LiveBench and DeepSWE follow the release their publisher's site serves, each night.

Each site names its current data on its own page: LiveBench's page script lists its releases, and Datacurve's page
loads one leaderboard file. The client reads that page, takes the newest release it names (never one older than the
last read by hand), and fetches it from the same host; a page that names none fails the source, never the night.
LiveBench's newer releases weight the overall (`_overall_weights` in `categories.json`), and the parser computes it
as the page does. The pages are recorded from 2026-11-10 (`tests/fixtures/livebench/`, `tests/fixtures/datacurve/`).

covers D-250
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from app.clients.datacurve import DatacurveClient
from app.clients.livebench import LiveBenchClient, parse_livebench
from app.clients.protocols import SourceError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
LB_SITE = "https://livebench.ai/"
LB_SCRIPT = "https://livebench.ai/static/js/main.c61c63f5.js"
DC_SITE = "https://deepswe.datacurve.ai/"


def _fixture(*parts: str) -> str:
    return (FIXTURES.joinpath(*parts)).read_text(encoding="utf-8")


def _release(release: str, name: str) -> str:
    return f"https://livebench.ai/data/{release}/{name}"


def _leaderboard(version: str) -> str:
    return f"https://deepswe.datacurve.ai/artifacts/{version}/leaderboard-live.json"


def _script(releases: list[str]) -> str:
    return _fixture("livebench", "page-script.js").replace(
        '["20261014","20261025","20261106"]', json.dumps(releases, separators=(",", ":")))


def _serve_livebench(respx_mock: respx.MockRouter, script: str) -> None:
    respx_mock.get(LB_SITE).mock(return_value=httpx.Response(200, text=_fixture("livebench", "page.html")))
    respx_mock.get(LB_SCRIPT).mock(return_value=httpx.Response(200, text=script))


@pytest.mark.respx(assert_all_called=False)
def test_livebench_reads_the_newest_release_its_page_names(respx_mock: respx.MockRouter) -> None:
    """Clause 1: the page lists 2026-10-14, 2026-10-25 and 2026-11-06; the night reads 2026-11-06 and dates its rows."""
    _serve_livebench(respx_mock, _fixture("livebench", "page-script.js"))
    table = respx_mock.get(_release("20261106", "table.csv")).mock(
        return_value=httpx.Response(200, text=_fixture("livebench", "table.csv")))
    cats = respx_mock.get(_release("20261106", "categories.json")).mock(
        return_value=httpx.Response(200, text=_fixture("livebench", "categories-20261106.json")))
    pinned = respx_mock.get(_release("20261014", "table.csv")).mock(return_value=httpx.Response(200, text=""))
    raw = LiveBenchClient().fetch_raw()
    assert json.loads(raw)["release"] == "2026-11-06"
    rows, _ = parse_livebench(raw)
    assert {row.run_date for row in rows} == {"2026-11-06"}
    assert table.called and cats.called and not pinned.called


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("releases", [["20260925", "20261001"], [], ["20261399"]],
                         ids=["only-older-than-the-floor", "none", "not-a-date"])
def test_a_page_that_names_no_release_at_or_past_the_floor_fails_livebench(
    respx_mock: respx.MockRouter, releases: list[str],
) -> None:
    """Clauses 1 and 4: never older than 2026-10-14; nothing else is fetched."""
    _serve_livebench(respx_mock, _script(releases))
    data = respx_mock.get(url__startswith="https://livebench.ai/data/").mock(return_value=httpx.Response(200))
    with pytest.raises(SourceError):
        LiveBenchClient().fetch_raw()
    assert not data.called


@pytest.mark.respx(assert_all_called=False)
def test_a_page_that_loads_no_script_fails_livebench(respx_mock: respx.MockRouter) -> None:
    """Clause 4: the page changed shape; the night carries the last good rows (D-156)."""
    respx_mock.get(LB_SITE).mock(return_value=httpx.Response(200, text="<html><body>LiveBench</body></html>"))
    with pytest.raises(SourceError):
        LiveBenchClient().fetch_raw()


@pytest.mark.respx(assert_all_called=False)
def test_a_page_redirected_off_the_site_fails_livebench(respx_mock: respx.MockRouter) -> None:
    """Clause 4: no other host is asked."""
    respx_mock.get(LB_SITE).mock(return_value=httpx.Response(
        302, headers={"location": "https://elsewhere.example.net/"}))
    elsewhere = respx_mock.get("https://elsewhere.example.net/").mock(return_value=httpx.Response(200))
    with pytest.raises(SourceError):
        LiveBenchClient().fetch_raw()
    assert not elsewhere.called


def _raw(table: str, categories: dict[str, object], release: str = "2026-11-06") -> str:
    return json.dumps({"release": release, "table": table, "categories": categories})


def test_the_overall_is_weighted_by_the_releases_own_weights() -> None:
    """Clause 2: the page's weighted mean of the category averages; an unnamed category weighs 1."""
    rows, _ = parse_livebench(_raw("model,a,b,c\nm-1,40,100,70\n",
                                   {"A": ["a"], "B": ["b"], "C": ["c"], "_overall_weights": {"B": 3}}))
    assert rows[0].score == 82.0  # (40 + 100 * 3 + 70) / 5


def test_the_recorded_release_weights_long_agentic_coding_and_design() -> None:
    """Clause 2, on the release recorded 2026-11-10: Long Agentic 2.0, Coding 1.5, Design 1.5, the rest 1."""
    categories = json.loads(_fixture("livebench", "categories-20261106.json"))
    table = ("model,long_agentic,reasoning,coding,browser,data_analysis,research,design\n"
             "m-1,10,20,30,40,50,60,70\n")
    rows, _ = parse_livebench(_raw(table, categories))
    weighted = (10 * 2 + 20 + 30 * 1.5 + 40 + 50 + 60 + 70 * 1.5) / (2 + 1 + 1.5 + 1 + 1 + 1 + 1.5)
    assert rows[0].score == round(weighted, 2)


@pytest.mark.parametrize("weights", [
    ["A", 2], {"A": 0}, {"A": -1}, {"A": "high"}, {"A": True}, {"A": float("inf")}, {"Z": 2},
], ids=["not-a-map", "zero", "negative", "text", "bool", "infinite", "an-unknown-category"])
def test_weights_of_any_other_shape_fail_livebench(weights: object) -> None:
    """Clause 2: a weights entry the parser cannot read as the page does is a changed format, never a guess."""
    with pytest.raises(SourceError):
        parse_livebench(_raw("model,a,b\nm-1,40,100\n", {"A": ["a"], "B": ["b"], "_overall_weights": weights}))


@pytest.mark.parametrize("release", [None, "", "20261106", "2026-13-01"], ids=["absent", "blank", "undashed", "no-date"])
def test_a_release_without_its_date_fails_livebench(release: str | None) -> None:
    """Clause 1: every row is dated by the release read, so a payload that names none is not the board."""
    payload = {"table": "model,a\nm-1,40\n", "categories": {"A": ["a"]}}
    if release is not None:
        payload["release"] = release
    with pytest.raises(SourceError):
        parse_livebench(json.dumps(payload))


@pytest.mark.respx(assert_all_called=False)
def test_deepswe_reads_the_leaderboard_its_page_loads(respx_mock: respx.MockRouter) -> None:
    """Clause 3: the recorded page loads `v1.1`; the night fetches that file from the same host."""
    respx_mock.get(DC_SITE).mock(return_value=httpx.Response(200, text=_fixture("datacurve", "page.html")))
    board = respx_mock.get(_leaderboard("v1.1")).mock(
        return_value=httpx.Response(200, text=_fixture("datacurve", "leaderboard-live.json")))
    assert json.loads(DatacurveClient().fetch_raw())["rows"]
    assert board.called


@pytest.mark.respx(assert_all_called=False)
def test_deepswe_takes_the_newest_version_its_page_names(respx_mock: respx.MockRouter) -> None:
    """Clause 3: a page naming `v1.1` and `v1.10` reads `v1.10`, the newest (numeric order: the test below)."""
    page = _fixture("datacurve", "page.html") + '"/artifacts/v1.10/leaderboard-live.json"'
    respx_mock.get(DC_SITE).mock(return_value=httpx.Response(200, text=page))
    old = respx_mock.get(_leaderboard("v1.1")).mock(return_value=httpx.Response(200, text="{}"))
    new = respx_mock.get(_leaderboard("v1.10")).mock(
        return_value=httpx.Response(200, text=_fixture("datacurve", "leaderboard-live.json")))
    DatacurveClient().fetch_raw()
    assert new.called and not old.called


@pytest.mark.respx(assert_all_called=False)
def test_deepswe_compares_versions_as_numbers_v1_10_beats_v1_9(respx_mock: respx.MockRouter) -> None:
    """Clause 3 (tester, 2026-11-10b): `v1.9` and `v1.10` -- text order puts `1.9` last, numeric order `1.10`."""
    page = (_fixture("datacurve", "page.html")
            + '"/artifacts/v1.9/leaderboard-live.json" "/artifacts/v1.10/leaderboard-live.json"')
    respx_mock.get(DC_SITE).mock(return_value=httpx.Response(200, text=page))
    old = respx_mock.get(_leaderboard("v1.9")).mock(return_value=httpx.Response(200, text="{}"))
    new = respx_mock.get(_leaderboard("v1.10")).mock(
        return_value=httpx.Response(200, text=_fixture("datacurve", "leaderboard-live.json")))
    DatacurveClient().fetch_raw()
    assert new.called and not old.called


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("page", ['"/artifacts/v1/leaderboard-live.json"', "<html>DeepSWE</html>"],
                         ids=["only-older-than-v1.1", "no-leaderboard-named"])
def test_a_page_that_names_no_leaderboard_at_or_past_v1_1_fails_deepswe(
    respx_mock: respx.MockRouter, page: str,
) -> None:
    """Clauses 3 and 4: never older than `v1.1`; nothing else is fetched."""
    respx_mock.get(DC_SITE).mock(return_value=httpx.Response(200, text=page))
    artifacts = respx_mock.get(url__startswith="https://deepswe.datacurve.ai/artifacts/").mock(
        return_value=httpx.Response(200))
    with pytest.raises(SourceError):
        DatacurveClient().fetch_raw()
    assert not artifacts.called


def test_the_credits_and_citations_name_the_board_not_a_release() -> None:
    """Clause 5: the release is the row's date (LiveBench) or the night's file (DeepSWE), never a fixed credit."""
    from app.workflows import board_tables, rank

    for source, pinned in (("livebench", "2026-10-14"), ("datacurve_deepswe", "v1.1")):
        citation = rank.SOURCE_ATTRIBUTION[source]
        [credit] = rank.credits_for([citation])
        assert pinned not in citation and pinned not in str(credit["data"]), source
    assert not hasattr(board_tables, "LIVEBENCH_RELEASE_DATE")


@pytest.mark.respx(assert_all_called=False)
def test_a_hostile_page_fails_livebench_in_linear_time(respx_mock: respx.MockRouter) -> None:
    """Clause 4 (security delta 2026-11-10b, M23): a page of many `<script` openings that load nothing fails the
    source at once. A pattern quadratic in the page ran past the build's kill on a page of a few megabytes, which
    loses the night for every source, not this one."""
    import time

    respx_mock.get(LB_SITE).mock(return_value=httpx.Response(200, text="<script " * 12_000))
    started = time.monotonic()
    with pytest.raises(SourceError):
        LiveBenchClient().fetch_raw()
    assert time.monotonic() - started < 2.0


@pytest.mark.respx(assert_all_called=False)
def test_a_version_past_any_real_length_fails_deepswe_not_the_night(respx_mock: respx.MockRouter) -> None:
    """Clauses 3 and 4 (security delta 2026-11-10b, M24): a version of 5,000 digits is past Python's integer
    conversion limit; it fails the source as `SourceError`, never a `ValueError` the build does not catch."""
    page = '"/artifacts/v' + "9" * 5_000 + '/leaderboard-live.json"'
    respx_mock.get(DC_SITE).mock(return_value=httpx.Response(200, text=page))
    artifacts = respx_mock.get(url__startswith="https://deepswe.datacurve.ai/artifacts/").mock(
        return_value=httpx.Response(200))
    with pytest.raises(SourceError):
        DatacurveClient().fetch_raw()
    assert not artifacts.called
