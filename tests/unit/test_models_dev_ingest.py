"""models.dev pricing ingestion tests (#265, D-194) — cite REQ-ING-005 and REQ-ING-004.

models.dev (`sst/models.dev`, MIT) takes OpenRouter's place as the second price source. Its catalogue
lists the same model under its maker and under every reseller; only the maker's own entry is read, so
the second price is the vendor's list price and never a reseller's, and never models.dev's copy of
OpenRouter's catalogue.
"""

from __future__ import annotations

import importlib
import json

import pytest

FIXTURE = json.dumps(
    {
        "anthropic": {"id": "anthropic", "name": "Anthropic", "models": {
            "claude-opus-5-5": {"id": "claude-opus-5-5", "cost": {"input": 5, "output": 25, "cache_read": 0.5},
                                "limit": {"context": 1000000, "output": 128000}},
            "claude-free": {"id": "claude-free", "cost": {"input": 0, "output": 0}},
            "claude-unpriced": {"id": "claude-unpriced"},
        }},
        "xai": {"id": "xai", "name": "xAI", "models": {
            "grok-5": {"id": "grok-5", "cost": {"input": 3, "output": 15}, "limit": {"context": 256000}},
            "grok-bad": {"id": "grok-bad", "cost": {"input": "3", "output": True}},
        }},
        "zai": {"id": "zai", "name": "Z.AI", "models": {
            "glm-5.3": {"id": "glm-5.3", "cost": {"input": 1, "output": 3.2}},
        }},
        "openrouter": {"id": "openrouter", "name": "OpenRouter", "models": {
            "anthropic/claude-opus-5-5": {"id": "anthropic/claude-opus-5-5", "cost": {"input": 5, "output": 25}},
        }},
        "deepinfra": {"id": "deepinfra", "name": "Deep Infra", "models": {
            "zai-org/GLM-5.3": {"id": "zai-org/GLM-5.3", "cost": {"input": 0.8, "output": 2.5}},
        }},
        "broken": "not-a-provider",
    }
)


def _client():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.models_dev")


def test_only_the_model_makers_own_entries_are_read_at_their_price_per_million() -> None:
    """covers REQ-ING-005: a reseller's entry and models.dev's copy of OpenRouter are never a price."""
    rows, skipped = _client().parse_models_dev(FIXTURE)
    by_alias = {r.alias: r for r in rows}
    assert set(by_alias) == {"anthropic/claude-opus-5-5", "x-ai/grok-5", "z-ai/glm-5.3"}
    opus = by_alias["anthropic/claude-opus-5-5"]
    assert (opus.input_per_m, opus.output_per_m, opus.context) == (5.0, 25.0, 1000000)
    assert by_alias["z-ai/glm-5.3"].output_per_m == pytest.approx(3.2)
    assert {r.source for r in rows} == {"models_dev"}
    assert skipped == 3  # free, unpriced, a string or bool price


def test_every_maker_read_names_a_vendor_the_registry_knows() -> None:
    """covers REQ-ING-005: the route each alias carries is one `registry._VENDOR_SLUGS` maps, so a
    models.dev price joins its model rather than standing alone under an unknown vendor."""
    from app.workflows import registry

    assert set(_client().MAKERS.values()) <= set(registry._VENDOR_SLUGS)
    assert "openrouter" not in _client().MAKERS


def test_a_payload_that_is_not_a_catalogue_is_refused() -> None:
    """covers REQ-ING-005: an envelope that is not an object of providers fails the source."""
    from app.clients.protocols import SourceError

    for raw in ("[]", "null", "not json", json.dumps({"anthropic": {"models": []}})):
        with pytest.raises(SourceError):
            _client().parse_models_dev(raw)


def test_ingest_stores_with_provenance_and_replaces() -> None:
    """covers REQ-ING-004: provenance stamped; a second run replaces the models_dev set only."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import ingest
    from app.workflows.schema import connect

    conn = connect()
    source = FakeRawSource("models_dev", FIXTURE, url="https://models.dev/api.json")
    ingest.ingest_models_dev(conn, source, ingest.RunContext(observed_at="t1"))
    ingest.ingest_models_dev(conn, source, ingest.RunContext(observed_at="t2"))
    rows = conn.execute("SELECT alias, source, source_url, observed_at FROM pricing ORDER BY alias").fetchall()
    assert [tuple(r) for r in rows] == [
        ("anthropic/claude-opus-5-5", "models_dev", "https://models.dev/api.json", "t2"),
        ("x-ai/grok-5", "models_dev", "https://models.dev/api.json", "t2"),
        ("z-ai/glm-5.3", "models_dev", "https://models.dev/api.json", "t2"),
    ]


def test_models_dev_replaces_openrouter_as_the_second_price_source() -> None:
    """covers REQ-ING-005 (D-194 clause 2): the build reads models.dev and no longer reads OpenRouter."""
    from app.workflows import sources

    names = {s.name for s in sources.REMOTE_SOURCES}
    assert "models_dev" in names
    assert "openrouter" not in names
    models_dev = next(s for s in sources.REMOTE_SOURCES if s.name == "models_dev")
    assert models_dev.writes_scores is False and models_dev.required is True


def test_the_pricing_credit_names_models_dev_and_its_licence() -> None:
    """covers REQ-ING-005 (D-194 clause 5): served models.dev prices are cited and credited."""
    from app.workflows import board_tables, rank

    citation = rank.attributions_for((), priced=True, pricing_sources={"litellm", "models_dev"})
    assert citation == (rank.PRICING_ATTRIBUTION,)
    assert "models.dev" in rank.PRICING_ATTRIBUTION and "OpenRouter" not in rank.PRICING_ATTRIBUTION
    assert [c["id"] for c in rank.credits_for(citation)] == ["litellm", "models_dev"]
    credit = board_tables.CREDITS["models_dev"]
    assert (credit.licence, credit.url) == ("MIT", "https://models.dev")
    assert "openrouter" not in board_tables.CREDITS


def test_a_model_another_maker_made_is_not_read_from_the_catalogue_that_resells_it() -> None:
    """covers REQ-ING-005 (#265): the live catalogue lists Zhipu's GLM under Mistral and Alibaba, and
    DeepSeek under Alibaba and NVIDIA. Read as the maker's price, each was a reseller's, and its route
    named the wrong vendor for the registry (`alibaba/glm-5.2`)."""
    catalogue = json.dumps({
        "alibaba": {"models": {
            "qwen3-32b": {"cost": {"input": 0.7, "output": 2.8}},
            "glm-5.2": {"cost": {"input": 1.4, "output": 4.4}},
            "deepseek-v4-flash-0731": {"cost": {"input": 0.2, "output": 0.4}},
        }},
        "mistral": {"models": {
            "mistral-large-3": {"cost": {"input": 2, "output": 6}},
            "zai-glm-5-2": {"cost": {"input": 1.4, "output": 4.4}},
        }},
        "nvidia": {"models": {
            "nemotron-ultra-4": {"cost": {"input": 0.6, "output": 1.8}},
            "deepseek-ai/deepseek-v4-flash": {"cost": {"input": 0.14, "output": 0.28}},
            "llama-3.3-nemotron-super-49b": {"cost": {"input": 0.1, "output": 0.4}},
        }},
    })
    rows, skipped = _client().parse_models_dev(catalogue)
    assert sorted(r.alias for r in rows) == ["alibaba/qwen3-32b", "mistral/mistral-large-3", "nvidia/nemotron-ultra-4"]
    assert skipped == 5


def test_the_makers_whose_models_only_openrouter_priced_are_read() -> None:
    """covers REQ-ING-005 (#265): measured against main's build of 2026-10-13, six served models lost
    their only price with OpenRouter. Four have a maker that sells them and that models.dev lists:
    Upstage (Solar), StepFun (Step) and Arcee (Trinity). Their routes name a vendor the registry knows."""
    from app.workflows import registry

    catalogue = json.dumps({
        "upstage": {"models": {"solar-pro4": {"cost": {"input": 0.3, "output": 1.2}}}},
        "stepfun": {"models": {"step-3.5-flash": {"cost": {"input": 0.1, "output": 0.3}}}},
        "arcee": {"models": {"trinity-large-thinking": {"cost": {"input": 0.25, "output": 0.8}}}},
    })
    rows, _ = _client().parse_models_dev(catalogue)
    assert sorted(r.alias for r in rows) == [
        "arcee-ai/trinity-large-thinking", "stepfun/step-3.5-flash", "upstage/solar-pro4"]
    assert [registry.route_vendor(r.alias.split("/")[0]) for r in sorted(rows, key=lambda r: r.alias)] == [
        "Arcee", "StepFun", "Upstage"]


def test_a_namespaced_model_in_a_makers_catalogue_is_another_publishers_and_a_bool_is_no_context() -> None:
    """covers REQ-ING-005 (the review's M3): the live catalogue lists Thinking Machines' model under Arcee as
    `thinkingmachines/inkling-small`, which names no family word; only its namespace keeps it out."""
    catalogue = json.dumps({"arcee": {"models": {
        "thinkingmachines/inkling-small": {"cost": {"input": 0.2, "output": 0.6}},
        "trinity-large-thinking": {"cost": {"input": 0.25, "output": 0.8}, "limit": {"context": True}},
    }}})
    rows, skipped = _client().parse_models_dev(catalogue)
    assert [(r.alias, r.context) for r in rows] == [("arcee-ai/trinity-large-thinking", None)] and skipped == 1
