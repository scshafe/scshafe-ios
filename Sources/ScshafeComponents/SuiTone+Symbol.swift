import ScshafeTokens
import SwiftUI

extension SuiTone {
    /// The tone's fixed SF Symbol. A tone's colour is always drawn with it (colour is
    /// never the only signal).
    public var symbol: String {
        switch self {
        case .neutral: "circle"
        case .info: "info.circle.fill"
        case .ok: "checkmark.circle.fill"
        case .warn: "exclamationmark.triangle.fill"
        case .danger: "xmark.octagon.fill"
        }
    }

    /// The spoken prefix ("Warning: ..."), in English. Components take an override so an
    /// app can localise it.
    public var label: String {
        switch self {
        case .neutral: "Note"
        case .info: "Information"
        case .ok: "OK"
        case .warn: "Warning"
        case .danger: "Error"
        }
    }
}
