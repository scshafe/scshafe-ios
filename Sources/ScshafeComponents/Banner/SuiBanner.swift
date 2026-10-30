import ScshafeTokens
import SwiftUI

/// An inline, persistent message on a solid card: the tone's symbol, a title, an
/// optional message, optional actions and an optional dismiss button. Never glass.
/// VoiceOver reads "<tone>, title, message"; a warning or an error is also announced
/// when it appears.
public struct SuiBanner<Actions: View>: View {
    private let tone: SuiTone
    private let title: String
    private let message: String?
    private let toneLabel: String
    private let dismissLabel: String
    private let onDismiss: (() -> Void)?
    private let actions: Actions

    public init(
        _ title: String,
        tone: SuiTone,
        message: String? = nil,
        toneLabel: String? = nil,
        dismissLabel: String = "Dismiss",
        onDismiss: (() -> Void)? = nil,
        @ViewBuilder actions: () -> Actions
    ) {
        self.title = title
        self.tone = tone
        self.message = message
        self.toneLabel = toneLabel ?? tone.label
        self.dismissLabel = dismissLabel
        self.onDismiss = onDismiss
        self.actions = actions()
    }

    /// What VoiceOver reads and announces.
    static func spokenLabel(toneLabel: String, title: String, message: String?) -> String {
        [toneLabel + ",", title, message].compactMap { $0 }.joined(separator: " ")
    }

    private var spoken: String { Self.spokenLabel(toneLabel: toneLabel, title: title, message: message) }

    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: SuiRadius.md, style: .continuous) }

    public var body: some View {
        HStack(alignment: .top, spacing: SuiSpace.md) {
            Image(systemName: tone.symbol)
                .foregroundStyle(tone == .neutral ? SuiColor.muted : tone.base)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: SuiSpace.xs) {
                VStack(alignment: .leading, spacing: SuiSpace.xs) {
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(SuiColor.textStrong)
                    if let message {
                        Text(message).suiText(.caption)
                    }
                }
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(spoken)
                actions
                    .padding(.top, SuiSpace.xs)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            if let onDismiss {
                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .frame(minWidth: 44, minHeight: 44)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel(dismissLabel)
                .foregroundStyle(SuiColor.muted)
                .buttonStyle(.plain)
                .padding(.trailing, -SuiSpace.sm)
                .padding(.vertical, -SuiSpace.sm)
            }
        }
        .padding(SuiSpace.md)
        .background(SuiColor.card, in: shape)
        .overlay(alignment: .leading) { tone.base.frame(width: SuiSpace.xs) }
        .clipShape(shape)
        .overlay(shape.suiBorder(SuiColor.border))
        .accessibilityElement(children: .contain)
        .onAppear {
            if tone == .warn || tone == .danger {
                AccessibilityNotification.Announcement(spoken).post()
            }
        }
    }
}

extension SuiBanner where Actions == EmptyView {
    public init(
        _ title: String,
        tone: SuiTone,
        message: String? = nil,
        toneLabel: String? = nil,
        dismissLabel: String = "Dismiss",
        onDismiss: (() -> Void)? = nil
    ) {
        self.init(
            title, tone: tone, message: message, toneLabel: toneLabel,
            dismissLabel: dismissLabel, onDismiss: onDismiss
        ) { EmptyView() }
    }
}

#Preview("Banners") {
    VStack(spacing: SuiSpace.md) {
        SuiBanner("Saved", tone: .ok)
        SuiBanner("Could not save", tone: .danger, message: "Check the connection and try again.", onDismiss: {}) {
            Button("Retry") {}.buttonStyle(.bordered)
        }
    }
    .padding()
}
