"""`scripts/calibrate_board.py` counts and pairs MODELS, not board names (W-113).

The script counted 64 rankable entries on `vision` where the engine ranks 41 models, and paired a
model with its own dated snapshot when it measured `close_call` -- which moved two shipped tie
margins (vision 8.1 -> 7.8, search_factuality 4.2 -> 4.9). The fetch needs the network, so this
pins the step that decides the population, and then runs `main()` itself on a patched fetch --
the W4 seat put the old pairing back into `main()` and the helper-only test stayed green.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "calibrate_board.py"


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("calibrate_board", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_model_on_the_board_under_three_names_is_one_model_at_its_best_score() -> None:
    script = _script()
    model_of = {
        "gpt-4o-2024-05-13": "GPT-4o",
        "gpt-4o-2024-08-06": "GPT-4o",
        "chatgpt-4o-latest": "GPT-4o",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
    }
    by_name = {
        "gpt-4o-2024-05-13": 1200.0,
        "gpt-4o-2024-08-06": 1210.0,
        "chatgpt-4o-latest": 1195.0,
        "gemini-2.5-flash": 1205.0,
    }

    best = script.one_name_per_model(model_of, by_name)

    assert best == {"GPT-4o": "gpt-4o-2024-08-06", "Gemini 2.5 Flash": "gemini-2.5-flash"}


def test_a_model_is_never_paired_with_its_own_snapshot() -> None:
    script = _script()
    model_of = {"a-v1": "A", "a-v2": "A", "b": "B"}
    by_name = {"a-v1": 1200.0, "a-v2": 1201.0, "b": 1230.0}
    intervals = {"a-v1": (1190.0, 1210.0), "a-v2": (1191.0, 1211.0), "b": (1205.0, 1255.0)}

    names = list(script.one_name_per_model(model_of, by_name).values())
    gaps = script._overlapping_gaps(names, by_name, intervals)

    # Only A (at 1201) against B: the 1.0 gap between A's two names is not a pair of models.
    assert gaps == [29.0]


def test_main_counts_models_and_pairs_models_on_a_board_with_two_names_for_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`main()`, end to end, on a board where one model appears under two names (W4 review MAJOR-3).

    Three priced models, four board names: `claude-opus-4-5` and its `-thinking` variant are one
    model. Counting names says 4 and pairs the model with itself; counting models says 3, and only
    one pair of MODELS still overlaps at its published interval.
    """
    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_litellm
    from app.workflows.rank import build_price_medians
    from app.workflows.registry import reconcile
    from app.workflows.schema import connect

    from .test_api_v1 import PRICING

    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), RunContext(observed_at="2026-09-22T00:00:00Z"))
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()

    def row(name: str, rating: float, half: float) -> dict[str, object]:
        return {"row": {"model_name": name, "rating": rating, "rating_lower": rating - half,
                        "rating_upper": rating + half, "category": "overall",
                        "leaderboard_publish_date": "2026-09-13"}}

    board = json.dumps({"rows": [
        row("claude-opus-4-5", 1300.0, 10.0),
        row("claude-opus-4-5-thinking", 1301.0, 10.0),
        row("gpt-5", 1320.0, 15.0),
        row("deepseek-v3.2", 1250.0, 10.0),
    ]})
    script = _script()
    monkeypatch.setattr(script.ArenaClient, "fetch_raw", lambda self: board)
    out = tmp_path / "record.json"

    assert script.main(["--config", "vision", "--db", str(db), "--out", str(out)]) == 0

    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["ranked_population"] == 3, record
    assert record["rankable_board_names"] == 4, record
    # Only opus (at its best name, 1301) against gpt-5 overlaps; the name-pairing counted three.
    assert record["overlapping_pairs"] == 1, record
