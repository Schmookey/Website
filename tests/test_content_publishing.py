"""Regression tests for the offline publishing generator and accessible cards."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_content", ROOT / "scripts/build_content.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ContentPublishingTests(unittest.TestCase):
    def test_first_sentence_is_the_default_blurb(self):
        doc = html.fromstring(
            '<html><div class="e-content"><figure><img src="/assets/images/home.png" '
            'alt="Screenshot"></figure><p>First complete sentence. Another sentence.</p></div></html>'
        )
        self.assertEqual(builder.first_sentence(doc), "First complete sentence.")
        card = builder.make_card(ROOT, {
            "url": "/blog/posts/coding_vibes.html",
            "title": "Example article",
            "date": "2026-11-17T09:00:00+00:00",
        }, doc)
        self.assertIn('class="p-summary">First complete sentence.</p>', card)
        self.assertIn('src="/assets/images/home.png"', card)
        self.assertIn('class="post-card-area-link"', card)
        self.assertIn('aria-hidden="true" tabindex="-1"', card)
        self.assertEqual(card.count('href="/blog/posts/coding_vibes.html"'), 4)

    def test_current_editorial_card_metadata_is_preserved(self):
        posts = json.loads((ROOT / "assets/data/posts.json").read_text(encoding="utf-8"))
        by_name = {post["title"]: post for post in posts}
        november = by_name["November Update"]
        self.assertEqual(november["cardImage"], "/assets/images/Schmookey_Riverfront.png")
        self.assertTrue(november["cardBlurb"].startswith("I reckon November"))
        music = by_name["ListenBrainz"]
        self.assertEqual(music["cardTitle"], "My exploration of music")
        doc = builder.get_post(ROOT, music)
        rendered = builder.make_card(ROOT, music, doc)
        self.assertIn("My exploration of music", rendered)
        self.assertIn('src="/assets/images/listenbrainz_logo.png"', rendered)

    def test_generated_indexes_remain_semantic_and_complete(self):
        records, updates = builder.content_items(ROOT)
        self.assertGreaterEqual(len(records), 10)
        result = builder.build_cards(ROOT, records)
        for section, page in builder.INDEXES.items():
            parsed = html.fromstring(result[page])
            cards = parsed.xpath('//main[contains(@class,"h-feed")]/article[contains(@class,"post-card")]')
            expected = [p for p, _ in records if p["section"] == section]
            self.assertEqual(len(cards), len(expected))
            for card in cards:
                self.assertEqual(len(card.xpath('./a[@class="post-card-area-link"]')), 1)
                links = card.xpath('.//a[contains(@class,"u-url")]/@href')
                self.assertEqual(len(links), 1)

    def test_all_feeds_match_metadata(self):
        records, updates = builder.content_items(ROOT)
        outputs = builder.build_feeds(ROOT, records, updates)
        jsonfeed = json.loads(outputs["feed.json"])
        self.assertGreaterEqual(len(jsonfeed["items"]), len(records) + len(updates))
        self.assertEqual(jsonfeed["items"][0]["title"], "November Update")
        self.assertIn("<item>", outputs["feed.xml"])
        self.assertIn("November Update", outputs["atom.xml"])


    def test_sitemap_contains_all_published_posts_and_public_pages(self):
        import xml.etree.ElementTree as ET
        records, updates = builder.content_items(ROOT)
        xml_text = builder.build_sitemap(ROOT, records, updates)
        root = ET.fromstring(xml_text)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        locs = [entry.text for entry in root.findall(f"{ns}url/{ns}loc")]
        self.assertIn("https://schmookey.xyz/blog/posts/november_update.html", locs)
        self.assertIn("https://schmookey.xyz/blog/", locs)
        self.assertIn("https://schmookey.xyz/music/", locs)
        self.assertIn("https://schmookey.xyz/now.html", locs)
        self.assertIn("https://schmookey.xyz/privacy.html", locs)
        self.assertIn("https://schmookey.xyz/changelog.html", locs)
        self.assertEqual(len(locs), len(set(locs)))
        notes = json.loads((ROOT / "assets/data/notes.json").read_text(encoding="utf-8"))
        self.assertEqual(len(locs), len(builder.SITEMAP_PAGES) + len(records) + len(notes))
        self.assertNotIn("https://schmookey.xyz/blog/posts/blog-template.html", locs)
        self.assertNotIn("https://schmookey.xyz/404.html", locs)
        by_loc = {
            entry.findtext(f"{ns}loc"): entry.findtext(f"{ns}lastmod")
            for entry in root.findall(f"{ns}url")
        }
        self.assertEqual(by_loc["https://schmookey.xyz/blog/posts/november_update.html"],
                         "2026-11-15")
        self.assertEqual(by_loc["https://schmookey.xyz/now.html"], "2026-11-11")
        self.assertEqual(by_loc["https://schmookey.xyz/changelog.html"], "2026-11-13")
        self.assertEqual(xml_text, builder.build_sitemap(ROOT, records, updates))

    def test_adding_new_post_updates_sitemap_without_hard_coding(self):
        records, updates = builder.content_items(ROOT)
        # Derive from a fresh metadata record; no edits to the sitemap are needed.
        test_post = dict(records[0][0], url="/blog/posts/new-example.html",
                         date="2026-11-17T12:00:00+00:00")
        output = builder.build_sitemap(ROOT, [*records, (test_post, records[0][1])], updates)
        self.assertIn("https://schmookey.xyz/blog/posts/new-example.html", output)
        self.assertIn("<lastmod>2026-11-17</lastmod>", output)



if __name__ == "__main__":
    unittest.main()
