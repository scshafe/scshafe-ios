# scshafe-ios

The SCSHAFE iOS component library: a Swift package of shared SwiftUI design
tokens and components for the SCSHAFE iOS apps. It is the iOS sibling of
[scshafe-ui](https://github.com/scshafe/scshafe-ui) (web, and the source of
the design tokens) and [scshafe-qt](https://github.com/scshafe/scshafe-qt)
(Qt/QML). iOS 26 and later; light and dark follow the system.

Status: pre-0.1. The design (`docs/design.md`) is accepted; the milestones in
it are built one PR each. Tokens, tones and text roles are generated (M1).

- Brief: [docs/brief.md](docs/brief.md). Research: [docs/research.md](docs/research.md).
- `Package.swift`: the products `ScshafeTokens` (generated tokens) and
  `ScshafeComponents` (styles and components); provisional names.
- `tokens/sui-tokens.json`: the committed snapshot of the `@scshafe/ui`
  token registry (0.9.0), the same schema as scshafe-qt's.
- `tools/gen_tokens.py`: keeps the snapshot and the generated Swift in step
  with the registry (`--refresh --from <scshafe-ui checkout>`, `--check`).

## Verify

```sh
./scripts/verify    # token --check and the Python tests (any OS, no Xcode needed)
```

CI runs the same on Linux, and builds and tests the package for an iOS
simulator on macOS (`.github/workflows/ci.yml`).

## License

MIT (`LICENSE`).
