import ScshafeTokens
import SwiftUI
import Testing
@testable import ScshafeComponents

@MainActor
@Suite struct SuiFeedbackTests {
    private struct Failure: LocalizedError {
        var errorDescription: String? { "The connection was lost." }
    }

    @Test func toneHapticsFollowOutcomes() {
        #expect(SuiTone.ok.haptic == .success)
        #expect(SuiTone.warn.haptic == .warning)
        #expect(SuiTone.danger.haptic == .error)
        #expect(SuiTone.neutral.haptic == nil)
        #expect(SuiTone.info.haptic == nil)
    }

    @Test func toastExpiresAfterItsHold() {
        var hold = SuiToastHold(.seconds(1))
        let early = hold.advance(by: .milliseconds(600), touching: false)
        #expect(!early)
        let late = hold.advance(by: .milliseconds(600), touching: false)
        #expect(late)
    }

    @Test func toastWaitsWhileTouched() {
        var hold = SuiToastHold(.seconds(1))
        let whileTouched = hold.advance(by: .seconds(5), touching: true)
        #expect(!whileTouched)
        #expect(hold.remaining == .seconds(1))
        let afterwards = hold.advance(by: .seconds(1), touching: false)
        #expect(afterwards)
    }

    @Test func toastNeverExpiresWhenSuspended() {
        var hold = SuiToastHold(.seconds(1), suspended: true)
        let suspended = hold.advance(by: .seconds(60), touching: false)
        #expect(!suspended)
    }

    @Test func toastItemsAreDistinct() {
        let a = SuiToastItem("Moved")
        let b = SuiToastItem("Moved")
        #expect(a.id != b.id)
        #expect(a.hold == .seconds(6))
        #expect(a.toneLabel == SuiTone.neutral.label)
    }

    @Test func loadStateValue() {
        #expect(SuiLoadState.content(3).value == 3)
        #expect(SuiLoadState<Int>.empty.value == nil)
        #expect(SuiLoadState<Int>.loading("Loading plan").value == nil)
        #expect(SuiLoadState<Int>.failed(Failure()).value == nil)
    }

    private func loadable(_ state: SuiLoadState<[String]>) -> some View {
        SuiLoadable(
            state,
            errorTitle: "Could not load",
            retry: {},
            empty: { SuiEmptyState("No items yet", systemImage: "tray", message: "Items you add appear here.") }
        ) { items in
            VStack(alignment: .leading) { ForEach(items, id: \.self) { Text($0) } }
        }
    }

    // A spinner animates, so the loading state has no image reference.
    @Test func emptyStateAndLoadable() {
        assertVariants(
            VStack(spacing: SuiSpace.lg) {
                loadable(.empty)
                loadable(.failed(Failure()))
                loadable(.content(["First row", "Second row"]))
            },
            height: 1100
        )
    }

    @Test func toastOnItsOwn() {
        assertVariants(
            VStack(spacing: SuiSpace.md) {
                SuiToastView(item: SuiToastItem("Moved to Archive", tone: .ok, undo: {}), onUndo: {})
                SuiToastView(item: SuiToastItem("Could not send", tone: .danger), onUndo: {})
                SuiToastView(item: SuiToastItem("Draft saved"), onUndo: {})
            }
            .environment(\.suiTransparency, .reduced),
            height: 500
        )
    }
}
