"""Terminal-Bench 4.0 from its Apache-2.0 leaderboard repository (#265, D-194) — cite REQ-SRC-012.

`computer-use` ranked on Epoch's copy of Terminal-Bench 2.0, whose leaderboard states no licence. TB 4.0's
official leaderboard is defined and kept in `harbor-framework/terminal-bench` (Apache-2.0), one JSON
file a submission under `leaderboard/submissions/`. The fixture is three of them, recorded on 2026-10-13
and trimmed to the fields read.
"""

from __future__ import annotations

import importlib
import json

import httpx
import pytest
import respx

LISTING = "https://api.github.com/repos/harbor-framework/terminal-bench/contents/leaderboard/submissions"
RAW = "https://raw.githubusercontent.com/harbor-framework/terminal-bench/main/leaderboard/submissions/"


def _submission(model: str, agent: str, effort: str | None, shown: str, accuracy: object, date: str,
                cost: float) -> dict[str, object]:
    return {
        "source_filter": {"agent": agent, "model_name": model, "reasoning_effort": effort},
        "metadata": {"date": date, "reasoning_effort": shown, "model_display": {"label": model}},
        "metrics": {"accuracy": accuracy, "accuracy_ci95_half_width": 3.5, "n_trials": 330, "total_cost_usd": cost},
        "disqualified_trials": [],
    }


OPUS = _submission("anthropic/claude-opus-5-5", "claude-code", "max", "max", 64.85, "2026-09-22", 6620.5)
GLM = _submission("z-ai/glm-5.3-flash", "claude-code", None, "none", 35.76, "2026-08-26", 2883.11)
FLASH = _submission("gemini/gemini-3.8-flash", "mini-swe-agent", "high", "high", 19.09, "2026-09-02", 412.0)
FILES = {
    "2026-09-30-anthropic-claude-opus-5-5-max-claude-code.json": OPUS,
    "2026-10-06-z-ai-glm-5-3-flash-none-claude-code.json": GLM,
    "2026-09-01-gemini-gemini-3-8-flash-high-mini-swe-agent.json": FLASH,
}


def _raw(files: dict[str, object]) -> str:
    return json.dumps([{"file": name, "body": json.dumps(body)} for name, body in files.items()])


def _tb():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.terminalbench")


def test_each_submission_is_a_row_at_its_accuracy_agent_effort_and_date() -> None:
    """covers REQ-SRC-012: the accuracy is TB 4.0's percentage; the agent is the harness; the run's
    effort is the submission's, and `none` or no effort is stored as unspecified."""
    rows, skipped = _tb().parse_terminalbench_4(_raw(FILES), source="terminalbench_4", source_url=LISTING)
    assert skipped == 0
    by_name = {r.raw_name: r for r in rows}
    opus = by_name["anthropic/claude-opus-5-5"]
    assert (opus.score, opus.harness, opus.effort, opus.run_date, opus.cost_total) == (
        64.85, "claude-code", "max", "2026-09-22", 6620.5)
    assert (opus.benchmark, opus.metric, opus.source) == ("Terminal-Bench 4.0", "% resolved", "terminalbench_4")
    assert by_name["z-ai/glm-5.3-flash"].effort is None
    assert by_name["gemini/gemini-3.8-flash"].effort == "high"


@pytest.mark.parametrize("accuracy", [101.0, -1.0, float("nan"), "64.85", None, True])
def test_a_submission_without_a_usable_accuracy_is_skipped_and_counted(accuracy: object) -> None:
    """covers REQ-SRC-012: a score outside 0..100, not a number, or missing is never stored."""
    bad = _submission("openai/gpt-6-sol", "codex", "max", "max", accuracy, "2026-09-22", 1.0)
    rows, skipped = _tb().parse_terminalbench_4(_raw({"bad.json": bad, "ok.json": OPUS}),
                                                source="terminalbench_4", source_url=LISTING)
    assert [r.raw_name for r in rows] == ["anthropic/claude-opus-5-5"]
    assert skipped == 1


def test_a_body_that_is_not_a_submission_is_skipped_and_an_envelope_that_is_not_a_list_is_refused() -> None:
    """covers REQ-SRC-012: one broken file costs its row; a broken payload fails the source."""
    from app.clients.protocols import SourceError

    raw = json.dumps([{"file": "a.json", "body": "not json"}, {"file": "b.json", "body": "[]"},
                      {"file": "c.json", "body": json.dumps(OPUS)}, "not-an-entry"])
    rows, skipped = _tb().parse_terminalbench_4(raw, source="terminalbench_4", source_url=LISTING)
    assert [r.raw_name for r in rows] == ["anthropic/claude-opus-5-5"] and skipped == 3
    for envelope in ("{}", "null", "not json"):
        with pytest.raises(SourceError):
            _tb().parse_terminalbench_4(envelope, source="terminalbench_4", source_url=LISTING)


def test_two_runs_of_one_model_agent_and_effort_keep_the_better() -> None:
    """covers REQ-SRC-012: the scores table holds one row per model, agent and effort."""
    again = _submission("anthropic/claude-opus-5-5", "claude-code", "max", "max", 60.0, "2026-09-30", 1.0)
    rows, skipped = _tb().parse_terminalbench_4(_raw({"a.json": again, "b.json": OPUS}),
                                                source="terminalbench_4", source_url=LISTING)
    assert [(r.raw_name, r.score) for r in rows] == [("anthropic/claude-opus-5-5", 64.85)] and skipped == 1


@respx.mock
def test_the_client_reads_every_submission_file_the_listing_names_from_the_repository() -> None:
    """covers REQ-SRC-012: GitHub's contents API lists the files; each is read from the repository's own
    raw path, and a listing entry that points anywhere else is refused, never fetched."""
    listing = [{"name": name, "type": "file", "download_url": RAW + name} for name in FILES]
    listing.append({"name": "README.md", "type": "file", "download_url": RAW + "README.md"})
    respx.get(LISTING).mock(return_value=httpx.Response(200, json=listing))
    for name, body in FILES.items():
        respx.get(RAW + name).mock(return_value=httpx.Response(200, json=body))
    client = _tb().TerminalBench4Client()
    assert set(client.hosts) == {"api.github.com", "raw.githubusercontent.com"}
    raw = client.fetch_raw()
    assert sorted(entry["file"] for entry in json.loads(raw)) == sorted(FILES)
    rows, _ = _tb().parse_terminalbench_4(raw, source=client.name, source_url=client.url)
    assert len(rows) == 3

    elsewhere = [{"name": "x.json", "type": "file", "download_url": "https://raw.githubusercontent.com/someone/else/main/x.json"}]
    respx.get(LISTING).mock(return_value=httpx.Response(200, json=elsewhere))
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError, match="outside"):
        client.fetch_raw()


def test_computer_use_ranks_on_terminal_bench_4_and_epochs_copy_of_2_0_is_gone() -> None:
    """covers REQ-SRC-012 (D-194 clause 2): the surface, its family and the source list."""
    from app.workflows import board_tables, categories, families, sources

    spec = categories.CATEGORIES["computer-use"]
    assert (spec.primary_source, spec.primary_benchmark) == ("terminalbench_4", "Terminal-Bench 4.0")
    # #379 (D-219 clause 3): OSWorld-Verified stands beside it; the primary stays.
    assert families.FAMILIES["computer-use"] == ("terminalbench_4", "osworld_verified", "arena_agent")
    assert "terminalbench_4" in families.FAMILIES["agentic-coding"]
    assert "terminalbench_4" in {s.name for s in sources.REMOTE_SOURCES}
    assert "epoch_terminalbench" not in {b.source_name for b in board_tables.EPOCH_BOARDS}
    assert all("epoch_terminalbench" not in family for family in families.FAMILIES.values())


def test_terminal_bench_is_credited_under_apache_2_0_with_its_repository() -> None:
    """covers REQ-SRC-012 (D-194 clause 5): the citation and the Credits screen name the licence."""
    from app.workflows import board_tables, rank

    citation = rank.SOURCE_ATTRIBUTION["terminalbench_4"]
    assert "Apache-2.0" in citation and "github.com/harbor-framework/terminal-bench" in citation
    assert citation in rank.ATTRIBUTIONS
    credit = board_tables.CREDITS["terminal_bench"]
    assert (credit.licence, credit.url, credit.licence_url) == (
        "Apache-2.0", "https://github.com/harbor-framework/terminal-bench",
        "https://github.com/harbor-framework/terminal-bench/blob/main/LICENSE")
    assert [c["id"] for c in rank.credits_for([citation])] == ["terminal_bench"]


# --- The #265 review (docs/reviews/issue-265-licensed-sources-review.md) ------------------------------------

@respx.mock
@pytest.mark.parametrize("link", [
    RAW + "../../../../evil/repo/main/x.json",
    "https://raw.githubusercontent.com/harbor-framework/terminal-bench/main/leaderboard/other/x.json",
    "https://raw.githubusercontent.com/harbor-framework/terminal-bench-x/main/leaderboard/submissions/x.json",
    # #326: the check read the decoded path, so an encoded `..` as the ref passed it and was sent raw.
    "https://raw.githubusercontent.com/harbor-framework/terminal-bench/%2e%2e/leaderboard/submissions/x.json",
    "https://raw.githubusercontent.com/harbor-framework/terminal-bench/%2E%2E/leaderboard/submissions/x.json",
])
def test_a_listed_file_whose_path_leaves_the_submissions_directory_is_refused(link: str) -> None:
    """The review's M2: httpx removes dot segments before the request, so a prefix test let `..` out."""
    from app.clients.protocols import SourceError

    respx.get(LISTING).mock(return_value=httpx.Response(200, json=[{"name": "x.json", "type": "file", "download_url": link}]))
    with pytest.raises(SourceError, match="outside"):
        _tb().TerminalBench4Client().fetch_raw()


@respx.mock
def test_only_json_files_are_read_and_a_listing_that_is_not_a_list_or_too_long_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The review's M3: the file filter, the list check and the count cap each had no test."""
    from app.clients.protocols import SourceError

    name = next(iter(FILES))
    listing = [{"name": name, "type": "file", "download_url": RAW + name},
               {"name": "nested.json", "type": "dir", "download_url": None},  # round 2's N2
               {"name": "notes.txt", "type": "file", "download_url": RAW + "notes.txt"}]
    respx.get(LISTING).mock(return_value=httpx.Response(200, json=listing))
    respx.get(RAW + name).mock(return_value=httpx.Response(200, json=FILES[name]))
    assert [e["file"] for e in json.loads(_tb().TerminalBench4Client().fetch_raw())] == [name]
    monkeypatch.setattr(_tb(), "MAX_SUBMISSIONS", 0)
    with pytest.raises(SourceError, match="more than"):
        _tb().TerminalBench4Client().fetch_raw()
    respx.get(LISTING).mock(return_value=httpx.Response(200, json={"message": "API rate limit exceeded"}))
    with pytest.raises(SourceError, match="not a list"):
        _tb().TerminalBench4Client().fetch_raw()


def test_an_effort_the_schema_does_not_hold_skips_the_row_and_not_the_source() -> None:
    """The review's M3: an unknown effort reaching the store would fail the whole source there."""
    odd = _submission("openai/gpt-6-sol", "codex", "ultra", "ultra", 49.39, "2026-09-22", 1.0)
    rows, skipped = _tb().parse_terminalbench_4(_raw({"odd.json": odd, "ok.json": OPUS}),
                                                source="terminalbench_4", source_url=LISTING)
    assert [r.raw_name for r in rows] == ["anthropic/claude-opus-5-5"] and skipped == 1


def test_one_model_run_at_two_efforts_is_two_rows() -> None:
    """The #265 Tester's M4: the table holds a row per model, agent AND effort; dropping effort from the key
    collapsed them."""
    high = _submission("anthropic/claude-opus-5-5", "claude-code", "high", "high", 58.0, "2026-09-22", 1.0)
    rows, skipped = _tb().parse_terminalbench_4(_raw({"a.json": high, "b.json": OPUS}),
                                                source="terminalbench_4", source_url=LISTING)
    assert sorted((r.effort, r.score) for r in rows) == [("high", 58.0), ("max", 64.85)] and skipped == 0
