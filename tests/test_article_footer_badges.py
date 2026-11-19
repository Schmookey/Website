"""Keep five independent 88x31 buttons in each article's original footer row."""
from pathlib import Path
import unittest

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
POSTS = sorted((ROOT / "blog/posts").glob("*.html")) + sorted(
    (ROOT / "music/posts").glob("*.html")
)
EXPECTED = [
    "/assets/images/valid-rss-rogers.png",
    "/assets/images/CC_BY-NC_icon-88x31.png",
    "/assets/images/88x31_IndieWeb.png",
    "/assets/images/88x31_Webmention.png",
    "/assets/images/88x31_Microformats.png",
]
LINKS = {
    "/assets/images/88x31_IndieWeb.png": "https://indieweb.org",
    "/assets/images/88x31_Webmention.png": "https://webmention.io/",
    "/assets/images/88x31_Microformats.png": "https://microformats.org/",
}


class ArticleFooterBadgeTests(unittest.TestCase):
    def test_badges_are_in_existing_row_above_navigation(self):
        self.assertEqual(len(POSTS), 11)
        for page in POSTS:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                footer = doc.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," post-container ")]/footer[contains(concat(" ",normalize-space(@class)," ")," retro-post-footer ")]')
                self.assertEqual(len(footer), 1)
                row = footer[0].xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," footer-buttons ")]')
                self.assertEqual(len(row), 1)
                badges = row[0].xpath('.//img/@src')
                self.assertEqual(badges, EXPECTED)
                nav = footer[0].xpath('.//nav[contains(concat(" ",normalize-space(@class)," ")," footer-nav ")]')
                self.assertEqual(len(nav), 1)
                self.assertTrue(row[0].sourceline < nav[0].sourceline)
                for src, href in LINKS.items():
                    matches = row[0].xpath('.//a[img[@src=$image]]', image=src)
                    self.assertEqual(len(matches), 1)
                    self.assertEqual(matches[0].get("href"), href)
                    image = matches[0].xpath('./img')[0]
                    self.assertTrue(image.get("alt"))
                    self.assertEqual(image.get("width"), "88")
                    self.assertEqual(image.get("height"), "31")

    def test_footer_hover_text(self):
        for page in POSTS:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                self.assertEqual(doc.xpath('//a[img[@src="/assets/images/88x31_Webmention.png"]]/@title'), ["Learn more about Webmentions"])
                self.assertEqual(doc.xpath('//a[img[@src="/assets/images/88x31_Microformats.png"]]/@title'), ["learn more about Microformats"])

    def test_webmention_hud_is_icon_only_without_removing_live_count(self):
        """Keep the live Webmention count accessible but visually hide its label."""
        stylesheet = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        selector = ".layout.article-layout .retro-post-hud .hud-meta #mention-count"
        self.assertIn(selector + " {", stylesheet)
        rule = stylesheet.split(selector + " {", 1)[1].split("}", 1)[0]
        self.assertIn("clip-path: inset(50%);", rule)
        self.assertIn("position: absolute;", rule)
        script = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        self.assertIn('document.getElementById("mention-count")', script)
        self.assertIn('countEl.textContent', script)
        for page in POSTS:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                pills = doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," hud-meta ")]'
                                  '/span[contains(concat(" ",normalize-space(@class)," ")," meta-pill ")]'
                                  '[span[@id="mention-count"]]')
                self.assertEqual(len(pills), 1)
                self.assertIn("💬", pills[0].text_content())
                self.assertEqual(len(pills[0].xpath('./span[@id="mention-count"]')), 1)

    def test_no_changes_to_global_badge_layout_necessary(self):
        stylesheet = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".footer-buttons{", stylesheet)
        self.assertIn("flex-wrap:wrap;", stylesheet)
        self.assertIn(".footer-buttons img{", stylesheet)


if __name__ == "__main__":
    unittest.main()
