"""OSWorld-Verified from its own results workbook (#379, D-219) — cite REQ-SRC-013.

The OSWorld team publishes its verified board as one workbook, `osworld_verified_results.xlsx`, which its page
loads and averages in the browser. The site moved from `os-world.github.io` (now a plain-HTTP redirect) to
`osworld-v1.xlang.ai`, the one host the client asks. D-219 clause 2 reads the rows the page's default "Foundation E2E
GUI" tab shows that a catalogue can sell: approach type `General model`, no extra accessibility tree and no coding
action, at 100 steps; a model's score is the mean of its runs, as the page shows it, dated by its latest run. The
fixture is the workbook as published on 2026-10-22 (`tests/fixtures/osworld/`).
"""

from __future__ import annotations

import importlib
import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest
import respx

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "osworld" / "osworld_verified_results.xlsx"
SITE = "https://osworld-v1.xlang.ai/"
WORKBOOK = "https://osworld-v1.xlang.ai/static/data/osworld_verified_results.xlsx"
OLD_HOME = "https://os-world.github.io/static/data/osworld_verified_results.xlsx"


def _ow():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.osworld")


def _raw() -> str:
    return json.dumps(_ow().workbook_rows(FIXTURE.read_bytes()))


def _parse(raw: str):
    return _ow().parse_osworld(raw, source="osworld_verified")


def _by_name(rows: list) -> dict[str, object]:
    return {row.raw_name: row for row in rows}


def test_each_general_model_at_100_steps_is_a_row_at_the_mean_of_its_runs_dated_by_its_latest() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): 20 general models run end to end at 100 steps; the one that used an extra
    accessibility tree or coding action (Coasty CUA v1) is skipped and counted. A score is the mean of the model's
    runs, as the page shows it, in points; a row is dated by its latest run."""
    rows, skipped = _parse(_raw())
    assert (len(rows), skipped) == (20, 1)
    fable = _by_name(rows)["claude-fable-5[1m]"]
    assert (round(fable.score, 2), fable.run_date, fable.harness) == (85.96, "2026-08-01", "OSWorld (100 steps)")
    assert (fable.benchmark, fable.metric, fable.source, fable.source_url) == (
        "OSWorld-Verified", "% success", "osworld_verified", SITE)
    assert _by_name(rows)["claude-sonnet-4-6"].run_date == "2026-03-08"
    assert round(_by_name(rows)["o3"].score, 2) == 23.0
    assert "Coasty CUA v1" not in _by_name(rows)
    # Specialized GUI models and agentic frameworks are not catalogue models (D-219 clause 2).
    assert not any(name.startswith(("opencua", "uitars", "agent s")) for name in _by_name(rows))


def test_runs_of_one_model_are_averaged_as_the_page_averages_them() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): two runs at 100 steps stand as one row at their mean."""
    workbook = json.loads(_raw())
    first = next(row for row in workbook if row.get("Model") == "o3" and str(row.get("Max steps")) == "100")
    workbook.append(first | {"Success rate": "27"})
    rows, skipped = _parse(json.dumps(workbook))
    assert (len(rows), skipped) == (20, 1)
    assert round(_by_name(rows)["o3"].score, 2) == 25.0


@pytest.mark.parametrize("change", [
    {"Success rate": "🚧"}, {"Success rate": "-"}, {"Success rate": "130"}, {"Additional a11y tree used": "Yes"},
    {"Additional coding-based action": "Yes"},
], ids=["under-construction", "a-dash", "above-a-hundred", "a11y-tree", "coding-action"])
def test_a_run_that_is_not_a_usable_end_to_end_score_is_skipped_and_counted(change: dict[str, object]) -> None:
    workbook = json.loads(_raw())
    for row in workbook:
        if row.get("Model") == "o3" and str(row.get("Max steps")) == "100":
            row |= change
    rows, skipped = _parse(json.dumps(workbook))
    assert (len(rows), skipped) == (19, 2)
    assert "o3" not in _by_name(rows)


def test_a_run_at_another_step_budget_or_of_another_approach_is_not_this_board() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): a run at 15 or 50 steps is another measurement, never mixed in."""
    rows, _ = _parse(_raw())
    sonnet = _by_name(rows)["claude-sonnet-4-5-20250929"]
    assert round(sonnet.score, 2) == 62.88  # its 15- and 50-step runs read 42.88 and 58.08


@pytest.mark.parametrize("raw", ["not json", "{}", json.dumps([]), json.dumps([{"Model": "o3"}])],
                         ids=["not-json", "not-a-list", "empty", "no-usable-row"])
def test_a_workbook_that_is_not_the_board_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): a broken payload is a failed night, carried, never an empty board."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


def _zip(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, body in members.items():
            archive.writestr(name, body)
    return buffer.getvalue()


@pytest.mark.parametrize("data", [
    b"<html>301 Moved Permanently</html>",
    _zip({"xl/worksheets/sheet1.xml": b"<?xml version='1.0'?><!DOCTYPE x [<!ENTITY a 'b'>]><worksheet/>"}),
    _zip({"xl/workbook.xml": b"<workbook/>"}),
], ids=["not-a-workbook", "an-entity-declaration", "no-sheet"])
def test_a_file_that_is_not_a_plain_workbook_fails_the_source(data: bytes) -> None:
    """covers REQ-SRC-013: the workbook is read with the standard library, refusing a document that declares entities
    (an expansion bomb) and a file that is not a workbook."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _ow().workbook_rows(data)


def test_a_sheet_larger_than_the_cap_fails_the_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """covers REQ-SRC-013: a member that unpacks past the cap is refused before it is read (a zip bomb)."""
    from app.clients.protocols import SourceError

    monkeypatch.setattr(_ow(), "MAX_MEMBER_BYTES", 1024)
    with pytest.raises(SourceError, match="unpacks"):
        _ow().workbook_rows(FIXTURE.read_bytes())


@pytest.mark.respx(assert_all_called=False)
def test_the_client_reads_the_workbook_from_the_sites_own_host_with_no_token(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-013 (D-219 clause 2): one public file, no `Authorization` header, from its own host."""
    monkeypatch.setenv("HF_TOKEN", "stand-in-token-for-tests")
    site = respx_mock.get(WORKBOOK).mock(return_value=httpx.Response(200, content=FIXTURE.read_bytes()))
    client = _ow().OSWorldClient()
    assert (client.name, client.url, tuple(client.hosts)) == ("osworld_verified", WORKBOOK, ("osworld-v1.xlang.ai",))
    rows, skipped = _parse(client.fetch_raw())
    assert (len(rows), skipped) == (20, 1)
    assert site.call_count == 1 and "authorization" not in site.calls.last.request.headers


@pytest.mark.respx(assert_all_called=False)
@pytest.mark.parametrize("answer", [
    httpx.Response(503, text="unavailable"),
    httpx.Response(301, headers={"location": "http://osworld-v1.xlang.ai/static/data/osworld_verified_results.xlsx"}),
    httpx.Response(302, headers={"location": "https://elsewhere.example.net/results.xlsx"}),
], ids=["down", "redirected-to-plain-http", "redirected-off-the-site"])
def test_a_site_that_fails_fails_the_source_and_no_other_host_is_asked(
    respx_mock: respx.MockRouter, answer: httpx.Response,
) -> None:
    """covers REQ-SRC-013: no fallback; the night fails and the refresh carries the previous night's rows (D-156)."""
    from app.clients.protocols import SourceError

    respx_mock.get(WORKBOOK).mock(return_value=answer)
    plain = respx_mock.get("http://osworld-v1.xlang.ai/static/data/osworld_verified_results.xlsx").mock(
        return_value=httpx.Response(200, content=FIXTURE.read_bytes()))
    elsewhere = respx_mock.get("https://elsewhere.example.net/results.xlsx").mock(
        return_value=httpx.Response(200, content=FIXTURE.read_bytes()))
    old = respx_mock.get(OLD_HOME).mock(return_value=httpx.Response(200, content=FIXTURE.read_bytes()))
    with pytest.raises(SourceError):
        _ow().OSWorldClient().fetch_raw()
    assert not plain.called and not elsewhere.called and not old.called


def test_the_source_is_declared_optional_and_its_floor_is_half_the_recorded_board() -> None:
    """covers REQ-SRC-013 (D-219 clause 2): optional (D-121), floor half the board as recorded."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "osworld_verified")
    assert declared.client is _ow().OSWorldClient and declared.required is False
    rows, _ = declared.parse(_raw())
    assert declared.minimum_rows == len(rows) // 2


def test_computer_use_adds_osworld_verified_after_its_primary() -> None:
    """covers REQ-SRC-013 (D-219 clause 3): OSWorld-Verified stands in `computer-use`; the primary stays."""
    from app.workflows import categories, families

    assert families.FAMILIES["computer-use"] == ("terminalbench_4", "osworld_verified", "arena_agent")
    assert categories.CATEGORIES["computer-use"].primary_source == "terminalbench_4"


def test_osworld_is_credited_under_the_sites_cc_by_sa_licence_with_its_link() -> None:
    """covers REQ-SRC-013 (D-219 clauses 1 and 4): the citation and the Credits screen name the site and licence."""
    from app.workflows import board_tables, rank

    citation = rank.SOURCE_ATTRIBUTION["osworld_verified"]
    assert SITE in citation and "CC BY-SA 4.0" in citation and citation in rank.ATTRIBUTIONS
    [credit] = rank.credits_for([citation])
    assert credit == {**credit, "url": SITE, "licence": "CC BY-SA 4.0",
                      "licence_url": "https://creativecommons.org/licenses/by-sa/4.0/"}
    assert credit["id"] in board_tables.CREDITS


def test_the_registered_ingest_stores_each_row() -> None:
    """covers REQ-SRC-013: through the build's own path, the store keeps the parser's rows."""
    import sqlite3

    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "osworld_verified")
    conn: sqlite3.Connection = connect(":memory:")
    run = RunContext(observed_at="2026-10-22T00:00:00Z")
    report = declared.ingest(conn, FakeRawSource(name="osworld_verified", url=WORKBOOK, payload=_raw()), run)
    assert (report.stored, report.skipped) == (20, 1)
    stored = conn.execute("SELECT COUNT(*) FROM scores WHERE source = 'osworld_verified'").fetchone()[0]
    assert stored == 20
