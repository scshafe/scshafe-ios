// Placeholder test: the package builds for iOS and its targets link.
import Testing
@testable import ScshafeComponents
import ScshafeTokens

@Test func componentsUseTheSnapshotTokens() {
    #expect(SuiLibrary.tokenVersion == SuiTokenSource.version)
    #expect(SuiTokenSource.package == "@scshafe/ui")
}
