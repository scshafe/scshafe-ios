import ScshafeTokens
import SwiftUI

/// A transient message, optionally with an Undo.
public struct SuiToastItem: Identifiable, Sendable {
    public let id = UUID()
    public let message: String
    public let tone: SuiTone
    public let toneLabel: String
    public let undoTitle: String
    public let undo: (@MainActor @Sendable () -> Void)?
    public let hold: Duration

    /// `hold` is how long the toast stays; it is the time an Undo can be used.
    public init(
        _ message: String,
        tone: SuiTone = .neutral,
        toneLabel: String? = nil,
        undoTitle: String = "Undo",
        undo: (@MainActor @Sendable () -> Void)? = nil,
        hold: Duration = .seconds(6)
    ) {
        self.message = message
        self.tone = tone
        self.toneLabel = toneLabel ?? tone.label
        self.undoTitle = undoTitle
        self.undo = undo
        self.hold = hold
    }
}

/// How long a toast has left. A toast that offers Undo never expires while VoiceOver is
/// running, and none expires while it is being touched.
struct SuiToastHold {
    private(set) var remaining: Duration
    let suspended: Bool

    init(_ hold: Duration, suspended: Bool = false) {
        remaining = hold
        self.suspended = suspended
    }

    /// Advances the clock; true once the toast should go.
    mutating func advance(by elapsed: Duration, touching: Bool) -> Bool {
        guard !suspended else { return false }
        if !touching { remaining -= elapsed }
        return remaining <= .zero
    }
}

struct SuiToastView: View {
    let item: SuiToastItem
    let onUndo: () -> Void

    @Environment(\.dynamicTypeSize) private var typeSize

    /// At accessibility text sizes the message gets the full width and Undo goes below it.
    private var layout: AnyLayout {
        typeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: .leading, spacing: SuiSpace.xs))
            : AnyLayout(HStackLayout(spacing: SuiSpace.md))
    }

    var body: some View {
        layout {
            Image(systemName: item.tone.symbol)
                .foregroundStyle(item.tone == .neutral ? SuiColor.text : item.tone.text)
                .accessibilityHidden(true)
            Text(item.message)
                .font(.subheadline)
                .foregroundStyle(SuiColor.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityLabel(item.tone == .neutral ? item.message : "\(item.toneLabel), \(item.message)")
            if item.undo != nil {
                Button(item.undoTitle, action: onUndo)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(SuiColor.accent)
                    .frame(minHeight: 44)
                    .contentShape(Rectangle())
                    .accessibilityHint(item.message)
            }
        }
        .padding(.horizontal, SuiSpace.lg)
        .padding(.vertical, SuiSpace.xs)
        .frame(minHeight: 44)
        .suiGlass(in: RoundedRectangle(cornerRadius: SuiRadius.xl, style: .continuous))
        .accessibilityElement(children: .contain)
    }
}

private struct SuiToastModifier: ViewModifier {
    @Binding var item: SuiToastItem?
    let haptic: Bool

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityVoiceOverEnabled) private var voiceOver
    @State private var touching = false

    func body(content: Content) -> some View {
        content
            .overlay(alignment: .bottom) {
                if let item {
                    SuiToastView(item: item, onUndo: { undo(item) })
                        .padding(.horizontal, SuiSpace.lg)
                        .padding(.bottom, SuiSpace.sm)
                        .transition(reduceMotion ? .opacity : .move(edge: .bottom).combined(with: .opacity))
                        .simultaneousGesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { _ in touching = true }
                                .onEnded { _ in touching = false }
                        )
                }
            }
            .animation(reduceMotion ? nil : SuiMotion.standard, value: item?.id)
            .task(id: item?.id) { await hold() }
            .onChange(of: item?.id) { _, new in
                if new != nil, let item {
                    AccessibilityNotification.Announcement(item.message).post()
                }
            }
            .sensoryFeedback(trigger: item?.id) { _, new in
                guard haptic, new != nil else { return nil }
                return item?.tone.haptic?.feedback
            }
    }

    private func undo(_ current: SuiToastItem) {
        current.undo?()
        if item?.id == current.id { item = nil }
    }

    private func hold() async {
        guard let current = item else { return }
        var clock = SuiToastHold(current.hold, suspended: voiceOver && current.undo != nil)
        if clock.suspended { return }
        let tick = Duration.milliseconds(100)
        while true {
            try? await Task.sleep(for: tick)
            if Task.isCancelled { return }
            if clock.advance(by: tick, touching: touching) {
                if item?.id == current.id { item = nil }
                return
            }
        }
    }
}

extension View {
    /// Shows `item` as a toast above the bottom edge until its hold ends, it is undone or
    /// another replaces it (the replaced toast's Undo is not run). Set `item` to show one.
    /// `haptic: false` turns off the tone's haptic.
    public func suiToast(_ item: Binding<SuiToastItem?>, haptic: Bool = true) -> some View {
        modifier(SuiToastModifier(item: item, haptic: haptic))
    }
}
