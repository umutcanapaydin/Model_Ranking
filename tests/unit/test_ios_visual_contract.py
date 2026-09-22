"""REQ-CMP-001/002: a visual refresh must not move card meaning behind navigation."""

import re
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[2] / "ios/ModelRanking"


def test_pick_cards_keep_scale_familiar_price_and_evidence() -> None:
    view = (CLIENT / "ContentView.swift").read_text()
    pick = view.split("struct PickRow: View", 1)[1].split("struct RankedRow: View", 1)[0]
    assert re.search(r"if let scale\s*\{\s*Text\(scale\)", pick)
    assert "Text(priceInPages(pick.blendedPerM, in: language))" in pick
    for rendered in ("Text(whyText)", "Text(evidence)", "Text(tradeOff)"):
        assert rendered in pick


def test_the_model_card_is_the_detail_navigation_label() -> None:
    """REQ-DTL-001: the whole recommendation, including its model, opens existing evidence."""
    view = (CLIENT / "ContentView.swift").read_text()
    pick = view.split("struct PickRow: View", 1)[1].split("struct RankedRow: View", 1)[0]
    body = pick.split("var body: some View", 1)[1]
    assert re.search(r"NavigationLink\s*\{\s*ModelDetail\(", body)
    label = body.split("} label: {", 1)[1]
    assert "Text(pick.model)" in label
    assert "Text(UIText.openEvidence(language))" in label
