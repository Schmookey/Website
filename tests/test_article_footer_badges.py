"""Keep five independent 88x31 buttons in each article's original footer row."""
import json
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
        records = json.loads((ROOT / "assets/data/posts.json").read_text(encoding="utf-8"))
        self.assertTrue(records, "Post metadata must not be empty")
        expected_pages = {ROOT / post["url"].lstrip("/") for post in records}
        expected_pages.add(ROOT / "blog/posts/blog-template.html")
        self.assertEqual(set(POSTS), expected_pages,
                         "Every indexed article and template must be checked; no unindexed article files")
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

    def test_webmention_speech_bubble_uses_existing_reply_count(self):
        """Exactly one reply counter, after the two reading metrics."""
        stylesheet = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertNotIn(".hud-meta #mention-count", stylesheet)

        script = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        self.assertNotIn('document.getElementById("mention-count")', script)
        self.assertIn('document.getElementById("wm-replies")', script)
        self.assertIn('if (repliesEl) repliesEl.textContent = String(replies);', script)
        self.assertIn('if (repliesEl) repliesEl.textContent = "0";', script)
        # The terminal still renders the replies, likes and reposts underneath.
        self.assertIn('visibleMentions.map(renderMentionItem).join("")', script)
        self.assertIn('property === "in-reply-to"', script)
        self.assertIn('property === "like-of"', script)
        self.assertIn('property === "repost-of"', script)

        for page in POSTS:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                hud = doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," hud-meta ")]')
                self.assertEqual(len(hud), 1)
                pills = hud[0].xpath('./span[contains(concat(" ",normalize-space(@class)," ")," meta-pill ")]')
                self.assertEqual(len(pills), 5, "Reading time, words, replies, likes and reposts")
                expected = [
                    ("time", "reading-time", "Reading time"),
                    ("words", "word-count", "Word count"),
                    ("comments", "wm-replies", "Replies"),
                    ("likes", "wm-likes", "Likes"),
                    ("shares", "wm-reposts", "Reposts"),
                ]
                for pill, (icon, identifier, label) in zip(pills, expected):
                    self.assertEqual(pill.xpath('./span[@aria-hidden="true"]/@class'),
                                     ["hud-icon hud-icon-" + icon])
                    self.assertEqual(pill.get("title"), label)
                    self.assertIn(label + ":", pill.text_content())
                    self.assertEqual(len(pill.xpath('./span[@id=$id]', id=identifier)), 1)
                    self.assertEqual(len(doc.xpath('//*[@id=$id]', id=identifier)), 1)
                self.assertEqual(doc.xpath('//*[@id="mention-count"]'), [])
                self.assertEqual(len(doc.xpath('//*[@id="comments-list"]')), 1)
                self.assertEqual(len(doc.xpath('//*[@id="load-comments-btn"]')), 1)

    def test_no_changes_to_global_badge_layout_necessary(self):
        stylesheet = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".footer-buttons{", stylesheet)
        self.assertIn("flex-wrap:wrap;", stylesheet)
        self.assertIn(".footer-buttons img{", stylesheet)


if __name__ == "__main__":
    unittest.main()
