//  EngineClient.swift — the only thing in this app that talks to the engine.
//
//  D-116 ships the engine as a service and D-123 keeps it on `localhost` until the app needs an
//  endpoint off this machine. So the base URL is configuration, not a constant: the simulator
//  reaches the developer's Mac at 127.0.0.1, and the day there is a deployed host only this value
//  changes.

import Foundation

/// Every way this app can fail to get an answer, named.
///
/// **The engine already writes an honest sentence for most of these** — a 503 says the evidence
/// database is unavailable, an empty answer says why it is empty. The client's job is to SHOW that
/// sentence, not to replace it with "Something went wrong", which is how a server's honesty gets
/// undone at the last step (M8 plan, Trap 2).
enum EngineError: LocalizedError, Equatable {
    /// Nothing is listening. Almost always: the engine is not running.
    case unreachable(String)
    /// The engine answered, and refused. Its own message is carried through unchanged.
    case refused(status: Int, code: String, message: String)
    /// The engine answered with something this app could not read — a contract mismatch.
    /// Under D-124 this is a finding against `/v1` BEFORE it is a client-side workaround.
    case undecodable(String)

    var errorDescription: String? {
        switch self {
        case .unreachable:
            return "The engine is not answering."
        case let .refused(_, _, message):
            return message
        case .undecodable:
            return "The engine's answer was not in a shape this app understands."
        }
    }

    /// What the person holding the phone can actually DO about it. Empty when there is nothing.
    var recovery: String? {
        switch self {
        case let .unreachable(detail):
            return "Start it with `make run` in the engine repository, then try again.\n\n\(detail)"
        case .refused:
            // The engine's message is the recovery; repeating it here would say it twice.
            return nil
        case let .undecodable(detail):
            return "This is a mismatch between the app and the /v1 contract, and it is a defect in "
                + "one of them rather than something to retry.\n\n\(detail)"
        }
    }
}

/// Reads answers from the engine. Holds no state and computes nothing.
struct EngineClient {
    let baseURL: URL
    private let session: URLSession

    /// Where the engine lives during development. `make run` binds 8080 on the developer's Mac,
    /// and the iOS Simulator shares that host's loopback.
    static let localDefault = URL(string: "http://127.0.0.1:8080")!

    init(baseURL: URL = EngineClient.localDefault, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    /// Ask for a recommendation. `task` and `budget` are the engine's vocabulary (D-118), passed
    /// straight through — the app does not translate them, because two vocabularies is how one run
    /// acquires two spellings.
    func recommendation(task: String, budget: String) async throws -> Recommendation {
        var components = URLComponents(
            url: baseURL.appendingPathComponent("v1/recommendations"),
            resolvingAgainstBaseURL: false
        )!
        components.queryItems = [
            URLQueryItem(name: "task", value: task),
            URLQueryItem(name: "budget", value: budget),
        ]

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(from: components.url!)
        } catch {
            throw EngineError.unreachable(error.localizedDescription)
        }

        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard status == 200 else {
            // Carry the ENGINE's words. It distinguishes an unavailable database from an unknown
            // task, and flattening them here would discard the distinction it was built to make.
            if let body = try? JSONDecoder().decode(EngineErrorBody.self, from: data) {
                throw EngineError.refused(
                    status: status, code: body.error.code, message: body.error.message
                )
            }
            throw EngineError.refused(
                status: status, code: "unexpected",
                message: "The engine answered \(status) in a shape this app did not recognise."
            )
        }

        do {
            return try JSONDecoder().decode(Recommendation.self, from: data)
        } catch {
            throw EngineError.undecodable(String(describing: error))
        }
    }
}
