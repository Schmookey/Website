"""The 16-bit update-card redesign must affect only the homepage centre feed."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
START = "HOME PAGE: LATEST UPDATES ONLY — 16-BIT PANEL STYLING"
SCOPE = "body .layout.site-panel-layout.site-panel-three-col > main.center.panel #site-updates > .activity-card"


class HomeLatestUpdatesStyleTests(unittest.TestCase):
    def test_only_homepage_centre_updates_are_restyled(self):
        page = html.parse(str(ROOT / "index.html"))
        self.assertEqual(
            page.xpath('//main[contains(concat(" ",normalize-space(@class)," ")," center ")]'
                       '/div[@id="site-updates"]/@id'),
            ["site-updates"]
        )
        self.assertEqual(page.xpath('//main/h2/text()'), ["Latest Updates"])
        self.assertEqual(len(page.xpath('//aside[contains(@class,"left")]')), 1)
        self.assertEqual(len(page.xpath('//aside[contains(@class,"right")]')), 1)

        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertEqual(css.count(START), 1)
        # Every selector in the new rules targets a direct activity card
        # belonging to the homepage's centre #site-updates container.
        scoped = css.split(START, 1)[1]
        for selector in re.findall(r"(?:^|\n)([^{}]+)\{", scoped):
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for part in selector.split(","):
                self.assertTrue(part.strip().startswith(SCOPE), part)
        self.assertIn("transform: translateY(-3px);", scoped)
        self.assertIn("border-left: 7px solid #c1121f;", scoped)
        self.assertIn("border-radius: 0;", scoped)

    def test_existing_data_rendering_is_untouched(self):
        js = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        self.assertIn('"site-updates"', js)
        self.assertIn('class="activity-card ${escapeHTML(item.type)}"', js)
        self.assertIn("sortByNewest(updates).slice(0, 10)", js)


if __name__ == "__main__":
    unittest.main()
