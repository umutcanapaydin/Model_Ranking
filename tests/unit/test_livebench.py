"""LiveBench 2.0 from its own release files (#379, D-219) — cite REQ-SRC-013.

LiveBench publishes each release as static files on its own site: `table.csv`, one row per model and one column per
suite, and `categories.json`, each category's columns. Its page computes the overall score in the browser and stores
none: "mean of category averages". D-219 clause 2 reads release 2026-10-14 (LiveBench 2.0), pinned as Datacurve's
`v1.1` is, and computes the overall the way the page states it, rounded to two places as the page rounds. LiveBench
publishes no data licence; its public numbers are used under D-215 with its credit. The fixture is the release as
published on 2026-10-22 (`tests/fixtures/livebench/`).
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import httpx
import pytest
import respx

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "livebench"
SITE = "https://livebench.ai/"
TABLE = "https://livebench.ai/data/20261014/table.csv"
CATEGORIES = "https://livebench.ai/data/20261014/categories.json"


def _lb():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.livebench")


def _table() -> str:
    return (FIXTURES / "table.csv").read_text(encoding="utf-8")


def _categories() -> str:
    return (FIXTURES / "categories.json").read_text(encoding="utf-8")


def _raw(table: str | None = None, categories: str | None = None) -> str:
    return json.dumps({"table": _table() if table is None else table,
                       "categories": json.loads(_categories() if categories is None else categories)})


def _parse(raw: str):
    return _lb().parse_livebench(raw, source="livebench")


def _by_name(rows: list) -> dict[str, object]:
    return {row.raw_name: row for row in rows}


def test_each_model_is_a_row_at_the_mean_of_its_category_averages_dated_by_the_release() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): 49 models, none skipped; the score is the mean of the seven category
    averages, rounded to two places as the page rounds; every row is dated by the release."""
    rows, skipped = _parse(_raw())
    assert (len(rows), skipped) == (49, 0)
    top = _by_name(rows)["claude-fable-5.1"]
    assert (top.score, top.run_date, top.harness, top.source_url) == (87.99, "2026-10-14", "LiveBench", SITE)
    assert (top.benchmark, top.metric, top.source) == ("LiveBench", "% correct", "livebench")
    assert _by_name(rows)["gpt-6-astra"].score == 86.14


def test_a_category_of_several_columns_is_averaged_before_the_categories_are() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): a category's average is the mean of its columns, then the overall is
    the mean of the categories, so a category of two columns counts once, as the page counts it."""
    table = "model,a,b,c\nm-1,10,30,60\n"
    rows, _ = _parse(_raw(table, json.dumps({"First": ["a", "b"], "Second": ["c"]})))
    assert _by_name(rows)["m-1"].score == 40.0  # (mean(10, 30) + 60) / 2


@pytest.mark.parametrize("cell", ["", "-", "n/a", "high", "130"], ids=["blank", "dash", "n-a", "text", "above-100"])
def test_a_row_missing_a_category_is_skipped_and_counted(cell: str) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): a model without every category is not on the board's footing."""
    lines = _table().splitlines()
    header, first = lines[0].split(","), lines[1].split(",")
    first[header.index("browser")] = cell
    table = "\n".join([lines[0], ",".join(first), *lines[2:]]) + "\n"
    rows, skipped = _parse(_raw(table))
    assert (len(rows), skipped) == (48, 1)
    assert first[0] not in _by_name(rows)


@pytest.mark.parametrize("raw", [
    "not json", json.dumps([]), json.dumps({"table": "model,a\n", "categories": {"A": ["a"]}}),
    json.dumps({"table": "model,a\nm,1\n", "categories": {}}),
    json.dumps({"table": "model,a\nm,1\n", "categories": {"A": ["missing"]}}),
], ids=["not-json", "not-an-object", "no-rows", "no-categories", "a-category-names-no-column"])
def test_a_release_that_is_not_the_board_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-013: a broken payload is a failed night, carried, never an empty board."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


@pytest.mark.respx(assert_all_called=False)
def test_the_client_reads_both_files_of_the_pinned_release_from_its_own_host(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): two public files of release 2026-10-14, no `Authorization` header."""
    monkeypatch.setenv("HF_TOKEN", "stand-in-token-for-tests")
    table = respx_mock.get(TABLE).mock(return_value=httpx.Response(200, text=_table()))
    cats = respx_mock.get(CATEGORIES).mock(return_value=httpx.Response(200, text=_categories()))
    client = _lb().LiveBenchClient()
    assert (client.name, client.url, tuple(client.hosts)) == ("livebench", TABLE, ("livebench.ai",))
    rows, _ = _parse(client.fetch_raw())
    assert len(rows) == 49
    assert table.call_count == 1 and cats.call_count == 1
    assert "authorization" not in table.calls.last.request.headers


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("answer", [
    httpx.Response(404, text="not found"),
    httpx.Response(302, headers={"location": "https://elsewhere.example.net/table.csv"}),
], ids=["gone", "redirected-off-the-site"])
def test_a_site_that_fails_fails_the_source_and_no_other_host_is_asked(
    respx_mock: respx.MockRouter, answer: httpx.Response,
) -> None:
    """covers REQ-SRC-013: no fallback; the refresh carries the previous night's rows (D-156)."""
    from app.clients.protocols import SourceError

    respx_mock.get(TABLE).mock(return_value=answer)
    respx_mock.get(CATEGORIES).mock(return_value=httpx.Response(200, text=_categories()))
    elsewhere = respx_mock.get("https://elsewhere.example.net/table.csv").mock(
        return_value=httpx.Response(200, text=_table()))
    with pytest.raises(SourceError):
        _lb().LiveBenchClient().fetch_raw()
    assert not elsewhere.called


def test_the_source_is_declared_optional_and_its_floor_is_half_the_recorded_board() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): optional (D-121), floor half the board as recorded."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "livebench")
    assert declared.client is _lb().LiveBenchClient and declared.required is False
    rows, _ = declared.parse(_raw())
    assert declared.minimum_rows == len(rows) // 2


def test_everyday_adds_livebench_after_its_other_boards() -> None:
    """covers REQ-SRC-013 (D-219 clause 3): LiveBench stands in `everyday`; the primary stays."""
    from app.workflows import categories, families

    assert families.FAMILIES["everyday"][:3] == ("epoch_eci", "arena", "epoch_mmlu")
    assert "livebench" in families.FAMILIES["everyday"]
    assert categories.CATEGORIES["everyday"].primary_source == "epoch_eci"


def test_livebench_is_credited_for_its_public_numbers_with_its_link() -> None:
    """covers REQ-SRC-013 (D-219 clauses 1 and 4): no data licence published; public numbers attributed (D-215)."""
    from app.workflows import rank

    citation = rank.SOURCE_ATTRIBUTION["livebench"]
    assert SITE in citation and citation in rank.ATTRIBUTIONS
    [credit] = rank.credits_for([citation])
    assert credit == {**credit, "url": SITE, "licence_url": None}
    assert "D-215" in str(credit["licence"])
    # The release the client reads is the one the credit and the citation name: one fact, kept once.
    assert _lb().RELEASE_DATE in str(credit["data"]) and _lb().RELEASE_DATE in citation
    assert _lb().TABLE_URL == TABLE


def test_the_registered_ingest_stores_each_row() -> None:
    """covers REQ-SRC-013: through the build's own path, the store keeps the parser's rows."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "livebench")
    conn = connect(":memory:")
    report = declared.ingest(conn, FakeRawSource(name="livebench", url=TABLE, payload=_raw()),
                             RunContext(observed_at="2026-10-22T00:00:00Z"))
    assert (report.stored, report.skipped) == (49, 0)


@pytest.mark.parametrize("name", ["minimax-m3.1-flash", "MiniMax M3.1", "minimax-m3-1-flash"])
def test_a_point_release_of_minimax_m3_is_never_read_as_minimax_m3(name: str) -> None:
    """covers REQ-SRC-013 (D-219, the unlinked-id count): LiveBench ranks MiniMax M3.1 Flash beside MiniMax M3, and the
    curated rule took any `minimax-m3` prefix, so M3's row would have carried M3.1 Flash's score. The rule stops
    before a point release, as MiniMax M2's does; every spelling the artifact links to M3 today still reads as M3."""
    from app.workflows.registry import canonicalize

    rule = canonicalize(name)
    assert rule is None or rule.canonical_id != "minimax-m3", name
    for spelling in ("minimax-m3", "MiniMax-M3", "Minimax M3", "MiniMax-M3_none", "fireworks_ai/minimax-m3",
                     "together_ai/MiniMaxAI/MiniMax-M3", "azure_ai/FW-MiniMax-M3"):
        found = canonicalize(spelling)
        assert found is not None and found.canonical_id == "minimax-m3", spelling


@pytest.mark.parametrize("raw", [
    json.dumps({"table": "model,a\n" + "x" * 200_000 + ",1\n", "categories": {"c": ["a"]}}),
    "[" * 100_000,
], ids=["a-field-past-csvs-limit", "json-nested-past-the-recursion-limit"])
def test_a_release_that_breaks_the_readers_fails_the_source_and_nothing_else(raw: str) -> None:
    """covers REQ-SRC-013, D-121 (the queue-1021 integration review's M2): `csv.Error` and `RecursionError` are bad
    input, not builder bugs, so they fail this optional source as `SourceError` and never abort the night."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


@pytest.mark.respx(assert_all_called=False)
def test_categories_nested_past_the_recursion_limit_fail_the_source(respx_mock: respx.MockRouter) -> None:
    """covers REQ-SRC-013, D-121 (the queue-1021 integration review's M2): the client's own `json.loads` too."""
    from app.clients.protocols import SourceError

    respx_mock.get(TABLE).mock(return_value=httpx.Response(200, text=_table()))
    respx_mock.get(CATEGORIES).mock(return_value=httpx.Response(200, text="[" * 100_000))
    with pytest.raises(SourceError, match=r"categories\.json"):
        _lb().LiveBenchClient().fetch_raw()


def test_a_bad_optional_source_leaves_the_build_going_on_to_the_next() -> None:
    """covers D-121 (the queue-1021 integration review's M2): through `_ingest_sources`, LiveBench's oversized field
    is named as a missing optional source, and SimpleBench, declared after it, is still read and stored."""
    import dataclasses

    from app.clients.fakes import FakeRawSource
    from app.workflows import build, sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    simplebench_file = Path(__file__).resolve().parents[1] / "fixtures" / "simplebench" / "leaderboard-data.js"
    bad = json.dumps({"table": "model,a\n" + "x" * 200_000 + ",1\n", "categories": {"c": ["a"]}})
    declared = {s.name: s for s in sources.REMOTE_SOURCES}
    chain = (
        dataclasses.replace(declared["livebench"], client=lambda: FakeRawSource("livebench", bad)),
        dataclasses.replace(declared["simplebench"], client=lambda: FakeRawSource(
            "simplebench", simplebench_file.read_text(encoding="utf-8"))),
    )
    conn = connect(":memory:")
    reports, missing = build._ingest_sources(conn, chain, RunContext(observed_at="2026-10-22T00:00:00Z"))
    assert [line.split(":")[0] for line in missing] == ["livebench"]
    assert [(report.source, report.stored) for report in reports] == [("simplebench", 106)]
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE source = 'livebench'").fetchone()[0] == 0
