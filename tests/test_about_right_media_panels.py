"""About page media widgets must use independent right-hand sidebar panels.

These structural checks are offline and do not contact the widget APIs.
"""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]


class AboutRightMediaPanelsTests(unittest.TestCase):
    def test_three_separate_panels_preserve_widget_mount_points(self):
        doc = html.parse(str(ROOT / "about.html"))
        sidebar = doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," site-panel-three-col ")]/aside[contains(concat(" ",normalize-space(@class)," ")," about-media-sidebar ")]')
        self.assertEqual(len(sidebar), 1)
        panels = sidebar[0].xpath('./section[contains(concat(" ",normalize-space(@class)," ")," about-media-panel ")]')
        self.assertEqual(len(panels), 3)
        self.assertEqual([panel.xpath("./h2/text()")[0] for panel in panels],
                         ["NOW LISTENING", "NOW READING", "LAST WATCHED"])
        for panel in panels:
            self.assertEqual(len(panel.xpath('./div[contains(@class,"about-media-panel-content")]')), 1)
            self.assertEqual(len(panel.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," media-widget ")]')), 1)

        self.assertEqual(len(panels[0].xpath('.//*[@id="latest-listen"]')), 1)
        for key in ("listen-cover", "listen-track", "listen-artist", "listen-album",
                    "listen-link", "mf2-listen-of"):
            self.assertEqual(len(panels[0].xpath('.//*[@id=$id]', id=key)), 1)
        self.assertEqual(panels[0].xpath('.//*[@id="listen-link"]/@href'),
                         ["https://listenbrainz.org/user/jon_cass"])

        book = panels[1].xpath('.//article[contains(concat(" ",normalize-space(@class)," ")," h-entry ")]')
        self.assertEqual(len(book), 1)
        self.assertEqual(book[0].xpath('.//a[contains(@href,"bookwyrm.social/book/")]/@href')[0],
                         "https://bookwyrm.social/book/902505/s/walking-practice")
        self.assertTrue(book[0].xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," p-read-of ")]'))
        self.assertTrue(book[0].xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," h-cite ")]'))
        self.assertEqual(len(panels[2].xpath('.//*[@id="trakt-latest-card"]')), 1)
        self.assertEqual(panels[2].xpath('.//a[contains(@class,"trakt-live-links")]/@href'), [])
        self.assertEqual(panels[2].xpath('.//p[contains(@class,"trakt-live-links")]/a/@href'),
                         ["/now-watching.html"])

    def test_existing_scripts_and_other_sidebars_unchanged(self):
        doc = html.parse(str(ROOT / "about.html"))
        self.assertEqual(len(doc.xpath('//script[@src="/assets/js/main.js"]')), 1)
        self.assertEqual(len(doc.xpath('//script[@src="/assets/js/trakt-history.js"]')), 1)
        self.assertEqual(len(doc.xpath('//aside[contains(@class,"site-panel-sidebar")]')), 1)
        self.assertEqual(len(doc.xpath('//aside[contains(@class,"about-media-sidebar")]//script[contains(text(),"annotateListen")]')), 1)

    def test_css_uses_existing_16_bit_panel_treatment(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("ABOUT PAGE — THREE INDEPENDENT RIGHT SIDEBAR PANELS", css)
        self.assertIn(".about-media-sidebar > .about-media-panel{", css)
        self.assertIn(".about-media-panel > h2{", css)
        for color in ("#0b0f1f", "#c1121f", "#1e40ff"):
            self.assertIn(color, css)


if __name__ == "__main__":
    unittest.main()
