import ScshafeTokens
import SnapshotTesting
import SwiftUI
import UIKit

/// The variants every component state is rendered in (docs/design.md, 8): light and
/// dark x default and an accessibility text size x standard and increased contrast.
struct SnapshotVariant {
    let name: String
    let traits: UITraitCollection

    static let all: [SnapshotVariant] = {
        var variants: [SnapshotVariant] = []
        for (styleName, style) in [("light", UIUserInterfaceStyle.light), ("dark", .dark)] {
            for (sizeName, size) in [("default", UIContentSizeCategory.large), ("ax3", .accessibilityExtraExtraExtraLarge)] {
                for (contrastName, contrast) in [("standard", UIAccessibilityContrast.normal), ("increased", .high)] {
                    variants.append(SnapshotVariant(
                        name: "\(styleName)-\(sizeName)-\(contrastName)",
                        traits: UITraitCollection(traitsFrom: [
                            UITraitCollection(userInterfaceStyle: style),
                            UITraitCollection(preferredContentSizeCategory: size),
                            UITraitCollection(accessibilityContrast: contrast),
                        ])
                    ))
                }
            }
        }
        return variants
    }()
}

/// Renders `view` once per variant at iPhone width, with the page background behind it.
/// References are recorded on the CI runner and compared there (the pinned simulator).
@MainActor
func assertVariants<V: View>(
    _ view: V,
    height: CGFloat = 700,
    variants: [SnapshotVariant] = SnapshotVariant.all,
    drawInWindow: Bool = false,
    file: StaticString = #filePath,
    testName: String = #function,
    line: UInt = #line
) {
    for variant in variants {
        assertSnapshot(
            of: view.padding().frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                .background(SuiColor.bg),
            as: .image(
                drawHierarchyInKeyWindow: drawInWindow,
                perceptualPrecision: 0.98,
                layout: .fixed(width: 390, height: height),
                traits: variant.traits
            ),
            named: variant.name,
            file: file,
            testName: testName,
            line: line
        )
    }
}
