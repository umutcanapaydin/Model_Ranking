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
        // Not `coding`: a coding request answers on two surfaces, neither the winner (Ruling A,
        // D-115), and a combined list would replace both (review B2, owner ruling 2026-09-28).
        Refinement(value: "software", kind: .domain, board: "arena_text_industry_software_and_it_services",
                   surfaces: ["assistant", "everyday", "document", "web-dev"],
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

    /// M20-W3 (#211, D-188): the boards a question combines: its surface's family, in the family's
    /// order, then at most `maxAdded` refinements the surface allows, language before domain, none
    /// twice. A family the engine did not send (an engine older than M20) is the caller's primary board.
    static func familyBoards(family: [String], surface: String, chosen: [Refinement]) -> [String] {
        var boards: [String] = []
        for board in family where !boards.contains(board) { boards.append(board) }
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

    /// M20-W3: the words that name a language the TASK concerns or a domain, for a device with no
    /// on-device model to choose the refinement (D-168 clause 3). Compared in plain letters (D-187), and
    /// only words with one reading: "Polish" is a language only as "in Polish" or its Turkish name,
    /// never polishing a photo; the Turkish word for business is not read, since in plain letters it
    /// is the English "is".
    static let refinementWords: [String: (stems: [String], words: [String], phrases: [[String]])] = [
        "chinese": (["cince"], ["chinese", "mandarin"], []),
        "french": (["fransizca"], ["french"], []),
        "german": (["almanca"], ["german"], []),
        "japanese": (["japonca"], ["japanese"], []),
        "korean": (["korece"], ["korean"], []),
        "polish": (["lehce"], [], [["in", "polish"], ["into", "polish"], ["polish", "language"]]),
        "russian": (["rusca"], ["russian"], []),
        "spanish": (["ispanyolca"], ["spanish"], []),
        "legal": (["hukuk", "avukat"], ["legal", "law", "lawyer", "lawyers"], []),
        "medicine": (["tibb", "saglik", "doktor"], ["medical", "medicine", "doctor", "doctors", "health",
                                                    "healthcare", "clinical"], []),
        "business": (["finans", "pazarlama", "muhasebe", "isletme"], ["business", "finance", "financial",
                                                                      "marketing", "accounting"], []),
        "software": (["yazilim"], ["software"], []),
        "writing": (["siir", "hikaye", "edebiyat", "kompozisyon"], ["writing", "essay", "novel", "poem",
                                                                    "poetry", "story", "stories", "literature"], []),
        "entertainment": (["muzik"], ["movie", "movies", "film", "films", "music", "sports", "sport"], []),
        "science": (["bilim", "fizik", "kimya", "biyoloji"], ["science", "scientific", "physics", "chemistry",
                                                              "biology"], []),
        "mathematical": (["matematik"], ["math", "maths", "mathematics", "mathematical"], []),
    ]

    /// The refinements a question's words name, in table order (languages, then domains).
    static func read(_ question: String) -> [Refinement] {
        let raw = question.lowercased()
        let readings = InputSignals.folds(question).map { InputSignals.wordsOf($0).map(CategoryHints.plain) }
        return table.filter { refinement in
            guard let entry = refinementWords[refinement.value] else { return false }
            return readings.contains { words in
                words.indices.contains { index in
                    let word = words[index]
                    guard entry.words.contains(word) || entry.stems.contains(where: word.hasPrefix) else { return false }
                    // A mother-in-law is no law, and science fiction (bilim kurgu) is no science.
                    if word == "law" && raw.contains("-in-law") { return false }
                    if word.hasPrefix("bilim") && index + 1 < words.count && words[index + 1].hasPrefix("kurgu") { return false }
                    return true
                } || entry.phrases.contains { phrase in
                    words.indices.contains { start in
                        start + phrase.count <= words.count
                            && phrase.indices.allSatisfy { words[start + $0] == phrase[$0] }
                    }
                }
            }
        }
    }

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
