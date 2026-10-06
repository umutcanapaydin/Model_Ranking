"""#124 (REQ-SRC-010 as M19 states it): each served source is credited as its publisher's terms ask.

The facts, each read at its source (`docs/research/data-licences-2026-10-04.md` has the URLs):
- Epoch's hub "also includes data sourced from external projects, which retains its original
  licensing. Users are responsible for complying with the license terms of the specific data they
  use, and should credit the original sources as indicated" (epoch.ai/benchmarks/use-this-data, read
  2026-10-06). Each external file names its source in a `Source` column (the bundle of 2026-10-06).
- SWE-bench's site data is CC BY-NC 4.0 (its repo's `LICENSE`); Aider's leaderboard is Apache-2.0.
- OpenRouter's terms (last updated 2026-08-31) state no attribution clause for `/models`.
- CC BY 4.0 §3(a)(1) asks for a link to the material where practicable, and the licence's URI.

Where attribution must appear is the owner's ruling (#88, question 6); this file holds only what
each string says.
"""

from __future__ import annotations

import pytest

import app.clients.openrouter as openrouter
from app.workflows.rank import ATTRIBUTIONS, PRICING_ATTRIBUTION, SOURCE_ATTRIBUTION

#: Each board Epoch compiles from another publisher -> the name and link its `Source` column gives.
EXTERNAL = {
    "epoch_arc_agi": ("ARC Prize", "https://arcprize.org/leaderboard"),
    "epoch_deepswe_external": ("DeepSWE", "https://deepswe.datacurve.ai/"),
    "epoch_terminalbench": ("Terminal-Bench", "https://www.tbench.ai/leaderboard/terminal-bench/2.0"),
    "epoch_webdev": ("WebDev Arena", "https://arena.ai/leaderboard"),
    "epoch_mmlu": ("Stanford CRFM", "https://crfm.stanford.edu/helm/lite/latest/#/leaderboard/mmlu"),
}

#: A source under a Creative Commons licence -> the link to its material (CC BY §3(a)(1)(A)(v)).
CREATIVE_COMMONS = {
    "arena": "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset",
    "epoch_eci": "https://epoch.ai/benchmarks",
    "swebench": "https://www.swebench.com",
}
LICENCE_LINKS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
}


@pytest.mark.parametrize(("source", "credit"), sorted(EXTERNAL.items()))
def test_an_external_board_credits_its_original_source(source: str, credit: tuple[str, str]) -> None:
    name, link = credit
    citation = SOURCE_ATTRIBUTION[source]
    assert name in citation and link in citation, citation
    assert "Epoch AI" in citation, "the compilation is Epoch's, and is credited too"
    assert "CC-BY-4.0" not in citation, "Epoch's grant does not reach data that keeps its own licence"
    assert citation in ATTRIBUTIONS, "`attributions_for` drops a citation the catalogue does not hold"


def test_swebench_and_aider_are_each_credited_under_their_own_licence() -> None:
    swebench, aider = SOURCE_ATTRIBUTION["swebench"], SOURCE_ATTRIBUTION["aider"]
    assert "swebench.com" in swebench and "CC-BY-NC-4.0" in swebench, swebench
    assert "Aider" not in swebench, "one string named two publishers and only Aider's licence"
    assert "Aider" in aider and "Apache-2.0" in aider and "CC-BY-NC" not in aider, aider
    assert {swebench, aider} <= set(ATTRIBUTIONS)


@pytest.mark.parametrize(("source", "material"), sorted(CREATIVE_COMMONS.items()))
def test_a_creative_commons_source_links_its_material_and_its_licence(source: str, material: str) -> None:
    citation = SOURCE_ATTRIBUTION[source]
    assert material in citation, citation
    named = [token for token in LICENCE_LINKS if f"({token}," in citation]
    assert named, f"no licence named with its link: {citation}"
    assert all(LICENCE_LINKS[token] in citation for token in named), citation


def test_the_pricing_credit_claims_no_term_openrouter_does_not_state() -> None:
    assert "attribution required" not in PRICING_ATTRIBUTION
    assert "attribution required" not in (openrouter.__doc__ or "")


def test_a_credit_the_reader_sees_carries_no_markup_or_file_name() -> None:
    """The M19-W1 review's M7: the app prints a board's attribution as it is
    (`ContentView.swift`'s detail screen), so a credit names its sources in words, without code
    formatting or a file name."""
    for citation in ATTRIBUTIONS:
        assert "`" not in citation and ".csv" not in citation, citation
