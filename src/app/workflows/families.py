"""Each surface's family of boards (M20-W1, D-188 clause 1, #209).

A family is every board that measures a surface's task, the primary first: the boards the phone
combines into the product's own list (M20-W2). The engine holds the only copy and publishes it on
`/v1/categories`; the phone reads it there and keeps none of its own.

A board stands in a family when it measures the task itself. The boards that narrow a question
instead (a language, a domain, a facet of one board) stand outside every family, each with its
reason: the question adds them as refinements (D-168, M20-W3), and counting them in a family would
let one source's facets outvote the others. A board may stand in two families: Terminal-Bench measures
both agentic coding and operating a computer.

Client-free: the serving process imports this module, so it imports nothing from `app.clients` (W-125).
"""

from __future__ import annotations

#: surface -> its family, the primary board first (`categories.CATEGORIES[surface].primary_source`).
FAMILIES: dict[str, tuple[str, ...]] = {
    "coding": ("swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"),
    "agentic-coding": ("epoch_deepswe_external", "epoch_terminalbench", "arena_agent"),
    "assistant": ("arena", "arena_text_instruction_following", "arena_text_multi_turn"),
    "everyday": ("epoch_eci", "arena", "arena_text_hard_prompts"),
    "expert": ("epoch_gpqa", "arena_text_expert", "epoch_mmlu"),
    "mathematics": ("epoch_aime", "epoch_frontiermath", "epoch_frontiermath_t4", "arena_text_math"),
    "computer-use": ("epoch_terminalbench", "arena_agent"),
    "abstract": ("epoch_arc_agi", "epoch_chess", "epoch_mystery"),
    "web-dev": ("epoch_webdev", "arena_text_coding"),
    "document": ("arena_document", "arena_text_longer_query"),
    "factuality": ("arena_factuality", "epoch_simpleqa"),
    "vision": ("arena_vision", "arena_vision_ocr", "arena_vision_diagram"),
    "search": ("arena_search", "arena_search_factuality"),
    "search_factuality": ("arena_search_factuality", "arena_search"),
}

_LANGUAGE = "a language slice of Arena's text board: a refinement the question adds (D-168), not the task"
_VISION_LANGUAGE = "a language slice of Arena's vision board: a refinement, not the task"
_DOMAIN = "a domain slice of Arena's text board: a refinement the question adds (D-168), not the task"
_AGENT_FACET = "a facet of Arena's agent board, which stands in the family once through `arena_agent`"
_VISION_FACET = "a facet of Arena's vision board that names no surface's task"

#: board -> why it stands in no family.
OUTSIDE_FAMILIES: dict[str, str] = {
    "arena_text_chinese": _LANGUAGE,
    "arena_text_english": _LANGUAGE,
    "arena_text_french": _LANGUAGE,
    "arena_text_german": _LANGUAGE,
    "arena_text_japanese": _LANGUAGE,
    "arena_text_korean": _LANGUAGE,
    "arena_text_non_english": _LANGUAGE,
    "arena_text_polish": _LANGUAGE,
    "arena_text_russian": _LANGUAGE,
    "arena_text_spanish": _LANGUAGE,
    "arena_vision_chinese": _VISION_LANGUAGE,
    "arena_vision_english": _VISION_LANGUAGE,
    "arena_text_industry_business_and_management_and_financial_operations": _DOMAIN,
    "arena_text_industry_entertainment_and_sports_and_media": _DOMAIN,
    "arena_text_industry_legal_and_government": _DOMAIN,
    "arena_text_industry_life_and_physical_and_social_science": _DOMAIN,
    "arena_text_industry_mathematical": _DOMAIN,
    "arena_text_industry_medicine_and_healthcare": _DOMAIN,
    "arena_text_industry_software_and_it_services": _DOMAIN,
    "arena_text_industry_writing_and_literature_and_language": _DOMAIN,
    "arena_text_creative_writing": "creative writing: no surface measures it; a refinement where a question asks for it",
    "arena_agent_bash_recovery_steps": _AGENT_FACET,
    "arena_agent_praise_complaint": _AGENT_FACET,
    "arena_agent_steerability": _AGENT_FACET,
    "arena_agent_task_outcome_explicit": _AGENT_FACET,
    "arena_agent_tool_hallucination": _AGENT_FACET,
    "arena_vision_captioning": _VISION_FACET,
    "arena_vision_creative_writing_vision": _VISION_FACET,
    "arena_vision_entity_recognition": _VISION_FACET,
    "arena_vision_homework": _VISION_FACET,
    "arena_vision_humor": _VISION_FACET,
}
