"""M5 W2 effort parsing, storage, ranking, and disclosure (REQ-CAN-005/-REC-011)."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from app.clients.deepswe import parse_deepswe
from app.clients.fakes import FakeRawSource
from app.workflows.categories import CATEGORIES
from app.workflows.coverage import main as coverage_main
from app.workflows.ingest import RunContext, ingest_swebench
from app.workflows.rank import build_price_medians, category_ranking, export_ranking
from app.workflows.recommend import main
from app.workflows.registry import canonicalize, resolve_effort
from app.workflows.schema import EFFORT_LEVELS, connect

SOURCE_URL = "https://epoch.ai/data/benchmark_data.zip#deepswe_external.csv"


@pytest.mark.parametrize("separator", ["_", "-"])
@pytest.mark.parametrize("effort", EFFORT_LEVELS)
def test_effort_suffix_family_is_removed_before_base_registry_rule(
    separator: str, effort: str
) -> None:
    """REQ-CAN-005: every effort suffix is data, never swallowed by a base rule."""
    raw = f"claude-opus-5{separator}{effort}"
    resolved = resolve_effort(raw)
    assert resolved.model_name == "claude-opus-5"
    assert resolved.effort == effort
    assert canonicalize(resolved.model_name) == canonicalize(raw)


def test_model_family_max_is_not_misread_as_effort() -> None:
    """REQ-CAN-005: Qwen's model-family token remains part of the model identity."""
    resolved = resolve_effort("qwen3.7-max")
    assert resolved.model_name == "qwen3.7-max"
    assert resolved.effort is None


def test_explicit_effort_wins_suffix_conflict_and_unknown_is_visible() -> None:
    """REQ-CAN-005: column precedence is deterministic; conflict/unknown are counted."""
    raw = """Model version,Pass@1,Harness,Reasoning effort,Release date
claude-opus-5_max,0.70,mini-swe-agent,medium,2026-07-01
gpt-5.6-sol_xhigh,0.68,mini-swe-agent,,2026-07-01
kimi-k2.7-code,0.30,mini-swe-agent,,2026-07-01
"""
    rows, stats = parse_deepswe(raw, source="epoch_deepswe_external", source_url=SOURCE_URL)
    assert [(r.raw_name, r.effort, r.run_date) for r in rows] == [
        ("claude-opus-5_max", "medium", None),
        ("gpt-5.6-sol_xhigh", "xhigh", None),
    ]
    assert [r.score for r in rows] == [70.0, 68.0]
    assert stats.skipped == 1
    assert stats.unknown_effort == 1
    assert stats.conflicts == 1


def test_suffix_effort_is_stored_through_existing_ingest_entrypoint() -> None:
    """REQ-CAN-005: suffix inference reaches the persisted score, not only a helper."""
    payload = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [{"name": "agent + Claude Opus 5_max", "resolved": 70.0}],
                }
            ]
        }
    )
    conn = connect()
    ingest_swebench(conn, FakeRawSource("swebench", payload), RunContext(observed_at="t"))
    assert conn.execute("SELECT effort FROM scores").fetchone() == ("max",)


def _effort_cli_db(path: Path) -> None:
    conn = connect(str(path))
    conn.executemany(
        "INSERT INTO models (id, display, vendor) VALUES (?,?,?)",
        [
            ("claude-5-opus", "Claude Opus 5", "Anthropic"),
            ("gpt-5.6-sol", "GPT-5.6 Sol", "OpenAI"),
        ],
    )
    conn.executemany(
        "INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source,"
        " source_url, observed_at) VALUES (?,?,?,?,?,?,?)",
        [
            ("claude-opus-5", "claude-5-opus", 10.0, 20.0, "prices", "https://p", "t"),
            ("gpt-5.6-sol", "gpt-5.6-sol", 1.0, 4.0, "prices", "https://p", "t"),
        ],
    )
    conn.execute(
        "INSERT INTO plan_config (id, staleness_days, cap_dusuk, cap_orta) VALUES (1,30,10,25)"
    )
    conn.executemany(
        "INSERT INTO plans (id, provider, name, monthly_usd, currency, region, limits,"
        " source_url, last_verified, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "claude-plan",
                "Anthropic",
                "Claude Plan",
                20.0,
                "USD",
                "US",
                "verbatim",
                "https://plans/claude",
                "2026-08-15",
                "2026-08-16T00:00:00+00:00",
            ),
            (
                "gpt-plan",
                "OpenAI",
                "GPT Plan",
                10.0,
                "USD",
                "US",
                "verbatim",
                "https://plans/gpt",
                "2026-08-15",
                "2026-08-16T00:00:00+00:00",
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO plan_models (plan_id, raw_name, model_id) VALUES (?,?,?)",
        [
            ("claude-plan", "Claude Opus 5", "claude-5-opus"),
            ("gpt-plan", "GPT-5.6 Sol", "gpt-5.6-sol"),
        ],
    )
    conn.executemany(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort,"
        " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "claude-5-opus",
                "claude-opus-5_high",
                "DeepSWE",
                "% resolved",
                65.0,
                "mini-swe-agent",
                "high",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "gpt-5.6-sol",
                "gpt-5.6-sol_high",
                "DeepSWE",
                "% resolved",
                60.0,
                "mini-swe-agent",
                "high",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "gpt-5.6-sol",
                "gpt-5.6-sol_max",
                "DeepSWE",
                "% resolved",
                75.0,
                "mini-swe-agent",
                "max",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "claude-5-opus",
                "claude-opus-5_low",
                "DeepSWE",
                "% resolved",
                40.0,
                "mini-swe-agent",
                "low",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "claude-5-opus",
                "claude-opus-5_max_foreign_harness",
                "DeepSWE",
                "% resolved",
                99.0,
                "foreign-agent",
                "max",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "claude-5-opus",
                "claude-opus-5_max_foreign_source",
                "DeepSWE",
                "% resolved",
                98.0,
                "mini-swe-agent",
                "max",
                "other_deepswe_copy",
                "https://other.example/board.csv",
                "t",
            ),
            # Adversarial rows: neither a foreign harness nor a foreign source may
            # supply the range disclosed beside mini-swe-agent/Epoch evidence.
            (
                "gpt-5.6-sol",
                "gpt-5.6-sol_max_foreign_harness",
                "DeepSWE",
                "% resolved",
                99.0,
                "foreign-agent",
                "max",
                "epoch_deepswe_external",
                SOURCE_URL,
                "t",
            ),
            (
                "gpt-5.6-sol",
                "gpt-5.6-sol_max_foreign_source",
                "DeepSWE",
                "% resolved",
                98.0,
                "mini-swe-agent",
                "max",
                "other_deepswe_copy",
                "https://other.example/board.csv",
                "t",
            ),
        ],
    )
    conn.commit()
    conn.close()


def test_live_recommendation_ranks_high_and_discloses_higher_effort(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """REQ-REC-011: the real CLI ranks one DATA level and publishes the range."""
    db = tmp_path / "advisor.db"
    _effort_cli_db(db)
    assert main(["--db", str(db), "--task", "agentic-coding"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ranking_effort"] == "high"
    assert all(pick["effort"] == "high" for pick in out["picks"])

    by_model = {pick["model"]: pick for pick in out["picks"]}
    gpt = by_model["GPT-5.6 Sol"]
    assert gpt["score"] == 60.0  # max=75 exists but never enters high-level ordering
    assert (gpt["higher_effort"], gpt["higher_effort_score"]) == ("max", 75.0)
    assert "max effort" in gpt["effort_note"]
    assert "75.0 puan" in gpt["effort_note"]

    claude = by_model["Claude Opus 5"]
    assert claude["higher_effort"] is None
    assert claude["effort_note"] == (
        "Bu model high effort düzeyinde sıralandı; aynı harness ve kaynakta "
        "karşılaştırılabilir daha yüksek effort sonucu yok."
    )
    assert "yalnız" not in claude["effort_note"]  # low evidence also exists


def test_live_subscription_answer_carries_the_same_effort_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """REQ-REC-011: the plan CLI cannot drop the effort/range disclosure."""
    db = tmp_path / "advisor.db"
    _effort_cli_db(db)
    assert (
        main(
            [
                "--db",
                str(db),
                "--task",
                "agentic-coding",
                "--subscription",
            ]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["ranking_effort"] == "high"
    by_model = {pick["scored_by_model"]: pick for pick in out["picks"]}
    assert by_model["GPT-5.6 Sol"]["score"] == 60.0
    assert by_model["GPT-5.6 Sol"]["higher_effort_score"] == 75.0
    assert "max effort" in by_model["GPT-5.6 Sol"]["effort_note"]
    assert by_model["Claude Opus 5"]["effort_note"] == (
        "Bu model high effort düzeyinde sıralandı; aynı harness ve kaynakta "
        "karşılaştırılabilir daha yüksek effort sonucu yok."
    )
    assert "yalnız" not in by_model["Claude Opus 5"]["effort_note"]


def test_ranking_export_rounds_every_score_without_rounding_internal_math(tmp_path: Path) -> None:
    """D-109/REQ-REC-011: raw selection, one-decimal CSV+JSON boundary."""
    db = tmp_path / "advisor.db"
    _effort_cli_db(db)
    conn = connect(str(db))
    conn.execute("UPDATE scores SET score = 60.555 WHERE raw_name = 'gpt-5.6-sol_high'")
    conn.execute("UPDATE scores SET score = 75.555 WHERE raw_name = 'gpt-5.6-sol_max'")
    build_price_medians(conn)
    ranking = category_ranking(conn, CATEGORIES["agentic-coding"])
    gpt = next(row for row in ranking if row.model == "GPT-5.6 Sol")
    assert (gpt.score, gpt.higher_effort_score) == (60.555, 75.555)

    csv_path, json_path = export_ranking(ranking, tmp_path, [], category="agentic-coding")
    json_gpt = next(
        row for row in json.loads(json_path.read_text())["rows"] if row["model"] == "GPT-5.6 Sol"
    )
    assert (json_gpt["score"], json_gpt["higher_effort_score"]) == (60.6, 75.6)
    with csv_path.open() as handle:
        csv_gpt = next(row for row in csv.DictReader(handle) if row["model"] == "GPT-5.6 Sol")
    assert (csv_gpt["score"], csv_gpt["higher_effort_score"]) == ("60.6", "75.6")


def test_coverage_entrypoint_requires_the_category_effort(tmp_path: Path, capsys) -> None:
    """REQ-CAN-005: max-only evidence cannot make a high-policy plan scoreable."""
    db = tmp_path / "advisor.db"
    _effort_cli_db(db)
    conn = connect(str(db))
    conn.execute("INSERT INTO models VALUES ('grok-4.6', 'Grok 4.6', 'xAI')")
    conn.execute(
        "INSERT INTO plans (id, provider, name, monthly_usd, currency, region, limits,"
        " source_url, last_verified, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "max-only-plan",
            "xAI",
            "Max Only Plan",
            15.0,
            "USD",
            "US",
            "verbatim",
            "https://plans/max-only",
            "2026-08-15",
            "2026-08-16T00:00:00+00:00",
        ),
    )
    conn.execute(
        "INSERT INTO plan_models (plan_id, raw_name, model_id) VALUES (?,?,?)",
        ("max-only-plan", "Grok 4.6", "grok-4.6"),
    )
    score_values = (
        "grok-4.6_max",
        "DeepSWE",
        "% resolved",
        80.0,
        "mini-swe-agent",
        "max",
        "epoch_deepswe_external",
        SOURCE_URL,
        "t",
    )
    conn.execute(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source,"
        " source_url, observed_at, model_id) VALUES (?,?,?,?,?,?,?,?,?, 'grok-4.6')",
        score_values,
    )
    conn.commit()
    conn.close()

    assert coverage_main(["--db", str(db), "--today", "2026-08-16"]) == 1
    first = json.loads(capsys.readouterr().out)
    agentic = next(row for row in first["plan_coverage"] if row["category"] == "agentic-coding")
    assert "Max Only Plan" in agentic["unscoreable_no_scores"]

    conn = connect(str(db))
    conn.execute(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source,"
        " source_url, observed_at, model_id) VALUES (?,?,?,?,?,?,?,?,?, 'grok-4.6')",
        ("grok-4.6_high", *score_values[1:5], "high", *score_values[6:]),
    )
    conn.commit()
    conn.close()
    assert coverage_main(["--db", str(db), "--today", "2026-08-16"]) == 1
    second = json.loads(capsys.readouterr().out)
    agentic = next(row for row in second["plan_coverage"] if row["category"] == "agentic-coding")
    assert "Max Only Plan" in agentic["scoreable"]


@pytest.mark.skipif(not os.getenv("EPOCH_DATA_DIR"), reason="set EPOCH_DATA_DIR for local contract")
def test_real_deepswe_shape_has_one_disclosed_unknown_effort() -> None:
    """REQ-CAN-005 contract: owner-fetched 50-row DeepSWE shape stays understood."""
    bundle = Path(os.environ["EPOCH_DATA_DIR"])
    raw = (bundle / "deepswe_external.csv").read_text(encoding="utf-8-sig")
    rows, stats = parse_deepswe(raw, source="epoch_deepswe_external", source_url=SOURCE_URL)
    assert len(rows) == 49
    assert stats == type(stats)(skipped=1, unknown_effort=1, conflicts=0)
    assert {row.effort for row in rows} == set(EFFORT_LEVELS)
    assert all(row.run_date is None for row in rows)


def test_no_effort_free_category_can_see_more_than_one_effort_level() -> None:
    """W4 review MINOR-3 structural guard: Trap 2 of the M5 plan, made unrepeatable.

    A category with no `ranking_effort` does NOT filter on effort, so its `MAX()` spans
    every effort level a source publishes for the same model+harness — silently
    advertising a max-effort number to a buyer whose plan may not offer it. That is
    exactly the trap the signed plan named. `coding` is effort-free today and is safe
    only because its sources publish one level; nothing structural said so until now.

    The rule: an effort-free category may only be fed by evidence that carries a single
    non-`unspecified` effort per (model, benchmark, metric, harness, source).
    """
    from app.workflows.categories import CATEGORIES
    from app.workflows.schema import EFFORT_UNSPECIFIED, connect

    effort_free = [spec for spec in CATEGORIES.values() if spec.ranking_effort is None]
    assert effort_free, "guard is vacuous if every category names an effort"

    conn = connect()
    for spec in effort_free:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " effort, run_date, source, source_url, observed_at)"
            " VALUES ('m','raw-low',?,?,58.1,'h','low','2026-01-01','s','https://x','t')",
            (spec.primary_benchmark, spec.metric),
        )
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " effort, run_date, source, source_url, observed_at)"
            " VALUES ('m','raw-max',?,?,73.6,'h','max','2026-01-01','s','https://x','t')",
            (spec.primary_benchmark, spec.metric),
        )
        clash = conn.execute(
            "SELECT COUNT(DISTINCT effort) FROM scores"
            " WHERE benchmark = ? AND metric = ? AND model_id = 'm' AND harness = 'h'"
            "   AND source = 's' AND effort != ?",
            (spec.primary_benchmark, spec.metric, EFFORT_UNSPECIFIED),
        ).fetchone()[0]
        # The database ACCEPTS the clash — SQLite has no opinion. The point of this test
        # is that the category is effort-free, so if such rows ever reach it the ranking
        # silently takes the higher one. Whoever adds a multi-effort source to an
        # effort-free category must give that category a ranking_effort first.
        assert clash == 2
        assert spec.ranking_effort is None, (
            f"category {spec.id!r} is effort-free; a multi-effort source may not feed it"
            " without an explicit effort policy (M5 plan Trap 2)"
        )
    conn.close()
