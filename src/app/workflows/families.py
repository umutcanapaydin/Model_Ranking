"""Each surface's family of boards (M20-W1, D-188 clause 1, #209).

A family is every board that measures a surface's task, the primary first: the boards the phone
combines into the product's own list (M20-W2). The engine holds the only copy and publishes it on
`/v1/categories`; the phone reads it there and keeps none of its own.

A board stands in a family when it measures the task itself, and a family holds at most one board of
each source: Arena publishes slices of one vote (its text, vision and agent boards), and a board beside
its own slice would let that source outvote the others (the W1 review's M1). Two publishers of one
benchmark are two measurements (D-168 clause 5): SWE-bench's own board and Epoch's both stand in
`coding`. The boards that narrow a question instead (a language, a domain, another facet) stand outside
every family, each with its reason; the ones the app's refinement table names are added by the
question (D-168, M20-W3). A board may stand in two families: Terminal-Bench measures both agentic
coding and operating a computer.

Client-free: the serving process imports this module, so it imports nothing from `app.clients` (W-125).
"""

from __future__ import annotations

#: surface -> its family, the primary board first (`categories.CATEGORIES[surface].primary_source`).
FAMILIES: dict[str, tuple[str, ...]] = {
    "coding": ("swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"),
    "agentic-coding": ("epoch_deepswe_external", "epoch_terminalbench", "arena_agent"),
    "assistant": ("arena",),
    "everyday": ("epoch_eci", "arena", "epoch_mmlu"),
    "expert": ("epoch_gpqa", "arena_text_expert", "epoch_mmlu"),
    "mathematics": ("epoch_aime", "epoch_frontiermath", "epoch_frontiermath_t4", "arena_text_math"),
    "computer-use": ("epoch_terminalbench", "arena_agent"),
    "abstract": ("epoch_arc_agi", "epoch_chess", "epoch_mystery"),
    "web-dev": ("arena_webdev", "arena_text_coding"),
    "document": ("arena_document", "arena_text_longer_query"),
    "factuality": ("arena_factuality", "epoch_simpleqa"),
    "vision": ("arena_vision",),
    "search": ("arena_search",),
    "search_factuality": ("arena_search_factuality",),
}

#: surface -> the board a refinement takes the place of: the family's board of Arena's text vote. Every
#: refinement is a slice of that vote, so beside it one vote would count twice, for the coverage and for
#: the mean (the M20 repo review's M1; D-188 clauses 1 and 6). A surface no refinement refines has none.
REFINED_BOARD: dict[str, str] = {
    "assistant": "arena",
    "everyday": "arena",
    "expert": "arena_text_expert",
    "mathematics": "arena_text_math",
    "web-dev": "arena_text_coding",
    "document": "arena_text_longer_query",
    "factuality": "arena_factuality",
}

_LANGUAGE = "a language slice of Arena's text board: a refinement the question adds (D-168), not the task"
_VISION_LANGUAGE = "a language slice of Arena's vision board, which no refinement adds yet"
_TEXT_FACET = "a facet of Arena's text board, which stands in its families through `arena` or one slice"
_NO_LANGUAGE = "a slice of Arena's text board that names no one language a question could ask for"
_DOMAIN = "a domain slice of Arena's text board: a refinement the question adds (D-168), not the task"
_AGENT_FACET = "a facet of Arena's agent board, which stands in the family once through `arena_agent`"
_VISION_FACET = "a facet of Arena's vision board that names no surface's task"

#: board -> why it stands in no family.
OUTSIDE_FAMILIES: dict[str, str] = {
    "epoch_webdev": "Epoch's copy of LMArena's WebDev board, one vote with `arena_webdev`, which `web-dev` reads under its CC-BY grant (#185)",
    "arena_text_chinese": _LANGUAGE,
    "arena_text_english": _NO_LANGUAGE,
    "arena_text_french": _LANGUAGE,
    "arena_text_german": _LANGUAGE,
    "arena_text_japanese": _LANGUAGE,
    "arena_text_korean": _LANGUAGE,
    "arena_text_non_english": _NO_LANGUAGE,
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
    "arena_text_creative_writing": "creative writing: no surface measures it, and no refinement adds it yet",
    "arena_text_instruction_following": _TEXT_FACET,
    "arena_text_multi_turn": _TEXT_FACET,
    "arena_text_hard_prompts": _TEXT_FACET,
    "arena_vision_ocr": "a facet of Arena's vision board, which stands in `vision` itself",
    "arena_vision_diagram": "a facet of Arena's vision board, which stands in `vision` itself",
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
