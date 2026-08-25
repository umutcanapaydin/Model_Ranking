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
    /// What the reader typed, and what the router made of it (D-126, REQ-RTR-001).
    @State private var question = ""
    @State private var routing: RoutingOutcome?
    @State private var routingInFlight = false
    private let budget = "unlimited"
    private let router = TieredRouter()

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
        // Computed once here rather than in the `ForEach`, so the footer below can ask "is this the
        // first answer?" of the SAME list the reader is looking at.
        let ordered = orderAnswers(
            surfaces: answers.map(\.surface), selected: task
        ).compactMap { id in answers.first { $0.surface == id } }
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 24) {
                // THE FRONT DOOR (D-126). The router picks the QUESTION; the engine answers it.
                // Nothing here says a model is good, and nothing typed leaves the device.
                Card {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 10) {
                            Image(systemName: "text.bubble")
                                .foregroundStyle(.secondary)
                            TextField("What do you want an AI to do?", text: $question)
                                .submitLabel(.search)
                                .onSubmit { Task { await ask() } }
                            if routingInFlight {
                                ProgressView().controlSize(.small)
                            }
                        }
                        if let outcome = routing {
                            // The choice is SHOWN, and changeable with one tap — the strip above
                            // is the override. D-126 requires the reader to see which question was
                            // picked, and a router whose choice cannot be corrected is one that
                            // decides FOR them.
                            Divider()
                            Text(outcome.explanation)
                                .font(.footnote)
                                .foregroundStyle(outcome.unmeasured ? .orange : .secondary)
                        }
                    }
                }

                // The surface the reader SELECTED speaks first. `task=coding` expands server-side
                // to two answers and `/v1` says in its own payload that their order carries no
                // meaning — so it always arrived alphabetically, and "Agentic coding" answered
                // every question about coding. Ordering ANSWERS is not the re-sorting Trap 1
                // forbids: that rule is about reordering models inside a ranking, which IS the
                // engine's answer.
                ForEach(ordered) { answer in
                    VStack(alignment: .leading, spacing: 12) {
                        SectionTitle(text: answer.title)

                        if answer.picks.isEmpty && answer.ranking.isEmpty {
                            Card { emptyAnswer(answer) }
                        } else {
                            ForEach(answer.picks) { pick in
                                PickRow(
                                    pick: pick,
                                    ranking: answer.ranking,
                                    scale: scaleExplanation(for: answer.metric)
                                )
                            }
                            rankingPreview(answer)
                        }
                        disclosures(answer)

                        if answer.id == ordered.first?.id {
                            // Ruling A's disclosure. It used to open the screen; the question
                            // field took that place, so it moved to where the answers START rather
                            // than being dropped — it is about how the ANSWERS are ordered, and
                            // that is where a reader needs it (REQ-APP-003).
                            Text(orderingNote)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                        if !answer.ranking.isEmpty {
                            // `ranking_effort` is part of what the number MEANS: agentic-coding
                            // ranks at a named comparable level, and a score shown without it
                            // invites the reader to compare it against one measured elsewhere.
                            Text(
                                answer.rankingEffort.map {
                                    "\(answer.ranking.count) models ranked on "
                                        + "\(answer.primaryBenchmark), at \($0) effort"
                                } ?? "\(answer.ranking.count) models ranked on "
                                    + "\(answer.primaryBenchmark)"
                            )
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 20)
            // The search field docks at the BOTTOM on this OS and floats over the scroll view. A
            // `List` reserves space for it; a `ScrollView` does not, so the last card sat under it
            // — visible in the first screenshot of this design and fixed before hand-over rather
            // than after. Measured by looking at the running app, which is the only way a layout
            // defect is ever found.
            .padding(.bottom, 88)
        }
        .background(Color(.systemGroupedBackground))
        .refreshable { await load() }
    }

    /// The top of the full ranking, plus the door to the rest.
    @ViewBuilder
    private func rankingPreview(_ answer: Answer) -> some View {
        // The picks are already on screen in large type; repeating them four lines below in small
        // type was the first thing the owner pointed at. Five models visible in total, split by
        // however many DISTINCT picks there turned out to be — one model can hold two pick labels.
        let picked = Set(answer.picks.map(\.model))
        let rows = previewRows(
            ranking: filtered(answer.ranking),
            pickedModels: filtered(answer.ranking).filter { picked.contains($0.model) },
            visibleTotal: homePreviewCount
        )
        if !rows.isEmpty {
            // The remaining models live in ONE card rather than a card each: they are the tail of
            // a list, not three separate answers, and giving them the same weight as the picks
            // would undo the distinction the picks exist to make.
            Card(padding: 4) {
                VStack(spacing: 0) {
                    ForEach(Array(rows.enumerated()), id: \.element.id) { index, row in
                        RankedRow(row: row)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 10)
                        if index < rows.count - 1 {
                            Divider().padding(.leading, 12)
                        }
                    }
                    Divider().padding(.leading, 12)
                    NavigationLink {
                        RankingList(answer: answer, filter: filter)
                    } label: {
                // The full ranking is NOT budget-filtered — D-125 publishes every ranked model
                // beside the three picks, deliberately. A review found the payload giving two
                // accounts of one query: `budget=low` reporting 25 eligible models and then
                // serving 58 rows whose most expensive is $36/1M, with no marker on any row.
                //
                // The engine is right and the SCREEN was silent, so the screen says it. Both
                // numbers are already in the payload; nothing here is computed, and no contract
                // moved. It reads as one sentence when they agree and as a disclosure when they
                // do not.
                        HStack {
                            Text(
                                answer.eligibleCount < answer.ranking.count
                                    ? "See all \(answer.ranking.count) — "
                                        + "\(answer.eligibleCount) fit your budget"
                                    : "See all \(answer.ranking.count)"
                            )
                            .font(.subheadline)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(.tertiary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 12)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                }
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
        filterRanking(rows, by: filter, name: \.model, vendor: \.vendor)
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
        // D-135. Classified and DEDUPLICATED in the Engine, where it is tested, rather than here
        // where nothing executes. What arrives is already: every fact, each said once, each
        // carrying how loudly it should speak.
        //
        // Before this, five of the nine surfaces printed the same fact twice in the same orange —
        // `source_health.notice` and `evidence_dating_note` both saying the benchmark publishes no
        // evaluation dates — and the one notice that was real and actionable, SWE-bench at 179
        // days, wore exactly the same triangle as the five that can never clear.
        let items = classifyDisclosures(
            stalenessNotice: answer.sourceHealth?.notice ?? answer.staleNotice,
            ageDays: (answer.sourceHealth?.sources ?? []).map(\.ageDays),
            datingNote: answer.evidenceDatingNote,
            effortMixNotice: answer.effortMixNotice,
            closeCall: answer.closeCall
        )
        return VStack(alignment: .leading, spacing: 8) {
            ForEach(items, id: \.text) { item in
                switch item.weight {
                case .state:
                    // Became true, can become false. Worth interrupting for.
                    Label(item.text, systemImage: "exclamationmark.triangle.fill")
                        .font(.caption)
                        .foregroundStyle(.orange)
                case .property:
                    // A fact about the source. Present, readable, and not shouting — no icon,
                    // because five identical triangles is how the real one got lost.
                    Text(item.text)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
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
            // **The strip keeps where the reader put it.** Selecting a category rebuilds this
            // view, and without a bound position SwiftUI recreates the ScrollView at offset zero —
            // so the owner scrolled right to Mathematics, tapped it, and the strip snapped back to
            // Coding with no chip visibly selected. He had to scroll again to see what he had
            // chosen.
            //
            // `scrollPosition(id:)` persists the visible chip across the rebuild. It does NOT
            // scroll on his behalf: the strip moves when he moves it and at no other time, which
            // is what he asked for.
            ScrollViewReader { proxy in
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
                        .id(category.id)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }
            // **No `.scrollPosition(id:)` here, and that is the fix.** The first attempt bound the
            // scroll offset AND asked a `ScrollViewReader` to centre the selection; the two
            // control the same thing and the binding wins, so the programmatic scroll silently did
            // nothing. Measured, not reasoned: tapping a clipped chip selected it and the strip did
            // not move a pixel.
            //
            // Centring on selection subsumes what the binding was for. The strip cannot snap back
            // to the start, because on every change it goes to the chosen chip instead.
            // CENTRE the selected chip. Keeping the reader's scroll offset was the first fix and
            // it was not enough: he scrolled right, tapped `Web development`, and the chip he had
            // just chosen sat half-cut against the right edge — the strip had not jumped back to
            // the start, but the thing he selected was not the thing he could see.
            //
            // `anchor: .center` rather than `.leading`, because a chip pinned to the left edge
            // hides the categories before it and reads as "you are at the start of the list"
            // again. The move happens only on a SELECTION; dragging is still entirely his.
            .onChange(of: task) { _, now in
                withAnimation(.easeOut(duration: 0.25)) {
                    proxy.scrollTo(now, anchor: .center)
                }
            }
            }
            .background(.bar)
        }
    }

    /// Route the typed question to a surface, then load it.
    private func ask() async {
        let typed = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !typed.isEmpty else { return }
        routingInFlight = true
        defer { routingInFlight = false }

        let known = categories.map(\.id)
        guard !known.isEmpty else { return }

        let outcome = await router.route(typed, within: known)
        routing = outcome
        // The engine is asked for a SURFACE and nothing else. What the reader typed never reaches
        // it, and the only thing the router contributes to the request is which of nine ids it is
        // (REQ-RTR-004 — the scoring path is untouched, D-104).
        if outcome.categoryID != task {
            task = outcome.categoryID
            await load()
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


// MARK: - The design vocabulary (M11-W3.5)
//
// Three shapes and nothing else: a CARD, a BADGE, and a SECTION TITLE. The owner asked for
// something less plain after using the app, and chose "card-based and breathing" from three
// directions. Kept to three shapes deliberately — a screen whose vocabulary grows past that stops
// being consistent and starts being decorated, and this product's whole claim is that it says
// exactly what it measured.
//
// **Nothing about WHAT is shown changed.** Every disclosure the list carried is still on screen:
// the unmeasured sentence, the ordering note, the stale-evidence notice, the effort-mix notice,
// "See all N — M fit your budget". A design pass that quietly drops one of those would be the
// worst outcome available here, because the disclosures are what make this product honest and not
// one of them is load-bearing to a layout.

/// A rounded surface with real padding. The one container everything sits in.
struct Card<Content: View>: View {
    var padding: CGFloat = 16
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
    }
}

/// The pick label — "Best Quality", "Best Value", "Budget Pick" — as a badge rather than a caption.
///
/// Each pick answers a DIFFERENT question, and the label is the only thing that says which. As a
/// small tinted caption it read as decoration; as a badge it reads as the heading it actually is.
struct PickBadge: View {
    let label: String

    var body: some View {
        Text(label.replacingOccurrences(of: "_", with: " ").uppercased())
            .font(.caption2.weight(.semibold))
            .tracking(0.6)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Capsule().fill(Color.accentColor.opacity(0.14)))
            .foregroundStyle(Color.accentColor)
    }
}

/// A surface's name, above its cards.
struct SectionTitle: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.title3.weight(.semibold))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 4)
    }
}

struct PickRow: View {
    let pick: Pick
    /// The surface's full ranking, so this row can say WHERE the model sits. Optional because a
    /// surface can serve picks with nothing ranked behind them.
    var ranking: [RankedModel] = []
    /// What the score's scale is, in one line. `nil` when the metric is one we cannot explain —
    /// a missing explanation is a gap, a wrong one is a lie.
    var scale: String?

    private var pickMeaning: String? {
        var parts: [String] = []
        if let rank = rankOf(pick.model, in: ranking, name: \.model) {
            parts.append("#\(rank) of \(ranking.count)")
        }
        if let scale { parts.append(scale) }
        parts.append(priceInPages(pick.blendedPerM))
        return parts.isEmpty ? nil : parts.joined(separator: "  ·  ")
    }

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 8) {
                PickBadge(label: pick.label)
                VStack(alignment: .leading, spacing: 2) {
                    Text(pick.model).font(.title3.weight(.semibold))
                    Text(pick.vendor).font(.subheadline).foregroundStyle(.secondary)
                }
                Text(Format.scoreAndPrice(pick.score, pick.metric, pick.blendedPerM))
                    .font(.subheadline.weight(.medium))
                    .monospacedDigit()
                // REQ-CMP-001/002. The exact number is never replaced — it gains a companion.
                // `161.7 ECI` is unreadable because its scale is published nowhere; `#1 of 58` is
                // readable by anyone. The rank is a POSITION in the engine's own ordering, so
                // nothing is re-sorted (Trap 1).
                if let meaning = pickMeaning {
                    Text(meaning)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                Text(pick.why).font(.footnote).foregroundStyle(.secondary)
                if let tradeOff = pick.tradeOff {
                    Text(tradeOff).font(.footnote).foregroundStyle(.tertiary)
                }
            }
        }
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
        ScrollViewReader { proxy in
            List {
                ForEach(rows) { row in
                    RankedRow(row: row).id(row.id)
                }
            }
            // **Back to the top whenever the filter changes**, and this is the defect the owner
            // reported as "it filters by category, not by model name". It never did: on `coding`,
            // `c` matches 12 of 44 models and the first is Claude Opus 4.7. He was scrolled
            // halfway down a 44-row list; typing shrank it to 12, the offset clamped to the end,
            // and what he was left looking at were the three lowest-scoring matches — GPT-5.2
            // Codex, Qwen3 Coder, GPT-5.1 Codex — which read exactly like a category filter.
            //
            // A list that changes underneath the reader has to take them to the top of what they
            // are now looking at. Anything else shows them an arbitrary slice of a new list and
            // lets them draw a conclusion from it, which is precisely what happened.
            .onChange(of: filter) { _, _ in
                guard let first = rows.first else { return }
                proxy.scrollTo(first.id, anchor: .top)
            }
        }
        .navigationTitle(answer.title)
        .searchable(text: $filter, prompt: "Filter by model name")
    }

    private var rows: [RankedModel] {
        filterRanking(answer.ranking, by: filter, name: \.model, vendor: \.vendor)
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
