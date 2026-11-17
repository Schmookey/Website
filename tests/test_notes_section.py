"""Notes is an independent section with a site-wide navigation entry."""
from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ET
from lxml import html

ROOT = Path(__file__).resolve().parents[1]


class NotesSectionTests(unittest.TestCase):
    def test_notes_between_random_and_now_on_every_page(self):
        pages = sorted(ROOT.rglob("*.html"))
        menu_pages = 0
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                doc = html.parse(str(page))
                menus = doc.xpath('//nav[contains(concat(" ",normalize-space(@class)," ")," menu ")]')
                if not menus:
                    # Verification pages, error pages and HTML fragments do not have the site navigation.
                    continue
                menu_pages += 1
                self.assertEqual(len(menus), 1)
                links = menus[0].xpath("./a/@href")
                self.assertIn("/random/", links)
                self.assertIn("/notes/", links)
                self.assertIn("/now.html", links)
                i = links.index("/random/")
                self.assertEqual(links[i + 1:i + 3], ["/notes/", "/now.html"])
        self.assertEqual(menu_pages, 28)

    def test_independent_empty_notes_feed_and_metadata(self):
        notes = html.parse(str(ROOT / "notes/index.html"))
        self.assertEqual(notes.xpath('//link[@rel="canonical"]/@href'), ["https://schmookey.xyz/notes/"])
        self.assertEqual(notes.xpath('//nav[contains(@class,"menu")]/a[@aria-current="page"]/@href'), ["/notes/"])
        self.assertEqual(len(notes.xpath('//main[contains(@class,"h-feed")]')), 1)
        self.assertEqual(len(notes.xpath('//main//article[contains(@class,"h-entry")]')), 0)
        self.assertTrue(notes.xpath('//main//p[contains(@class,"notes-empty")]'))
        self.assertEqual(notes.xpath('//link[@rel="webmention"]/@href'),
                         ["https://webmention.io/schmookey.xyz/webmention"])
        self.assertEqual(notes.xpath('//link[@href="/notes/feed.xml"]/@type'), ["application/rss+xml"])
        self.assertEqual(notes.xpath('//link[@href="/notes/atom.xml"]/@type'), ["application/atom+xml"])
        self.assertEqual(json.loads((ROOT / "assets/data/notes.json").read_text()), [])
        rss = ET.parse(ROOT / "notes/feed.xml").getroot()
        self.assertEqual(rss.findtext("./channel/title"), "Schmookey Notes")
        atom = ET.parse(ROOT / "notes/atom.xml").getroot()
        self.assertEqual(atom.findtext("{http://www.w3.org/2005/Atom}title"), "Schmookey Notes")

    def test_sitemap_includes_notes(self):
        data = (ROOT / "sitemap.xml").read_text()
        self.assertIn("<loc>https://schmookey.xyz/notes/</loc>", data)


if __name__ == "__main__":
    unittest.main()
