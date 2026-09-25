"""#38 -- an effort written in parentheses is read as the same effort written with an underscore.

The Agent Arena boards (M17-W3) spell a run's effort `GPT 6 Astra (Max)`, where Epoch writes
`gpt-6-astra_max`; Aider and SWE-bench write `gpt-5 (high)`. Measured on the 2026-09-25 candidate:
nine names per agent board linked to nothing, and curated names such as `Claude Opus 5 (Max)` linked
to their model with the effort lost (`unspecified`), beside `Claude Opus 5 (High)` on the same board.

Only a TRAILING parenthesis holding one of the schema's effort levels is an effort. `(no thinking)`,
`(default)`, `(May 2024)` and a date stay part of the name, as they always were.
"""

from __future__ import annotations

import pytest

from app.workflows.ingest import RunContext, _store_scores
from app.workflows.registry import derive_identity, reconcile, resolve_effort
from app.workflows.schema import ScoreRow, connect


@pytest.mark.parametrize(("name", "model_id", "effort"), [
    ("GPT 6 Astra (Max)", "gpt6-astra", "max"),
    ("Grok 4.7 (xHigh)", "grok4.7", "xhigh"),
    ("Gemini 3.8 Flash (High)", "gemini3.8-flash", "high"),
    ("Kimi K3 (max)", "kimi-k3", "max"),
])
def test_a_derived_name_reads_its_parenthesised_effort(name: str, model_id: str, effort: str) -> None:
    identity = derive_identity(name)
    assert identity is not None
    assert (identity.model_id, identity.effort) == (model_id, effort)


@pytest.mark.parametrize(("name", "model_name", "effort"), [
    ("Claude Opus 5 (Max)", "Claude Opus 5", "max"),
    ("Claude Opus 5 (High)", "Claude Opus 5", "high"),
    ("gpt-5 (low)", "gpt-5", "low"),
])
def test_a_curated_name_reads_its_parenthesised_effort(name: str, model_name: str, effort: str) -> None:
    resolution = resolve_effort(name)
    assert (resolution.model_name, resolution.effort) == (model_name, effort)


@pytest.mark.parametrize("name", [
    "claude-sonnet-4-20250514 (no thinking)", "gemini-2.5-flash-preview-04-17 (default)",
    "GPT-4o (May 2024)", "Claude 4.5 Sonnet (20250929)", "DeepSeek V4 Pro (High) (0813)",
    "mimo-v2-flash (thinking)",
])
def test_a_parenthesis_that_is_not_a_trailing_effort_stays_part_of_the_name(name: str) -> None:
    assert resolve_effort(name).effort is None
    identity = derive_identity(name)
    assert identity is None or identity.effort is None


def _score(raw: str) -> ScoreRow:
    return ScoreRow(raw_name=raw, benchmark="b", metric="ips", score=0.1, harness="h", run_date=None,
                    cost_total=None, source="arena_agent", source_url="u")


def test_the_stored_row_carries_the_effort_and_links_to_the_model_without_it() -> None:
    """Through ingest and reconcile, as the build runs them: both spellings of one run land on one
    model at one effort, and the served name never carries `(Max)`."""
    conn = connect(":memory:")
    try:
        _store_scores(conn, "arena_agent", [_score("GPT 6 Astra (Max)"), _score("Claude Opus 5 (High)")],
                      RunContext())
        conn.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                     "source_url, observed_at) VALUES ('gpt-6-astra_high', 'e', '%', 50, 'h', 'unspecified', "
                     "'epoch_eci', 'u', 'z')")
        conn.execute("INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, observed_at) "
                     "VALUES ('openai/gpt-6-astra', 1, 2, 'p', 'u', 'z')")
        reconcile(conn)
        rows = dict(((r[0]), (r[1], r[2])) for r in conn.execute(
            "SELECT raw_name, model_id, effort FROM scores"))
        assert rows["GPT 6 Astra (Max)"] == ("gpt6-astra", "max")
        assert rows["gpt-6-astra_high"] == ("gpt6-astra", "high")
        assert rows["Claude Opus 5 (High)"] == ("claude-5-opus", "high")
        display = conn.execute("SELECT display FROM models WHERE id = 'gpt6-astra'").fetchone()[0]
        assert "(" not in display
    finally:
        conn.close()
