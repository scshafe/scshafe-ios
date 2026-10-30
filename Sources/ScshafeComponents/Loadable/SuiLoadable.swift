import ScshafeTokens
import SwiftUI

/// The state of something that loads. The app computes it; the library owns no
/// networking and no model.
public enum SuiLoadState<Value> {
    /// Loading, with the label that says what (a bare spinner is never enough).
    case loading(String)
    case empty
    case failed(any Error)
    case content(Value)

    /// The loaded value, if there is content.
    public var value: Value? {
        if case .content(let value) = self { value } else { nil }
    }

    fileprivate var tag: Int {
        switch self {
        case .loading: 0
        case .empty: 1
        case .failed: 2
        case .content: 3
        }
    }
}

/// Loading, empty, failed (with Retry) or content, behind one wrapper. The non-content
/// states share a minimum height so the layout does not jump.
public struct SuiLoadable<Value, Content: View, Empty: View>: View {
    private let state: SuiLoadState<Value>
    private let errorTitle: String
    private let retryTitle: String
    private let retry: (() -> Void)?
    private let empty: Empty
    private let content: (Value) -> Content

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    public init(
        _ state: SuiLoadState<Value>,
        errorTitle: String,
        retryTitle: String = "Retry",
        retry: (() -> Void)? = nil,
        @ViewBuilder empty: () -> Empty,
        @ViewBuilder content: @escaping (Value) -> Content
    ) {
        self.state = state
        self.errorTitle = errorTitle
        self.retryTitle = retryTitle
        self.retry = retry
        self.empty = empty()
        self.content = content
    }

    public var body: some View {
        Group {
            switch state {
            case .loading(let label):
                ProgressView(label)
                    .frame(maxWidth: .infinity, minHeight: Self.minimumHeight)
            case .empty:
                empty.frame(maxWidth: .infinity, minHeight: Self.minimumHeight)
            case .failed(let error):
                SuiBanner(errorTitle, tone: .danger, message: error.localizedDescription) {
                    if let retry {
                        Button(retryTitle, action: retry).buttonStyle(.bordered)
                    }
                }
                .frame(maxWidth: .infinity, minHeight: Self.minimumHeight, alignment: .top)
            case .content(let value):
                content(value)
            }
        }
        .transition(.opacity)
        .animation(reduceMotion ? nil : SuiMotion.standard, value: state.tag)
    }

    static var minimumHeight: CGFloat { SuiSpace.xxl * 6 }
}

#Preview("Loadable") {
    SuiLoadable(
        SuiLoadState<[String]>.content(["One", "Two"]),
        errorTitle: "Could not load",
        empty: { SuiEmptyState("Nothing here", systemImage: "tray") }
    ) { items in
        List(items, id: \.self) { Text($0) }
    }
}
