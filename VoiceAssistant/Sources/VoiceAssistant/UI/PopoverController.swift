import Foundation
import AppKit
import Combine

// MARK: - PopoverController Protocol

/// Protocol for popover management functionality.
protocol PopoverControllerProtocol: AnyObject {
    /// Show popover relative to menubar item
    /// - Parameter menubarItem: Menubar item to position popover relative to
    func showPopover(from menubarItem: NSStatusItem)

    /// Hide popover
    func hidePopover()

    /// Toggle popover visibility
    /// - Parameter menubarItem: Menubar item to position popover relative to
    func togglePopover(from menubarItem: NSStatusItem)

    /// Check if popover is visible
    var isVisible: Bool { get }

    /// Set popover content view controller
    /// - Parameter viewController: View controller to display in popover
    func setContentViewController(_ viewController: NSViewController)

    /// Set popover delegate
    /// - Parameter delegate: Popover delegate
    func setDelegate(_ delegate: NSPopoverDelegate)
}

// MARK: - PopoverController

/// Manages NSPopover for voice input interface.
@MainActor
class PopoverController: NSObject, PopoverControllerProtocol {
    // MARK: - Properties

    private let popover = NSPopover()
    private var voiceInputViewController: VoiceInputViewController?
    private var cancellables = Set<AnyCancellable>()

    var isVisible: Bool {
        return popover.isShown
    }

    // MARK: - Initialization

    override init() {
        super.init()
        setupPopover()
        setupVoiceInputViewController()
    }

    // MARK: - PopoverControllerProtocol Implementation

    func showPopover(from menubarItem: NSStatusItem) {
        guard let button = menubarItem.button else {
            print("Cannot show popover: menubar item button not available")
            return
        }

        // Ensure content view controller is set
        if popover.contentViewController == nil {
            popover.contentViewController = voiceInputViewController
        }

        // Calculate popover position
        let popoverRect = calculatePopoverRect(for: button)

        // Show popover
        popover.show(relativeTo: popoverRect, of: button, preferredEdge: .minY)

        // Post notification
        NotificationCenter.default.post(name: .popoverDidShow, object: self)
    }

    func hidePopover() {
        guard popover.isShown else { return }

        popover.performClose(nil)

        // Reset voice input view controller
        voiceInputViewController?.reset()

        // Post notification
        NotificationCenter.default.post(name: .popoverDidHide, object: self)
    }

    func togglePopover(from menubarItem: NSStatusItem) {
        if popover.isShown {
            hidePopover()
        } else {
            showPopover(from: menubarItem)
        }
    }

    func setContentViewController(_ viewController: NSViewController) {
        popover.contentViewController = viewController

        if let voiceInputVC = viewController as? VoiceInputViewController {
            voiceInputViewController = voiceInputVC
        }
    }

    func setDelegate(_ delegate: NSPopoverDelegate) {
        popover.delegate = delegate
    }

    // MARK: - Service Injection

    func injectServices(
        audioRecordingService: AudioRecordingService,
        speechRecognitionService: SpeechRecognitionService,
        notificationService: NotificationService
    ) {
        voiceInputViewController?.setAudioRecordingService(audioRecordingService)
        voiceInputViewController?.setSpeechRecognitionService(speechRecognitionService)
        voiceInputViewController?.setNotificationService(notificationService)
    }

    // MARK: - Private Methods

    private func setupPopover() {
        popover.behavior = .transient
        popover.contentSize = NSSize(width: 320, height: 240)
        popover.animates = true
        popover.delegate = self

        // Configure appearance
        popover.appearance = NSAppearance(named: .aqua)
    }

    private func setupVoiceInputViewController() {
        voiceInputViewController = VoiceInputViewController()
        popover.contentViewController = voiceInputViewController
    }

    private func calculatePopoverRect(for button: NSButton) -> NSRect {
        // Position popover centered above the button
        let buttonFrame = button.bounds
        let popoverWidth: CGFloat = 320
        let popoverHeight: CGFloat = 240

        // Center the popover horizontally relative to the button
        let xOffset = (buttonFrame.width - popoverWidth) / 2

        return NSRect(
            x: xOffset,
            y: buttonFrame.height + 5, // Small gap between button and popover
            width: popoverWidth,
            height: 0 // Height is determined by popover.contentSize
        )
    }

    // MARK: - Convenience Methods

    /// Show popover with automatic menubar item detection
    func showPopover() {
        // Try to find the menubar item (this would typically be injected)
        if let menubarItem = findMenubarItem() {
            showPopover(from: menubarItem)
        } else {
            print("Cannot show popover: menubar item not found")
        }
    }

    /// Find menubar item (implementation depends on app structure)
    private func findMenubarItem() -> NSStatusItem? {
        // This would typically be injected or accessed via the app delegate
        // For now, return nil - this method should be implemented based on your app structure
        return nil
    }

    /// Update popover content size
    func updateContentSize(_ size: NSSize) {
        popover.contentSize = size
    }

    /// Configure popover appearance
    func configureAppearance(
        behavior: NSPopover.Behavior = .transient,
        animates: Bool = true,
        appearance: NSAppearance? = nil
    ) {
        popover.behavior = behavior
        popover.animates = animates
        if let appearance = appearance {
            popover.appearance = appearance
        }
    }
}

// MARK: - NSPopoverDelegate

extension PopoverController: NSPopoverDelegate {
    func popoverWillShow(_ notification: Notification) {
        // Prepare for popover display
        voiceInputViewController?.reset()
    }

    func popoverDidShow(_ notification: Notification) {
        // Post notification for other components
        NotificationCenter.default.post(name: .popoverDidShow, object: self)
    }

    func popoverWillClose(_ notification: Notification) {
        // Prepare for popover close
    }

    func popoverDidClose(_ notification: Notification) {
        // Cleanup after popover close
        voiceInputViewController?.reset()

        // Post notification for other components
        NotificationCenter.default.post(name: .popoverDidHide, object: self)
    }

    func popoverShouldDetach(_ popover: NSPopover) -> Bool {
        // Allow popover to become a window when dragged
        return true
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let popoverDidShow = Notification.Name("popoverDidShow")
    static let popoverDidHide = Notification.Name("popoverDidHide")
    static let popoverWillShow = Notification.Name("popoverWillShow")
    static let popoverWillHide = Notification.Name("popoverWillHide")
}

// MARK: - Popover Animation Helpers

extension PopoverController {
    /// Show popover with custom animation
    func showPopoverWithAnimation(from menubarItem: NSStatusItem, completion: @escaping () -> Void) {
        // Disable default animation
        popover.animates = false

        // Show popover
        showPopover(from: menubarItem)

        // Perform custom animation
        if let contentViewController = popover.contentViewController,
           let contentView = contentViewController.view {

            // Initial state
            contentView.layer?.opacity = 0
            contentView.layer?.transform = CATransform3DMakeScale(0.8, 0.8, 1.0)

            // Animate
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.25
                context.timingFunction = CAMediaTimingFunction(name: .easeOut)
                context.allowsImplicitAnimation = true

                contentView.layer?.opacity = 1.0
                contentView.layer?.transform = CATransform3DIdentity
            } completionHandler: {
                completion()
            }
        } else {
            completion()
        }
    }

    /// Hide popover with custom animation
    func hidePopoverWithAnimation(completion: @escaping () -> Void) {
        guard let contentViewController = popover.contentViewController,
              let contentView = contentViewController.view else {
            hidePopover()
            completion()
            return
        }

        // Animate out
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.2
            context.timingFunction = CAMediaTimingFunction(name: .easeIn)
            context.allowsImplicitAnimation = true

            contentView.layer?.opacity = 0
            contentView.layer?.transform = CATransform3DMakeScale(0.9, 0.9, 1.0)
        } completionHandler: {
            self.hidePopover()
            completion()
        }
    }
}

// MARK: - Popover Sizing Helpers

extension PopoverController {
    /// Auto-size popover based on content
    func autoSizePopover() {
        guard let contentViewController = popover.contentViewController,
              let contentView = contentViewController.view else { return }

        // Calculate preferred size based on content
        let fittingSize = contentView.fittingSize

        // Apply constraints
        let minWidth: CGFloat = 280
        let maxWidth: CGFloat = 400
        let minHeight: CGFloat = 200
        let maxHeight: CGFloat = 500

        let preferredWidth = max(minWidth, min(maxWidth, fittingSize.width))
        let preferredHeight = max(minHeight, min(maxHeight, fittingSize.height))

        updateContentSize(NSSize(width: preferredWidth, height: preferredHeight))
    }

    /// Resize popover with animation
    func resizePopover(to size: NSSize, animated: Bool = true) {
        if animated && popover.isShown {
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.2
                context.timingFunction = CAMediaTimingFunction(name: .easeOut)
                context.allowsImplicitAnimation = true

                self.popover.contentSize = size
            }
        } else {
            popover.contentSize = size
        }
    }
}

// MARK: - Global Keyboard Shortcuts

extension PopoverController {
    /// Set up global keyboard shortcut for showing/hiding popover
    func setupGlobalKeyboardShortcut(key: String, modifiers: NSEvent.ModifierFlags) {
        // Create hot key reference
        let hotKeyRef = UnsafeMutablePointer<EventHotKeyRef?>.allocate(capacity: 1)

        var hotKeyID = EventHotKeyID()
        hotKeyID.signature = OSType(0x56414354) // "VACT"
        hotKeyID.id = 1

        // Register hot key
        let status = RegisterEventHotKey(
            UInt32(key.first?.unicodeScalars.first?.value ?? 0),
            UInt32(modifiers.rawValue),
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            hotKeyRef
        )

        if status == noErr {
            print("Global keyboard shortcut registered successfully")
        } else {
            print("Failed to register global keyboard shortcut: \(status)")
        }

        hotKeyRef.deallocate()
    }
}

// MARK: - Accessibility Support

extension PopoverController {
    /// Configure popover for accessibility
    func configureForAccessibility() {
        popover.contentViewController?.view.setAccessibilityElement(true)
        popover.contentViewController?.view.setAccessibilityRole(.group)
        popover.contentViewController?.view.setAccessibilityLabel("Voice Input")
        popover.contentViewController?.view.setAccessibilityHelp("Use this interface to record and transcribe voice commands")
    }
}