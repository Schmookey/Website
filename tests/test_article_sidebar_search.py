"""Protect the Mega Drive article layout and offline search from regressions."""
from pathlib import Path
import unittest

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = sorted((ROOT / "blog/posts").glob("*.html")) + sorted((ROOT / "music/posts").glob("*.html"))
PUBLISHED = [p for p in PUBLISHED if p.name != "blog-template.html"]


class MegaDriveSearchTests(unittest.TestCase):
    def test_published_articles_keep_banner_socials_and_indieweb_markup(self):
        for page in PUBLISHED:
            with self.subTest(page=page.name):
                doc = html.parse(str(page))
                self.assertEqual(len(doc.xpath('//header[contains(@class,"header")]//img[contains(@src,"header-banner.webp")]')), 1)
                self.assertEqual(len(doc.xpath('//nav[contains(@class,"menu")]')), 1)
                self.assertEqual(len(doc.xpath('//main/article[contains(@class,"h-entry") and contains(@class,"post-container")]')), 1)
                self.assertEqual(len(doc.xpath('//aside[contains(@class,"sidebar") and contains(@class,"left")]//div[contains(@class,"badge-grid")]')), 1)
                badges = doc.xpath('//aside[contains(@class,"sidebar") and contains(@class,"left")]//div[contains(@class,"badge-grid")]/a')
                self.assertGreaterEqual(len(badges), 5)
                self.assertTrue(all(a.get("href") for a in badges))
                self.assertTrue(doc.xpath('//script[contains(@src,"main.js")]'))

    def test_only_articles_load_two_column_layout(self):
        js = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        article_js = (ROOT / "assets/js/article-sidebar.js").read_text(encoding="utf-8")
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn('script.src = "/assets/js/article-sidebar.js"', js)
        self.assertIn('layout.classList.add("article-layout")', article_js)
        self.assertIn('.layout.article-layout > .sidebar.right{', css)
        self.assertIn('display:none;', css)
        self.assertIn('.layout.article-layout{', css)
        self.assertIn('grid-template-columns:minmax(210px,240px) minmax(0,1fr)', css)
        for colour in ("#0b0f1f", "#c1121f", "#1e40ff", "#fff"):
            self.assertIn(colour, css)
        self.assertIn('social.append(badges)', article_js)
        self.assertIn('width:88px;', css)
        self.assertIn('height:31px;', css)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))', css)
        self.assertIn('@media(max-width:768px)', css)

    def test_search_is_local_and_has_accessible_results(self):
        doc = html.parse(str(ROOT / "search.html"))
        self.assertTrue(doc.xpath('//*[@id="site-search-page-query"]'))
        self.assertTrue(doc.xpath('//*[@id="site-search-results"]'))
        self.assertTrue(doc.xpath('//meta[@name="robots" and @content="noindex,follow"]'))
        js = (ROOT / "assets/js/site-search.js").read_text(encoding="utf-8")
        self.assertIn('"/assets/data/search-index.json"', js)
        self.assertIn('aria-live="polite"', js)
        self.assertNotIn('google.com/search', js)
        self.assertNotIn('algolia', js)
        self.assertTrue((ROOT / "assets/data/search-index.json").exists())


if __name__ == "__main__":
    unittest.main()
