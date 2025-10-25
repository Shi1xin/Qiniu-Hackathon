import Foundation
import AppKit
import UserNotifications

// MARK: - NotificationType

/// Types of notifications that can be shown by the app.
enum NotificationType: String, CaseIterable {
    case success = "success"
    case error = "error"
    case warning = "warning"
    case info = "info"
    case recordingStarted = "recording_started"
    case recordingStopped = "recording_stopped"
    case processing = "processing"
    case commandExecuted = "command_executed"

    var defaultTitle: String {
        switch self {
        case .success:
            return "Success"
        case .error:
            return "Error"
        case .warning:
            return "Warning"
        case .info:
            return "Information"
        case .recordingStarted:
            return "Recording Started"
        case .recordingStopped:
            return "Recording Stopped"
        case .processing:
            return "Processing"
        case .commandExecuted:
            return "Command Executed"
        }
    }

    var systemSound: NSSound.Name? {
        switch self {
        case .success:
            return .funk
        case .error:
            return .basso
        case .warning:
            return .purr
        case .info:
            return .glass
        case .recordingStarted:
            return .pop
        case .recordingStopped:
            return .blow
        case .processing:
            return .morse
        case .commandExecuted:
            return .hero
        }
    }
}

// MARK: - NotificationContent

/// Structure representing notification content.
struct NotificationContent {
    let title: String
    let subtitle: String?
    let informativeText: String?
    let type: NotificationType
    let userInfo: [String: Any]?
    let hasActionButton: Bool
    let actionButtonTitle: String?

    init(
        title: String,
        subtitle: String? = nil,
        informativeText: String? = nil,
        type: NotificationType = .info,
        userInfo: [String: Any]? = nil,
        hasActionButton: Bool = false,
        actionButtonTitle: String? = nil
    ) {
        self.title = title
        self.subtitle = subtitle
        self.informativeText = informativeText
        self.type = type
        self.userInfo = userInfo
        self.hasActionButton = hasActionButton
        self.actionButtonTitle = actionButtonTitle
    }
}

// MARK: - NotificationService Protocol

/// Protocol for managing system notifications.
protocol NotificationService: AnyObject {
    /// Request notification permissions
    func requestNotificationPermission() async -> Bool

    /// Show a notification with content
    /// - Parameter content: Notification content to display
    func showNotification(_ content: NotificationContent) async

    /// Show a simple success notification
    /// - Parameters:
    ///   - title: Notification title
    ///   - message: Optional informative message
    func showSuccess(title: String, message: String?) async

    /// Show an error notification
    /// - Parameters:
    ///   - title: Notification title
    ///   - error: Error to display
    func showError(title: String, error: Error) async

    /// Show a warning notification
    /// - Parameters:
    ///   - title: Notification title
    ///   - message: Warning message
    func showWarning(title: String, message: String?) async

    /// Show an info notification
    /// - Parameters:
    ///   - title: Notification title
    ///   - message: Info message
    func showInfo(title: String, message: String?) async

    /// Clear all pending notifications
    func clearAllNotifications() async

    /// Check if notifications are enabled
    var notificationsEnabled: Bool { get }
}

// MARK: - NotificationManager

/// Concrete implementation of NotificationService using UserNotifications framework.
@MainActor
class NotificationManager: NSObject, NotificationService {
    // MARK: - Properties

    private let notificationCenter = UNUserNotificationCenter.current()
    private var notificationsEnabled: Bool = false

    var notificationsEnabled: Bool {
        return notificationsEnabled
    }

    // MARK: - Initialization

    override init() {
        super.init()
        setupNotificationCenter()
    }

    // MARK: - NotificationService Implementation

    func requestNotificationPermission() async -> Bool {
        do {
            let granted = try await notificationCenter.requestAuthorization(options: [.alert, .sound, .badge])
            notificationsEnabled = granted
            return granted
        } catch {
            print("Failed to request notification permission: \(error)")
            notificationsEnabled = false
            return false
        }
    }

    func showNotification(_ content: NotificationContent) async {
        guard notificationsEnabled else {
            print("Notifications are disabled, skipping notification: \(content.title)")
            return
        }

        // Create the content for the notification
        let unContent = UNMutableNotificationContent()
        unContent.title = content.title
        unContent.subtitle = content.subtitle ?? ""
        unContent.body = content.informativeText ?? ""
        unContent.userInfo = content.userInfo ?? [:]
        unContent.sound = .default

        // Set category based on notification type
        unContent.categoryIdentifier = content.type.rawValue

        // Create trigger (immediate)
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)

        // Create request
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: unContent,
            trigger: trigger
        )

        do {
            try await notificationCenter.add(request)
            playNotificationSound(for: content.type)
        } catch {
            print("Failed to show notification: \(error)")
            // Fallback to NSUserNotification if UNUserNotification fails
            showFallbackNotification(content)
        }
    }

    func showSuccess(title: String, message: String? = nil) async {
        await showNotification(NotificationContent(
            title: title,
            subtitle: nil,
            informativeText: message,
            type: .success
        ))
    }

    func showError(title: String, error: Error) async {
        await showNotification(NotificationContent(
            title: title,
            subtitle: nil,
            informativeText: error.localizedDescription,
            type: .error,
            userInfo: ["error": String(describing: error)]
        ))
    }

    func showWarning(title: String, message: String?) async {
        await showNotification(NotificationContent(
            title: title,
            subtitle: nil,
            informativeText: message,
            type: .warning
        ))
    }

    func showInfo(title: String, message: String?) async {
        await showNotification(NotificationContent(
            title: title,
            subtitle: nil,
            informativeText: message,
            type: .info
        ))
    }

    func clearAllNotifications() async {
        notificationCenter.removeAllPendingNotificationRequests()
        notificationCenter.removeAllDeliveredNotifications()
    }

    // MARK: - Private Methods

    private func setupNotificationCenter() {
        notificationCenter.delegate = self
        Task {
            await checkNotificationPermissions()
        }
    }

    private func checkNotificationPermissions() async {
        let settings = await notificationCenter.notificationSettings()
        notificationsEnabled = settings.authorizationStatus == .authorized
    }

    private func playNotificationSound(for type: NotificationType) {
        guard let soundName = type.systemSound else { return }

        let sound = NSSound(named: soundName)
        sound?.play()
    }

    private func showFallbackNotification(_ content: NotificationContent) {
        let notification = NSUserNotification()
        notification.title = content.title
        notification.subtitle = content.subtitle
        notification.informativeText = content.informativeText
        notification.identifier = UUID().uuidString

        if let userInfo = content.userInfo {
            notification.userInfo = userInfo
        }

        if content.hasActionButton {
            notification.hasActionButton = true
            notification.actionButtonTitle = content.actionButtonTitle ?? "View"
        }

        NSUserNotificationCenter.default.deliver(notification)
        playNotificationSound(for: content.type)
    }

    // MARK: - Predefined Notifications

    /// Show recording started notification
    func showRecordingStarted() async {
        await showNotification(NotificationContent(
            title: "Recording Started",
            subtitle: "Voice input is active",
            type: .recordingStarted
        ))
    }

    /// Show recording stopped notification
    func showRecordingStopped(duration: TimeInterval) async {
        let formattedDuration = formatDuration(duration)
        await showNotification(NotificationContent(
            title: "Recording Stopped",
            subtitle: "Duration: \(formattedDuration)",
            type: .recordingStopped
        ))
    }

    /// Show processing notification
    func showProcessing(text: String = "Transcribing audio...") async {
        await showNotification(NotificationContent(
            title: "Processing",
            subtitle: text,
            type: .processing
        ))
    }

    /// Show command executed notification
    func showCommandExecuted(command: String) async {
        await showNotification(NotificationContent(
            title: "Command Executed",
            subtitle: command,
            type: .commandExecuted
        ))
    }

    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationManager: UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Show notifications even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        // Handle notification interactions
        let userInfo = response.notification.request.content.userInfo
        handleNotificationAction(response.actionIdentifier, userInfo: userInfo)
        completionHandler()
    }

    private func handleNotificationAction(_ actionIdentifier: String, userInfo: [String: Any]) {
        switch actionIdentifier {
        case UNNotificationDefaultActionIdentifier:
            // User tapped on the notification
            NotificationCenter.default.post(
                name: .notificationTapped,
                object: nil,
                userInfo: userInfo
            )
        case UNNotificationDismissActionIdentifier:
            // User dismissed the notification
            break
        default:
            // Custom action button tapped
            NotificationCenter.default.post(
                name: .notificationActionTapped,
                object: nil,
                userInfo: ["action": actionIdentifier, "userInfo": userInfo]
            )
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let notificationTapped = Notification.Name("notificationTapped")
    static let notificationActionTapped = Notification.Name("notificationActionTapped")
}

// MARK: - Convenience Methods

extension NotificationService {
    /// Show notification with error handling
    func showNotificationSafe(_ content: NotificationContent) async {
        do {
            await showNotification(content)
        } catch {
            print("Failed to show notification: \(error)")
        }
    }

    /// Batch show multiple notifications
    func showNotifications(_ contents: [NotificationContent]) async {
        for content in contents {
            await showNotification(content)
            // Add small delay between notifications
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        }
    }
}