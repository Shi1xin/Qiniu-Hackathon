# Internal API Contracts

**Feature**: macOS Menubar Voice Assistant
**Version**: 1.0
**Date**: 2025-10-25

## Overview

This document defines the internal contracts between components of the voice assistant application. Since this is a single-process application, these are primarily Swift protocols and interfaces rather than network APIs.

## Core Service Protocols

### SpeechRecognitionService

```swift
protocol SpeechRecognitionService {
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

protocol SpeechRecognitionDelegate: AnyObject {
    /// Speech recognition produced a result
    func speechRecognition(_ service: SpeechRecognitionService, didReceive result: TranscriptionResult)

    /// Speech recognition encountered an error
    func speechRecognition(_ service: SpeechRecognitionService, didFailWithError error: SpeechRecognitionError)

    /// Speech recognition finished
    func speechRecognitionDidFinish(_ service: SpeechRecognitionService)

    /// Audio level changed during recording
    func speechRecognition(_ service: SpeechRecognitionService, audioLevel: Float)
}
```

### AudioRecordingService

```swift
protocol AudioRecordingService {
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

protocol AudioRecordingDelegate: AnyObject {
    /// Audio buffer received during recording
    func audioRecording(_ service: AudioRecordingService, didReceiveBuffer buffer: AVAudioBuffer)

    /// Recording level changed
    func audioRecording(_ service: AudioRecordingService, audioLevel: Float)

    /// Recording encountered an error
    func audioRecording(_ service: AudioRecordingService, didFailWithError error: AudioRecordingError)
}
```

### CommandExecutionService

```swift
protocol CommandExecutionService {
    /// Execute agent-tars command with voice input
    /// - Parameters:
    ///   - input: Voice input text
    ///   - delegate: Delegate to receive execution updates
    /// - Throws: CommandExecutionError
    func executeCommand(input: String, delegate: CommandExecutionDelegate) async throws

    /// Cancel current command execution
    func cancelExecution() async
}

protocol CommandExecutionDelegate: AnyObject {
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
```

### PreferencesService

```swift
protocol PreferencesService {
    /// User preferences
    var preferences: UserPreferences { get }

    /// Load preferences from storage
    func loadPreferences() -> UserPreferences

    /// Save preferences to storage
    func savePreferences(_ preferences: UserPreferences) async throws

    /// Update specific preference
    func updatePreference<T>(_ key: WritableKeyPath<UserPreferences, T>, to value: T) async throws

    /// Reset preferences to defaults
    func resetToDefaults() async throws
}
```

### NotificationService

```swift
protocol NotificationService {
    /// Show system notification
    /// - Parameters:
    ///   - title: Notification title
    ///   - message: Notification message
    ///   - identifier: Unique notification identifier
    func showNotification(title: String, message: String, identifier: String) async

    /// Show error notification
    func showErrorNotification(_ error: Error) async

    /// Show success notification
    func showSuccessNotification(_ message: String) async

    /// Clear specific notification
    func clearNotification(identifier: String) async

    /// Clear all notifications
    func clearAllNotifications() async
}
```

## UI Component Protocols

### MenubarInterface

```swift
protocol MenubarInterface: AnyObject {
    /// Show voice input popover
    func showVoiceInputPopover()

    /// Hide voice input popover
    func hideVoiceInputPopover()

    /// Update menubar icon state
    func updateIcon(state: MenubarIconState)

    /// Show menubar menu
    func showMenu()

    /// Delegate for menubar interactions
    var delegate: MenubarInterfaceDelegate? { get set }
}

enum MenubarIconState {
    case idle           // Default mic icon
    case listening      // Pulsing/recording icon
    case processing     // Processing/spinning icon
    case error          // Error state icon
}

protocol MenubarInterfaceDelegate: AnyObject {
    /// User clicked menubar icon
    func menubarInterfaceDidClickIcon(_ interface: MenubarInterface)

    /// User selected menu item
    func menubarInterface(_ interface: MenubarInterface, didSelectMenuItem item: MenuItem)
}

enum MenuItem {
    case voiceInput
    case preferences
    case about
    case quit
}
```

### VoiceInputViewController

```swift
protocol VoiceInputViewController: AnyObject {
    /// Current state of voice input
    var state: VoiceInputState { get set }

    /// Delegate for voice input events
    var delegate: VoiceInputDelegate? { get set }

    /// Start voice input session
    func startVoiceInput()

    /// Stop voice input session
    func stopVoiceInput()

    /// Show recognized text
    func showRecognizedText(_ text: String)

    /// Show processing state
    func showProcessing()

    /// Show error message
    func showError(_ message: String)

    /// Show command result
    func showCommandResult(_ result: String)
}

enum VoiceInputState {
    case idle
    case requestingPermissions
    case recording
    case processing
    case showingResult
    case showingError
}

protocol VoiceInputDelegate: AnyObject {
    /// User started voice input
    func voiceInputControllerDidStartInput(_ controller: VoiceInputViewController)

    /// User stopped voice input
    func voiceInputControllerDidStopInput(_ controller: VoiceInputViewController)

    /// User wants to retry voice input
    func voiceInputControllerDidRequestRetry(_ controller: VoiceInputViewController)

    /// User confirmed recognized text
    func voiceInputController(_ controller: VoiceInputViewController, didConfirmText text: String)

    /// User edited recognized text
    func voiceInputController(_ controller: VoiceInputViewController, didEditText text: String)
}
```

## Data Transfer Objects

### TranscriptionResult

```swift
struct TranscriptionResult: Codable, Sendable {
    let id: UUID
    let sessionId: UUID
    let text: String
    let confidence: Float
    let alternatives: [String]
    let isFinal: Bool
    let timestamp: Date

    init(sessionId: UUID, text: String, confidence: Float, alternatives: [String] = [], isFinal: Bool = false) {
        self.id = UUID()
        self.sessionId = sessionId
        self.text = text
        self.confidence = confidence
        self.alternatives = alternatives
        self.isFinal = isFinal
        self.timestamp = Date()
    }
}
```

### CommandExecutionResult

```swift
struct CommandExecutionResult: Codable, Sendable {
    let id: UUID
    let sessionId: UUID
    let command: String
    let inputText: String
    let status: CommandStatus
    let exitCode: Int?
    let stdout: String
    let stderr: String
    let startTime: Date
    let endTime: Date?

    var duration: TimeInterval? {
        guard let endTime = endTime else { return nil }
        return endTime.timeIntervalSince(startTime)
    }

    init(sessionId: UUID, command: String, inputText: String) {
        self.id = UUID()
        self.sessionId = sessionId
        self.command = command
        self.inputText = inputText
        self.status = .pending
        self.exitCode = nil
        self.stdout = ""
        self.stderr = ""
        self.startTime = Date()
        self.endTime = nil
    }
}
```

### UserPreferences

```swift
struct UserPreferences: Codable, Sendable {
    var language: String
    var keyboardShortcut: String
    var autoStart: Bool
    var showNotifications: Bool
    var recordingTimeout: TimeInterval
    var confidenceThreshold: Float
    var enableHapticFeedback: Bool
    var preferredVoice: String?

    static let `default` = UserPreferences(
        language: "en-US",
        keyboardShortcut: "⌃⌥V",
        autoStart: false,
        showNotifications: true,
        recordingTimeout: 30.0,
        confidenceThreshold: 0.7,
        enableHapticFeedback: true,
        preferredVoice: nil
    )
}
```

## Error Types

### SpeechRecognitionError

```swift
enum SpeechRecognitionError: Error, LocalizedError {
    case notAuthorized
    case recognitionUnavailable
    case recognitionFailed(Error)
    case audioSessionFailed(Error)
    case timeout

    var errorDescription: String? {
        switch self {
        case .notAuthorized:
            return "Speech recognition is not authorized. Please enable it in System Preferences."
        case .recognitionUnavailable:
            return "Speech recognition is currently unavailable."
        case .recognitionFailed(let error):
            return "Speech recognition failed: \(error.localizedDescription)"
        case .audioSessionFailed(let error):
            return "Audio session failed: \(error.localizedDescription)"
        case .timeout:
            return "Speech recognition timed out."
        }
    }
}
```

### CommandExecutionError

```swift
enum CommandExecutionError: Error, LocalizedError {
    case commandNotFound
    case executionFailed(String)
    case timeout
    case permissionDenied
    case invalidInput

    var errorDescription: String? {
        switch self {
        case .commandNotFound:
            return "agent-tars command not found. Please ensure it's installed."
        case .executionFailed(let message):
            return "Command execution failed: \(message)"
        case .timeout:
            return "Command execution timed out."
        case .permissionDenied:
            return "Permission denied to execute command."
        case .invalidInput:
            return "Invalid input provided."
        }
    }
}
```

## Service Integration Flow

### Voice Command Execution Flow

```
1. User clicks menubar icon
   ↓
2. MenubarInterface → VoiceInputViewController.startVoiceInput()
   ↓
3. SpeechRecognitionService.startRecognition()
   ↓
4. AudioRecordingService.startRecording()
   ↓
5. SpeechRecognitionDelegate.didReceive(result: TranscriptionResult)
   ↓
6. CommandExecutionService.executeCommand(input: result.text)
   ↓
7. CommandExecutionDelegate.didComplete(result: CommandExecutionResult)
   ↓
8. VoiceInputViewController.showCommandResult()
```

### Error Handling Flow

```
1. Service encounters error
   ↓
2. Service.delegate.serviceDidFail(error: Error)
   ↓
3. UI Controller shows error state
   ↓
4. User can retry or access preferences
   ↓
5. Optional: NotificationService shows error notification
```

## Implementation Notes

### Thread Safety
- All UI updates must occur on @MainActor
- Service delegates should handle background thread execution
- Use Sendable protocols for data transfer objects
- Implement proper isolation for shared state

### Memory Management
- Use weak references for delegates
- Implement proper cleanup in service deinitialization
- Monitor and limit memory usage for audio buffers
- Clear temporary data after session completion

### Performance Considerations
- Minimize UI updates during recording
- Use efficient data structures for results
- Implement proper streaming for long command outputs
- Cache frequently accessed preferences