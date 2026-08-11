"""End-to-end test through the REAL entry point (V4C-50; REQ-REC-001).

Builds a real SQLite file from fixture sources, then invokes the CLI exactly
as a user would: ``python -m app.workflows.recommend --db … --budget …``.
Network-free (fixtures); NOT env-gated — this is a load-bearing path.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parents[2] / "src"


def _build_db(tmp_path: Path) -> Path:
    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_litellm, ingest_swebench
    from app.workflows.registry import reconcile

    pricing = json.dumps(
        {
            "claude-4-5-opus": {
                "mode": "chat",
                "input_cost_per_token": 5e-06,
                "output_cost_per_token": 2.5e-05,
            },
            "deepseek-v3.2": {
                "mode": "chat",
                "input_cost_per_token": 2.8e-07,
                "output_cost_per_token": 4.1e-07,
            },
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {
                            "name": "live-SWE-agent + Claude 4.5 Opus",
                            "resolved": 79.2,
                            "date": "2025-12-15",
                        },
                        {
                            "name": "mini-SWE-agent + DeepSeek V3.2",
                            "resolved": 70.0,
                            "date": "2026-02-17",
                        },
                    ],
                }
            ]
        }
    )
    db_path = tmp_path / "advisor.db"
    conn = sqlite3.connect(db_path)
    from app.workflows.schema import DDL

    conn.executescript(DDL)
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    conn.commit()
    conn.close()
    return db_path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    prior = os.environ.get("PYTHONPATH")
    pythonpath = str(SRC_DIR) if not prior else f"{SRC_DIR}{os.pathsep}{prior}"
    env = {**os.environ, "PYTHONPATH": pythonpath}
    return subprocess.run(
        [sys.executable, "-m", "app.workflows.recommend", *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=env,
    )


def test_cli_end_to_end_three_picks(tmp_path: Path) -> None:
    """V4C-50: the REAL entry point returns three valid picks as JSON."""
    db = _build_db(tmp_path)
    proc = _run_cli("--db", str(db), "--budget", "sinirsiz")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert [p["label"] for p in payload["picks"]] == ["best_quality", "best_value", "budget_pick"]
    assert payload["picks"][0]["model"] == "Claude 4.5 Opus"
    assert payload["task"] == "coding"


def test_cli_budget_filters_through_entry_point(tmp_path: Path) -> None:
    db = _build_db(tmp_path)
    proc = _run_cli("--db", str(db), "--budget", "dusuk")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert all(p["blended_per_m"] <= 2.0 for p in payload["picks"])


def test_cli_missing_db_exits_2(tmp_path: Path) -> None:
    proc = _run_cli("--db", str(tmp_path / "nope.db"), "--budget", "orta")
    assert proc.returncode == 2
    assert "not found" in json.loads(proc.stdout)["error"]


def test_cli_task_assistant_through_entry_point(tmp_path: Path) -> None:
    """REQ-REC-005 (V4C-50): --task assistant works through the REAL entry point."""
    db_path = tmp_path / "advisor.db"
    conn = sqlite3.connect(db_path)
    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_arena, ingest_litellm
    from app.workflows.registry import reconcile
    from app.workflows.schema import DDL

    conn.executescript(DDL)
    run = RunContext(observed_at="2026-08-11T00:00:00+00:00")
    ingest_litellm(
        conn,
        FakeRawSource(
            "litellm",
            json.dumps(
                {
                    "gpt-5-chat": {
                        "mode": "chat",
                        "input_cost_per_token": 1.25e-06,
                        "output_cost_per_token": 1e-05,
                    },
                    "gemini-3-flash": {
                        "mode": "chat",
                        "input_cost_per_token": 5e-07,
                        "output_cost_per_token": 3e-06,
                    },
                }
            ),
        ),
        run,
    )
    arena = json.dumps(
        {
            "rows": [
                {
                    "row": {
                        "model_name": "gpt-5-chat",
                        "rating": 1420.0,
                        "category": "full",
                        "leaderboard_publish_date": "2026-08-01",
                    }
                },
                {
                    "row": {
                        "model_name": "gemini-3-flash",
                        "rating": 1398.0,
                        "category": "full",
                        "leaderboard_publish_date": "2026-08-01",
                    }
                },
            ],
            "num_rows_total": 2,
        }
    )
    ingest_arena(conn, FakeRawSource("arena", arena), run)
    reconcile(conn)
    conn.commit()
    conn.close()

    proc = _run_cli("--db", str(db_path), "--budget", "sinirsiz", "--task", "assistant")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["task"] == "assistant"
    assert payload["picks"][0]["metric"] == "elo"
    assert payload["picks"][0]["model"] == "GPT-5 chat"


def test_cli_invalid_task_rejected(tmp_path: Path) -> None:
    proc = _run_cli("--db", str(tmp_path / "x.db"), "--task", "resim")
    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr


def test_cli_corrupt_db_exits_2(tmp_path: Path) -> None:
    """W4 review MINOR-1: a DB without tables is a crash-class error (2), not 'no match' (1)."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_bytes(b"")  # exists, but has no schema
    proc = _run_cli("--db", str(db_path), "--budget", "orta")
    assert proc.returncode == 2
    assert "db unusable" in json.loads(proc.stdout)["error"]


def test_cli_invalid_budget_rejected_by_argparse(tmp_path: Path) -> None:
    proc = _run_cli("--db", str(tmp_path / "x.db"), "--budget", "bedava")
    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr


def test_cli_no_eligible_model_exits_1(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(db_path)
    from app.workflows.schema import DDL

    conn.executescript(DDL)
    conn.commit()
    conn.close()
    proc = _run_cli("--db", str(db_path), "--budget", "dusuk")
    assert proc.returncode == 1
    assert "no eligible model" in json.loads(proc.stdout)["error"]
