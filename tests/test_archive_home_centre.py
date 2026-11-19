"""Blog and Music archive centre panels mirror home without affecting shared layout."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "body .layout.site-panel-layout > main.center.panel.archive-main"


class ArchiveHomeCentreTests(unittest.TestCase):
    def test_both_archives_have_home_style_headers_and_existing_filters(self):
        for filename, section, heading in (
            ("blog-archive.html", "blog", "Blog Archive"),
            ("music-archive.html", "music", "Music Archive"),
        ):
            with self.subTest(filename=filename):
                doc = html.parse(str(ROOT / filename))
                mains = doc.xpath('//div[contains(concat(" ",normalize-space(@class), " "), " site-panel-layout ")]'
                                  '/main[contains(concat(" ",normalize-space(@class), " "), " archive-main ")]')
                self.assertEqual(len(mains), 1)
                main = mains[0]
                self.assertIn("panel", main.get("class").split())
                header = main.xpath("./header[@class='archive-16bit-header']")
                self.assertEqual(len(header), 1)
                self.assertEqual(header[0].xpath("./h1/text()"), [heading])
                self.assertIn("SCHMOOKEY.XYZ / 16-BIT",
                              header[0].xpath("./p[@class='archive-16bit-overline']/text()")[0])
                self.assertEqual(main.xpath("./div[@id='archive-list']/@data-section"), [section])
                self.assertEqual(doc.xpath("//link[@rel='stylesheet'][@href='/assets/css/archive-home-16bit.css']/@href"),
                                 ["/assets/css/archive-home-16bit.css"])
                self.assertEqual(doc.xpath("//script[@src='/assets/js/archive.js']/@src"),
                                 ["/assets/js/archive.js"])
                self.assertEqual(doc.xpath("//script[@src='/assets/js/main.js']/@src"),
                                 ["/assets/js/main.js"])
                self.assertEqual(len(doc.xpath("//aside[contains(@class,'site-panel-sidebar')]")), 1)
                self.assertEqual(len(doc.xpath("//footer[@class='footer']")), 1)
                self.assertEqual(len(doc.xpath("//nav[@class='menu']")), 1)

    def test_dedicated_styles_are_scoped_and_behave_like_home(self):
        css = (ROOT / "assets/css/archive-home-16bit.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertIn("background: #101832;", css)
        self.assertIn("background: #0f1832;", css)
        self.assertIn("border: 3px solid #a5b9f8;", css)
        self.assertIn("border-left: 7px solid #c1121f;", css)
        self.assertIn("border-radius: 0;", css)
        self.assertIn("text-decoration: none;", css)
        self.assertIn("position: absolute;", css)
        self.assertIn("inset: 0;", css)
        self.assertIn("transform: translateY(-3px);", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("focus-visible", css)
        self.assertNotIn("#site-updates", css)
        for selector in re.findall(r"(?:^|\n)([^{}]+)\{", css):
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for item in selector.split(","):
                self.assertTrue(item.strip().startswith(SCOPE), repr(item))


if __name__ == "__main__":
    unittest.main()
