import Foundation

enum SpeechServiceProvider: String, CaseIterable {
    case appleNative = "apple-native"
    case elevenLabs = "elevenlabs"

    var localizedName: String {
        switch self {
        case .appleNative: return "macOS 原生"
        case .elevenLabs: return "ElevenLabs"
        }
    }

    var parentMenuTitle: String {
        "语音服务：\(localizedName)"
    }
}

enum ElevenLabsConstants {
    static let apiBaseURL = URL(string: "https://api.elevenlabs.io")!
    static let speechToTextEndpoint = URL(string: "/v1/speech-to-text", relativeTo: apiBaseURL)!
    static func textToSpeechEndpoint(forVoice voiceId: String) -> URL {
        URL(string: "/v1/text-to-speech/\(voiceId)", relativeTo: apiBaseURL)!
    }
    static let speechToTextModelId = "scribe_v1"
    static let textToSpeechModelId = "eleven_flash_v2_5"
    static let defaultVoiceId = "21m00Tcm4TlvDq8ikWAM"
}

enum KeychainKeys {
    static let elevenLabsAPIKey = "com.vpilot.elevenlabs.api_key"
}
