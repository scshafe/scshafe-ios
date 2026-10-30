import ScshafeTokens
import SwiftUI
import Testing
@testable import ScshafeComponents

/// Few glass references on purpose: the OS draws the glass, and its look changes with
/// the OS. The solid fallback is ours and is covered in every variant.
@MainActor
@Suite struct SuiGlassTests {
    private func controls() -> some View {
        SuiGlassContainer(spacing: SuiSpace.md) {
            HStack(spacing: SuiSpace.md) {
                Button("Back") {}.suiButtonStyle(.glass)
                Button("Save") {}.suiButtonStyle(.prominent)
                Button("Delete") {}.suiButtonStyle(.destructive)
            }
        }
    }

    private func labelOnGlass() -> some View {
        Label("Floating", systemImage: "scope")
            .padding(SuiSpace.md)
            .suiGlass()
    }

    private var lightAndDark: [SnapshotVariant] {
        SnapshotVariant.all.filter { $0.name.hasSuffix("default-standard") }
    }

    @Test func solidFallback() {
        assertVariants(
            VStack(spacing: SuiSpace.lg) {
                controls()
                labelOnGlass()
            }
            .environment(\.suiTransparency, .reduced),
            height: 300
        )
    }

    @Test func glass() {
        assertVariants(
            VStack(spacing: SuiSpace.lg) {
                controls()
                labelOnGlass()
            },
            height: 300,
            variants: lightAndDark,
            drawInWindow: true
        )
    }
}
