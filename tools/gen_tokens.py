#!/usr/bin/env python3
"""Keep scshafe-ios's design tokens in step with @scshafe/ui's token registry.

A port of scshafe-qt's tools/gen_tokens.py (same snapshot, schema 1). Pipeline
(stdlib only; Node is needed only to read a registry):

    @scshafe/ui ./tokens export (lib/tokens.js) or src/tokens.ts
        -- node, --refresh -->  tokens/sui-tokens.json   (committed snapshot)
        -- this script     -->  the generated Swift sources (committed)

Colours are delivered as generated Swift (dynamic UIColor providers; owner
decision 1, docs/design.md). The generated files are Sources/ScshafeTokens/
*.generated.swift and one generated Swift test. --check validates the
snapshot, compares the generated files with what this script would write and,
when a registry is given, compares the snapshot with that registry.

Usage:
    python3 tools/gen_tokens.py                 # regenerate the outputs from the snapshot
    python3 tools/gen_tokens.py --refresh --from DIR
                                                # re-read the registry, rewrite snapshot + outputs
    python3 tools/gen_tokens.py --check         # fail if the snapshot or an output is stale

The registry is located with --from DIR, else $SCSHAFE_UI_DIR. DIR is a source
checkout of scshafe-ui at the release to use (for example a fresh
`git clone --depth 1 --branch v0.9.0 https://github.com/scshafe/scshafe-ui`)
or an installed package (node_modules/@scshafe/ui). Unlike scshafe-qt there is
no fallback to a sibling ../scshafe-ui checkout: a stale local checkout must
never be read by accident. --check says it skipped the registry comparison
when no registry is given (CI has none); --require-source turns the skip into
a failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "tokens" / "sui-tokens.json"
PACKAGE_NAME = "@scshafe/ui"
SNAPSHOT_SCHEMA = 1
TOKEN_KEYS = ("name", "light", "dark", "themed", "category", "role", "description")
CATEGORIES = {"color", "surface", "border", "shadow", "radius", "font", "space", "clamp", "motion", "material"}
ROLES = {None, "text", "surface", "overlay", "indicator", "decorative"}

_NODE_DUMP = r"""
const { pathToFileURL } = await import("node:url");
const m = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(JSON.stringify({
  tokens: m.SUI_TOKENS,
  reducedMotionDuration: m.SUI_REDUCED_MOTION_DURATION,
}));
"""


class GenError(Exception):
    pass


# --------------------------------------------------------------------------
# Registry extraction (Node)
# --------------------------------------------------------------------------


def _node_dump(file: Path) -> dict:
    cmd = ["node", "--no-warnings"]
    if file.suffix == ".ts":
        cmd.append("--experimental-strip-types")
    cmd += ["--input-type=module", "-e", _NODE_DUMP, str(file)]
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise GenError("node is required to read the registry (--refresh, or --check with a source)") from exc
    except subprocess.CalledProcessError as exc:
        raise GenError(f"node could not load {file}:\n{exc.stderr}") from exc
    raw = json.loads(out.stdout)
    tokens = [{key: tok.get(key) for key in TOKEN_KEYS} for tok in raw["tokens"]]
    return {"tokens": tokens, "reducedMotionDuration": raw["reducedMotionDuration"]}


def find_source(explicit: str | None) -> Path | None:
    for cand, label in ((explicit, "--from"), (os.environ.get("SCSHAFE_UI_DIR"), "$SCSHAFE_UI_DIR")):
        if not cand:
            continue
        if (Path(cand) / "package.json").is_file():
            return Path(cand).resolve()
        raise GenError(f"{label} {cand}: no package.json there")
    return None


def read_registry(src: Path) -> dict:
    pkg = json.loads((src / "package.json").read_text())
    if pkg.get("name") != PACKAGE_NAME:
        raise GenError(f"{src} is {pkg.get('name')!r}, not {PACKAGE_NAME}")
    export = pkg.get("exports", {}).get("./tokens", {})
    export_file = export.get("default") if isinstance(export, dict) else export
    files = []
    if export_file and (src / export_file).is_file():
        files.append(src / export_file)
    if (src / "src" / "tokens.ts").is_file():
        files.append(src / "src" / "tokens.ts")
    if not files:
        raise GenError(f"{src}: neither the ./tokens export nor src/tokens.ts exists")
    dumps = [_node_dump(f) for f in files]
    if len(dumps) == 2 and dumps[0] != dumps[1]:
        raise GenError(f"{files[0]} differs from {files[1]}: the built export is stale")
    used, data = files[0], dumps[0]
    source = {
        "package": PACKAGE_NAME,
        "version": pkg["version"],
        "file": used.relative_to(src).as_posix(),
        "fileSha256": hashlib.sha256(used.read_bytes()).hexdigest(),
    }
    if (src / ".git").exists():
        try:
            source["commit"] = subprocess.run(
                ["git", "-C", str(src), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            pass
    snap = {
        "schema": SNAPSHOT_SCHEMA,
        "source": source,
        "registryHash": registry_hash(data),
        "reducedMotionDuration": data["reducedMotionDuration"],
        "tokens": data["tokens"],
    }
    validate(snap)
    return snap


def registry_hash(data: dict) -> str:
    canonical = {"reducedMotionDuration": data["reducedMotionDuration"], "tokens": data["tokens"]}
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode()).hexdigest()


# --------------------------------------------------------------------------
# The snapshot
# --------------------------------------------------------------------------


def validate(snap: dict) -> None:
    """Raise GenError unless the snapshot is well formed and every value parses."""
    if snap.get("schema") != SNAPSHOT_SCHEMA:
        raise GenError(f"unknown snapshot schema {snap.get('schema')!r}")
    src = snap.get("source", {})
    if src.get("package") != PACKAGE_NAME or not src.get("version"):
        raise GenError(f"snapshot source is {src!r}, not a {PACKAGE_NAME} release")
    if registry_hash(snap) != snap.get("registryHash"):
        raise GenError("registryHash does not match the tokens (hand-edited?)")
    names = [tok.get("name") for tok in snap["tokens"]]
    if len(set(names)) != len(names):
        raise GenError("duplicate token names")
    by_name = {tok["name"]: tok for tok in snap["tokens"]}
    for tok in snap["tokens"]:
        name = tok["name"]
        if set(tok) != set(TOKEN_KEYS):
            raise GenError(f"{name}: keys {sorted(tok)}")
        if not re.fullmatch(r"--sui-[a-z0-9-]+", name):
            raise GenError(f"{name}: not a --sui-* custom property")
        if tok["category"] not in CATEGORIES:
            raise GenError(f"{name}: unknown category {tok['category']!r}")
        if tok.get("role") not in ROLES:
            raise GenError(f"{name}: unknown role {tok.get('role')!r}")
        for theme in ("light", "dark"):
            parsed = parse_value(tok[theme])
            if isinstance(parsed, Ref) and parsed.name not in by_name:
                raise GenError(f"{name} ({theme}): unknown reference {parsed.name}")
            if tok["category"] in ("color", "surface", "border") and not isinstance(resolve(parsed, by_name, theme), Rgba):
                raise GenError(f"{name} ({theme}): {tok[theme]!r} is not a colour")
            if tok["category"] == "shadow" and not isinstance(resolve(parsed, by_name, theme), (Rgba, tuple)):
                raise GenError(f"{name} ({theme}): {tok[theme]!r} is not a shadow or a colour")


def load_snapshot(path: Path = SNAPSHOT) -> dict:
    try:
        snap = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise GenError(f"{path}: {exc}") from exc
    try:
        validate(snap)
    except GenError as exc:
        raise GenError(f"{path}: {exc}") from exc
    return snap


def dump_snapshot(snap: dict) -> str:
    return json.dumps(snap, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------
# CSS value parsing (for the emitter and the tests)
# --------------------------------------------------------------------------

_HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGBA = re.compile(r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)$")
_VAR = re.compile(r"^var\((--sui-[a-z0-9-]+)\)$")
_PX = re.compile(r"^(-?[\d.]+)px$")
_TIME = re.compile(r"^([\d.]+)(ms|s)$")
_PERCENT = re.compile(r"^([\d.]+)%$")
_BEZIER = re.compile(r"^cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)$")
_SHADOW = re.compile(
    r"^(-?[\d.]+)(?:px)?\s+(-?[\d.]+)(?:px)?\s+([\d.]+)(?:px)?(?:\s+(-?[\d.]+)(?:px)?)?\s+(rgba?\(.*\)|#[0-9a-fA-F]+)$"
)


@dataclass(frozen=True)
class Rgba:
    r: int
    g: int
    b: int
    a: float


@dataclass(frozen=True)
class Shadow:
    x: float
    y: float
    blur: float
    spread: float
    color: Rgba


@dataclass(frozen=True)
class Ref:
    name: str


@dataclass(frozen=True)
class Bezier:
    x1: float
    y1: float
    x2: float
    y2: float


def parse_color(value: str) -> Rgba | None:
    value = value.strip()
    if m := _HEX.match(value):
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return Rgba(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    if m := _RGBA.match(value):
        a = m.group(4)
        return Rgba(int(m.group(1)), int(m.group(2)), int(m.group(3)), float(a) if a is not None else 1.0)
    return None


def _split_layers(value: str) -> list[str]:
    """Split a CSS list on top-level commas (not those inside parentheses)."""
    layers, depth, start = [], 0, 0
    for i, ch in enumerate(value):
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            layers.append(value[start:i].strip())
            start = i + 1
    layers.append(value[start:].strip())
    return layers


def _parse_shadow(value: str) -> Shadow | None:
    if m := _SHADOW.match(value):
        color = parse_color(m.group(5))
        if color is not None:
            return Shadow(float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0), color)
    return None


def parse_value(value: str):
    """Return Ref | Rgba | tuple[Shadow, ...] | Bezier | ("px"|"ms"|"percent", n) | ("string", s)."""
    value = value.strip()
    if m := _VAR.match(value):
        return Ref(m.group(1))
    if (c := parse_color(value)) is not None:
        return c
    if m := _PX.match(value):
        return ("px", _num(m.group(1)))
    if m := _TIME.match(value):
        return ("ms", _num(str(float(m.group(1)) * (1000 if m.group(2) == "s" else 1))))
    if m := _PERCENT.match(value):
        return ("percent", _num(m.group(1)))
    if m := _BEZIER.match(value):
        return Bezier(*(float(g) for g in m.groups()))
    shadows = [_parse_shadow(layer) for layer in _split_layers(value)]
    if shadows and all(shadows):
        return tuple(shadows)
    return ("string", value)


def resolve(parsed, by_name: dict, theme: str, seen: tuple = ()):
    """Follow var() references to a concrete value in the given theme."""
    while isinstance(parsed, Ref):
        if parsed.name in seen:
            raise GenError(f"reference cycle at {parsed.name}")
        seen = (*seen, parsed.name)
        parsed = parse_value(by_name[parsed.name][theme])
    return parsed


def _num(text: str) -> int | float:
    f = float(text)
    return int(f) if f.is_integer() else f


def swift_name(css_name: str) -> str:
    """--sui-text-strong -> textStrong; --sui-space-2xl -> space2xl (scshafe-qt's naming)."""
    parts = css_name.removeprefix("--sui-").split("-")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# NATIVE-ONLY TOKENS (scshafe-ios; not in the @scshafe/ui registry)
#
# The only place besides the generated Swift where a colour or duration
# literal may appear (tests/test_rules.py). Values follow scshafe-qt's
# NATIVE-ONLY section (tools/gen_tokens.py there) so the platforms match.
# --------------------------------------------------------------------------

# Tint and border strength of a tone (chip, banner, toast): scshafe-qt's
# TONE_TINT (the strongest tint tone text is contrast-checked on) and TONE_BORDER.
TONE_TINT = 0.12
TONE_BORDER = 0.45

# The bucket palette: eight categorical tones for user-defined groups, copied
# verbatim from scshafe-qt's NATIVE_BUCKETS.
#   name      light (base, text)        dark (base, text)
NATIVE_BUCKETS = (
    ("blue", ("#2f7dd9", "#0053a4"), ("#6dadff", "#96c4ff")),
    ("teal", ("#018a8b", "#045f5f"), ("#03c3c3", "#36d5d5")),
    ("green", ("#108f3b", "#046325"), ("#67c377", "#83d48f")),
    ("olive", ("#7e8205", "#565901"), ("#adb33c", "#c0c661")),
    ("amber", ("#a47204", "#714e04"), ("#db9e2e", "#ebb55a")),
    ("rust", ("#cd5630", "#9c2e00"), ("#f58967", "#fea88d")),
    ("rose", ("#c65085", "#9a265f"), ("#ee83af", "#fea5c8")),
    ("violet", ("#9065d0", "#6a3ea5"), ("#b995f6", "#cdb3ff")),
)
BUCKET_WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight")

# Status tones (scshafe-ui and scshafe-qt names, in order) and the registry
# tone colour each one reads. neutral reads muted / tint / line.
STATUS_TONES = (("info", "toneBlue"), ("ok", "toneGreen"), ("warn", "toneYellow"), ("danger", "toneRed"))

# Text roles (scshafe-qt's SuiText variants) over Dynamic Type text styles.
#   role         text style    modifiers                   colour    heading mono
TEXT_ROLES = (
    ("display", "largeTitle", (".bold()",), "textStrong", True),
    ("title", "title2", (".bold()",), "textStrong", True),
    ("heading", "title3", (".bold()",), "textStrong", True),
    ("subheading", "headline", (), "textStrong", True),
    ("section", "subheadline", (".weight(.semibold)",), "muted", True),
    ("label", "footnote", (".weight(.semibold)",), "muted", False),
    ("body", "body", (), "text", False),
    ("caption", "footnote", (), "muted", False),
    ("small", "caption", (), "muted", False),
    ("code", "footnote", (".monospaced()",), "text", False),
)

# Registry tokens that have no iOS counterpart (docs/design.md, 3.1).
DROPPED = {
    "--sui-glass", "--sui-glass-thick", "--sui-glass-sheen", "--sui-glass-edge", "--sui-glass-highlight",
    "--sui-glass-shadow", "--sui-glass-blur", "--sui-glass-saturate",  # the OS renders glass
    "--sui-bg-hover", "--sui-border-hover", "--sui-focus-ring",  # no hover, system focus
    "--sui-shadow-color", "--sui-mono", "--sui-chat-text-size",
}
DROPPED_CATEGORIES = {"clamp", "material", "font"}
SHADOW_NAMES = {"--sui-shadow": "card", "--sui-shadow-lg": "floating"}

HEADER = """\
// GENERATED by tools/gen_tokens.py from tokens/sui-tokens.json
// ({package} {version}, registry {registry_hash}).
// Do not edit; change the snapshot or the generator and rerun it.
"""


def _fmt(n) -> str:
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return str(n)


def _kept(tok: dict) -> bool:
    return tok["category"] not in DROPPED_CATEGORIES and tok["name"] not in DROPPED


def _rgba(c: Rgba) -> str:
    return f"SuiRGBA({c.r}, {c.g}, {c.b}, {_fmt(c.a)})"


def _color_expr(light: Rgba, dark: Rgba) -> str:
    return f"Color(sui: {_rgba(light)}, {_rgba(dark)})"


def _hex_rgba(value: str) -> Rgba:
    c = parse_color(value)
    assert c is not None, value
    return c


def _length(tok: dict, by_name: dict) -> float:
    kind, value = resolve(parse_value(tok["light"]), by_name, "light")
    if kind != "px":
        raise GenError(f"{tok['name']}: {tok['light']!r} is not a length")
    return value


def _ident(prefix: str, name: str) -> str:
    """--sui-radius-sm -> sm; --sui-radius -> base; --sui-space-2xl -> xxl."""
    rest = name.removeprefix("--sui-").removeprefix(prefix).strip("-")
    if not rest:
        return "base"
    swift = swift_name("--sui-" + rest)
    return "xxl" if swift == "2xl" else swift


def _header(snap: dict) -> str:
    src = snap["source"]
    return HEADER.format(package=src["package"], version=src["version"], registry_hash=snap["registryHash"])


def render_tokens(snap: dict) -> str:
    by_name = {t["name"]: t for t in snap["tokens"]}
    toks = [t for t in snap["tokens"] if _kept(t)]
    src = snap["source"]
    out = [_header(snap), "import SwiftUI\n\n"]
    out.append(
        "/// Where this package's design tokens come from.\n"
        "public enum SuiTokenSource {\n"
        "    /// The token registry the tokens are generated from.\n"
        f'    public static let package = "{src["package"]}"\n'
        "    /// The registry release of the committed snapshot (tokens/sui-tokens.json).\n"
        f'    public static let version = "{src["version"]}"\n'
        "    /// The snapshot's registry hash.\n"
        f'    public static let registryHash = "{snap["registryHash"]}"\n'
        "}\n\n"
    )

    out.append("/// Colours. Each resolves for light and dark appearance.\npublic enum SuiColor {\n")
    for t in toks:
        if t["category"] not in ("color", "surface", "border"):
            continue
        light = resolve(parse_value(t["light"]), by_name, "light")
        dark = resolve(parse_value(t["dark"]), by_name, "dark")
        out.append(f"    /// {t['description']} (`{t['name']}`)\n")
        out.append(f"    public static let {swift_name(t['name'])} = {_color_expr(light, dark)}\n")
    out.append("}\n\n")

    for enum, prefix, doc in (("SuiSpace", "space", "Spacing steps, in points."),
                              ("SuiRadius", "radius", "Corner radii, in points.")):
        out.append(f"/// {doc}\npublic enum {enum} {{\n")
        for t in toks:
            if t["category"] == prefix:
                out.append(f"    /// `{t['name']}`\n")
                out.append(f"    public static let {_ident(prefix, t['name'])}: CGFloat = {_fmt(_length(t, by_name))}\n")
        out.append("}\n\n")

    out.append("/// Shadows of the solid (non-glass) floating surfaces. `radius` is the CSS blur / 2.\npublic enum SuiShadow {\n")
    for t in toks:
        if t["name"] not in SHADOW_NAMES:
            continue
        shapes = []
        for theme in ("light", "dark"):
            layers = resolve(parse_value(t[theme]), by_name, theme)
            if not isinstance(layers, tuple) or len(layers) != 1:
                raise GenError(f"{t['name']} ({theme}): expected one shadow layer")
            shapes.append(layers[0])
        light, dark = shapes
        if (light.x, light.y, light.blur, light.spread) != (dark.x, dark.y, dark.blur, dark.spread):
            raise GenError(f"{t['name']}: light and dark shadow geometry differ")
        out.append(f"    /// {t['description']} (`{t['name']}`)\n")
        out.append(
            f"    public static let {SHADOW_NAMES[t['name']]} = SuiShadowStyle(\n"
            f"        color: {_color_expr(light.color, dark.color)},\n"
            f"        radius: {_fmt(light.blur / 2)}, x: {_fmt(light.x)}, y: {_fmt(light.y)})\n"
        )
    out.append("}\n\n")

    motion = {t["name"]: t for t in toks if t["category"] == "motion"}
    kind, ms = parse_value(motion["--sui-duration"]["light"])
    if kind != "ms":
        raise GenError("--sui-duration is not a time")
    reduced = parse_value(snap["reducedMotionDuration"])
    rms = reduced[1] if isinstance(reduced, tuple) and reduced[0] == "ms" else 0
    ease = parse_value(motion["--sui-ease"]["light"])
    spring = parse_value(motion["--sui-ease-spring"]["light"])
    if not (isinstance(ease, Bezier) and isinstance(spring, Bezier)):
        raise GenError("--sui-ease or --sui-ease-spring is not a cubic-bezier")

    def curve(b: Bezier) -> str:
        return f"Animation.timingCurve({_fmt(b.x1)}, {_fmt(b.y1)}, {_fmt(b.x2)}, {_fmt(b.y2)}, duration: duration)"

    out.append(
        "/// Motion. Under Reduce Motion use `reducedDuration` (a cross-fade or nothing).\n"
        "public enum SuiMotion {\n"
        "    /// `--sui-duration`, in seconds.\n"
        f"    public static let duration: Double = {_fmt(ms / 1000)}\n"
        "    /// The registry's reduced-motion duration, in seconds.\n"
        f"    public static let reducedDuration: Double = {_fmt(rms / 1000)}\n"
        "    /// `--sui-ease`.\n"
        f"    public static let standard = {curve(ease)}\n"
        "    /// `--sui-ease-spring`.\n"
        f"    public static let spring = {curve(spring)}\n"
        "}\n"
    )
    return "".join(out)


def render_native(snap: dict) -> str:
    out = [_header(snap), "import SwiftUI\n\n"]
    out.append(
        "// NATIVE-ONLY tokens: not in the registry (see NATIVE-ONLY in tools/gen_tokens.py).\n\n"
        "public enum SuiNative {\n"
        "    /// The tint under tone text.\n"
        f"    public static let toneTint: Double = {_fmt(TONE_TINT)}\n"
        "    /// The border strength of a tone.\n"
        f"    public static let toneBorder: Double = {_fmt(TONE_BORDER)}\n"
        "}\n\n"
    )
    out.append(
        "/// A status tone (the names of scshafe-ui and scshafe-qt). Pair its colour with\n"
        "/// its symbol: see `symbol` and `label` in ScshafeComponents.\n"
        "public enum SuiTone: String, CaseIterable, Sendable {\n"
        "    case neutral, info, ok, warn, danger\n\n"
        "    /// The dot, border and tint colour.\n"
        "    public var base: Color {\n        switch self {\n        case .neutral: SuiColor.muted\n"
    )
    for name, color in STATUS_TONES:
        out.append(f"        case .{name}: SuiColor.{color}\n")
    out.append("        }\n    }\n\n    /// Text on `fill`.\n    public var text: Color {\n        switch self {\n        case .neutral: SuiColor.text\n")
    for name, color in STATUS_TONES:
        out.append(f"        case .{name}: SuiColor.{color}Text\n")
    out.append(
        "        }\n    }\n\n"
        "    /// The fill under tone text.\n"
        "    public var fill: Color { self == .neutral ? SuiColor.tint : base.opacity(SuiNative.toneTint) }\n\n"
        "    /// The border colour.\n"
        "    public var border: Color { self == .neutral ? SuiColor.line : base.opacity(SuiNative.toneBorder) }\n"
        "}\n\n"
    )
    out.append(
        "/// One of eight categorical colours for user-defined groups. Never a status.\n"
        "public enum SuiBucket: Int, CaseIterable, Sendable {\n"
        f"    case {', '.join(f'{w} = {i + 1}' for i, w in enumerate(BUCKET_WORDS))}\n\n"
    )
    for attr, idx, doc in (("base", 0, "The dot, border and tint colour."), ("text", 1, "Text on `fill`.")):
        out.append(f"    /// {doc}\n    public var {attr}: Color {{\n        switch self {{\n")
        for w, (_, light, dark) in zip(BUCKET_WORDS, NATIVE_BUCKETS):
            out.append(f"        case .{w}: {_color_expr(_hex_rgba(light[idx]), _hex_rgba(dark[idx]))}\n")
        out.append("        }\n    }\n\n")
    out.append(
        "    /// The fill under bucket text.\n"
        "    public var fill: Color { base.opacity(SuiNative.toneTint) }\n\n"
        "    /// The border colour.\n"
        "    public var border: Color { base.opacity(SuiNative.toneBorder) }\n\n"
        "    /// The colour's name (blue, teal, ...), for debugging and previews.\n"
        "    public var colorName: String {\n        switch self {\n"
    )
    for w, (n, _, _) in zip(BUCKET_WORDS, NATIVE_BUCKETS):
        out.append(f'        case .{w}: "{n}"\n')
    out.append("        }\n    }\n}\n\n")

    out.append(
        "/// Text roles (scshafe-qt's `SuiText` variants) over Dynamic Type text styles.\n"
        "public enum SuiTextRole: CaseIterable, Sendable {\n"
        f"    case {', '.join(r[0] for r in TEXT_ROLES)}\n\n"
        "    public var font: Font {\n        switch self {\n"
    )
    for role, style, mods, _, _ in TEXT_ROLES:
        out.append(f"        case .{role}: Font.{style}{''.join(mods)}\n")
    out.append("        }\n    }\n\n    public var color: Color {\n        switch self {\n")
    for role, _, _, color, _ in TEXT_ROLES:
        out.append(f"        case .{role}: SuiColor.{color}\n")
    heads = ", ".join("." + r[0] for r in TEXT_ROLES if r[4])
    out.append(
        "        }\n    }\n\n    /// Announced to VoiceOver as a heading.\n"
        f"    public var isHeading: Bool {{\n        switch self {{\n        case {heads}: true\n        default: false\n        }}\n    }}\n}}\n"
    )
    return "".join(out)


def render_tests(snap: dict) -> str:
    """A generated Swift test: every colour resolves to the snapshot's values."""
    by_name = {t["name"]: t for t in snap["tokens"]}
    rows = []
    for t in snap["tokens"]:
        if _kept(t) and t["category"] in ("color", "surface", "border"):
            light = resolve(parse_value(t["light"]), by_name, "light")
            dark = resolve(parse_value(t["dark"]), by_name, "dark")
            rows.append(
                f'        ("{swift_name(t["name"])}", SuiColor.{swift_name(t["name"])}, '
                f"[{light.r}, {light.g}, {light.b}, {_fmt(light.a)}], [{dark.r}, {dark.g}, {dark.b}, {_fmt(dark.a)}]),\n"
            )
    return (
        _header(snap)
        + "import SwiftUI\nimport Testing\nimport UIKit\n@testable import ScshafeTokens\n\n"
        "@Suite struct SuiTokenSnapshotTests {\n"
        "    private static let colors: [(String, Color, [Double], [Double])] = [\n"
        + "".join(rows)
        + "    ]\n\n"
        "    private func components(_ color: Color, _ style: UIUserInterfaceStyle) -> [Double] {\n"
        "        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0\n"
        "        UIColor(color).resolvedColor(with: UITraitCollection(userInterfaceStyle: style))\n"
        "            .getRed(&r, green: &g, blue: &b, alpha: &a)\n"
        "        return [r * 255, g * 255, b * 255, a]\n"
        "    }\n\n"
        "    @Test func coloursMatchTheSnapshot() {\n"
        "        for (name, color, light, dark) in Self.colors {\n"
        "            for (style, want) in [(UIUserInterfaceStyle.light, light), (.dark, dark)] {\n"
        "                let got = components(color, style)\n"
        "                for i in 0..<3 {\n"
        "                    #expect(abs(got[i] - want[i]) < 0.5, \"\\(name) channel \\(i) \\(style.rawValue)\")\n"
        "                }\n"
        "                #expect(abs(got[3] - want[3]) < 0.01, \"\\(name) alpha \\(style.rawValue)\")\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        f'    @Test func sourceIsTheSnapshot() {{\n        #expect(SuiTokenSource.version == "{snap["source"]["version"]}")\n    }}\n'
        "}\n"
    )


def render_outputs(snap: dict) -> dict[Path, str]:
    """Every generated file, keyed by path, rendered from the snapshot."""
    tokens = ROOT / "Sources" / "ScshafeTokens"
    return {
        tokens / "SuiTokens.generated.swift": render_tokens(snap),
        tokens / "SuiNative.generated.swift": render_native(snap),
        ROOT / "Tests" / "ScshafeTokensTests" / "SuiTokenSnapshotTests.generated.swift": render_tests(snap),
    }


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_outputs(snap: dict) -> list[Path]:
    written = []
    for path, text in render_outputs(snap).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        written.append(path)
    return written


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail if the snapshot or a generated file is stale")
    mode.add_argument("--refresh", action="store_true", help="re-read the registry into the snapshot")
    ap.add_argument("--from", dest="source", metavar="DIR", help="scshafe-ui checkout or installed package")
    ap.add_argument("--require-source", action="store_true", help="with --check: fail if no registry is given")
    args = ap.parse_args(argv)

    try:
        if args.refresh:
            src = find_source(args.source)
            if src is None:
                raise GenError("no registry given: pass --from DIR or set SCSHAFE_UI_DIR")
            snap = read_registry(src)
            SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
            SNAPSHOT.write_text(dump_snapshot(snap))
            written = write_outputs(snap)
            print(
                f"refreshed {_rel(SNAPSHOT)} from {src} ({snap['source']['version']}, "
                f"{len(snap['tokens'])} tokens); wrote {len(written)} generated file(s)"
            )
            return 0

        snap = load_snapshot()
        if not args.check:
            written = write_outputs(snap)
            print(f"wrote {len(written)} generated file(s) from {_rel(SNAPSHOT)}")
            return 0

        problems = []
        if SNAPSHOT.read_text() != dump_snapshot(snap):
            problems.append(f"{_rel(SNAPSHOT)} is not in canonical form: run --refresh")
        for path, text in render_outputs(snap).items():
            if not path.is_file() or path.read_text() != text:
                problems.append(f"{_rel(path)} is stale: run `python3 tools/gen_tokens.py`")
        src = find_source(args.source)
        if src is None:
            msg = "no registry given (--from or $SCSHAFE_UI_DIR)"
            if args.require_source:
                problems.append(msg)
            else:
                print(f"note: {msg}; snapshot-vs-registry comparison skipped")
        else:
            live = read_registry(src)
            if live["registryHash"] != snap["registryHash"] or live["source"]["version"] != snap["source"]["version"]:
                problems.append(
                    f"snapshot is stale: {src} is {live['source']['version']} {live['registryHash']}, "
                    f"snapshot has {snap['source']['version']} {snap['registryHash']}: run --refresh"
                )
            else:
                print(f"registry {src} matches the snapshot ({live['source']['version']}, {live['registryHash']})")
        if problems:
            for p in problems:
                print(f"error: {p}", file=sys.stderr)
            return 1
        print(
            f"ok: snapshot {snap['source']['package']} {snap['source']['version']} "
            f"({len(snap['tokens'])} tokens, {snap['registryHash']}); "
            f"{len(render_outputs(snap))} generated file(s) current"
        )
        return 0
    except GenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
