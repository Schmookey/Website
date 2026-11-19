"""Notes list heading matches Now without changing the generated Notes stream."""
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "body .layout.site-panel-layout > main.center.panel.notes-page > .notes-heading.notes-16bit-header"


class NotesCentreHeaderTests(unittest.TestCase):
    def test_existing_feed_heading_rss_and_entries_remain(self):
        doc = html.parse(str(ROOT / "notes/index.html"))
        main = doc.xpath('//main[contains(concat(" ",normalize-space(@class)," ")," notes-page ")]')
        self.assertEqual(len(main), 1)
        self.assertIn("h-feed", main[0].get("class").split())
        headers = main[0].xpath('./header[contains(concat(" ",normalize-space(@class)," ")," notes-16bit-header ")]')
        self.assertEqual(len(headers), 1)
        header = headers[0]
        self.assertEqual(header.xpath("./h1[@class='p-name']/text()"), ["NOTES"])
        self.assertEqual(header.xpath("./p[@class='notes-16bit-overline']/text()"),
                         ["SCHMOOKEY.XYZ / 16-BIT NOTES"])
        self.assertIn("Short thoughts, interesting discoveries and things worth sharing", 
                      " ".join(header.itertext()))
        self.assertEqual(header.xpath(".//a/@href"), ["/notes/feed.xml"])
        self.assertEqual(len(main[0].xpath('./section[@class="notes-stream"]')), 1)
        self.assertIn("<!-- BEGIN GENERATED NOTES -->",
                      (ROOT / "notes/index.html").read_text(encoding="utf-8"))
        self.assertEqual(doc.xpath('//link[@rel="stylesheet"][@href="/assets/css/notes-16bit-header.css"]/@href'),
                         ["/assets/css/notes-16bit-header.css"])
        self.assertEqual(len(doc.xpath("//aside[contains(@class,'site-panel-sidebar')]")), 1)

    def test_css_scoped_exclusively_to_notes_heading(self):
        css = (ROOT / "assets/css/notes-16bit-header.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertIn("background: #101832;", css)
        self.assertIn("border: 3px solid #1e40ff;", css)
        self.assertIn("text-shadow: 3px 3px 0 #c1121f;", css)
        self.assertIn("repeating-linear-gradient", css)
        self.assertNotIn(".notes-stream", css)
        self.assertNotIn(".h-entry", css)
        for selector in re.findall(r"(?:^|\n)([^{}]+)\{", css):
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for part in selector.split(","):
                self.assertTrue(part.strip().startswith(SCOPE), repr(part))


if __name__ == "__main__":
    unittest.main()
