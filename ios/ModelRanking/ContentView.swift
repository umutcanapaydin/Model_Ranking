//  ContentView.swift — the home screen (M8-W2).
//
//  The owner's shape: categories stacked, each showing its three recommendations and then the top
//  few of the full ranking, with the whole list one tap away. A search field at the top FILTERS by
//  model name — it does not re-rank, because the ranking is the engine's answer and searching is
//  the user narrowing what they look at (owner's ruling, M8-W1 review).
//
//  Why the picks stay above the list, and it is a product decision rather than a layout habit: the
//  three picks answer three different questions, and on today's data the score-ordered top 5 for
//  `coding` is four models above $8/1M while `best_value` — 3.5 points off the leader at 84% less —
//  does not appear in it at all. A screen showing only the ranked list would lose the claim the
//  product is making.

import SwiftUI

/// How many ranking rows the home screen previews before "See all".
private let homePreviewCount = 5

struct ContentView: View {
    @State private var state: LoadState = .idle
    @State private var filter = ""
    /// Fetched from the engine on first load, never listed here. See `EngineClient.categories()`.
    @State private var categories: [Category] = []
    @State private var task = "coding"
    private let budget = "unlimited"

    enum LoadState {
        case idle, loading
        case loaded([Answer], orderingNote: String)
        case failed(EngineError)
    }

    private let client = EngineClient()

    var body: some View {
        NavigationStack {
            Group {
                switch state {
                case .idle, .loading:
                    ProgressView("Asking the engine…")
                case let .loaded(answers, note):
                    home(answers, orderingNote: note)
                case let .failed(error):
                    failure(error)
                }
            }
            .safeAreaInset(edge: .top) { categoryStrip }
            .navigationTitle("Which model?")
            // Inline, because the category strip already occupies the top of the screen and a
            // large title left an empty band above it with nothing in it.
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $filter, prompt: "Filter by model name")
            .task { await load() }
        }
    }

    // MARK: - Home

    @ViewBuilder
    private func home(_ answers: [Answer], orderingNote: String) -> some View {
        List {
            Section {
                Text(orderingNote)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            ForEach(answers) { answer in
                Section {
                    if answer.picks.isEmpty && answer.ranking.isEmpty {
                        emptyAnswer(answer)
                    } else {
                        ForEach(answer.picks) { pick in
                            PickRow(pick: pick)
                        }
                        rankingPreview(answer)
                    }
                    disclosures(answer)
                } header: {
                    Text(answer.title)
                } footer: {
                    if !answer.ranking.isEmpty {
                        // `ranking_effort` is part of what the number MEANS: agentic-coding ranks
                        // at a named comparable level, and a score shown without it invites the
                        // reader to compare it against one measured somewhere else.
                        Text(
                            answer.rankingEffort.map {
                                "\(answer.ranking.count) models ranked on "
                                    + "\(answer.primaryBenchmark), at \($0) effort"
                            } ?? "\(answer.ranking.count) models ranked on \(answer.primaryBenchmark)"
                        )
                    }
                }
            }
        }
        .refreshable { await load() }
    }

    /// The top of the full ranking, plus the door to the rest.
    @ViewBuilder
    private func rankingPreview(_ answer: Answer) -> some View {
        let rows = filtered(answer.ranking)
        if !rows.isEmpty {
            ForEach(rows.prefix(homePreviewCount)) { row in
                RankedRow(row: row)
            }
            NavigationLink {
                RankingList(answer: answer, filter: filter)
            } label: {
                Text("See all \(answer.ranking.count)")
                    .font(.subheadline)
            }
        } else if !filter.isEmpty {
            Text("No model here matches “\(filter)”.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }

    /// Name-only filtering. It narrows what is SHOWN and never changes the order — the engine
    /// decided that, and a client that re-sorts is answering a different question (Trap 1).
    private func filtered(_ rows: [RankedModel]) -> [RankedModel] {
        guard !filter.isEmpty else { return rows }
        return rows.filter {
            $0.model.localizedCaseInsensitiveContains(filter)
                || $0.vendor.localizedCaseInsensitiveContains(filter)
        }
    }

    @ViewBuilder
    private func emptyAnswer(_ answer: Answer) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("No picks").font(.headline)
            if let reason = answer.unavailableReason {
                Text(reason).font(.subheadline).foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    /// Everything the engine discloses about its own evidence. Each of these sentences cost a
    /// review round to make the server say; a client that drops them undoes the property.
    @ViewBuilder
    private func disclosures(_ answer: Answer) -> some View {
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

    // MARK: - Failure

    @ViewBuilder
    private func failure(_ error: EngineError) -> some View {
        ContentUnavailableView {
            Label("No answer", systemImage: "exclamationmark.triangle")
        } description: {
            VStack(spacing: 12) {
                Text(error.errorDescription ?? "")
                if let recovery = error.recovery {
                    Text(recovery).font(.footnote).foregroundStyle(.secondary)
                }
            }
        } actions: {
            Button("Try again") { Task { await load() } }
        }
    }

    /// The nine surfaces, horizontally. PROVISIONAL: the home-screen direction is still the
    /// owner's to pick from the three drafted artboards, and this commits to none of them — it
    /// exists so every category the engine can answer is reachable and visible on a device.
    @ViewBuilder
    private var categoryStrip: some View {
        if categories.count > 1 {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(categories) { category in
                        Button {
                            guard category.id != task else { return }
                            task = category.id
                            Task { await load() }
                        } label: {
                            Text(category.title)
                                .font(.subheadline)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 8)
                                .background(
                                    Capsule().fill(
                                        category.id == task
                                            ? AnyShapeStyle(.tint)
                                            : AnyShapeStyle(.quaternary)
                                    )
                                )
                                .foregroundStyle(category.id == task ? .white : .primary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }
            .background(.bar)
        }
    }

    private func load() async {
        state = .loading
        do {
            // Asked once and reused. A failure here is NOT fatal to the screen: the strip simply
            // does not appear, and the default surface still answers — a discovery call that can
            // blank the product would be a worse dependency than the hardcoded list it replaces.
            if categories.isEmpty {
                categories = (try? await client.categories()) ?? []
            }
            // One request carries every surface for the coding intent (Ruling A), so the home
            // screen cannot show one answer while another is still loading.
            let recommendation = try await client.recommendation(task: task, budget: budget)
            state = .loaded(recommendation.answers, orderingNote: recommendation.orderingNote)
        } catch let error as EngineError {
            state = .failed(error)
        } catch {
            state = .failed(.undecodable(String(describing: error)))
        }
    }
}

// MARK: - Rows

struct PickRow: View {
    let pick: Pick

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(pick.label.replacingOccurrences(of: "_", with: " ").capitalized)
                .font(.caption)
                .foregroundStyle(.tint)
            Text(pick.model).font(.headline)
            Text(pick.vendor).font(.subheadline).foregroundStyle(.secondary)
            Text(Format.scoreAndPrice(pick.score, pick.metric, pick.blendedPerM))
                .font(.subheadline)
                .monospacedDigit()
            Text(pick.why).font(.footnote)
            if let tradeOff = pick.tradeOff {
                Text(tradeOff).font(.footnote).foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct RankedRow: View {
    let row: RankedModel

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(row.model)
                Text(row.vendor).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text(Format.scoreAndPrice(row.score, row.metric, row.blendedPerM))
                .font(.caption)
                .monospacedDigit()
                .foregroundStyle(.secondary)
        }
    }
}

/// The whole ranking for one surface.
struct RankingList: View {
    let answer: Answer
    @State var filter: String

    var body: some View {
        List {
            ForEach(rows) { row in
                RankedRow(row: row)
            }
        }
        .navigationTitle(answer.title)
        .searchable(text: $filter, prompt: "Filter by model name")
    }

    private var rows: [RankedModel] {
        guard !filter.isEmpty else { return answer.ranking }
        return answer.ranking.filter {
            $0.model.localizedCaseInsensitiveContains(filter)
                || $0.vendor.localizedCaseInsensitiveContains(filter)
        }
    }
}

/// Number formatting, in one place.
///
/// **Deliberately not localised.** The device locale is `en_TR` on the owner's simulator, which
/// rendered the engine's `2.06` as `$2,06` — and `$2,06` reads as two thousand and six to anyone
/// outside a comma-decimal locale, beside a `$` that is unambiguously not local currency. The
/// engine rounds at its own output boundary (D-109); this prints what it sent.
enum Format {
    static func scoreAndPrice(_ score: Double, _ metric: String, _ price: Double) -> String {
        "\(trim(score)) \(metric)  ·  $\(trim(price))/1M"
    }

    private static func trim(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.numberStyle = .decimal
        formatter.usesGroupingSeparator = false
        formatter.maximumFractionDigits = 3
        return formatter.string(from: NSNumber(value: value)) ?? "\(value)"
    }
}
