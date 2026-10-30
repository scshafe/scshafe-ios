import ScshafeTokens
import SwiftUI

/// Haptics with Apple's documented meanings (HIG, Playing haptics). They complement
/// what is shown and never stand alone.
public enum SuiHaptic: Sendable {
    /// A task finished.
    case success
    /// A task finished with a caveat.
    case warning
    /// A task failed.
    case error
    /// A value changed (a tool, a tab, a picker).
    case selection
    /// Something snapped or landed.
    case impact

    var feedback: SensoryFeedback {
        switch self {
        case .success: .success
        case .warning: .warning
        case .error: .error
        case .selection: .selection
        case .impact: .impact
        }
    }
}

extension SuiTone {
    /// The haptic that goes with a tone's outcome; `nil` for the tones that are not one.
    public var haptic: SuiHaptic? {
        switch self {
        case .ok: .success
        case .warn: .warning
        case .danger: .error
        case .neutral, .info: nil
        }
    }
}

extension View {
    /// Plays `haptic` when `trigger` changes. Pair it with a visible change.
    public func suiHaptic<T: Equatable>(_ haptic: SuiHaptic, trigger: T) -> some View {
        sensoryFeedback(haptic.feedback, trigger: trigger)
    }
}
