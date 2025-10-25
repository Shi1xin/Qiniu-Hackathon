import Foundation

// MARK: - VoiceSessionStatus

enum VoiceSessionStatus: String, CaseIterable, Codable {
    case pending = "pending"      // User clicked menubar, waiting to start
    case recording = "recording"  // Currently recording audio
    case processing = "processing" // Transcribing speech
    case completed = "completed"  // Successfully completed
    case failed = "failed"        // Failed with error
    case cancelled = "cancelled"  // User cancelled
}

// MARK: - VoiceSession

/// Represents a single voice interaction from initiation to completion.
class VoiceSession: ObservableObject, Codable {
    // MARK: - Properties

    /// Unique identifier for the session
    let id: UUID

    /// When the voice input was initiated
    @Published var startTime: Date

    /// When the session completed (null for active sessions)
    @Published var endTime: Date?

    /// Current state of the session
    @Published var status: VoiceSessionStatus

    /// Current audio input level (0.0-1.0)
    @Published var audioLevel: Float

    /// Total session duration in seconds
    var duration: TimeInterval {
        guard let endTime = endTime else {
            return Date().timeIntervalSince(startTime)
        }
        return endTime.timeIntervalSince(startTime)
    }

    // MARK: - Initialization

    init() {
        self.id = UUID()
        self.startTime = Date()
        self.endTime = nil
        self.status = .pending
        self.audioLevel = 0.0
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, startTime, endTime, status, audioLevel
    }

    required init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        startTime = try container.decode(Date.self, forKey: .startTime)
        endTime = try container.decodeIfPresent(Date.self, forKey: .endTime)
        status = try container.decode(VoiceSessionStatus.self, forKey: .status)
        audioLevel = try container.decode(Float.self, forKey: .audioLevel)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(startTime, forKey: .startTime)
        try container.encodeIfPresent(endTime, forKey: .endTime)
        try container.encode(status, forKey: .status)
        try container.encode(audioLevel, forKey: .audioLevel)
    }

    // MARK: - Session Management

    /// Start recording phase
    func startRecording() {
        status = .recording
        audioLevel = 0.0
    }

    /// Start processing phase
    func startProcessing() {
        status = .processing
        audioLevel = 0.0
    }

    /// Complete session successfully
    func complete() {
        status = .completed
        endTime = Date()
    }

    /// Mark session as failed
    func fail() {
        status = .failed
        endTime = Date()
    }

    /// Cancel session
    func cancel() {
        status = .cancelled
        endTime = Date()
    }

    /// Update audio level during recording
    func updateAudioLevel(_ level: Float) {
        guard status == .recording else { return }
        audioLevel = max(0.0, min(1.0, level))
    }
}