import SwiftUI

/// The band between a shape and the same shape inset by `width`.
private struct SuiRing<S: InsettableShape>: Shape {
    let shape: S
    let width: CGFloat

    func path(in rect: CGRect) -> Path {
        var path = shape.path(in: rect)
        path.addPath(shape.inset(by: width).path(in: rect))
        return path
    }
}

extension InsettableShape {
    /// An inside border, filled as a ring rather than stroked: a stroked pill drew stray
    /// marks at its ends in offscreen renders.
    func suiBorder(_ color: Color, lineWidth: CGFloat = 1) -> some View {
        SuiRing(shape: self, width: lineWidth).fill(color, style: FillStyle(eoFill: true))
    }
}
