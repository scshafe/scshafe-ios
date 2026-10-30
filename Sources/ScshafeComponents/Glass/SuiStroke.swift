import ScshafeTokens
import SwiftUI

extension InsettableShape {
    /// An inside border. Drawn as an inset stroke: `strokeBorder` left stray marks in
    /// offscreen renders.
    func suiBorder(_ color: Color, lineWidth: CGFloat = 1) -> some View {
        inset(by: lineWidth / 2).stroke(color, lineWidth: lineWidth)
    }
}

/// A pill: the capsule of a chip or a button. A rounded rectangle at the pill radius, because
/// `Capsule` strokes left stray marks at its ends in offscreen renders.
public struct SuiPill: InsettableShape {
    private var inset: CGFloat = 0

    public init() {}

    public func path(in rect: CGRect) -> Path {
        RoundedRectangle(cornerRadius: SuiRadius.pill, style: .continuous)
            .inset(by: inset)
            .path(in: rect)
    }

    public func inset(by amount: CGFloat) -> SuiPill {
        var copy = self
        copy.inset += amount
        return copy
    }
}
