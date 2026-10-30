"""The token pipeline: the committed snapshot and tools/gen_tokens.py."""

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import gen_tokens as gen

ROOT = Path(__file__).resolve().parent.parent
# The owner fixed @scshafe/ui 0.9.0 as the first token source (docs/brief.md).
# A refresh may move forward, never back.
MIN_VERSION = (0, 9, 0)
SWIFT_SOURCE = ROOT / "Sources" / "ScshafeTokens"


def version_tuple(text):
    return tuple(int(part) for part in text.split("-")[0].split("."))


def run_main(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gen.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.snap = gen.load_snapshot()

    def test_source_is_scshafe_ui_at_least_the_brief_version(self):
        src = self.snap["source"]
        self.assertEqual(src["package"], "@scshafe/ui")
        self.assertGreaterEqual(version_tuple(src["version"]), MIN_VERSION)
        self.assertRegex(src.get("commit", ""), r"^[0-9a-f]{40}$", "refresh from a git checkout of a release")

    def test_tokens_are_unique_and_prefixed(self):
        names = [tok["name"] for tok in self.snap["tokens"]]
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertRegex(name, r"^--sui-[a-z0-9-]+$")

    def test_swift_names_are_unique(self):
        names = [gen.swift_name(tok["name"]) for tok in self.snap["tokens"]]
        self.assertEqual(len(names), len(set(names)))

    def test_swift_output_covers_the_kept_tokens_and_drops_the_rest(self):
        text = gen.render_tokens(self.snap)
        for tok in self.snap["tokens"]:
            name = gen.swift_name(tok["name"])
            if tok["category"] in ("color", "surface", "border") and tok["name"] not in gen.DROPPED:
                self.assertIn(f"public static let {name} = Color(sui:", text, tok["name"])
            if tok["name"] in gen.DROPPED or tok["category"] in gen.DROPPED_CATEGORIES:
                self.assertNotIn(f"`{tok['name']}`", text, tok["name"])

    def test_swift_output_is_deterministic_and_has_no_alias_left(self):
        self.assertEqual(gen.render_outputs(self.snap), gen.render_outputs(self.snap))
        for text in gen.render_outputs(self.snap).values():
            self.assertNotIn("var(--", text)

    def test_native_output_has_five_tones_eight_buckets_and_the_text_roles(self):
        text = gen.render_native(self.snap)
        self.assertIn("case neutral, info, ok, warn, danger", text)
        self.assertEqual(len(gen.NATIVE_BUCKETS), 8)
        for role, *_ in gen.TEXT_ROLES:
            self.assertIn(f"case .{role}:", text)

    def test_canonical_form(self):
        self.assertEqual(gen.SNAPSHOT.read_text(), gen.dump_snapshot(self.snap))

    def test_glass_and_motion_tokens_present(self):
        # The 0.6.0+ registry the brief asks for: glass, the larger radii, easing.
        names = {tok["name"] for tok in self.snap["tokens"]}
        for name in ("--sui-glass", "--sui-glass-edge", "--sui-popover", "--sui-radius-xl",
                     "--sui-radius-pill", "--sui-ease", "--sui-ease-spring", "--sui-accent"):
            self.assertIn(name, names)

    def test_every_colour_resolves_in_both_themes(self):
        by_name = {tok["name"]: tok for tok in self.snap["tokens"]}
        for tok in self.snap["tokens"]:
            if tok["category"] not in ("color", "surface", "border"):
                continue
            for theme in ("light", "dark"):
                with self.subTest(token=tok["name"], theme=theme):
                    value = gen.resolve(gen.parse_value(tok[theme]), by_name, theme)
                    self.assertIsInstance(value, gen.Rgba)

    def test_generated_swift_names_the_snapshot_version(self):
        text = "\n".join(p.read_text() for p in sorted(SWIFT_SOURCE.glob("*.swift")))
        versions = re.findall(r'version\s*=\s*"([0-9.]+)"', text)
        self.assertIn(self.snap["source"]["version"], versions)


class ParseTest(unittest.TestCase):
    def test_colours(self):
        self.assertEqual(gen.parse_value("#0a4f99"), gen.Rgba(10, 79, 153, 1.0))
        self.assertEqual(gen.parse_value("#fff"), gen.Rgba(255, 255, 255, 1.0))
        self.assertEqual(gen.parse_value("rgba(24, 36, 56, 0.82)"), gen.Rgba(24, 36, 56, 0.82))

    def test_lengths_times_and_curves(self):
        self.assertEqual(gen.parse_value("12px"), ("px", 12))
        self.assertEqual(gen.parse_value("120ms"), ("ms", 120))
        self.assertEqual(gen.parse_value("0s"), ("ms", 0))
        self.assertEqual(gen.parse_value("180%"), ("percent", 180))
        self.assertEqual(gen.parse_value("cubic-bezier(0.34, 1.36, 0.64, 1)"), gen.Bezier(0.34, 1.36, 0.64, 1.0))

    def test_shadows(self):
        one = gen.parse_value("0 10px 34px rgba(0, 0, 0, 0.22)")
        self.assertEqual(one, (gen.Shadow(0, 10, 34, 0, gen.Rgba(0, 0, 0, 0.22)),))
        two = gen.parse_value("0 8px 24px rgba(15, 23, 42, 0.1), 0 1px 3px rgba(15, 23, 42, 0.08)")
        self.assertEqual(len(two), 2)

    def test_references_and_strings(self):
        self.assertEqual(gen.parse_value("var(--sui-blue)"), gen.Ref("--sui-blue"))
        self.assertEqual(gen.parse_value("ui-monospace, Menlo")[0], "string")

    def test_swift_name(self):
        self.assertEqual(gen.swift_name("--sui-text-strong"), "textStrong")
        self.assertEqual(gen.swift_name("--sui-space-2xl"), "space2xl")
        self.assertEqual(gen.swift_name("--sui-glass-accent-text"), "glassAccentText")


class CheckTest(unittest.TestCase):
    def test_check_passes_on_this_checkout(self):
        env = os.environ.pop("SCSHAFE_UI_DIR", None)
        try:
            code, out = run_main("--check")
        finally:
            if env is not None:
                os.environ["SCSHAFE_UI_DIR"] = env
        self.assertEqual(code, 0, out)

    def test_require_source_fails_without_a_registry(self):
        env = os.environ.pop("SCSHAFE_UI_DIR", None)
        try:
            code, out = run_main("--check", "--require-source")
        finally:
            if env is not None:
                os.environ["SCSHAFE_UI_DIR"] = env
        self.assertEqual(code, 1, out)

    def test_hand_edit_is_detected(self):
        snap = json.loads(gen.SNAPSHOT.read_text())
        snap["tokens"][0]["light"] = "#000000"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sui-tokens.json"
            path.write_text(json.dumps(snap))
            with self.assertRaisesRegex(gen.GenError, "registryHash"):
                gen.load_snapshot(path)

    def test_bad_value_is_refused(self):
        snap = json.loads(gen.SNAPSHOT.read_text())
        tok = next(t for t in snap["tokens"] if t["category"] == "color" and not t["light"].startswith("var("))
        tok["light"] = "not-a-colour"
        snap["registryHash"] = gen.registry_hash(snap)
        with self.assertRaisesRegex(gen.GenError, "not a colour"):
            gen.validate(snap)


FAKE_REGISTRY = """
export const SUI_REDUCED_MOTION_DURATION = "0s";
export const SUI_TOKENS = [
  { name: "--sui-blue", light: "#0a4f99", dark: "#6cb6ff", themed: true,
    category: "color", role: "text", description: "Blue." },
  { name: "--sui-accent", light: "var(--sui-blue)", dark: "var(--sui-blue)", themed: true,
    category: "color", role: "text", description: "Accent." },
  { name: "--sui-space-sm", light: "8px", dark: "8px", themed: false,
    category: "space", description: "Small space." },
];
"""


@unittest.skipUnless(shutil.which("node"), "node is needed to read a registry")
class RegistryTest(unittest.TestCase):
    def make_package(self, root, version):
        (root / "src").mkdir()
        (root / "src" / "tokens.ts").write_text(FAKE_REGISTRY)
        (root / "package.json").write_text(json.dumps({"name": "@scshafe/ui", "version": version}))

    def test_read_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, "9.9.9")
            snap = gen.read_registry(root)
        self.assertEqual(snap["source"]["version"], "9.9.9")
        self.assertEqual(snap["source"]["file"], "src/tokens.ts")
        self.assertEqual([t["name"] for t in snap["tokens"]], ["--sui-blue", "--sui-accent", "--sui-space-sm"])
        self.assertIsNone(snap["tokens"][2]["role"])
        self.assertEqual(snap["registryHash"], gen.registry_hash(snap))

    def test_check_reports_a_different_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, "9.9.9")
            code, out = run_main("--check", "--from", str(root))
        self.assertEqual(code, 1, out)
        self.assertIn("snapshot is stale", out)

    def test_refuses_another_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps({"name": "left-pad", "version": "1.0.0"}))
            with self.assertRaisesRegex(gen.GenError, "not @scshafe/ui"):
                gen.read_registry(root)

    def test_snapshot_commit_is_a_real_git_commit_when_refreshed_from_git(self):
        if not shutil.which("git"):
            self.skipTest("git missing")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, "9.9.9")
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@example.com"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            subprocess.run([*git, "add", "."], check=True)
            subprocess.run([*git, "commit", "-qm", "registry"], check=True)
            snap = gen.read_registry(root)
        self.assertRegex(snap["source"]["commit"], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
