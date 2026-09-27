//  Refinements.swift — the boards a question may add to its surface's own (D-168, M17-W5).
//
//  A question selects a surface, as it always has, and so the surface's primary board. When the
//  question concerns a language, a domain or a kind of conversation, a refinement adds one Arena
//  slice, at most two refinements in all. Every refinement is declared here, with the surfaces it
//  may refine and the reason; the on-device model may only choose among these values (D-104,
//  D-126), and `tests/unit/test_refinements.py` holds every entry against the boards the engine
//  serves.
//
//  The language is the language the TASK concerns, not the language the question is written in:
//  a question written in Turkish about Python adds no language board (D-168 clause 3).

import Foundation

/// The kinds of refinement, in the order their boards are added (D-168 clause 1).
enum RefinementKind: String, CaseIterable {
    case language
    case domain
    case kind
}

struct Refinement: Equatable, Hashable {
    /// What the on-device model's schema may emit for this refinement's kind.
    let value: String
    let kind: RefinementKind
    /// The board it adds, by its `/v1/boards` id.
    let board: String
    /// The surfaces it may refine. Any other surface ignores it.
    let surfaces: [String]
    let reason: String
}

enum Refinements {
    /// At most this many refinements join the surface's primary board (D-168 clause 1).
    static let maxAdded = 2

    static let table: [Refinement] = [
        Refinement(value: "english", kind: .language, board: "arena_text_english",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in English: how people rate answers in that language"),
        Refinement(value: "chinese", kind: .language, board: "arena_text_chinese",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Chinese: how people rate answers in that language"),
        Refinement(value: "french", kind: .language, board: "arena_text_french",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in French: how people rate answers in that language"),
        Refinement(value: "german", kind: .language, board: "arena_text_german",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in German: how people rate answers in that language"),
        Refinement(value: "japanese", kind: .language, board: "arena_text_japanese",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Japanese: how people rate answers in that language"),
        Refinement(value: "korean", kind: .language, board: "arena_text_korean",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Korean: how people rate answers in that language"),
        Refinement(value: "polish", kind: .language, board: "arena_text_polish",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Polish: how people rate answers in that language"),
        Refinement(value: "russian", kind: .language, board: "arena_text_russian",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Russian: how people rate answers in that language"),
        Refinement(value: "spanish", kind: .language, board: "arena_text_spanish",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts written in Spanish: how people rate answers in that language"),
        Refinement(value: "legal", kind: .domain, board: "arena_text_industry_legal_and_government",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about legal and government questions"),
        Refinement(value: "medicine", kind: .domain, board: "arena_text_industry_medicine_and_healthcare",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about medicine and healthcare questions"),
        Refinement(value: "business", kind: .domain, board: "arena_text_industry_business_and_management_and_financial_operations",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about business, management and finance questions"),
        Refinement(value: "software", kind: .domain, board: "arena_text_industry_software_and_it_services",
                   surfaces: ["assistant", "everyday", "document", "coding", "web-dev"],
                   reason: "Arena prompts about software and IT questions"),
        Refinement(value: "writing", kind: .domain, board: "arena_text_industry_writing_and_literature_and_language",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about writing, literature and language questions"),
        Refinement(value: "entertainment", kind: .domain, board: "arena_text_industry_entertainment_and_sports_and_media",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about entertainment, sports and media questions"),
        Refinement(value: "science", kind: .domain, board: "arena_text_industry_life_and_physical_and_social_science",
                   surfaces: ["assistant", "everyday", "document", "factuality", "expert"],
                   reason: "Arena prompts about life, physical and social science questions"),
        Refinement(value: "mathematical", kind: .domain, board: "arena_text_industry_mathematical",
                   surfaces: ["assistant", "everyday", "expert", "mathematics"],
                   reason: "Arena prompts about mathematical questions asked in conversation"),
        Refinement(value: "multi_turn", kind: .kind, board: "arena_text_multi_turn",
                   surfaces: ["assistant", "everyday"],
                   reason: "Arena prompts that are conversations of several turns"),
        Refinement(value: "longer_query", kind: .kind, board: "arena_text_longer_query",
                   surfaces: ["assistant", "everyday", "document"],
                   reason: "Arena prompts that are long prompts"),
        Refinement(value: "creative_writing", kind: .kind, board: "arena_text_creative_writing",
                   surfaces: ["assistant", "everyday"],
                   reason: "Arena prompts that are creative writing"),
        Refinement(value: "hard_prompts", kind: .kind, board: "arena_text_hard_prompts",
                   surfaces: ["assistant", "everyday", "expert"],
                   reason: "Arena prompts that are prompts people judged hard"),
        Refinement(value: "instruction_following", kind: .kind, board: "arena_text_instruction_following",
                   surfaces: ["assistant", "everyday", "document"],
                   reason: "Arena prompts that are prompts with explicit instructions to follow"),
        Refinement(value: "coding", kind: .kind, board: "arena_text_coding",
                   surfaces: ["coding", "web-dev", "agentic-coding"],
                   reason: "Arena prompts that are coding asked in conversation"),
        Refinement(value: "math", kind: .kind, board: "arena_text_math",
                   surfaces: ["mathematics"],
                   reason: "Arena prompts that are maths asked in conversation"),
        Refinement(value: "expert", kind: .kind, board: "arena_text_expert",
                   surfaces: ["expert"],
                   reason: "Arena prompts that are expert-level prompts"),
        Refinement(value: "ocr", kind: .kind, board: "arena_vision_ocr",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about reading text in an image"),
        Refinement(value: "diagram", kind: .kind, board: "arena_vision_diagram",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about understanding diagrams"),
        Refinement(value: "homework", kind: .kind, board: "arena_vision_homework",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about homework photographed or scanned"),
        Refinement(value: "captioning", kind: .kind, board: "arena_vision_captioning",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about describing an image"),
        Refinement(value: "entity_recognition", kind: .kind, board: "arena_vision_entity_recognition",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about recognising people, places and things in an image"),
        Refinement(value: "humor", kind: .kind, board: "arena_vision_humor",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about explaining humour in an image"),
        Refinement(value: "creative_writing_vision", kind: .kind, board: "arena_vision_creative_writing_vision",
                   surfaces: ["vision"],
                   reason: "Arena vision prompts about creative writing about an image"),
    ]

    /// The refinements a surface may take, in table order.
    static func allowed(for surface: String) -> [Refinement] {
        table.filter { $0.surfaces.contains(surface) }
    }

    /// The boards a question selects: the surface's primary board, then at most `maxAdded`
    /// refinements the surface allows, language before domain before kind, none chosen twice.
    static func boards(primary: String, surface: String, chosen: [Refinement]) -> [String] {
        var boards = [primary]
        var added = 0
        for kind in RefinementKind.allCases {
            for refinement in chosen where refinement.kind == kind && refinement.surfaces.contains(surface) {
                guard added < maxAdded, !boards.contains(refinement.board) else { continue }
                boards.append(refinement.board)
                added += 1
            }
        }
        return boards
    }
}
