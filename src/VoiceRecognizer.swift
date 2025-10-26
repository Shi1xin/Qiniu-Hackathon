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
    private var speechServiceProvider: SpeechServiceProvider = .appleNative
    private var activeProvider: SpeechServiceProvider = .appleNative
    private var elevenLabsAPIKey: String?
    private var recordingFileURL: URL?
    private var audioFile: AVAudioFile?
    private var recordingTimeoutWorkItem: DispatchWorkItem?
    private lazy var urlSession: URLSession = {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 60
        configuration.timeoutIntervalForResource = 120
        return URLSession(configuration: configuration)
    }()

    weak var delegate: VoiceRecognizerDelegate?

    override init() {
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))!
        super.init()
    }

    func updateSpeechService(provider: SpeechServiceProvider, apiKey: String?) {
        speechServiceProvider = provider
        elevenLabsAPIKey = apiKey
    }

    func requestPermissionsAndStartRecording() {
        switch speechServiceProvider {
        case .appleNative:
            SFSpeechRecognizer.requestAuthorization { status in
                DispatchQueue.main.async {
                    switch status {
                    case .authorized:
                        print("语音识别权限已授权")
                        self.requestMicrophonePermissionAndStartRecording()
                    case .denied:
                        print("语音识别权限被拒绝")
                        self.notifyFailure(code: 1, message: "语音识别权限被拒绝")
                    case .restricted:
                        print("语音识别权限受限")
                        self.notifyFailure(code: 2, message: "语音识别权限受限")
                    case .notDetermined:
                        print("语音识别权限未确定")
                        self.notifyFailure(code: 3, message: "语音识别权限未确定")
                    @unknown default:
                        print("未知的语音识别权限状态")
                        self.notifyFailure(code: 4, message: "未知的语音识别权限状态")
                    }
                }
            }
        case .elevenLabs:
            guard let apiKey = elevenLabsAPIKey, !apiKey.isEmpty else {
                notifyFailure(code: 11, message: "未配置 ElevenLabs API Key")
                return
            }

            requestMicrophonePermissionAndStartRecording()
        }
    }

    private func requestMicrophonePermissionAndStartRecording() {
        AVCaptureDevice.requestAccess(for: .audio) { granted in
            DispatchQueue.main.async {
                if granted {
                    print("麦克风权限已授权")
                    self.startRecording()
                } else {
                    print("麦克风权限被拒绝")
                    self.notifyFailure(code: 5, message: "麦克风权限被拒绝")
                }
            }
        }
    }

    func startRecording() {
        resetCurrentSession()
        lastRecognizedText = ""
        activeProvider = speechServiceProvider

        print("准备开始录音, provider = \(activeProvider.rawValue)")

        switch activeProvider {
        case .appleNative:
            startAppleSpeechRecognition()
        case .elevenLabs:
            startElevenLabsRecording()
        }
    }

    func stopRecording(dueToCancellation: Bool = true) {
        recordingTimeoutWorkItem?.cancel()

        switch activeProvider {
        case .appleNative:
            stopAppleRecording(dueToCancellation: dueToCancellation)
        case .elevenLabs:
            stopElevenLabsRecording(dueToCancellation: dueToCancellation)
        }
    }

    private func startAppleSpeechRecognition() {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest else {
            notifyFailure(code: 6, message: "创建语音识别请求失败")
            return
        }

        recognitionRequest.shouldReportPartialResults = true

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }
        isTapInstalled = true

        audioEngine.prepare()

        do {
            try audioEngine.start()
            delegate?.voiceRecognizerDidStartRecording(self)
        } catch {
            notifyFailure(error: error)
            return
        }

        scheduleRecordingTimeout()

        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self else { return }

            if let result {
                let recognizedText = result.bestTranscription.formattedString
                let trimmedText = recognizedText.trimmingCharacters(in: .whitespacesAndNewlines)
                print("识别结果: \(recognizedText)")

                if !trimmedText.isEmpty {
                    self.lastRecognizedText = trimmedText
                }

                if result.isFinal {
                    let finalText = !trimmedText.isEmpty ? trimmedText : self.lastRecognizedText
                    DispatchQueue.main.async {
                        self.delegate?.voiceRecognizer(self, didReceiveText: finalText)
                        self.stopRecording(dueToCancellation: false)
                    }
                }
            }

            if let error {
                let nsError = error as NSError
                print("识别错误: \(error) | domain: \(nsError.domain) code: \(nsError.code)")

                if nsError.domain == "kLSRErrorDomain" && nsError.code == 301 {
                    print("识别任务已取消，忽略该错误。")
                    return
                }

                DispatchQueue.main.async {
                    self.notifyFailure(error: error)
                    self.stopRecording()
                }
            }
        }
    }

    private func startElevenLabsRecording() {
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("vpilot-elevenlabs-\(UUID().uuidString)")
            .appendingPathExtension("wav")

        do {
            audioFile = try AVAudioFile(forWriting: tempURL,
                                        settings: recordingFormat.settings,
                                        commonFormat: recordingFormat.commonFormat,
                                        interleaved: recordingFormat.isInterleaved)
        } catch {
            notifyFailure(error: error)
            return
        }

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            guard let self else { return }
            do {
                try self.audioFile?.write(from: buffer)
            } catch {
                print("写入录音缓冲失败: \(error)")
            }
        }
        isTapInstalled = true
        recordingFileURL = tempURL

        audioEngine.prepare()

        do {
            try audioEngine.start()
            delegate?.voiceRecognizerDidStartRecording(self)
        } catch {
            notifyFailure(error: error)
            return
        }

        scheduleRecordingTimeout()
    }

    private func stopAppleRecording(dueToCancellation: Bool) {
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

    private func stopElevenLabsRecording(dueToCancellation: Bool) {
        if audioEngine.isRunning {
            audioEngine.stop()
        }

        if isTapInstalled {
            audioEngine.inputNode.removeTap(onBus: 0)
            isTapInstalled = false
        }

        audioFile = nil
        let fileURL = recordingFileURL
        recordingFileURL = nil

        delegate?.voiceRecognizerDidStopRecording(self)
        print("录音已停止")

        if dueToCancellation {
            if let fileURL = fileURL {
                try? FileManager.default.removeItem(at: fileURL)
            }
            return
        }

        guard let fileURL = fileURL else {
            return
        }

        transcribeElevenLabsAudio(at: fileURL)
    }

    private func transcribeElevenLabsAudio(at url: URL) {
        guard let apiKey = elevenLabsAPIKey, !apiKey.isEmpty else {
            notifyFailure(code: 12, message: "未配置 ElevenLabs API Key")
            try? FileManager.default.removeItem(at: url)
            return
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: ElevenLabsConstants.speechToTextEndpoint)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "xi-api-key")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        var body = Data()
        appendFormField(name: "model_id", value: ElevenLabsConstants.speechToTextModelId, to: &body, boundary: boundary)

        do {
            let fileData = try Data(contentsOf: url)
            appendFileField(name: "file", filename: url.lastPathComponent, mimeType: "audio/wav", fileData: fileData, to: &body, boundary: boundary)
        } catch {
            notifyFailure(error: error)
            try? FileManager.default.removeItem(at: url)
            return
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        urlSession.dataTask(with: request) { [weak self] data, response, error in
            guard let self else { return }

            defer { try? FileManager.default.removeItem(at: url) }

            if let error {
                self.notifyFailure(error: error)
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                self.notifyFailure(code: 13, message: "无法解析 ElevenLabs 响应")
                return
            }

            guard (200..<300).contains(httpResponse.statusCode) else {
                let message = String(data: data ?? Data(), encoding: .utf8) ?? "\(httpResponse.statusCode)"
                print("ElevenLabs STT 请求失败: \(message)")
                self.notifyFailure(code: httpResponse.statusCode, message: "ElevenLabs 语音识别失败: \(message)")
                return
            }

            guard
                let data,
                let json = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any]
            else {
                self.notifyFailure(code: 14, message: "解析 ElevenLabs 响应失败")
                return
            }

            let transcript = (json["text"] as? String)
                ?? (json["transcription"] as? String)
                ?? (json["output_text"] as? String)

            guard let trimmed = transcript?.trimmingCharacters(in: .whitespacesAndNewlines), !trimmed.isEmpty else {
                self.notifyFailure(code: 15, message: "ElevenLabs 未返回识别结果")
                return
            }

            DispatchQueue.main.async {
                self.delegate?.voiceRecognizer(self, didReceiveText: trimmed)
            }
        }.resume()
    }

    private func scheduleRecordingTimeout() {
        recordingTimeoutWorkItem?.cancel()

        let workItem = DispatchWorkItem { [weak self] in
            guard let self else { return }
            if self.audioEngine.isRunning {
                print("录音超时，自动停止")
                self.stopRecording()
            }
        }

        recordingTimeoutWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + 10, execute: workItem)
    }

    private func resetCurrentSession() {
        recordingTimeoutWorkItem?.cancel()

        if audioEngine.isRunning {
            audioEngine.stop()
        }

        if isTapInstalled {
            audioEngine.inputNode.removeTap(onBus: 0)
            isTapInstalled = false
        }

        recognitionRequest?.endAudio()
        recognitionTask?.cancel()

        recognitionRequest = nil
        recognitionTask = nil
        audioFile = nil

        if let url = recordingFileURL {
            try? FileManager.default.removeItem(at: url)
            recordingFileURL = nil
        }
    }

    private func notifyFailure(code: Int, message: String) {
        let error = NSError(domain: "VoiceRecognizer", code: code, userInfo: [NSLocalizedDescriptionKey: message])
        notifyFailure(error: error)
    }

    private func notifyFailure(error: Error) {
        DispatchQueue.main.async {
            self.delegate?.voiceRecognizer(self, didFailWithError: error)
        }
    }

    private func appendFormField(name: String, value: String, to data: inout Data, boundary: String) {
        data.append("--\(boundary)\r\n".data(using: .utf8)!)
        data.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
        data.append("\(value)\r\n".data(using: .utf8)!)
    }

    private func appendFileField(name: String, filename: String, mimeType: String, fileData: Data, to data: inout Data, boundary: String) {
        data.append("--\(boundary)\r\n".data(using: .utf8)!)
        data.append("Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        data.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        data.append(fileData)
        data.append("\r\n".data(using: .utf8)!)
    }
}