import Cocoa
import QuartzCore

protocol VoiceInputWindowDelegate: AnyObject {
    func voiceInputWindowDidRequestStartRecording(_ window: VoiceInputWindow)
    func voiceInputWindowDidRequestStopRecording(_ window: VoiceInputWindow)
    func voiceInputWindowDidRequestCancel(_ window: VoiceInputWindow)
}

class VoiceInputWindow: NSObject {
    weak var delegate: VoiceInputWindowDelegate?

    private var window: NSWindow!
    private var titleLabel: NSTextField!
    private var statusLabel: NSTextField!
    private var recordButton: NSButton!
    private var cancelButton: NSButton!
    private var pulseLayer: CAShapeLayer!
    private var outsideEventMonitor: Any?
    private var isRecording = false

    override init() {
        super.init()
        setupWindow()
    }

    private func setupWindow() {
        let windowRect = NSRect(x: 0, y: 0, width: 300, height: 150)
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
        let contentView = NSView()
        contentView.wantsLayer = true
        contentView.layer?.cornerRadius = 12
        contentView.layer?.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.95).cgColor

        // 标题标签
        titleLabel = NSTextField(labelWithString: "🎤 语音输入")
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
    recordButton.bezelStyle = .rounded
    recordButton.translatesAutoresizingMaskIntoConstraints = false

    // 取消按钮
    cancelButton = NSButton(title: "取消", target: self, action: #selector(cancelClicked))
    cancelButton.bezelStyle = .rounded
    cancelButton.translatesAutoresizingMaskIntoConstraints = false

        // 音频波形视图
        let waveformView = NSView()
        waveformView.wantsLayer = true
        waveformView.layer?.backgroundColor = NSColor.controlAccentColor.withAlphaComponent(0.1).cgColor
        waveformView.layer?.cornerRadius = 8
        waveformView.translatesAutoresizingMaskIntoConstraints = false

        // 创建脉冲动画
        setupPulseAnimation(in: waveformView)

        // 添加子视图
    let buttonStack = NSStackView(views: [recordButton, cancelButton])
    buttonStack.orientation = .horizontal
    buttonStack.alignment = .centerY
    buttonStack.spacing = 12
    buttonStack.translatesAutoresizingMaskIntoConstraints = false

    contentView.addSubview(titleLabel)
    contentView.addSubview(statusLabel)
    contentView.addSubview(waveformView)
    contentView.addSubview(buttonStack)

        window.contentView = contentView

        // 设置约束
        NSLayoutConstraint.activate([
            // 标题
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),

            // 波形视图
            waveformView.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 15),
            waveformView.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            waveformView.widthAnchor.constraint(equalToConstant: 80),
            waveformView.heightAnchor.constraint(equalToConstant: 80),

            // 状态标签
            statusLabel.topAnchor.constraint(equalTo: waveformView.bottomAnchor, constant: 15),
            statusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            statusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),

            // 取消按钮
            recordButton.heightAnchor.constraint(equalToConstant: 36),
            recordButton.widthAnchor.constraint(equalToConstant: 140),
            cancelButton.heightAnchor.constraint(equalToConstant: 32),
            cancelButton.widthAnchor.constraint(equalToConstant: 80),
            buttonStack.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            buttonStack.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20)
        ])
    }

    private func setupPulseAnimation(in view: NSView) {
        pulseLayer = CAShapeLayer()
        let size = CGSize(width: 60, height: 60)
        let rect = CGRect(origin: CGPoint(x: (view.bounds.width - size.width) / 2,
                                        y: (view.bounds.height - size.height) / 2),
                         size: size)
        pulseLayer.path = CGPath(ellipseIn: rect, transform: nil)
        pulseLayer.fillColor = NSColor.controlAccentColor.cgColor
        pulseLayer.opacity = 0.3

        view.layer?.addSublayer(pulseLayer)

        // 创建脉冲动画
        let pulseAnimation = CABasicAnimation(keyPath: "transform.scale")
        pulseAnimation.duration = 1.5
        pulseAnimation.fromValue = 1.0
        pulseAnimation.toValue = 1.3
        pulseAnimation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        pulseAnimation.autoreverses = true
        pulseAnimation.repeatCount = .infinity

        pulseLayer.add(pulseAnimation, forKey: "pulse")
    }

    func showWindow(at statusItem: NSStatusItem) {
    updateStatus("点击下方按钮开始录音")
        setRecordingState(false)
        setRecordButtonEnabled(true)

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

        // 添加进入动画
        window.alphaValue = 0
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            window.animator().alphaValue = 1.0
        }

        // 添加全局点击监听器，点击窗口外部时关闭窗口
        if let monitor = outsideEventMonitor {
            NSEvent.removeMonitor(monitor)
        }
        outsideEventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .leftMouseDown) { [weak self] _ in
            DispatchQueue.main.async {
                self?.hideWindow()
            }
        }
    }

    func hideWindow() {
        if let monitor = outsideEventMonitor {
            NSEvent.removeMonitor(monitor)
            outsideEventMonitor = nil
        }

        // 添加退出动画
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            context.completionHandler = {
                self.window.orderOut(nil)
                self.setRecordingState(false)
                self.setRecordButtonEnabled(true)
            }
            window.animator().alphaValue = 0.0
        }
    }

    func updateStatus(_ status: String) {
        statusLabel.stringValue = status

        // 根据状态更新脉冲动画
        if status.contains("录音") {
            pulseLayer.opacity = 0.6
            pulseLayer.fillColor = NSColor.systemRed.cgColor
        } else if status.contains("识别") {
            pulseLayer.opacity = 0.4
            pulseLayer.fillColor = NSColor.systemOrange.cgColor
        } else {
            pulseLayer.opacity = 0.3
            pulseLayer.fillColor = NSColor.controlAccentColor.cgColor
        }
    }

    @objc private func cancelClicked() {
        delegate?.voiceInputWindowDidRequestCancel(self)
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
        recordButton.contentTintColor = recording ? NSColor.systemRed : nil
    }

    func setRecordButtonEnabled(_ enabled: Bool) {
        recordButton.isEnabled = enabled
    }
}