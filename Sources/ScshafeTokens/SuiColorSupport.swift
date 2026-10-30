// Hand-written support for the generated tokens (SuiTokens.generated.swift).
import SwiftUI
import UIKit

/// An sRGB colour in 0-255 channels and 0-1 alpha, as the registry writes it.
struct SuiRGBA: Sendable {
    let red: Double
    let green: Double
    let blue: Double
    let alpha: Double

    init(_ red: Double, _ green: Double, _ blue: Double, _ alpha: Double) {
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha
    }

    var uiColor: UIColor {
        UIColor(red: red / 255, green: green / 255, blue: blue / 255, alpha: alpha)
    }
}

extension Color {
    /// A colour that follows the system appearance: `light` or `dark`.
    init(sui light: SuiRGBA, _ dark: SuiRGBA) {
        self.init(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark ? dark.uiColor : light.uiColor
        })
    }
}

/// A drop shadow for a solid floating surface (`SuiShadow`).
public struct SuiShadowStyle: Sendable {
    public let color: Color
    public let radius: CGFloat
    public let x: CGFloat
    public let y: CGFloat
}

extension View {
    /// Applies a `SuiShadow` token.
    public func suiShadow(_ style: SuiShadowStyle) -> some View {
        shadow(color: style.color, radius: style.radius, x: style.x, y: style.y)
    }
}
