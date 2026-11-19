"""Journal styling must match home within only their existing transparent centre areas."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = "/assets/css/journal-home-centre.css"

class JournalHomeStyleTests(unittest.TestCase):
    def test_journal_headers_and_scripts_remain_intact(self):
        specs = [
            ("listening.html", "listening-page", "Listening Journal",
             "listening-log", "assets/js/main.js"),
            ("now-watching.html", "watching-page", "Viewing Journal",
             "trakt-history", "assets/js/trakt-history.js"),
        ]
        for filename, page_class, title, container, script in specs:
            with self.subTest(filename=filename):
                page = html.parse(str(ROOT / filename))
                centre = page.xpath(
                    '//div[contains(concat(" ", normalize-space(@class), " "), " site-panel-layout ")]'
                    '/section[contains(concat(" ", normalize-space(@class), " "), " '+page_class+' ")]'
                )
                self.assertEqual(len(centre), 1)
                self.assertNotIn("panel", centre[0].get("class").split())
                self.assertEqual(centre[0].xpath('./header[@class="journal-home-header"]/h1/text()'), [title])
                self.assertEqual(len(centre[0].xpath('./header/p[@class="journal-home-overline"]')), 1)
                self.assertEqual(len(centre[0].xpath('./div[@id="'+container+'"]')), 1)
                self.assertEqual(page.xpath("//link[@rel='stylesheet'][@href='"+CSS_PATH+"']/@href"), [CSS_PATH])
                self.assertEqual(page.xpath("//script[@src='/"+script+"']/@src"), ["/"+script])
                self.assertEqual(len(page.xpath("//aside[contains(@class,'site-panel-sidebar')]")), 1)
                self.assertEqual(len(page.xpath("//footer[@class='footer']")), 1)
        watch = html.parse(str(ROOT / "now-watching.html"))
        self.assertEqual(watch.xpath('//a[contains(@href,"/profile/Pati3nt_Z3ro")]/@href'),
                         ["https://app.trakt.tv/profile/Pati3nt_Z3ro"])
        listen = html.parse(str(ROOT / "listening.html"))
        self.assertEqual(listen.xpath('//span[@id="listening-count"]/@id'), ["listening-count"])

    def test_all_rules_target_journal_centre_descendants(self):
        css = (ROOT / CSS_PATH.lstrip("/")).read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for rule in re.findall(r"(?:^|\n)([^{}]+)\{", css):
            selector = rule.strip()
            if selector.startswith("@media"):
                continue
            # Commas inside :is(...) are part of one selector, not a rule split.
            for part in selector.replace(":is(.listening-page, .watching-page)", ":is(.listening-page|.watching-page)").split(","):
                part = part.strip()
                self.assertTrue(part.startswith(
                    "body .layout.site-panel-layout > .centre-content"
                ), repr(part))
                self.assertTrue(
                    ".journal-home-" in part or
                    ".listening-log " in part or
                    "#trakt-history " in part or
                    "#trakt-history > " in part,
                    repr(part))
        # The centre shell itself must never receive a styled rule; a date divider may remove a shadow.
        self.assertNotIn(" > .centre-content:is(.listening-page, .watching-page) {", css)
        self.assertIn("border-left: 7px solid #c1121f;", css)
        self.assertIn("background: #0f1832;", css)
        self.assertIn("background: #101832;", css)
        self.assertIn("transform: translateY(-3px);", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("focus-visible", css)

    def test_original_journal_data_loaders_are_not_modified(self):
        main = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        trakt = (ROOT / "assets/js/trakt-history.js").read_text(encoding="utf-8")
        self.assertIn('id="listening-log"', (ROOT / "listening.html").read_text())
        self.assertIn('id="trakt-history"', (ROOT / "now-watching.html").read_text())
        self.assertIn('loadListeningJournal("jon_cass", 100)', main)
        self.assertIn('const LIVE_HISTORY =', trakt)

if __name__ == "__main__":
    unittest.main()
