//  D-175 clause 3 -- routing scripted for a UI test.
//
//  A UI test cannot depend on the on-device model's reading: the same question routes differently
//  between runs (M17's probes). So a UI test launches the app with `-UITestRouting <json>`, a table
//  from question text to what the model would fill (`surface`, `language`, `domain`), and this
//  router stands in for the model tier. Its answer goes through `ModelOutputBoundary` exactly as the
//  model's does, so a UI test cannot reach a choice the boundary would refuse.
//
//  This file reads nothing from outside the app: it is handed the arguments. Only a Debug build hands
//  it the launch arguments (`LaunchRouting.swift`), and `make client-decls` refuses a Release build
//  that reads them. The Engine is not compiled on DEBUG (test_ios_platform_drift), so this lives here
//  unconditionally and is inert in Release.

import Foundation

struct ScriptedModelRouter: QuestionRouter {
    /// Question text -> the model's fields, as the generation schema names them.
    let answers: [String: [String: String]]

    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        guard let answer = answers[question] else { return nil }
        var refinements: [RefinementKind: String] = [:]
        for kind in RefinementKind.allCases {
            refinements[kind] = answer[kind.rawValue]
        }
        return ModelOutputBoundary.outcome(for: answer["surface"], within: known, refinements: refinements)
    }

    /// The table in `arguments` as `-UITestRouting <json>`, or nil when there is none.
    static func from(arguments: [String]) -> ScriptedModelRouter? {
        guard let flag = arguments.firstIndex(of: "-UITestRouting"), flag + 1 < arguments.count,
              let answers = try? JSONDecoder().decode([String: [String: String]].self,
                                                      from: Data(arguments[flag + 1].utf8))
        else { return nil }
        return ScriptedModelRouter(answers: answers)
    }
}
