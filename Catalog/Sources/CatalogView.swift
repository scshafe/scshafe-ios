import ScshafeComponents
import ScshafeTokens
import SwiftUI

private enum Appearance: String, CaseIterable, Identifiable {
    case system, light, dark
    var id: Self { self }
    var scheme: ColorScheme? {
        switch self {
        case .system: nil
        case .light: .light
        case .dark: .dark
        }
    }
}

struct CatalogView: View {
    @State private var appearance = Appearance.system
    @State private var textSize = DynamicTypeSize.large
    @State private var solid = false
    @State private var toast: SuiToastItem?
    @State private var load = SuiLoadState<[String]>.loading("Loading items")
    @State private var tapped = 0

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: SuiSpace.xl) {
                    controls
                    tones
                    banners
                    glass
                    feedback
                    loadable
                    text
                }
                .padding(SuiSpace.lg)
            }
            .background(SuiColor.bg)
            .navigationTitle("Catalog")
        }
        .tint(SuiColor.accent)
        .preferredColorScheme(appearance.scheme)
        .dynamicTypeSize(textSize)
        .environment(\.suiTransparency, solid ? .reduced : .automatic)
        .suiToast($toast)
    }

    private func section<Content: View>(_ title: String, @ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: SuiSpace.md) {
            Text(title).suiText(.heading)
            content()
        }
    }

    private var controls: some View {
        section("Environment") {
            Picker("Appearance", selection: $appearance) {
                ForEach(Appearance.allCases) { Text($0.rawValue.capitalized).tag($0) }
            }
            .pickerStyle(.segmented)
            Picker("Text size", selection: $textSize) {
                Text("Default").tag(DynamicTypeSize.large)
                Text("Large").tag(DynamicTypeSize.xxxLarge)
                Text("Accessibility").tag(DynamicTypeSize.accessibility3)
            }
            .pickerStyle(.segmented)
            Toggle("Solid surfaces (reduced transparency)", isOn: $solid)
        }
    }

    private var tones: some View {
        section("Tones and chips") {
            ViewThatFits(in: .horizontal) {
                HStack { toneChips }
                VStack(alignment: .leading) { toneChips }
            }
            ViewThatFits(in: .horizontal) {
                HStack { bucketChips }
                VStack(alignment: .leading) { bucketChips }
            }
        }
    }

    @ViewBuilder private var toneChips: some View {
        ForEach(SuiTone.allCases, id: \.self) { SuiChip($0.rawValue.capitalized, tone: $0) }
    }

    @ViewBuilder private var bucketChips: some View {
        ForEach(SuiBucket.allCases, id: \.self) { SuiChip($0.colorName.capitalized, bucket: $0) }
    }

    private var banners: some View {
        section("Banners") {
            SuiBanner("Saved", tone: .ok)
            SuiBanner("Heads up", tone: .warn, message: "Two rooms are not placed yet.", onDismiss: {})
            SuiBanner("Could not save", tone: .danger, message: "Check the connection and try again.") {
                Button("Retry") {}.buttonStyle(.bordered)
            }
        }
    }

    private var glass: some View {
        section("Glass: controls and the floating layer only") {
            ZStack {
                RoundedRectangle(cornerRadius: SuiRadius.lg, style: .continuous)
                    .fill(SuiBucket.one.fill)
                SuiGlassContainer(spacing: SuiSpace.md) {
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: SuiSpace.md) { glassButtons }
                        VStack(spacing: SuiSpace.md) { glassButtons }
                    }
                    .padding(SuiSpace.lg)
                }
            }
        }
    }

    @ViewBuilder private var glassButtons: some View {
        Button("Back") { tapped += 1 }.suiButtonStyle(.glass)
        Button("Save") { tapped += 1 }.suiButtonStyle(.prominent)
        Button("Delete") { tapped += 1 }.suiButtonStyle(.destructive)
    }

    private var feedback: some View {
        section("Toasts and haptics") {
            Button("Show an undo toast") {
                toast = SuiToastItem("Moved to Archive", tone: .ok, undo: { tapped += 1 })
            }
            Button("Show an error toast") {
                toast = SuiToastItem("Could not send", tone: .danger)
            }
            Text("Undo or selection counted: \(tapped)").suiText(.caption)
                .suiHaptic(.selection, trigger: tapped)
        }
        .buttonStyle(.bordered)
    }

    private var loadable: some View {
        section("Loading, empty, error, content") {
            Picker("State", selection: Binding(get: { stateIndex }, set: { setState($0) })) {
                Text("Loading").tag(0)
                Text("Empty").tag(1)
                Text("Error").tag(2)
                Text("Content").tag(3)
            }
            .pickerStyle(.segmented)
            SuiLoadable(
                load,
                errorTitle: "Could not load",
                retry: { setState(0) },
                empty: { SuiEmptyState("No items yet", systemImage: "tray", message: "Items you add appear here.") }
            ) { items in
                VStack(alignment: .leading) { ForEach(items, id: \.self) { Text($0) } }
            }
        }
    }

    private struct Failure: LocalizedError {
        var errorDescription: String? { "The connection was lost." }
    }

    private var stateIndex: Int {
        switch load {
        case .loading: 0
        case .empty: 1
        case .failed: 2
        case .content: 3
        }
    }

    private func setState(_ index: Int) {
        switch index {
        case 0: load = .loading("Loading items")
        case 1: load = .empty
        case 2: load = .failed(Failure())
        default: load = .content(["First row", "Second row", "Third row"])
        }
    }

    private var text: some View {
        section("Text roles") {
            ForEach(SuiTextRole.allCases, id: \.self) { role in
                Text("\(String(describing: role)): the quick brown fox").suiText(role)
            }
        }
    }
}
