import SwiftUI

extension InsettableShape {
    /// An inside border. Drawn as an inset stroke with round caps: a butt-capped stroke of a
    /// pill drew stray marks at its ends in offscreen renders.
    func suiBorder(_ color: Color, lineWidth: CGFloat = 1) -> some View {
        inset(by: lineWidth / 2)
            .stroke(color, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round, lineJoin: .round))
    }
}
