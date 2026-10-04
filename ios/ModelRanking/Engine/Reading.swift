//  Reading.swift — whether what was typed is a search for a model at all (D-169, amended M18-W3).
//
//  Some input states no need: an attempt to instruct the model, chit-chat or nonsense, a knowledge
//  question, or content pasted in for the app to act on. Measured in M17, the on-device model alone
//  could not tell those from the product's normal input. M18 holds the line with two signals
//  decided here, in code, and tested, combined with the model's own reading. Where the two disagree,
//  the reader is asked rather than decided for.

import Foundation

/// How the app reads what was typed.
enum InputReading: Equatable {
    /// A search for a model: routed and answered as always.
    case search
    /// Not a search for a model: a guiding note, no ranking, no request, no gap entry.
    case notASearch
    /// One sign says it is not a search and the other does not: the reader is asked, in one tap.
    case unsure
}

/// The signals decided in code. They read the text only, so they run on every tier, model or not.
enum InputSignals {
    /// Text with no word in any language: keyboard runs ("asdf qwer"), one letter repeated
    /// ("aaaa"), letters with no vowel ("sdfsdf"), or nothing but digits and punctuation. Fewer than
    /// four letters decides nothing ("ok", "zzz"): too little to read in code.
    static func noWord(_ text: String) -> Bool {
        let letters = text.filter(\.isLetter)
        if letters.isEmpty { return !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        guard letters.count >= 4 else { return false }
        let tokens = text.lowercased().split { !$0.isLetter }.map(String.init)
        return !tokens.contains(where: isWord)
    }

    /// Content pasted in to be acted on now: three or more lines, a code block, or a short
    /// instruction to act ("translate into Spanish:", "şunu düzelt:") followed by a colon and the
    /// content. A question that only contains a colon, such as an error line pasted into a question
    /// about code ("TypeError: …"), is not pasted content by this rule.
    static func pastedContent(_ text: String) -> Bool {
        let lines = text.split(whereSeparator: \.isNewline).filter {
            !$0.trimmingCharacters(in: .whitespaces).isEmpty
        }
        if lines.count >= 3 || text.contains("```") { return true }
        guard let colon = text.firstIndex(of: ":") else { return false }
        let before = text[..<colon].lowercased()
        let after = text[text.index(after: colon)...].trimmingCharacters(in: .whitespacesAndNewlines)
        let words = before.split { !$0.isLetter }.map(String.init)
        guard (1...8).contains(words.count), after.count >= 2 else { return false }
        return words.contains { word in actVerbs.contains { word == $0 || (word.hasPrefix($0) && $0.count >= 4) } }
    }

    /// The verbs that ask the app to do something to text it is given, in both languages. A Turkish
    /// verb is matched by its stem, so "çevir", "çevirir misin" and "düzeltir misin" all count.
    /// Held by `ReadingTests`; a verb added here is a reviewed edit.
    static let actVerbs: Set<String> = [
        "translate", "fix", "summarize", "summarise", "rewrite", "correct", "proofread", "convert",
        "explain", "answer", "solve", "calculate", "compute", "debug", "refactor", "rephrase",
        "paraphrase", "shorten", "improve", "edit", "write",
        "çevir", "tercüme", "düzelt", "özetle", "açıkla", "cevapla", "yanıtla", "hesapla", "dönüştür",
        "çöz", "kısalt", "iyileştir", "yaz",
    ]

    /// A word, in any language: letters from a script beyond Latin (Cyrillic, Greek, Arabic, CJK and
    /// the rest) are always words here; a Latin token is a word when it has a vowel, is not one letter
    /// repeated or two letters alternating, and is not a run along a keyboard row.
    private static func isWord(_ token: String) -> Bool {
        if token.unicodeScalars.contains(where: { $0.value > 0x024F }) { return true }
        let distinct = Set(token)
        if token.count >= 2, distinct.count <= (token.count >= 4 ? 2 : 1) { return false }
        guard token.contains(where: { vowels.contains($0) }) else { return false }
        return !(token.count >= 4 && keyboardRows.contains { $0.contains(token) })
    }

    private static let vowels: Set<Character> = Set("aeiouyáàâäãåæéèêëíìîïóòôöõøúùûüıœ")

    /// Each row of the US and Turkish Q keyboards, both ways.
    private static let keyboardRows: [String] = {
        let rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "qwertyuıopğü", "asdfghjklşi", "zxcvbnmöç"]
        let backwards = rows.map { row in String(row.reversed()) }
        return rows + backwards
    }()
}

/// D-169 as amended at M18-W3: the reading, from the two code signals and the model's verdict.
///
/// - `noWord` decides alone: there is nothing to route.
/// - The model's "not a search" and pasted content together decide it is not a search.
/// - Either one alone is a doubt, and the reader is asked.
/// - `modelSaysNotASearch` is `nil` where no model read the question (another tier answered).
func inputReading(noWord: Bool, pasted: Bool, modelSaysNotASearch: Bool?) -> InputReading {
    if noWord { return .notASearch }
    switch (modelSaysNotASearch ?? false, pasted) {
    case (true, true): return .notASearch
    case (true, false), (false, true): return .unsure
    case (false, false): return .search
    }
}
