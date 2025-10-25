// swift-tools-version:5.9
import PackageDescription
import Foundation

let packageRoot = URL(fileURLWithPath: #filePath)
    .deletingLastPathComponent()
let infoPlistPath = packageRoot
    .appendingPathComponent("src/Resources/Info.plist")
    .path

let package = Package(
    name: "VPilot",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "VPilot",
            targets: ["VPilot"]
        )
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "VPilot",
            dependencies: [],
            path: "src",
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