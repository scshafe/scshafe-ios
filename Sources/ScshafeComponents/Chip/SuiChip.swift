import ScshafeTokens
import SwiftUI

/// A status pill: a tone's symbol and a word, or a bucket's dot and name. Solid, never
/// glass. VoiceOver reads it as one element, "<tone>, <title>".
public struct SuiChip: View {
    private let title: String
    private let symbol: String?
    private let dot: Color?
    private let fill: Color
    private let border: Color
    private let text: Color
    private let prefix: String?

    /// A status chip. `systemImage` replaces the tone's own symbol; `toneLabel`
    /// replaces its spoken prefix (use it to localise).
    public init(_ title: String, tone: SuiTone, systemImage: String? = nil, toneLabel: String? = nil) {
        self.title = title
        symbol = systemImage ?? tone.symbol
        dot = nil
        fill = tone.fill
        border = tone.border
        text = tone.text
        prefix = toneLabel ?? tone.label
    }

    /// A category chip for a user-defined group: a dot and the group's name.
    public init(_ title: String, bucket: SuiBucket) {
        self.title = title
        symbol = nil
        dot = bucket.base
        fill = bucket.fill
        border = bucket.border
        text = bucket.text
        prefix = nil
    }

    /// What VoiceOver reads.
    static func spokenLabel(prefix: String?, title: String) -> String {
        prefix.map { "\($0), \(title)" } ?? title
    }

    public var body: some View {
        HStack(spacing: SuiSpace.xs) {
            if let symbol {
                Image(systemName: symbol).imageScale(.small).accessibilityHidden(true)
            }
            if let dot {
                Circle().fill(dot).frame(width: SuiSpace.sm, height: SuiSpace.sm).accessibilityHidden(true)
            }
            Text(title).fixedSize(horizontal: false, vertical: true)
        }
        .font(.caption.weight(.semibold))
        .foregroundStyle(text)
        .padding(.horizontal, SuiSpace.sm)
        .padding(.vertical, SuiSpace.xs)
        .background(fill, in: Capsule())
        .overlay(Capsule().suiBorder(border))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Self.spokenLabel(prefix: prefix, title: title))
    }
}

#Preview("Chips") {
    VStack(alignment: .leading, spacing: SuiSpace.md) {
        ForEach(SuiTone.allCases, id: \.self) { tone in
            SuiChip(tone.rawValue.capitalized, tone: tone)
        }
        SuiChip("Backlog", bucket: .three)
    }
    .padding()
}
