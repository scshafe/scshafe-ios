import ScshafeTokens
import SwiftUI

/// A thin layer over `ContentUnavailableView`: a title, a symbol, an optional description
/// and optional actions. Use it for "no items", "nothing found" and "inbox zero".
public struct SuiEmptyState<Actions: View>: View {
    private let title: String
    private let systemImage: String
    private let message: String?
    private let actions: Actions

    public init(
        _ title: String,
        systemImage: String,
        message: String? = nil,
        @ViewBuilder actions: () -> Actions
    ) {
        self.title = title
        self.systemImage = systemImage
        self.message = message
        self.actions = actions()
    }

    public var body: some View {
        ContentUnavailableView {
            Label(title, systemImage: systemImage)
        } description: {
            if let message {
                Text(message)
            }
        } actions: {
            actions
        }
    }
}

extension SuiEmptyState where Actions == EmptyView {
    public init(_ title: String, systemImage: String, message: String? = nil) {
        self.init(title, systemImage: systemImage, message: message) { EmptyView() }
    }
}

#Preview("Empty state") {
    SuiEmptyState("No items yet", systemImage: "tray", message: "Items you add appear here.") {
        Button("Add an item") {}.buttonStyle(.bordered)
    }
}
