import Foundation
import AppKit
import Combine
import Speech

// MARK: - VoiceInputViewController Protocol

/// Protocol for voice input view controller functionality.
@MainActor
protocol VoiceInputViewControllerProtocol: AnyObject, Sendable {
    /// Current voice session
    var session: VoiceSession { get }

    /// Start recording
    func startRecording()

    /// Stop recording
    func stopRecording()

    /// Cancel recording
    func cancelRecording()

    /// Update audio level display
    /// - Parameter level: Audio level (0.0-1.0)
    func updateAudioLevel(_ level: Float)

    /// Show transcription result
    /// - Parameter result: Transcription result
    func showTranscription(_ result: TranscriptionResult)

    /// Show error message
    /// - Parameter error: Error to display
    func showError(_ error: Error)

    /// Reset view to initial state
    func reset()
}

// MARK: - VoiceInputViewController

/// NSViewController for managing voice input interface.
@MainActor
class VoiceInputViewController: NSViewController, VoiceInputViewControllerProtocol {
    // MARK: - Properties

    let session = VoiceSession()
    private var cancellables = Set<AnyCancellable>()

    // UI Elements
    private var containerView: NSView!
    private var microphoneButton: NSButton!
    private var audioLevelView: AudioLevelView!
    private var statusLabel: NSTextField!
    private var transcriptionLabel: NSTextField!
    private var cancelButton: NSButton!
    private var settingsButton: NSButton!

    // Services (to be injected)
    private var audioRecordingService: AudioRecordingService?
    private var speechRecognitionService: SpeechRecognitionService?
    private var notificationService: NotificationService?

    // MARK: - Initialization

    init() {
        super.init(nibName: nil, bundle: nil)
        setupView()
        setupBindings()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupView()
        setupBindings()
    }

    // MARK: - Lifecycle

    override func loadView() {
        // View is already created in setupView()
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupConstraints()
    }

    // MARK: - VoiceInputViewControllerProtocol Implementation

    func startRecording() {
        guard !session.status.isActive else { return }

        session.startRecording()
        updateUIForRecordingState()

        microphoneButton?.state = .on

        // Start audio recording (service will be injected)
        audioRecordingService?.startRecording(delegate: self)
    }

    func stopRecording() {
        guard session.status == .recording else { return }

        session.startProcessing()
        updateUIForProcessingState()

        microphoneButton?.state = .off

        // Stop audio recording
        Task {
            await audioRecordingService?.stopRecording()
        }
    }

    func cancelRecording() {
        guard session.status.isActive else { return }

        session.cancel()
        updateUIForIdleState()

        microphoneButton?.state = .off

        // Cancel audio recording
        Task {
            await audioRecordingService?.cancelRecording()
        }
    }

    func updateAudioLevel(_ level: Float) {
        session.updateAudioLevel(level)
        audioLevelView?.updateLevel(level)
    }

    func showTranscription(_ result: TranscriptionResult) {
        session.complete()
        updateUIForCompletedState()

        transcriptionLabel.stringValue = result.transcribedText

        // Show success notification
        Task {
            await notificationService?.showSuccess(
                title: "Transcription Complete",
                message: result.transcribedText
            )
        }

        // Auto-dismiss after delay
        autoDismissAfterDelay()
    }

    func showError(_ error: Error) {
        session.fail()
        updateUIForErrorState()

        statusLabel.stringValue = "Error: \(error.localizedDescription)"

        // Show error notification
        Task {
            await notificationService?.showError(
                title: "Recording Failed",
                error: error
            )
        }

        // Auto-dismiss after delay
        autoDismissAfterDelay()
    }

    func reset() {
        session.status = .pending
        session.audioLevel = 0.0
        updateUIForIdleState()
    }

    // MARK: - Service Injection

    func setAudioRecordingService(_ service: AudioRecordingService) {
        self.audioRecordingService = service
    }

    func setSpeechRecognitionService(_ service: SpeechRecognitionService) {
        self.speechRecognitionService = service
    }

    func setNotificationService(_ service: NotificationService) {
        self.notificationService = service
    }

    // MARK: - Private Methods - UI Setup

    private func setupView() {
        view = NSView()
        view.wantsLayer = true
        view.layer?.cornerRadius = 12
        view.layer?.backgroundColor = NSColor.controlBackgroundColor.cgColor

        setupContainerView()
        setupMicrophoneButton()
        setupAudioLevelView()
        setupStatusLabel()
        setupTranscriptionLabel()
        setupCancelButton()
        setupSettingsButton()
    }

    private func setupContainerView() {
        containerView = NSView()
        containerView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(containerView)
    }

    private func setupMicrophoneButton() {
        microphoneButton = NSButton()
        microphoneButton.image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Microphone")
        microphoneButton.alternateImage = NSImage(systemSymbolName: "mic.slash.fill", accessibilityDescription: "Stop Recording")
        microphoneButton.imageScaling = .scaleProportionallyUpOrDown
        microphoneButton.bezelStyle = .regularSquare
        microphoneButton.isBordered = false
        microphoneButton.translatesAutoresizingMaskIntoConstraints = false
        microphoneButton.target = self
        microphoneButton.action = #selector(microphoneButtonClicked)
        microphoneButton.wantsLayer = true
        microphoneButton.layer?.cornerRadius = 25

        view.addSubview(microphoneButton)
    }

    private func setupAudioLevelView() {
        audioLevelView = AudioLevelView()
        audioLevelView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(audioLevelView)
    }

    private func setupStatusLabel() {
        statusLabel = NSTextField()
        statusLabel.stringValue = "Click to start recording"
        statusLabel.font = NSFont.systemFont(ofSize: 14, weight: .medium)
        statusLabel.alignment = .center
        statusLabel.isEditable = false
        statusLabel.isBezeled = false
        statusLabel.drawsBackground = false
        statusLabel.textColor = .secondaryLabelColor
        statusLabel.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(statusLabel)
    }

    private func setupTranscriptionLabel() {
        transcriptionLabel = NSTextField()
        transcriptionLabel.stringValue = ""
        transcriptionLabel.font = NSFont.systemFont(ofSize: 16)
        transcriptionLabel.alignment = .center
        transcriptionLabel.isEditable = false
        transcriptionLabel.isBezeled = false
        transcriptionLabel.drawsBackground = false
        transcriptionLabel.textColor = .labelColor
        transcriptionLabel.lineBreakMode = .byWordWrapping
        transcriptionLabel.cell?.wraps = true
        transcriptionLabel.cell?.isScrollable = false
        transcriptionLabel.translatesAutoresizingMaskIntoConstraints = false
        transcriptionLabel.isHidden = true

        view.addSubview(transcriptionLabel)
    }

    private func setupCancelButton() {
        cancelButton = NSButton()
        cancelButton.title = "Cancel"
        cancelButton.bezelStyle = .rounded
        cancelButton.translatesAutoresizingMaskIntoConstraints = false
        cancelButton.target = self
        cancelButton.action = #selector(cancelButtonClicked)
        cancelButton.isHidden = true

        view.addSubview(cancelButton)
    }

    private func setupSettingsButton() {
        settingsButton = NSButton()
        settingsButton.image = NSImage(systemSymbolName: "gear", accessibilityDescription: "Settings")
        settingsButton.bezelStyle = .rounded
        settingsButton.imageScaling = .scaleProportionallyUpOrDown
        settingsButton.translatesAutoresizingMaskIntoConstraints = false
        settingsButton.target = self
        settingsButton.action = #selector(settingsButtonClicked)

        view.addSubview(settingsButton)
    }

    private func setupConstraints() {
        NSLayoutConstraint.activate([
            // Container view
            containerView.topAnchor.constraint(equalTo: view.topAnchor, constant: 16),
            containerView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            containerView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            containerView.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -16),

            // Microphone button
            microphoneButton.topAnchor.constraint(equalTo: containerView.topAnchor),
            microphoneButton.centerXAnchor.constraint(equalTo: containerView.centerXAnchor),
            microphoneButton.widthAnchor.constraint(equalToConstant: 50),
            microphoneButton.heightAnchor.constraint(equalToConstant: 50),

            // Audio level view
            audioLevelView.topAnchor.constraint(equalTo: microphoneButton.bottomAnchor, constant: 12),
            audioLevelView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            audioLevelView.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            audioLevelView.heightAnchor.constraint(equalToConstant: 60),

            // Status label
            statusLabel.topAnchor.constraint(equalTo: audioLevelView.bottomAnchor, constant: 12),
            statusLabel.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            statusLabel.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),

            // Transcription label
            transcriptionLabel.topAnchor.constraint(equalTo: audioLevelView.bottomAnchor, constant: 12),
            transcriptionLabel.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            transcriptionLabel.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            transcriptionLabel.bottomAnchor.constraint(lessThanOrEqualTo: cancelButton.topAnchor, constant: -12),

            // Cancel button
            cancelButton.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            cancelButton.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
            cancelButton.widthAnchor.constraint(equalToConstant: 80),
            cancelButton.heightAnchor.constraint(equalToConstant: 32),

            // Settings button
            settingsButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            settingsButton.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
            settingsButton.widthAnchor.constraint(equalToConstant: 32),
            settingsButton.heightAnchor.constraint(equalToConstant: 32)
        ])
    }

    // MARK: - Private Methods - UI Updates

    private func setupBindings() {
        session.$status
            .receive(on: DispatchQueue.main)
            .sink { [weak self] status in
                self?.updateUIForStatus(status)
            }
            .store(in: &cancellables)

        session.$audioLevel
            .receive(on: DispatchQueue.main)
            .sink { [weak self] level in
                self?.audioLevelView?.updateLevel(level)
            }
            .store(in: &cancellables)
    }

    private func updateUIForStatus(_ status: VoiceSessionStatus) {
        switch status {
        case .pending:
            updateUIForIdleState()
        case .recording:
            updateUIForRecordingState()
        case .processing:
            updateUIForProcessingState()
        case .completed:
            updateUIForCompletedState()
        case .failed:
            updateUIForErrorState()
        case .cancelled:
            updateUIForIdleState()
        }
    }

    private func updateUIForIdleState() {
        microphoneButton.state = .off
        microphoneButton.contentTintColor = .controlAccentColor
        statusLabel.stringValue = "Click to start recording"
        statusLabel.textColor = .secondaryLabelColor
        transcriptionLabel.isHidden = true
        cancelButton.isHidden = true
        audioLevelView?.reset()
    }

    private func updateUIForRecordingState() {
        microphoneButton.state = .on
        microphoneButton.contentTintColor = .systemRed
        statusLabel.stringValue = "Recording... Click to stop"
        statusLabel.textColor = .systemRed
        transcriptionLabel.isHidden = true
        cancelButton.isHidden = false
        audioLevelView?.setActive(true)
    }

    private func updateUIForProcessingState() {
        microphoneButton.isEnabled = false
        microphoneButton.contentTintColor = .systemBlue
        statusLabel.stringValue = "Processing..."
        statusLabel.textColor = .systemBlue
        cancelButton.isHidden = true
        audioLevelView?.setActive(false)
    }

    private func updateUIForCompletedState() {
        microphoneButton.isEnabled = true
        microphoneButton.contentTintColor = .systemGreen
        statusLabel.stringValue = "Recording completed"
        statusLabel.textColor = .systemGreen
        transcriptionLabel.isHidden = false
        cancelButton.isHidden = true
        audioLevelView?.setActive(false)
    }

    private func updateUIForErrorState() {
        microphoneButton.isEnabled = true
        microphoneButton.contentTintColor = .systemRed
        statusLabel.stringValue = "Recording failed"
        statusLabel.textColor = .systemRed
        transcriptionLabel.isHidden = true
        cancelButton.isHidden = true
        audioLevelView?.setActive(false)
    }

    // MARK: - Private Methods - Actions

    @objc private func microphoneButtonClicked() {
        switch session.status {
        case .pending, .completed, .failed, .cancelled:
            startRecording()
        case .recording:
            stopRecording()
        case .processing:
            // Do nothing during processing
            break
        }
    }

    @objc private func cancelButtonClicked() {
        cancelRecording()
    }

    @objc private func settingsButtonClicked() {
        // Post notification to show preferences
        NotificationCenter.default.post(name: .showPreferences, object: nil)
    }

    // MARK: - Private Methods - Helpers

    private func autoDismissAfterDelay() {
        Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
            await MainActor.run {
                self.reset()
            }
        }
    }
}

// MARK: - AudioRecordingDelegate

extension VoiceInputViewController: AudioRecordingDelegate {
    func audioRecording(_ service: AudioRecordingService, didReceiveBuffer buffer: AVAudioBuffer) {
        // Forward audio buffer to speech recognition service
        speechRecognitionService?.processAudioBuffer(buffer)
    }

    func audioRecording(_ service: AudioRecordingService, audioLevel: Float) {
        updateAudioLevel(audioLevel)
    }

    func audioRecording(_ service: AudioRecordingService, didFailWithError error: AudioRecordingError) {
        showError(error)
    }
}

// MARK: - VoiceSessionStatus Extension

extension VoiceSessionStatus {
    var isActive: Bool {
        switch self {
        case .recording, .processing:
            return true
        case .pending, .completed, .failed, .cancelled:
            return false
        }
    }
}

// MARK: - AudioLevelView

/// Custom view for displaying audio levels during recording.
class AudioLevelView: NSView {
    private var audioLevel: Float = 0.0
    private var isActive: Bool = false
    private var bars: [NSView] = []

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        setupBars()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupBars()
    }

    private func setupBars() {
        let barCount = 20
        let barWidth: CGFloat = 3
        let barSpacing: CGFloat = 2

        for i in 0..<barCount {
            let bar = NSView()
            bar.wantsLayer = true
            bar.layer?.cornerRadius = 1.5
            bar.translatesAutoresizingMaskIntoConstraints = false
            addSubview(bar)
            bars.append(bar)

            NSLayoutConstraint.activate([
                bar.widthAnchor.constraint(equalToConstant: barWidth),
                bar.heightAnchor.constraint(equalToConstant: CGFloat(i + 1) * 2),
                bar.bottomAnchor.constraint(equalTo: bottomAnchor),
                bar.leadingAnchor.constraint(equalTo: leadingAnchor, constant: CGFloat(i) * (barWidth + barSpacing))
            ])
        }
    }

    func updateLevel(_ level: Float) {
        audioLevel = max(0.0, min(1.0, level))
        updateBarAppearance()
    }

    func setActive(_ active: Bool) {
        isActive = active
        updateBarAppearance()
    }

    func reset() {
        audioLevel = 0.0
        isActive = false
        updateBarAppearance()
    }

    private func updateBarAppearance() {
        let activeBars = Int(audioLevel * CGFloat(bars.count))

        for (index, bar) in bars.enumerated() {
            if index < activeBars && isActive {
                bar.layer?.backgroundColor = NSColor.systemRed.cgColor
            } else {
                bar.layer?.backgroundColor = NSColor.controlBackgroundColor.cgColor
            }
        }

        needsDisplay = true
    }
}