# Data Model Specification

**Feature**: macOS Menubar Voice Assistant
**Version**: 1.0
**Date**: 2025-10-25

## Core Entities

### VoiceSession
Represents a single voice interaction from initiation to completion.

**Properties**:
- `id: UUID` - Unique identifier for the session
- `startTime: Date` - When the voice input was initiated
- `endTime: Date?` - When the session completed (null for active sessions)
- `status: VoiceSessionStatus` - Current state of the session
- `audioLevel: Float` - Current audio input level (0.0-1.0)
- `duration: TimeInterval` - Total session duration in seconds

**State Transitions**:
```
pending -> recording -> processing -> completed
pending -> recording -> failed
pending -> cancelled
```

### TranscriptionResult
Contains the speech recognition output and metadata.

**Properties**:
- `id: UUID` - Unique identifier
- `sessionId: UUID` - Reference to parent VoiceSession
- `text: String` - The recognized speech text
- `confidence: Float` - Recognition confidence score (0.0-1.0)
- `alternatives: [String]` - Alternative recognition results
- `isFinal: Bool` - Whether this is the final result
- `timestamp: Date` - When the transcription was generated

**Validation Rules**:
- `text` must not be empty for final results
- `confidence` must be between 0.0 and 1.0
- `alternatives` array should be ordered by confidence

### CommandExecution
Represents the execution of agent-tars command with voice input.

**Properties**:
- `id: UUID` - Unique identifier
- `sessionId: UUID` - Reference to parent VoiceSession
- `command: String` - The full command executed (e.g., "agent-tars run --input 'text'")
- `inputText: String` - The voice input text
- `startTime: Date` - When command execution started
- `endTime: Date?` - When execution completed
- `status: CommandStatus` - Execution status
- `exitCode: Int?` - Process exit code
- `stdout: String` - Standard output
- `stderr: String` - Standard error output
- `duration: TimeInterval?` - Execution duration in seconds

**State Transitions**:
```
pending -> running -> completed
pending -> running -> failed
pending -> cancelled
```

### UserPreferences
Stores user configuration and accessibility settings.

**Properties**:
- `language: String` - Preferred recognition language (e.g., "en-US")
- `keyboardShortcut: String` - Global keyboard shortcut (e.g., "⌃⌥V")
- `autoStart: Bool` - Whether to auto-start on login
- `showNotifications: Bool` - Whether to show system notifications
- `recordingTimeout: TimeInterval` - Maximum recording duration in seconds
- `confidenceThreshold: Float` - Minimum confidence for auto-acceptance
- `enableHapticFeedback: Bool` - Haptic feedback on interactions
- `preferredVoice: String?` - System voice for text-to-speech feedback

**Default Values**:
- `language`: "en-US"
- `keyboardShortcut`: "⌃⌥V" (Ctrl+Option+V)
- `autoStart`: false
- `showNotifications`: true
- `recordingTimeout`: 30.0
- `confidenceThreshold`: 0.7
- `enableHapticFeedback`: true

## Enums

### VoiceSessionStatus
```swift
enum VoiceSessionStatus: String, CaseIterable {
    case pending = "pending"      // User clicked menubar, waiting to start
    case recording = "recording"  // Currently recording audio
    case processing = "processing" // Transcribing speech
    case completed = "completed"  // Successfully completed
    case failed = "failed"        // Failed with error
    case cancelled = "cancelled"  // User cancelled
}
```

### CommandStatus
```swift
enum CommandStatus: String, CaseIterable {
    case pending = "pending"      // Waiting to execute
    case running = "running"      // Currently executing
    case completed = "completed"  // Successfully completed
    case failed = "failed"        // Failed with error
    case cancelled = "cancelled"  // User cancelled
    case timeout = "timeout"      // Execution timed out
}
```

### PermissionStatus
```swift
enum PermissionStatus: String, CaseIterable {
    case notDetermined = "not_determined"
    case granted = "granted"
    case denied = "denied"
    case restricted = "restricted"
}
```

## Relationships

```
VoiceSession (1) -----> (1) TranscriptionResult
VoiceSession (1) -----> (1) CommandExecution
UserPreferences (1) -----> (N) VoiceSession (global configuration)
```

## Data Storage

### UserDefaults Schema
User preferences are stored in UserDefaults with the following keys:

```swift
struct UserDefaultsKeys {
    static let language = "voiceAssistant.language"
    static let keyboardShortcut = "voiceAssistant.keyboardShortcut"
    static let autoStart = "voiceAssistant.autoStart"
    static let showNotifications = "voiceAssistant.showNotifications"
    static let recordingTimeout = "voiceAssistant.recordingTimeout"
    static let confidenceThreshold = "voiceAssistant.confidenceThreshold"
    static let enableHapticFeedback = "voiceAssistant.enableHapticFeedback"
    static let preferredVoice = "voiceAssistant.preferredVoice"
    static let firstLaunch = "voiceAssistant.firstLaunch"
}
```

### In-Memory Storage
Active sessions and recent results are kept in memory during app runtime:
- Current active `VoiceSession`
- Last 10 `TranscriptionResult` items for quick access
- Last 10 `CommandExecution` results for history

## Data Validation

### VoiceSession Validation
- `id` must be a valid UUID
- `startTime` must be before `endTime` if both present
- `duration` must be non-negative
- `audioLevel` must be between 0.0 and 1.0

### TranscriptionResult Validation
- `text` must not be empty for final results
- `confidence` must be between 0.0 and 1.0
- `alternatives` array must not contain empty strings
- `sessionId` must reference a valid VoiceSession

### CommandExecution Validation
- `command` must not be empty
- `inputText` must not be empty
- `exitCode` must be valid if present
- `startTime` must be before `endTime` if both present

## Privacy and Security

### Data Handling
- No voice data is stored permanently
- Transcription results are kept only in memory during session
- Command execution results are not logged persistently
- No network transmission of voice or text data

### Memory Management
- Audio buffers are released immediately after processing
- Session data is cleared after completion
- Weak references prevent retain cycles
- Memory usage monitored and limited

## Error Handling

### Validation Errors
```swift
enum ValidationError: Error {
    case invalidSession(String)
    case invalidTranscription(String)
    case invalidCommand(String)
    case invalidPreferences(String)
}
```

### Data Corruption Handling
- Graceful fallback to default values
- Session restart on data inconsistency
- User notification of data issues
- Automatic cleanup of corrupted data