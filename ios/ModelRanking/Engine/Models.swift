//  Models.swift — the /v1 contract, in Swift.
//
//  These types are a MIRROR of the payload the engine serves, not a design of their own. Every
//  field here exists because `PUBLIC_ANSWER_FIELDS` or `PUBLIC_PICK_FIELDS` in
//  `src/app/adapter/main.py` publishes it, and the shape was read off a live response rather than
//  remembered — a Swift struct written from an imagined payload is exactly the "typed-out
//  enumeration" this project has been caught by five times.
//
//  **Nothing in this file computes.** No sorting, no arithmetic on prices or scores, no derived
//  "best" flag. The engine decides all of that (D-104, D-105, D-109) and the client renders it.
//  If a screen needs a value that is not here, that is a finding against /v1 (D-124), not a
//  licence to compute it on the phone.

import Foundation

/// The whole response to one question.
struct Recommendation: Decodable {
    let apiVersion: String
    let query: Query
    /// Both coding answers arrive here when the task is `coding` — Ruling A, frozen by D-115.
    let answers: [Answer]
    /// The engine's own words about why the order carries no meaning. Rendered, never paraphrased.
    let orderingNote: String
    /// The engine states this explicitly so a client cannot infer ranking from position.
    let surfacesAreRanked: Bool

    enum CodingKeys: String, CodingKey {
        case apiVersion = "api_version"
        case query
        case answers
        case orderingNote = "ordering_note"
        case surfacesAreRanked = "surfaces_are_ranked"
    }
}

/// One rankable surface, as the engine advertises it on `/v1/categories`.
///
/// Fetched rather than hardcoded, deliberately. The engine derives this list from CATEGORIES; a
/// copy of it in Swift would be a second roster to keep in step, and this project has already
/// spent two milestones on the cost of a list typed out by hand.
struct Category: Decodable, Identifiable, Equatable {
    let id: String
    let title: String
    let primaryBenchmark: String
    let metric: String
    let rankingEffort: String?
    /// D-138 (M13-W2). The margin inside which this surface's engine calls two models
    /// indistinguishable, on the surface's own scale. Optional because an engine older than D-138
    /// does not send it, and a client that then invented one would be computing on the phone the
    /// very number this file promises never to compute. Absent means exact positions, not "no ties".
    let closeCallMargin: Double?
    /// The evidence-only second board, and how many days old its newest run is against the
    /// artifact's own anchor. A `nil` age: the board publishes no dates, or the artifact is unread.
    let secondaryBenchmark: String?
    let secondaryAgeDays: Int?
    /// D-143 (M14-W4). The pinned reference an Elo score is read out of 100 against. `nil` from an
    /// engine older than W4, and for a scale that is already out of 100 or has no anchor (ECI).
    let scoreAnchor: Double?
    /// D-152 (M16-W1). The surface's floor on its own scale; `nil` from an engine older than W1.
    let minQuality: Double?
    /// D-153 (M16-W1). A code for what the price leaves out, on the search surfaces only.
    let priceExcludes: String?
    /// D-168 (M17-W5). The board this surface ranks on, by id: the first board a question selecting
    /// this surface combines. `nil` from an engine older than W5, which then combines nothing.
    let primaryBoard: String?
    /// D-188 (M20-W1). The surface's family: every board that measures its task, the primary first,
    /// by id. `nil` from an engine older than M20: the surface then has no family on the phone.
    let boards: [String]?
    /// The M20 repo review's M1 (D-188 clause 6): the family's board a refinement takes the place of,
    /// its board of Arena's text vote. `nil` where no refinement refines the surface, or from an engine
    /// older than the M20 closure (a refinement then joins beside the family, as before).
    let refinedBoard: String?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case primaryBenchmark = "primary_benchmark"
        case metric
        case rankingEffort = "ranking_effort"
        case closeCallMargin = "close_call_margin"
        case secondaryBenchmark = "secondary_benchmark"
        case secondaryAgeDays = "secondary_age_days"
        case scoreAnchor = "score_anchor"
        case minQuality = "min_quality"
        case priceExcludes = "price_excludes"
        case primaryBoard = "primary_board"
        case boards
        case refinedBoard = "refined_board"
    }
}

struct CategoryList: Decodable {
    let categories: [Category]
}

struct Query: Decodable {
    let task: String
    let budget: String
}

/// One surface's answer. A surface with nothing to say still arrives, carrying the reason.
struct Answer: Decodable, Identifiable {
    let surface: String
    let title: String
    let primaryBenchmark: String
    let metric: String
    let eligibleCount: Int
    let frontierSize: Int
    let picks: [Pick]

    /// Present when `picks` is empty. The engine distinguishes "nothing fits your budget" from
    /// "this surface has no evidence to rank" — two different sentences, and M7 spent a security
    /// round making sure they are not collapsed into one. The client must not collapse them either.
    let unavailableReason: String?
    /// D-176 clause 7 (M18-W2 review M2): which reason, as a code: `no_evidence`, `over_budget`,
    /// `unreadable`. The app composes the sentence from it.
    let unavailableReasonCode: String?

    let closeCall: String?
    /// D-176 (M18-W2): the values `closeCall` quotes, so `Notices.swift` says it in either language.
    let closeCallFact: CloseCallFact?
    let staleNotice: String?
    let effortMixNotice: String?
    let rankingEffort: String?
    let evidenceDating: String?
    let evidenceDatingNote: String?
    let sources: [String]
    let sourceHealth: SourceHealth?

    /// Every model the engine ranked for this surface, in ITS order (D-125).
    ///
    /// This is not "more picks". The three picks answer three different questions; this answers
    /// one, in score order. **The client never re-sorts it** (M8 plan, Trap 1) — re-ordering the
    /// engine's answer is answering a different question with its numbers.
    let ranking: [RankedModel]

    var id: String { surface }

    enum CodingKeys: String, CodingKey {
        case surface, title, metric, picks, sources
        case primaryBenchmark = "primary_benchmark"
        case eligibleCount = "eligible_count"
        case frontierSize = "frontier_size"
        case unavailableReason = "unavailable_reason"
        case unavailableReasonCode = "unavailable_reason_code"
        case closeCall = "close_call"
        case closeCallFact = "close_call_fact"
        case staleNotice = "stale_notice"
        case effortMixNotice = "effort_mix_notice"
        case rankingEffort = "ranking_effort"
        case evidenceDating = "evidence_dating"
        case evidenceDatingNote = "evidence_dating_note"
        case sourceHealth = "source_health"
        case ranking
    }
}

/// One model's position in a surface's ranking. Carries no `label`, `why` or `trade_off`, because
/// nothing chose it — those belong to a `Pick`.
struct RankedModel: Decodable, Identifiable, Equatable {
    let model: String
    let vendor: String
    let score: Double
    let metric: String
    let secondaryScore: Double?
    let blendedPerM: Double
    let inputPerM: Double
    let outputPerM: Double
    let evidenceDate: String?
    let harness: String
    let effort: String?

    var id: String { model }

    enum CodingKeys: String, CodingKey {
        case model, vendor, score, metric, harness, effort
        case secondaryScore = "secondary_score"
        case blendedPerM = "blended_per_m"
        case inputPerM = "input_per_m"
        case outputPerM = "output_per_m"
        case evidenceDate = "evidence_date"
    }
}

/// How fresh this surface's evidence is, on a wall clock. `notice` is the sentence a user reads.
struct SourceHealth: Decodable, Equatable {
    let benchmark: String
    let stale: Bool
    let notice: String?
    let sources: [SourceRow]
    /// D-176 clause 7: why `sources` is empty, when it is: `no_source` or `unreadable`.
    let reason: String?
}

struct SourceRow: Decodable, Identifiable, Equatable {
    let source: String
    let rows: Int
    let newestRunDate: String?
    let ageDays: Int?
    let stale: Bool

    var id: String { source }

    enum CodingKeys: String, CodingKey {
        case source, rows, stale
        case newestRunDate = "newest_run_date"
        case ageDays = "age_days"
    }
}

/// One labelled answer. `label` is the engine's, not the client's: `best_quality`, `best_value`,
/// `budget_pick`.
struct Pick: Decodable, Identifiable {
    let label: String
    let model: String
    let vendor: String
    let score: Double
    let metric: String
    let secondaryScore: Double?
    let blendedPerM: Double
    let inputPerM: Double
    let outputPerM: Double
    let evidenceDate: String?
    let harness: String
    let effort: String?
    let higherEffort: String?
    let higherEffortScore: Double?
    let effortNote: String?
    let confidence: String
    let confidenceBasis: String
    /// The engine's explanation of why this model was chosen. Displayed verbatim.
    let why: String
    /// What this choice costs relative to the leader. Absent when there is nothing to trade off.
    let tradeOff: String?
    /// D-136: the machine-readable half of the two sentences above. `[String: Any]` is not
    /// `Decodable`, so these arrive through `JSONValue` and are unwrapped on demand — the client
    /// composes from them, and falls back to `why` / `tradeOff` when a reason is one this build
    /// does not know.
    let whyFact: JSONValue?
    let tradeOffFact: JSONValue?
    /// D-182 (#138): the id of the model this pick ranks, so one model is one card, as the engine
    /// decides it. Absent from an engine older than D-182; never shown.
    let modelId: String?

    var whyFactDictionary: [String: Any] { whyFact?.dictionary ?? [:] }
    var tradeOffFactDictionary: [String: Any] { tradeOffFact?.dictionary ?? [:] }

    var id: String { "\(label)-\(model)" }

    enum CodingKeys: String, CodingKey {
        case label, model, vendor, score, metric, harness, effort, confidence, why
        case whyFact = "why_fact"
        case tradeOffFact = "trade_off_fact"
        case secondaryScore = "secondary_score"
        case blendedPerM = "blended_per_m"
        case inputPerM = "input_per_m"
        case outputPerM = "output_per_m"
        case evidenceDate = "evidence_date"
        case higherEffort = "higher_effort"
        case higherEffortScore = "higher_effort_score"
        case effortNote = "effort_note"
        case confidenceBasis = "confidence_basis"
        case tradeOff = "trade_off"
        case modelId = "model_id"
    }
}

/// The engine's error envelope. `/v1` returns this shape for every refusal.
struct EngineErrorBody: Decodable {
    struct Detail: Decodable {
        let code: String
        let message: String
    }
    let error: Detail
}

/// A JSON value of unknown shape, decoded without losing it.
///
/// D-136's facts are open-ended by design — a new reason may carry values this build has never
/// seen — so decoding them into a fixed struct would either drop fields or refuse payloads a
/// newer engine sends. This keeps them, and the composition layer reads what it recognises.
enum JSONValue: Decodable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            self = .null
        }
    }

    /// Flatten to the loose dictionary the composition functions read. Nested objects and arrays
    /// are dropped rather than half-converted: no fact uses them today, and a client that guessed
    /// at their shape would be inventing structure the engine did not send.
    var dictionary: [String: Any] {
        guard case let .object(fields) = self else { return [:] }
        var out: [String: Any] = [:]
        for (key, value) in fields {
            switch value {
            case let .string(text): out[key] = text
            case let .number(double): out[key] = double
            case let .bool(flag): out[key] = flag
            case .object, .array, .null: continue
            }
        }
        return out
    }
}

// MARK: - The detail screen's subject (M15-W2, REQ-DTL-001/002)

/// A pick and a ranking row carry the same measured fields, so one detail screen serves both.
/// Declared here, beside the types, rather than in `Detail.swift`: these conformances are a
/// statement about the /v1 payload, and this file is where the payload lives.
extension Pick: DetailSubject {}

extension RankedModel: DetailSubject {}

// MARK: - M17-W4 (D-167): every board's standings, as positions

/// The `/v1/boards` payload: every board the engine ranks, fetched whatever the question is.
///
/// It carries POSITIONS and no score (D-167 clause 2), so nothing on the phone can average two
/// scales (D-105). The combination built from it (D-160 clause 2) returns with #61.
struct Standings: Codable, Equatable {
    let apiVersion: String
    let attributions: [String]
    let boards: [BoardStandings]
    let models: [StandingModel]
    /// #260: each publisher the attributions credit, for the Credits screen. `nil` from an engine
    /// that predates them, so a phone ahead of its engine still reads the boards. A `let`: the store
    /// reads it, and a privacy sink reads no mutable state (INV-66).
    let credits: [Credit]?

    init(apiVersion: String, attributions: [String], boards: [BoardStandings], models: [StandingModel],
         credits: [Credit]? = nil) {
        self.apiVersion = apiVersion
        self.attributions = attributions
        self.boards = boards
        self.models = models
        self.credits = credits
    }

    enum CodingKeys: String, CodingKey {
        case apiVersion = "api_version"
        case attributions
        case boards
        case models
        case credits
    }
}

/// One publisher on the Credits screen (#260): who, what, where its data is published, and the licence
/// or terms it is under. The links stay text: D-126's compiled gate refuses a `URL` made from a string
/// and every way to open one, so the reader selects and copies them.
struct Credit: Codable, Equatable, Identifiable {
    let id: String
    let publisher: String
    let data: String
    let url: String
    let licence: String
    /// `nil` where the publisher states no licence.
    let licenceUrl: String?
    /// #261: the copyright notice the licence asks to keep; `nil` where none is published, or from an
    /// engine older than it.
    let notice: String?

    init(id: String, publisher: String, data: String, url: String, licence: String, licenceUrl: String?,
         notice: String? = nil) {
        self.id = id
        self.publisher = publisher
        self.data = data
        self.url = url
        self.licence = licence
        self.licenceUrl = licenceUrl
        self.notice = notice
    }

    enum CodingKeys: String, CodingKey {
        case id
        case publisher
        case data
        case url
        case licence
        case licenceUrl = "licence_url"
        case notice
    }
}

/// What the Credits sheet shows (#260), decided here, where `swift test` reaches it (the Tester's B1);
/// the view only draws it.
enum CreditsScreen: Equatable {
    /// No boards yet: the credits come with them.
    case notLoaded(String)
    /// Boards from an engine older than the screen, which carry no credits.
    case notSent(String)
    case listed([CreditRow])

    /// The notices CC BY 4.0 section 3(a)(1) asks for, at the top of the sheet: how the app changes the
    /// data, and that it comes without warranty (the Tester's round-2 B1: owned here, so a test holds it).
    static func notice(_ language: Language) -> String {
        UIText.creditsPurpose(language)
    }

    static func state(_ standings: Standings?, _ language: Language) -> CreditsScreen {
        guard let standings else { return .notLoaded(UIText.creditsUnavailable(language)) }
        guard let credits = standings.credits, !credits.isEmpty else {
            return .notSent(UIText.creditsNotSent(language))
        }
        return .listed(credits.map { CreditRow($0, language) })
    }

    /// #261: the full text of each licence the credits name that asks for it (Apache-2.0 section 4(a),
    /// MIT), once each, in the order the credits first name it. Each publisher's own copyright notice is
    /// on its row (`CreditRow.notice`).
    static func licenceTexts(_ standings: Standings?) -> [LicenceText] {
        var texts: [LicenceText] = []
        for credit in standings?.credits ?? [] {
            let text = LicenceText.carried.first { credit.licence.hasPrefix($0.name) }
            if let text, !texts.contains(text) { texts.append(text) }
        }
        return texts
    }
}

/// #261: one licence's name and full text, as the Credits sheet carries it.
struct LicenceText: Equatable, Identifiable {
    let name: String
    let text: String
    var id: String { name }

    /// The licences whose text the app carries: a credit's licence names one when it begins with its name.
    static let carried = [LicenceText(name: "Apache-2.0", text: apache20), LicenceText(name: "MIT", text: mit)]

    /// The Apache License, Version 2.0, as Aider's and Terminal-Bench's repositories publish it.
    static let apache20 = """
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

    /// The MIT licence's terms, as LiteLLM and models.dev publish them; each copyright line is its
    /// publisher's notice.
    static let mit = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
}

/// One credit's lines. Each link is a line of its own, so selecting it copies the address alone.
struct CreditRow: Equatable, Identifiable {
    let id: String
    let publisher: String
    let data: String
    let dataLabel: String
    let dataLink: String
    let licence: String
    let licenceLink: String?
    let notice: String?

    init(_ credit: Credit, _ language: Language) {
        id = credit.id
        publisher = credit.publisher
        data = credit.data
        dataLabel = UIText.creditsData(language)
        dataLink = credit.url
        licence = "\(UIText.creditsLicence(language)): \(credit.licence)"
        licenceLink = credit.licenceUrl
        notice = credit.notice
    }
}

/// One board: its identity, dates and attribution, and its rankable models in order.
struct BoardStandings: Codable, Equatable, Identifiable {
    let id: String
    let benchmark: String
    let metric: String
    /// The effort a surface ranks this board at (D-112), or `nil` where each model stands on its
    /// best evidence and says which effort that was.
    let rankingEffort: String?
    /// The newest evaluation date on the board; `nil` for a board that publishes none.
    let evidenceDate: String?
    let observedAt: String?
    let attribution: String
    let standings: [Standing]

    enum CodingKeys: String, CodingKey {
        case id
        case benchmark
        case metric
        case rankingEffort = "ranking_effort"
        case evidenceDate = "evidence_date"
        case observedAt = "observed_at"
        case attribution
        case standings
    }
}

/// A model's place on one board. Tied models share a position.
struct Standing: Codable, Equatable {
    let model: String
    let position: Int
    /// The effort its evidence was run at (D-112): what an unequal comparison is disclosed with.
    let effort: String

    enum CodingKeys: String, CodingKey {
        case model
        case position
        case effort
    }
}

/// Each model once, with the price every surface ranks it at and its accessibility (M17-W3).
struct StandingModel: Codable, Equatable, Identifiable {
    let id: String
    let display: String
    let vendor: String
    let blendedPerM: Double
    let accessibility: String?

    enum CodingKeys: String, CodingKey {
        case id
        case display
        case vendor
        case blendedPerM = "blended_per_m"
        case accessibility
    }
}

/// The standings as decoded, and what the phone keeps of them: the same standings encoded again,
/// so only the fields this app decodes are ever stored, never whatever else a payload carried
/// (M17-W4 security S2). The size ceiling holds wherever standings are made, not only on the
/// network path.
struct FetchedStandings: Equatable {
    let standings: Standings
    let payload: Data

    init(payload data: Data) throws {
        guard data.count <= EngineClient.maxStandingsBytes else {
            throw EngineError.undecodable(
                "the standings payload is \(data.count) bytes, larger than the \(EngineClient.maxStandingsBytes) this app accepts")
        }
        standings = try JSONDecoder().decode(Standings.self, from: data)
        let encoder = JSONEncoder()
        encoder.outputFormatting = .sortedKeys
        payload = try encoder.encode(standings)
    }
}
