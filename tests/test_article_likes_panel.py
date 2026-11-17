"""Match the Changelog's Likes badges on every blog and music article."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = sorted((ROOT / "blog/posts").glob("*.html")) + sorted(
    (ROOT / "music/posts").glob("*.html")
)


def badge_links(section):
    return [(a.get("href"), im.get("src"), im.get("alt"))
            for a in section.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," badge-grid ")]/a')
            for im in a.xpath("./img")]


class LikesPanelTests(unittest.TestCase):
    def test_every_article_reuses_changelog_likes_buttons(self):
        changelog = html.parse(str(ROOT / "changelog.html"))
        original = changelog.xpath(
            '//aside[contains(@class,"site-panel-sidebar")]'
            '/section[contains(@class,"article-likes-badges")]'
        )
        self.assertEqual(len(original), 1)
        expected = badge_links(original[0])
        self.assertEqual(len(expected), 5)
        self.assertEqual(len(ARTICLES), 11)

        for page in ARTICLES:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                sidebar = doc.xpath(
                    '//aside[contains(concat(" ",normalize-space(@class)," ")," article-sidebar ")]'
                )
                self.assertEqual(len(sidebar), 1)
                sections = sidebar[0].xpath("./section")
                self.assertEqual(len(sections), 5)
                self.assertEqual(
                    [sec.get("class").split()[-1] for sec in sections],
                    ["site-search-widget", "article-related-posts", "article-more-posts",
                     "article-social-badges", "article-likes-badges"]
                )
                likes = sections[-1]
                self.assertEqual(likes.xpath('./h2/text()'), ["LIKES"])
                self.assertEqual(
                    [(href, src.lstrip("/") if src.startswith("/") else src, alt)
                     for href, src, alt in badge_links(likes)],
                    [(href, src.lstrip("/") if src.startswith("/") else src, alt)
                     for href, src, alt in expected]
                )
                self.assertTrue(all(src.startswith("/assets/images/")
                                    for _, src, _ in badge_links(likes)))
                self.assertTrue(all(a.get("width") == "88" and a.get("height") == "31"
                                    for a in likes.xpath(".//img")))
                self.assertEqual(len(sections[3].xpath('.//div[contains(@class,"badge-grid")]/a')), 5)
                self.assertEqual(len(doc.xpath('//article[contains(@class,"post-container")]'
                    '//div[contains(@class,"footer-buttons")]/a/img')), 5)

    def test_likes_uses_existing_megadrive_panel_styling(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".layout.article-layout .article-likes-badges .badge-grid", css)
        self.assertIn(".article-likes-badges .badge-grid img", css)
        self.assertIn("order:5;", css)


if __name__ == "__main__":
    unittest.main()
