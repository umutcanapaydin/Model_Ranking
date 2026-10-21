"""DeepSWE from Datacurve's own leaderboard (#265, D-216) — cite REQ-SRC-012.

`agentic-coding` ranked on Epoch's copy of the DeepSWE board, which publishes no licence. Datacurve's site loads its
leaderboard as one JSON file (`leaderboard-live.json`, DeepSWE v1.1): one row a configuration, with its model, harness,
stated reasoning effort and Pass@1. It is public, read with no token, and used under D-215 with Datacurve's credit.
On a night the site fails, the refresh's carry-forward keeps the previous night's rows (D-156, the owner's ruling of
2026-10-21): the source has no fallback. The fixture is the file of 2026-10-21, trimmed to the fields read
(`tests/fixtures/datacurve/`).
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import httpx
import pytest
import respx

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "datacurve"
SITE = "https://deepswe.datacurve.ai/"
LIVE = "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json"
#: The Hugging Face dataset D-216's earlier text read; the source must never ask it.
HUB_JOBS = "https://huggingface.co/api/datasets/datacurve/deep-swe-leaderboard/tree/main/raw/jobs"


def _dc():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.datacurve")


def _live(board: object | None = None) -> str:
    text = (FIXTURES / "leaderboard-live.json").read_text(encoding="utf-8")
    return text if board is None else json.dumps(board)


def _parse(raw: str):
    return _dc().parse_datacurve(raw, source="datacurve_deepswe")


def _by_key(rows: list) -> dict[tuple[str, str | None], object]:
    return {(row.raw_name, row.effort): row for row in rows}


def test_each_leaderboard_row_is_a_row_at_its_pass_at_1_harness_and_stated_effort() -> None:
    """covers REQ-SRC-012 (D-216 clauses 1, 3, 4): 70 configurations, none skipped; the score is Pass@1 in points; a
    row keeps the effort Datacurve states, and the one that states none ran at its default and stands at `high`. The
    list gathers jobs of several dates and names none per row, so its rows are undated."""
    rows, skipped = _parse(_live())
    assert (len(rows), skipped) == (70, 0)
    top = _by_key(rows)[("gpt-6-astra", "xhigh")]
    assert (round(top.score, 2), top.harness, top.run_date, top.source_url) == (74.12, "mini-swe-agent", None, SITE)
    assert (top.benchmark, top.metric, top.source) == ("DeepSWE", "% resolved", "datacurve_deepswe")
    assert _by_key(rows)[("kimi-k2-7-code", "high")].score == pytest.approx(30.53, abs=0.01)
    assert sorted(effort for name, effort in _by_key(rows) if name == "gpt-6-astra") == [
        "high", "low", "max", "medium", "xhigh"]
    assert sum(1 for row in rows if row.effort == "high") == 19


@pytest.mark.parametrize("change", [
    {"pass_at_1": 1.5}, {"pass_at_1": "0.7"}, {"pass_at_1": None}, {"pass_at_1": True}, {"reasoning_effort": "ultra"},
    {"source": "swe-bench"}, {"model": ""}, {"harness": None},
], ids=["above-one", "text", "missing", "a-bool", "unknown-effort", "another-benchmark", "no-model", "no-harness"])
def test_a_leaderboard_row_that_is_not_a_usable_deepswe_score_is_skipped_and_counted(change: dict[str, object]) -> None:
    board = json.loads(_live())
    board["rows"][0] |= change  # gpt-6-astra at xhigh
    rows, skipped = _parse(_live(board))
    assert (len(rows), skipped) == (69, 1)
    assert ("gpt-6-astra", "xhigh") not in _by_key(rows)


def test_two_rows_of_one_model_harness_and_effort_keep_the_better() -> None:
    board = json.loads(_live())
    board["rows"].append(board["rows"][0] | {"pass_at_1": 0.5})
    rows, skipped = _parse(_live(board))
    assert (len(rows), skipped) == (70, 1)
    assert round(_by_key(rows)[("gpt-6-astra", "xhigh")].score, 2) == 74.12


@pytest.mark.parametrize("raw", ["not json", "[]", json.dumps({"rows": "none"}), json.dumps({"rows": []}),
                                 json.dumps({"no_rows": 1})],
                         ids=["not-json", "a-list", "rows-not-a-list", "no-rows", "no-rows-key"])
def test_a_leaderboard_that_is_not_the_boards_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-012 (D-216 clause 6): a broken payload is a failed night, carried, never an empty board."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


@pytest.mark.respx(assert_all_called=False)
def test_the_client_reads_the_leaderboard_with_no_token_from_its_own_host(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-012 (D-216 clauses 1 and 5): one public file, no `Authorization` header even with a token in the
    environment, and the Hugging Face dataset is never asked."""
    monkeypatch.setenv("HF_TOKEN", "stand-in-token-for-tests")
    site = respx_mock.get(LIVE).mock(return_value=httpx.Response(200, text=_live()))
    hub = respx_mock.get(HUB_JOBS).mock(return_value=httpx.Response(200, json=[]))
    client = _dc().DatacurveClient()
    assert (client.name, client.url, tuple(client.hosts)) == ("datacurve_deepswe", LIVE, ("deepswe.datacurve.ai",))
    rows, skipped = _parse(client.fetch_raw())
    assert (len(rows), skipped) == (70, 0)
    assert site.call_count == 1 and "authorization" not in site.calls.last.request.headers
    assert not hub.called


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("answer", [
    httpx.Response(503, text="unavailable"),
    httpx.Response(302, headers={"location": "https://elsewhere.example.net/leaderboard-live.json"}),
], ids=["down", "redirected-off-the-site"])
def test_a_site_that_fails_fails_the_source_and_nothing_else_is_asked(
    respx_mock: respx.MockRouter, answer: httpx.Response,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 6): no fallback. The night fails, and the refresh carries the previous
    night's rows (`test_datacurve_move.py` holds that); no other host and no dataset is read."""
    from app.clients.protocols import SourceError

    respx_mock.get(LIVE).mock(return_value=answer)
    elsewhere = respx_mock.get("https://elsewhere.example.net/leaderboard-live.json").mock(
        return_value=httpx.Response(200, text=_live()))
    hub = respx_mock.get(HUB_JOBS).mock(return_value=httpx.Response(200, json=[]))
    with pytest.raises(SourceError):
        _dc().DatacurveClient().fetch_raw()
    assert not elsewhere.called and not hub.called


def test_no_token_is_read_anywhere_in_the_source() -> None:
    """covers REQ-SRC-012 (D-216 clause 5): the engine holds no Hugging Face token for this source."""
    module = _dc()
    assert not any(hasattr(module, name) for name in ("read_token", "token_available", "token_file"))


def test_the_source_is_declared_optional_and_its_floor_is_half_the_recorded_board() -> None:
    """covers REQ-SRC-012 (D-216 clause 6): optional (D-121), so a failed night is carried and never fails another
    source; half the recorded board, as Arena's floors are, so a cut file fails rather than thins the surface."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    assert declared.client is _dc().DatacurveClient and declared.required is False
    rows, _ = declared.parse(_live())
    assert declared.minimum_rows == len(rows) // 2


def test_the_registered_ingest_stores_each_row_at_the_effort_a_reader_is_shown() -> None:
    """covers REQ-SRC-012: through the build's own path, the store keeps the parser's efforts."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    conn = connect()
    report = declared.ingest(conn, FakeRawSource("datacurve_deepswe", _live()), RunContext(observed_at="t"))
    assert (report.stored, report.skipped, report.effort_unknown) == (70, 0, 0)
    stored = dict(conn.execute("SELECT effort, count(*) FROM scores WHERE source = 'datacurve_deepswe' GROUP BY effort"))
    assert stored == {"high": 19, "xhigh": 14, "max": 14, "medium": 12, "low": 11}
