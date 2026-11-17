"""Offline checks for the shared compact search control on all article pages."""
import json
from pathlib import Path
import unittest

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
POSTS = sorted((ROOT / "blog/posts").glob("*.html")) + sorted((ROOT / "music/posts").glob("*.html"))


class CompactSearchTests(unittest.TestCase):
    def test_all_article_pages_have_compact_accessible_search(self):
        self.assertEqual(len(POSTS), 11)
        for page in POSTS:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                widgets = doc.xpath(
                    '//aside[contains(concat(" ",normalize-space(@class)," ")," left ")]'
                    '/section[contains(concat(" ",normalize-space(@class)," ")," site-search-widget ")]'
                )
                self.assertEqual(len(widgets), 1)
                widget = widgets[0]
                self.assertTrue(widget.xpath('.//form[@action="/search.html" and @method="get"]'))
                inputs = widget.xpath('.//input[@id="site-search-input" and @name="q"]')
                self.assertEqual(len(inputs), 1)
                self.assertEqual(inputs[0].get("placeholder"), "Search blog")
                labels = widget.xpath('.//label[@for="site-search-input"]')
                self.assertEqual(len(labels), 1)
                self.assertIn("visually-hidden", labels[0].get("class", ""))
                controls = widget.xpath('.//div[contains(@class,"site-search-controls")]')
                self.assertEqual(len(controls), 1)
                self.assertEqual(controls[0].xpath('./input'), inputs)
                buttons = controls[0].xpath('./button[@type="submit"]')
                self.assertEqual(len(buttons), 1)
                self.assertIn("site-search-submit", buttons[0].get("class", ""))
                self.assertIn("blog and music", buttons[0].get("aria-label", ""))
                self.assertTrue(buttons[0].xpath('./svg'))
                self.assertFalse(widget.xpath('.//button[normalize-space(text())="SEARCH"]'))

    def test_other_sidebars_share_the_same_script_generated_form(self):
        source = (ROOT / "assets/js/site-search.js").read_text(encoding="utf-8")
        self.assertIn('placeholder="Search blog"', source)
        self.assertIn('class="site-search-submit"', source)
        self.assertIn('class="visually-hidden">Search blog and music posts', source)
        self.assertIn('const existing = sidebar.querySelector(".site-search-widget")', source)
        self.assertIn('widget.dataset.searchReady = "true"', source)
        self.assertNotIn('>SEARCH</button>', source)

    def test_search_results_share_the_input_design(self):
        doc = html.parse(str(ROOT / "search.html"))
        controls = doc.xpath('//form[@id="site-search-page-form"]/div[contains(@class,"site-search-controls")]')
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0].xpath('./input/@placeholder'), ["Search blog"])
        self.assertEqual(len(controls[0].xpath('./button[contains(@class,"site-search-submit")]/svg')), 1)
        self.assertEqual(len(doc.xpath('//label[@for="site-search-page-query" and contains(@class,"visually-hidden")]')), 1)

    def test_search_still_excludes_general_pages(self):
        data = json.loads((ROOT / "assets/data/search-index.json").read_text(encoding="utf-8"))
        self.assertEqual({i["section"] for i in data["items"]}, {"blog", "music"})
        self.assertTrue(all(i["url"].startswith(("/blog/posts/", "/music/posts/"))
                            for i in data["items"]))
        source = (ROOT / "assets/js/site-search.js").read_text(encoding="utf-8")
        self.assertIn('item.section === "music"', source)

    def test_shared_css_preserves_palette_and_inner_icon(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("UNIFIED COMPACT SEARCH", css)
        self.assertIn("position:absolute;", css)
        self.assertIn(".site-search-controls .site-search-submit", css)
        for colour in ("#c1121f", "#1e40ff", "#0b0f1f", "#fff"):
            self.assertIn(colour, css)


if __name__ == "__main__":
    unittest.main()
