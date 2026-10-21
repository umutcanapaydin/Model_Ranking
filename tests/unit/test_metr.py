"""METR's time horizons, and the `long-tasks` surface they open (#379, D-218 clause 2, D-219) — cite REQ-SRC-013.

METR publishes each model's time horizon as one YAML file its page offers for download (Time Horizon 1.1,
`assets/benchmark_results_1_1.yaml`): the length of task, in a skilled person's minutes, the model finishes half the
time. METR publishes no licence and no terms; its public numbers are used under D-215 with its credit. D-218 clause 2
opens a surface for it, `long-tasks`, not a second board in `agentic-coding`. The fixture is the file as published on
2026-10-22 (`tests/fixtures/metr/`).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import httpx
import pytest
import respx

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "metr" / "benchmark_results_1_1.yaml"
SITE = "https://metr.org/time-horizons/"
DATA = "https://metr.org/assets/benchmark_results_1_1.yaml"


def _metr():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.metr")


def _raw() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _parse(raw: str):
    return _metr().parse_metr(raw, source="metr_time_horizons")


def _by_name(rows: list) -> dict[str, object]:
    return {row.raw_name: row for row in rows}


def test_each_model_is_a_row_at_its_fifty_percent_horizon_in_minutes_and_undated() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): 26 models, none skipped; the score is the 50% time horizon in minutes; the
    harness is the scaffold METR names last; a row is undated, because `release_date` is the model's release (D-139).
    A name is METR's key with its `_inspect` mark (the harness) removed and its underscores read as hyphens."""
    rows, skipped = _parse(_raw())
    assert (len(rows), skipped) == (26, 0)
    top = _by_name(rows)["claude-mythos-preview-early"]
    assert (round(top.score, 2), top.harness, top.run_date, top.source_url) == (
        1044.78, "metr_agents/react", None, SITE)
    assert (top.benchmark, top.metric, top.source) == ("METR time horizon", "minutes", "metr_time_horizons")
    assert _by_name(rows)["gpt-5-2"].harness == "triframe_inspect/triframe_agent"
    assert round(_by_name(rows)["claude-opus-4-6"].score, 2) == 718.81
    assert _by_name(rows)["gpt2"].harness == "METR"  # names no scaffold


@pytest.mark.parametrize("change", [
    {"metrics": {"p50_horizon_length": {"estimate": -1.0}}},
    {"metrics": {"p50_horizon_length": {"estimate": "long"}}},
    {"metrics": {"p50_horizon_length": {}}},
    {"metrics": {}},
    {"metrics": {"p50_horizon_length": {"estimate": True}}},
], ids=["negative", "text", "no-estimate", "no-horizon", "a-bool"])
def test_a_model_without_a_usable_horizon_is_skipped_and_counted(change: dict[str, object]) -> None:
    import yaml

    board = yaml.safe_load(_raw())
    board["results"]["o3_inspect"] |= change
    rows, skipped = _parse(yaml.safe_dump(board))
    assert (len(rows), skipped) == (25, 1)
    assert "o3" not in _by_name(rows)


@pytest.mark.parametrize("raw", ["[unclosed", "just text", "results: []", "results: {}", "a: &x [*x]"],
                         ids=["not-yaml", "a-string", "results-a-list", "no-results", "an-alias-loop"])
def test_a_file_that_is_not_the_board_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-013: a broken payload is a failed night, carried, never an empty board; YAML is read through
    the project's bounded loader (W-005)."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


@pytest.mark.respx(assert_all_called=False)
def test_the_client_reads_the_file_from_metrs_own_host_with_no_token(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): one public file, no `Authorization` header, from METR's own host."""
    monkeypatch.setenv("HF_TOKEN", "stand-in-token-for-tests")
    site = respx_mock.get(DATA).mock(return_value=httpx.Response(200, text=_raw()))
    client = _metr().MetrClient()
    assert (client.name, client.url, tuple(client.hosts)) == ("metr_time_horizons", DATA, ("metr.org",))
    rows, _ = _parse(client.fetch_raw())
    assert len(rows) == 26
    assert site.call_count == 1 and "authorization" not in site.calls.last.request.headers


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("answer", [
    httpx.Response(503, text="unavailable"),
    httpx.Response(302, headers={"location": "https://elsewhere.example.net/benchmark_results.yaml"}),
], ids=["down", "redirected-off-the-site"])
def test_a_site_that_fails_fails_the_source_and_no_other_host_is_asked(
    respx_mock: respx.MockRouter, answer: httpx.Response,
) -> None:
    """covers REQ-SRC-013: no fallback; the refresh carries the previous night's rows (D-156)."""
    from app.clients.protocols import SourceError

    respx_mock.get(DATA).mock(return_value=answer)
    elsewhere = respx_mock.get("https://elsewhere.example.net/benchmark_results.yaml").mock(
        return_value=httpx.Response(200, text=_raw()))
    with pytest.raises(SourceError):
        _metr().MetrClient().fetch_raw()
    assert not elsewhere.called


def test_the_source_is_declared_optional_and_its_floor_is_half_the_recorded_board() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): optional (D-121), floor half the board as recorded."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "metr_time_horizons")
    assert declared.client is _metr().MetrClient and declared.required is False
    rows, _ = declared.parse(_raw())
    assert declared.minimum_rows == len(rows) // 2


def test_long_tasks_is_its_own_surface_ranked_on_metrs_horizon_alone() -> None:
    """covers REQ-SRC-013 (D-218 clause 2, D-219 clause 3): `long-tasks` ranks on METR's board, its only board, priced,
    titled for what it measures; it is not a board of `agentic-coding`."""
    from app.workflows import categories, families
    from app.workflows.standings import HIGHER_IS_BETTER

    spec = categories.CATEGORIES["long-tasks"]
    assert (spec.title, spec.primary_source, spec.primary_benchmark, spec.metric, spec.score_unit, spec.priced) == (
        "Long tasks", "metr_time_horizons", "METR time horizon", "minutes", "minutes", True)
    assert families.FAMILIES["long-tasks"] == ("metr_time_horizons",)
    assert "metr_time_horizons" not in families.FAMILIES["agentic-coding"]
    assert "minutes" in HIGHER_IS_BETTER


def test_metr_is_credited_for_its_public_numbers_with_its_link() -> None:
    """covers REQ-SRC-013 (D-219 clauses 1 and 4): no licence published, public numbers attributed under D-215."""
    from app.workflows import rank

    citation = rank.SOURCE_ATTRIBUTION["metr_time_horizons"]
    assert SITE in citation and citation in rank.ATTRIBUTIONS
    [credit] = rank.credits_for([citation])
    assert credit == {**credit, "publisher": "METR", "url": SITE, "licence_url": None}
    assert "D-215" in str(credit["licence"])


def test_the_registered_ingest_stores_each_row() -> None:
    """covers REQ-SRC-013: through the build's own path, the store keeps the parser's rows."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "metr_time_horizons")
    conn = connect(":memory:")
    report = declared.ingest(conn, FakeRawSource(name="metr_time_horizons", url=DATA, payload=_raw()),
                             RunContext(observed_at="2026-10-22T00:00:00Z"))
    assert (report.stored, report.skipped) == (26, 0)
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE source = 'metr_time_horizons'").fetchone()[0] == 26
