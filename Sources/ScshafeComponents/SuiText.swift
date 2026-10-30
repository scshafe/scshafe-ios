import ScshafeTokens
import SwiftUI

extension View {
    /// Sets the font and colour of a text role (Dynamic Type text styles). The heading
    /// roles are announced as headings.
    public func suiText(_ role: SuiTextRole) -> some View {
        font(role.font)
            .foregroundStyle(role.color)
            .accessibilityAddTraits(role.isHeading ? .isHeader : [])
    }
}
