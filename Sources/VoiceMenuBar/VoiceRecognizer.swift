import Foundation
import Speech
import AVFoundation

protocol VoiceRecognizerDelegate: AnyObject {
    func voiceRecognizer(_ recognizer: VoiceRecognizer, didReceiveText text: String)
    func voiceRecognizer(_ recognizer: VoiceRecognizer, didFailWithError error: Error)
    func voiceRecognizerDidStartRecording(_ recognizer: VoiceRecognizer)
    func voiceRecognizerDidStopRecording(_ recognizer: VoiceRecognizer)
}

class VoiceRecognizer: NSObject {
    private let speechRecognizer: SFSpeechRecognizer
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    private var isTapInstalled = false
    private var lastRecognizedText = ""

    weak var delegate: VoiceRecognizerDelegate?

    override init() {
        // 设置为中文识别
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))!
        super.init()
    }

    func requestPermissionsAndStartRecording() {
        // 请求语音识别权限
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                switch status {
                case .authorized:
                    print("语音识别权限已授权")
                    self.requestMicrophonePermissionAndStartRecording()
                case .denied:
                    print("语音识别权限被拒绝")
                    self.delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 1, userInfo: [NSLocalizedDescriptionKey: "语音识别权限被拒绝"]))
                case .restricted:
                    print("语音识别权限受限")
                    self.delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 2, userInfo: [NSLocalizedDescriptionKey: "语音识别权限受限"]))
                case .notDetermined:
                    print("语音识别权限未确定")
                    self.delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 3, userInfo: [NSLocalizedDescriptionKey: "语音识别权限未确定"]))
                @unknown default:
                    print("未知的语音识别权限状态")
                    self.delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 4, userInfo: [NSLocalizedDescriptionKey: "未知的语音识别权限状态"]))
                }
            }
        }
    }

    private func requestMicrophonePermissionAndStartRecording() {
        // 在macOS上也需要请求麦克风权限
        AVCaptureDevice.requestAccess(for: .audio) { granted in
            DispatchQueue.main.async {
                if granted {
                    print("麦克风权限已授权")
                    self.startRecording()
                } else {
                    print("麦克风权限被拒绝")
                    self.delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 5, userInfo: [NSLocalizedDescriptionKey: "麦克风权限被拒绝"]))
                }
            }
        }
    }

    func startRecording() {
        // 停止之前的识别任务
    stopRecording()

        lastRecognizedText = ""

        // macOS 上不需要配置音频会话，直接开始录音
        print("准备开始录音")

        // 创建识别请求
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            print("创建语音识别请求失败")
            delegate?.voiceRecognizer(self, didFailWithError: NSError(domain: "VoiceRecognizer", code: 6, userInfo: [NSLocalizedDescriptionKey: "创建语音识别请求失败"]))
            return
        }

        recognitionRequest.shouldReportPartialResults = true

        // 配置音频引擎
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        isTapInstalled = true

        audioEngine.prepare()
        do {
            try audioEngine.start()
            print("音频引擎启动成功")
            delegate?.voiceRecognizerDidStartRecording(self)
        } catch {
            print("启动音频引擎失败: \(error)")
            delegate?.voiceRecognizer(self, didFailWithError: error)
            return
        }

        // 开始识别任务
        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { result, error in
            if let result = result {
                let recognizedText = result.bestTranscription.formattedString
                let trimmedText = recognizedText.trimmingCharacters(in: .whitespacesAndNewlines)
                print("识别结果: \(recognizedText)")

                if !trimmedText.isEmpty {
                    self.lastRecognizedText = trimmedText
                }

                // 检查是否有足够的停顿时间来确定录音结束
                if result.isFinal {
                    let finalText = !trimmedText.isEmpty ? trimmedText : self.lastRecognizedText
                    DispatchQueue.main.async {
                        self.delegate?.voiceRecognizer(self, didReceiveText: finalText)
                        self.stopRecording(dueToCancellation: false)
                    }
                }
            }

            if let error = error {
                let nsError = error as NSError
                print("识别错误: \(error) | domain: \(nsError.domain) code: \(nsError.code)")

                if nsError.domain == "kLSRErrorDomain" && nsError.code == 301 {
                    print("识别任务已取消，忽略该错误。")
                    return
                }

                DispatchQueue.main.async {
                    self.delegate?.voiceRecognizer(self, didFailWithError: error)
                    self.stopRecording()
                }
            }

        }

        // 设置超时自动停止
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) {
            if self.audioEngine.isRunning {
                print("录音超时，自动停止")
                self.stopRecording()
            }
        }
    }

    func stopRecording(dueToCancellation: Bool = true) {
        if audioEngine.isRunning {
            audioEngine.stop()
        }

        if isTapInstalled {
            audioEngine.inputNode.removeTap(onBus: 0)
            isTapInstalled = false
        }

        recognitionRequest?.endAudio()

        if dueToCancellation {
            recognitionTask?.cancel()
        }

        recognitionRequest = nil
        recognitionTask = nil
        lastRecognizedText = ""

        delegate?.voiceRecognizerDidStopRecording(self)
        print("录音已停止")
    }
}