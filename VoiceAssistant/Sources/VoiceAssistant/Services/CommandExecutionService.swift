import Foundation
import Subprocess

// MARK: - CommandExecutionService Protocol

/// Protocol for executing external commands (agent-tars).
protocol CommandExecutionService: AnyObject {
    /// Execute agent-tars command with voice input
    /// - Parameters:
    ///   - input: Voice input text
    ///   - delegate: Delegate to receive execution updates
    /// - Throws: CommandExecutionError
    func executeCommand(input: String, delegate: CommandExecutionDelegate) async throws

    /// Cancel current command execution
    func cancelExecution() async
}

// MARK: - CommandExecutionDelegate Protocol

/// Delegate for receiving command execution events.
@MainActor
protocol CommandExecutionDelegate: AnyObject, Sendable {
    /// Command execution started
    func commandExecutionDidStart(_ service: CommandExecutionService)

    /// Command execution produced output
    func commandExecution(_ service: CommandExecutionService, didReceiveOutput output: String)

    /// Command execution produced error output
    func commandExecution(_ service: CommandExecutionService, didReceiveError error: String)

    /// Command execution completed
    func commandExecutionDidComplete(_ service: CommandExecutionService, result: CommandExecutionResult)

    /// Command execution failed
    func commandExecution(_ service: CommandExecutionService, didFailWithError error: CommandExecutionError)
}

// MARK: - CommandExecutionManager

/// Concrete implementation of CommandExecutionService using Swift-Subprocess.
class CommandExecutionManager: CommandExecutionService, @unchecked Sendable {
    // MARK: - Properties

    private weak var delegate: CommandExecutionDelegate?
    private var currentTask: Subprocess.Execution?
    private var currentExecution: CommandExecutionResult?
    private let commandTimeout: TimeInterval = 60.0 // 60 seconds timeout

    private let agentTarsPath: String

    // MARK: - Initialization

    init(agentTarsPath: String = "agent-tars") {
        self.agentTarsPath = agentTarsPath
    }

    // MARK: - CommandExecutionService Implementation

    func executeCommand(input: String, delegate: CommandExecutionDelegate) async throws {
        guard !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw CommandExecutionError.invalidInput
        }

        // Cancel any existing execution
        await cancelExecution()

        self.delegate = delegate

        // Create command execution record
        let execution = CommandExecution(sessionId: UUID(), inputText: input)
        self.currentExecution = execution

        do {
            try await executeAgentTarsCommand(input: input, execution: execution)
        } catch {
            let commandError = error as? CommandExecutionError ?? CommandExecutionError.executionFailed(error.localizedDescription)
            delegate.commandExecution(self, didFailWithError: commandError)
            throw commandError
        }
    }

    func cancelExecution() async {
        currentTask?.interrupt()
        currentTask = nil
        currentExecution = nil
    }

    // MARK: - Private Methods

    private func executeAgentTarsCommand(input: String, execution: CommandExecution) async throws {
        guard let delegate = delegate else { return }

        delegate.commandExecutionDidStart(self)

        let fullCommand = "\(agentTarsPath) run --input \"\(input)\""

        // Update execution command
        execution.command = fullCommand
        execution.startExecution()

        do {
            // Create and run subprocess
            let task = try await Subprocess.run(
                .path(agentTarsPath),
                arguments: ["run", "--input", input],
                output: .string(limit: 1_000_000, using: .utf8),
                error: .string(limit: 100_000, using: .utf8)
            )

            self.currentTask = task

            // Handle subprocess result
            if task.terminationStatus.isSuccess {
                let output = try task.standardOutput ?? ""
                execution.complete(with: output, exitCode: Int(task.terminationStatus.code))
                delegate.commandExecutionDidComplete(self, result: execution)
            } else {
                let errorOutput = try task.standardError ?? "Unknown error"
                execution.fail(with: errorOutput, exitCode: Int(task.terminationStatus.code))
                delegate.commandExecution(self, didReceiveError: errorOutput)
                delegate.commandExecutionDidComplete(self, result: execution)
            }

        } catch let error as Subprocess.Error {
            // Handle subprocess-specific errors
            let commandError: CommandExecutionError
            switch error {
            case .cannotLaunchExecutable(let path):
                commandError = .commandNotFound
            case .processTerminated(let terminationStatus):
                if terminationStatus.wasSignaled {
                    commandError = .processCrashed
                } else {
                    commandError = .executionFailed("Process terminated with code \(terminationStatus.code)")
                }
            default:
                commandError = .executionFailed(error.localizedDescription)
            }

            execution.fail(with: error.localizedDescription)
            delegate.commandExecution(self, didFailWithError: commandError)
            throw commandError

        } catch {
            // Handle other errors
            let commandError = CommandExecutionError.executionFailed(error.localizedDescription)
            execution.fail(with: error.localizedDescription)
            delegate.commandExecution(self, didFailWithError: commandError)
            throw commandError
        }

        currentTask = nil
        currentExecution = nil
    }

    // MARK: - Utility Methods

    /// Find the agent-tars executable path
    private func findAgentTarsPath() -> String {
        // Try to find agent-tars in common locations
        let searchPaths = [
            "/usr/local/bin/agent-tars",
            "/usr/bin/agent-tars",
            "/opt/homebrew/bin/agent-tars",
            "~/.cargo/bin/agent-tars",
            "agent-tars" // Fall back to PATH
        ]

        for path in searchPaths {
            let expandedPath = NSString(string: path).expandingTildeInPath
            if FileManager.default.isExecutableFile(atPath: expandedPath) {
                return expandedPath
            }
        }

        return "agent-tars" // Fall back to default
    }

    /// Check if agent-tars is available
    func isAgentTarsAvailable() -> Bool {
        let path = findAgentTarsPath()
        return FileManager.default.isExecutableFile(atPath: NSString(string: path).expandingTildeInPath)
    }
}