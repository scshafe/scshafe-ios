// swift-tools-version: 6.2
// The SCSHAFE iOS component library. iOS 26 is the floor for the library and
// for every app that uses it (docs/brief.md). Names and layout: docs/design.md.
import PackageDescription

let package = Package(
    name: "scshafe-ios",
    platforms: [
        .iOS(.v26),
    ],
    products: [
        // Generated design tokens only (colours, space, radius, motion): no
        // views, so an extension can take the tokens alone.
        .library(name: "ScshafeTokens", targets: ["ScshafeTokens"]),
        // Styles, modifiers and components built on the tokens.
        .library(name: "ScshafeComponents", targets: ["ScshafeComponents"]),
    ],
    targets: [
        .target(name: "ScshafeTokens"),
        .target(name: "ScshafeComponents", dependencies: ["ScshafeTokens"]),
        .testTarget(name: "ScshafeTokensTests", dependencies: ["ScshafeTokens"]),
        .testTarget(name: "ScshafeComponentsTests", dependencies: ["ScshafeComponents"]),
    ],
    swiftLanguageModes: [.v6]
)
