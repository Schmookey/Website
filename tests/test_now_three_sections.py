"""The Now page stays a three-paragraph Mega Drive-inspired snapshot."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]


class NowThreeSectionsTests(unittest.TestCase):
    def test_three_conversational_sections_no_inventory_lists(self):
        doc = html.parse(str(ROOT / "now.html"))
        panels = doc.xpath('//main[contains(concat(" ",normalize-space(@class)," ")," now-main ")]//section[contains(concat(" ",normalize-space(@class)," ")," now-16bit-card ")]')
        self.assertEqual(len(panels), 3)
        headings = [panel.xpath('string(./div/h2)').strip() for panel in panels]
        self.assertEqual(headings, ["CURRENT CHAPTER", "MAIN QUEST", "SIDE QUESTS"])
        for i, panel in enumerate(panels, start=1):
            self.assertEqual(panel.xpath('./div/span[contains(@class,"now-16bit-slot")]/text()'),
                             [f"{i:02d} / 03"])
            paragraph = panel.xpath('./p')
            self.assertEqual(len(paragraph), 1)
            self.assertGreater(len(" ".join(paragraph[0].itertext()).strip()), 65)
            self.assertFalse(panel.xpath('.//ul | .//ol | .//li'))
            self.assertEqual(panel.xpath('./div/h2/@id'), [panel.get("aria-labelledby")])
        self.assertEqual(doc.xpath('//main//h1/text()'), ["NOW"])
        self.assertEqual(len(doc.xpath('//main//time[@datetime]')), 1)

    def test_shared_site_shell_and_styling_are_unchanged(self):
        doc = html.parse(str(ROOT / "now.html"))
        self.assertEqual(len(doc.xpath('//header[@class="header"]//img[@src="/assets/images/header-banner.webp"]')), 1)
        self.assertEqual(len(doc.xpath('//aside[contains(@class,"site-panel-sidebar")]')), 1)
        self.assertEqual(len(doc.xpath('//nav[@class="menu"]')), 1)
        self.assertEqual(len(doc.xpath('//footer[@class="footer"]')), 1)
        self.assertFalse(doc.xpath('//main//*[contains(@class,"jrpg-window")]'))
        style = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".now-16bit-card", style)
        # Explicit stylesheet prevents a stale cached copy of global CSS
        # from leaving the newly renamed Now components unstyled.
        self.assertEqual(doc.xpath('//link[@rel="stylesheet"][@href="/assets/css/now-16bit.css"]/@href'),
                         ["/assets/css/now-16bit.css"])
        dedicated = (ROOT / "assets/css/now-16bit.css").read_text(encoding="utf-8")
        self.assertIn(".now-16bit-card", dedicated)
        self.assertIn(".now-16bit-header", dedicated)
        self.assertIn("#1e40ff", style)
        self.assertIn("#c1121f", style)
        self.assertIn("focus-visible", style)


if __name__ == "__main__":
    unittest.main()
