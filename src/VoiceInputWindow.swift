import Cocoa

private final class VoiceInputFloatingWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

enum InputMode: String, CaseIterable {
    case voice
    case text

    var localizedName: String {
        switch self {
        case .voice: return "语音输入"
        case .text: return "文字输入"
        }
    }

    var parentMenuTitle: String {
        "输入方式"
    }
}

protocol VoiceInputWindowDelegate: AnyObject {
    func voiceInputWindowDidRequestStartRecording(_ window: VoiceInputWindow)
    func voiceInputWindowDidRequestStopRecording(_ window: VoiceInputWindow)
    func voiceInputWindow(_ window: VoiceInputWindow, didSubmitText text: String)
}

class VoiceInputWindow: NSObject {
    weak var delegate: VoiceInputWindowDelegate?

    private var window: NSWindow!
    private var titleLabel: NSTextField!
    private var statusLabel: NSTextField!
    private var inputTextField: NSTextField!
    private var recordButton: NSButton!
    private var backgroundView: NSVisualEffectView!
    private var responseScrollView: NSScrollView!
    private var responseTextView: NSTextView!
    private var outsideEventMonitor: Any?
    private var isRecording = false
    private var inputMode: InputMode = .voice
    private var llmResponseTexts: [String] = []
    private let minWindowHeight: CGFloat = 150
    private var chromeHeight: CGFloat = 0
    private var recordButtonTopConstraintVoice: NSLayoutConstraint!
    private var recordButtonTopConstraintText: NSLayoutConstraint!
    private var inputTextFieldHeightConstraint: NSLayoutConstraint!

    override init() {
        super.init()
        setupWindow()
    }

    private func setupWindow() {
        let windowRect = NSRect(x: 0, y: 0, width: 320, height: minWindowHeight)
        window = VoiceInputFloatingWindow(
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

    // 文本输入框
    inputTextField = NSTextField()
    inputTextField.placeholderString = "请输入要执行的指令"
    inputTextField.font = NSFont.systemFont(ofSize: 14)
    inputTextField.isBordered = true
    inputTextField.isBezeled = true
    inputTextField.focusRingType = .default
    inputTextField.usesSingleLineMode = true
    inputTextField.maximumNumberOfLines = 1
    inputTextField.lineBreakMode = .byTruncatingTail
    inputTextField.translatesAutoresizingMaskIntoConstraints = false
    inputTextField.target = self
    inputTextField.action = #selector(submitTextFromField)
    inputTextField.isHidden = true

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
        responseTextView.isVerticallyResizable = true
        responseTextView.isHorizontallyResizable = false
        responseTextView.minSize = NSSize(width: 0, height: 0)
        responseTextView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        responseTextView.textContainer?.widthTracksTextView = true
        responseTextView.textContainer?.heightTracksTextView = false

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
    backgroundView.addSubview(inputTextField)
        backgroundView.addSubview(recordButton)
        backgroundView.addSubview(responseScrollView)

        NSLayoutConstraint.activate([
            titleLabel.topAnchor.constraint(equalTo: backgroundView.topAnchor, constant: 20),
            titleLabel.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 20),
            titleLabel.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -20),

            statusLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 14),
            statusLabel.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 20),
            statusLabel.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -20),

            inputTextField.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 18),
            inputTextField.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 18),
            inputTextField.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -18),

            recordButton.centerXAnchor.constraint(equalTo: backgroundView.centerXAnchor),
            recordButton.heightAnchor.constraint(equalToConstant: 38),
            recordButton.widthAnchor.constraint(equalToConstant: 150),

            responseScrollView.topAnchor.constraint(equalTo: recordButton.bottomAnchor, constant: 18),
            responseScrollView.leadingAnchor.constraint(equalTo: backgroundView.leadingAnchor, constant: 18),
            responseScrollView.trailingAnchor.constraint(equalTo: backgroundView.trailingAnchor, constant: -18),
            responseScrollView.bottomAnchor.constraint(equalTo: backgroundView.bottomAnchor, constant: -16)
        ])

        inputTextFieldHeightConstraint = inputTextField.heightAnchor.constraint(equalToConstant: 0)
        inputTextFieldHeightConstraint.isActive = true
        recordButtonTopConstraintVoice = recordButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 22)
        recordButtonTopConstraintText = recordButton.topAnchor.constraint(equalTo: inputTextField.bottomAnchor, constant: 18)
        recordButtonTopConstraintVoice.isActive = true

        updateButtonAppearance()

    }

    func setInputMode(_ mode: InputMode, forceStatusReset: Bool = false) {
        let previousMode = inputMode
        inputMode = mode
        let shouldResetStatus = forceStatusReset || previousMode != mode

        switch inputMode {
        case .voice:
            inputTextField.isHidden = true
            inputTextFieldHeightConstraint.constant = 0
            recordButtonTopConstraintText.isActive = false
            recordButtonTopConstraintVoice.isActive = true
            isRecording = false
            if shouldResetStatus {
                updateStatus("点击下方按钮开始录音")
            }
        case .text:
            inputTextField.isHidden = false
            inputTextFieldHeightConstraint.constant = 32
            recordButtonTopConstraintVoice.isActive = false
            recordButtonTopConstraintText.isActive = true
            isRecording = false
            if shouldResetStatus {
                updateStatus("输入指令后按回车或点击下方按钮")
            }
        }

        updateButtonAppearance()
        if shouldResetStatus {
            setRecordButtonEnabled(true)
        }

        backgroundView.layoutSubtreeIfNeeded()
        chromeHeight = 0
        resetWindowHeightIfNeeded()
    }

    func focusTextInput() {
        guard inputMode == .text else { return }
        window.makeFirstResponder(inputTextField)
    }

    private func updateButtonAppearance() {
        let accent = NSColor.controlAccentColor
        switch inputMode {
        case .voice:
            recordButton.title = isRecording ? "停止录音" : "开始录音"
            let tint = isRecording ? NSColor.systemRed : accent
            recordButton.contentTintColor = tint
            recordButton.layer?.backgroundColor = tint.withAlphaComponent(0.18).cgColor
        case .text:
            recordButton.title = "发送指令"
            recordButton.contentTintColor = accent
            recordButton.layer?.backgroundColor = accent.withAlphaComponent(0.18).cgColor
        }
    }

    private func applyDefaultStatusForCurrentMode() {
        switch inputMode {
        case .voice:
            updateStatus("点击下方按钮开始录音")
        case .text:
            updateStatus("输入指令后按回车或点击下方按钮")
        }
    }

    @objc private func submitTextFromField() {
        guard inputMode == .text else { return }
        guard recordButton.isEnabled else { return }
        setRecordButtonEnabled(false)
        submitTextInput()
    }

    private func submitTextInput() {
        let trimmed = inputTextField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            updateStatus("请输入要执行的指令")
            setRecordButtonEnabled(true)
            focusTextInput()
            return
        }

        delegate?.voiceInputWindow(self, didSubmitText: trimmed)
        inputTextField.stringValue = ""
    }

    func showWindow(at statusItem: NSStatusItem) {
        applyDefaultStatusForCurrentMode()
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
    NSApp.activate(ignoringOtherApps: true)
        window.alphaValue = 1.0
        focusTextInput()

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
        let isActiveRecording = inputMode == .voice && status.contains("正在录音")
        statusLabel.textColor = isActiveRecording ? NSColor.systemRed : NSColor.secondaryLabelColor
    }

    @objc private func recordButtonClicked() {
        setRecordButtonEnabled(false)
        switch inputMode {
        case .voice:
            if isRecording {
                delegate?.voiceInputWindowDidRequestStopRecording(self)
            } else {
                delegate?.voiceInputWindowDidRequestStartRecording(self)
            }
        case .text:
            submitTextInput()
        }
    }

    func setRecordingState(_ recording: Bool) {
        if inputMode == .voice {
            isRecording = recording
        } else {
            isRecording = false
        }
        updateButtonAppearance()
    }

    func setRecordButtonEnabled(_ enabled: Bool) {
        recordButton.isEnabled = enabled
        recordButton.alphaValue = enabled ? 1.0 : 0.6
    }

    func resetLLMResponses() {
        llmResponseTexts.removeAll()
        chromeHeight = 0
        renderLLMResponses()
    }

    func displayLLMResponses(_ responses: [String]) {
        llmResponseTexts = responses
        renderLLMResponses()
    }

    private func renderLLMResponses() {
        guard responseTextView != nil else { return }

        if llmResponseTexts.isEmpty {
            responseTextView.string = ""
        } else {
            let formatted = llmResponseTexts.enumerated().map { index, content in
                guard llmResponseTexts.count > 1 else { return content }
                return "\(index + 1). \(content)"
            }.joined(separator: "\n\n")
            responseTextView.string = formatted
        }

        responseTextView.scrollToEndOfDocument(nil)
        updateWindowHeightForCurrentContent()
    }

    private func updateWindowHeightForCurrentContent() {
        backgroundView.layoutSubtreeIfNeeded()

        guard !llmResponseTexts.isEmpty,
              let textContainer = responseTextView.textContainer,
              let layoutManager = responseTextView.layoutManager else {
            resetWindowHeightIfNeeded()
            return
        }

        let availableWidth = responseScrollView.contentSize.width
        textContainer.containerSize = NSSize(width: availableWidth, height: CGFloat.greatestFiniteMagnitude)
        layoutManager.ensureLayout(for: textContainer)
        let usedHeight = layoutManager.usedRect(for: textContainer).height
        let verticalInset = responseTextView.textContainerInset.height * 2
        let contentHeight = max(usedHeight + verticalInset, 0)

        if chromeHeight == 0 {
            backgroundView.layoutSubtreeIfNeeded()
            chromeHeight = backgroundView.frame.height - responseScrollView.frame.height
            if chromeHeight <= 0 {
                chromeHeight = minWindowHeight - max(responseScrollView.frame.height, 0)
            }
        }

        let maxHeight = computeMaxWindowHeight()
        var desiredHeight = chromeHeight + contentHeight
        desiredHeight = max(minWindowHeight, desiredHeight)
        desiredHeight = min(maxHeight, desiredHeight)

        let currentContentHeight = window.contentView?.frame.height ?? window.frame.height
        if abs(currentContentHeight - desiredHeight) > 0.5 {
            var frame = window.frame
            let delta = desiredHeight - currentContentHeight
            frame.size.height += delta
            frame.origin.y -= delta
            window.setFrame(frame, display: window.isVisible, animate: false)
        }

        responseScrollView.flashScrollers()
    }

    private func resetWindowHeightIfNeeded() {
        guard let contentHeight = window.contentView?.frame.height else { return }
        if abs(contentHeight - minWindowHeight) <= 0.5 { return }

        var frame = window.frame
        let delta = minWindowHeight - contentHeight
        frame.size.height += delta
        frame.origin.y -= delta
        window.setFrame(frame, display: window.isVisible, animate: false)
    }

    private func computeMaxWindowHeight() -> CGFloat {
        if let screenHeight = window.screen?.visibleFrame.height ?? NSScreen.main?.visibleFrame.height {
            return max(minWindowHeight, floor(screenHeight / 3))
        }
        return minWindowHeight * 1.5
    }
}