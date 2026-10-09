//  ServedModelNames.swift -- the names of the models the engine serves today (#194, the M21-W2 review's
//  M2). The registry's family words (`ModelFamilies`) miss a model the engine derives from its sources
//  (Yi, StarCoder, Solar): the phone reads those from `/v1/boards`' model list it already keeps. A
//  served family word the registry does not name is read as an ambiguous one: a model only beside a
//  token its own served names put after it, or in a question about a model's cost or making.

import Foundation

struct ServedModelNames: Equatable {
    /// Served family word -> the tokens its served names put right after it.
    let versions: [String: Set<String>]

    init() { versions = [:] }

    init(displayNames: [String]) {
        var versions: [String: Set<String>] = [:]
        for name in displayNames {
            let tokens = name.lowercased().split { !$0.isLetter && !$0.isNumber }.map(String.init)
            guard let first = tokens.first, first.count > 1, first.first?.isLetter == true else { continue }
            versions[first, default: []].formUnion(tokens.count > 1 ? [tokens[1]] : [])
        }
        self.versions = versions
    }

    init(_ standings: Standings?) {
        self.init(displayNames: standings?.models.map(\.display) ?? [])
    }
}
