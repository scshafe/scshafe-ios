"""Repository checks: the skeleton's parts exist and the brief's rules hold."""

import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".build", ".swiftpm", "DerivedData", ".venv", "node_modules", "build", "dist", ".cache"}
# A tailnet hostname ends in the label before "ts.net". The only label
# allowed is the placeholder "<tailnet>" (docs/brief.md: never write the
# tailnet's name).
SUFFIX = ".ts" + ".net"  # split so this file does not match itself
TS_NET = re.compile(r"([A-Za-z0-9<>_-]+)" + re.escape(SUFFIX) + r"\b")
PLACEHOLDER = "<tailnet>"
# Machine-local paths never go in this public repository (split for the same reason).
LOCAL_PATH = re.compile("(/" + "home/[a-z]|/" + "Users/[A-Za-z]|~/" + "src/)")
# The only e-mail addresses allowed are GitHub noreply ones and example domains.
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
ALLOWED_EMAIL = re.compile(r"(@users\.noreply\.github\.com|@example\.(com|org|net))$")
# Build products and per-user Xcode state are never tracked.
GENERATED = re.compile(r"(^|/)(\.build|\.swiftpm|DerivedData|xcuserdata)/|\.xcuserstate$|(^|/)\.DS_Store$")


def text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    yield os.path.relpath(path, ROOT), handle.read()
            except (UnicodeDecodeError, OSError):
                continue


def tracked_files():
    """The files git tracks, or every file when this is not a git checkout."""
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], check=True, capture_output=True).stdout
        return [p for p in out.decode("utf-8").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [rel for rel, _ in text_files()]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


class SkeletonTest(unittest.TestCase):
    def test_parts_exist(self):
        for rel in ("README.md", "LICENSE", "AGENTS.md", "docs/brief.md", "docs/research.md",
                    "Package.swift", "tokens/sui-tokens.json", "tools/gen_tokens.py", "scripts/verify"):
            with self.subTest(path=rel):
                self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), f"{rel} is missing")

    def test_mit_licence(self):
        self.assertTrue(read("LICENSE").startswith("MIT License"))

    def test_ios_26_floor(self):
        package = read("Package.swift")
        self.assertRegex(package, r"swift-tools-version:\s*6\.[2-9]")
        self.assertIn(".iOS(.v26)", package)
        self.assertNotRegex(package, r"\.iOS\(\.v1[0-9]|\.iOS\(\.v2[0-5]\)", "iOS 26 is the floor (docs/brief.md)")


class PublicRepositoryTest(unittest.TestCase):
    def test_placeholder_matches(self):
        self.assertEqual(TS_NET.findall("host." + PLACEHOLDER + SUFFIX), [PLACEHOLDER])
        self.assertEqual(TS_NET.findall("host.example-name" + SUFFIX), ["example-name"])

    def test_no_tailnet_name(self):
        found = [rel for rel, text in text_files() if any(l != PLACEHOLDER for l in TS_NET.findall(text))]
        self.assertEqual(found, [], "write <tailnet> instead of the tailnet's name")

    def test_no_machine_local_paths(self):
        found = [rel for rel, text in text_files() if LOCAL_PATH.search(text)]
        self.assertEqual(found, [], "no machine-local paths in this public repository")

    def test_no_personal_email(self):
        found = [
            f"{rel}: {addr}"
            for rel, text in text_files()
            for addr in EMAIL.findall(text)
            if not ALLOWED_EMAIL.search(addr)
        ]
        self.assertEqual(found, [], "only noreply or example e-mail addresses")

    def test_no_build_products_tracked(self):
        found = [p for p in tracked_files() if GENERATED.search(p)]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
