import ScshafeTokens
import SwiftUI

/// Whether glass may be translucent. `.reduced` forces the solid fallback, as
/// Reduce Transparency and Increase Contrast do (scshafe-ui's `data-sui-transparency`).
public enum SuiTransparency: Sendable {
    case automatic
    case reduced
}

extension EnvironmentValues {
    /// Forces the solid fallback of `suiGlass` (tests and previews use it).
    @Entry public var suiTransparency: SuiTransparency = .automatic
}

/// The kinds of glass the library offers.
public enum SuiGlassStyle: Sendable {
    /// System `.regular` glass: the default.
    case regular
    /// System `.clear` glass over media, with the dimming layer the HIG asks for.
    case clearOverMedia
}

private struct SuiGlassModifier<S: InsettableShape>: ViewModifier {
    @Environment(\.suiTransparency) private var transparency
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorSchemeContrast) private var contrast

    let style: SuiGlassStyle
    let shape: S
    let interactive: Bool

    private var solid: Bool {
        transparency == .reduced || reduceTransparency || contrast == .increased
    }

    @ViewBuilder
    func body(content: Content) -> some View {
        if solid {
            content
                .background(SuiColor.popover, in: shape)
                .overlay(shape.strokeBorder(SuiColor.borderStrong, lineWidth: contrast == .increased ? 2 : 1))
                .suiShadow(SuiShadow.floating)
        } else if style == .clearOverMedia {
            content
                .background(SuiColor.backdrop, in: shape)
                .glassEffect(.clear.interactive(interactive), in: shape)
        } else {
            content.glassEffect(.regular.interactive(interactive), in: shape)
        }
    }
}

extension View {
    /// Glass for a control or the floating layer, never for content. Becomes a solid
    /// `popover` surface under Reduce Transparency, Increase Contrast or a forced
    /// `suiTransparency`. This is the only way the library applies glass.
    public func suiGlass<S: InsettableShape>(
        _ style: SuiGlassStyle = .regular,
        in shape: S,
        interactive: Bool = false
    ) -> some View {
        modifier(SuiGlassModifier(style: style, shape: shape, interactive: interactive))
    }

    /// `suiGlass` in a capsule.
    public func suiGlass(_ style: SuiGlassStyle = .regular, interactive: Bool = false) -> some View {
        suiGlass(style, in: Capsule(), interactive: interactive)
    }
}

/// Groups nearby glass elements so they render and morph together. Pass-through when
/// the solid fallback applies.
public struct SuiGlassContainer<Content: View>: View {
    private let spacing: CGFloat?
    private let content: Content

    public init(spacing: CGFloat? = nil, @ViewBuilder content: () -> Content) {
        self.spacing = spacing
        self.content = content()
    }

    public var body: some View {
        GlassEffectContainer(spacing: spacing) { content }
    }
}
