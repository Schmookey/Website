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
        expected = (
            ("https://www.wheresyoured.at/the-ai-demand-bubble/", "https://www.wheresyoured.at/", "August 4, 2026"),
            ("https://www.usermag.co/p/my-journey-into-the-slop-factory", "https://www.usermag.co/", "July 30, 2026"),
            ("https://www.gamefile.news/p/sony-drops-playstation-discs-2028-ps3-vita-stores-closing", "https://substack.com/@stephentotilo", "July 1, 2026"),
        )
        for card, (article, source, date) in zip(cards, expected):
            self.assertFalse(card.xpath('.//*[contains(@class,"followed-blog-panel-heading")]'))
            self.assertEqual(card.xpath('./h4[contains(@class,"title")]/a/@href'), [article])
            self.assertEqual(card.xpath('./small[contains(@class,"source")]/a/@href'), [source])
            self.assertEqual(card.xpath('./small[contains(@class,"date")]/text()')[0].strip(), date)
            self.assertTrue(card.xpath('./p[contains(@class,"summary")]/text()')[0].strip())
            self.assertEqual(card.xpath('./h4/a/@target'), ["_blank"])
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
