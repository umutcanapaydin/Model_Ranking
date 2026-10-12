"""#260 (the owner's D-185 ruling, 2026-10-12): every served source is credited on a Credits screen
with its publisher, its licence and its links.

The credits are derived from the attributions a payload already owes (`attributions_for`), never kept
as a second list beside them: an attribution with no credit is refused, so a source cannot be served
and left off the screen.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows import rank
from app.workflows.board_tables import EPOCH_ATTRIBUTION, EPOCH_EXTERNAL_ATTRIBUTION
from app.workflows.rank import (
    ATTRIBUTIONS,
    PRICING_ATTRIBUTION,
    PRICING_ATTRIBUTION_LITELLM,
    SOURCE_ATTRIBUTION,
    SWEBENCH_ATTRIBUTION,
)

from .test_board_standings import _chess, _conn, _payload

CREDIT_KEYS = {"id", "publisher", "data", "url", "licence", "licence_url"}


def credits_for(attributions: list[str] | tuple[str, ...]) -> list[dict[str, str | None]]:
    return rank.credits_for(attributions)  # type: ignore[no-any-return]


def _ids(attributions: list[str] | tuple[str, ...]) -> list[str]:
    return [credit["id"] for credit in credits_for(attributions)]


@pytest.mark.parametrize("citation", sorted({*ATTRIBUTIONS, PRICING_ATTRIBUTION_LITELLM, *SOURCE_ATTRIBUTION.values()}))
def test_every_citation_the_engine_can_owe_has_a_credit(citation: str) -> None:
    """Derived from the catalogue and the per-source map, so a new attribution without a credit fails."""
    credits = credits_for([citation])
    assert credits, citation
    for credit in credits:
        assert set(credit) == CREDIT_KEYS
        assert credit["publisher"] and credit["data"] and credit["licence"]
        assert credit["url"].startswith("https://"), credit
        assert credit["licence_url"] is None or credit["licence_url"].startswith("https://"), credit


def test_an_attribution_with_no_credit_is_refused() -> None:
    with pytest.raises(ValueError, match="no credit"):
        credits_for(["Scores: somebody nobody reviewed"])


def test_each_publisher_is_credited_once_in_the_order_the_attributions_come() -> None:
    owed = [EPOCH_EXTERNAL_ATTRIBUTION["epoch_arc_agi"], EPOCH_ATTRIBUTION, PRICING_ATTRIBUTION]
    assert _ids(owed) == ["arc_prize", "epoch", "litellm", "openrouter"]


def test_a_board_epoch_compiles_credits_its_publisher_and_epoch() -> None:
    for source, publisher in (("epoch_arc_agi", "arc_prize"), ("epoch_deepswe_external", "datacurve"),
                              ("epoch_terminalbench", "terminal_bench"), ("epoch_mmlu", "helm"),
                              ("epoch_webdev", "arena_site")):
        assert _ids([SOURCE_ATTRIBUTION[source]]) == [publisher, "epoch"], source


def test_prices_credit_openrouter_only_where_its_prices_are_served() -> None:
    assert _ids([PRICING_ATTRIBUTION]) == ["litellm", "openrouter"]
    assert _ids([PRICING_ATTRIBUTION_LITELLM]) == ["litellm"]


def test_the_owners_ruling_is_what_the_screen_says() -> None:
    """The owner, 2026-10-12: SWE-bench is CC BY-NC 4.0 and credited; MMLU is HELM (Apache-2.0) and
    the model makers' arXiv reports, credited."""
    swebench = credits_for([SWEBENCH_ATTRIBUTION])[0]
    assert (swebench["licence"], swebench["licence_url"]) == (
        "CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/")
    helm = credits_for([EPOCH_EXTERNAL_ATTRIBUTION["epoch_mmlu"]])[0]
    assert "Apache-2.0" in helm["licence"] and "arXiv" in helm["data"]


def test_the_boards_payload_carries_the_credits_its_attributions_owe() -> None:
    conn = _conn()
    _chess(conn)
    payload = _payload(conn)
    assert payload["credits"] == credits_for(payload["attributions"])
    assert [c["id"] for c in payload["credits"]] == ["litellm", "epoch"]  # the catalogue order


def test_the_boards_payload_credits_openrouter_when_it_serves_its_prices() -> None:
    conn: sqlite3.Connection = _conn()
    _chess(conn)
    conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url, observed_at) "
                 "VALUES ('a', 'a', 1.0, 2.0, 'openrouter', 'u', '2026-09-25')")
    assert "openrouter" in [c["id"] for c in _payload(conn)["credits"]]
