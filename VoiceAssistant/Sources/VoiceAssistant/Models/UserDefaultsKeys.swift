import Foundation

/// UserDefaults keys for storing user preferences and application state.
struct UserDefaultsKeys {
    // MARK: - User Preferences

    /// Preferred recognition language
    static let language = "voiceAssistant.language"

    /// Global keyboard shortcut
    static let keyboardShortcut = "voiceAssistant.keyboardShortcut"

    /// Auto-start on login setting
    static let autoStart = "voiceAssistant.autoStart"

    /// Show notifications setting
    static let showNotifications = "voiceAssistant.showNotifications"

    /// Recording timeout in seconds
    static let recordingTimeout = "voiceAssistant.recordingTimeout"

    /// Confidence threshold for auto-acceptance
    static let confidenceThreshold = "voiceAssistant.confidenceThreshold"

    /// Haptic feedback setting
    static let enableHapticFeedback = "voiceAssistant.enableHapticFeedback"

    /// Preferred system voice for TTS
    static let preferredVoice = "voiceAssistant.preferredVoice"

    // MARK: - Application State

    /// First launch flag
    static let firstLaunch = "voiceAssistant.firstLaunch"

    /// Last used version
    static let lastVersion = "voiceAssistant.lastVersion"

    /// Permission request timestamps
    static let microphonePermissionRequested = "voiceAssistant.microphonePermissionRequested"
    static let speechRecognitionPermissionRequested = "voiceAssistant.speechRecognitionPermissionRequested"

    // MARK: - Usage Statistics (Optional)

    /// Total number of voice sessions
    static let totalSessions = "voiceAssistant.totalSessions"

    /// Last session date
    static let lastSessionDate = "voiceAssistant.lastSessionDate"

    /// Average session duration
    static let averageSessionDuration = "voiceAssistant.averageSessionDuration"

    // MARK: - Debug Settings (Development Only)

    /// Enable debug logging
    static let debugLoggingEnabled = "voiceAssistant.debugLoggingEnabled"

    /// Debug log level
    static let debugLogLevel = "voiceAssistant.debugLogLevel"

    // MARK: - Helper Methods

    /// Get all preference keys (excludes debug and statistics keys)
    static var allPreferenceKeys: [String] {
        return [
            language,
            keyboardShortcut,
            autoStart,
            showNotifications,
            recordingTimeout,
            confidenceThreshold,
            enableHapticFeedback,
            preferredVoice
        ]
    }

    /// Get all application state keys
    static var allStateKeys: [String] {
        return [
            firstLaunch,
            lastVersion,
            microphonePermissionRequested,
            speechRecognitionPermissionRequested
        ]
    }

    /// Get all statistics keys
    static var allStatisticsKeys: [String] {
        return [
            totalSessions,
            lastSessionDate,
            averageSessionDuration
        ]
    }

    /// Get all debug keys
    static var allDebugKeys: [String] {
        return [
            debugLoggingEnabled,
            debugLogLevel
        ]
    }

    /// Get all keys (for debugging or reset purposes)
    static var allKeys: [String] {
        return allPreferenceKeys + allStateKeys + allStatisticsKeys + allDebugKeys
    }

    // MARK: - Validation

    /// Validate that all keys are unique
    static var hasUniqueKeys: Bool {
        let allKeysList = allKeys
        let uniqueKeys = Set(allKeysList)
        return allKeysList.count == uniqueKeys.count
    }

    /// Check if a key is a preference key
    static func isPreferenceKey(_ key: String) -> Bool {
        return allPreferenceKeys.contains(key)
    }

    /// Check if a key is a state key
    static func isStateKey(_ key: String) -> Bool {
        return allStateKeys.contains(key)
    }

    /// Check if a key is a statistics key
    static func isStatisticsKey(_ key: String) -> Bool {
        return allStatisticsKeys.contains(key)
    }

    /// Check if a key is a debug key
    static func isDebugKey(_ key: String) -> Bool {
        return allDebugKeys.contains(key)
    }
}