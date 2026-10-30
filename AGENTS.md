# scshafe-ios agent notes

- The SCSHAFE iOS component library: one Swift package (iOS 26 floor) of
  SwiftUI design tokens generated from `@scshafe/ui`'s registry and shared
  components (`Sui`-prefixed) for homemesh, parley, mailroom-ios and
  jobtrack-ios. The iOS sibling of scshafe-ui (web) and scshafe-qt (Qt/QML):
  keep names, tones and rules in parity with them. `docs/brief.md` is fixed;
  `docs/design.md` is the designer's (the first PR), kept in step with the
  code. `docs/research.md` is background. Build nothing past the skeleton
  until the owner accepts the design.
- Tokens: `tools/gen_tokens.py` (a port of scshafe-qt's) reads the registry
  into the committed snapshot `tokens/sui-tokens.json` and generates the
  Swift. Never edit the snapshot or a generated file by hand; refresh from a
  fresh clone of scshafe-ui at a release tag (`--refresh --from DIR`), and
  change the snapshot and the generated files in one commit.
- This machine has no Xcode: `./scripts/verify` (token `--check` and the
  Python tests) runs here; the Swift build and tests run in CI's `ios` job on
  `macos-26`. Wait for both CI jobs before merging.
- Public, MIT. No machine-local paths, account e-mail addresses, tailnet
  names (write `<tailnet>`), hostnames or credentials in the repository, its
  issues, its PRs or its CI logs; `tests/test_repository.py` enforces paths,
  e-mail addresses and tailnet names. No application-specific names or
  endpoints in the library.
- Changing a consumer app (homemesh, parley, mailroom-ios, jobtrack-ios) is
  that app's agent's work: file an agent request or ask the owner.

<!-- scshafe-dev:begin landing -->
## Verify and landing

Managed by scshafe-dev: `dev adopt` and `dev update` refresh this section from `dev.toml`; change `dev.toml`, not these lines.

Before finishing, both of these must pass:

```sh
./scripts/verify
dev check .
```

How a change lands:

1. Work on a branch and open a PR.
2. Run the two commands above. If the repository is private, GitHub Actions does not run for it: verify locally and say in the PR what you ran. If it is public, wait for CI to be green.
3. Merge your own PR with a merge commit, one change at a time: `gh pr merge <N> --merge --subject "Merge #<N>: <title>"`. Never squash or rebase (both are off on the repository), and pass `--subject`: `gh pr merge` does not make the `Merge #N: <title>` subject by itself.

The project's agent may merge its own PR and push `main`; there is no approval gate.
<!-- scshafe-dev:end landing -->
