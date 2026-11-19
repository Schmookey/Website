"""Webrings redesign: one outer centre panel, approved header, all nine rings intact."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "body .layout.site-panel-layout > main.center.webrings-main"
SECTION = "WEBRINGS CENTRE ONLY — APPROVED SINGLE PANEL / 16-BIT HEADER"
RINGS = ["Dinhe", "Hotline", "Hyperlink", "RETROWEB", "DotComBoom",
         "IndieWebring", "Fediring", "CDRing", "Wii Ring"]


class WebringsCentrePanelTests(unittest.TestCase):
    def test_one_outer_panel_without_nested_decorative_panel(self):
        page = html.parse(str(ROOT / "webrings.html"))
        mains = page.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " site-panel-layout ")]'
                           '/main[contains(concat(" ", normalize-space(@class), " "), " webrings-main ")]')
        self.assertEqual(len(mains), 1)
        main = mains[0]
        self.assertIn("center", main.get("class").split())
        self.assertEqual(main.xpath("./article[@class='panel']"), [])
        self.assertEqual(main.xpath("./header[@class='webrings-16bit-header']/h2/text()"), ["WEBRINGS"])
        self.assertEqual(main.xpath("./header[@class='webrings-16bit-header']/p[@class='webrings-16bit-overline']/text()"),
                         ["SCHMOOKEY.XYZ / 16-BIT WEBRINGS"])
        self.assertEqual(main.xpath("./header[@class='webrings-16bit-header']/p[@class='webrings-16bit-intro']/text()"),
                         ["My Communities"])
        grid = main.xpath("./div[@class='trophy-room']/div[@class='trophy-grid']")
        self.assertEqual(len(grid), 1)
        self.assertEqual(len(grid[0].xpath("./div[@class='trophy']")), 9)
        names = ["".join(node.itertext()).replace("🏆", "").strip()
                 for node in grid[0].xpath("./div[@class='trophy']/div[@class='trophy-title']")]
        self.assertEqual(names, RINGS)

    def test_original_webring_links_and_widgets_preserved(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        self.assertGreaterEqual(len(grid.xpath(".//a[@href]")), 10)
        self.assertEqual(len(grid.xpath(".//iframe[@src]")), 2)
        self.assertEqual(len(grid.xpath(".//script[@src]")), 3)
        self.assertEqual(len(page.xpath("//script[@src='/assets/js/main.js']")), 1)
        self.assertEqual(len(page.xpath("//aside[contains(@class,'site-panel-sidebar')]")), 1)
        self.assertEqual(len(page.xpath("//aside//section[@class='site-search-widget']")), 1)
        self.assertEqual(len(page.xpath("//aside//section[contains(@class,'article-social-badges')]")), 1)
        self.assertEqual(len(page.xpath("//aside//section[contains(@class,'article-likes-badges')]")), 1)

    def test_new_css_is_scoped_and_existing_card_motion_is_retained(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertEqual(css.count(SECTION), 1)
        section = css.split(SECTION, 1)[1].split("*/", 1)[1].split(
            "CHANGELOG CENTRE ONLY — 16-BIT HOME-STYLE PANELS", 1)[0]
        for selector in re.findall(r"(?:^|\n)([^{}]+)\{", section):
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for part in selector.split(","):
                self.assertTrue(part.strip().startswith(SCOPE), repr(part))
        self.assertIn("repeating-linear-gradient", section)
        self.assertIn("background: #101832", section)
        self.assertIn("border: 3px solid #1e40ff", section)
        self.assertIn("margin-top: 0;", section)
        self.assertIn("min-height: 126px;", section)
        self.assertIn("display: flex;", section)
        self.assertIn("justify-content: center;", section)
        self.assertIn("gap: 16px;", section)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", section)
        self.assertIn("prefers-reduced-motion: reduce", section)
        self.assertIn("background: transparent;", section)
        self.assertIn("transform:translateY(-4px) scale(1.02)", css)


if __name__ == "__main__":
    unittest.main()
