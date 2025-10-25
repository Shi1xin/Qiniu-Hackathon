import Cocoa
import QuartzCore

class VoiceInputWindow: NSObject {
    private var window: NSWindow!
    private var titleLabel: NSTextField!
    private var statusLabel: NSTextField!
    private var cancelButton: NSButton!
    private var pulseLayer: CAShapeLayer!

    override init() {
        super.init()
        setupWindow()
    }

    private func setupWindow() {
        let windowRect = NSRect(x: 0, y: 0, width: 300, height: 150)
        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )

        window.title = "语音输入"
        window.level = .floating
        window.isOpaque = false
        window.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.95)
        window.center()

        setupContentView()
    }

    private func setupContentView() {
        let contentView = NSView()
        contentView.wantsLayer = true
        contentView.layer?.cornerRadius = 12

        // 标题标签
        titleLabel = NSTextField(labelWithString: "🎤 语音输入")
        titleLabel.font = NSFont.boldSystemFont(ofSize: 18)
        titleLabel.textColor = NSColor.labelColor
        titleLabel.alignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false

        // 状态标签
        statusLabel = NSTextField(labelWithString: "准备开始录音...")
        statusLabel.font = NSFont.systemFont(ofSize: 14)
        statusLabel.textColor = NSColor.secondaryLabelColor
        statusLabel.alignment = .center
        statusLabel.translatesAutoresizingMaskIntoConstraints = false

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
        contentView.addSubview(titleLabel)
        contentView.addSubview(statusLabel)
        contentView.addSubview(waveformView)
        contentView.addSubview(cancelButton)

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
            cancelButton.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),
            cancelButton.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            cancelButton.heightAnchor.constraint(equalToConstant: 32),
            cancelButton.widthAnchor.constraint(equalToConstant: 80)
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

    func showWindow() {
        updateStatus("准备开始录音...")
        window.makeKeyAndOrderFront(nil)
        window.center()

        // 添加进入动画
        window.alphaValue = 0
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            window.animator().alphaValue = 1.0
        }
    }

    func hideWindow() {
        // 添加退出动画
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            context.completionHandler = {
                self.window.orderOut(nil)
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
        hideWindow()
    }
}