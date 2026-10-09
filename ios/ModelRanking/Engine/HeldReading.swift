//  HeldReading.swift — D-169's held reading, in the Engine where tests reach it (#132, M21-W3).
//
//  A question read as not a search, or one the app is not sure about, is held: it sends no request,
//  and the screen shows the note or asks the reader. Its state and its transitions live here, driven
//  by Swift tests; `ContentView` renders them.

import Foundation

/// D-169 (M18-W3): what was typed, and how it was read, while the screen shows the note or asks.
struct HeldReading: Equatable {
    let typed: String
    let outcome: RoutingOutcome

    /// What `ask` does with a routed outcome: nothing for a search, which is answered; otherwise the
    /// reading is held (a stub in the red commit).
    static func holding(_ outcome: RoutingOutcome, typed: String) -> HeldReading? {
        nil
    }

    /// "Find a model": the held question answered as a search, routed as read (a stub).
    var confirmed: RoutingOutcome { outcome }

    /// "No": the note (a stub).
    var declined: HeldReading { self }

    /// The card: the question back exactly while the reading is unsure, the note otherwise (a stub).
    var asksBack: Bool { false }
}
