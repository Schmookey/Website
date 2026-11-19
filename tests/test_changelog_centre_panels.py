"""The Changelog's 16-bit redesign is limited to its centre-content panel."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "body .layout.site-panel-layout > main.center.panel.changelog-main"
SECTION = "CHANGELOG CENTRE ONLY — 16-BIT HOME-STYLE PANELS"


class ChangelogCentrePanelTests(unittest.TestCase):
    def test_header_and_changelog_entries_allow_future_versions(self):
        """New user-written versions must not break CI due to fixed entry counts."""
        import re

        page = html.parse(str(ROOT / "changelog.html"))
        main = page.xpath("//main[contains(concat(' ', normalize-space(@class), ' '), ' changelog-main ')]")
        self.assertEqual(len(main), 1)
        self.assertEqual(main[0].xpath("./header[@class='changelog-16bit-header']/h2/text()"),
                         ["Changelog"])

        cards = main[0].xpath("./div[@class='changelog-card']")
        self.assertGreaterEqual(len(cards), 1, "Changelog needs at least one version")
        versions = []
        for card in cards:
            title = "".join(card.xpath("./div[@class='changelog-card-title']/text()")).strip()
            match = re.fullmatch(r"Version (\d+)\.(\d+)\s*—", title)
            self.assertIsNotNone(match, f"Missing version title: {title!r}")
            versions.append((int(match.group(1)), int(match.group(2))))
            self.assertEqual(
                len(card.xpath("./div[@class='changelog-card-title']//span[contains("
                               "concat(' ', normalize-space(@class), ' '), ' auto-date ')]")),
                1, f"{title} must have one date placeholder"
            )
            entries = card.xpath("./ul[@class='changelog-card-list']/li")
            self.assertGreaterEqual(len(entries), 1, f"{title} needs at least one entry")
            for item in entries:
                self.assertTrue(item.text_content().strip(), f"{title} has an empty entry")

        self.assertEqual(len(versions), len(set(versions)), "Duplicate changelog versions")
        self.assertEqual(versions, sorted(versions, reverse=True),
                         "Newest changelog versions must appear first")
        self.assertEqual(len(page.xpath("//aside[contains(@class,'site-panel-sidebar')]")), 1)
        self.assertEqual(len(page.xpath("//script[@src='/assets/js/main.js']")), 1)
        self.assertFalse(main[0].xpath(".//*[@class='jrpg-window']"))

    def test_css_is_scoped_and_preserves_hover_movement(self):
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertEqual(css.count(SECTION), 1)
        section = css.split(SECTION, 1)[1].split("*/", 1)[1].split("HOME PAGE CENTRE: 16-BIT LATEST UPDATES HEADER ONLY", 1)[0]
        self.assertIn("transform: translateY(-3px);", section)
        self.assertIn("prefers-reduced-motion: reduce", section)
        self.assertIn("repeating-linear-gradient", section)
        self.assertIn("border-left: 7px solid #c1121f;", section)
        # Every new style targets a child of the Changelog centre panel.
        import re
        selectors = re.findall(r"(?:^|\n)([^{}]+)\{", section)
        for selector in selectors:
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for part in selector.split(","):
                self.assertTrue(part.strip().startswith(SCOPE), repr(part))


if __name__ == "__main__":
    unittest.main()
