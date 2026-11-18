"""Home followed-blog articles share one retro panel with smaller cards."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]


class HomeFollowedBlogPanelTests(unittest.TestCase):
    def test_one_panel_three_compact_cards_preserve_article_content(self):
        doc = html.parse(str(ROOT / "index.html"))
        right = doc.xpath(
            '//div[contains(concat(" ",normalize-space(@class)," ")," site-panel-layout ")]'
            '/aside[contains(concat(" ",normalize-space(@class)," ")," followed-blogs-sidebar ")]'
        )
        self.assertEqual(len(right), 1)
        section = right[0].xpath('./section[contains(@class,"webring")]')
        self.assertEqual(len(section), 1)
        self.assertEqual(len(right[0].xpath("./section")), 1)
        self.assertEqual(section[0].xpath('./h3/text()'), ["Articles from blogs I follow."])
        cards = section[0].xpath(
            './section[contains(@class,"articles")]/article[contains(@class,"followed-blog-panel")]'
        )
        self.assertEqual(len(cards), 3)
        # These are hand-curated links and will change. Check the structure,
        # accessibility and URL safety without pinning old article titles/dates.
        from datetime import datetime
        from urllib.parse import urlsplit
        urls = []
        for card in cards:
            self.assertFalse(card.xpath('.//*[contains(@class,"followed-blog-panel-heading")]'))
            articles = card.xpath('./h4[contains(@class,"title")]/a')
            sources = card.xpath('./small[contains(@class,"source")]/a')
            dates = card.xpath('./small[contains(@class,"date")]/text()')
            summaries = card.xpath('./p[contains(@class,"summary")]')
            self.assertEqual(len(articles), 1)
            self.assertEqual(len(sources), 1)
            self.assertEqual(len(dates), 1)
            self.assertEqual(len(summaries), 1)
            self.assertTrue(articles[0].text_content().strip())
            self.assertTrue(summaries[0].text_content().strip())
            self.assertTrue(sources[0].text_content().strip())
            datetime.strptime(dates[0].strip(), "%B %d, %Y")
            for anchor in (articles[0], sources[0]):
                target = urlsplit(anchor.get("href", ""))
                self.assertEqual(target.scheme, "https")
                self.assertTrue(target.hostname)
                self.assertNotIn("//", target.path)
                self.assertEqual(anchor.get("target"), "_blank")
                self.assertIn("noopener", anchor.get("rel", "").split())
            urls.append(articles[0].get("href"))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(section[0].xpath('./p[contains(@class,"attribution")]/a/@href'),
                         ["https://git.sr.ht/~sircmpwn/openring"])

    def test_scoped_compact_panel_styles(self):
        style = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("HOME — COMPACT FOLLOWED-BLOG COLLECTION", style)
        self.assertIn(".followed-blogs-sidebar > .webring > h3{", style)
        self.assertIn(".followed-blogs-sidebar .articles > .followed-blog-panel{", style)
        self.assertNotIn(".followed-blog-panel-heading{", style)
        for colour in ("#0b0f1f", "#1e40ff", "#c1121f"):
            self.assertIn(colour, style)
        about = (ROOT / "about.html").read_text(encoding="utf-8")
        self.assertIn("about-media-sidebar", about)


if __name__ == "__main__":
    unittest.main()
