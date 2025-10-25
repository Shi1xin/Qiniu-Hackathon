import Foundation
import Combine

// MARK: - PreferencesService Protocol

/// Protocol for managing user preferences and application settings.
protocol PreferencesService: AnyObject {
    /// Current user preferences
    var preferences: UserPreferences { get }

    /// Publisher for preference changes
    var preferencesPublisher: AnyPublisher<UserPreferences, Never> { get }

    /// Load preferences from storage
    /// - Returns: Loaded user preferences
    func loadPreferences() -> UserPreferences

    /// Save preferences to storage
    /// - Parameter preferences: Preferences to save
    /// - Throws: ValidationError if preferences are invalid
    func savePreferences(_ preferences: UserPreferences) throws

    /// Update specific preference fields
    /// - Parameter update: Closure to modify preferences
    /// - Throws: ValidationError if updated preferences are invalid
    func updatePreferences(_ update: (inout UserPreferences) -> Void) throws

    /// Reset preferences to default values
    func resetToDefaults() throws

    /// Validate preferences
    /// - Parameter preferences: Preferences to validate
    /// - Returns: True if preferences are valid
    func validatePreferences(_ preferences: UserPreferences) -> Bool

    /// Export preferences to data
    /// - Parameter preferences: Preferences to export
    /// - Returns: Encoded preferences data
    /// - Throws: Encoding error
    func exportPreferences(_ preferences: UserPreferences) throws -> Data

    /// Import preferences from data
    /// - Parameter data: Encoded preferences data
    /// - Returns: Decoded preferences
    /// - Throws: Decoding or validation error
    func importPreferences(from data: Data) throws -> UserPreferences
}

// MARK: - PreferencesManager

/// Concrete implementation of PreferencesService using UserDefaults.
@MainActor
class PreferencesManager: PreferencesService {
    // MARK: - Properties

    private let userDefaults: UserDefaults
    private let preferencesSubject = CurrentValueSubject<UserPreferences, Never>(UserPreferences.default)

    var preferences: UserPreferences {
        return preferencesSubject.value
    }

    var preferencesPublisher: AnyPublisher<UserPreferences, Never> {
        preferencesSubject.eraseToAnyPublisher()
    }

    // MARK: - Initialization

    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        loadAndPublishPreferences()
    }

    // MARK: - PreferencesService Implementation

    func loadPreferences() -> UserPreferences {
        let loadedPreferences = UserPreferences(
            language: userDefaults.string(forKey: UserDefaultsKeys.language) ?? UserPreferences.default.language,
            keyboardShortcut: userDefaults.string(forKey: UserDefaultsKeys.keyboardShortcut) ?? UserPreferences.default.keyboardShortcut,
            autoStart: userDefaults.bool(forKey: UserDefaultsKeys.autoStart),
            showNotifications: userDefaults.bool(forKey: UserDefaultsKeys.showNotifications),
            recordingTimeout: userDefaults.double(forKey: UserDefaultsKeys.recordingTimeout) > 0 ?
                userDefaults.double(forKey: UserDefaultsKeys.recordingTimeout) : UserPreferences.default.recordingTimeout,
            confidenceThreshold: userDefaults.float(forKey: UserDefaultsKeys.confidenceThreshold) > 0 ?
                userDefaults.float(forKey: UserDefaultsKeys.confidenceThreshold) : UserPreferences.default.confidenceThreshold,
            enableHapticFeedback: userDefaults.object(forKey: UserDefaultsKeys.enableHapticFeedback) == nil ?
                UserPreferences.default.enableHapticFeedback : userDefaults.bool(forKey: UserDefaultsKeys.enableHapticFeedback),
            preferredVoice: userDefaults.string(forKey: UserDefaultsKeys.preferredVoice)
        )

        // Validate loaded preferences and fallback to defaults if needed
        if validatePreferences(loadedPreferences) {
            return loadedPreferences
        } else {
            // Reset to defaults if loaded preferences are invalid
            savePreferencesToUserDefaults(UserPreferences.default)
            return UserPreferences.default
        }
    }

    func savePreferences(_ preferences: UserPreferences) throws {
        guard validatePreferences(preferences) else {
            throw ValidationError.invalidPreferences("Invalid preference values detected")
        }

        savePreferencesToUserDefaults(preferences)
        preferencesSubject.send(preferences)
    }

    func updatePreferences(_ update: (inout UserPreferences) -> Void) throws {
        var updatedPreferences = preferences
        update(&updatedPreferences)

        guard validatePreferences(updatedPreferences) else {
            throw ValidationError.invalidPreferences("Updated preferences contain invalid values")
        }

        try savePreferences(updatedPreferences)
    }

    func resetToDefaults() throws {
        try savePreferences(UserPreferences.default)
    }

    func validatePreferences(_ preferences: UserPreferences) -> Bool {
        return preferences.isValid
    }

    func exportPreferences(_ preferences: UserPreferences) throws -> Data {
        guard validatePreferences(preferences) else {
            throw ValidationError.invalidPreferences("Cannot export invalid preferences")
        }

        do {
            return try JSONEncoder().encode(preferences)
        } catch {
            throw ValidationError.invalidPreferences("Failed to encode preferences: \(error.localizedDescription)")
        }
    }

    func importPreferences(from data: Data) throws -> UserPreferences {
        do {
            let importedPreferences = try JSONDecoder().decode(UserPreferences.self, from: data)

            guard validatePreferences(importedPreferences) else {
                throw ValidationError.invalidPreferences("Imported preferences contain invalid values")
            }

            try savePreferences(importedPreferences)
            return importedPreferences
        } catch let error as ValidationError {
            throw error
        } catch {
            throw ValidationError.invalidPreferences("Failed to decode preferences: \(error.localizedDescription)")
        }
    }

    // MARK: - Private Methods

    private func loadAndPublishPreferences() {
        let loadedPreferences = loadPreferences()
        preferencesSubject.send(loadedPreferences)
    }

    private func savePreferencesToUserDefaults(_ preferences: UserPreferences) {
        userDefaults.set(preferences.language, forKey: UserDefaultsKeys.language)
        userDefaults.set(preferences.keyboardShortcut, forKey: UserDefaultsKeys.keyboardShortcut)
        userDefaults.set(preferences.autoStart, forKey: UserDefaultsKeys.autoStart)
        userDefaults.set(preferences.showNotifications, forKey: UserDefaultsKeys.showNotifications)
        userDefaults.set(preferences.recordingTimeout, forKey: UserDefaultsKeys.recordingTimeout)
        userDefaults.set(preferences.confidenceThreshold, forKey: UserDefaultsKeys.confidenceThreshold)
        userDefaults.set(preferences.enableHapticFeedback, forKey: UserDefaultsKeys.enableHapticFeedback)

        if let preferredVoice = preferences.preferredVoice {
            userDefaults.set(preferredVoice, forKey: UserDefaultsKeys.preferredVoice)
        } else {
            userDefaults.removeObject(forKey: UserDefaultsKeys.preferredVoice)
        }
    }
}

// MARK: - Convenience Extensions

extension PreferencesService {
    /// Update single preference property
    func update<T>(_ keyPath: WritableKeyPath<UserPreferences, T>, to value: T) throws {
        try updatePreferences { preferences in
            preferences[keyPath: keyPath] = value
        }
    }

    /// Get preference value for key path
    func getValue<T>(_ keyPath: KeyPath<UserPreferences, T>) -> T {
        return preferences[keyPath: keyPath]
    }
}

// MARK: - Migration Support

extension PreferencesManager {
    /// Migrate preferences from older versions
    func migratePreferences(from version: String) {
        switch version {
        case "1.0":
            // Example migration logic
            var currentPreferences = preferences
            if currentPreferences.recordingTimeout == 0 {
                currentPreferences.recordingTimeout = UserPreferences.default.recordingTimeout
                try? savePreferences(currentPreferences)
            }
        default:
            break
        }
    }

    /// Check if this is the first launch
    var isFirstLaunch: Bool {
        return !userDefaults.bool(forKey: UserDefaultsKeys.firstLaunch)
    }

    /// Mark first launch as completed
    func completeFirstLaunch() {
        userDefaults.set(true, forKey: UserDefaultsKeys.firstLaunch)
    }

    /// Get and update last version used
    var lastVersion: String? {
        get { return userDefaults.string(forKey: UserDefaultsKeys.lastVersion) }
        set { userDefaults.set(newValue, forKey: UserDefaultsKeys.lastVersion) }
    }
}