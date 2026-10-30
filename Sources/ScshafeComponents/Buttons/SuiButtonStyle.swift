import ScshafeTokens
import SwiftUI

/// The button looks the library offers. Apple's glass styles on the floating layer;
/// a solid style when glass is off.
public enum SuiButtonKind: Sendable {
    /// A secondary glass button.
    case glass
    /// The one prominent action of a bar or sheet.
    case prominent
    /// A prominent action with the danger tone.
    case destructive
}

private struct SuiButtonModifier: ViewModifier {
    @Environment(\.suiTransparency) private var transparency
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorSchemeContrast) private var contrast

    let kind: SuiButtonKind

    private var solid: Bool {
        transparency == .reduced || reduceTransparency || contrast == .increased
    }

    @ViewBuilder
    func body(content: Content) -> some View {
        if solid {
            content.buttonStyle(SuiSolidButtonStyle(kind: kind))
        } else {
            switch kind {
            case .glass:
                content.buttonStyle(.glass)
            case .prominent:
                content.buttonStyle(.glassProminent)
            case .destructive:
                content.buttonStyle(.glassProminent).tint(SuiTone.danger.base)
            }
        }
    }
}

/// The solid look of the glass buttons (Reduce Transparency, Increase Contrast).
struct SuiSolidButtonStyle: ButtonStyle {
    @Environment(\.colorSchemeContrast) private var contrast

    let kind: SuiButtonKind

    private var tint: Color { kind == .destructive ? SuiTone.danger.base : SuiColor.accent }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.body.weight(kind == .glass ? .regular : .semibold))
            .foregroundStyle(kind == .glass ? SuiColor.text : tint)
            .padding(.horizontal, SuiSpace.lg)
            .frame(minHeight: 44)
            .background(kind == .glass ? SuiColor.popover : SuiColor.accentSubtle, in: Capsule())
            .overlay(Capsule().strokeBorder(
                kind == .glass ? SuiColor.borderStrong : tint,
                lineWidth: contrast == .increased ? 2 : 1))
            .opacity(configuration.isPressed ? 0.7 : 1)
            .contentShape(Capsule())
    }
}

extension View {
    /// Styles the buttons inside this view: the system glass styles, or their solid
    /// look under Reduce Transparency and Increase Contrast. For controls on the
    /// floating layer; content actions use the system styles.
    public func suiButtonStyle(_ kind: SuiButtonKind) -> some View {
        modifier(SuiButtonModifier(kind: kind))
    }
}
