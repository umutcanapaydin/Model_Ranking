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

CREDIT_KEYS = {"id", "publisher", "data", "url", "licence", "licence_url", "notice"}


def credits_for(attributions: list[str] | tuple[str, ...]) -> list[dict[str, str | None]]:
    return rank.credits_for(attributions)


def _ids(attributions: list[str] | tuple[str, ...]) -> list[str]:
    return [credit["id"] for credit in credits_for(attributions)]


@pytest.mark.parametrize("citation", sorted({*ATTRIBUTIONS, PRICING_ATTRIBUTION_LITELLM, *SOURCE_ATTRIBUTION.values(),
                                              *rank.METADATA_ATTRIBUTION.values()}))
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
    owed = [EPOCH_EXTERNAL_ATTRIBUTION["epoch_deepswe_external"], EPOCH_ATTRIBUTION, PRICING_ATTRIBUTION]
    assert _ids(owed) == ["datacurve", "epoch_compilation", "epoch", "litellm", "models_dev"]


def test_a_board_epoch_compiles_credits_its_publisher_and_epochs_compilation() -> None:
    for source, publisher in (("epoch_deepswe_external", "datacurve"),
                              ("epoch_mmlu", "helm"),
                              ("epoch_webdev", "arena_site")):
        assert _ids([SOURCE_ATTRIBUTION[source]]) == [publisher, "epoch_compilation"], source


def test_epochs_licence_is_claimed_for_its_own_boards_only() -> None:
    """The #260 review's B1: Epoch's external data "retains its original licensing", so the credit for
    Epoch's compilation claims no licence, and the CC BY credit names Epoch's own boards."""
    from app.workflows.board_tables import CREDITS

    compilation = CREDITS["epoch_compilation"]
    assert compilation.licence_url is None and "CC BY" not in compilation.licence
    assert "compil" not in CREDITS["epoch"].data.lower()


def test_prices_credit_models_dev_only_where_its_prices_are_served() -> None:
    assert _ids([PRICING_ATTRIBUTION]) == ["litellm", "models_dev"]
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


def test_the_boards_payload_credits_models_dev_when_it_serves_its_prices() -> None:
    conn: sqlite3.Connection = _conn()
    _chess(conn)
    conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url, observed_at) "
                 "VALUES ('a', 'a', 1.0, 2.0, 'models_dev', 'u', '2026-09-25')")
    assert "models_dev" in [c["id"] for c in _payload(conn)["credits"]]


def test_the_accessibility_epoch_publishes_is_credited_whatever_boards_are_served() -> None:
    """The #260 review's M1: `/v1/boards` serves each model's accessibility from Epoch's metadata, so
    Epoch is credited even where no Epoch board is served."""
    from .test_board_standings import _score

    conn = _conn()
    _score(conn, "arena", "Arena text", "elo", "a", "a", 1300.0)
    conn.execute("INSERT INTO access (raw_name, model_id, accessibility, source, source_url, observed_at) "
                 "VALUES ('a', 'a', 'api', 'epoch_access', 'u', '2026-09-25')")
    payload = _payload(conn)
    assert payload["models"][0]["accessibility"] == "api"
    assert "epoch" in [c["id"] for c in payload["credits"]]


def test_a_board_is_attributed_from_the_boards_alone() -> None:
    """The #260 round-2 review's M3: a source that is not a board (`epoch_access`) does not pass the
    board check, so a board that took its id would be refused, not served half-attributed."""
    with pytest.raises(ValueError, match="SOURCE_ATTRIBUTION"):
        rank.attributions_for(["epoch_access"], priced=False)


def test_an_accessibility_source_nobody_credits_is_refused_by_its_own_map() -> None:
    """The #260 round-2 review's M3: the error names the map the source belongs in."""
    from .test_board_standings import _score

    conn = _conn()
    _score(conn, "arena", "Arena text", "elo", "a", "a", 1300.0)
    conn.execute("INSERT INTO access (raw_name, model_id, accessibility, source, source_url, observed_at) "
                 "VALUES ('a', 'a', 'api', 'somebody_access', 'u', '2026-09-25')")
    with pytest.raises(ValueError, match="METADATA_ATTRIBUTION"):
        _payload(conn)


def test_lmarenas_credit_keeps_its_copyright_notice() -> None:
    """CC BY 4.0 section 3(a)(1)(A)(ii): the copyright notice the dataset's own credit carries (the
    #260 review's M3, held since round 2's M2)."""
    from app.workflows.board_tables import ARENA_ATTRIBUTION

    assert "\u00a9 LMArena" in ARENA_ATTRIBUTION
    assert credits_for([ARENA_ATTRIBUTION])[0]["data"].startswith("\u00a9 LMArena")


def test_a_citation_outside_the_catalogue_is_refused_not_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    """The #260 Tester's M4: `attributions_for` kept only the catalogue's citations, so a metadata source
    whose citation was credited but not catalogued was served with no attribution and no credit."""
    stray = "Metadata: somebody's model list"
    monkeypatch.setitem(rank.METADATA_ATTRIBUTION, "somebody_meta", stray)
    monkeypatch.setitem(rank.CREDITS_BY_ATTRIBUTION, stray, ("epoch",))
    with pytest.raises(ValueError, match="catalogue"):
        rank.attributions_for([], priced=False, metadata_sources=["somebody_meta"])


def test_the_credits_sheet_shows_what_the_engine_layer_decides() -> None:
    """The #260 Tester's B1: the sheet's state and lines are decided in the Engine (`CreditsScreen`),
    where `swift test` holds them; the view draws them, each link in a `Text` of its own, selectable."""
    import pathlib
    import re

    view = (pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/ContentView.swift").read_text(encoding="utf-8")
    sheet = view[view.index("private var creditsSheet"):]
    sheet = sheet[: sheet.index("\n    }\n") + 6]
    assert "CreditsScreen.state(standings, language)" in sheet
    # The Tester's round-2 M1: the selection is on the credits' lines, and the empty texts are the ones
    # `CreditsScreen` chose, never named here.
    rows = sheet[sheet.index("ForEach(rows)"):sheet.index("case let .notSent")]
    assert ".textSelection(.enabled)" in rows
    for line in ("row.publisher", "row.data", "row.dataLabel", "row.dataLink", "row.licence", "licenceLink"):
        assert re.search(rf"Text\({re.escape(line)}\)", rows), line
    assert "UIText.creditsUnavailable" not in sheet and "UIText.creditsNotSent" not in sheet
    assert re.search(r"case let \.notSent\(text\), let \.notLoaded\(text\):\s*Text\(text\)", sheet)
    # The Tester's round-2 B1: the CC BY notices are `CreditsScreen`'s, and the sheet draws them.
    assert "Text(CreditsScreen.notice(language))" in sheet


def test_the_credits_button_opens_the_sheet() -> None:
    """The Tester's round-2 M2: the button sets the flag the sheet is presented on."""
    import pathlib
    import re

    view = (pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/ContentView.swift").read_text(encoding="utf-8")
    assert ".sheet(isPresented: $showingCredits) { creditsSheet }" in view
    assert re.search(r'Button \{ showingCredits = true \} label: \{[^}]*\}\s*\.accessibilityIdentifier\("credits"\)', view)


def test_every_publishers_licence_is_the_one_the_ruling_and_the_record_give() -> None:
    """The #260 Tester's M1: every credit's licence and licence link, pinned whole, so a credit cannot
    claim a licence D-193 and `docs/research/data-licences-2026-10-04.md` do not give it."""
    from app.workflows.board_tables import CREDITS

    cc_by, cc_by_nc = "https://creativecommons.org/licenses/by/4.0/", "https://creativecommons.org/licenses/by-nc/4.0/"
    assert {credit.id: (credit.licence, credit.licence_url) for credit in CREDITS.values()} == {
        "lmarena": ("CC BY 4.0", cc_by),
        "epoch": ("CC BY 4.0", cc_by),
        "epoch_compilation": ("Each board keeps its publisher's licence or terms, named in that publisher's credit",
                              None),
        "swebench": ("CC BY-NC 4.0", cc_by_nc),
        "aider": ("Apache-2.0", "https://github.com/Aider-AI/aider/blob/main/LICENSE.txt"),
        "litellm": ("MIT", "https://github.com/BerriAI/litellm/blob/main/LICENSE"),
        "models_dev": ("MIT", "https://github.com/sst/models.dev/blob/dev/LICENSE"),
        "arc_prize": ("MIT", "https://opensource.org/license/mit"),
        "datacurve": ("\u00a9 Datacurve; no licence published", None),
        "terminal_bench": ("Apache-2.0", "https://github.com/harbor-framework/terminal-bench/blob/main/LICENSE"),
        "helm": ("Apache-2.0 (the HELM repository, D-193); each report as its authors published it",
                 "https://github.com/stanford-crfm/helm/blob/main/LICENSE"),
        "arena_site": ("Arena Terms of Use", "https://help.arena.ai/articles/5629909088-terms-of-use"),
        # The #265 review's B2: the retired sources' publishers, for an artifact an older release built.
        "arc_prize_leaderboard": ("ARC Prize Terms", "https://arcprize.org/terms"),
        "terminal_bench_2": ("No licence stated on the leaderboard", None),
        "openrouter": ("OpenRouter Terms of Service", "https://openrouter.ai/terms"),
    }


def test_the_boards_payload_refuses_a_served_citation_with_no_credit(monkeypatch: pytest.MonkeyPatch) -> None:
    """The #260 Tester's M3: refused where the payload is built, not only in `credits_for`."""
    conn = _conn()
    _chess(conn)
    monkeypatch.delitem(rank.CREDITS_BY_ATTRIBUTION, EPOCH_ATTRIBUTION)
    with pytest.raises(ValueError, match="no credit"):
        _payload(conn)


def test_every_citation_a_source_can_owe_is_in_the_catalogue() -> None:
    """The #260 Tester's M4: the maps' citations are the catalogue's, so none is dropped."""
    catalogue = {*ATTRIBUTIONS, PRICING_ATTRIBUTION_LITELLM}
    assert set(SOURCE_ATTRIBUTION.values()) <= catalogue
    assert set(rank.METADATA_ATTRIBUTION.values()) <= catalogue



def test_an_apache_or_mit_credit_carries_the_notice_its_licence_asks_to_keep() -> None:
    """#261 (the #260 review's K1): Apache-2.0 section 4(c) and MIT ask a redistributor to keep the
    copyright notice. Each such credit carries the line its publisher's LICENSE file holds, read on
    2026-10-14; a publisher whose file holds none is named in `PUBLISHES_NO_NOTICE` with why."""
    from app.workflows.board_tables import CREDITS, PUBLISHES_NO_NOTICE

    notices = {credit.id: credit.notice for credit in CREDITS.values()}
    assert notices["litellm"] == "Copyright (c) 2023 Berri AI"
    assert notices["models_dev"] == "Copyright (c) 2025 models.dev"
    assert notices["helm"] == "Copyright 2022 Stanford University"
    for credit in CREDITS.values():
        if credit.licence.startswith(("Apache-2.0", "MIT")):
            assert bool(credit.notice) != (credit.id in PUBLISHES_NO_NOTICE), credit.id
        else:
            assert credit.notice is None and credit.id not in PUBLISHES_NO_NOTICE, credit.id
    assert credits_for([PRICING_ATTRIBUTION_LITELLM])[0]["notice"] == "Copyright (c) 2023 Berri AI"


#: #261: the published texts, whitespace folded, as read on 2026-10-14: Apache-2.0 from Aider's and
#: Terminal-Bench's LICENSE files (the same text), MIT's terms from models.dev's and LiteLLM's.
LICENCE_TEXT_SHA256 = {
    "apache20": "0ffddef9e48f8a09aed5caf2d44f7ba1c1be2d9b8e0a6f693b1635b2d5566645",
    "mit": "fe2a9817987f862eaced948f0468c7f51d2fedfc48c5c505b246a49a3870e9a5",
}


@pytest.mark.parametrize("name", sorted(LICENCE_TEXT_SHA256))
def test_the_app_carries_each_licence_text_verbatim(name: str) -> None:
    """#261: the licences ask for a copy of themselves, so the app's copy is the published text, word for
    word; only its line breaks may differ. The backlog-gates review's N1: the text is read as the build
    compiles it (`_swift`, #247), and once, so a dead copy above a changed live one satisfies nothing."""
    import hashlib
    import pathlib
    import re

    from .test_ios_client_contract import _swift

    models = _swift(pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Models.swift")
    found = re.findall(rf'static let {name} = """\n(.*?)\n"""', models, re.S)
    assert len(found) == 1, f"Models.swift holds {len(found)} live `{name}` texts, not one"
    match = re.search(rf'static let {name} = """\n(.*?)\n"""', models, re.S)
    assert match
    folded = " ".join(match.group(1).split())
    assert hashlib.sha256(folded.encode()).hexdigest() == LICENCE_TEXT_SHA256[name]
