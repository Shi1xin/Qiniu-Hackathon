import Foundation
import Speech
import AVFoundation
import Combine

// MARK: - SpeechRecognitionService Protocol

/// Protocol for speech recognition functionality.
protocol SpeechRecognitionService: AnyObject {
    /// Current authorization status for speech recognition
    var authorizationStatus: SFSpeechRecognizerAuthorizationStatus { get }

    /// Whether speech recognition is currently available
    var isAvailable: Bool { get }

    /// Currently supported languages
    var supportedLocales: [Locale] { get }

    /// Request speech recognition permissions
    func requestAuthorization() async -> SFSpeechRecognizerAuthorizationStatus

    /// Start speech recognition session
    /// - Parameters:
    ///   - locale: Language locale for recognition
    ///   - delegate: Delegate to receive recognition results
    /// - Throws: SpeechRecognitionError
    func startRecognition(locale: Locale, delegate: SpeechRecognitionDelegate) async throws

    /// Stop current recognition session
    func stopRecognition() async

    /// Cancel current recognition session
    func cancelRecognition() async
}

// MARK: - SpeechRecognitionDelegate Protocol

/// Delegate for receiving speech recognition events.
@MainActor
protocol SpeechRecognitionDelegate: AnyObject, Sendable {
    /// Speech recognition produced a result
    func speechRecognition(_ service: SpeechRecognitionService, didReceive result: TranscriptionResult)

    /// Speech recognition encountered an error
    func speechRecognition(_ service: SpeechRecognitionService, didFailWithError error: SpeechRecognitionError)

    /// Speech recognition finished
    func speechRecognitionDidFinish(_ service: SpeechRecognitionService)

    /// Audio level changed during recording
    func speechRecognition(_ service: SpeechRecognitionService, audioLevel: Float)
}

// MARK: - SpeechRecognitionManager

/// Concrete implementation of SpeechRecognitionService using macOS Speech Framework.
class SpeechRecognitionManager: NSObject, SpeechRecognitionService, @unchecked Sendable {
    // MARK: - Properties

    private let speechRecognizer: SFSpeechRecognizer
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var audioEngine = AVAudioEngine()
    private weak var delegate: SpeechRecognitionDelegate?
    private var currentSessionId: UUID?

    var authorizationStatus: SFSpeechRecognizerAuthorizationStatus {
        return SFSpeechRecognizer.authorizationStatus()
    }

    var isAvailable: Bool {
        return speechRecognizer.isAvailable && authorizationStatus == .authorized
    }

    var supportedLocales: [Locale] {
        return SFSpeechRecognizer.supportedLocales()
    }

    // MARK: - Initialization

    override init() {
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))!
        super.init()
        setupAudioSession()
    }

    // MARK: - SpeechRecognitionService Implementation

    func requestAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
        let currentStatus = authorizationStatus
        if currentStatus != .notDetermined {
            return currentStatus
        }

        let newStatus = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status)
            }
        }

        return newStatus
    }

    func startRecognition(locale: Locale, delegate: SpeechRecognitionDelegate) async throws {
        guard authorizationStatus == .authorized else {
            throw SpeechRecognitionError.notAuthorized
        }

        guard isAvailable else {
            throw SpeechRecognitionError.recognitionUnavailable
        }

        // Cancel any existing session
        await cancelRecognition()

        // Update speech recognizer for new locale
        let newRecognizer = SFSpeechRecognizer(locale: locale)
        guard let recognizer = newRecognizer, recognizer.isAvailable else {
            throw SpeechRecognitionError.unsupportedLanguage(locale.identifier)
        }

        self.delegate = delegate
        self.currentSessionId = UUID()

        try await startRecognitionSession(with: recognizer)
    }

    func stopRecognition() async {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)

        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.finish()
        recognitionTask = nil

        currentSessionId = nil
    }

    func cancelRecognition() async {
        recognitionTask?.cancel()
        await stopRecognition()
    }

    // MARK: - Private Methods

    private func setupAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }

    private func startRecognitionSession(with recognizer: SFSpeechRecognizer) async throws {
        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw SpeechRecognitionError.recognitionUnavailable
        }

        recognitionRequest.shouldReportPartialResults = true

        // Configure audio input
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        // Install tap for audio buffer
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            recognitionRequest.append(buffer)

            // Calculate audio level for visual feedback
            let audioLevel = self?.calculateAudioLevel(from: buffer) ?? 0.0
            Task { @MainActor in
                self?.delegate?.speechRecognition(self!, audioLevel: audioLevel)
            }
        }

        // Prepare and start audio engine
        audioEngine.prepare()
        try audioEngine.start()

        // Start recognition task
        recognitionTask = recognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            Task { @MainActor in
                guard let self = self, let sessionId = self.currentSessionId else { return }

                if let result = result {
                    let transcription = TranscriptionResult(
                        sessionId: sessionId,
                        text: result.bestTranscription.formattedString,
                        confidence: Float(result.bestTranscription.averageConfidenceScore),
                        alternatives: result.transcriptions.map { $0.formattedString },
                        isFinal: result.isFinal
                    )
                    self.delegate?.speechRecognition(self, didReceive: transcription)
                }

                if let error = error {
                    let speechError = SpeechRecognitionError.recognitionFailed(error.localizedDescription)
                    self.delegate?.speechRecognition(self, didFailWithError: speechError)
                    self.stopRecognition()
                } else if result?.isFinal == true {
                    self.delegate?.speechRecognitionDidFinish(self)
                    self.stopRecognition()
                }
            }
        }
    }

    private func calculateAudioLevel(from buffer: AVAudioBuffer) -> Float {
        guard let pcmBuffer = buffer as? AVAudioPCMBuffer else { return 0.0 }

        let channelData = pcmBuffer.floatChannelData!
        let channelDataValue = channelData.pointee
        let channelDataPointer = UnsafeMutablePointer<Float>(channelDataValue)

        var rms: Float = 0.0
        let length = Int(pcmBuffer.frameLength)

        for i in 0..<length {
            let sample = channelDataPointer[i]
            rms += sample * sample
        }

        rms = sqrt(rms / Float(length))
        return min(rms * 20, 1.0) // Scale and clamp to 0.0-1.0
    }
}