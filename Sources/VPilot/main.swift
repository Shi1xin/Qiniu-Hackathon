import Cocoa
import Speech
import AVFoundation
import UserNotifications

class VPilotApp: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var voiceRecognizer: VoiceRecognizer!
    private var voiceInputWindow: VoiceInputWindow!
    private var isRecording = false
    private let speechSynthesizer = AVSpeechSynthesizer()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // 设置应用为后台应用，不显示在Dock中
        NSApp.setActivationPolicy(.accessory)

        // 创建状态栏项目
        setupStatusBarItem()

        // 初始化语音识别器
        voiceRecognizer = VoiceRecognizer()
        voiceRecognizer.delegate = self

        // 初始化语音输入窗口
        voiceInputWindow = VoiceInputWindow()
        voiceInputWindow.delegate = self
    }

    private func setupStatusBarItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)

        if let button = statusItem.button {
            // 创建一个简单的图标
            let image = createMicrophoneIcon()
            button.image = image
            button.action = #selector(statusBarClicked)
            button.target = self
        }
    }

    private func createMicrophoneIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)

        image.lockFocus()

        // 绘制简单的麦克风图标
        let path = NSBezierPath()

        // 麦克风主体
        path.move(to: NSPoint(x: size.width * 0.4, y: size.height * 0.2))
        path.line(to: NSPoint(x: size.width * 0.4, y: size.height * 0.6))
        path.curve(to: NSPoint(x: size.width * 0.6, y: size.height * 0.6),
                  controlPoint1: NSPoint(x: size.width * 0.4, y: size.height * 0.7),
                  controlPoint2: NSPoint(x: size.width * 0.6, y: size.height * 0.7))
        path.line(to: NSPoint(x: size.width * 0.6, y: size.height * 0.2))
        path.curve(to: NSPoint(x: size.width * 0.4, y: size.height * 0.2),
                  controlPoint1: NSPoint(x: size.width * 0.6, y: size.height * 0.1),
                  controlPoint2: NSPoint(x: size.width * 0.4, y: size.height * 0.1))

        NSColor.systemGray.setFill()
        path.fill()

        // 麦克风支架
        let standPath = NSBezierPath()
        standPath.move(to: NSPoint(x: size.width * 0.35, y: size.height * 0.75))
        standPath.line(to: NSPoint(x: size.width * 0.65, y: size.height * 0.75))
        standPath.line(to: NSPoint(x: size.width * 0.6, y: size.height * 0.85))
        standPath.line(to: NSPoint(x: size.width * 0.4, y: size.height * 0.85))
        standPath.close()

        NSColor.systemGray.setFill()
        standPath.fill()

        image.unlockFocus()

        return image
    }

    @objc private func statusBarClicked() {
        voiceInputWindow.showWindow(at: statusItem)

        if isRecording {
            voiceInputWindow.setRecordingState(true)
            voiceInputWindow.updateStatus("正在录音...")
            voiceInputWindow.setRecordButtonEnabled(true)
        }
    }
}

// MARK: - VoiceRecognizerDelegate
extension VPilotApp: VoiceRecognizerDelegate {
    func voiceRecognizer(_ recognizer: VoiceRecognizer, didReceiveText text: String) {
        print("识别到的文本: \(text)")

        // 隐藏提示窗口
        voiceInputWindow.hideWindow()

        // 执行命令
        executeCommand(with: text)
    }

    func voiceRecognizer(_ recognizer: VoiceRecognizer, didFailWithError error: Error) {
        print("语音识别失败: \(error)")

        // 隐藏提示窗口
        voiceInputWindow.hideWindow()

        // 显示错误提示
        showErrorMessage("语音识别失败: \(error.localizedDescription)")
    }

    func voiceRecognizerDidStartRecording(_ recognizer: VoiceRecognizer) {
        print("开始录音")
        isRecording = true
        voiceInputWindow.setRecordingState(true)
        voiceInputWindow.setRecordButtonEnabled(true)
        voiceInputWindow.updateStatus("正在录音...")
    }

    func voiceRecognizerDidStopRecording(_ recognizer: VoiceRecognizer) {
        print("停止录音")
        isRecording = false
        voiceInputWindow.setRecordingState(false)
        voiceInputWindow.setRecordButtonEnabled(false)
        voiceInputWindow.updateStatus("正在识别...")
    }

    private func executeCommand(with input: String) {
        let trimmedInput = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedInput.isEmpty else {
            print("识别结果为空，跳过命令执行。")
            showErrorMessage("没有识别到有效的指令，请再试一次。")
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/homebrew/bin/agent-tars")
        process.arguments = ["run", "--input", trimmedInput]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: data, encoding: .utf8) {
                print("命令输出: \(output)")
                // 可以选择显示结果通知
                showNotification("命令执行完成", message: output)
                speakResult(output)
            }
        } catch {
            print("执行命令失败: \(error)")
            showErrorMessage("执行命令失败: \(error.localizedDescription)")
        }
    }

    private func speakResult(_ message: String) {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        // 标准化语音输出，避免朗读多余的空白字符。
        let normalizedTokens = trimmed
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }
        guard !normalizedTokens.isEmpty else { return }

        var normalizedMessage = normalizedTokens.joined(separator: " ")
        let maxLength = 200
        if normalizedMessage.count > maxLength {
            let prefix = normalizedMessage.prefix(maxLength)
            normalizedMessage = String(prefix) + "，更多内容请查看通知。"
        }

        DispatchQueue.main.async { [weak self] in
            guard let self else { return }

            if self.speechSynthesizer.isSpeaking {
                self.speechSynthesizer.stopSpeaking(at: .immediate)
            }

            let utterance = AVSpeechUtterance(string: normalizedMessage)
            utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
            utterance.rate = AVSpeechUtteranceDefaultSpeechRate
            self.speechSynthesizer.speak(utterance)
        }
    }

    private func showNotification(_ title: String, message: String) {
        let center = UNUserNotificationCenter.current()
        center.requestAuthorization(options: [.alert, .sound]) { granted, error in
            if granted {
                let content = UNMutableNotificationContent()
                content.title = title
                content.body = message
                content.sound = UNNotificationSound.default

                let request = UNNotificationRequest(
                    identifier: UUID().uuidString,
                    content: content,
                    trigger: nil
                )

                center.add(request) { error in
                    if let error = error {
                        print("发送通知失败: \(error)")
                    }
                }
            } else {
                print("通知权限被拒绝")
            }
        }
    }

    private func showErrorMessage(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "错误"
        alert.informativeText = message
        alert.alertStyle = .critical
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
}

// MARK: - VoiceInputWindowDelegate
extension VPilotApp: VoiceInputWindowDelegate {
    func voiceInputWindowDidRequestStartRecording(_ window: VoiceInputWindow) {
        guard !isRecording else {
            voiceInputWindow.setRecordButtonEnabled(true)
            return
        }

        voiceInputWindow.updateStatus("正在准备录音...")
        voiceRecognizer.requestPermissionsAndStartRecording()
    }

    func voiceInputWindowDidRequestStopRecording(_ window: VoiceInputWindow) {
        guard isRecording else {
            voiceInputWindow.setRecordButtonEnabled(true)
            return
        }

        voiceInputWindow.updateStatus("正在停止录音...")
        voiceInputWindow.setRecordButtonEnabled(false)
        voiceRecognizer.stopRecording(dueToCancellation: false)
    }
}

// MARK: - Main Entry Point
let app = NSApplication.shared
let delegate = VPilotApp()
app.delegate = delegate
app.run()