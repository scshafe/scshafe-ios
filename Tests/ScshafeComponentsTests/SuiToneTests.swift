import ScshafeTokens
import Testing
@testable import ScshafeComponents

@Suite struct SuiToneTests {
    @Test func everyToneHasASymbolAndALabel() {
        for tone in SuiTone.allCases {
            #expect(!tone.symbol.isEmpty)
            #expect(!tone.label.isEmpty)
        }
    }

    @Test func symbolsAreDistinct() {
        let symbols = SuiTone.allCases.map(\.symbol)
        #expect(Set(symbols).count == symbols.count)
    }
}
