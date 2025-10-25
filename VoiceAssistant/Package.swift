// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "VoiceAssistant",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "VoiceAssistant",
            targets: ["VoiceAssistant"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/swiftlang/swift-subprocess.git", branch: "main")
    ],
    targets: [
        .executableTarget(
            name: "VoiceAssistant",
            dependencies: [
                .product(name: "Subprocess", package: "swift-subprocess")
            ],
            path: "Sources/VoiceAssistant"
        ),
        .testTarget(
            name: "UnitTests",
            dependencies: ["VoiceAssistant"],
            path: "Tests/UnitTests"
        ),
        .testTarget(
            name: "IntegrationTests",
            dependencies: ["VoiceAssistant"],
            path: "Tests/IntegrationTests"
        ),
    ]
)