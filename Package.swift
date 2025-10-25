// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "VoiceMenuBar",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "VoiceMenuBar",
            targets: ["VoiceMenuBar"]
        )
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "VoiceMenuBar",
            dependencies: [],
            resources: [
                .copy("Resources")
            ]
        )
    ]
)