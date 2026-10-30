// Placeholder until the design (docs/design.md) is accepted: the tokens that
// tools/gen_tokens.py generates from tokens/sui-tokens.json replace it.

/// Where this package's design tokens come from.
public enum SuiTokenSource {
    /// The @scshafe/ui token registry the tokens are generated from.
    public static let package = "@scshafe/ui"
    /// The registry release of the committed snapshot (tokens/sui-tokens.json).
    /// tests/test_tokens.py keeps the two equal.
    public static let version = "0.9.0"
}
