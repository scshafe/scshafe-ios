# scshafe-ios design

Status: **proposed**, for the owner's acceptance. Nothing past the skeleton is
built until the owner accepts this design and settles the
[Owner decisions](#owner-decisions). `docs/brief.md` is fixed and wins over
this file; `docs/research.md` (2026-10-30) is background. Where this design
leans on the research's claims that the research itself marked unverified,
the design says so and puts the check in a milestone.

## 1. Goals and non-goals

One Swift package of SwiftUI design tokens and the shared "feedback kit"
components for homemesh, parley, mailroom-ios and jobtrack-ios, in parity with
scshafe-ui (web) and scshafe-qt (Qt/QML). Parity means the same token names,
the same five status tones with the same meanings, and the same rules.

Not in this design's scope: Pocket ID sign-in (v0.2, its own product), app
icons, screens (homemesh's plan screen, the house hub), and anything specific
to one app. Those are the apps' work.

## 2. Package layout and names

```
Package.swift                    swift-tools-version 6.2, iOS 26 only
Sources/ScshafeTokens/           generated; no views
  SuiTokens.generated.swift      colours, space, radius, motion, shadow
  SuiNative.generated.swift      tones, buckets, tone alphas, text roles
Sources/ScshafeComponents/       hand-written
  Tone/  Glass/  Buttons/  Chip/  Banner/  EmptyState/  Toast/  Loadable/  Haptics/
Tests/ScshafeTokensTests/        token values against the snapshot
Tests/ScshafeComponentsTests/    logic tests + snapshot tests
Catalog/                         XcodeGen app (see 9); depends on the package by path
tokens/sui-tokens.json           committed snapshot (schema 1)
tools/gen_tokens.py              snapshot reader and Swift emitter
```

- **Products:** keep the provisional `ScshafeTokens` and `ScshafeComponents`.
  Consumers write `import ScshafeComponents` (and `import ScshafeTokens` when
  they need a raw token). `ScshafeComponents` does **not** re-export
  `ScshafeTokens` (`@_exported` is underscored API). v0.2 adds `ScshafeAuth` as
  a third product; nothing in v0.1 anticipates it.
- **Prefix:** every public type is `Sui…`; modifiers are `.sui…`.
- **Language mode:** Swift 6 language mode for both targets (tools 6.2). A
  Swift 6 module is consumable from an app still in Swift 5 mode, because the
  mode is per module. Public API is `@MainActor` where it touches views;
  token namespaces are `Sendable` value types and need no isolation. The
  research left the mode unverified; M1 confirms it builds against the
  consumers' settings (homemesh builds with complete strict concurrency).
- **No third-party runtime dependency.** The only dependency is
  swift-snapshot-testing, on the test target.

## 3. Token pipeline

```
scshafe-ui registry (tag v0.9.0)
   -- node, tools/gen_tokens.py --refresh --from DIR -->  tokens/sui-tokens.json
   -- tools/gen_tokens.py (stdlib Python)              -->  Sources/ScshafeTokens/*.generated.swift
```

- The snapshot half is already in the skeleton (schema 1, `registryHash`,
  source version, file sha256, commit). The Swift emitter is milestone M1.
- `--check` (in `./scripts/verify`, so on `ubuntu-latest` and on this
  machine) fails when the snapshot is invalid or a generated file differs
  from what the generator would write. Generated files carry a header with the
  source version and registry hash, and are never edited by hand.
- **No local scshafe-ui is ever read implicitly.** `--refresh` needs
  `--from DIR` or `$SCSHAFE_UI_DIR` and checks the version in DIR against the
  release asked for, as the skeleton already does.
- A token bump is one commit: snapshot and generated files together, with
  the new source version in the commit subject and the CHANGELOG.
- The Swift emitter emits **resolved** values: `var(--sui-blue)` aliases are
  followed and the alias is noted in the doc comment (`/// --sui-accent`).
- The question of *where* the snapshot comes from, and how a new release is
  noticed, is owner decision 2; colour delivery is owner decision 1. The rest
  of this section holds for either answer.

### 3.1 Token-to-Swift mapping

Names convert `--sui-text-strong` to `textStrong`. px becomes pt 1:1.
Registry categories (77 tokens in 0.9.0):

| Category (count) | Swift | Decision |
| --- | --- | --- |
| color (25) and surface, border (themed) | `SuiColor.<name>`, a `Color` that resolves light/dark | **Kept**, except the rows below |
| radius (6) | `SuiRadius.sm/md/base/lg/xl/pill: CGFloat` | Kept; use with `.rect(cornerRadius:style: .continuous)` |
| space (7) | `SuiSpace.none/xs/sm/md/lg/xl/xxl: CGFloat` | Kept |
| motion (3) | `SuiMotion.duration`, `.standard`, `.spring: Animation` | Kept. `ease`/`ease-spring` become `Animation.timingCurve(…)`; Reduce Motion uses the registry's `reducedMotionDuration` (0 s), i.e. the animation becomes `nil`, a cross-fade stays. |
| shadow (2 of 4) | `SuiShadow.card`, `.floating` (colour, radius, x, y) | Only `shadow` and `shadow-lg`. The solid fallback and the toast need them. `shadow-color` is folded in; `glass-shadow` dropped. |
| border: `line`, `border`, `border-strong`, `field-border` | `SuiColor` | Kept. `field-border` is the 3:1 boundary of a form control. |
| surface: `bg`, `panel`, `card`, `bg-elevated`, `surface-2`, `popover`, `field`, `tint`, `code-bg`, `backdrop` | `SuiColor` | Kept. `popover` is what glass becomes under the solid fallback. |
| `glass`, `glass-thick`, `glass-sheen`, `glass-edge`, `glass-highlight`, `glass-shadow`, `glass-blur`, `glass-saturate` (material) | none | **Dropped.** The OS renders real glass (`glassEffect`); a hand-tuned recipe would fight the user's Clear/Tinted setting and iOS 27's slider. The solid fallback is `popover` + `border-strong`. |
| `bg-hover`, `border-hover` | none | **Dropped.** No hover on iOS. Pressed states come from the button styles. |
| `focus-ring` | none | **Dropped.** System focus on iPad/keyboard. |
| `mono`, `chat-text-size` (font) | none | **Dropped.** Web font stacks. Mono is `Font.system(design: .monospaced)`. |
| `clamp-*` (6) | none | **Dropped.** Web fluid layout; iOS uses size classes. |

Accent: `SuiColor.accent` is `#0a4f99` light / `#6cb6ff` dark in 0.9.0 (brief
decision 3). Apps apply it with `.tint(SuiColor.accent)` at the root; the
library never smears it across glass.

### 3.2 Native-only tokens

As in scshafe-qt, a clearly delimited section of `gen_tokens.py` (the
"NATIVE-ONLY" section, the only place besides the generated files where a
colour or duration literal may appear) holds what the registry does not:

- **Tone helpers:** `toneTint = 0.12` (fill under tone text) and
  `toneBorder = 0.45`, from scshafe-qt (`TONE_TINT`, `TONE_BORDER`).
- **Buckets 1 to 8** (blue, teal, green, olive, amber, rust, rose, violet),
  base and text colour per theme, **copied verbatim** from scshafe-qt's
  `NATIVE_BUCKETS` so mailroom's bucket chips match the desktop app. The
  generator test re-checks scshafe-qt's contrast contracts (text 4.5:1 on its
  tint, base 3:1) for the iOS surfaces.
- **Text roles** (section 5) mapped to Dynamic Type.
- Nothing else. Any addition to this section is itself a design change.

scshafe-qt's two themes are the registry's two themes; iOS does not invent a
third. **Increased contrast** has no registry values. The design handles it by
rule, not by new colours (see 6.2): surfaces go opaque and borders move to
`border-strong`.

## 4. Tone system

`enum SuiTone: CaseIterable { neutral, info, ok, warn, danger }`, the names
and order of scshafe-ui and scshafe-qt (`statusTones`). Mapping to registry
colours (as scshafe-qt's `toneBase`/`toneText`): info = `tone-blue`,
ok = `tone-green`, warn = `tone-yellow`, danger = `tone-red`, neutral =
`muted`/`tint`/`line`.

```swift
SuiTone.ok.base      // dot, border (at toneBorder), tint (at toneTint)
SuiTone.ok.text      // text on the tint
SuiTone.ok.fill      // base at 12 %, or tint for neutral
SuiTone.ok.border
SuiTone.ok.symbol    // "checkmark.circle.fill"
SuiTone.ok.label     // "OK": the hidden/spoken prefix
SuiBucket.one ... .eight   // categorical; never used for status
```

Symbols are fixed, one per tone, and are part of the tone, not chosen per
call site: neutral `circle`, info `info.circle.fill`, ok
`checkmark.circle.fill`, warn `exclamationmark.triangle.fill`, danger
`xmark.octagon.fill`. A tone's colour is **always paired with its symbol**
(brief 6): there is no API that draws a tone colour without it, and
VoiceOver reads a spoken prefix ("Warning: …") that the app can localise
through the component's `toneLabel` parameter (default English). Buckets are
decoration for user-defined groups; a bucket chip carries the group's name, so
needs no symbol. Status and category never share a colour: the plan-canvas
lesson from the research (orange meant eight things).

## 5. Text roles

scshafe-ui has no type scale, so iOS maps scshafe-qt's `SuiText` variants to
Dynamic Type text styles (never fixed sizes):

| Role (scshafe-qt) | iOS | Colour |
| --- | --- | --- |
| display | `.largeTitle`, bold | `textStrong` |
| title | `.title2`, bold | `textStrong` |
| heading | `.title3`, bold | `textStrong` |
| subheading | `.headline` | `textStrong` |
| section | `.subheadline`, semibold | `muted` |
| label | `.footnote`, semibold | `muted` |
| body | `.body` | `text` |
| caption | `.footnote` | `muted` |
| small | `.caption` | `muted` |
| code | `.footnote`, monospaced | `text` |

`Text("…").suiText(.title)` applies font, colour and, for the heading roles,
the `.isHeader` accessibility trait. Upper-casing is not applied (iOS 26
section headers are no longer all caps). The design deliberately maps the
sizes by *role*, not by pixel, so the scale follows Apple. The pixel sizes the
web uses are not reproduced; if the owner wants exact pt parity that is a
design change.

## 6. Glass and its solid fallback

### 6.1 Doctrine (brief 8)

Glass only on controls and the floating layer; never on content. A card, row,
message, chip or banner is a solid surface (`card`, `panel`, `tint`). Glass
never sits on glass. A group of nearby glass elements shares one container.
`.regular` is the default; `.clear` is permitted only over media with a 35 %
dimming layer (HIG), and the library offers it only through an explicit
`SuiGlassStyle.clearOverMedia` that adds the dimming itself.

### 6.2 API

```swift
extension View {
    func suiGlass<S: Shape>(_ style: SuiGlassStyle = .regular,
                            in shape: S = Capsule(),
                            interactive: Bool = false) -> some View
}
struct SuiGlassContainer<Content: View>: View   // wraps GlassEffectContainer
```

`suiGlass` is the **only** call to `glassEffect` in the library (a repository
test greps for it). With the iOS 26 floor there is no `#available` and no
material fallback. It has one branch, the solid one:

| Condition | Result |
| --- | --- |
| default | system glass: `glassEffect(.regular, in: shape)` |
| Reduce Transparency, Increase Contrast, or forced `suiTransparency = .reduced` | solid `popover` fill, `border-strong` stroke (2 pt under Increase Contrast), `SuiShadow.floating` |

The system's own glass already adapts to these settings; the explicit solid
branch exists so that **our** surfaces behave identically in every state and
can be snapshot-tested. `suiTransparency` is an `@Entry` environment value
(`.automatic` / `.reduced`) mirroring scshafe-ui's `data-sui-transparency`;
`.automatic` reads `accessibilityReduceTransparency` and
`colorSchemeContrast`. It is also how tests force the state (system settings
cannot be set from a snapshot).

Button styles: `SuiButtonStyle.glass` and `.glassProminent` return the
system `.glass`/`.glassProminent` styles through the shim above so the solid
branch applies; a `.suiDestructive` variant tints with `SuiTone.danger`.
Apple's styles remain the right default for toolbars; the library adds styles
only for tone and for the solid branch, not for restyling.

Known risk, to check in M2 on a simulator: the research cites one
single-source report that a `Menu` inside a `GlassEffectContainer` broke the
morph on iOS 26.0–26.1. We target 26.5+, so we only note it.

## 7. Components

Common rules, enforced by tests where they can be: system text styles only;
every icon-only control takes a **required** `accessibilityLabel:` parameter
(it does not compile without one); minimum 44 × 44 pt hit target; animation
through `SuiMotion` and `nil` under Reduce Motion; strings come from the
caller (no application-specific words, and the library's own default English
strings, such as tone prefixes and "Retry", are overridable parameters);
colours only from tokens.

**API style.** SwiftUI style protocols (`ButtonStyle`, `LabelStyle`) for
things that restyle a system control (the glass button styles, a tone
`LabelStyle`); plain views for composite components (`SuiChip`, `SuiBanner`,
`SuiEmptyState`, `SuiToast`, `SuiLoadable`), because they have no system
control to style. This is the research's recommendation applied where it fits.

### 7.1 `SuiChip` (status pill)

```swift
SuiChip("On the plan", tone: .ok)                 // default symbol of the tone
SuiChip("Backlog", bucket: .three)                // category: dot + name
SuiChip("Failing", tone: .danger, systemImage: "wifi.slash")  // symbol override
```

Solid `fill` of the tone, `border`, `text`; capsule; text style `.caption`
semibold. Accessibility: one element, label "<tone prefix>, <title>"; not a
button; decorative symbol hidden. Replaces homemesh's `badge(_:_:)` and
parley's `TurnStateBadge`.

### 7.2 `SuiBanner`

Inline, persistent, solid (`card` with a tone-bordered leading edge): tone
symbol, `title`, optional `message`, optional action(s) and a dismiss button
(optional, labelled). `.suiBanner(item:)`-style presentation is not provided;
a banner is a view the screen places. VoiceOver reads "<prefix>, title,
message"; on appearance it posts an announcement (`.announcement`) for `warn`
and `danger` only. Replaces footnote status strings and red error text.

### 7.3 `SuiEmptyState`

A thin layer over `ContentUnavailableView`: `title`, `systemImage`,
`description`, optional action. Adds the token text roles and the tone
symbol option; adds nothing else. Search variant passes through to
`ContentUnavailableView.search`.

### 7.4 `SuiToast` and undo

```swift
.suiToast($toast)            // SuiToastItem?: message, tone, optional action
SuiToastItem("Moved to Archive", tone: .ok, undo: { … }, hold: .seconds(6))
```

The one floating, transient element, so it is the one thing besides controls
that carries glass (`suiGlass` in a capsule; solid under the fallback), placed
with `safeAreaInset`/`safeAreaBar` above the bottom bar. Behaviour: one toast
at a time (a new one replaces the old; its undo is not run); `hold` default 6 s
(mailroom's "undo for the hold"); the timer **pauses while VoiceOver is
running** and while the user is touching the toast, and with VoiceOver on an
undo toast never auto-dismisses before it was read; an Undo button is a real
`Button` (44 pt, labelled "Undo", plus the message as a hint). Posts an
announcement. Haptic: `SuiHaptics` for its tone. Under Reduce Motion it fades
instead of sliding.

### 7.5 `SuiLoadable`

```swift
enum SuiLoadState<Value> { case loading(String?), empty, failed(Error), content(Value) }
SuiLoadable(state, retry: { … }) { value in … }
    .suiEmpty { SuiEmptyState(…) }
```

Renders `ProgressView(label)` (a label is required; an unlabelled spinner is
what the research found in five places), `SuiEmptyState`, a `SuiBanner`-based
error with Retry (danger tone, localisable text from the caller), or the
content. Transitions with cross-fade; no layout jump (the loading and error
states use the same minimum height as the content area). It owns no
networking and no `@Observable` model: the state is a value the app computes.

### 7.6 `SuiHaptics`

A tiny layer over `sensoryFeedback(_:trigger:)`:
`.suiHaptic(.success, trigger: x)`, with the mapping fixed to Apple's
meanings: **outcome** `success`/`warning`/`error` for task results,
**selection** for value changes, **impact** for snapping. Haptics
complement, never replace, visual feedback, so the modifier is only offered on
views that also show state; `SuiToast` and `SuiBanner` call it for you (opt
out with a flag). No custom CoreHaptics patterns in v0.1.

## 8. Testing

- **Python** (`./scripts/verify`, runs here and on `ubuntu-latest`): snapshot
  schema, `--check` freshness of generated Swift, `tests/test_repository.py`
  privacy rules, and a new `tests/test_rules.py` (the scshafe-qt analogue):
  no colour or duration literal (`Color(`/`#xxxxxx`/`.seconds(` constant
  animation values) outside the generated files and the NATIVE-ONLY section;
  `glassEffect` appears only in `Glass/`; no `UIDesignRequiresCompatibility`.
- **Swift unit tests** (CI `ios` job): token values equal the snapshot (a
  generated test), tone and bucket helpers, the text-role table, toast
  timing with an injected clock, `SuiLoadState` transitions.
- **Snapshot tests**: pointfreeco's swift-snapshot-testing, a pinned version,
  on one pinned simulator, since references must be recorded and compared on
  the same device and OS. Variants per component state (owner decision 4):
  light/dark × default/accessibility text size × standard/increased contrast,
  plus `suiTransparency = .reduced` on the glass-bearing pieces. Snapshots
  are images, not view hierarchies, with a small perceptual tolerance. **Glass
  is kept to four reference images** (button, container, toast, solid
  fallback), because the OS glass rendering changes between OS versions and
  will churn; everything else is solid and cheap to keep.
- **Accessibility**: a test per component that the accessibility label
  and traits are set; Dynamic Type at the largest accessibility size must not
  clip (checked by the snapshot, not by assertion).
- The research's list of API names it could not verify (`MagnifyGesture`,
  swipe actions, `LabeledContentStyle`, snapshot trait names, whether SwiftPM
  accepts `v`-prefixed tags) is worked through in M1 and M2 by compiling
  against the SDK; the design uses none of the first three.

## 9. Catalogue

A `Catalog/` XcodeGen app (`project.yml`, generated project not committed),
a single-screen gallery of tokens, tones and components in all states, with a
toggle for dark mode, Dynamic Type size and `suiTransparency`. It depends on
the package by local path and is never in a consumer's dependency graph.
SwiftUI `#Preview` blocks accompany every component in the package itself
(free, no app needed). Whether CI builds the Catalog is owner decision 3.

## 10. CI

Already in `.github/workflows/ci.yml`: `verify` (`./scripts/verify` on
`ubuntu-latest`) and `ios` (`macos-26`, Xcode 26.6 via `xcode-select`,
`xcodebuild test -scheme scshafe-ios-Package` on a simulator). Design
changes to it, all in M1:

- Pin the simulator by name and OS (owner decision 6) instead of the
  newest iPhone, so snapshots are reproducible.
- Cache nothing that costs money; GitHub-hosted runners only. The package's
  one test dependency is resolved by SwiftPM at the pinned version.
- Add the Catalog build (`xcodebuild build`, no tests, after
  `brew install xcodegen` pinned by version) if decision 3 says so.
- An Xcode 27 leg is **not** added now: GitHub's `macos-26` image has no
  stable Xcode 27 (research, 13 Oct 2026). When one exists it is an
  allowed-to-fail matrix leg first, promoted after one green release.
- A scheduled (weekly) job compares `tokens/sui-tokens.json` with the latest
  scshafe-ui release and opens an issue on drift if the owner approves
  decision 2.
- All third-party actions pinned by SHA, as the existing file does.

## 11. Releases

SemVer, annotated tags on `main`, never moved or deleted; a CHANGELOG entry
per release that records the scshafe-ui version the tokens come from (also in
the generated header). While 0.x, a minor may break. Apps pin
`.upToNextMinor(from: "0.1.0")` in `Package.swift` or XcodeGen `packages:`.
Tag style (`v0.1.0` or `0.1.0`) is owner decision 5; SwiftPM resolves both
styles of semantic-version tag, which M1 proves by resolving the tag in the
Catalog.

## 12. Adoption plan

Per the brief: homemesh first, parley second, both before `0.1.0`; mailroom-ios
and jobtrack-ios start on 0.1. Changing an app is that app's agent's work, so
each step is an **agent request** (or an owner ask) with a precise list, never
a PR from here.

1. **homemesh** (iOS 17 → 26, its own PR first): replace `badge(_:_:)` with
   `SuiChip`; footnote status strings with `SuiBanner` / `SuiToast` (with the
   revision-based undo it already has) and `SuiHaptics`; its five bare
   `ProgressView()` loaders with `SuiLoadable`; the empty house list with
   `SuiEmptyState`; `GlassBackground` with `suiGlass` (and shrink the scan
   overlay to controls only); set `.tint(SuiColor.accent)`.
2. **parley:** `TurnStateBadge` → `SuiChip`; red error text → `SuiBanner`;
   the plain empty conversation → `SuiEmptyState`; haptics on send, dictation
   start/stop and reply ready; `.bar` strips removed (the app's work, not the
   library's).
3. Anything a second consumer does not need is not extracted (scshafe-ui's
   rule: two consumers, byte-identical render, no reverse imports). If
   parley and homemesh diverge on a component's shape, it stays in v0.1 only
   with the shape both can use, otherwise it moves to 0.2.

## 13. Milestones

| M | Deliverable | Gate |
| --- | --- | --- |
| M0 | This design accepted; owner decisions answered | the owner |
| M1 | Swift emitter and generated tokens, `SuiTone`/buckets/text roles, `test_rules.py`, CI simulator pin | `./scripts/verify`, `dev check .`, both CI jobs |
| M2 | `suiGlass`, container, button styles; `SuiChip`; `SuiBanner`; snapshot harness | both CI jobs |
| M3 | `SuiEmptyState`, `SuiToast`, `SuiLoadable`, `SuiHaptics`; Catalog app | both CI jobs; Catalog builds |
| M4 | homemesh adoption request filed, adopted against a pre-release tag (`0.1.0-rc.1`) | homemesh agent's PR green |
| M5 | parley adoption, same | parley agent's PR green |
| M6 | `0.1.0`: CHANGELOG, tag, README | owner reads the Catalog; both consumers pinned |
| later | v0.2: `ScshafeAuth` after a line-by-line diff of parley's and homemesh's sign-in code | not before M6 |

## Owner decisions

Recommended answer first. Nothing below is decided by this PR.

### 1. Colour delivery

1. **Generated Swift code (recommended).** Each themed token is a `Color`
   built from a `UIColor` dynamic provider keyed on `userInterfaceStyle`
   (and, for the solid fallback, `accessibilityContrast`). Diffs read line by
   line in review; the emitter is checked on Linux by `--check` like every
   other generated file; there are no string lookups to mistype. Cost: no
   Xcode colour-set UI, and a hand-rolled increased-contrast rule.
2. **Generated asset catalog** (`.xcassets` in the package, `Color("name",
   bundle: .module)`). Apple's native path for contrast variants. Cost: JSON
   diffs are noisy, names are strings, and the registry has no
   increased-contrast values to fill that slot anyway, so it would hold
   duplicated light/dark values.

### 2. Token source and drift

1. **scshafe-ui publishes the snapshot JSON as a release artefact; scshafe-ios
   and scshafe-qt read it (recommended).** Ends the "three readers" drift the
   research found; a weekly CI job here opens an issue when scshafe-ui has a
   newer release than the snapshot, and CI compares the snapshot with the
   release asset by hash. Needs a change in scshafe-ui (not ours to make: an
   agent request or the owner), so until then the interim reader stays.
2. **Each repository keeps its own reader** (today). No cross-repo work, but
   drift stays possible and has already happened twice (Qt is at 0.4.1).
3. Reader per repo *plus* the weekly drift job here only. A middle path that
   needs nothing from scshafe-ui.

### 3. Catalogue app

1. **Both (recommended):** `#Preview` blocks in the package from M2 and the
   XcodeGen `Catalog/` app from M3, with CI building (not running) it so it
   cannot rot. About two minutes on the macOS job, free.
2. Previews only. Cheapest, but no on-device Dynamic Type/transparency
   toggles and nothing for the owner to run before accepting 0.1.0.
3. Catalog app, not built in CI. Saves minutes; it will rot.

### 4. Snapshot testing

1. **swift-snapshot-testing at one exact version, iPhone 17 on iOS 26.5, light
   and dark × default and an accessibility text size × standard and increased
   contrast, plus forced reduced transparency for glass pieces, and four
   glass references (recommended).** The exact release is chosen in M1 from
   the releases at least two weeks old (the research did not verify the
   current version). The `macos-26` image has the iOS 26.5 runtime.
2. Same, without increased contrast. Fewer images; misses the variant Apple
   asks for.
3. No image snapshots; logic and accessibility tests only. No dependency and
   no reference churn on OS updates, but visual regressions go unseen.

### 5. Release and tag scheme

1. **Annotated `v0.1.0` tags (recommended)**, matching scshafe-ui and
   scshafe-qt. SwiftPM reads semantic-version tags with or without a `v`
   (the research flags this unverified; M1 resolves the tag from the Catalog
   before M6 relies on it). A CHANGELOG, Keep-a-Changelog style; apps pin
   `upToNextMinor` while 0.x.
2. Bare `0.1.0` tags. Zero SwiftPM doubt; breaks the family's tag convention.

### 6. CI

1. **`macos-26`, Xcode 26.6 pinned, the simulator pinned by name and OS
   (iPhone 17, iOS 26.5), no Xcode 27 leg until the image has a stable one,
   then an allowed-to-fail leg (recommended).** Python checks stay on
   `ubuntu-latest`.
2. Newest installed runtime (today's behaviour). Never pinned; snapshots
   would shift when the image updates.
3. Add the Xcode 27 leg now as a beta leg. Earlier warning, but flaky and,
   per the research, no stable image exists yet.

### 7. Smaller choices I made and will change on request

These are in the design and are not blocking; say so if you disagree.

- Keep the product names `ScshafeTokens` / `ScshafeComponents`; no re-export.
- Swift 6 language mode in the package.
- Drop all `glass-*` / `material`, hover and `clamp-*` tokens (3.1).
- Text roles follow Dynamic Type styles, not the web's pixel sizes (5).
- Toast hold 6 s, pausing under VoiceOver (7.4).
- Adoption is requested of the app agents, not done from this repository (12).
