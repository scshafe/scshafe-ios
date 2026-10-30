import ScshafeTokens
import SwiftUI
import Testing
@testable import ScshafeComponents

@MainActor
@Suite struct SuiChipBannerTests {
    @Test func chipSpeaksItsToneBeforeItsTitle() {
        #expect(SuiChip.spokenLabel(prefix: "Warning", title: "Needs input") == "Warning, Needs input")
        #expect(SuiChip.spokenLabel(prefix: nil, title: "Backlog") == "Backlog")
    }

    @Test func bannerSpeaksToneTitleAndMessage() {
        let spoken = SuiBanner<EmptyView>.spokenLabel(toneLabel: "Error", title: "Could not save", message: "Try again.")
        #expect(spoken == "Error, Could not save Try again.")
        #expect(SuiBanner<EmptyView>.spokenLabel(toneLabel: "OK", title: "Saved", message: nil) == "OK, Saved")
    }

    @Test func chipGallery() {
        assertVariants(
            VStack(alignment: .leading, spacing: SuiSpace.md) {
                ForEach(SuiTone.allCases, id: \.self) { tone in
                    SuiChip(tone.rawValue.capitalized, tone: tone)
                }
                ForEach(SuiBucket.allCases, id: \.self) { bucket in
                    SuiChip(bucket.colorName.capitalized, bucket: bucket)
                }
            },
            height: 900
        )
    }

    @Test func bannerGallery() {
        assertVariants(
            VStack(spacing: SuiSpace.md) {
                SuiBanner("Saved", tone: .ok)
                SuiBanner("Heads up", tone: .warn, message: "Two rooms are not placed yet.", onDismiss: {})
                SuiBanner("Could not save", tone: .danger, message: "Check the connection and try again.") {
                    Button("Retry") {}.buttonStyle(.bordered)
                }
                SuiBanner("Note", tone: .neutral)
                SuiBanner("Update available", tone: .info)
            },
            height: 1100
        )
    }
}
