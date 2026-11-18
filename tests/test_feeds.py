"""Keep RSS, Atom, and JSON feeds aligned with canonical post and update data."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from lxml import etree as LET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://schmookey.xyz"
ATOM = "{http://www.w3.org/2005/Atom}"


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def slug(title):
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", title.lower()))


class FeedConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = json.loads((ROOT / "feed.json").read_text(encoding="utf-8"))
        cls.rss = ET.parse(ROOT / "feed.xml").getroot()
        cls.atom = ET.parse(ROOT / "atom.xml").getroot()
        cls.posts = json.loads((ROOT / "assets/data/posts.json").read_text(encoding="utf-8"))
        cls.updates = json.loads((ROOT / "assets/data/site-updates.json").read_text(encoding="utf-8"))

    def test_all_sources_are_in_json_feed_with_consistent_dates(self):
        items = self.feed["items"]
        by_id = {item["id"]: item for item in items}
        self.assertEqual(len(by_id), len(items), "Feed IDs must be unique")
        self.assertEqual(
            [stamp(item["date_published"]) for item in items],
            sorted((stamp(item["date_published"]) for item in items), reverse=True),
        )
        for p in self.posts:
            ident = "urn:schmookey:post:" + Path(p["url"]).stem
            with self.subTest(post=p["title"]):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["url"], BASE + p["url"])
                self.assertEqual(stamp(by_id[ident]["date_published"]), stamp(p["date"]))
                self.assertEqual(by_id[ident]["title"], p["title"])
                self.assertTrue((ROOT / p["url"].lstrip("/")).is_file())
        for u in self.updates:
            ident = f"urn:schmookey:update:{slug(u['title'])}:{u['date']}"
            with self.subTest(update=u["title"]):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["url"], BASE + u["url"])
                self.assertEqual(stamp(by_id[ident]["date_published"]), stamp(u["date"]))

    def test_rss_human_readable_stylesheet(self):
        rss_text = (ROOT / "feed.xml").read_text(encoding="utf-8")
        self.assertIn('<?xml-stylesheet type="text/xsl" href="/assets/xsl/rss.xsl"?>', rss_text)
        xsl_path = ROOT / "assets/xsl/rss.xsl"
        self.assertTrue(xsl_path.is_file())
        stylesheet = LET.XSLT(LET.parse(str(xsl_path)))
        rendered = str(stylesheet(LET.parse(str(ROOT / "feed.xml"))))
        self.assertIn("Visit Schmookey", rendered)
        self.assertIn("https://schmookey.xyz/", rendered)
        self.assertIn("November Update", rendered)
        self.assertEqual(rendered.count('class="entry"'), len(self.feed["items"]))
        self.assertIn("https://schmookey.xyz/blog/posts/november_update.html", rendered)

    def test_rss_and_atom_match_json_feed(self):
        items = self.feed["items"]
        rss_items = self.rss.findall("./channel/item")
        atom_items = self.atom.findall(f"{ATOM}entry")
        self.assertEqual(len(rss_items), len(items))
        self.assertEqual(len(atom_items), len(items))
        for source, rss, atom in zip(items, rss_items, atom_items):
            with self.subTest(entry=source["id"]):
                self.assertEqual(rss.findtext("guid"), source["id"])
                self.assertEqual(rss.findtext("title"), source["title"])
                self.assertEqual(rss.findtext("link"), source["url"])
                self.assertEqual(stamp(source["date_published"]),
                                 parsedate_to_datetime(rss.findtext("pubDate")).astimezone(timezone.utc))
                self.assertEqual(rss.findtext("description"), source["content_text"])
                self.assertEqual(atom.findtext(f"{ATOM}id"), source["id"])
                self.assertEqual(atom.findtext(f"{ATOM}title"), source["title"])
                self.assertEqual(atom.find(f"{ATOM}link").get("href"), source["url"])
                self.assertEqual(stamp(atom.findtext(f"{ATOM}published")), stamp(source["date_published"]))
                self.assertEqual(atom.findtext(f"{ATOM}summary"), source["content_text"])
        newest = stamp(items[0]["date_published"])
        self.assertEqual(parsedate_to_datetime(self.rss.findtext("./channel/lastBuildDate")).astimezone(timezone.utc), newest)
        self.assertEqual(stamp(self.atom.findtext(f"{ATOM}updated")), newest)


if __name__ == "__main__":
    unittest.main()
