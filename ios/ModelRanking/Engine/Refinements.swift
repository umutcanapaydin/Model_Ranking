//  Refinements.swift — the boards a question may add to its surface's own (D-168, M17-W5).
//
//  A question selects a surface, as it always has, and so the surface's primary board. When the
//  question concerns a language or a domain, a refinement adds one Arena slice, at most two in all. Every refinement is declared here, with the surfaces it
//  may refine and the reason; the on-device model may only choose among these values (D-104,
//  D-126), and `tests/unit/test_refinements.py` holds every entry against the boards the engine
//  serves.
//
//  The language is the language the TASK concerns, not the language the question is written in:
//  a question written in Turkish about Python adds no language board (D-168 clause 3).
//
//  Measured before merge (docs/research/m17-w5-refinement-probe-2026-09-28.md): English as a task
//  language, and every "kind" of conversation or image task, were added by the on-device model to
//  most questions they do not describe, each a board that shortens the list (D-167 clause 3). They
//  are left out; every value here is one a question either clearly names or does not.

import Foundation

/// The kinds of refinement, in the order their boards are added (D-168 clause 1). A "kind" of
/// conversation or image task was a third, until the probe showed the on-device model adding one to
/// most questions it does not describe (owner ruling 2026-09-28, D-168 note).
enum RefinementKind: String, CaseIterable {
    case language
    case domain
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
    ]

    /// The refinements a surface may take, in table order.
    static func allowed(for surface: String) -> [Refinement] {
        table.filter { $0.surfaces.contains(surface) }
    }

    /// The boards a question selects: the surface's primary board, then at most `maxAdded`
    /// refinements the surface allows, language before domain, none chosen twice.
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
