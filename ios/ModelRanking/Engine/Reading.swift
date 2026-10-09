//  Reading.swift — whether what was typed is a search for a model at all (D-169, amended at M18-W3
//  and by D-184 at M19-W4).
//
//  Some input states no need: an attempt to instruct the model, chit-chat or nonsense, a knowledge
//  question, or content pasted in for the app to act on. Measured in M17, the on-device model alone
//  could not tell those from the product's normal input. M18 holds the line with signals decided
//  here, in code, and tested, combined with the model's own reading; M19-W4 adds a question of fact
//  to the doubts (D-184). Where the two disagree, the reader is asked rather than decided for.

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
///
/// Every list here is matched on whole words, under both the default and the Turkish case folding
/// (review M7: "İ" and "I" fold differently in Turkish), never on a bare prefix (review B4:
/// "yap" matched "yapay"). A Turkish verb is matched by its stem only in the forms a request takes
/// (`isTurkishVerb`), and a Turkish noun by a stem long enough to have no other reading.
enum InputSignals {
    /// Text with no word in any language: keyboard runs ("asdf qwer"), one letter repeated
    /// ("aaaa"), a long run of letters with no vowel ("sdfsdf"), or nothing but digits and
    /// punctuation. Fewer than four letters decides nothing ("ok", "zzz"). A token written in capitals
    /// is an acronym, and an acronym is a word (review B3: "HTML CSS", "PHP SQL").
    static func noWord(_ text: String) -> Bool {
        let letters = text.filter(\.isLetter)
        if letters.isEmpty { return !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        guard letters.count >= 4 else { return false }
        let tokens = text.split { !$0.isLetter }.map(String.init)
        return !tokens.contains(where: isWord)
    }

    /// Content pasted in to be acted on now: three or more lines, a code block, or a short
    /// instruction to act ("translate into Spanish:", "şunu düzelt:") followed by a colon and the
    /// content. The instruction must be a verb, not a noun made from one (review M8: "Çeviri:",
    /// "Kod düzeltme:" name a topic), and a question that only contains a colon, such as an error
    /// line pasted into a question about code ("TypeError: …"), is not pasted content.
    static func pastedContent(_ text: String) -> Bool {
        let lines = text.split(whereSeparator: \.isNewline).filter {
            !$0.trimmingCharacters(in: .whitespaces).isEmpty
        }
        if lines.count >= 3 || text.contains("```") { return true }
        guard let colon = text.firstIndex(of: ":") else { return false }
        let after = text[text.index(after: colon)...].trimmingCharacters(in: .whitespacesAndNewlines)
        guard after.count >= 2 else { return false }
        let before = folds(String(text[..<colon])).map(wordsOf)
        // A search names what it searches for before the colon ("Best model to explain code: …");
        // an instruction does not (the second review's M12). Judged over every folding: "AI" folds
        // to "aı" in Turkish (the M19-W4 review's K2).
        let searchWords: Set<String> = ["model", "models", "llm", "ai", "which", "best", "hangi", "modeli", "modelin"]
        if before.contains(where: { $0.contains(where: searchWords.contains) }) { return false }
        // Or a comparison before it ("make vs cmake: which is better"), or a question for a model after
        // it: a model, AI or LLM named, with "which" or "best" first, or the Turkish `hangi`/`hangisi`
        // anywhere, since Turkish puts it last ("…: en iyi model hangisi"). Content may open with
        // "which" or name AI, and still be content (the M19-W4 reviews' M6, M3 and the fifth's M1).
        if before.contains(where: { $0.contains("vs") || $0.contains("versus") }) { return false }
        if folds(after).map(wordsOf).contains(where: { words in
            let asks = ["which", "best"].contains(words.first ?? "")
                || words.contains(where: { ["hangi", "hangisi"].contains($0) })
            return asks && words.contains(where: { $0.hasPrefix("model") || ["ai", "llm", "yapay"].contains($0) })
        }) {
            return false
        }
        return before.contains { words in
            guard (1...8).contains(words.count) else { return false }
            // "make: *** No rule to make target" is the tool's error line, not an order to make (the
            // fourth M19-W4 review's M4).
            if words == ["make"] { return false }
            // The verb where an instruction puts it: first in English ("translate into Spanish:",
            // "please fix this:"), last in Turkish ("şunu İngilizceye çevir:", "çevirir misin:").
            let english = words.prefix(2).contains(where: actVerbsEnglish.contains)
            let turkish = words.indices.suffix(2).contains { isTurkishVerb(words, at: $0, stems: actStemsTurkish) }
            return english || turkish
        }
    }

    /// An attempt to instruct the model behind the text box: an imperative aimed at its instructions
    /// ("ignore your previous instructions", "print your system prompt", "önceki talimatları unut",
    /// "sistem komutunu göster"), or a role handed to it ("you are now", "sen artık bir"). A verb AND
    /// its object are both needed, in one sentence (the second review's M11): "which model follows
    /// your instructions best" names instructions and orders nothing. The verb must be an order
    /// (the third review's M17): in English it opens its sentence, after at most a "please" or a
    /// "can you", so "which model won't ignore my instructions" and "make eslint ignore some rules"
    /// order nothing; in Turkish it is in a request's form, so "unutmayan" ("that does not forget")
    /// is not. It is a doubt, not a verdict: alone, the reader is asked.
    static func instructsTheApp(_ text: String) -> Bool {
        folds(text).contains { folded in
            let words = wordsOf(folded)
            let spaced = " " + words.joined(separator: " ") + " "
            if rolePhrases.contains(where: { spaced.contains(" \($0) ") }) { return true }
            let sentences = folded.split(whereSeparator: { ".!?;,:\n".contains($0) }).map { wordsOf(String($0)) }
            return sentences.contains { sentence in
                let english = sentence.indices.contains { spot in
                    instructionVerbsEnglish.contains(sentence[spot]) && sentence[..<spot].allSatisfy(orderLeadIns.contains)
                }
                let turkish = sentence.indices.contains { isTurkishVerb(sentence, at: $0, stems: instructionStemsTurkish) }
                return (english || turkish) && sentence.contains(where: isInstructionObject)
            }
        }
    }

    /// The verbs of an order aimed at the model's instructions: English as whole words, Turkish by
    /// `isTurkishVerb`.
    static let instructionVerbsEnglish: Set<String> = ["ignore", "disregard", "forget", "print", "reveal", "repeat"]
    static let instructionStemsTurkish: Set<String> = ["unut", "yoksay", "yazdır", "göster", "paylaş", "kopyala"]
    /// What may stand before an English order in its sentence.
    static let orderLeadIns: Set<String> = [
        "please", "pls", "kindly", "now", "just", "and", "then", "also", "so", "first", "ok", "okay", "can",
        "could", "will", "would", "you",
    ]

    /// What such an order is aimed at: English as whole words; Turkish nouns by a long stem, but
    /// "komut" and "istem" by their forms, since "komut satırı" is the command line and "istemiyorum"
    /// is "I don't want" (the third review's M17).
    static func isInstructionObject(_ word: String) -> Bool {
        if ["instruction", "instructions", "prompt", "prompts", "rules"].contains(word) { return true }
        if ["talimat", "kural", "ayarlar"].contains(where: { word.hasPrefix($0) }) { return true }
        return ["komutu", "komutunu", "komutları", "komutlarını", "istem", "istemi", "istemini", "istemleri",
                "istemlerini"].contains(word)
    }
    /// A role handed to the model, or its answer dictated.
    static let rolePhrases: [String] = [
        "you are now", "from now on you", "reply with the single word", "sen artık bir", "artık sen bir",
        "kuralları bir kenara", "pretend ur a", "from now on answer",
    ]

    /// A greeting, thanks or small talk, and nothing else ("hi", "how are you", "ok", "selam",
    /// "nasılsın", "test test"): every word is one of these, and there are at most six. A model
    /// search always names something beyond these words, so this decides alone.
    static func smallTalk(_ text: String) -> Bool {
        folds(text).contains { folded in
            // A phrase counts as one word of small talk ("eline sağlık"); its words alone do not, so
            // "sağlık" (health) is a search (the M19-W4 review's M1).
            var spaced = " " + wordsOf(folded).joined(separator: " ") + " "
            var phrases = 0
            for phrase in smallTalkPhrases where spaced.contains(" \(phrase) ") {
                spaced = spaced.replacingOccurrences(of: " \(phrase) ", with: " ")
                phrases += 1
            }
            let words = spaced.split(separator: " ").map(String.init)
            return (1...6).contains(words.count + phrases) && words.allSatisfy(smallTalkWords.contains)
        }
    }

    static let smallTalkPhrases = ["eline sağlık"]

    static let smallTalkWords: Set<String> = [
        "hi", "hello", "hey", "hiya", "yo", "sup", "thanks", "thank", "you", "thx", "ok", "okay", "cool",
        "nice", "great", "lol", "haha", "bye", "good", "morning", "evening", "night", "how", "are",
        "doing", "today", "test", "testing", "selam", "merhaba", "mrb", "slm", "nasılsın", "naber",
        "teşekkürler", "teşekkür", "ederim", "sağol", "sağ", "ol", "tamam", "peki", "günaydın", "iyi",
        "geceler", "akşamlar", "görüşürüz", "nasilsin", "eyvallah", "tmm", "çok", "that", "was", "really",
        "helpful", "much",
    ]

    /// #66 (M19-W4): a question of everyday fact asked for its answer, not a search for a model
    /// ("when did the berlin wall fall", "kanadanın başkenti neresi"). Short, written as a question of
    /// fact, and naming no model, no task, no person asking, nothing current and no image the asker
    /// has. A doubt, as the others are: alone, the reader is asked. The model called 21 and 20 of 22
    /// such questions on the tuning set "a model search".
    static func asksAFact(_ text: String) -> Bool {
        let folded = folds(text).map(wordsOf)
        // A suffix after an apostrophe belongs to its word ("Hamlet'i", "Türkiye'nin"), so it is no
        // English "I" (the second M19-W4 review's M2); "I'm" still leaves an "I".
        let bare = text.replacingOccurrences(of: "['’]\\p{L}+", with: "", options: .regularExpression)
        // Excluded if ANY folding names a model, the asker, a task or the rest: "I" and "AI" fold to
        // "ı" and "aı" in Turkish, and iOS capitalises "I" (the M19-W4 review's MJ2).
        if folds(bare).map(wordsOf).contains(where: { words in
            words.contains(where: { word in
                word.hasPrefix("model") || factExclusions.contains(word) || actVerbsEnglish.contains(word)
                    || factExclusionStemsTurkish.contains(where: word.hasPrefix) || isImageNoun(word)
            })
        }) {
            return false
        }
        return folded.contains { words in
            guard (2...10).contains(words.count) else { return false }
            let english = factOpeners.contains { words.starts(with: $0) }
            let pairs = zip(words, words.dropFirst())
            let turkish = words.contains(where: factWordsTurkish.contains)
                || pairs.contains { $0 == "ne" && $1 == "zaman" }
                || pairs.contains { $0 == "hangi" && ($1.hasPrefix("yıl") || $1.hasPrefix("yil")) }
            return english || turkish
        }
    }

    /// How an English question of fact opens.
    static let factOpeners: [[String]] = [
        ["who"], ["when"], ["where"], ["whats"], ["what", "is"], ["what", "s"], ["what", "was"], ["what", "year"],
        ["how", "many"], ["how", "much"], ["how", "tall"], ["how", "long"], ["how", "far"], ["how", "old"],
        ["how", "big"], ["how", "high"],
    ]
    /// The Turkish words of a question of fact: where, who, how many ("ne zaman" and "hangi yıl" are
    /// read as pairs). Not "hangisi" (which one): `X için hangisi` is how a Turkish reader asks for a
    /// model (the M19-W4 review's MJ2); not "nerede", which no tuning row holds whole (its M2).
    static let factWordsTurkish: Set<String> = ["neresi", "kim", "kaç"]
    /// A word that makes it a search, a task or a request rather than a question of fact: a model, an
    /// AI or an AI tool named, the asker in it or their wish, a recommendation, a task, something
    /// current, or an image the asker has (with the image nouns of `isImageNoun`).
    static let factExclusions: Set<String> = [
        "ai", "llm", "gpt", "yapay", "zeka", "zekâ", "chatbot", "chatgpt", "claude", "gemini", "deepseek",
        "llama", "mistral", "grok", "copilot", "opus", "sonnet", "assistant", "asistan", "bot", "best",
        "better", "recommend", "i", "my", "me", "we", "our", "us", "bana", "benim", "ben", "istiyorum", "iyi",
        "iyisi", "coding", "code", "programming", "writing", "translation", "math", "maths", "essay",
        "homework", "today", "tonight", "now", "latest", "live", "yesterday", "tomorrow", "week", "bugün",
        "bugun", "şimdi", "dün", "yarın", "güncel", "hafta", "this", "screenshot",
    ]
    /// The same in Turkish, by stem, since the language joins its suffixes: to recommend, to code, to
    /// translate, homework, software (the M19-W4 review's MJ2 and M2).
    static let factExclusionStemsTurkish = ["öner", "kodla", "çevir", "çeviri", "ödev", "yazılım"]

    /// #113 (M18-W3): a request to MAKE or CHANGE an image, which nothing here measures: `vision`
    /// measures reading one. The on-device model sent these to `vision` even when told not to (0 of
    /// 6 on the tuning set). `TieredRouter.read` applies this ONLY to a question routed to `vision`:
    /// beyond it, a question about code, a website, a store or a file that mentions an image is routed
    /// as its tier chose (the M18 reviews' B4). M19-W4 reached further, three times, and each reach drew
    /// a review verdict on that class; the slice came out (#191). Narrowly, here:
    /// - English: a making verb, then within four words an image that is the verb's object: not after
    ///   "from", "of", "for" or the like, not a modifier ("image upload", "photo gallery"), and not
    ///   turned "into" text, a table or data (that is reading it);
    /// - "draw me", or "draw a/an" before a picture word, not an idiom ("draw a conclusion");
    /// - Turkish: an image within four words before a making verb ("kedi resmini düzenle"), a form of
    ///   "çiz" itself, or "arka plan" with a removing verb after it.
    static func makesAnImage(_ text: String) -> Bool {
        folds(text).contains { folded in
            let turkishWords = wordsOf(folded)
            // English words compared as English: "This" and "Into" fold to "thıs" and "ınto" in Turkish,
            // and "into" decides a reading (the second M19-W4 review's K1). Turkish words stay as they are.
            let words = turkishWords.map { $0.replacingOccurrences(of: "ı", with: "i") }
            for (index, word) in words.enumerated() {
                let next = Array(words.dropFirst(index + 1).prefix(4))
                if word == "background", index > 0,
                   ["remove", "blur", "replace", "change"].contains(words[index - 1])
                    || (index > 1 && ["remove", "blur", "replace", "change"].contains(words[index - 2])),
                   words.contains(where: isImageNoun) {
                    return true
                }
                if turkishWords[index] == "arka", turkishWords.dropFirst(index + 1).first?.hasPrefix("plan") == true,
                   turkishWords.dropFirst(index + 2).prefix(3).contains(where: { candidate in
                       ["kaldır", "sil", "değiştir", "degistir", "bulanıklaştır"].contains { candidate.hasPrefix($0) }
                   }) {
                    return true
                }
                if word == "draw", let first = next.first {
                    if first == "me" { return true }
                    if ["a", "an", "my"].contains(first), next.count > 1, !drawIdioms.contains(next[1]) {
                        return true
                    }
                }
                if drawStemsTurkish.contains(turkishWords[index]) { return true }
                if imageVerbsEnglish.contains(word), let at = next.firstIndex(where: isImageNoun) {
                    let between = next[..<at]
                    let after = at + 1 < next.count ? next[at + 1] : (index + at + 2 < words.count ? words[index + at + 2] : "")
                    // "turn a photo (of a receipt) into a spreadsheet" reads the image: an "into" anywhere
                    // after the verb, unless a picture or a style follows it ("into a cartoon", "into an
                    // oil painting"). Text, a summary, LaTeX or a list is read (the third review's M16).
                    let readInto = words.indices.dropFirst(index + 1).contains { spot in
                        words[spot] == "into" && !words.dropFirst(spot + 1).prefix(4).contains { target in
                            pictureTargets.contains(target) || isImageNoun(target)
                        }
                    }
                    if !between.contains(where: readingPrepositions.contains), !modifierHeads.contains(after), !readInto {
                        return true
                    }
                }
                // An image before "galerisi", "yükleme", "sayfası" or "bölümü" names a gallery or an
                // upload page, not an image to make (the M19-W4 review's MJ1); other cases are not read.
                if isTurkishVerb(turkishWords, at: index, stems: imageStemsTurkish),
                   turkishWords.indices[max(0, index - 4)..<index].contains(where: { spot in
                       isImageNoun(turkishWords[spot])
                           && !(spot + 1 < index && modifierHeadsTurkish.contains(where: turkishWords[spot + 1].hasPrefix))
                   }) {
                    return true
                }
            }
            return false
        }
    }

    private static let imageVerbsEnglish: Set<String> = [
        "generate", "create", "make", "design", "edit", "retouch", "remove", "turn", "paint", "illustrate",
        "fix", "enhance", "restore", "colorize", "colourise", "brighten", "sharpen", "redraw",
    ]
    private static let readingPrepositions: Set<String> = [
        "from", "of", "for", "in", "on", "about", "using", "with", "based", "into", "to",
    ]
    /// A word after an image noun that makes the noun a modifier: the object is something else.
    private static let modifierHeads: Set<String> = [
        "upload", "uploads", "uploader", "gallery", "galleries", "classifier", "classifiers",
        "classification", "recognition", "caption", "captions", "description", "descriptions",
        "processing", "compression", "dataset", "datasets", "data", "file", "files", "format", "size",
        "sizes", "url", "urls", "tag", "tags", "metadata", "search", "model", "models", "page", "pages",
        "slider", "carousel", "viewer", "loader", "loading", "lazy", "responsive", "component", "api",
    ]
    /// What an image turned "into" is made, not read: a picture or a style.
    private static let pictureTargets: Set<String> = [
        "cartoon", "cartoons", "painting", "paintings", "sketch", "sketches", "anime", "manga", "watercolour",
        "watercolor", "drawing", "drawings", "sticker", "stickers", "emoji", "emojis", "meme", "memes", "comic",
        "comics", "artwork", "art", "pixel", "oil", "pencil", "character", "caricature", "collage", "mosaic",
        "style", "gif", "animation",
    ]
    /// A word after an image noun that makes the noun a modifier, in Turkish: a gallery, an upload,
    /// a page or a section of it.
    private static let modifierHeadsTurkish = ["galeri", "yükleme", "sayfa", "bölüm"]
    private static let drawIdioms: Set<String> = [
        "conclusion", "conclusions", "comparison", "distinction", "line", "parallel", "chart", "graph",
        "plot", "diagram", "table", "box", "boundary", "sample", "card", "blank", "crowd", "breath",
    ]
    private static let imageStemsTurkish: Set<String> = [
        "oluştur", "tasarla", "düzenle", "rötuşla", "kaldır", "sil", "üret", "düzelt", "netleştir",
        "renklendir", "boya", "çiz",
    ]
    private static let drawStemsTurkish: Set<String> = [
        "çiz", "çizer", "çizebilir", "çizsene", "çizin", "çizsin", "çizermisin", "çizebilirmisin",
    ]

    private static func isImageNoun(_ word: String) -> Bool {
        let english: Set<String> = [
            "image", "images", "picture", "pictures", "photo", "photos", "logo", "logos", "illustration",
            "illustrations", "avatar", "avatars", "drawing", "poster", "icon", "icons", "wallpaper",
            "selfie", "portrait", "cartoon",
        ]
        if english.contains(word) { return true }
        // Turkish nouns take suffixes ("resmini", "fotoğrafımdaki"), so long stems are matched at the
        // start. Not "resm-": "resmi" is also "official" (review B4).
        let stems = ["resim", "resmin", "görsel", "fotoğraf", "fotograf", "illüstrasyon", "afiş", "portre", "çizim"]
        if stems.contains(where: { word.hasPrefix($0) }) { return true }
        return ["logo", "logoyu", "logosu", "logomu", "logomuzu", "ikon", "ikonu", "simge", "simgesi", "avatar",
                "avatarı", "avatarımı"].contains(word)
    }

    /// The verbs that ask the app to do something to text it is given. English as whole words;
    /// Turkish by `isTurkishVerb`. Held by `ReadingTests`; a verb added here is a reviewed edit.
    static let actVerbsEnglish: Set<String> = [
        "translate", "fix", "summarize", "summarise", "rewrite", "correct", "proofread", "convert",
        "explain", "answer", "solve", "calculate", "compute", "debug", "refactor", "rephrase",
        "paraphrase", "shorten", "improve", "edit", "write", "make",
    ]
    static let actStemsTurkish: Set<String> = [
        "çevir", "tercüme", "düzelt", "özetle", "açıkla", "cevapla", "yanıtla", "hesapla", "dönüştür",
        "çöz", "kısalt", "iyileştir", "yaz", "duzelt", "yap", "cevir",
    ]

    /// A Turkish verb from `stems`, as a request is written: the bare imperative ("çevir"), a polite
    /// imperative ("çevirsene", "çevirin"), the ability form ("çevirebilir"), or the aorist before a
    /// question particle ("çevirir misin"). A noun built from the verb ("çeviri", "düzeltme") is not.
    static func isTurkishVerb(_ words: [String], at index: Int, stems: Set<String>) -> Bool {
        let word = words[index]
        let questionFollows = index + 1 < words.count
            && ["mi", "mı", "mu", "mü", "misin", "mısın", "musun", "müsün", "misiniz", "mısınız"]
                .contains(where: { words[index + 1].hasPrefix($0) })
        for stem in stems where word.hasPrefix(stem) {
            let rest = String(word.dropFirst(stem.count))
            if ["", "sene", "sana", "in", "ın", "un", "ün", "iver", "ıver", "ebilir", "abilir", "yebilir",
                "yabilir"].contains(rest) {
                return true
            }
            if ["ir", "ır", "ur", "ür", "er", "ar", "r"].contains(rest), questionFollows { return true }
            if ["irmisin", "ırmısın", "urmusun", "ürmüsün", "ermisin", "armısın", "rmısın", "rmisin"].contains(rest) {
                return true
            }
        }
        return false
    }

    /// The text folded both ways: the default and Turkish case folding differ on "I" and "İ", and a
    /// reader may write either (review M7).
    static func folds(_ text: String) -> [String] {
        [text.lowercased(), text.lowercased(with: Locale(identifier: "tr_TR"))]
    }

    static func wordsOf(_ text: String) -> [String] {
        text.split { !$0.isLetter }.map(String.init)
    }

    /// A word, in any language: letters from a script beyond Latin (Cyrillic, Greek, Arabic, CJK and
    /// the rest) are always words here. A Latin token is not a word when it is one letter repeated or
    /// two alternating, or a run along a keyboard row, in any case. Otherwise a token written in
    /// capitals, with or without a plural "s", is an acronym and a word; any other is a word unless it
    /// has five or more letters and no vowel.
    private static func isWord(_ original: String) -> Bool {
        if original.unicodeScalars.contains(where: { $0.value > 0x024F }) { return true }
        let token = original.lowercased()
        let distinct = Set(token)
        if token.count >= 2, distinct.count <= (token.count >= 4 ? 2 : 1) { return false }
        if token.count >= 4, keyboardRows.contains(where: { $0.contains(token) }) { return false }
        // After the checks above, so nonsense typed in capitals is not an acronym; one plural "s"
        // dropped, so "CRDTs" and "LLMs" are (the third review's M18).
        let stem = original.count > 2 && original.hasSuffix("s") ? String(original.dropLast()) : original
        if stem.count >= 2, stem == stem.uppercased() { return true }
        return token.count < 5 || token.contains(where: { vowels.contains($0) })
    }

    private static let vowels: Set<Character> = Set("aeiouyáàâäãåæéèêëíìîïóòôöõøúùûüıœ")

    /// Each row of the US and Turkish Q keyboards, both ways.
    private static let keyboardRows: [String] = {
        let rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "qwertyuıopğü", "asdfghjklşi", "zxcvbnmöç"]
        let backwards = rows.map { row in String(row.reversed()) }
        return rows + backwards
    }()
}

/// D-169 as amended at M18-W3 and by D-184: the reading, from the signals in code and the model's
/// verdict.
///
/// - No word, or small talk and nothing else, decides alone: there is nothing to route.
/// - A doubt in code (pasted content, an instruction to the app, a question of fact) and the
///   model's "not a search" together decide it is not a search.
/// - Either one alone is a doubt, and the reader is asked.
/// - `modelSaysNotASearch` is `nil` where no model read the question (another tier answered).
func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
    if noWord || smallTalk { return .notASearch }
    switch (modelSaysNotASearch ?? false, doubt) {
    case (true, true): return .notASearch
    case (true, false), (false, true): return .unsure
    case (false, false): return .search
    }
}
