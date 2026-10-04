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

    /// An attempt to instruct the model behind the text box, by the phrasings such attempts use, in
    /// both languages: "ignore your previous instructions", "you are now", "print your system
    /// prompt", "önceki talimatları unut", "sen artık". Each phrase is specific enough that a model
    /// search does not use it. Held by `ReadingTests`; a phrase added here is a reviewed edit.
    static func instructsTheApp(_ text: String) -> Bool {
        let folded = text.lowercased()
        return instructionPhrases.contains { folded.contains($0) }
    }

    static let instructionPhrases: [String] = [
        "ignore your", "ignore all", "ignore the previous", "ignore previous", "previous instructions",
        "system prompt", "your instructions", "your hidden", "you are now", "forget everything",
        "forget your", "stay in character", "reply with the single", "respond only with",
        "and nothing else", "new rule:", "talimat", "sistem komut", "sistem istem", "sen artık",
        "artık sen", "bundan sonra sadece", "kuralları bir kenara", "kuralları unut", "gizli ayar",
        "başka bir şey yazma", "yeni kural",
    ]

    /// A greeting, thanks or small talk, and nothing else ("hi", "how are you", "ok", "selam",
    /// "nasılsın", "test test 123"): every word is one of these, and there are at most six.
    static func smallTalk(_ text: String) -> Bool {
        let words = text.lowercased().split { !$0.isLetter }.map(String.init)
        guard (1...6).contains(words.count) else { return false }
        return words.allSatisfy(smallTalkWords.contains)
    }

    static let smallTalkWords: Set<String> = [
        "hi", "hello", "hey", "hiya", "yo", "sup", "thanks", "thank", "you", "thx", "ok", "okay", "cool",
        "nice", "great", "lol", "haha", "bye", "good", "morning", "evening", "night", "how", "are",
        "doing", "today", "test", "testing", "selam", "merhaba", "mrb", "slm", "nasılsın", "naber",
        "teşekkürler", "teşekkür", "ederim", "sağol", "sağ", "ol", "tamam", "peki", "günaydın", "iyi",
        "geceler", "akşamlar", "görüşürüz",
    ]

    /// #113 (M18-W3): a request to MAKE or CHANGE an image, which nothing here measures: `vision`
    /// measures reading one. The on-device model sent these to `vision` even when told not to (0 of
    /// 6 on the tuning set), so the line is drawn here: a verb that makes or changes followed,
    /// within three words, by an image, or "draw"/"çiz" alone. Held by `ReadingTests`.
    static func makesAnImage(_ text: String) -> Bool {
        let words = text.lowercased().split { !$0.isLetter }.map(String.init)
        if words.contains(where: { $0 == "draw" || $0.hasPrefix("çiz") || $0 == "sketch" }) { return true }
        for (index, word) in words.enumerated() where imageVerbs.contains(where: { word.hasPrefix($0) }) {
            let near = words.dropFirst(index + 1).prefix(3) + words.prefix(index).suffix(3)
            if near.contains(where: { candidate in imageNouns.contains { candidate.hasPrefix($0) } }) { return true }
        }
        return false
    }

    private static let imageVerbs = [
        "generate", "create", "make", "design", "edit", "retouch", "remove", "turn", "paint", "illustrate",
        "fix", "enhance", "restore", "colorize", "colourise", "brighten", "sharpen",
        "oluştur", "yap", "tasarla", "düzenle", "rötuş", "kaldır", "sil", "üret", "düzelt",
        "netleştir", "renklendir",
    ]
    private static let imageNouns = [
        "image", "picture", "photo", "logo", "illustration", "avatar", "drawing", "poster", "icon",
        "wallpaper", "selfie", "background", "resim", "görsel", "fotoğraf", "logo", "illüstrasyon",
        "afiş", "ikon", "simge", "arka", "avatar", "portre", "portrait",
    ]

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

/// D-169 as amended at M18-W3: the reading, from the signals in code and the model's verdict.
///
/// - `noWord` decides alone: there is nothing to route. So do an instruction to the app and small
///   talk, read in code (`certain`).
/// - The model's "not a search" and pasted content together decide it is not a search.
/// - Either one alone is a doubt, and the reader is asked.
/// - `modelSaysNotASearch` is `nil` where no model read the question (another tier answered).
func inputReading(noWord: Bool, pasted: Bool, modelSaysNotASearch: Bool?, certain: Bool = false) -> InputReading {
    if noWord || certain { return .notASearch }
    switch (modelSaysNotASearch ?? false, pasted) {
    case (true, true): return .notASearch
    case (true, false), (false, true): return .unsure
    case (false, false): return .search
    }
}
