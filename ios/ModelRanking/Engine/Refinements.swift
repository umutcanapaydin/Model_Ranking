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
    /// The most boards a family may bring; the largest served family has five (`families.py`).
    static let maxFamily = 16

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
    /// order and none twice, then at most `maxAdded` refinements the surface allows, language before
    /// domain. A refinement the family already holds takes none of the places. A family the engine did
    /// not send (an engine older than M20) is the primary board alone.
    static func familyBoards(primary: String, family: [String], surface: String, chosen: [Refinement],
                             refined: String? = nil) -> [String] {
        // One pass with a set, and no more than `maxFamily` boards: a broken payload's family of
        // thousands neither freezes the screen nor builds a list from all of them (the M20 closure
        // security seat's S3).
        var boards: [String] = []
        var seen = Set<String>()
        for board in family.isEmpty ? [primary] : family where boards.count < maxFamily && seen.insert(board).inserted {
            boards.append(board)
        }
        let allowed = RefinementKind.allCases.flatMap { kind in
            chosen.filter { $0.kind == kind && $0.surfaces.contains(surface) }
        }
        // The M20 repo review's M1 (D-188 clause 6): every refinement is a slice of Arena's text vote,
        // so the first one allowed takes the place of the family's board of that vote, and no other
        // joins: one vote, one board. An engine that names no such board keeps the older way.
        if let refined, let index = boards.firstIndex(of: refined) {
            if let first = allowed.first(where: { !boards.contains($0.board) }) { boards[index] = first.board }
            return boards
        }
        var added = 0
        for refinement in allowed {
            guard added < maxAdded, !boards.contains(refinement.board) else { continue }
            boards.append(refinement.board)
            added += 1
        }
        return boards
    }

    /// The words that name one refinement. `stems` match the start of a word and `words` the whole
    /// word; `names` are English language names, read only as the language of a task (`namesLanguage`).
    struct Words {
        var stems: [String] = []
        var words: [String] = []
        var names: [String] = []
    }

    /// M20-W3: the words that name a language the TASK concerns or a domain, for a question the
    /// on-device model did not read (D-168 clause 3, D-188 clause 6). Compared in plain letters (D-187),
    /// and only words with one reading (the W3 review's M1 to M3):
    /// - an English language name is also a nationality or a country's ("french fries", "the Korean
    ///   war", "German cars"), so it counts only beside a word that makes it a language; the Turkish
    ///   names ("Almanca") are only languages, except the one for Polish, which is also "dialect";
    /// - a domain word a reader also uses for something else is left out: law (Moore's), health (a
    ///   battery's), a novel approach, user stories, a thin film, a PhD ("doktora"), a healthy recipe;
    /// - the Turkish word for business is not read, since in plain letters it is the English "is".
    static let refinementWords: [String: Words] = [
        "chinese": Words(stems: ["cince"], names: ["chinese", "mandarin"]),
        "french": Words(stems: ["fransizca"], names: ["french"]),
        "german": Words(stems: ["almanca"], names: ["german"]),
        "japanese": Words(stems: ["japonca"], names: ["japanese"]),
        "korean": Words(stems: ["korece"], names: ["korean"]),
        "polish": Words(names: ["polish"]),
        "russian": Words(stems: ["rusca"], names: ["russian"]),
        "spanish": Words(stems: ["ispanyolca"], names: ["spanish"]),
        "legal": Words(stems: ["hukuk", "avukat"], words: ["legal", "lawyer", "lawyers"]),
        "medicine": Words(stems: ["tibb"], words: ["medical", "medicine", "doctor", "doctors", "healthcare", "clinical",
                                                   "doktor", "doktorlar", "doktoru", "saglik"]),
        // The noun's forms only: the stem also starts the verb "to operate" (a server).
        "business": Words(stems: ["finans", "pazarlama", "muhasebe"],
                           words: ["business", "finance", "financial", "marketing", "accounting", "isletme",
                                   "isletmesi", "isletmeler", "isletmeleri", "isletmem", "isletmemiz", "isletmemin",
                                   "isletmeye", "isletmede", "isletmenin"]),
        "software": Words(stems: ["yazilim"], words: ["software"]),
        "writing": Words(stems: ["siir", "hikaye", "edebiyat", "kompozisyon"],
                         words: ["writing", "essay", "essays", "novels", "poem", "poems", "poetry", "literature"]),
        "entertainment": Words(stems: ["muzik"], words: ["movie", "movies", "music", "sports", "sport"]),
        "science": Words(stems: ["bilim", "kimya", "biyoloji"],
                         words: ["science", "scientific", "physics", "chemistry", "biology", "fizik", "fizigi",
                                 "fizikte", "fizikten", "fizikle"]),
        "mathematical": Words(stems: ["matematik"], words: ["math", "maths", "mathematics", "mathematical"]),
    ]

    /// A language name counts before one of `languageAfter` ("Japanese language", "Korean
    /// translation"), or after one of `languageBefore` ("in French", "learn Spanish") or after "to" or
    /// "from" in a question that asks to translate ("translate from Korean"), when it ends the question
    /// or one of `languageEnds` follows it: "in Chinese stocks" and "French cuisine" are no language
    /// (the second round's M1), and a Chinese speaker is a person or a loudspeaker.
    static let languageBefore: Set<String> = ["in", "into", "learn", "learning", "speak", "speaking"]
    static let languageAfter: Set<String> = ["language", "translation", "translations", "translator"]
    static let languageEnds: Set<String> = ["please", "and", "or", "too", "only", "with", "for", "so", "because", "as",
                                            "to", "from", "fluently", "well", "better", "properly", "correctly",
                                            "instead", "now", "languages", "text", "texts"]
    static let translating: Set<String> = ["translate", "translates", "translating", "translation", "translator"]

    /// A matched word after one of these, or before one of these, is something else: data or computer
    /// science, science fiction (one word or two), physical therapy, writing code, an AI's software, a
    /// server's or a battery's health (the Turkish word before a check or a status). A trailing `*` reads a word by
    /// its start.
    static let notAfter: [String: Set<String>] = [
        "science": ["data", "computer"], "scientific": ["data", "computer"], "bilim": ["veri", "bilgisayar"],
        "hikaye": ["kullanici"],
        // AI software is the AI itself, as the router reads it (`CategoryHints.notAfter`).
        "software": ["ai", "zeka", "chatbot"], "yazilim": ["zeka"],
    ]
    static let notBefore: [String: [String]] = [
        "science": ["fiction"], "bilim": ["kurgu*"], "fizik": ["tedavi*"], "doctor": ["who"],
        "saglik": ["kontrol*", "durum*"],
        "writing": ["code", "codes", "tests", "scripts", "sql", "queries", "functions"],
    ]
    static let notStarting = ["bilimkurgu"]

    /// The refinements a question's words name: at most one of each kind, as the on-device model's
    /// schema has one field per kind (the second round's M2), each the first the question names; the
    /// language first.
    static func read(_ question: String) -> [Refinement] {
        let readings = CategoryHints.readings(question)
        // Where each refinement is first named, in either reading. No order is computed: the first of
        // each kind is found by one pass (the client orders nothing of its own, Ruling A's tripwire).
        var firstOfKind: [RefinementKind: (refinement: Refinement, at: Int)] = [:]
        for refinement in table {
            guard let entry = refinementWords[refinement.value] else { continue }
            for words in readings {
                let at = words.indices.first { index in
                    entry.names.contains { namesLanguage($0, words, at: index) } || matches(entry, words, at: index)
                }
                if let at, at < (firstOfKind[refinement.kind]?.at ?? Int.max) {
                    firstOfKind[refinement.kind] = (refinement, at)
                }
            }
        }
        return RefinementKind.allCases.compactMap { firstOfKind[$0]?.refinement }
    }

    private static func namesLanguage(_ name: String, _ words: [String], at index: Int) -> Bool {
        guard words[index] == name else { return false }
        let before = index > 0 ? words[index - 1] : "", after = index + 1 < words.count ? words[index + 1] : ""
        if languageAfter.contains(after) { return true }
        let asks = languageBefore.contains(before)
            || ((before == "to" || before == "from") && words.contains(where: translating.contains))
        return asks && (after.isEmpty || languageEnds.contains(after))
    }

    private static func matches(_ entry: Words, _ words: [String], at index: Int) -> Bool {
        let word = words[index]
        guard !notStarting.contains(where: word.hasPrefix),
              let matched = entry.words.first(where: { $0 == word }) ?? entry.stems.first(where: word.hasPrefix)
        else { return false }
        if index > 0, let blocked = notAfter[matched], blocked.contains(words[index - 1]) { return false }
        if index + 1 < words.count, let blocked = notBefore[matched] {
            let next = words[index + 1]
            if blocked.contains(where: { $0.hasSuffix("*") ? next.hasPrefix(String($0.dropLast())) : next == $0 }) {
                return false
            }
        }
        return true
    }

    /// The refinements a surface may take, in table order.
    static func allowed(for surface: String) -> [Refinement] {
        table.filter { $0.surfaces.contains(surface) }
    }

    /// The boards a question selects with no family: the surface's primary board, then at most
    /// `maxAdded` refinements the surface allows, language before domain, none chosen twice.
    static func boards(primary: String, surface: String, chosen: [Refinement]) -> [String] {
        familyBoards(primary: primary, family: [primary], surface: surface, chosen: chosen)
    }
}
