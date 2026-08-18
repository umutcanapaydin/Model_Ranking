//  ContentView.swift — W1's one screen.
//
//  **Deliberately plain.** W1 exists to prove the seam: Swift's decoder against the real payload,
//  on the simulator's network stack, against a running engine. Design is W2's, and W2 opens with a
//  decision only the owner can make — how do you show two EQUAL answers on a phone, when a list has
//  a first item and tabs have a selected one?
//
//  Until he rules, this screen makes the least-committal choice available: both answers are laid
//  out identically, one after the other, under the engine's own sentence saying the order means
//  nothing. That is not a neutral presentation — there is none — but it is the one that adds the
//  least of its own.

import SwiftUI

struct ContentView: View {
    @State private var state: LoadState = .idle
    @State private var task = "coding"
    @State private var budget = "medium"

    enum LoadState {
        case idle
        case loading
        case loaded(Recommendation)
        case failed(EngineError)
    }

    private let client = EngineClient()

    var body: some View {
        NavigationStack {
            Group {
                switch state {
                case .idle, .loading:
                    ProgressView("Asking the engine…")
                case let .loaded(recommendation):
                    loaded(recommendation)
                case let .failed(error):
                    failure(error)
                }
            }
            .navigationTitle("Which model?")
            .task { await load() }
        }
    }

    // MARK: - Loaded

    @ViewBuilder
    private func loaded(_ recommendation: Recommendation) -> some View {
        List {
            Section {
                // The engine's own words about the ordering. Rendered because a caller who does not
                // read documentation still reads the screen (M6, ORDERING_NOTE).
                Text(recommendation.orderingNote)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            ForEach(recommendation.answers) { answer in
                Section(answer.title) {
                    if answer.picks.isEmpty {
                        emptyAnswer(answer)
                    } else {
                        ForEach(answer.picks) { pick in
                            pickRow(pick)
                        }
                    }
                    disclosures(answer)
                }
            }
        }
        .refreshable { await load() }
    }

    /// A surface with nothing to say still appears, carrying the engine's reason.
    /// Dropping it would read as "there is only one coding answer", which is the thing Ruling A
    /// exists to prevent.
    @ViewBuilder
    private func emptyAnswer(_ answer: Answer) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("No picks")
                .font(.headline)
            if let reason = answer.unavailableReason {
                Text(reason)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func pickRow(_ pick: Pick) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(pick.label.replacingOccurrences(of: "_", with: " ").capitalized)
                .font(.caption)
                .foregroundStyle(.secondary)

            Text(pick.model)
                .font(.headline)
            Text(pick.vendor)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            // Values are rendered AS RECEIVED. The engine rounds at its own output boundary
            // (D-109); formatting them differently here would publish a second precision.
            Text("\(pick.score, specifier: "%g") \(pick.metric)  ·  $\(pick.blendedPerM, specifier: "%g")/1M")
                .font(.subheadline)
                .monospacedDigit()

            Text(pick.why)
                .font(.footnote)
            if let tradeOff = pick.tradeOff {
                Text(tradeOff)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    /// Everything the engine discloses about its own evidence. All of it, because each of these
    /// sentences cost a review round to make the server say.
    @ViewBuilder
    private func disclosures(_ answer: Answer) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(
                [
                    answer.sourceHealth?.notice,
                    answer.staleNotice,
                    answer.evidenceDatingNote,
                    answer.effortMixNotice,
                    answer.closeCall,
                ].compactMap { $0 },
                id: \.self
            ) { notice in
                Label(notice, systemImage: "exclamationmark.triangle")
                    .font(.caption)
                    .foregroundStyle(.orange)
            }
        }
    }

    // MARK: - Failure

    @ViewBuilder
    private func failure(_ error: EngineError) -> some View {
        ContentUnavailableView {
            Label("No answer", systemImage: "exclamationmark.triangle")
        } description: {
            VStack(spacing: 12) {
                // The ENGINE's sentence, not ours.
                Text(error.errorDescription ?? "")
                if let recovery = error.recovery {
                    Text(recovery)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
        } actions: {
            Button("Try again") { Task { await load() } }
        }
    }

    // MARK: - Loading

    private func load() async {
        state = .loading
        do {
            state = .loaded(try await client.recommendation(task: task, budget: budget))
        } catch let error as EngineError {
            state = .failed(error)
        } catch {
            state = .failed(.undecodable(String(describing: error)))
        }
    }
}
