import SwiftUI
import Testing
@testable import ScshafeTokens

@Suite struct SuiNativeTests {
    @Test func radiiSpacesAndMotionFollowTheRegistry() {
        #expect(SuiRadius.sm == 8)
        #expect(SuiRadius.base == SuiRadius.md)
        #expect(SuiRadius.pill == 999)
        #expect(SuiSpace.none == 0)
        #expect(SuiSpace.xxl == 32)
        #expect(SuiMotion.duration == 0.12)
        #expect(SuiMotion.reducedDuration == 0)
    }

    @Test func fiveTonesAndEightBuckets() {
        #expect(SuiTone.allCases.map(\.rawValue) == ["neutral", "info", "ok", "warn", "danger"])
        #expect(SuiBucket.allCases.count == 8)
        #expect(SuiBucket.one.colorName == "blue")
        #expect(SuiBucket.eight.colorName == "violet")
    }

    @Test func headingRolesAreTheTitleRoles() {
        let headings = SuiTextRole.allCases.filter(\.isHeading)
        #expect(headings == [.display, .title, .heading, .subheading, .section])
    }
}
