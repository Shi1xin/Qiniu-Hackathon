import AppKit
import Foundation
import AVFoundation
import Speech

/// Main application coordinator that manages all services and UI components.
@MainActor
class VoiceAssistantApp: ObservableObject {
    // MARK: - Properties

    private var menubarManager: MenubarManager?
    private var preferencesService: PreferencesService?
    private var speechRecognitionService: SpeechRecognitionService?
    private var audioRecordingService: AudioRecordingService?
    private var commandExecutionService: CommandExecutionService?
    private var notificationService: NotificationService?
    private var popoverController: PopoverController?

    // Voice session management
    private var currentVoiceSession: VoiceSession?

    /// Application state
    @Published var isRunning = false

    // MARK: - Initialization

    init() {
        setupServices()
    }

    // MARK: - Application Lifecycle

    /// Start the application
    func start() {
        guard !isRunning else { return }

        do {
            try setupMenubar()
            setupVoiceInputInterface()
            requestPermissions()
            isRunning = true
            print("Voice Assistant started successfully")
        } catch {
            print("Failed to start Voice Assistant: \(error)")
            notificationService?.showErrorNotification(error)
        }
    }

    /// Stop the application
    func stop() {
        guard isRunning else { return }

        // Cancel any ongoing voice session
        if let session = currentVoiceSession {
            session.cancel()
        }

        menubarManager?.cleanup()
        menubarManager = nil
        popoverController = nil

        // Clear services
        speechRecognitionService = nil
        audioRecordingService = nil
        commandExecutionService = nil
        notificationService = nil
        preferencesService = nil

        isRunning = false
        print("Voice Assistant stopped")
    }

    // MARK: - Voice Input Management

    /// Start voice input session
    func startVoiceInput() {
        Task {
            await beginVoiceSession()
        }
    }

    private func beginVoiceSession() async {
        guard let speechService = speechRecognitionService,
              let audioService = audioRecordingService,
              let commandService = commandExecutionService else {
            print("Services not properly initialized")
            return
        }

        // Create new voice session
        let session = VoiceSession()
        currentVoiceSession = session

        do {
            // Start voice input
            try await audioService.startRecording(delegate: self)
            session.startRecording()

            // Update menubar state
            menubarManager?.updateIcon(state: .listening)

        } catch {
            session.fail()
            await handleVoiceSessionError(error)
        }
    }

    private func stopVoiceInput() {
        Task {
            await endVoiceSession()
        }
    }

    private func endVoiceSession() async {
        guard let session = currentVoiceSession else { return }

        session.startProcessing()
        menubarManager?.updateIcon(state: .processing)

        // Stop recording
        await audioRecordingService?.stopRecording()

        // Stop recognition
        await speechRecognitionService?.stopRecognition()
    }

    private func completeVoiceSession(with transcription: TranscriptionResult) async {
        guard let session = currentVoiceSession,
              let commandService = commandExecutionService else { return }

        session.complete()

        do {
            // Execute agent-tars command
            try await commandService.executeCommand(input: transcription.text, delegate: self)
        } catch {
            await handleCommandExecutionError(error)
        }
    }

    // MARK: - Private Setup

    private func setupServices() {
        // Initialize services in dependency order
        preferencesService = PreferencesManager()
        notificationService = NotificationManager(preferencesService: preferencesService!)
        speechRecognitionService = SpeechRecognitionManager()
        audioRecordingService = AudioRecordingManager()
        commandExecutionService = CommandExecutionManager()
    }

    private func setupMenubar() throws {
        menubarManager = try MenubarManager(preferencesService: preferencesService!)
        menubarManager?.delegate = self
        menubarManager?.setup()
    }

    private func setupVoiceInputInterface() {
        guard let prefs = preferencesService else { return }

        let voiceInputVC = VoiceInputViewController(
            audioRecordingService: audioRecordingService!,
            speechRecognitionService: speechRecognitionService!
        )
        voiceInputVC.delegate = self

        popoverController = PopoverController(viewController: voiceInputVC)
        menubarManager?.setPopoverController(popoverController)
    }

    private func requestPermissions() {
        Task {
            let micGranted = await requestMicrophonePermission()
            let speechGranted = await requestSpeechRecognitionPermission()

            if !micGranted || !speechGranted {
                notificationService?.showNotification(
                    title: "Permissions Required",
                    message: "Please enable microphone and speech recognition permissions in System Preferences.",
                    identifier: "permissions-required"
                )
            }
        }
    }

    // MARK: - Permission Requests

    private func requestMicrophonePermission() async -> Bool {
        guard let audioService = audioRecordingService else { return false }

        let granted = await audioService.requestMicrophonePermission()
        if !granted {
            print("Microphone permission denied")
        }
        return granted
    }

    private func requestSpeechRecognitionPermission() async -> Bool {
        guard let speechService = speechRecognitionService else { return false }

        let status = await speechService.requestAuthorization()
        let granted = status == .authorized
        if !granted {
            print("Speech recognition permission denied")
        }
        return granted
    }

    // MARK: - Error Handling

    private func handleVoiceSessionError(_ error: Error) async {
        menubarManager?.updateIcon(state: .error)

        if let speechError = error as? SpeechRecognitionError {
            notificationService?.showErrorNotification(speechError)
        } else if let audioError = error as? AudioRecordingError {
            notificationService?.showErrorNotification(audioError)
        } else {
            notificationService?.showErrorNotification(error)
        }

        // Reset after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            self.menubarManager?.updateIcon(state: .idle)
        }
    }

    private func handleCommandExecutionError(_ error: Error) async {
        menubarManager?.updateIcon(state: .error)

        if let commandError = error as? CommandExecutionError {
            notificationService?.showErrorNotification(commandError)
        } else {
            notificationService?.showErrorNotification(error)
        }

        // Reset after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            self.menubarManager?.updateIcon(state: .idle)
        }
    }
}

// MARK: - MenubarInterfaceDelegate

extension VoiceAssistantApp: MenubarInterfaceDelegate {
    func menubarInterfaceDidClickIcon(_ interface: MenubarInterface) {
        startVoiceInput()
    }

    func menubarInterface(_ interface: MenubarInterface, didSelectMenuItem item: MenuItem) {
        switch item {
        case .voiceInput:
            startVoiceInput()
        case .preferences:
            // TODO: Open preferences window
            print("Preferences requested")
        case .about:
            // TODO: Show about dialog
            print("About requested")
        case .quit:
            NSApplication.shared.terminate(nil)
        }
    }
}

// MARK: - VoiceInputDelegate

extension VoiceAssistantApp: VoiceInputDelegate {
    func voiceInputControllerDidStartInput(_ controller: VoiceInputViewControllerProtocol) {
        // Voice input started via UI
        beginVoiceSession()
    }

    func voiceInputControllerDidStopInput(_ controller: VoiceInputViewControllerProtocol) {
        // Voice input stopped via UI
        endVoiceSession()
    }

    func voiceInputControllerDidRequestRetry(_ controller: VoiceInputViewControllerProtocol) {
        // Retry voice input
        startVoiceInput()
    }

    func voiceInputController(_ controller: VoiceInputViewControllerProtocol, didConfirmText text: String) {
        // User confirmed transcribed text
        if let session = currentVoiceSession {
            let transcription = TranscriptionResult.final(
                sessionId: session.id,
                text: text,
                confidence: 1.0 // User confirmed, so high confidence
            )
            Task {
                await completeVoiceSession(with: transcription)
            }
        }
    }

    func voiceInputController(_ controller: VoiceInputViewControllerProtocol, didEditText text: String) {
        // User edited transcribed text
        // This will be handled when user confirms
    }
}

// MARK: - SpeechRecognitionDelegate

extension VoiceAssistantApp: SpeechRecognitionDelegate {
    func speechRecognition(_ service: SpeechRecognitionService, didReceive result: TranscriptionResult) {
        // Forward to voice input controller if available
        if let popover = popoverController {
            popover.contentViewController?.showRecognizedText(result.text)
        }

        // Check confidence threshold
        guard let prefs = preferencesService else { return }

        if result.isFinal && result.confidence >= prefs.preferences.confidenceThreshold {
            Task {
                await completeVoiceSession(with: result)
            }
        }
    }

    func speechRecognition(_ service: SpeechRecognitionService, didFailWithError error: SpeechRecognitionError) {
        Task {
            await handleVoiceSessionError(error)
        }
    }

    func speechRecognitionDidFinish(_ service: SpeechRecognitionService) {
        menubarManager?.updateIcon(state: .idle)
        currentVoiceSession = nil
    }

    func speechRecognition(_ service: SpeechRecognitionService, audioLevel: Float) {
        // Update audio level in voice input controller
        if let popover = popoverController {
            popover.contentViewController?.updateAudioLevel(audioLevel)
        }
    }
}

// MARK: - AudioRecordingDelegate

extension VoiceAssistantApp: AudioRecordingDelegate {
    func audioRecording(_ service: AudioRecordingService, didReceiveBuffer buffer: AVAudioBuffer) {
        // Audio buffer received - handled by speech recognition service
    }

    func audioRecording(_ service: AudioRecordingService, audioLevel: Float) {
        // Update audio level in menubar and voice input controller
        currentVoiceSession?.updateAudioLevel(audioLevel)
        menubarManager?.updateAudioLevel(audioLevel)

        if let popover = popoverController {
            popover.contentViewController?.updateAudioLevel(audioLevel)
        }
    }

    func audioRecording(_ service: AudioRecordingService, didFailWithError error: AudioRecordingError) {
        Task {
            await handleVoiceSessionError(error)
        }
    }
}

// MARK: - CommandExecutionDelegate

extension VoiceAssistantApp: CommandExecutionDelegate {
    func commandExecutionDidStart(_ service: CommandExecutionService) {
        print("Command execution started")
    }

    func commandExecution(_ service: CommandExecutionService, didReceiveOutput output: String) {
        // Handle command output
        print("Command output: \(output)")
    }

    func commandExecution(_ service: CommandExecutionService, didReceiveError error: String) {
        print("Command error: \(error)")
    }

    func commandExecutionDidComplete(_ service: CommandExecutionService, result: CommandExecutionResult) {
        menubarManager?.updateIcon(state: .idle)

        if result.isSuccess {
            notificationService?.showSuccessNotification("Command executed successfully")
        } else {
            notificationService?.showErrorNotification(result.displayResult)
        }

        currentVoiceSession = nil
    }

    func commandExecution(_ service: CommandExecutionService, didFailWithError error: CommandExecutionError) {
        Task {
            await handleCommandExecutionError(error)
        }
    }
}