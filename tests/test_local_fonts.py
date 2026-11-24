"""Keep first-party font loading local and preserve the upstream font/licence."""
from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LocalFontTests(unittest.TestCase):
    def test_original_font_and_licence(self):
        for name, expected in (
            ("PressStart2P-Regular.ttf", "39adf42efa597906e53be689474ac82214112124"),
            ("OFL.txt", "22796dfe6e3784d69d255b0bf253e2b16f3281de"),
        ):
            data = (ROOT / "assets/fonts" / name).read_bytes()
            git_blob = f"blob {len(data)}\0".encode() + data
            self.assertEqual(hashlib.sha1(git_blob).hexdigest(), expected)

    def test_local_font_declaration(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn('@font-face', css)
        self.assertIn('url("/assets/fonts/PressStart2P-Regular.ttf")', css)
        self.assertIn('font-display: swap', css)

    def test_no_external_google_font_requests(self):
        paths = list(ROOT.glob("*.html"))
        for directory in ("blog", "music", "notes", "random", "Templates", "assets", "scripts"):
            paths.extend(p for p in (ROOT / directory).rglob("*")
                         if p.is_file() and p.suffix.lower() in (".html", ".css", ".js", ".py", ".xsl"))
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                content = path.read_text(encoding="utf-8").lower()
                self.assertNotIn("fonts.googleapis.com", content)
                self.assertNotIn("fonts.gstatic.com", content)


if __name__ == "__main__":
    unittest.main()
