import Cocoa

protocol VoiceInputWindowDelegate: AnyObject {
    func voiceInputWindowDidRequestStartRecording(_ window: VoiceInputWindow)
    func voiceInputWindowDidRequestStopRecording(_ window: VoiceInputWindow)
}

class VoiceInputWindow: NSObject {
    weak var delegate: VoiceInputWindowDelegate?

    private var window: NSWindow!
    private var titleLabel: NSTextField!
    private var statusLabel: NSTextField!
    private var recordButton: NSButton!
    private var backgroundView: NSVisualEffectView!
    private var responseScrollView: NSScrollView!
    private var responseTextView: NSTextView!
    private var outsideEventMonitor: Any?
    private var isRecording = false
    private var llmResponseTexts: [String] = []

    override init() {
        super.init()
        setupWindow()
    }

    private func setupWindow() {
        let windowRect = NSRect(x: 0, y: 0, width: 320, height: 260)
        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )

        window.title = "语音输入"
        window.level = .popUpMenu
        window.isOpaque = false
        window.backgroundColor = NSColor.clear
        window.hasShadow = true
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window.ignoresMouseEvents = false

        setupContentView()
    }

    private func setupContentView() {
        backgroundView = NSVisualEffectView()
        backgroundView.material = .menu
        backgroundView.state = .active
        backgroundView.blendingMode = .withinWindow
        backgroundView.wantsLayer = true
        backgroundView.layer?.cornerRadius = 16
        backgroundView.layer?.masksToBounds = true

        // 标题标签
        titleLabel = NSTextField(labelWithString: "VPilot")
        titleLabel.font = NSFont.boldSystemFont(ofSize: 18)
        titleLabel.textColor = NSColor.labelColor
        titleLabel.alignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false

        // 状态标签
        statusLabel = NSTextField(labelWithString: "点击下方按钮开始录音")
        statusLabel.font = NSFont.systemFont(ofSize: 14)
        statusLabel.textColor = NSColor.secondaryLabelColor
        statusLabel.alignment = .center
        statusLabel.translatesAutoresizingMaskIntoConstraints = false

        // 录音按钮
        recordButton = NSButton(title: "开始录音", target: self, action: #selector(recordButtonClicked))
        recordButton.bezelStyle = .regularSquare
        recordButton.isBordered = false
        recordButton.wantsLayer = true
        recordButton.layer?.cornerRadius = 18
        recordButton.layer?.backgroundColor = NSColor.controlAccentColor.withAlphaComponent(0.18).cgColor
        recordButton.contentTintColor = NSColor.controlAccentColor
        recordButton.translatesAutoresizingMaskIntoConstraints = false

        // LLM响应滚动区域
        responseTextView = NSTextView(frame: .zero)
        responseTextView.isEditable = false
        responseTextView.isSelectable = true
        responseTextView.drawsBackground = false
        responseTextView.textContainerInset = NSSize(width: 4, height: 8)
        responseTextView.font = NSFont.systemFont(ofSize: 13)

        responseScrollView = NSScrollView()
        responseScrollView.hasVerticalScroller = true
        responseScrollView.hasHorizontalScroller = false
        responseScrollView.borderType = .noBorder
        responseScrollView.drawsBackground = false
        responseScrollView.documentView = responseTextView
        responseScrollView.translatesAutoresizingMaskIntoConstraints = false

        window.contentView = backgroundView

        backgroundView.addSubview(titleLabel)
        backgroundView.addSubview(statusLabel)
        backgroundView.addSubview(recordButton)
        backgroundView.addSubview(responseScrollView)

        NSLayoutConstraint.activate([
            titleLabel.topAnchor.constraint(equalTo: backgroundView.topAnchor, constant: 20),
            titleLabel.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 20),
            titleLabel.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -20),

            statusLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 14),
            statusLabel.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 20),
            statusLabel.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -20),

            recordButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 22),
            recordButton.centerXAnchor.constraint(equalTo: backgroundView.centerXAnchor),
            recordButton.heightAnchor.constraint(equalToConstant: 38),
            recordButton.widthAnchor.constraint(equalToConstant: 150),

            responseScrollView.topAnchor.constraint(equalTo: recordButton.bottomAnchor, constant: 18),
            responseScrollView.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 18),
            responseScrollView.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -18),
            responseScrollView.bottomAnchor.constraint(equalTo: backgroundView.bottomAnchor, constant: -16)
        ])

        renderLLMResponses()
    }

    func showWindow(at statusItem: NSStatusItem) {
        updateStatus("点击下方按钮开始录音")
        setRecordingState(false)
        setRecordButtonEnabled(true)
        renderLLMResponses()

        // 计算窗口位置，显示在状态栏图标附近
        if let button = statusItem.button, let screen = NSScreen.main {
            let buttonFrame = button.window?.frame ?? button.frame
            let windowSize = window.frame.size

            // 计算窗口应该显示的位置
            var x = buttonFrame.maxX - windowSize.width
            var y = buttonFrame.minY - windowSize.height - 5

            // 确保窗口不超出屏幕边界
            let screenFrame = screen.visibleFrame
            if x < screenFrame.minX {
                x = screenFrame.minX + 10
            }
            if x + windowSize.width > screenFrame.maxX {
                x = screenFrame.maxX - windowSize.width - 10
            }
            if y < screenFrame.minY {
                y = buttonFrame.maxY + 5
            }

            window.setFrameOrigin(NSPoint(x: x, y: y))
        }

        window.makeKeyAndOrderFront(nil)
        window.alphaValue = 1.0

        // 添加全局点击监听器，点击窗口外部时关闭窗口
        if let monitor = outsideEventMonitor {
            NSEvent.removeMonitor(monitor)
        }
        outsideEventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .leftMouseDown) { [weak self] _ in
            DispatchQueue.main.async {
                guard let self = self else { return }
                if self.isRecording {
                    return
                }
                self.hideWindow()
            }
        }
    }

    func hideWindow() {
        if let monitor = outsideEventMonitor {
            NSEvent.removeMonitor(monitor)
            outsideEventMonitor = nil
        }

        window.orderOut(nil)
        setRecordingState(false)
        setRecordButtonEnabled(true)
    }

    func updateStatus(_ status: String) {
        statusLabel.stringValue = status
        let isActiveRecording = status.contains("正在录音")
        statusLabel.textColor = isActiveRecording ? NSColor.systemRed : NSColor.secondaryLabelColor
    }

    @objc private func recordButtonClicked() {
        recordButton.isEnabled = false
        if isRecording {
            delegate?.voiceInputWindowDidRequestStopRecording(self)
        } else {
            delegate?.voiceInputWindowDidRequestStartRecording(self)
        }
    }

    func setRecordingState(_ recording: Bool) {
        isRecording = recording
        recordButton.title = recording ? "停止录音" : "开始录音"
        let accent = NSColor.controlAccentColor
        recordButton.contentTintColor = recording ? NSColor.systemRed : accent
        recordButton.layer?.backgroundColor = recording ? NSColor.systemRed.withAlphaComponent(0.18).cgColor : accent.withAlphaComponent(0.18).cgColor
    }

    func setRecordButtonEnabled(_ enabled: Bool) {
        recordButton.isEnabled = enabled
        recordButton.alphaValue = enabled ? 1.0 : 0.6
    }

    func resetLLMResponses() {
        llmResponseTexts.removeAll()
        renderLLMResponses()
    }

    func displayLLMResponses(_ responses: [String]) {
        llmResponseTexts = responses
        renderLLMResponses()
    }

    private func renderLLMResponses() {
        guard responseTextView != nil else { return }

        if llmResponseTexts.isEmpty {
            responseTextView.string = "暂无LLM响应。"
        } else {
            let formatted = llmResponseTexts.enumerated().map { index, content in
                guard llmResponseTexts.count > 1 else { return content }
                return "\(index + 1). \(content)"
            }.joined(separator: "\n\n")
            responseTextView.string = formatted
        }

        responseTextView.scrollToEndOfDocument(nil)
    }
}