import Foundation

// MARK: - UserPreferences

/// Stores user configuration and accessibility settings.
struct UserPreferences: Codable, Sendable {
    // MARK: - Properties

    /// Preferred recognition language (e.g., "en-US")
    var language: String

    /// Global keyboard shortcut (e.g., "⌃⌥V")
    var keyboardShortcut: String

    /// Whether to auto-start on login
    var autoStart: Bool

    /// Whether to show system notifications
    var showNotifications: Bool

    /// Maximum recording duration in seconds
    var recordingTimeout: TimeInterval

    /// Minimum confidence for auto-acceptance
    var confidenceThreshold: Float

    /// Haptic feedback on interactions
    var enableHapticFeedback: Bool

    /// System voice for text-to-speech feedback
    var preferredVoice: String?

    // MARK: - Default Values

    static let `default` = UserPreferences(
        language: "en-US",
        keyboardShortcut: "⌃⌥V",  // Ctrl+Option+V
        autoStart: false,
        showNotifications: true,
        recordingTimeout: 30.0,
        confidenceThreshold: 0.7,
        enableHapticFeedback: true,
        preferredVoice: nil
    )

    // MARK: - Validation

    /// Validate preferences values
    var isValid: Bool {
        // Language should not be empty
        guard !language.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return false
        }

        // Keyboard shortcut should not be empty
        guard !keyboardShortcut.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return false
        }

        // Recording timeout should be positive and reasonable
        guard recordingTimeout > 0 && recordingTimeout <= 300 else {
            return false
        }

        // Confidence threshold should be between 0.0 and 1.0
        guard confidenceThreshold >= 0.0 && confidenceThreshold <= 1.0 else {
            return false
        }

        return true
    }

    // MARK: - Localization

    /// Get localized display name for language
    var localizedLanguage: String {
        let locale = Locale(identifier: language)
        return locale.localizedString(forIdentifier: language) ?? language
    }

    /// Get supported languages for speech recognition
    static var supportedLanguages: [(code: String, name: String)] {
        return [
            ("en-US", "English (United States)"),
            ("en-GB", "English (United Kingdom)"),
            ("en-AU", "English (Australia)"),
            ("en-CA", "English (Canada)"),
            ("en-IN", "English (India)"),
            ("zh-CN", "Chinese (Simplified)"),
            ("zh-TW", "Chinese (Traditional)"),
            ("ja-JP", "Japanese"),
            ("ko-KR", "Korean"),
            ("es-ES", "Spanish (Spain)"),
            ("es-MX", "Spanish (Mexico)"),
            ("fr-FR", "French (France)"),
            ("fr-CA", "French (Canada)"),
            ("de-DE", "German (Germany)"),
            ("it-IT", "Italian (Italy)"),
            ("pt-BR", "Portuguese (Brazil)"),
            ("ru-RU", "Russian (Russia)"),
            ("ar-SA", "Arabic (Saudi Arabia)")
        ]
    }

    // MARK: - Keyboard Shortcuts

    /// Validate keyboard shortcut format
    var isValidKeyboardShortcut: Bool {
        // Basic validation - should contain modifier keys
        let modifiers = ["⌃", "⌥", "⇧", "⌘"]
        return modifiers.contains { keyboardShortcut.contains($0) }
    }

    /// Parse keyboard shortcut components
    var keyboardShortcutComponents: (modifiers: String, key: String) {
        let modifiers = ["⌃", "⌥", "⇧", "⌘"]
        var shortcutModifiers = ""
        var key = ""

        for char in keyboardShortcut {
            if modifiers.contains(String(char)) {
                shortcutModifiers += String(char)
            } else {
                key += String(char)
            }
        }

        return (shortcutModifiers, key)
    }

    // MARK: - Preferences Management

    /// Reset to default values
    mutating func resetToDefaults() {
        self = Self.default
    }

    /// Create a copy with updated language
    func with(language: String) -> UserPreferences {
        var prefs = self
        prefs.language = language
        return prefs
    }

    /// Create a copy with updated keyboard shortcut
    func with(keyboardShortcut: String) -> UserPreferences {
        var prefs = self
        prefs.keyboardShortcut = keyboardShortcut
        return prefs
    }

    /// Create a copy with updated auto-start setting
    func with(autoStart: Bool) -> UserPreferences {
        var prefs = self
        prefs.autoStart = autoStart
        return prefs
    }

    /// Create a copy with updated notifications setting
    func with(showNotifications: Bool) -> UserPreferences {
        var prefs = self
        prefs.showNotifications = showNotifications
        return prefs
    }

    /// Create a copy with updated recording timeout
    func with(recordingTimeout: TimeInterval) -> UserPreferences {
        var prefs = self
        prefs.recordingTimeout = recordingTimeout
        return prefs
    }

    /// Create a copy with updated confidence threshold
    func with(confidenceThreshold: Float) -> UserPreferences {
        var prefs = self
        prefs.confidenceThreshold = confidenceThreshold
        return prefs
    }

    /// Create a copy with updated haptic feedback setting
    func with(enableHapticFeedback: Bool) -> UserPreferences {
        var prefs = self
        prefs.enableHapticFeedback = enableHapticFeedback
        return prefs
    }

    /// Create a copy with updated preferred voice
    func with(preferredVoice: String?) -> UserPreferences {
        var prefs = self
        prefs.preferredVoice = preferredVoice
        return prefs
    }
}