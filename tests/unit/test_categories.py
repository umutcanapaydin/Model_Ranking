"""Category layer + assistant ranking tests — cite REQ-CAT-001/-002/-003, REQ-ING-008."""

from __future__ import annotations

import inspect
import json
import pathlib
import sqlite3
from pathlib import Path

import pytest

from app.clients.fakes import FakeRawSource
from app.workflows.categories import CATEGORIES, get_category
from app.workflows.ingest import (
    RunContext,
    ingest_arena,
    ingest_litellm,
    ingest_swebench,
)
from app.workflows.rank import (
    ARENA_ATTRIBUTION,
    PRICING_ATTRIBUTION,
    build_price_medians,
    category_ranking,
    coding_ranking,
    export_ranking,
)
from app.workflows.registry import reconcile
from app.workflows.schema import connect

PRICING = json.dumps(
    {
        "gpt-5-chat": {
            "mode": "chat",
            "input_cost_per_token": 1.25e-06,
            "output_cost_per_token": 1e-05,
        },
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "gemini-3-flash": {
            "mode": "chat",
            "input_cost_per_token": 5e-07,
            "output_cost_per_token": 3e-06,
        },
    }
)
ARENA = json.dumps(
    {
        "rows": [
            {
                "row": {
                    "model_name": "gpt-5-chat",
                    "rating": 1420.5,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
            {
                "row": {
                    "model_name": "claude-4.5-opus",
                    "rating": 1415.2,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
            {
                "row": {
                    "model_name": "gemini-3-flash",
                    "rating": 1380.0,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
        ],
        "num_rows_total": 3,
    }
)
SWE = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {"name": "agent + Claude 4.5 Opus", "resolved": 79.2, "date": "2025-12-15"}
                ],
            }
        ]
    }
)


def _db() -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at="2026-08-11T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_arena(conn, FakeRawSource("arena", ARENA), run)
    ingest_swebench(conn, FakeRawSource("swebench", SWE), run)
    reconcile(conn)
    build_price_medians(conn)
    return conn


def test_categories_are_data_not_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-CAT-001: adding a category = adding a map entry, no code branch."""
    assert set(CATEGORIES) == {
        "coding",
        "assistant",
        "agentic-coding",
        "everyday",
        "expert",
        "mathematics",
        "computer-use",
        "abstract",
        "web-dev",
        # M14-W2: added as two map entries and no code branch, which is the property this test
        # names -- the rest of the engine served them without a line changing.
        "document",
        "factuality",
        # M15-W3: three more, chosen by the W1 survey's measurement rather than by intuition.
        "vision",
        "search",
        "search_factuality",
    }
    for spec in CATEGORIES.values():
        assert spec.primary_benchmark and spec.metric and spec.primary_source
    assert CATEGORIES["agentic-coding"].ranking_effort == "high"
    with pytest.raises(ValueError, match="unknown task"):
        get_category("photoshop")


def test_assistant_ranking_orders_by_elo() -> None:
    """REQ-CAT-002: assistant category ranks on Arena Elo."""
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    assert [r.model for r in ranking] == ["GPT-5 chat", "Claude 4.5 Opus", "Gemini 3 Flash"]
    assert ranking[0].score == 1420.5
    assert ranking[0].harness == "arena-crowd"


def test_no_cross_scale_averaging_structural() -> None:
    """REQ-CAT-003: a model's assistant score is its Elo, untouched by its SWE %.

    Claude has BOTH an Elo (1415.2) and a SWE % (79.2); if any blending
    happened, the assistant score could not remain exactly the raw Elo.
    """
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    claude = next(r for r in ranking if r.model == "Claude 4.5 Opus")
    assert claude.score == 1415.2  # raw Elo, not blended with 79.2
    coding = coding_ranking(conn)
    assert coding[0].score == 79.2  # raw %, not blended with Elo


def test_coding_regression_lock_via_category_layer() -> None:
    """REQ-REC-005: coding_ranking still works and equals the category-layer call."""
    conn = _db()
    assert coding_ranking(conn) == category_ranking(conn, CATEGORIES["coding"])


def test_export_filenames_derive_from_category(tmp_path: Path) -> None:
    """W3 review: assistant export must not overwrite the coding artifact."""
    conn = _db()
    a_csv, a_json = export_ranking(
        category_ranking(conn, CATEGORIES["assistant"]), tmp_path, [], category="assistant"
    )
    c_csv, c_json = export_ranking(coding_ranking(conn), tmp_path, [], category="coding")
    assert a_json.name == "assistant_ranking.json"
    assert c_json.name == "coding_ranking.json"
    assert a_csv != c_csv


def test_export_carries_attribution(tmp_path: Path) -> None:
    """REQ-ING-008: every JSON export names Arena CC-BY-4.0 + all sources + observed_at."""
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    meta: list[dict[str, str | int | None]] = [
        {"source": "arena", "observed_at": "2026-08-11T00:00:00+00:00"}
    ]
    _, json_path = export_ranking(ranking, tmp_path, meta, category="assistant")
    payload = json.loads(json_path.read_text())
    attributions = " ".join(payload["attribution"])
    assert "CC-BY-4.0" in attributions
    assert "lmarena-ai/leaderboard-dataset" in attributions
    assert "OpenRouter" in attributions
    # W4 review BLOCKING-2: an export cites the sources IT carries. This ranking is
    # Arena-only, so claiming SWE-bench/Aider/Epoch here would be a false provenance
    # claim — the exact defect the static catalogue produced in every payload.
    assert "Epoch AI" not in attributions
    assert "swebench.com" not in attributions
    assert tuple(payload["attribution"]) == (ARENA_ATTRIBUTION, PRICING_ATTRIBUTION)
    assert payload["generated_from"][0]["observed_at"] == "2026-08-11T00:00:00+00:00"


# --- M8: the six categories added when the scope widened to all AI tools (D-126/D-127) ---------


def test_no_category_can_exclude_a_model_it_calls_level_with_the_leader() -> None:
    """The invariant the M8 calibration was rebuilt on: `value_window` >= `close_call`.

    `close_call` is a MEASURED fact about the benchmark -- two scores inside it are
    indistinguishable at the board's own precision, and the surface says so. `value_window` is
    the reach of the Best Value pick. If a window were narrower than the close-call threshold,
    the product would disclose "level with the leader" about a model and in the same breath
    refuse to consider it -- ranking noise as if it were quality, which is the one thing this
    engine exists not to do.

    It can fail: `expert` was drafted at window 8.0 against close_call 5.0 and passed; the
    original `mathematics` draft (window 15.0, close 9.5) passed too. Narrow either below its
    close_call and this goes red.
    """
    for name, spec in CATEGORIES.items():
        assert spec.value_window >= spec.close_call, (
            f"{name}: value_window {spec.value_window} is narrower than close_call "
            f"{spec.close_call}; models the surface calls indistinguishable from the leader "
            "would be excluded from the value pick"
        )


def test_every_source_the_build_ingests_can_be_attributed() -> None:
    """A source whose evidence cannot be credited must never reach a user (REQ-ING-008).

    This gates a defect that has already happened: wiring the Epoch boards raised
    `ValueError: unattributed evidence source 'epoch_mmlu'` at BUILD time, after the categories
    were written and the ingestion had run. The rule existed and its gate did not, so the only
    thing that caught it was running the pipeline by hand.

    The referent is the SOURCE REGISTRY, not the category map -- deliberately, because the first
    version of this test asked only about each category's `primary_source` and a mutant that
    deleted `epoch_mmlu`'s attribution walked straight through it. `epoch_mmlu` is nobody's
    primary source; it is served as EVIDENCE, which is precisely the population the control
    covers and the test did not. A test narrower than the rule it cites is not a gate.
    """
    from app.workflows.rank import SOURCE_ATTRIBUTION
    from app.workflows.sources import EPOCH_BOARDS, LOCAL_BUNDLES, REMOTE_SOURCES

    ingested = (
        {s.name for s in REMOTE_SOURCES if s.writes_scores}
        | {b.name for b in LOCAL_BUNDLES}
        | {b.source_name for b in EPOCH_BOARDS}
    )
    unattributed = sorted(ingested - set(SOURCE_ATTRIBUTION))
    assert not unattributed, (
        f"the build ingests {unattributed} with no SOURCE_ATTRIBUTION entry; serving a pick "
        "whose evidence comes from one of these raises at request time"
    )


def test_every_category_is_reachable_by_the_name_the_api_accepts() -> None:
    """A category in the map that `get_category` cannot resolve is a category nobody can query."""
    for name, spec in CATEGORIES.items():
        assert get_category(name) is spec
        assert spec.id == name, f"{name} carries id {spec.id!r}; the API would route on the key"


# --- M8 fresh-eyes review: eight of ten threshold mutants survived ------------------------------


def test_a_category_ranks_on_the_board_it_names_and_reads_the_metric_that_board_publishes() -> None:
    """CAT-05 / CAT-06: nothing checked that a category and its source agree about WHAT is measured.

    `test_every_source_a_category_names_as_primary_exists_in_the_registry` asserts only that the
    source NAME resolves. An independent tester pointed `expert` at `epoch_eci` and relabelled
    `abstract`'s metric as `"elo"`; both stayed green across the whole suite. The first ranks a
    category on the wrong board, the second describes a percentage board as an Elo board — and
    D-105's whole point is that a number is meaningless without its scale.

    The check is DERIVED: `EpochBoard` already declares the benchmark and metric it publishes, so
    the agreement can be computed rather than restated. That is what makes it a gate and not a
    second copy of the table.
    """
    from app.workflows.sources import EPOCH_BOARDS

    boards = {b.source_name: b for b in EPOCH_BOARDS}
    checked = 0
    for name, spec in CATEGORIES.items():
        board = boards.get(spec.primary_source)
        if board is None:
            continue  # not a declared Epoch board; covered by the registry test
        checked += 1
        assert spec.primary_benchmark == board.benchmark, (
            f"{name} says it ranks on {spec.primary_benchmark!r} and its source "
            f"{spec.primary_source!r} publishes {board.benchmark!r}"
        )
        assert spec.metric == board.metric, (
            f"{name} reads {spec.metric!r} from a board that publishes {board.metric!r}; a score "
            "relabelled onto another scale is D-105's defect with a different spelling"
        )
    assert checked >= 6, f"expected the six board-backed categories to be checked; saw {checked}"


def test_no_threshold_is_on_a_scale_its_own_metric_cannot_reach() -> None:
    """CAT-01 / CAT-02 / CAT-09: no test pinned any `min_quality`, on any scale.

    D-127 states the obligation and shipped no gate for it: *"A threshold copied from one scale to
    another is a wrong answer wearing a correct-looking constant."* An independent tester moved
    `web-dev`'s Elo floor to `100.0` (every model clears it, so the floor stops existing and no
    disclosure fires) and `expert`'s percentage floor to `200.0` (nobody ever qualifies, forever).
    Both green.

    This does not pin the calibrated VALUES — those are measured and will move as boards move. It
    pins the property that outlives any recalibration: a percentage threshold lives in (0, 100],
    and an Elo threshold cannot.
    """
    for name, spec in CATEGORIES.items():
        assert spec.min_quality > 0, (
            f"{name} has a floor of {spec.min_quality}; a floor of zero admits the whole board and "
            "is a Budget Pick with no quality bar at all"
        )
        assert spec.close_call > 0, (
            f"{name} has a close-call threshold of {spec.close_call}, so it would never disclose a "
            "near tie — on a board whose measurement error is real, that publishes noise as rank"
        )
        if spec.metric.startswith("%"):
            assert spec.min_quality <= 100.0, (
                f"{name} measures {spec.metric!r} and its floor is {spec.min_quality}, which no "
                "score on that scale can reach"
            )
            assert spec.value_window <= 100.0, (
                f"{name}'s value window of {spec.value_window} spans more than the whole scale"
            )
        # An Elo board has no natural ceiling, so "<= 100" cannot bound its window. This does,
        # and it holds on all nine: a value window WIDER than the quality floor reaches models the
        # floor has already rejected, which makes the two controls contradict each other. Added
        # after CAT-10 (`web-dev`'s window set to 1e9, making every model "best value") survived
        # the first version of this test.
        assert spec.value_window < spec.min_quality, (
            f"{name}'s value window ({spec.value_window}) is wider than its quality floor "
            f"({spec.min_quality}); Best Value would reach models Budget Pick refuses"
        )
        if spec.metric == "elo":
            assert spec.min_quality >= 1000.0, (
                f"{name} ranks on Elo and its floor is {spec.min_quality}; that is a percentage "
                "constant on an Elo board, and every model would clear it"
            )


def test_no_surface_states_a_bar_the_engine_does_not_apply() -> None:
    """One product, one bar. Stage 4.0 MINOR-1.

    W-084 established the rule — *"printing `84` states a bar the engine does not apply"* — and it
    was applied to `recommend.py` and not to `subscribe.py`. On **6 of 9 surfaces** the CLI then
    stated a different minimum-quality bar than the API: `expert` said `84` where the engine
    applies `83.6`, `mathematics` said `84` where the engine applies `84.4`. One product, two bars.

    That is the recurring shape rather than a formatting slip: **a lesson attaches to an artifact,
    not to the person who learned it** (V4C-50). It is attached here, to the constants, because
    that is the one place every surface that quotes them can be reached at once.

    **The first version of this test passed against the reverted defect** and was thrown away. It
    compared strings that could not differ. What it needed to do is what it does now: take the
    format specifier each surface actually writes, apply it to the real constant, and check the
    number a reader would see.
    """
    import re

    from app.workflows import recommend, subscribe

    quoted = re.compile(r"\{spec\.(min_quality|value_window)(:[^}]+)?\}")
    offenders = []
    for module in (subscribe, recommend):
        source = pathlib.Path(inspect.getsourcefile(module) or "").read_text(encoding="utf-8")
        for field, fmt in quoted.findall(source):
            for task, spec in CATEGORIES.items():
                value = getattr(spec, field)
                shown = format(value, fmt[1:]) if fmt else str(value)
                if shown != f"{value:g}":
                    offenders.append(
                        f"{module.__name__}: `{{spec.{field}{fmt}}}` shows {shown} on {task}, "
                        f"but the engine applies {value:g}"
                    )
    assert not offenders, "a surface states a bar the engine does not apply:\n" + "\n".join(
        sorted(set(offenders))
    )


def test_every_surface_names_the_source_its_board_arrives_on() -> None:
    """MAJOR-2 of the M14 closure seat: `primary_source` decides who DISCLOSES, so it must be right.

    `build.py` answers "this source is missing, which surfaces must stay silent?" from this field
    (D-121). The seat repointed `document` at `arena` and every one of 912 tests stayed green: the
    surface would then keep answering from a board nobody fetched, and the missing-source action
    would say "no surface names it as primary" about a board two surfaces are built on.

    Pinned as a TABLE rather than a rule, because the pairing is a fact about each board's
    registration, not something a pattern can derive: `assistant` reads the source `arena` whose
    benchmark label is `Arena text`, and no rule turns one name into the other.
    """
    from app.workflows.build import _surfaces_left_without_evidence

    pairs = {
        "assistant": "arena",
        "document": "arena_document",
        "factuality": "arena_factuality",
        "vision": "arena_vision",
        "search": "arena_search",
        "search_factuality": "arena_search_factuality",
        "coding": "swebench",
        "agentic-coding": "epoch_deepswe_external",
        "everyday": "epoch_eci",
        "expert": "epoch_gpqa",
        "mathematics": "epoch_aime",
        "computer-use": "epoch_terminalbench",
        "abstract": "epoch_arc_agi",
        "web-dev": "epoch_webdev",
    }
    assert set(pairs) == set(CATEGORIES), "a surface was added or removed without pinning its source"
    for surface, source in pairs.items():
        assert CATEGORIES[surface].primary_source == source, surface

    # ...and the pairing is load-bearing THROUGH the live entry point: an unavailable source must
    # name its own surfaces, which is what a reader is told instead of an answer.
    for surface, source in pairs.items():
        actions = _surfaces_left_without_evidence([f"{source}: fetch failed"])
        assert any(surface in action and "must" in action for action in actions), (
            f"{source} going missing does not silence {surface}"
        )


def test_the_two_board_surfaces_rank_only_their_own_board() -> None:
    """REQ-SUR-001: `document` and `factuality` each rank ONLY their own benchmark.

    D-105: an Elo on one board is not comparable to an Elo on another, so a row labelled
    `Arena document` must never reach `assistant`, and the reverse.
    """
    for surface, benchmark in (("document", "Arena document"), ("factuality", "Arena factuality")):
        spec = CATEGORIES[surface]
        assert spec.primary_benchmark == benchmark
        assert spec.metric == "elo"
        assert spec.primary_benchmark != CATEGORIES["assistant"].primary_benchmark
        # D-145: the floor is on the board's own scale, and below its value window's reach
        assert spec.min_quality >= 1000.0
        assert spec.value_window < spec.min_quality


def test_a_board_only_reaches_its_own_surface_through_the_ranking_query() -> None:
    """REQ-SUR-001 behaviourally, through `category_ranking` -- the M14 closure seat's MAJOR-3.

    The wave record cited a test that only read `CategorySpec` fields, which cannot fail on the
    thing the criterion is about: the criterion is a property of the QUERY, not of four strings.
    Here three boards carry the same model at three different ratings, plus one model that exists
    on one board only, and each surface must see exactly its own.

    D-105 in one assertion: an Elo on the document board is not an Elo on the chat board, and a
    leader on one must never arrive as a leader on the other.
    """
    import json

    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_arena, ingest_litellm
    from app.workflows.rank import build_price_medians, category_ranking
    from app.workflows.registry import reconcile
    from app.workflows.schema import connect

    from .test_api_v1 import PRICING

    def board(rows: list[tuple[str, float]]) -> str:
        return json.dumps(
            {
                "rows": [
                    {
                        "row": {
                            "model_name": name,
                            "rating": rating,
                            "category": "overall",
                            "leaderboard_publish_date": "2026-09-13",
                        }
                    }
                    for name, rating in rows
                ]
            }
        )

    from app.clients.arena import ARENA_BOARDS

    # M15-W3 review B-1: the first version ingested three boards and checked a hand-written tuple
    # of three surfaces, so pointing `vision` at the chat board passed. Every surface fed by an
    # Arena board is now in the fixture, each board carrying the shared model at its OWN rating.
    arena_ids = {b.id for b in ARENA_BOARDS.values()}
    surfaces = sorted(s for s, spec in CATEGORIES.items() if spec.primary_source in arena_ids)
    assert {"assistant", "document", "factuality", "vision", "search", "search_factuality"} <= set(
        surfaces
    ), surfaces
    sources = sorted({CATEGORIES[s].primary_source for s in surfaces})
    rating = {sid: 1400.0 + 10.0 * i for i, sid in enumerate(sources)}

    conn = connect()
    run = RunContext(observed_at="2026-09-21T00:00:00Z")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    shared, only_here = "GPT-5", "DeepSeek V3.2"  # display names, as the registry canonicalises
    for sid in sources:
        rows = [("gpt-5", rating[sid])]
        if sid == "arena_document":
            rows.append(("deepseek-v3.2", rating[sid] - 5.0))
        ingest_arena(conn, FakeRawSource(sid, board(rows)), run)
    reconcile(conn)
    build_price_medians(conn)

    seen = {
        surface: {row.model: row.score for row in category_ranking(conn, CATEGORIES[surface])}
        for surface in surfaces
    }
    for surface in surfaces:
        own = rating[CATEGORIES[surface].primary_source]
        assert seen[surface].get(shared) == own, (surface, seen[surface])
    # The model that exists on ONE board reaches ONE surface. This is the assertion the mutant that
    # merged the boards at ingest died on, now stated where a reader meets it.
    assert only_here in seen["document"], seen["document"]
    assert [s for s in surfaces if only_here in seen[s]] == ["document"]


#: The three M15 surfaces' thresholds as the calibration record states them after the W-113
#: correction (`docs/reviews/m15-category-calibration.md`, correction of 2026-09-22). M15-W3 review
#: m-1 and W4 review MINOR-2: only the anchors were pinned, so moving a floor or putting a
#: corrected margin back to its old value passed every test.
#: The margins and windows are the M15 calibration record's. The FLOORS of `vision` and
#: `search_factuality` moved in M16-W3 under D-148 (record `docs/research/m16-w3-floor-table-2026-09-23.md`,
#: pinned by `test_floor_rule.py`); `search`'s did not move.
PINNED_M15_THRESHOLDS = {
    "vision": (1253.3, 7.8, 31.2),
    "search": (1206.9, 6.5, 25.9),
    "search_factuality": (1202.1, 4.9, 19.5),
}


def test_the_m15_surfaces_ship_the_thresholds_their_calibration_record_states() -> None:
    for surface, (floor, close_call, window) in PINNED_M15_THRESHOLDS.items():
        spec = CATEGORIES[surface]
        assert (spec.min_quality, spec.close_call, spec.value_window) == (
            floor,
            close_call,
            window,
        ), surface
        # the M14 rule: the window is four times the unrounded median, so within rounding of 4x
        assert abs(spec.value_window - 4 * spec.close_call) <= 0.2, surface
