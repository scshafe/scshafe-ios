import SwiftUI

extension InsettableShape {
    /// An inside border. Drawn as an inset stroke: `strokeBorder` on a capsule left stray
    /// marks at its ends in offscreen renders.
    func suiBorder(_ color: Color, lineWidth: CGFloat = 1) -> some View {
        inset(by: lineWidth / 2).stroke(color, lineWidth: lineWidth)
    }
}
