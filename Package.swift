// swift-tools-version:5.9
import PackageDescription
import Foundation

let packageRoot = URL(fileURLWithPath: #filePath)
    .deletingLastPathComponent()
let infoPlistPath = packageRoot
    .appendingPathComponent("Sources/VoiceMenuBar/Resources/Info.plist")
    .path

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
            ],
            linkerSettings: [
                .unsafeFlags([
                    "-Xlinker", "-sectcreate",
                    "-Xlinker", "__TEXT",
                    "-Xlinker", "__info_plist",
                    "-Xlinker", infoPlistPath
                ], .when(platforms: [.macOS]))
            ]
        )
    ]
)