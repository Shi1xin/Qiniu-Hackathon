import Foundation

// MARK: - SpeechRecognitionError

enum SpeechRecognitionError: Error, LocalizedError, Codable {
    case notAuthorized
    case recognitionUnavailable
    case recognitionFailed(String)
    case audioSessionFailed(String)
    case timeout
    case microphoneDenied
    case microphoneUnavailable
    case unsupportedLanguage(String)
    case invalidInput
    case configurationError(String)

    var errorDescription: String? {
        switch self {
        case .notAuthorized:
            return "Speech recognition is not authorized. Please enable it in System Preferences."
        case .recognitionUnavailable:
            return "Speech recognition is currently unavailable."
        case .recognitionFailed(let message):
            return "Speech recognition failed: \(message)"
        case .audioSessionFailed(let message):
            return "Audio session failed: \(message)"
        case .timeout:
            return "Speech recognition timed out."
        case .microphoneDenied:
            return "Microphone access was denied. Please enable it in System Preferences."
        case .microphoneUnavailable:
            return "Microphone is not available or is being used by another application."
        case .unsupportedLanguage(let language):
            return "Language '\(language)' is not supported for speech recognition."
        case .invalidInput:
            return "Invalid input provided for speech recognition."
        case .configurationError(let message):
            return "Configuration error: \(message)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .notAuthorized:
            return "Go to System Preferences → Security & Privacy → Privacy → Speech Recognition and enable access."
        case .microphoneDenied:
            return "Go to System Preferences → Security & Privacy → Privacy → Microphone and enable access."
        case .microphoneUnavailable:
            return "Close other applications using the microphone and try again."
        case .unsupportedLanguage:
            return "Choose a supported language from the preferences."
        case .recognitionUnavailable:
            return "Check your internet connection and try again."
        default:
            return "Try again or check the application preferences."
        }
    }

    var isUserActionable: Bool {
        switch self {
        case .notAuthorized, .microphoneDenied, .microphoneUnavailable, .unsupportedLanguage:
            return true
        default:
            return false
        }
    }
}

// MARK: - CommandExecutionError

enum CommandExecutionError: Error, LocalizedError, Codable {
    case commandNotFound
    case executionFailed(String)
    case timeout
    case permissionDenied
    case invalidInput
    case processCrashed
    case invalidPath(String)
    case missingArguments
    case configurationError(String)

    var errorDescription: String? {
        switch self {
        case .commandNotFound:
            return "agent-tars command not found. Please ensure it's installed and accessible in your PATH."
        case .executionFailed(let message):
            return "Command execution failed: \(message)"
        case .timeout:
            return "Command execution timed out."
        case .permissionDenied:
            return "Permission denied to execute command."
        case .invalidInput:
            return "Invalid input provided for command execution."
        case .processCrashed:
            return "The command process crashed unexpectedly."
        case .invalidPath(let path):
            return "Invalid command path: \(path)"
        case .missingArguments:
            return "Required arguments are missing for command execution."
        case .configurationError(let message):
            return "Configuration error: \(message)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .commandNotFound:
            return "Install agent-tars and ensure it's in your system PATH, or specify the correct path in preferences."
        case .permissionDenied:
            return "Check file permissions and ensure the command is executable."
        case .invalidInput:
            return "Check your input and try again."
        case .timeout:
            return "Try running the command manually to check if it's working correctly."
        case .invalidPath:
            return "Verify the command path and ensure the file exists."
        case .missingArguments:
            return "Check the command syntax and provide all required arguments."
        default:
            return "Check the command configuration and try again."
        }
    }

    var isUserActionable: Bool {
        switch self {
        case .commandNotFound, .permissionDenied, .invalidInput, .invalidPath, .missingArguments:
            return true
        default:
            return false
        }
    }
}

// MARK: - ValidationError

enum ValidationError: Error, LocalizedError, Codable {
    case invalidSession(String)
    case invalidTranscription(String)
    case invalidCommand(String)
    case invalidPreferences(String)

    var errorDescription: String? {
        switch self {
        case .invalidSession(let message):
            return "Invalid session data: \(message)"
        case .invalidTranscription(let message):
            return "Invalid transcription data: \(message)"
        case .invalidCommand(let message):
            return "Invalid command data: \(message)"
        case .invalidPreferences(let message):
            return "Invalid preferences data: \(message)"
        }
    }
}

// MARK: - PermissionStatus

enum PermissionStatus: String, CaseIterable, Codable {
    case notDetermined = "not_determined"
    case granted = "granted"
    case denied = "denied"
    case restricted = "restricted"

    var isAuthorized: Bool {
        return self == .granted
    }

    var localizedDescription: String {
        switch self {
        case .notDetermined:
            return "Permission not yet requested"
        case .granted:
            return "Permission granted"
        case .denied:
            return "Permission denied"
        case .restricted:
            return "Permission restricted"
        }
    }
}

// MARK: - AudioRecordingError

enum AudioRecordingError: Error, LocalizedError, Codable {
    case microphoneAccessDenied
    case audioSessionFailure(String)
    case hardwareUnavailable
    case configurationError(String)
    case interruption
    case formatNotSupported

    var errorDescription: String? {
        switch self {
        case .microphoneAccessDenied:
            return "Microphone access was denied."
        case .audioSessionFailure(let message):
            return "Audio session failed: \(message)"
        case .hardwareUnavailable:
            return "Microphone hardware is unavailable."
        case .configurationError(let message):
            return "Audio configuration error: \(message)"
        case .interruption:
            return "Audio recording was interrupted."
        case .formatNotSupported:
            return "Audio format is not supported."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .microphoneAccessDenied:
            return "Enable microphone access in System Preferences."
        case .hardwareUnavailable:
            return "Check if microphone is properly connected."
        case .interruption:
            return "Try recording again when the interruption is resolved."
        default:
            return "Check audio settings and try again."
        }
    }
}