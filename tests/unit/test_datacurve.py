"""DeepSWE from Datacurve's own CC BY 4.0 dataset, read with the owner's token (#265, D-216) — cite REQ-SRC-012.

`agentic-coding` ranked on Epoch's copy of the DeepSWE board, which publishes no licence. Datacurve publishes the
runs themselves as `datacurve/deep-swe-leaderboard` on Hugging Face, gated behind a read token. The board is the
newest job directory under `raw/jobs/`: its result file holds each run's Pass@1, and its config file the reasoning
effort each run was given. The fixtures are both files of the job of 2026-06-06, recorded on 2026-10-21 and trimmed
to the fields read (`tests/fixtures/datacurve/`). No real token appears here: the client is handed a stand-in.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import httpx
import pytest
import respx

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "datacurve"
JOB = "20260606-deep-swe-leaderboard-all-4x"
HUB = "https://huggingface.co"
JOBS = f"{HUB}/api/datasets/datacurve/deep-swe-leaderboard/tree/main/raw/jobs"
FILES = f"{HUB}/datasets/datacurve/deep-swe-leaderboard/resolve/main/raw/jobs"
#: A stand-in, shaped like nothing Hugging Face issues: the owner's token never enters a test.
TOKEN = "stand-in-token-for-tests"


def _dc():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.datacurve")


def _text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _envelope(result: object | None = None, config: object | None = None, job: object = JOB) -> str:
    return json.dumps({
        "job": job,
        "result": _text("result.json") if result is None else json.dumps(result),
        "config": _text("config.json") if config is None else json.dumps(config),
    })


def _parse(raw: str):
    return _dc().parse_datacurve(raw, source="datacurve_deepswe")


def _by_key(rows: list) -> dict[tuple[str, str | None], object]:
    return {(row.raw_name, row.effort): row for row in rows}


# --- the parser, on the recorded job ------------------------------------------------------------------------------

def test_each_run_is_a_row_at_its_pass_at_1_harness_and_the_jobs_date() -> None:
    """covers REQ-SRC-012: 27 runs, none skipped; the score is Pass@1 in points, the agent is the harness, and the
    run date is the day the job finished. The row links the job's public page, never a URL a token opens."""
    rows, skipped = _parse(_envelope())
    assert (len(rows), skipped) == (27, 0)
    top = _by_key(rows)[("gpt-5-5", "xhigh")]
    assert (round(top.score, 2), top.harness, top.run_date) == (68.81, "mini-swe-agent", "2026-06-06")
    assert (top.benchmark, top.metric, top.source) == ("DeepSWE", "% resolved", "datacurve_deepswe")
    assert top.source_url == f"{HUB}/datasets/datacurve/deep-swe-leaderboard/tree/main/raw/jobs/{JOB}"
    assert {row.harness for row in rows} == {"mini-swe-agent"}


def test_a_run_keeps_the_effort_its_config_states_and_a_default_run_stands_at_high() -> None:
    """covers REQ-SRC-012 (D-216 clause 2): the result file names an effort only for a model run at several. The job's
    config states the rest: four ran at `xhigh`, `max` or `medium` and keep it, so none is ranked as a `high` run; the
    eleven given no effort ran at their model's default and stand at `high`, D-194 clause 1's level."""
    rows, _ = _parse(_envelope())
    efforts = {row.raw_name: row.effort for row in rows if row.raw_name not in ("gpt-5-5", "claude-opus-4-7",
                                                                                  "claude-opus-4-8")}
    assert efforts == {
        "gpt-5-4": "xhigh", "gpt-5-4-mini": "xhigh", "claude-opus-4-6": "max", "gemini-3-5-flash": "medium",
        "claude-sonnet-4-6": "high",
        **dict.fromkeys(("claude-haiku-4-5", "deepseek-v4-pro", "gemini-3-1-pro-preview", "gemini-3-flash-preview",
                         "glm-5-1", "grok-build-0-1", "kimi-k2-6", "mimo-v2-5-pro", "minimax-m2-7", "minimax-m3",
                         "qwen3-6-plus"), "high"),
    }
    assert sorted(effort for name, effort in _by_key(rows) if name == "claude-opus-4-8") == [
        "high", "max", "medium", "xhigh"]
    assert sum(1 for row in rows if row.effort == "high") == 15


@pytest.mark.parametrize("change", ["model missing from the config", "two configs and no effort in the key",
                                    "an effort the key names outside the schema",
                                    "an effort the config names outside the schema"])
def test_a_run_whose_effort_cannot_be_known_is_skipped_and_counted(change: str) -> None:
    """covers REQ-SRC-012 (D-216 clause 2): an effort is read, never guessed."""
    result = json.loads(_text("result.json"))
    config = json.loads(_text("config.json"))
    evals = result["stats"]["evals"]
    if change == "model missing from the config":
        config["agents"] = [a for a in config["agents"] if a["model_name"] != "kimi-k2-6"]
        gone = ("kimi-k2-6", "high")
    elif change == "two configs and no effort in the key":
        config["agents"].append({"name": "mini-swe-agent", "model_name": "glm-5-1", "kwargs": {"reasoning_effort": "low"}})
        gone = ("glm-5-1", "high")
    elif change == "an effort the key names outside the schema":
        evals["mini-swe-agent__gpt-5-5__ultra__deep-swe"] = evals.pop("mini-swe-agent__gpt-5-5__xhigh__deep-swe")
        gone = ("gpt-5-5", "xhigh")
    else:
        for agent in config["agents"]:
            if agent["model_name"] == "gpt-5-4":
                agent["kwargs"] = {"reasoning_effort": "minimal"}
        gone = ("gpt-5-4", "xhigh")
    rows, skipped = _parse(_envelope(result, config))
    assert (len(rows), skipped) == (26, 1)
    assert gone not in _by_key(rows)


@pytest.mark.parametrize("entry", [
    {"n_trials": 452, "metrics": [{"mean": 1.5}]},
    {"n_trials": 452, "metrics": [{"mean": -0.1}]},
    {"n_trials": 452, "metrics": [{"mean": float("nan")}]},
    {"n_trials": 452, "metrics": [{"mean": "0.5"}]},
    {"n_trials": 452, "metrics": [{"mean": True}]},
    {"n_trials": 452, "metrics": []},
    {"n_trials": 0, "metrics": [{"mean": 0.5}]},
    "not an entry",
])
def test_a_run_without_a_usable_pass_at_1_is_skipped_and_counted(entry: object) -> None:
    """covers REQ-SRC-012: a score outside 0..1, not a number, missing, or over no trials is never stored."""
    result = json.loads(_text("result.json"))
    result["stats"]["evals"]["mini-swe-agent__kimi-k2-6__deep-swe"] = entry
    rows, skipped = _parse(_envelope(result))
    assert (len(rows), skipped) == (26, 1)
    assert "kimi-k2-6" not in {row.raw_name for row in rows}


def test_a_key_that_is_not_a_deepswe_run_is_skipped_and_counted() -> None:
    result = json.loads(_text("result.json"))
    evals = result["stats"]["evals"]
    evals["mini-swe-agent__kimi-k2-6__swe-bench"] = evals.pop("mini-swe-agent__kimi-k2-6__deep-swe")
    evals["just-a-name"] = evals["mini-swe-agent__glm-5-1__deep-swe"]
    rows, skipped = _parse(_envelope(result))
    assert (len(rows), skipped) == (26, 2)


@pytest.mark.parametrize("raw", [
    "not json",
    json.dumps([]),
    json.dumps({"job": JOB, "result": "{}", "config": _text("config.json")}),
    json.dumps({"job": JOB, "result": "not json", "config": _text("config.json")}),
    json.dumps({"job": JOB, "result": _text("result.json"), "config": json.dumps({"agents": "none"})}),
    json.dumps({"job": None, "result": _text("result.json"), "config": _text("config.json")}),
], ids=["not-json", "not-an-object", "no-evals", "result-not-json", "agents-not-a-list", "no-job"])
def test_an_envelope_or_a_file_that_is_not_the_boards_fails_the_source(raw: str) -> None:
    """covers REQ-SRC-012: a broken payload is a failed source, never an empty board."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _parse(raw)


# --- the client, against the canonical double (respx on the bounded fetch) -----------------------------------------

def _listing(*names: str) -> list[dict[str, object]]:
    return [{"type": "directory", "oid": "0" * 40, "size": 0, "path": f"raw/jobs/{name}"} for name in names]


def _hub(listing: object, job: str = JOB) -> dict[str, respx.Route]:
    return {
        "jobs": respx.get(JOBS).mock(return_value=httpx.Response(200, json=listing)),
        "result": respx.get(f"{FILES}/{job}/result.json").mock(return_value=httpx.Response(200, text=_text("result.json"))),
        "config": respx.get(f"{FILES}/{job}/config.json").mock(return_value=httpx.Response(200, text=_text("config.json"))),
    }


@pytest.fixture
def no_token_file(tmp_path: Path) -> Path:
    return tmp_path / "absent" / "hf-token"


@respx.mock(assert_all_called=False)
def test_the_client_reads_the_newest_job_with_the_token_sent_to_the_hub_alone(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path,
) -> None:
    """covers REQ-SRC-012 (D-216 clauses 1 and 3): the tree API lists the jobs, the newest by its date is read, and
    every request carries the token; a later job needs no code change."""
    monkeypatch.setenv("HF_TOKEN", TOKEN)
    newer = "20261001-deep-swe-leaderboard-all-4x"
    listing = [*_listing(JOB, newer, "not-a-dated-job"),
               {"type": "file", "oid": "0" * 40, "size": 9, "path": "raw/jobs/20991231-a-file-not-a-job"}]
    routes = _hub(listing, job=newer)
    client = _dc().DatacurveClient(token_file=no_token_file)
    assert client.name == "datacurve_deepswe" and tuple(client.hosts) == ("huggingface.co",)
    rows, skipped = _parse(client.fetch_raw())
    assert (len(rows), skipped) == (27, 0)
    assert {row.source_url.rsplit("/", 1)[1] for row in rows} == {newer}
    for route in routes.values():
        assert route.call_count == 1
        assert route.calls.last.request.headers["authorization"] == f"Bearer {TOKEN}"


@respx.mock(assert_all_called=False)
def test_without_a_token_the_source_fails_loudly_and_asks_nothing_of_the_hub(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 3): no token is a failed source that says where the token goes."""
    from app.clients.protocols import SourceError

    monkeypatch.delenv("HF_TOKEN", raising=False)
    routes = _hub(_listing(JOB))
    with pytest.raises(SourceError, match="HF_TOKEN") as raised:
        _dc().DatacurveClient(token_file=no_token_file).fetch_raw()
    assert str(no_token_file) in str(raised.value)
    assert not any(route.called for route in routes.values())


@respx.mock(assert_all_called=False)
def test_the_owners_token_file_is_read_and_one_others_can_read_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 3): the file is the owner's alone (mode 600), as the owner made it."""
    from app.clients.protocols import SourceError

    monkeypatch.delenv("HF_TOKEN", raising=False)
    token_file = tmp_path / "hf-token"
    token_file.write_text(TOKEN + "\n", encoding="utf-8")
    routes = _hub(_listing(JOB))
    for loose in (0o644, 0o640, 0o604):
        token_file.chmod(loose)
        with pytest.raises(SourceError, match="chmod 600"):
            _dc().DatacurveClient(token_file=token_file).fetch_raw()
    assert not any(route.called for route in routes.values())
    token_file.chmod(0o600)
    _dc().DatacurveClient(token_file=token_file).fetch_raw()
    assert routes["result"].calls.last.request.headers["authorization"] == f"Bearer {TOKEN}"


@respx.mock(assert_all_called=False)
@pytest.mark.parametrize("bad", ["", "   \n", "two words", "line\nbreak", "x" * 400])
def test_a_token_that_is_not_one_is_refused_without_echoing_it(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path, bad: str,
) -> None:
    from app.clients.protocols import SourceError

    monkeypatch.setenv("HF_TOKEN", bad)
    routes = _hub(_listing(JOB))
    with pytest.raises(SourceError) as raised:
        _dc().DatacurveClient(token_file=no_token_file).fetch_raw()
    assert not any(route.called for route in routes.values())
    if bad.strip():
        assert bad not in str(raised.value)


@respx.mock(assert_all_called=False)
def test_a_refused_token_fails_the_source_and_the_message_never_holds_it(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 3): a 401 from the hub is a failed source; the token is never echoed."""
    from app.clients.protocols import SourceError

    monkeypatch.setenv("HF_TOKEN", TOKEN)
    respx.get(JOBS).mock(return_value=httpx.Response(200, json=_listing(JOB)))
    respx.get(f"{FILES}/{JOB}/result.json").mock(return_value=httpx.Response(401, text="Access to dataset is restricted"))
    with pytest.raises(SourceError) as raised:
        _dc().DatacurveClient(token_file=no_token_file).fetch_raw()
    assert TOKEN not in str(raised.value)


@respx.mock(assert_all_called=False)
def test_a_redirect_off_the_hub_is_refused_and_never_requested(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 3): the token goes to `huggingface.co` alone, redirects included."""
    from app.clients.protocols import SourceError

    monkeypatch.setenv("HF_TOKEN", TOKEN)
    respx.get(JOBS).mock(return_value=httpx.Response(200, json=_listing(JOB)))
    respx.get(f"{FILES}/{JOB}/result.json").mock(
        return_value=httpx.Response(302, headers={"location": "https://cdn.example.net/result.json"}))
    elsewhere = respx.get("https://cdn.example.net/result.json").mock(return_value=httpx.Response(200, text="{}"))
    with pytest.raises(SourceError, match="refused a hop"):
        _dc().DatacurveClient(token_file=no_token_file).fetch_raw()
    assert not elsewhere.called


@respx.mock(assert_all_called=False)
@pytest.mark.parametrize("listing", [_listing("not-a-dated-job"), {"error": "rate limited"}, []])
def test_a_listing_with_no_dated_job_fails_the_source(
    monkeypatch: pytest.MonkeyPatch, no_token_file: Path, listing: object,
) -> None:
    from app.clients.protocols import SourceError

    monkeypatch.setenv("HF_TOKEN", TOKEN)
    respx.get(JOBS).mock(return_value=httpx.Response(200, json=listing))
    with pytest.raises(SourceError):
        _dc().DatacurveClient(token_file=no_token_file).fetch_raw()


# --- the registry and the build's own ingest ----------------------------------------------------------------------

def test_the_source_is_declared_optional_and_its_floor_sits_below_the_recorded_board() -> None:
    """covers REQ-SRC-012 (D-216 clauses 1 and 4): one declaration, read by the build and the smoke gate; optional
    as every board fetched from Hugging Face is (D-121), so a missing token never fails another source's night."""
    from app.workflows import sources

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    assert declared.client is _dc().DatacurveClient and declared.required is False
    rows, _ = declared.parse(_envelope())
    assert 0 < declared.minimum_rows <= len(rows) // 2


def test_the_registered_ingest_stores_each_run_at_the_effort_a_reader_is_shown() -> None:
    """covers REQ-SRC-012: through the build's own path, the store keeps the parser's efforts."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    conn = connect()
    report = declared.ingest(conn, FakeRawSource("datacurve_deepswe", _envelope()), RunContext(observed_at="t"))
    assert (report.stored, report.skipped, report.effort_unknown) == (27, 0, 0)
    stored = dict(conn.execute("SELECT effort, count(*) FROM scores WHERE source = 'datacurve_deepswe' GROUP BY effort"))
    assert stored == {"high": 15, "xhigh": 5, "max": 3, "medium": 4}
