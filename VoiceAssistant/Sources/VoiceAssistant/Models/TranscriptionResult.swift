import Foundation

// MARK: - TranscriptionResult

/// Contains the speech recognition output and metadata.
struct TranscriptionResult: Codable, Sendable {
    // MARK: - Properties

    /// Unique identifier
    let id: UUID

    /// Reference to parent VoiceSession
    let sessionId: UUID

    /// The recognized speech text
    let text: String

    /// Recognition confidence score (0.0-1.0)
    let confidence: Float

    /// Alternative recognition results
    let alternatives: [String]

    /// Whether this is the final result
    let isFinal: Bool

    /// When the transcription was generated
    let timestamp: Date

    // MARK: - Initialization

    init(sessionId: UUID, text: String, confidence: Float, alternatives: [String] = [], isFinal: Bool = false) {
        self.id = UUID()
        self.sessionId = sessionId
        self.text = text
        self.confidence = max(0.0, min(1.0, confidence))
        self.alternatives = alternatives.filter { !$0.isEmpty }
        self.isFinal = isFinal
        self.timestamp = Date()
    }

    // MARK: - Validation

    /// Validate transcription result data
    var isValid: Bool {
        // For final results, text must not be empty
        if isFinal && text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return false
        }

        // Confidence must be between 0.0 and 1.0
        guard confidence >= 0.0 && confidence <= 1.0 else {
            return false
        }

        // Alternatives array should not contain empty strings
        guard alternatives.allSatisfy({ !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) else {
            return false
        }

        return true
    }

    // MARK: - Convenience

    /// Create a partial result for real-time feedback
    static func partial(sessionId: UUID, text: String, confidence: Float) -> TranscriptionResult {
        return TranscriptionResult(
            sessionId: sessionId,
            text: text,
            confidence: confidence,
            alternatives: [],
            isFinal: false
        )
    }

    /// Create a final result
    static func final(sessionId: UUID, text: String, confidence: Float, alternatives: [String] = []) -> TranscriptionResult {
        return TranscriptionResult(
            sessionId: sessionId,
            text: text,
            confidence: confidence,
            alternatives: alternatives,
            isFinal: true
        )
    }

    /// Get the best text (main result or first alternative if main is empty)
    var bestText: String {
        if text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return alternatives.first ?? text
        }
        return text
    }
}