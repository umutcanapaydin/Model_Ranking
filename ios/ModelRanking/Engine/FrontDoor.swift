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
