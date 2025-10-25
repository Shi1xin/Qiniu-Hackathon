import Foundation

// MARK: - CommandStatus

enum CommandStatus: String, CaseIterable, Codable {
    case pending = "pending"      // Waiting to execute
    case running = "running"      // Currently executing
    case completed = "completed"  // Successfully completed
    case failed = "failed"        // Failed with error
    case cancelled = "cancelled"  // User cancelled
    case timeout = "timeout"      // Execution timed out
}

// MARK: - CommandExecution

/// Represents the execution of agent-tars command with voice input.
class CommandExecution: ObservableObject, Codable {
    // MARK: - Properties

    /// Unique identifier
    let id: UUID

    /// Reference to parent VoiceSession
    let sessionId: UUID

    /// The full command executed (e.g., "agent-tars run --input 'text'")
    @Published var command: String

    /// The voice input text
    @Published var inputText: String

    /// When command execution started
    let startTime: Date

    /// When execution completed
    @Published var endTime: Date?

    /// Execution status
    @Published var status: CommandStatus

    /// Process exit code
    @Published var exitCode: Int?

    /// Standard output
    @Published var stdout: String

    /// Standard error output
    @Published var stderr: String

    /// Execution duration in seconds
    var duration: TimeInterval? {
        guard let endTime = endTime else { return nil }
        return endTime.timeIntervalSince(startTime)
    }

    /// Whether execution was successful
    var isSuccess: Bool {
        return status == .completed && (exitCode == 0 || exitCode == nil)
    }

    // MARK: - Initialization

    init(sessionId: UUID, inputText: String) {
        self.id = UUID()
        self.sessionId = sessionId
        self.command = "agent-tars run --input \"\(inputText)\""
        self.inputText = inputText
        self.startTime = Date()
        self.endTime = nil
        self.status = .pending
        self.exitCode = nil
        self.stdout = ""
        self.stderr = ""
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, sessionId, command, inputText, startTime, endTime, status, exitCode, stdout, stderr
    }

    required init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        sessionId = try container.decode(UUID.self, forKey: .sessionId)
        command = try container.decode(String.self, forKey: .command)
        inputText = try container.decode(String.self, forKey: .inputText)
        startTime = try container.decode(Date.self, forKey: .startTime)
        endTime = try container.decodeIfPresent(Date.self, forKey: .endTime)
        status = try container.decode(CommandStatus.self, forKey: .status)
        exitCode = try container.decodeIfPresent(Int.self, forKey: .exitCode)
        stdout = try container.decode(String.self, forKey: .stdout)
        stderr = try container.decode(String.self, forKey: .stderr)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(sessionId, forKey: .sessionId)
        try container.encode(command, forKey: .command)
        try container.encode(inputText, forKey: .inputText)
        try container.encode(startTime, forKey: .startTime)
        try container.encodeIfPresent(endTime, forKey: .endTime)
        try container.encode(status, forKey: .status)
        try container.encodeIfPresent(exitCode, forKey: .exitCode)
        try container.encode(stdout, forKey: .stdout)
        try container.encode(stderr, forKey: .stderr)
    }

    // MARK: - Execution Management

    /// Start command execution
    func startExecution() {
        status = .running
    }

    /// Complete execution successfully
    func complete(with output: String = "", exitCode: Int = 0) {
        status = .completed
        stdout = output
        self.exitCode = exitCode
        endTime = Date()
    }

    /// Fail execution with error
    func fail(with error: String, exitCode: Int? = nil) {
        status = .failed
        stderr = error
        self.exitCode = exitCode
        endTime = Date()
    }

    /// Timeout execution
    func timeout() {
        status = .timeout
        stderr = "Command execution timed out"
        endTime = Date()
    }

    /// Cancel execution
    func cancel() {
        status = .cancelled
        endTime = Date()
    }

    /// Append output during execution
    func appendOutput(_ output: String) {
        stdout += output
    }

    /// Append error output during execution
    func appendError(_ error: String) {
        stderr += error
    }

    // MARK: - Validation

    /// Validate command execution data
    var isValid: Bool {
        // Command must not be empty
        guard !command.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return false
        }

        // Input text must not be empty
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return false
        }

        // Start time must be before end time if both present
        if let endTime = endTime {
            guard startTime <= endTime else {
                return false
            }
        }

        return true
    }

    // MARK: - Convenience

    /// Get formatted result for display
    var displayResult: String {
        if isSuccess {
            return stdout.trimmingCharacters(in: .whitespacesAndNewlines)
        } else {
            return stderr.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? "Command failed with exit code \(exitCode ?? -1)"
                : stderr.trimmingCharacters(in: .whitespacesAndNewlines)
        }
    }
}