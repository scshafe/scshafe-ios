#!/usr/bin/env python3
"""Keep scshafe-ios's design tokens in step with @scshafe/ui's token registry.

A port of scshafe-qt's tools/gen_tokens.py (same snapshot, schema 1). Pipeline
(stdlib only; Node is needed only to read a registry):

    @scshafe/ui ./tokens export (lib/tokens.js) or src/tokens.ts
        -- node, --refresh -->  tokens/sui-tokens.json   (committed snapshot)
        -- this script     -->  the generated Swift sources (committed)

The Swift emitter is not written yet: how colours are delivered (a generated
asset catalog or generated Swift code) is an open question for the design
(docs/brief.md). Until it lands, OUTPUTS is empty and this script keeps the
snapshot honest: --check validates it and, when a registry is given, compares
it with that registry.

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


def render_outputs(snap: dict) -> dict[Path, str]:
    """Every generated file, keyed by path, rendered from the snapshot.

    Empty until the design (docs/design.md) settles how colours are delivered:
    the Swift emitter (Sources/ScshafeTokens/...) and, if chosen, the asset
    catalog are added here, and --check then keeps them current.
    """
    return {}


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
