"""Verify the custom HUD assets and article / Note metric markup."""
from pathlib import Path
import unittest
from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("time", "words", "comments", "likes", "shares")

class HUDIconsTests(unittest.TestCase):
    def test_assets_and_both_theme_rules(self):
        css = (ROOT / "assets/css/hud-icons.css").read_text()
        for theme in ("dark", "light"):
            for kind in KINDS:
                path = f"assets/images/icons/hud/{theme}/{kind}.svg"
                icon = etree.parse(str(ROOT / path)).getroot()
                self.assertEqual(icon.get("viewBox"), "0 0 24 24")
                self.assertIn("/" + path, css)
        self.assertIn('html[data-schmookey-theme="light"]', css)

    def test_article_huds(self):
        pages = sorted((ROOT / "blog/posts").glob("*.html")) + sorted((ROOT / "music/posts").glob("*.html"))
        self.assertTrue(pages)
        for path in pages:
            with self.subTest(page=path.name):
                doc = html.parse(str(path))
                self.assertEqual(doc.xpath('//link[@href="/assets/css/hud-icons.css"]/@href'), ["/assets/css/hud-icons.css"])
                rows = doc.xpath('//div[contains(@class,"hud-icon-meta")]')
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0].xpath('./span/span[@id]/@id'), ["reading-time","word-count","wm-replies","wm-likes","wm-reposts"])
                self.assertEqual(rows[0].xpath('./span/span[@aria-hidden="true"]/@class'), ["hud-icon hud-icon-"+k for k in KINDS])
                self.assertEqual(len(rows[0].xpath('./span[@title]/span[contains(@class,"visually-hidden")]')), 5)

    def test_note_huds(self):
        for path in (ROOT / "notes").glob("*.html"):
            with self.subTest(page=path.name):
                doc = html.parse(str(path))
                self.assertTrue(doc.xpath('//link[@href="/assets/css/hud-icons.css"]'))
                rows = doc.xpath('//div[contains(@class,"hud-icon-meta")]')
                self.assertTrue(rows)
                for row in rows:
                    self.assertEqual(row.xpath('./span/span[@aria-hidden="true"]/@class'), ["hud-icon hud-icon-"+k for k in KINDS[2:]])
                    self.assertEqual(len(row.xpath('./span[@title]/span[contains(@class,"visually-hidden")]')), 3)
                if path.name == "index.html":
                    self.assertEqual(len(rows), len(doc.xpath('//article[@class="h-entry"]')))
                    self.assertEqual(len(rows), len(doc.xpath('//section[@data-note-target]/details')))
                self.assertFalse(doc.xpath('//*[@id="word-count"]'))

if __name__ == "__main__":
    unittest.main()
