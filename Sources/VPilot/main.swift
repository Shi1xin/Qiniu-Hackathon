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
    private var isSpeechEnabled = true
    private var plannerEnabled = false
    private var browserControlMode: BrowserControlMode = .mixed
    private enum BrowserControlMode: String, CaseIterable {
        case mixed = "mixed"
        case browserUseOnly = "browser-use-only"
        case guiAgentOnly = "gui-agent-only"

        var localizedName: String {
            switch self {
            case .mixed: return "混合"
            case .browserUseOnly: return "仅Browser Use"
            case .guiAgentOnly: return "仅GUI Agent"
            }
        }

        var parentMenuTitle: String {
            "浏览器控制：\(localizedName)"
        }
    }
    private lazy var speechToggleMenuItem: NSMenuItem = {
        let item = NSMenuItem(title: "语音播报", action: #selector(toggleSpeechOutput(_:)), keyEquivalent: "")
        item.target = self
        item.state = .on
        return item
    }()
    private lazy var browserModeMenuItem: NSMenuItem = {
        let parent = NSMenuItem(title: browserControlMode.parentMenuTitle, action: nil, keyEquivalent: "")
        let submenu = NSMenu()
        BrowserControlMode.allCases.forEach { mode in
            let item = NSMenuItem(title: mode.localizedName, action: #selector(selectBrowserMode(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = mode.rawValue
            item.state = mode == browserControlMode ? .on : .off
            submenu.addItem(item)
        }
        parent.submenu = submenu
        return parent
    }()
    private lazy var plannerToggleMenuItem: NSMenuItem = {
        let item = NSMenuItem(title: "启用任务规划", action: #selector(togglePlanner(_:)), keyEquivalent: "")
        item.target = self
        item.state = .off
        return item
    }()
    private lazy var statusMenu: NSMenu = {
        let menu = NSMenu()
        menu.addItem(speechToggleMenuItem)
        menu.addItem(browserModeMenuItem)
        menu.addItem(plannerToggleMenuItem)
        menu.addItem(NSMenuItem.separator())
        let quitItem = NSMenuItem(title: "退出", action: #selector(quitApplication), keyEquivalent: "")
        quitItem.target = self
        menu.addItem(quitItem)
        return menu
    }()

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
            // 加载菜单栏图标
            let image = loadMenuBarIcon()
            button.image = image
            button.action = #selector(statusBarClicked)
            button.target = self
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
    }

    private func loadMenuBarIcon() -> NSImage {
        // 尝试从Resources目录加载SVG图标
        if let resourcePath = Bundle.main.resourcePath {
            let svgPath = (resourcePath as NSString).appendingPathComponent("MICROPHONE-mono.svg")
            if let svgImage = NSImage(contentsOfFile: svgPath) {
                svgImage.isTemplate = true // 使图标适应系统主题
                svgImage.size = NSSize(width: 18, height: 18)
                return svgImage
            }
        }
        
        // 如果加载失败，回退到绘制简单图标
        return createFallbackIcon()
    }

    private func createFallbackIcon() -> NSImage {
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
        guard let event = NSApp.currentEvent else { return }

        let isContextClick = event.type == .rightMouseUp ||
            (event.type == .leftMouseUp && event.modifierFlags.contains(.control))

        if isContextClick {
            guard let button = statusItem.button else { return }
            updateStatusMenuItems()
            NSMenu.popUpContextMenu(statusMenu, with: event, for: button)
            return
        }

        voiceInputWindow.showWindow(at: statusItem)

        if isRecording {
            voiceInputWindow.setRecordingState(true)
            voiceInputWindow.updateStatus("正在录音...")
            voiceInputWindow.setRecordButtonEnabled(true)
        }
    }

    @objc private func quitApplication() {
        NSApp.terminate(nil)
    }

    private func updateStatusMenuItems() {
        speechToggleMenuItem.state = isSpeechEnabled ? .on : .off
        plannerToggleMenuItem.state = plannerEnabled ? .on : .off
        browserModeMenuItem.title = browserControlMode.parentMenuTitle
        if let submenu = browserModeMenuItem.submenu {
            for item in submenu.items {
                guard let raw = item.representedObject as? String,
                      let mode = BrowserControlMode(rawValue: raw) else { continue }
                item.state = mode == browserControlMode ? .on : .off
            }
        }
    }

    @objc private func toggleSpeechOutput(_ sender: NSMenuItem) {
        isSpeechEnabled.toggle()
        updateStatusMenuItems()

        if !isSpeechEnabled, speechSynthesizer.isSpeaking {
            speechSynthesizer.stopSpeaking(at: .immediate)
        }
    }

    @objc private func togglePlanner(_ sender: NSMenuItem) {
        plannerEnabled.toggle()
        updateStatusMenuItems()
    }

    @objc private func selectBrowserMode(_ sender: NSMenuItem) {
        guard let raw = sender.representedObject as? String,
              let mode = BrowserControlMode(rawValue: raw) else { return }
        browserControlMode = mode
        updateStatusMenuItems()
    }
}

// MARK: - VoiceRecognizerDelegate
extension VPilotApp: VoiceRecognizerDelegate {
    func voiceRecognizer(_ recognizer: VoiceRecognizer, didReceiveText text: String) {
        print("识别到的文本: \(text)")

        DispatchQueue.main.async { [weak self] in
            self?.voiceInputWindow.setRecordingState(false)
            self?.voiceInputWindow.setRecordButtonEnabled(true)
            self?.voiceInputWindow.updateStatus("识别完成，正在执行命令...")
        }

        // 执行命令
        executeCommand(with: text)
    }

    func voiceRecognizer(_ recognizer: VoiceRecognizer, didFailWithError error: Error) {
        print("语音识别失败: \(error)")

        DispatchQueue.main.async { [weak self] in
            self?.voiceInputWindow.setRecordingState(false)
            self?.voiceInputWindow.setRecordButtonEnabled(true)
            self?.voiceInputWindow.updateStatus("识别失败，请重试")
        }

        // 显示错误提示
        showErrorMessage("语音识别失败: \(error.localizedDescription)")
    }

    func voiceRecognizerDidStartRecording(_ recognizer: VoiceRecognizer) {
        print("开始录音")
        isRecording = true
        voiceInputWindow.setRecordingState(true)
        voiceInputWindow.setRecordButtonEnabled(true)
        voiceInputWindow.updateStatus("正在录音...")
        voiceInputWindow.resetLLMResponses()
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
        var arguments = ["run", "--input", trimmedInput, "--debug", "--stream", "--open"]

        if plannerEnabled {
            arguments.append("--planner.enabled")
        }

        arguments.append(contentsOf: ["--browser.control", browserControlMode.rawValue])

        process.arguments = arguments

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        let handle = pipe.fileHandleForReading
        var outputBuffer = ""
        var streamedResponses: [String] = []

        DispatchQueue.main.async { [weak self] in
            self?.voiceInputWindow.displayLLMResponses([])
        }

        handle.readabilityHandler = { [weak self] fileHandle in
            let data = fileHandle.availableData
            if data.isEmpty {
                fileHandle.readabilityHandler = nil
                return
            }

            let chunk = String(decoding: data, as: UTF8.self)
            outputBuffer += chunk
            print(chunk)

            guard let self = self else { return }
            let responses = self.extractLLMFinalResponses(from: outputBuffer)
            if responses != streamedResponses {
                streamedResponses = responses
                DispatchQueue.main.async {
                    self.voiceInputWindow.displayLLMResponses(responses)
                }
            }
        }

        process.terminationHandler = { [weak self] _ in
            handle.readabilityHandler = nil
            guard let self = self else { return }

            let finalResponses = self.extractLLMFinalResponses(from: outputBuffer)
            streamedResponses = finalResponses
            let notificationMessage: String

            if let last = finalResponses.last, !last.isEmpty {
                notificationMessage = last
            } else {
                let trimmed = outputBuffer.trimmingCharacters(in: .whitespacesAndNewlines)
                notificationMessage = trimmed.isEmpty ? "命令执行完成" : String(trimmed.prefix(200))
            }

            print("命令输出: \(outputBuffer)")

            DispatchQueue.main.async {
                self.voiceInputWindow.displayLLMResponses(finalResponses)
                self.voiceInputWindow.setRecordButtonEnabled(true)
                self.voiceInputWindow.updateStatus("执行完成，随时可以继续录音")
            }

            self.showNotification("命令执行完成", message: notificationMessage)
            self.speakResult(notificationMessage)
        }

        do {
            try process.run()
        } catch {
            handle.readabilityHandler = nil
            print("执行命令失败: \(error)")
            DispatchQueue.main.async { [weak self] in
                self?.voiceInputWindow.setRecordButtonEnabled(true)
                self?.voiceInputWindow.setRecordingState(false)
                self?.voiceInputWindow.updateStatus("执行失败，请重试")
            }
            showErrorMessage("执行命令失败: \(error.localizedDescription)")
        }
    }

    private func speakResult(_ message: String) {
        guard isSpeechEnabled else { return }

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

            let utterance: AVSpeechUtterance = AVSpeechUtterance(string: normalizedMessage)
            utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
            utterance.rate = AVSpeechUtteranceDefaultSpeechRate + 0.1
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

    private func extractLLMFinalResponses(from output: String) -> [String] {
        var results: [String] = []
        var searchStart = output.startIndex

        while let range = output.range(of: "LLMProcessor Finalized Response", range: searchStart..<output.endIndex) {
            var cursor = range.upperBound

            while cursor < output.endIndex, output[cursor].isWhitespace {
                cursor = output.index(after: cursor)
            }

            guard cursor < output.endIndex, output[cursor] == "{" else {
                searchStart = cursor
                continue
            }

            var braceDepth = 0
            var end = cursor
            while end < output.endIndex {
                let char = output[end]
                if char == "{" {
                    braceDepth += 1
                } else if char == "}" {
                    braceDepth -= 1
                    if braceDepth == 0 {
                        end = output.index(after: end)
                        break
                    }
                }
                end = output.index(after: end)
            }

            guard braceDepth == 0 else {
                searchStart = end
                continue
            }

            let jsonString = String(output[cursor..<end])
            if let content = parseContent(from: jsonString) {
                results.append(content)
            }

            searchStart = end
        }

        return results
    }

    private func parseContent(from jsonString: String) -> String? {
        guard let data = jsonString.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] else {
            return nil
        }

        guard let content = object["content"] as? String else {
            return nil
        }

        let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}

// MARK: - Main Entry Point
let app = NSApplication.shared
let delegate = VPilotApp()
app.delegate = delegate
app.run()