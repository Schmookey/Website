"""Ensure ListenBrainz is alongside GOG in Socials, never in Likes."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
STANDARD = (
    "index.html", "about.html", "blog/index.html", "music/index.html",
    "random/index.html", "blog-archive.html", "music-archive.html",
    "webrings.html", "changelog.html", "privacy.html", "now.html",
    "listening.html", "now-watching.html", "search.html", "page-template.html",
)
PAGES = [ROOT / name for name in STANDARD] + sorted((ROOT / "blog/posts").glob("*.html")) + sorted((ROOT / "music/posts").glob("*.html"))
LB_IMAGE = "/assets/images/listenbrainz88x31.gif"
GOG_IMAGE = "/assets/images/e-gog.png"
LB_PROFILE = "https://listenbrainz.org/user/jon_cass/"


class ListenBrainzLocationTests(unittest.TestCase):
    def test_all_26_panels_place_listenbrainz_immediately_after_gog(self):
        self.assertEqual(len(PAGES), 26)
        self.assertTrue((ROOT / LB_IMAGE.lstrip("/")).is_file())
        for path in PAGES:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                doc = html.parse(str(path))
                social = doc.xpath('//section[contains(concat(" ",normalize-space(@class)," ")," article-social-badges ")]')
                likes = doc.xpath('//section[contains(concat(" ",normalize-space(@class)," ")," article-likes-badges ")]')
                self.assertEqual((len(social), len(likes)), (1, 1))
                icons = social[0].xpath('.//div[contains(@class,"badge-grid")]/a/img')
                srcs = [im.get("src") for im in icons]
                self.assertIn(GOG_IMAGE, srcs)
                gog_index = srcs.index(GOG_IMAGE)
                self.assertLess(gog_index + 1, len(srcs))
                self.assertEqual(srcs[gog_index + 1], LB_IMAGE)
                self.assertEqual(srcs.count(LB_IMAGE), 1)
                self.assertEqual(icons[gog_index + 1].getparent().get("href"), LB_PROFILE)
                self.assertEqual(len(likes[0].xpath('.//img')), 5)
                self.assertFalse(likes[0].xpath('.//img[@src=$src]', src=LB_IMAGE))
                self.assertTrue(likes[0].xpath('.//img[@src="/assets/images/internet-archive.gif"]'))

    def test_article_footer_badges_still_present(self):
        for folder in ("blog", "music"):
            for path in (ROOT / folder / "posts").glob("*.html"):
                with self.subTest(path=path.name):
                    doc = html.parse(str(path))
                    self.assertEqual(
                        len(doc.xpath('//article[contains(@class,"post-container")]'
                                      '//div[contains(@class,"footer-buttons")]/a/img')), 5
                    )


if __name__ == "__main__":
    unittest.main()
