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
    /// The engine accepted the connection and did not answer in time. NOT the same as unreachable,
    /// and telling them apart is the point: "start the engine" is wrong advice for a running one.
    case timedOut(seconds: Int)
    /// The device has no network at all. Irrelevant on `localhost` and not once D-116 puts the
    /// engine on a host, which is why it is named now rather than discovered then.
    case offline
    /// The engine answered, and refused. Its own message is carried through unchanged.
    case refused(status: Int, code: String, message: String)
    /// The engine answered with something this app could not read — a contract mismatch.
    /// Under D-124 this is a finding against `/v1` BEFORE it is a client-side workaround.
    case undecodable(String)

    var errorDescription: String? {
        switch self {
        case .unreachable:
            return "The engine is not answering."
        case let .timedOut(seconds):
            return "The engine did not answer within \(seconds) seconds."
        case .offline:
            return "This device has no network connection."
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
        case .timedOut:
            return "It is running but slow to respond. Trying again is reasonable; if it keeps "
                + "happening the artifact is probably being rebuilt underneath it."
        case .offline:
            return "Reconnect and try again."
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

    /// How long a person will stare at a spinner before the app owes them a sentence.
    ///
    /// `URLSession.shared` defaults to SIXTY seconds, which on a phone is the "spinner that never
    /// ends" the M8 plan names as a failure state in its own right. Ten is long enough for a cold
    /// artifact read and short enough to still be an app.
    static let requestTimeout = 10

    init(baseURL: URL = EngineClient.localDefault, session: URLSession? = nil) {
        self.baseURL = baseURL
        if let session {
            self.session = session
        } else {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.timeoutIntervalForRequest = TimeInterval(EngineClient.requestTimeout)
            configuration.timeoutIntervalForResource = TimeInterval(EngineClient.requestTimeout)
            configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
            self.session = URLSession(configuration: configuration)
        }
    }

    /// Ask for a recommendation. `task` and `budget` are the engine's vocabulary (D-118), passed
    /// straight through — the app does not translate them, because two vocabularies is how one run
    /// acquires two spellings.
    func recommendation(task: String, budget: String) async throws -> Recommendation {
        try await get(
            "v1/recommendations",
            query: [
                URLQueryItem(name: "task", value: task),
                URLQueryItem(name: "budget", value: budget),
            ]
        )
    }

    /// The surfaces this engine can rank, asked rather than assumed.
    ///
    /// The app has no list of its own. Nine categories shipped in one build and more will follow;
    /// a Swift copy would be a roster that drifts silently, which is the defect this project keeps
    /// paying for in other forms.
    func categories() async throws -> [Category] {
        let list: CategoryList = try await get("v1/categories", query: [])
        return list.categories
    }

    /// One request shape for every endpoint, so the error vocabulary cannot diverge between them.
    private func get<T: Decodable>(_ path: String, query: [URLQueryItem]) async throws -> T {
        var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        )!
        components.queryItems = query.isEmpty ? nil : query

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(from: components.url!)
        } catch let error as URLError {
            // Mapped rather than flattened. All three arrive here as one thrown URLError, and all
            // three deserve different advice — the M8 plan's Trap 2 is the client replacing the
            // real condition with one generic sentence.
            switch error.code {
            case .timedOut:
                throw EngineError.timedOut(seconds: EngineClient.requestTimeout)
            case .notConnectedToInternet, .networkConnectionLost, .dataNotAllowed:
                throw EngineError.offline
            default:
                throw EngineError.unreachable(error.localizedDescription)
            }
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
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw EngineError.undecodable(String(describing: error))
        }
    }
}
