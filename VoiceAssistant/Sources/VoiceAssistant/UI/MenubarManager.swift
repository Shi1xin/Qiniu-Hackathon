import Foundation
import AppKit
import Combine

// MARK: - MenubarInterface Protocol

/// Protocol for menubar management functionality.
protocol MenubarInterface: AnyObject {
    /// Show the menubar item
    func show()

    /// Hide the menubar item
    func hide()

    /// Update menubar icon
    /// - Parameter state: Current recording state
    func updateIcon(for state: VoiceSessionStatus)

    /// Set menubar click handler
    /// - Parameter handler: Closure to execute on click
    func setClickHandler(_ handler: @escaping () -> Void)

    /// Show status tooltip
    /// - Parameter tooltip: Tooltip text to display
    func setTooltip(_ tooltip: String?)

    /// Enable/disable menubar item
    /// - Parameter enabled: Whether to enable the item
    func setEnabled(_ enabled: Bool)
}

// MARK: - MenubarManager

/// Manages the application's menubar item with microphone icon.
@MainActor
class MenubarManager: NSObject, MenubarInterface {
    // MARK: - Properties

    private var statusItem: NSStatusItem?
    private var clickHandler: (() -> Void)?
    private var currentState: VoiceSessionStatus = .pending
    private var cancellables = Set<AnyCancellable>()

    /// Icon images for different states
    private struct Icons {
        static let microphoneNormal = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Microphone")
        static let microphoneRecording = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Recording")
        static let microphoneProcessing = NSImage(systemSymbolName: "waveform", accessibilityDescription: "Processing")
        static let microphoneSuccess = NSImage(systemSymbolName: "checkmark.circle.fill", accessibilityDescription: "Success")
        static let microphoneError = NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: "Error")
        static let microphoneDisabled = NSImage(systemSymbolName: "mic.slash.fill", accessibilityDescription: "Microphone Disabled")
    }

    // MARK: - Initialization

    override init() {
        super.init()
        setupStatusItem()
    }

    deinit {
        statusItem = nil
    }

    // MARK: - MenubarInterface Implementation

    func show() {
        guard statusItem == nil else { return }
        setupStatusItem()
    }

    func hide() {
        statusItem = nil
    }

    func updateIcon(for state: VoiceSessionStatus) {
        currentState = state
        updateAppearance()
        updateTooltip()
    }

    func setClickHandler(_ handler: @escaping () -> Void) {
        self.clickHandler = handler
    }

    func setTooltip(_ tooltip: String?) {
        statusItem?.button?.toolTip = tooltip
    }

    func setEnabled(_ enabled: Bool) {
        statusItem?.button?.isEnabled = enabled
    }

    // MARK: - Private Methods

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)

        guard let statusItem = statusItem, let button = statusItem.button else {
            print("Failed to create status item")
            return
        }

        // Set initial appearance
        updateAppearance()
        updateTooltip()

        // Add click handler
        button.action = #selector(statusItemClicked)
        button.target = self
        button.sendAction(on: [.leftMouseUp, .rightMouseUp])

        // Set up menu for right-click
        setupContextMenu()
    }

    private func updateAppearance() {
        guard let button = statusItem?.button else { return }

        // Get appropriate icon and color for current state
        let (icon, color) = iconAndColor(for: currentState)

        button.image = icon
        button.contentTintColor = color

        // Add pulsing animation for recording state
        if currentState == .recording {
            startPulsingAnimation()
        } else {
            stopPulsingAnimation()
        }
    }

    private func updateTooltip() {
        let tooltip = tooltipText(for: currentState)
        setTooltip(tooltip)
    }

    private func iconAndColor(for state: VoiceSessionStatus) -> (NSImage?, NSColor) {
        switch state {
        case .pending:
            return (Icons.microphoneNormal, .controlTextColor)
        case .recording:
            return (Icons.microphoneRecording, .systemRed)
        case .processing:
            return (Icons.microphoneProcessing, .systemBlue)
        case .completed:
            return (Icons.microphoneSuccess, .systemGreen)
        case .failed:
            return (Icons.microphoneError, .systemRed)
        case .cancelled:
            return (Icons.microphoneDisabled, .controlTextColor)
        }
    }

    private func tooltipText(for state: VoiceSessionStatus) -> String {
        switch state {
        case .pending:
            return "Click to start voice input"
        case .recording:
            return "Recording... Click to stop"
        case .processing:
            return "Processing voice input"
        case .completed:
            return "Voice input completed"
        case .failed:
            return "Voice input failed"
        case .cancelled:
            return "Voice input cancelled"
        }
    }

    private func setupContextMenu() {
        let menu = NSMenu()

        // Add menu items
        let aboutItem = NSMenuItem(
            title: "About Voice Assistant",
            action: #selector(showAbout),
            keyEquivalent: ""
        )
        aboutItem.target = self
        menu.addItem(aboutItem)

        menu.addItem(NSMenuItem.separator())

        let preferencesItem = NSMenuItem(
            title: "Preferences...",
            action: #selector(showPreferences),
            keyEquivalent: ","
        )
        preferencesItem.target = self
        menu.addItem(preferencesItem)

        menu.addItem(NSMenuItem.separator())

        let quitItem = NSMenuItem(
            title: "Quit Voice Assistant",
            action: #selector(quitApplication),
            keyEquivalent: "q"
        )
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem?.menu = menu
    }

    // MARK: - Animations

    private var pulsingTimer: Timer?

    private func startPulsingAnimation() {
        stopPulsingAnimation()

        pulsingTimer = Timer.scheduledTimer(withTimeInterval: 0.8, repeats: true) { [weak self] _ in
            self?.togglePulseState()
        }
    }

    private func stopPulsingAnimation() {
        pulsingTimer?.invalidate()
        pulsingTimer = nil
    }

    private var isPulsed = false

    private func togglePulseState() {
        guard let button = statusItem?.button else { return }

        isPulsed.toggle()
        if isPulsed {
            button.contentTintColor = .systemRed.withAlphaComponent(0.6)
        } else {
            button.contentTintColor = .systemRed
        }
    }

    // MARK: - Actions

    @objc private func statusItemClicked() {
        guard let event = NSApp.currentEvent else { return }

        // Handle right-click to show context menu
        if event.type == .rightMouseUp {
            statusItem?.menu?.popUp(positioning: nil, at: NSEvent.mouseLocation, in: nil)
            return
        }

        // Handle left-click
        clickHandler?()
    }

    @objc private func showAbout() {
        if let mainWindow = NSApp.mainWindow {
            mainWindow.makeKeyAndOrderFront(nil)
        } else {
            let alert = NSAlert()
            alert.messageText = "Voice Assistant"
            alert.informativeText = "A menubar voice assistant for macOS\nVersion 1.0.0"
            alert.alertStyle = .informational
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
    }

    @objc private func showPreferences() {
        // Post notification to show preferences
        NotificationCenter.default.post(name: .showPreferences, object: nil)
    }

    @objc private func quitApplication() {
        NSApp.terminate(nil)
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let showPreferences = Notification.Name("showPreferences")
    static let menubarItemClicked = Notification.Name("menubarItemClicked")
}

// MARK: - Convenience Extensions

extension MenubarManager {
    /// Update menubar based on voice session
    func update(for session: VoiceSession) {
        updateIcon(for: session.status)
    }

    /// Reset menubar to default state
    func resetToDefault() {
        updateIcon(for: .pending)
        setEnabled(true)
    }

    /// Show error state temporarily
    func showErrorState() {
        updateIcon(for: .failed)

        // Reset to pending after 3 seconds
        Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            await MainActor.run {
                if currentState == .failed {
                    updateIcon(for: .pending)
                }
            }
        }
    }

    /// Show success state temporarily
    func showSuccessState() {
        updateIcon(for: .completed)

        // Reset to pending after 2 seconds
        Task {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            await MainActor.run {
                if currentState == .completed {
                    updateIcon(for: .pending)
                }
            }
        }
    }

    /// Bind to voice session publisher
    func bind(to session: VoiceSession) {
        session.$status
            .receive(on: DispatchQueue.main)
            .sink { [weak self] status in
                self?.updateIcon(for: status)
            }
            .store(in: &cancellables)

        session.$audioLevel
            .receive(on: DispatchQueue.main)
            .sink { [weak self] level in
                // Could update menubar appearance based on audio level
                self?.updateAudioLevelDisplay(level)
            }
            .store(in: &cancellables)
    }

    private func updateAudioLevelDisplay(_ level: Float) {
        // Optional: Update menubar appearance based on audio level
        // For example, change opacity or add visual feedback
        guard let button = statusItem?.button else { return }

        if currentState == .recording {
            let alpha = 0.5 + (level * 0.5) // Range from 0.5 to 1.0
            button.contentTintColor = .systemRed.withAlphaComponent(alpha)
        }
    }
}

// MARK: - NSStatusItem Customization

extension NSStatusItem {
    /// Set custom appearance with animation
    func setAppearance(icon: NSImage?, color: NSColor, animated: Bool = true) {
        guard let button = self.button else { return }

        if animated {
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.2
                context.allowsImplicitAnimation = true
                button.image = icon
                button.contentTintColor = color
            }
        } else {
            button.image = icon
            button.contentTintColor = color
        }
    }

    /// Add badge with number
    func setBadge(_ number: Int) {
        guard let button = self.button else { return }

        if number > 0 {
            // Create badge view
            let badge = NSTextField()
            badge.stringValue = "\(number)"
            badge.font = NSFont.systemFont(ofSize: 9, weight: .bold)
            badge.textColor = .white
            badge.backgroundColor = .systemRed
            badge.wantsLayer = true
            badge.layer?.cornerRadius = 7
            badge.alignment = .center
            badge.isBezeled = false
            badge.isEditable = false
            badge.isSelectable = false

            // Position badge
            badge.frame = NSRect(x: 16, y: 16, width: 14, height: 14)

            // Add to button
            if button.subviews.isEmpty {
                button.addSubview(badge)
            } else {
                button.subviews.first?.removeFromSuperview()
                button.addSubview(badge)
            }
        } else {
            // Remove badge
            button.subviews.forEach { $0.removeFromSuperview() }
        }
    }
}