"""Consistent Mega Drive Search, Socials and Likes across standard pages."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html", "about.html", "blog/index.html", "music/index.html",
    "random/index.html", "blog-archive.html", "music-archive.html",
    "webrings.html", "changelog.html", "privacy.html", "now.html",
    "listening.html", "now-watching.html", "search.html", "page-template.html",
)
LIKES = (
    "/assets/images/CC_BY-NC_icon-88x31.png",
    "/assets/images/right2repair.png",
    "/assets/images/indieweb88x31-flat.png",
    "/assets/images/fediverse.png",
    "/assets/images/linux_mint.gif",
)


def classes(el):
    return set((el.get("class") or "").split())


class StandardPagePanelTests(unittest.TestCase):
    def test_all_standard_pages_have_separate_left_hand_panels(self):
        self.assertEqual(len(PAGES), 15)
        for name in PAGES:
            with self.subTest(page=name):
                page = ROOT / name
                doc = html.parse(str(page))
                layout = doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," site-panel-layout ")]')
                self.assertEqual(len(layout), 1)
                left = layout[0].xpath('./aside[contains(concat(" ",normalize-space(@class)," ")," site-panel-sidebar ")]')
                self.assertEqual(len(left), 1)
                sections = left[0].xpath("./section")
                expected = ["site-search-widget", "article-social-badges", "article-likes-badges"]
                if name == "about.html":
                    expected.append("site-button-share")
                self.assertEqual(len(sections), len(expected))
                for section, class_name in zip(sections, expected):
                    self.assertIn(class_name, classes(section))
                self.assertEqual(sections[0].xpath('.//input/@placeholder'), ["Search blog"])
                self.assertEqual(len(sections[0].xpath('.//button[contains(@class,"site-search-submit")]/svg')), 1)
                social_images = sections[1].xpath('.//div[contains(@class,"badge-grid")]/a/img')
                self.assertEqual(len(social_images), 5)
                self.assertEqual(
                    sections[2].xpath('.//div[contains(@class,"badge-grid")]/a/img/@src'),
                    list(LIKES)
                )
                self.assertTrue(all(a.get("href") for a in sections[2].xpath('.//a')))
                self.assertTrue(all((image.get("alt") or "").strip()
                                    for image in sections[2].xpath('.//img')))
                self.assertFalse(doc.xpath(
                    '//aside[contains(concat(" ",normalize-space(@class)," ")," right ")]'
                    '//h2[normalize-space()="LIKES"]'
                ))
                self.assertEqual(len(doc.xpath('//script[@src="/assets/js/main.js"]')), 1)

    def test_about_button_is_unique_and_copy_behaviour_preserved(self):
        for name in PAGES:
            with self.subTest(page=name):
                doc = html.parse(str(ROOT / name))
                buttons = doc.xpath('//*[@id="copy-site-button"]')
                fields = doc.xpath('//*[@id="site-button-code"]')
                panels = doc.xpath('//section[contains(@class,"site-button-share")]')
                if name == "about.html":
                    self.assertEqual(len(buttons), 1)
                    self.assertEqual(len(fields), 1)
                    self.assertEqual(len(panels), 1)
                    self.assertEqual(len(panels[0].xpath('.//img[@src="/assets/images/schmookey-88x31.gif"]')), 1)
                    self.assertIn("schmookey-88x31.gif", fields[0].text or "")
                    self.assertEqual(fields[0].get("readonly"), "readonly")
                else:
                    self.assertFalse(buttons)
                    self.assertFalse(fields)
                    self.assertFalse(panels)
        js = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        self.assertIn('getElementById("copy-site-button")', js)

    def test_only_home_and_about_keep_meaningful_right_sidebar(self):
        for name in PAGES:
            doc = html.parse(str(ROOT / name))
            right = doc.xpath('//div[contains(@class,"site-panel-layout")]/aside[contains(@class,"right")]')
            self.assertEqual(len(right), 1 if name in {"index.html", "about.html"} else 0,
                             msg=name)
        about = html.parse(str(ROOT / "about.html"))
        self.assertEqual(len(about.xpath('//*[@id="latest-listen"]')), 1)
        self.assertEqual(len(about.xpath('//*[@id="trakt-latest-card"]')), 1)

    def test_article_pages_remain_unchanged_four_or_five_content_panels(self):
        for section in ("blog", "music"):
            for page in sorted((ROOT / section / "posts").glob("*.html")):
                with self.subTest(page=page.name):
                    doc = html.parse(str(page))
                    self.assertEqual(len(doc.xpath('//aside[contains(@class,"article-sidebar")]')), 1)
                    self.assertEqual(len(doc.xpath('//section[contains(@class,"article-likes-badges")]')), 1)
                    self.assertFalse(doc.xpath('//section[contains(@class,"site-button-share")]'))

    def test_css_retains_mega_drive_style(self):
        style = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("STANDARD PAGE PANELS", style)
        self.assertIn(".layout.site-panel-layout:not(.site-panel-three-col)", style)
        self.assertIn(".layout.site-panel-layout.site-panel-three-col", style)
        for colour in ("#0b0f1f", "#c1121f", "#1e40ff", "#fff"):
            self.assertIn(colour, style)


if __name__ == "__main__":
    unittest.main()
