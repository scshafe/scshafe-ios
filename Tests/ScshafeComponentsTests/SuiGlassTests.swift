import ScshafeTokens
import SwiftUI
import Testing
@testable import ScshafeComponents

/// The solid fallback is ours and is covered in every variant. System glass is drawn by
/// the OS and needs a host app to render, so it is not snapshotted in a package test.
@MainActor
@Suite struct SuiGlassTests {
    private func controls() -> some View {
        SuiGlassContainer(spacing: SuiSpace.md) {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: SuiSpace.md) { buttons }
                VStack(spacing: SuiSpace.md) { buttons }
            }
        }
    }

    @ViewBuilder private var buttons: some View {
        Button("Back") {}.suiButtonStyle(.glass)
        Button("Save") {}.suiButtonStyle(.prominent)
        Button("Delete") {}.suiButtonStyle(.destructive)
    }

    private func labelOnGlass() -> some View {
        Label("Floating", systemImage: "scope")
            .padding(SuiSpace.md)
            .suiGlass()
    }

    @Test func solidFallback() {
        assertVariants(
            VStack(spacing: SuiSpace.lg) {
                controls()
                labelOnGlass()
            }
            .environment(\.suiTransparency, .reduced),
            height: 420
        )
    }
}
