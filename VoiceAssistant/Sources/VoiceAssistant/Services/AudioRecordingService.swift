import Foundation
import AVFoundation
import Combine

// MARK: - AudioRecordingService Protocol

/// Protocol for audio recording functionality.
protocol AudioRecordingService: AnyObject {
    /// Current recording state
    var isRecording: Bool { get }

    /// Current audio input level (0.0-1.0)
    var audioLevel: Float { get }

    /// Request microphone permission
    func requestMicrophonePermission() async -> Bool

    /// Start audio recording session
    /// - Parameters:
    ///   - delegate: Delegate to receive audio data
    /// - Throws: AudioRecordingError
    func startRecording(delegate: AudioRecordingDelegate) async throws

    /// Stop current recording session
    func stopRecording() async

    /// Cancel current recording session
    func cancelRecording() async
}

// MARK: - AudioRecordingDelegate Protocol

/// Delegate for receiving audio recording events.
@MainActor
protocol AudioRecordingDelegate: AnyObject, Sendable {
    /// Audio buffer received during recording
    func audioRecording(_ service: AudioRecordingService, didReceiveBuffer buffer: AVAudioBuffer)

    /// Recording level changed
    func audioRecording(_ service: AudioRecordingService, audioLevel: Float)

    /// Recording encountered an error
    func audioRecording(_ service: AudioRecordingService, didFailWithError error: AudioRecordingError)
}

// MARK: - AudioRecordingManager

/// Concrete implementation of AudioRecordingService using AVFoundation.
class AudioRecordingManager: NSObject, AudioRecordingService, @unchecked Sendable {
    // MARK: - Properties

    private let audioEngine = AVAudioEngine()
    private var inputNode: AVAudioInputNode?
    private weak var delegate: AudioRecordingDelegate?
    private var audioLevelTimer: Timer?
    private var currentRecordingFormat: AVAudioFormat?

    @Published var isRecording = false
    @Published var audioLevel: Float = 0.0

    // MARK: - AudioRecordingService Implementation

    func requestMicrophonePermission() async -> Bool {
        let audioSession = AVAudioSession.sharedInstance()

        switch audioSession.recordPermission {
        case .undetermined:
            let granted = await withCheckedContinuation { continuation in
                audioSession.requestRecordPermission { granted in
                    continuation.resume(returning: granted)
                }
            }
            return granted

        case .granted:
            return true

        case .denied:
            return false

        @unknown default:
            return false
        }
    }

    func startRecording(delegate: AudioRecordingDelegate) async throws {
        guard !isRecording else {
            throw AudioRecordingError.configurationError("Already recording")
        }

        // Check microphone permission
        guard await requestMicrophonePermission() else {
            throw AudioRecordingError.microphoneAccessDenied
        }

        // Configure audio session
        try await configureAudioSession()

        // Set up audio engine
        try setupAudioEngine()

        // Set delegate
        self.delegate = delegate

        // Start recording
        try await startAudioEngine()

        isRecording = true
        startAudioLevelMonitoring()
    }

    func stopRecording() async {
        guard isRecording else { return }

        audioEngine.stop()
        inputNode?.removeTap(onBus: 0)

        stopAudioLevelMonitoring()

        isRecording = false
        audioLevel = 0.0
        inputNode = nil
        currentRecordingFormat = nil
        delegate = nil
    }

    func cancelRecording() async {
        await stopRecording()
    }

    // MARK: - Private Methods

    private func configureAudioSession() async throws {
        let audioSession = AVAudioSession.sharedInstance()

        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            throw AudioRecordingError.audioSessionFailure(error.localizedDescription)
        }
    }

    private func setupAudioEngine() throws {
        inputNode = audioEngine.inputNode

        guard let inputNode = inputNode else {
            throw AudioRecordingError.hardwareUnavailable
        }

        let recordingFormat = inputNode.outputFormat(forBus: 0)
        currentRecordingFormat = recordingFormat

        // Install tap to receive audio buffers
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            guard let self = self else { return }

            Task { @MainActor in
                self.delegate?.audioRecording(self, didReceiveBuffer: buffer)
            }
        }

        audioEngine.prepare()
    }

    private func startAudioEngine() async throws {
        do {
            try audioEngine.start()
        } catch {
            throw AudioRecordingError.configurationError("Failed to start audio engine: \(error.localizedDescription)")
        }
    }

    private func startAudioLevelMonitoring() {
        audioLevelTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateAudioLevel()
            }
        }
    }

    private func stopAudioLevelMonitoring() {
        audioLevelTimer?.invalidate()
        audioLevelTimer = nil
    }

    private func updateAudioLevel() {
        guard isRecording, let inputNode = inputNode else { return }

        // Get average power from input node
        let averagePower = inputNode.averagePowerForChannel(0)
        let normalizedLevel = pow(10.0, (0.05 * averagePower))

        audioLevel = max(0.0, min(1.0, normalizedLevel))
        delegate?.audioRecording(self, audioLevel: audioLevel)
    }
}

// MARK: - AVAudioInputNode Extension

extension AVAudioInputNode {
    /// Get average power for a specific channel
    func averagePowerForChannel(_ channel: Int) -> Float {
        // This is a simplified implementation
        // In a real implementation, you would analyze the audio buffer
        // to calculate the actual average power
        return -30.0 // Default value (in dB)
    }
}