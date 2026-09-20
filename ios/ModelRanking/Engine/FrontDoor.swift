//  FrontDoor.swift — the question is the front door. M13-W3, REQ-ASK-001..004.
//
//  The owner's words, translated from Turkish: *"it felt like a search bar, not an AI"*. The M13
//  council found why — Apple Intelligence had never once run, so every question was matched on
//  wording — and it found the rest of the reason on the screen: two text fields, two strips of
//  controls competing with the one input the product is supposed to be built around, and a route
//  the reader could not see. This file holds the logic of the new front door so that it executes
//  under `swift test`; `ContentView` renders it and decides nothing.

import Foundation

// MARK: - REQ-ASK-004: an older answer can never replace a newer selection

/// Issues a ticket per load and honours only the latest one.
///
/// `ContentView.load()` had no identity at all. Every chip, every budget button and every question
/// started an independent `Task`, and whichever response arrived LAST was rendered, whatever the
/// reader had chosen since. On a local engine the race is invisible; over a phone network, choosing
/// Mathematics and then Coding could leave Mathematics on screen under a Coding selection.
///
/// **Identity rather than cancellation, deliberately.** Cancelling a `URLSession` task is
/// best-effort and a cancelled response can still be delivered. A ticket compared at the moment of
/// APPLYING is exact: it is the comparison, not the network, that decides what is shown.
public struct RequestGate: Equatable {
    public private(set) var latest = 0

    public init() {}

    /// Start a load. The returned ticket is the only one `isCurrent` will accept until the next.
    public mutating func begin() -> Int {
        latest += 1
        return latest
    }

    public func isCurrent(_ ticket: Int) -> Bool { ticket == latest }

    /// Retire every ticket issued so far without starting anything. A `Change` selection does this
    /// to the ROUTING gate (M13-W3 review BLOCKING-2): the question still being routed is no longer
    /// what the reader is asking, and its late answer must not replace the surface they chose.
    public mutating func invalidate() {
        latest += 1
    }
}

// MARK: - REQ-ASK-001: the field can always be submitted, and never twice at once

/// Whether a question may be sent now. Both the Return key and the send button ask this.
///
/// The field used to submit from `.onSubmit` alone. With a hardware keyboard attached and focus
/// lost there was no way to send a question at all, and nothing stopped a second submission while
/// the first was still routing.
public func canSubmit(_ question: String, inFlight: Bool) -> Bool {
    !inFlight && !question.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
}

// MARK: - REQ-ASK-002: what the screen understood, in the reader's own words

/// How much of a question the echo quotes before cutting it. A line, not a paragraph.
let echoLimit = 60

/// `“prove a theorem” → Mathematics`.
///
/// The Stranger seat's finding: the only observable difference between the intelligent tier and
/// the fallback was one footnote in the same font, and the fallback's was the more informative of
/// the two. The echo is the proof a stranger can read — it shows that the words did not have to
/// match. `nil` for an empty question: there is nothing to echo, and `“” → Coding` would read as a
/// question the reader never asked.
public func echoLine(question: String, surfaceTitle: String) -> String? {
    let typed = question
        .components(separatedBy: .newlines)
        .joined(separator: " ")
        .trimmingCharacters(in: .whitespaces)
    guard !typed.isEmpty else { return nil }
    let shown = typed.count > echoLimit ? String(typed.prefix(echoLimit)) + "…" : typed
    return "“\(shown)” → \(surfaceTitle)"
}

/// One surface the reader can correct to.
public struct SurfaceChoice: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let isSelected: Bool
}

/// Every surface the engine serves, in the ENGINE's order, titled in the reader's language.
///
/// REQ-ASK-002's second half: the correction reaches every surface. It is built from
/// `/v1/categories` and nothing else, so a tenth surface appears here the day the engine serves it
/// — the two top strips this replaces were the only other way to reach one, and removing them
/// without this would have made seven of nine surfaces reachable only by guessing the right words.
func surfaceChoices(_ categories: [Category], selected: String, _ language: Language)
    -> [SurfaceChoice]
{
    categories.map { category in
        SurfaceChoice(
            id: category.id,
            title: UIText.surface(id: category.id, engineTitle: category.title, language),
            isSelected: category.id == selected
        )
    }
}

// MARK: - REQ-ASK-003: an unmeasured question gets a ranking AND the sentence above it

/// What the screen says under the echo, in the reader's language.
///
/// **An unmeasured question is answered, never declined, and never answered as if measured.** The
/// Product seat measured the alternative — returning nothing — as a regression: the app already
/// routes an unmeasured question to the chat ranking, and the ranking is useful. What it must carry
/// is the sentence saying what that ranking CANNOT tell the reader.
///
/// `manual` — both tiers declined — is the same case with a different cause. It used to say "Pick a
/// surface below" while the view loaded the chat ranking anyway, with `unmeasured: false`: the
/// words, the state and the action disagreed (second-opinion P1). It is now an unmeasured fallback
/// and says so, and it names the control that corrects it.
func routingNotice(_ outcome: RoutingOutcome, _ language: Language) -> String {
    switch (outcome.tier, outcome.unmeasured, language) {
    case (.manual, _, .english):
        return "We could not match this question to anything we measure. Below is the general "
            + "chat ranking: it cannot tell you which model is best at what you asked. Use Change "
            + "to pick a surface."
    case (.manual, _, .turkish):
        return "Bu soruyu ölçtüğümüz hiçbir şeyle eşleştiremedik. Aşağıdaki genel sohbet "
            + "sıralaması; sorduğunuz işte hangi modelin en iyi olduğunu söyleyemez. Bir alan "
            + "seçmek için Değiştir'e dokunun."
    // M13-W3 review MINOR-5, two corrections. The wording tier cannot KNOW the catalogue does not
    // measure a question, only that its words point there, so it says "going by its wording". And
    // the chat ranking is Arena's record of which answers people preferred in blind comparisons,
    // not a measure of "best at conversation".
    case (.similarity, true, .english):
        return "Going by its wording, this is not something we measure directly. Below is the "
            + "general chat ranking: it cannot tell you which model is best at what you asked, only "
            + "which models people preferred in conversation."
    case (.similarity, true, .turkish):
        return "Kelimelerine bakılırsa bunu doğrudan ölçmüyoruz. Aşağıdaki genel sohbet "
            + "sıralaması; sorduğunuz işte hangi modelin en iyi olduğunu söyleyemez, yalnızca "
            + "insanların sohbette hangi modelleri tercih ettiğini söyler."
    case (_, true, .english):
        return "This is not something we measure directly. Below is the general chat ranking: it "
            + "cannot tell you which model is best at what you asked, only which models people "
            + "preferred in conversation."
    case (_, true, .turkish):
        return "Bunu doğrudan ölçmüyoruz. Aşağıdaki genel sohbet sıralaması; sorduğunuz işte hangi "
            + "modelin en iyi olduğunu söyleyemez, yalnızca insanların sohbette hangi modelleri "
            + "tercih ettiğini söyler."
    case (.similarity, false, .english):
        return "Matched on wording, not on meaning — check this is the right surface."
    case (.similarity, false, .turkish):
        return "Anlama göre değil kelimelere göre eşleşti — doğru alan olduğunu kontrol edin."
    case (.model, false, .english):
        return "Matched by meaning, on this device."
    case (.model, false, .turkish):
        return "Anlamına göre, bu cihazda eşleşti."
    }
}

// MARK: - Why the intelligent tier is not running, said as help rather than as an error

/// Whether the on-device model can route questions, as the platform reports it.
///
/// `ModelRouter.unavailableReason` computed exactly this, read it once as a guard, and rendered it
/// nowhere: the app knew why it had degraded and told nobody for twelve milestones.
public enum OnDeviceState: Equatable {
    case available
    /// The hardware can never run it — every iPhone below the 15 Pro, which is most of the
    /// deployment target's base. For those readers the wording tier IS the product.
    case notEligible
    case turnedOff
    case downloading
    case unavailable

    /// One quiet line, or `nil` when there is nothing to explain. Never an error: the similarity
    /// tier still routes, and the screen works either way.
    public func help(_ language: Language) -> String? {
        switch (self, language) {
        case (.available, _):
            return nil
        case (.notEligible, .english):
            return "This device cannot run on-device intelligence, so questions are matched by "
                + "wording."
        case (.notEligible, .turkish):
            return "Bu cihaz cihaz içi zekâyı çalıştıramıyor; sorular kelimelere göre eşleştiriliyor."
        case (.turnedOff, .english):
            return "Apple Intelligence is off, so questions are matched by wording. Turning it on "
                + "in Settings matches them by meaning."
        case (.turnedOff, .turkish):
            return "Apple Intelligence kapalı; sorular kelimelere göre eşleştiriliyor. Ayarlar'dan "
                + "açarsanız anlamına göre eşleşir."
        case (.downloading, .english):
            return "The on-device model is still downloading; until it finishes, questions are "
                + "matched by wording."
        case (.downloading, .turkish):
            return "Cihaz içi model hâlâ iniyor; bitene kadar sorular kelimelere göre eşleştiriliyor."
        case (.unavailable, .english):
            return "On-device intelligence is unavailable right now, so questions are matched by "
                + "wording."
        case (.unavailable, .turkish):
            return "Cihaz içi zekâ şu an kullanılamıyor; sorular kelimelere göre eşleştiriliyor."
        }
    }
}

// MARK: - The gap register (M14-W3, REQ-GAP-001/002, D-142 §3)
//
// Every question the catalogue could not answer is a person telling us which surface to build next.
// Until this wave the decline sentinel was the product's own demand signal and it was thrown away.
// Now each unmeasured question is recorded ON THIS DEVICE with a count, and the owner reads the
// list, most-asked first. It never reaches the engine: REQ-RTR-004's data-flow test holds, and the
// register is written to a file excluded from iCloud backup, because "nothing leaves the device" is
// not true of a file the phone uploads every night.
//
// It lives in this file, not a new one, so the app target's project file does not change.

/// One question the catalogue could not answer, and how often it has been asked.
public struct GapEntry: Codable, Equatable, Identifiable {
    /// As the reader first typed it, trimmed and capped. Shown as-is.
    public let question: String
    public var count: Int
    public var lastAsked: Date

    public var id: String { gapKey(question) }
}

/// Two spellings of one question count as one: case and runs of whitespace do not make a new gap.
///
/// Folded with a PINNED locale, for W-079's reason: under `tr_TR` the capital I folds to a dotless
/// letter, and the same question typed on two phones would count as two.
func gapKey(_ question: String) -> String {
    question
        .lowercased(with: Locale(identifier: "en_US_POSIX"))
        .split(whereSeparator: \.isWhitespace)
        .joined(separator: " ")
}

/// The register itself: a value, so it is tested without a disk and saved as one document.
public struct GapRegister: Codable, Equatable {
    /// A bound on what the phone keeps. When full, the least-asked, oldest entry makes room.
    public static let maxEntries = 200
    /// A bound on what one entry keeps, so a pasted document is not stored as a "question".
    public static let maxLength = 200
    /// Review S-3: the character bound alone is not a size bound. One `Character` can carry
    /// thousands of combining marks, so an entry is also held to this many UTF-8 bytes.
    public static let maxBytes = 800

    public private(set) var entries: [GapEntry] = []

    public init() {}

    /// REQ-GAP-001. Records one unmeasured question. Blank text records nothing.
    public mutating func record(_ question: String, at date: Date = Date()) {
        var trimmed = String(question.trimmingCharacters(in: .whitespacesAndNewlines)
            .prefix(Self.maxLength))
        while trimmed.utf8.count > Self.maxBytes { trimmed.removeLast() }
        let key = gapKey(trimmed)
        guard !key.isEmpty else { return }
        if let index = entries.firstIndex(where: { $0.id == key }) {
            entries[index].count += 1
            entries[index].lastAsked = date
            return
        }
        if entries.count >= Self.maxEntries, let weakest = entries.indices.min(by: {
            (entries[$0].count, entries[$0].lastAsked) < (entries[$1].count, entries[$1].lastAsked)
        }) {
            entries.remove(at: weakest)
        }
        entries.append(GapEntry(question: trimmed, count: 1, lastAsked: date))
    }

    /// REQ-GAP-002. Most-asked first; among equals, the most recent first.
    public var ordered: [GapEntry] {
        entries.sorted { ($0.count, $0.lastAsked) > ($1.count, $1.lastAsked) }
    }

    public mutating func clear() { entries.removeAll() }
}

/// Where the register is kept: one JSON file on this device, never backed up.
public struct GapRegisterStore {
    public let url: URL
    /// Review S-1: how the file is written. The phone's store adds `.completeFileProtection`, so the
    /// register is unreadable while the device is locked; a store built on a test host's temporary
    /// folder writes atomically only. A parameter, not an `#if os(...)`: the Engine is compiled the
    /// same way for `swift test` and for the app (`test_ios_platform_drift.py`).
    public let writeOptions: Data.WritingOptions

    public init(url: URL, writeOptions: Data.WritingOptions = .atomic) {
        self.url = url
        self.writeOptions = writeOptions
    }

    /// Application Support, which the system does not purge, in a folder of its own that is
    /// excluded from backup (review S-2): the exclusion then belongs to the FOLDER, which an atomic
    /// write never replaces, rather than to a file every save swaps out.
    public static var onDevice: GapRegisterStore {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)
            .first ?? FileManager.default.temporaryDirectory
        return GapRegisterStore(
            url: base.appendingPathComponent("GapRegister", isDirectory: true)
                .appendingPathComponent("gap-register.json"),
            writeOptions: [.atomic, .completeFileProtection]
        )
    }

    /// An unreadable or absent file is an EMPTY register, never a crash on launch.
    public func load() -> GapRegister {
        guard let data = try? Data(contentsOf: url),
              let register = try? JSONDecoder().decode(GapRegister.self, from: data)
        else { return GapRegister() }
        return register
    }

    /// Best effort: a register that cannot be written costs the owner a signal, not the reader
    /// their answer, so a failure here is swallowed rather than surfaced in the middle of a question.
    public func save(_ register: GapRegister) {
        guard let data = try? JSONEncoder().encode(register) else { return }
        var folder = url.deletingLastPathComponent()
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try? folder.setResourceValues(values)
        guard (try? data.write(to: url, options: writeOptions)) != nil else { return }
        var target = url
        try? target.setResourceValues(values)
    }
}

/// REQ-GAP-001, review m-1: which routing outcomes are a GAP in what the product measures.
///
/// `unmeasured` alone also covers the manual tier, where the reader picked no question at all or the
/// router failed; those are the router's misses, not questions the catalogue cannot answer, and
/// counting them would tell the owner to build surfaces for failures.
func recordsGap(_ outcome: RoutingOutcome) -> Bool {
    outcome.unmeasured && outcome.tier != .manual
}
