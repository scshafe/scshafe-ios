# Adopting scshafe-ios

For an app's agent or developer. The design is `docs/design.md`; this is the
short path from "add the package" to "replace the hand-rolled version".

## Add the package

iOS 26 is the floor for the library and for the app. The package is public.

XcodeGen (`project.yml`):

```yaml
packages:
  ScshafeIOS:
    url: https://github.com/scshafe/scshafe-ios
    exactVersion: 0.1.0-rc.1      # a release candidate; from 0.1.0: upToNextMinorVersion: 0.1.0
targets:
  YourApp:
    dependencies:
      - package: ScshafeIOS
        product: ScshafeComponents
      - package: ScshafeIOS
        product: ScshafeTokens    # only where you use a raw token
```

Swift Package Manager: `.package(url: "https://github.com/scshafe/scshafe-ios", .upToNextMinor(from: "0.1.0"))`.
While the library is 0.x, a minor release may break: pin up to the next minor.
The package's own test dependency (swift-snapshot-testing) is not linked into
your app.

## Set up once

```swift
import ScshafeComponents
import ScshafeTokens

WindowGroup {
    RootView()
        .tint(SuiColor.accent)          // scshafe-ui's accent, light and dark
        .suiToast($model.toast)         // one place for toasts
}
```

Appearance follows the system. Do not force a colour scheme.

## What replaces what

| You have | Use |
| --- | --- |
| a hand-rolled status badge | `SuiChip("On the plan", tone: .ok)` (a tone's symbol is always drawn with its colour) |
| a footnote or red error text | `SuiBanner("Could not save", tone: .danger, message: ...) { Button("Retry") ... }` |
| "Saved." text, a status string | `model.toast = SuiToastItem("Saved", tone: .ok)`; with Undo: `SuiToastItem("Deleted", tone: .ok, undo: { ... })` |
| a bare `ProgressView()`, an if/else on loaded/empty/failed | `SuiLoadable(state, errorTitle: ..., retry: ..., empty: { SuiEmptyState(...) }) { value in ... }` |
| a plain-text empty list | `SuiEmptyState("No houses yet", systemImage: "house", message: ...)` |
| custom `.ultraThinMaterial` or a glass card | `.suiGlass(in: shape)` on a control or floating element only, in a `SuiGlassContainer` when several sit together |
| a custom button over the camera or a map | `.suiButtonStyle(.glass / .prominent / .destructive)` |
| `.font(.footnote)` everywhere | `.suiText(.caption)` and the other roles (Dynamic Type text styles) |
| literal colours | `SuiColor.*`; categories (zones, labels) use `SuiBucket`, never a status tone |
| haptic calls, or none | `.suiHaptic(.success, trigger: value)`; toasts and errors play their tone's haptic |

## Rules the library holds you to

- Glass only on controls and the floating layer. Cards, rows, messages and banners are solid.
- Colour is never the only signal: tones come with symbols, and `SuiChip` / `SuiBanner` speak their tone.
- Pass strings in (and localise them): the library has no application names. The few English defaults ("Undo", "Retry", "Dismiss", the tone words) have parameters.
- Every icon-only control needs an accessibility label.
- Do not add colour or duration literals; add a token upstream (scshafe-ui) instead.
- Do not change the library from an app. File an issue on `scshafe/scshafe-ios`
  (the owner or the project's agent triages) if a component does not fit.

## homemesh (first adopter, raised from iOS 17 to 26)

`badge(_:_:)` to `SuiChip`; footnote `status = "..."` strings to `SuiBanner` and
`SuiToast` (with the revision-based Undo it already has) and `.suiHaptic`; the
five bare loaders to `SuiLoadable`; the empty house list to `SuiEmptyState`;
`GlassBackground` to `.suiGlass`, keeping glass on the scan overlay's small
controls only; `.tint(SuiColor.accent)`; map statuses onto tones by meaning
("on the plan" ok, "needs input" warn, "invalid" danger) and canvas categories
(zones, furniture) onto buckets.

## parley (second adopter, before 0.1.0)

`TurnStateBadge` to `SuiChip`; red error text to `SuiBanner`; the plain empty
conversation to `SuiEmptyState`; haptics on send, dictation start and stop and
reply ready; the composer's `.background(.bar)` strips removed (that is the
app's work, not the library's).

## See it

The Catalog app (`Catalog/project.yml`, XcodeGen) shows every token, tone and
component, with switches for appearance, text size and solid surfaces.
