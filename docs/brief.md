# scshafe-ios: the owner's brief

The SCSHAFE iOS component library: one Swift package of shared SwiftUI design
tokens and components for the owner's iOS apps. It is the iOS sibling of
[scshafe-ui](https://github.com/scshafe/scshafe-ui) (`@scshafe/ui`, the web
library and the token registry, dark glass theme) and
[scshafe-qt](https://github.com/scshafe/scshafe-qt) (the Qt/QML library, whose
`SuiTheme` is generated from the same registry by `tools/gen_tokens.py`).

The research behind this brief is `docs/research.md` (2026-10-30): an audit
of the four iOS apps, Apple's iOS 26 design language (Liquid Glass) and how
shared SwiftUI libraries are built. Where it differs from this brief, the
brief wins.

## Consumers

| App | Where | Today | Role |
| --- | --- | --- | --- |
| homemesh | the homemesh repository, `ios/` | iOS 17, raised to 26 | first adopter |
| parley | the parley repository, `ios/` | iOS 26 | second adopter, before 0.1.0 |
| mailroom-ios | its own repository | iOS 26 | greenfield consumer from 0.1 |
| jobtrack-ios | its own repository | iOS 26 | greenfield consumer from 0.1 |

## Owner decisions (2026-10-30)

These are fixed; the design builds on them.

1. **Name and licence.** `scshafe-ios`, a public repository, MIT licence.
   Swift types are prefixed `Sui` (as scshafe-qt's `SuiTheme`, `SuiChip`).
   The package ships a tokens product and a components product, provisionally
   `ScshafeTokens` and `ScshafeComponents` (`Package.swift`); the design may
   refine the module and product names.
2. **iOS 26 floor** for the library and for every app that uses it (homemesh
   is raised from iOS 17 to 26). So there is no pre-iOS-26 material fallback
   and no `#available(iOS 26, *)` shim. Glass must still become a solid
   surface under Reduce Transparency and Increase Contrast.
3. **Appearance follows the system.** Light and dark are both supported, each
   with scshafe-ui's accent for that theme (`#0a4f99` light, `#6cb6ff` dark
   in 0.9.0).
4. **Tokens are generated from `@scshafe/ui` 0.9.0**, the current release
   (tag `v0.9.0`), never from an older copy. The pipeline ports scshafe-qt's
   `gen_tokens.py`: a committed snapshot (`tokens/sui-tokens.json`, the same
   schema 1 as scshafe-qt's) and a `--check` that fails CI when the snapshot
   or a generated file is stale. The snapshot and the generator's snapshot
   half are already in this skeleton (`tools/gen_tokens.py`); the Swift
   emitter waits for the colour-delivery decision below.
5. **Adoption order.** homemesh adopts first, then parley, both before the
   `0.1.0` tag, so every v0.1 component has two real consumers (scshafe-ui's
   extraction rule: "two real consumers, byte-identical render, no
   reverse-imports").
6. **v0.1 scope** (the research report's "feedback kit"):
   - the generated tokens: colours, space, radius, motion;
   - five status tones, `neutral`, `info`, `ok`, `warn`, `danger`, the same
     names as scshafe-ui and scshafe-qt; a tone's colour is always paired
     with a symbol (colour is never the only signal);
   - a glass helper and the glass button styles;
   - a chip / status pill;
   - a banner;
   - an empty state;
   - an undo toast;
   - a loading / error wrapper (loading, empty, error, content, retry);
   - haptics, following Apple's documented meanings.
7. **Not in v0.1:** Pocket ID sign-in is deferred to v0.2, as its own
   authentication product, after a line-by-line comparison of parley's and
   homemesh's sign-in code.
8. **Glass only on controls and the floating layer, never on content.**
   Cards, rows, messages and banners stay on solid surfaces (scshafe-ui's
   glass doctrine and Apple's "don't use Liquid Glass in the content layer").

## Rules

- **Public repository.** No machine-local paths, account e-mail addresses,
  tailnet names (write `<tailnet>`), hostnames or credentials in the
  repository, its issues, its PRs or its CI logs. `tests/test_repository.py`
  enforces the paths, e-mail addresses and tailnet names.
- **No application-specific names, endpoints or hosts** in the library. Apps
  pass their own strings in.
- **Tokens come only from the registry.** No colour or duration literals
  outside the generated file and the generator's native-only section (as
  scshafe-qt enforces with `tests/test_rules.py`). Never edit a generated
  file by hand; never read a local scshafe-ui checkout without checking it is
  at the intended release.
- **Accessibility is part of every component:** Dynamic Type (system text
  styles), VoiceOver labels (an icon-only control requires one), 44 pt
  targets, Reduce Motion, Reduce Transparency and Increase Contrast.
- **No service that costs money** without the owner's approval. CI uses
  GitHub-hosted runners only.

## Open questions for the design

The designer lists a recommendation for each in the design's "Owner
decisions" section, recommended answer first; the owner decides.

1. **Colour delivery:** a generated asset catalog in the package (Apple's
   path for light, dark and increased-contrast variants) or generated Swift
   code (for example dynamic `UIColor` providers), which diffs more clearly.
2. **Token source:** each consumer (scshafe-qt, scshafe-ios) reads
   scshafe-ui's registry with its own reader, or scshafe-ui publishes the
   snapshot JSON as a release artefact that both read. How a new scshafe-ui
   release is noticed, and whether CI compares the snapshot with the release.
3. **Catalogue app:** its shape (an XcodeGen app in the repository that
   depends on the package by local path, SwiftUI previews only, or both),
   and whether CI builds it.
4. **Snapshot testing:** the library (for example pointfreeco's
   swift-snapshot-testing) and its pinned version, the pinned simulator and
   OS, which variants are rendered (light and dark, an accessibility text
   size, increased contrast, reduced transparency), and how few glass
   snapshots to keep.
5. **Release and tag scheme:** SemVer with annotated tags as scshafe-ui and
   scshafe-qt do; whether Swift Package Manager accepts `v`-prefixed tags
   (`v0.1.0`) or needs bare ones (`0.1.0`); the CHANGELOG; how apps pin a 0.x
   release.
6. **CI:** the macOS job on `macos-26` with Xcode pinned (26.6 today, as
   homemesh and mailroom-ios pin it), the simulator destination, when an
   Xcode 27 leg is added; the token `--check` and the Python tests on
   `ubuntu-latest`.

The design also settles what the decisions above leave open: module and
product names, the Swift language mode, the token-to-Swift mapping
(namespaces, text roles mapped to Dynamic Type styles, which web-only tokens
such as `glass-blur` and the `clamp-*` layout tokens are dropped), the
native-only tokens (scshafe-qt's buckets 1 to 8 and tone helpers), the API
style (SwiftUI style protocols over wrapper views), and the milestones to
0.1.0, including the homemesh and parley adoption PRs.

## The designer's job (first PR)

1. Write `docs/design.md`: the package layout and names, the token pipeline
   and its Swift output, the tone system, glass and its solid fallback, each
   v0.1 component's API and accessibility contract, testing, the catalogue,
   CI, releases, the adoption plan for homemesh and parley, and milestones.
   List every decision the owner must make in an "Owner decisions" section,
   recommended answer first. Don't decide those yourself.
2. Keep `./scripts/verify` and `dev check .` passing, and CI green.
3. Build nothing past the skeleton until the owner accepts the design.
