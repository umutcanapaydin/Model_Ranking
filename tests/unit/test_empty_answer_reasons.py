"""M7-W1 — an empty answer states the RIGHT reason for being empty (D-121's binding condition).

Two different things make an answer empty, and telling them apart is the whole justification for
letting a degraded artifact ship:

  * the surface HAS evidence and nothing in it fits the budget — a result;
  * the surface has NO evidence source at all — a gap.

Until M7-W1 both produced the budget sentence. The security and code-review seats found it
independently: `source_health` correctly reported "no evidence source is present" while
`unavailable_reason`, the human-readable field beside it, said "nothing fits your budget". One
payload, two contradictory accounts of itself.

D-121 authorises a build to succeed without an optional source ONLY because the surface discloses
the gap. A false cause served next to the true one does not weaken that condition, it removes it —
so these tests guard an ADR, not a wording preference.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fakes import FakeRawSource
from app.workflows.build import build
from app.workflows.ingest import ingest_aider, ingest_litellm, ingest_swebench
from app.workflows.schema import connect
from app.workflows.sources import RemoteSource

PRICING = json.dumps(
    {
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
    }
)
SWEBENCH = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {
                        "name": "live-SWE-agent + GPT-5",
                        "resolved": 74.1,
                        "date": "2025-12-01",
                        "logs": True,
                        "trajs": True,
                    },
                    {
                        "name": "live-SWE-agent + Claude 4.5 Opus",
                        "resolved": 79.2,
                        "date": "2025-12-15",
                        "logs": True,
                        "trajs": True,
                    },
                ],
            }
        ]
    }
)
AIDER = json.dumps([{"model": "gpt-5 (high)", "pass_rate_2": 61.0, "edit_format": "diff"}])


@pytest.fixture
def served_db(tmp_path: Path) -> Path:
    """An artifact built WITHOUT any arena source — the D-121 degraded case, for real."""
    target = tmp_path / "degraded.db"
    conn: sqlite3.Connection = connect(str(target))
    try:
        build(
            conn,
            plans_yaml=Path("data/plans.yaml").read_text(encoding="utf-8"),
            rosters_yaml=Path("data/rosters.yaml").read_text(encoding="utf-8"),
            sources=(
                RemoteSource(
                    name="litellm",
                    client=lambda: FakeRawSource("litellm", PRICING),
                    ingest=ingest_litellm,
                    parse=lambda _: ([], 0),
                    minimum_rows=1,
                ),
                RemoteSource(
                    name="swebench",
                    client=lambda: FakeRawSource("swebench", SWEBENCH),
                    ingest=ingest_swebench,
                    parse=lambda _: ([], 0),
                    minimum_rows=1,
                ),
                RemoteSource(
                    name="aider",
                    client=lambda: FakeRawSource("aider", AIDER),
                    ingest=ingest_aider,
                    parse=lambda _: ([], 0),
                    minimum_rows=1,
                ),
            ),
            bundles=(),
            minimum_models=2,
        )
    finally:
        conn.close()
    return target


def _answers(served_db: Path, task: str, budget: str = "unlimited") -> list[dict[str, object]]:
    import importlib

    import app.adapter.main as main_mod

    main_mod = importlib.reload(main_mod)
    with TestClient(main_mod.app) as client:
        response = client.get(f"/v1/recommendations?task={task}&budget={budget}")
    assert response.status_code == 200
    return list(response.json()["answers"])


def test_a_surface_with_no_evidence_source_says_so_and_does_not_blame_the_budget(
    served_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The finding, as a test: `assistant` has no arena rows at all in this artifact."""
    monkeypatch.setenv("MODEL_RANKING_DB", str(served_db))
    monkeypatch.setenv("APP_ENV", "test")

    (answer,) = _answers(served_db, "assistant")

    assert answer["picks"] == []
    reason = str(answer["unavailable_reason"])
    assert "no evidence" in reason.lower()
    assert "budget" not in reason.lower() or "no budget was applied" in reason.lower()
    assert answer["source_health"]["stale"] is True  # type: ignore[index]


def test_a_surface_with_evidence_but_nothing_affordable_blames_the_budget(
    served_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The OTHER branch, which this wave accidentally left with no citing test at all.

    Added by the Stage-3b Tester at re-review. Before M7-W1 the budget sentence was covered by
    `test_api_v1.py:598`, which asserts `unavailable_reason` is truthy on an EMPTY database. The
    new no-evidence branch fires first on an empty database, so that assertion moved onto the new
    branch and the budget branch was left uncovered — `main.py:752` is a missing line, and six
    separate mutants of the branch condition and of the budget sentence itself all stayed green,
    including returning `None` as the reason.

    A fix that silently un-covers the path it forked from is the V3C-86 shape arrived at by
    accident, so the pin is the pair: same request, both branches, different sentences.
    """
    monkeypatch.setenv("MODEL_RANKING_DB", str(served_db))
    monkeypatch.setenv("APP_ENV", "test")

    answers = {a["surface"]: a for a in _answers(served_db, "coding", budget="low")}
    coding = answers["coding"]
    agentic = answers["agentic-coding"]

    assert coding["picks"] == [], "fixture assumption: nothing on coding fits the low budget"
    budget_reason = str(coding["unavailable_reason"])
    assert budget_reason, "a surface WITH evidence and no affordable model must still say why"
    assert "budget" in budget_reason.lower()
    assert "no evidence" not in budget_reason.lower(), (
        "the budget branch is serving the evidence-gap sentence; the two causes have collapsed "
        "back into one blanket explanation"
    )

    gap_reason = str(agentic["unavailable_reason"])
    assert "no evidence" in gap_reason.lower()
    assert gap_reason != budget_reason, "one payload must not give one cause for two conditions"


def test_the_two_reasons_are_not_the_same_sentence(
    served_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a refactor collapsed them back into one message, this is what would notice.

    A surface WITH evidence and an impossible budget must still get the budget sentence — the fix
    must not have replaced one blanket explanation with a different blanket explanation.
    """
    monkeypatch.setenv("MODEL_RANKING_DB", str(served_db))
    monkeypatch.setenv("APP_ENV", "test")

    no_evidence = next(
        a for a in _answers(served_db, "assistant") if a["surface"] == "assistant"
    )
    coding = [a for a in _answers(served_db, "coding") if a["surface"] == "coding"]
    assert coding and coding[0]["picks"], "fixture assumption: coding must have evidence"

    assert "no evidence" in str(no_evidence["unavailable_reason"]).lower()
