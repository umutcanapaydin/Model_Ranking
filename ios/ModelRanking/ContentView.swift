//  ContentView.swift — the home screen (M8-W2; the front door rebuilt at M13-W3).
//
//  M13-W3, REQ-ASK-001..004. The owner, translated from Turkish: *"it felt like a search bar, not an
//  AI"*. The question field is now the only input on the home screen. The category strip and the
//  budget strip are gone: the council removed the budget strip unanimously, and the nine surfaces
//  moved behind a `Change` sheet reached from the matched-surface row, which keeps the correction
//  D-126 requires. The model-name filter moved to the full ranking. Two text fields on one screen
//  is why the question bar read as the weaker of two search boxes.
//
//  Every decision this screen makes lives in the Engine, where `swift test` runs it
//  (`FrontDoor.swift`, `Uncertainty.swift`). This file renders.
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
    /// Fetched from the engine on every load, never listed here. See `EngineClient.categories()`.
    @State private var categories: [Category] = []
    @State private var task = "coding"
    /// What the reader is typing, and what they had typed when they last asked (D-126).
    @State private var question = ""
    @State private var asked = ""
    @State private var routing: RoutingOutcome?
    @State private var routingInFlight = false
    /// REQ-ASK-001. Explicit, because the field used to give no visible response to a tap and never
    /// raised the software keyboard (handover §3.3). The field, its icon and the send button all
    /// act on this one binding.
    @FocusState private var questionFocused: Bool
    /// REQ-ASK-004. Every load takes a ticket, and only the latest may change the screen.
    @State private var gate = RequestGate()
    /// REQ-ASK-004 for the QUESTION (M13-W3 review BLOCKING-2): routing is the slow half of a
    /// question, and a `Change` selection made while it runs retires its ticket.
    @State private var routingGate = RequestGate()
    /// A reload after the first: the answers stay on screen and the progress shows in the card,
    /// rather than the whole screen, question field included, being replaced by a spinner.
    @State private var reloading = false
    /// The `Change` sheet (REQ-ASK-002).
    @State private var choosingSurface = false
    /// The reader's language. `@AppStorage` so the choice survives a relaunch — a flag switch that
    /// forgets is a flag switch nobody uses twice.
    @AppStorage("language") private var language: Language = .english
    private let router = TieredRouter()
    /// Whether the on-device tier can run here, said as quiet help when it cannot.
    private let onDevice = TieredRouter.onDeviceState()
    /// Every question is asked at `unlimited` since the budget strip went (M13-W3). The engine still
    /// takes a budget, and `/v1/budgets` still publishes the caps for other consumers (D-134).
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
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    // D-136. Two flags, because a flag is the one label that needs no language to
                    // read — which is the whole problem this milestone is about.
                    Picker("", selection: $language) {
                        ForEach(Language.allCases) { option in
                            Text(option.flag).tag(option)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 96)
                }
            }
            .navigationTitle(UIText.title(language))
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $choosingSurface) { surfaceSheet }
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
                questionCard

                // The surface the reader SELECTED speaks first. `task=coding` expands server-side
                // to two answers and `/v1` says in its own payload that their order carries no
                // meaning — so it always arrived alphabetically, and "Agentic coding" answered
                // every question about coding. Ordering ANSWERS is not the re-sorting Trap 1
                // forbids: that rule is about reordering models inside a ranking, which IS the
                // engine's answer.
                ForEach(ordered) { answer in
                    VStack(alignment: .leading, spacing: 12) {
                        SectionTitle(text: UIText.surface(id: answer.surface, engineTitle: answer.title, language))

                        if answer.picks.isEmpty && answer.ranking.isEmpty {
                            Card { emptyAnswer(answer) }
                        } else {
                            // REQ-UNC-001, the owner's ruling of 2026-09-15: every position is the
                            // RANGE the engine's own margin (D-138) cannot narrow. Computed ONCE per
                            // answer so the picks, the preview and the full list cannot disagree.
                            let info = category(for: answer)
                            let ranges = rankRanges(
                                answer.ranking.map(\.score), margin: info?.closeCallMargin
                            )
                            ForEach(answer.picks) { pick in
                                PickRow(
                                    pick: pick,
                                    ranking: answer.ranking,
                                    scale: scaleExplanation(for: answer.metric, in: language),
                                    language: language,
                                    ranges: ranges,
                                    secondaryBenchmark: info?.secondaryBenchmark,
                                    secondaryAgeDays: info?.secondaryAgeDays
                                )
                            }
                            rankingPreview(
                                answer,
                                ranges: ranges,
                                leaderNote: leaderSentence(
                                    ranges: ranges, margin: info?.closeCallMargin,
                                    metric: answer.metric, language
                                )
                            )
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
        }
        // The bottom search field this compensated for (`.padding(.bottom, 88)`, handover §3.2) is
        // gone from this screen, and the safe area is the platform's number rather than ours.
        .safeAreaPadding(.bottom)
        .scrollDismissesKeyboard(.interactively)
        .background(Color(.systemGroupedBackground))
        .refreshable { await load() }
    }

    // MARK: - The front door (REQ-ASK-001..003)

    private var questionCard: some View {
        Card {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 10) {
                    Image(systemName: "text.bubble")
                        .foregroundStyle(.secondary)
                        .onTapGesture { questionFocused = true }
                    TextField(UIText.askPlaceholder(language), text: $question)
                        .focused($questionFocused)
                        .submitLabel(.send)
                        .onSubmit(submit)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                    // A visible way to send. With a hardware keyboard attached and focus lost,
                    // `.onSubmit` was the ONLY way, which meant no way (handover §3.2).
                    Button(action: submit) {
                        if routingInFlight || reloading {
                            ProgressView().controlSize(.small)
                        } else {
                            Image(systemName: "arrow.up.circle.fill").font(.title2)
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.tint)
                    // No surfaces, nothing to route to: disabled and SAID (below), rather than a
                    // spinner followed by a question silently dropped (review MINOR-7).
                    .disabled(!canSubmit(question, inFlight: routingInFlight) || categories.isEmpty)
                    .accessibilityLabel(UIText.send(language))
                }
                Divider()
                matchedSurfaceRow
            }
        }
    }

    /// What the screen understood, and the one tap that corrects it (REQ-ASK-002).
    @ViewBuilder
    private var matchedSurfaceRow: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Group {
                    if let outcome = routing,
                       let echo = echoLine(question: asked, surfaceTitle: surfaceTitle(outcome.categoryID))
                    {
                        Text(echo)
                    } else {
                        Text("\(UIText.showing(language)): \(surfaceTitle(task))")
                    }
                }
                .font(.subheadline.weight(.medium))
                Spacer(minLength: 8)
                Button(UIText.change(language)) { choosingSurface = true }
                    .font(.subheadline)
                    .disabled(categories.isEmpty)
            }
            if categories.isEmpty {
                Text(UIText.surfacesUnavailable(language))
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            if let outcome = routing {
                // REQ-ASK-003: for an unmeasured question this is the sentence ABOVE the ranking
                // saying what that ranking cannot tell the reader.
                Text(routingNotice(outcome, language))
                    .font(.footnote)
                    .foregroundStyle(outcome.unmeasured ? .orange : .secondary)
                if !outcome.alternatives.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            Text(outcome.unmeasured
                                 ? UIText.closestMeasured(language)
                                 : UIText.alternatives(language))
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                            ForEach(outcome.alternatives, id: \.self) { id in
                                Button(surfaceTitle(id)) { select(id) }
                                    .font(.footnote)
                                    .buttonStyle(.bordered)
                                    .controlSize(.small)
                            }
                        }
                    }
                }
                // Quiet help, never an error: the wording tier still routes. Shown only when the
                // question was NOT routed by the model, since that is the only time it explains
                // anything the reader is looking at.
                if outcome.tier != .model, let help = onDevice.help(language) {
                    Text(help)
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }
        }
    }

    /// Every surface the engine serves, two to a row. The correction reaches all nine.
    private var surfaceSheet: some View {
        NavigationStack {
            ScrollView {
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    ForEach(surfaceChoices(categories, selected: task, language)) { choice in
                        Button { select(choice.id) } label: {
                            Text(choice.title)
                                .font(.subheadline.weight(choice.isSelected ? .semibold : .regular))
                                .multilineTextAlignment(.leading)
                                .frame(maxWidth: .infinity, minHeight: 52, alignment: .leading)
                                .padding(12)
                                .background(
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .fill(choice.isSelected
                                              ? AnyShapeStyle(Color.accentColor.opacity(0.18))
                                              : AnyShapeStyle(Color(.secondarySystemGroupedBackground)))
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(16)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle(UIText.chooseSurface(language))
            .navigationBarTitleDisplayMode(.inline)
        }
        .presentationDetents([.medium, .large])
    }

    /// A surface's title in the reader's language, from the engine's own list.
    private func surfaceTitle(_ id: String) -> String {
        let title = categories.first { $0.id == id }?.title ?? id
        return UIText.surface(id: id, engineTitle: title, language)
    }

    /// The top of the full ranking, plus the door to the rest.
    @ViewBuilder
    private func rankingPreview(_ answer: Answer, ranges: [RankRange], leaderNote: String?)
        -> some View
    {
        // The picks are already on screen in large type; repeating them four lines below in small
        // type was the first thing the owner pointed at. Five models visible in total, split by
        // however many DISTINCT picks there turned out to be — one model can hold two pick labels.
        let picked = Set(answer.picks.map(\.model))
        let rows = previewRows(
            ranking: answer.ranking,
            pickedModels: answer.ranking.filter { picked.contains($0.model) },
            visibleTotal: homePreviewCount
        )
        if !rows.isEmpty {
            // The remaining models live in ONE card rather than a card each: they are the tail of
            // a list, not three separate answers, and giving them the same weight as the picks
            // would undo the distinction the picks exist to make.
            Card(padding: 4) {
                VStack(spacing: 0) {
                    ForEach(Array(rows.enumerated()), id: \.element.id) { index, row in
                        RankedRow(
                            row: row,
                            rank: rankOf(row.model, in: answer.ranking, name: \.model)
                                .flatMap { shortRankLabel(at: $0 - 1, in: ranges) },
                            language: language
                        )
                            .padding(.horizontal, 12)
                            .padding(.vertical, 10)
                        if index < rows.count - 1 {
                            Divider().padding(.leading, 12)
                        }
                    }
                    Divider().padding(.leading, 12)
                    NavigationLink {
                        // The model-name filter lives HERE since M13-W3, on the full list where
                        // narrowing by name is useful, and not on the home screen beside the
                        // question field.
                        RankingList(
                            answer: answer, filter: "", language: language,
                            ranges: ranges, leaderNote: leaderNote
                        )
                    } label: {
                // The full ranking is NOT budget-filtered — D-125 publishes every ranked model
                // beside the three picks, deliberately. `UIText.seeAll` reads as one sentence when
                // the eligible count and the ranking agree and as a disclosure when they do not;
                // at `unlimited` they agree, and the comparison stays for the day they do not.
                        HStack {
                            Text(UIText.seeAll(answer.ranking.count, eligible: answer.eligibleCount, language))
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
        }
    }

    /// The discovery entry for an answer's surface: its margin and its second board (D-138).
    private func category(for answer: Answer) -> Category? {
        categories.first { $0.id == answer.surface }
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

    // MARK: - Actions

    /// Send the question. Return and the button both come here, and both ask `canSubmit`.
    ///
    /// `routingInFlight` is set HERE, synchronously, before the task starts: set inside `ask()`,
    /// a second tap could land between the tap and the task's first line and route twice.
    private func submit() {
        guard canSubmit(question, inFlight: routingInFlight) else { return }
        routingInFlight = true
        questionFocused = false
        Task { await ask() }
    }

    /// Route the typed question to a surface, then load it.
    ///
    /// REQ-ASK-004 for the question (M13-W3 review BLOCKING-2). Routing is the slow half, and the
    /// reader can pick a surface from `Change` while it runs; the result is applied only if no
    /// selection has been made since. The echo and its sentence appear once the answer they describe
    /// has LOADED, so "Below is the general chat ranking" never sits above the previous surface's
    /// ranking (review MINOR-8).
    private func ask() async {
        defer { routingInFlight = false }
        let typed = question.trimmingCharacters(in: .whitespacesAndNewlines)
        if categories.isEmpty { await load() }
        let known = categories.map(\.id)
        guard !typed.isEmpty, !known.isEmpty else { return }

        let ticket = routingGate.begin()
        let outcome = await router.route(typed, within: known)
        guard routingGate.isCurrent(ticket) else { return }
        // The engine is asked for a SURFACE and nothing else. What the reader typed never reaches
        // it, and the only thing the router contributes to the request is which of nine ids it is
        // (REQ-RTR-004 — the scoring path is untouched, D-104).
        if outcome.categoryID != task {
            task = outcome.categoryID
            await load()
            guard routingGate.isCurrent(ticket) else { return }
        }
        asked = typed
        routing = outcome
    }

    /// The reader corrected the surface: from the sheet, or from an alternative under the echo.
    /// The echo describes the ROUTER's choice, so it goes once the reader has overruled it, and a
    /// question still routing is retired with it.
    private func select(_ id: String) {
        choosingSurface = false
        routingGate.invalidate()
        routing = nil
        guard id != task else { return }
        task = id
        Task { await load() }
    }

    private func load() async {
        // REQ-ASK-004. The ticket is compared at the moment of APPLYING a result, so a slower
        // answer for a surface the reader has already left is dropped rather than rendered.
        let ticket = gate.begin()
        if case .loaded = state {
            reloading = true
        } else {
            state = .loading
        }
        defer {
            if gate.isCurrent(ticket) { reloading = false }
        }
        // Re-read on every load (M13-W2 review MINOR-1). The second board's age is a fact about
        // the ARTIFACT, which the refresh replaces every twelve hours. A failed re-read keeps the
        // list it had: a discovery call that can blank the product is a worse dependency than the
        // facts it adds.
        if let fresh = try? await client.categories(), !fresh.isEmpty, gate.isCurrent(ticket) {
            categories = fresh
        }
        do {
            // One request carries every surface for the coding intent (Ruling A), so the home
            // screen cannot show one answer while another is still loading.
            let recommendation = try await client.recommendation(task: task, budget: budget)
            guard gate.isCurrent(ticket) else { return }
            state = .loaded(recommendation.answers, orderingNote: recommendation.orderingNote)
        } catch let error as EngineError {
            guard gate.isCurrent(ticket) else { return }
            state = .failed(error)
        } catch {
            guard gate.isCurrent(ticket) else { return }
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

/// The pick label — "Best Quality", "Best Value", "Affordable Pick" — as a badge rather than a
/// caption.
///
/// Each pick answers a DIFFERENT question, and the label is the only thing that says which. As a
/// small tinted caption it read as decoration; as a badge it reads as the heading it actually is.
struct PickBadge: View {
    /// Already localised by the caller — `UIText.pickLabel`. The badge renders a word; deciding
    /// WHICH word is a language question and does not belong in a view.
    let label: String

    var body: some View {
        Text(label)
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
    /// D-136. The sentences below are composed from the engine's FACTS in this language, and fall
    /// back to the engine's own English when the fact carries a reason this build does not know.
    /// **Falling back is correct**; inventing a Turkish sentence for a reason we do not understand
    /// would be the product speaking without knowing what it is saying.
    var language: Language = .english
    /// REQ-UNC-001. The answer's rank ranges, computed once by the caller from the engine's margin.
    /// `nil` renders the exact positions that shipped before D-138.
    var ranges: [RankRange]?
    /// REQ-UNC-002. The surface's second board and its age, from `/v1/categories` (D-138).
    var secondaryBenchmark: String?
    var secondaryAgeDays: Int?

    private var whyText: String {
        whySentence(pick.whyFactDictionary, in: language) ?? pick.why
    }

    /// REQ-UNC-002: a count a reader can check, and never the word "confidence".
    private var evidenceText: String? {
        evidenceLine(
            verdict: pick.confidence,
            basis: pick.confidenceBasis,
            secondaryScore: pick.secondaryScore,
            secondaryBenchmark: secondaryBenchmark,
            secondaryAgeDays: secondaryAgeDays,
            evidenceDate: pick.evidenceDate,
            language
        )
    }

    private var tradeOffText: String? {
        guard let prose = pick.tradeOff else { return nil }
        return tradeOffSentence(pick.tradeOffFactDictionary, in: language) ?? prose
    }

    /// REQ-UNC-001: `#1–27 of 50` where the engine's margin cannot narrow the position, and a single
    /// number only where it can. `nil` when the pick is not in the ranking it came with.
    private var rankText: String? {
        guard let position = rankOf(pick.model, in: ranking, name: \.model) else { return nil }
        return rankLabel(
            at: position - 1,
            in: ranges ?? rankRanges(ranking.map(\.score), margin: nil),
            of: ranking.count,
            language
        )
    }

    private var pickMeaning: String? {
        var parts: [String] = []
        if let rank = rankText { parts.append(rank) }
        if let scale { parts.append(scale) }
        parts.append(priceInPages(pick.blendedPerM, in: language))
        return parts.isEmpty ? nil : parts.joined(separator: "  ·  ")
    }

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 8) {
                PickBadge(label: UIText.pickLabel(pick.label, language))
                VStack(alignment: .leading, spacing: 2) {
                    Text(pick.model).font(.title3.weight(.semibold))
                    Text(pick.vendor).font(.subheadline).foregroundStyle(.secondary)
                }
                // REQ-CMP-004: a score says what it is out of, or only the rank is shown — and
                // where there is no rank to show, the engine's own number stays (MINOR-8).
                Text(figuresLine(
                    score: pick.score, metric: pick.metric, blendedPerM: pick.blendedPerM, language,
                    ranked: rankText != nil
                ))
                    .font(.subheadline.weight(.medium))
                    .monospacedDigit()
                // REQ-CMP-001/002, amended for ECI by D-140: a number either says what it is out of
                // or gives way to the rank below, which anyone can read. The rank is a POSITION in
                // the engine's own ordering, so nothing is re-sorted (Trap 1).
                if let meaning = pickMeaning {
                    Text(meaning)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                Text(whyText).font(.footnote).foregroundStyle(.secondary)
                if let evidence = evidenceText {
                    Text(evidence).font(.footnote).foregroundStyle(.secondary)
                }
                if let tradeOff = tradeOffText {
                    Text(tradeOff).font(.footnote).foregroundStyle(.tertiary)
                }
            }
        }
    }
}

struct RankedRow: View {
    let row: RankedModel
    /// `5–13`, `1`: the row's position as the engine's margin allows it (REQ-UNC-001). `nil` shows
    /// none.
    var rank: String?
    /// Passed in, never read from storage here — see `RankingList`: two views on one screen
    /// disagreeing about the reader's language would be worse than one that is untranslated.
    var language: Language = .english

    var body: some View {
        HStack {
            if let rank {
                Text(rank)
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .frame(minWidth: 30, alignment: .leading)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(row.model)
                Text(row.vendor).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text(figuresLine(
                score: row.score, metric: row.metric, blendedPerM: row.blendedPerM, language,
                ranked: rank != nil
            ))
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
    /// Passed in rather than read from storage here: a detail screen that could disagree with the
    /// screen that opened it about what language the reader is in would be worse than one that is
    /// simply not translated.
    var language: Language = .english
    /// Computed by the home screen from the engine's margin, so both screens agree on every range.
    var ranges: [RankRange] = []
    /// How many models the benchmark cannot separate from the leader. Said here, where the ranges
    /// appear in bulk, and not on the home screen, where the engine's `close_call` already says it.
    var leaderNote: String?

    var body: some View {
        ScrollViewReader { proxy in
            List {
                Section {
                    ForEach(rows) { row in
                        RankedRow(row: row, rank: rank(of: row), language: language).id(row.id)
                    }
                } header: {
                    if let leaderNote {
                        Text(leaderNote).textCase(nil)
                    }
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
        .navigationTitle(UIText.surface(id: answer.surface, engineTitle: answer.title, language))
        .searchable(text: $filter, prompt: UIText.filterPlaceholder(language))
    }

    private var rows: [RankedModel] {
        filterRanking(answer.ranking, by: filter, name: \.model, vendor: \.vendor)
    }

    /// Read from the FULL ranking, never the filtered one. Filtering narrows what is shown; a
    /// model's tie with the leader does not change because the reader typed a letter.
    private func rank(of row: RankedModel) -> String? {
        rankOf(row.model, in: answer.ranking, name: \.model)
            .flatMap { shortRankLabel(at: $0 - 1, in: ranges) }
    }
}

// `Format` moved to the Engine at M13-W4 as `figuresLine` / `priceTag` (`Scores.swift`), where
// `swift test` runs it. The rule it carried is unchanged: numbers are printed in POSIX form,
// never in the reader's locale, because `$2,06` reads as two thousand and six.
