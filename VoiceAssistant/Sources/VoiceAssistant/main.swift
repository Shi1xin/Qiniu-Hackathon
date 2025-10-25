import AppKit

/// Main entry point for the Voice Assistant application.
/// This is a menubar application that runs as a background process.
@main
struct VoiceAssistantMain {
    static func main() {
        // Create and run the NSApplication
        let app = NSApplication.shared
        let delegate = AppDelegate()
        app.delegate = delegate

        // Set activation policy to accessory (no dock icon)
        app.setActivationPolicy(.accessory)

        // Run the application
        app.run()
    }
}

/// Application delegate that handles application lifecycle events.
class AppDelegate: NSObject, NSApplicationDelegate {
    private var voiceAssistantApp: VoiceAssistantApp?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Initialize the main voice assistant application
        voiceAssistantApp = VoiceAssistantApp()
        voiceAssistantApp?.start()
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        // Clean up before terminating
        voiceAssistantApp?.stop()
        return .terminateNow
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Final cleanup
        voiceAssistantApp = nil
    }
}