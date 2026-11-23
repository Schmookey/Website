"""Webrings redesign: one outer centre panel, approved header, all thirteen featured sites intact."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "body .layout.site-panel-layout > main.center.webrings-main"
SECTION = "WEBRINGS CENTRE ONLY — APPROVED SINGLE PANEL / 16-BIT HEADER"
RINGS = ["Dinhe", "Hotline", "Hyperlink", "RETROWEB", "DotComBoom",
         "IndieWebring", "Fediring", "CDRing", "Wii Ring", "BlogR Directory", "*nixRing", "RSS Webring", "1.44MB Webring"]


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
        self.assertEqual(len(grid[0].xpath("./div[@class='trophy']")), 13)
        self.assertEqual(len(grid[0].xpath("./div[@class='trophy trophy-empty-slot']")), 2)
        names = ["".join(node.itertext()).replace("🏆", "").strip()
                 for node in grid[0].xpath("./div[@class='trophy']/div[@class='trophy-title']")]
        self.assertEqual(names, RINGS)

    def test_blogr_badge_scales_inside_a_complete_three_slot_row(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        slots = grid.xpath("./div[contains(concat(' ', normalize-space(@class), ' '), ' trophy ')]")
        self.assertEqual(len(slots), 15)
        self.assertEqual([slot.get("class") for slot in slots[9:12]],
                         ["trophy", "trophy", "trophy"])
        badge = slots[9].xpath('./div[@class="webring-content"]/a[@class="blogr-directory-link"]')[0]
        self.assertEqual(badge.get("href"), "https://blogr.directory")
        self.assertEqual(badge.get("target"), "_blank")
        self.assertEqual(set(badge.get("rel", "").split()), {"noopener", "noreferrer"})
        image = badge.xpath("./img")[0]
        self.assertEqual(image.get("src"), "https://blogr.directory/share-blogr-image.png")
        self.assertEqual(image.get("alt"), "Listed on BlogR Directory")
        self.assertEqual(image.get("width"), "250")
        self.assertIn("max-width: 100%", image.get("style", ""))
        self.assertEqual(slots[11].get("class"), "trophy")

    def test_linuxring_mint_widget_fills_the_next_sticker_slot(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        linuxring = grid.xpath("./div[@class='trophy'][div[@class='trophy-title'][contains(., '*nixRing')]]")
        self.assertEqual(len(linuxring), 1)
        script = linuxring[0].xpath(".//div[contains(@class, 'linuxring-widget')]/script")[0]
        self.assertEqual(script.get("src"), "https://softmachine.dev/webring/linuxring/ring.js")
        self.assertEqual(script.get("data-icon"), "mint")
        self.assertIsNotNone(script.get("defer"))
        fallback = linuxring[0].xpath(".//noscript/a")[0]
        self.assertEqual(fallback.get("href"), "https://softmachine.dev/webring/linuxring/")
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".linuxring-widget #nixring", css)
        self.assertIn("flex-wrap: wrap;", css)

    def test_rss_web_ring_uses_own_site_url_and_fills_fourth_row(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        cards = grid.xpath("./div[@class='trophy']")
        self.assertEqual(len(cards), 13)
        rss = cards[11]
        self.assertEqual(rss.xpath("./div[@class='trophy-title']/text()"), ["🏆 RSS Webring"])
        links = rss.xpath(".//nav[@class='rssring-nav']/a")
        self.assertEqual(len(links), 3)
        for link, action in zip(links, ("previous", "random", "next")):
            self.assertEqual(
                link.get("href"),
                "https://webri.ng/webring/rssring/" + action
                + "?via=https%3A%2F%2Fschmookey.xyz%2F")
        self.assertNotIn("bohemiansultriness", html.tostring(rss, encoding="unicode"))
        self.assertEqual(rss.xpath(".//p[@class='rssring-label']/a/@href"),
                         ["https://webri.ng/webring/rssring"])
        self.assertEqual(len(grid.xpath("./div[@class='trophy trophy-empty-slot']")), 2)
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".rssring-nav", css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", css)

    def test_floppy_disk_webring_fills_first_slot_of_a_new_three_card_row(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        slots = grid.xpath("./div[contains(concat(' ', normalize-space(@class), ' '), ' trophy ')]")
        self.assertEqual(len(slots), 15)
        self.assertEqual([slot.get("class") for slot in slots[-3:]],
                         ["trophy", "trophy trophy-empty-slot", "trophy trophy-empty-slot"])
        floppy = slots[-3]
        self.assertEqual(floppy.xpath("./div[@class='trophy-title']/text()"),
                         ["🏆 1.44MB Webring"])
        nav = floppy.xpath(".//nav[@class='floppy-ring-nav']")[0]
        self.assertEqual(nav.xpath("./a/@href"),
                         ["https://1.44mb.club/prev", "https://1.44mb.club/next"])
        self.assertEqual(nav.xpath("./a/text()"), ["<<", ">>"])
        self.assertEqual(nav.xpath("./span/text()"), ["💾"])
        self.assertTrue(all(slot.get("aria-hidden") == "true" for slot in slots[-2:]))
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn(".trophy-grid .floppy-ring-nav", css)
        self.assertIn("flex-wrap: wrap;", css)

    def test_original_webring_links_and_widgets_preserved(self):
        page = html.parse(str(ROOT / "webrings.html"))
        grid = page.xpath('//main[contains(@class, "webrings-main")]//div[@class="trophy-grid"]')[0]
        self.assertGreaterEqual(len(grid.xpath(".//a[@href]")), 10)
        self.assertEqual(len(grid.xpath(".//iframe[@src]")), 2)
        self.assertEqual(len(grid.xpath(".//script[@src]")), 4)
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
