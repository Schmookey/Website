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


if __name__ == "__main__":
    unittest.main()
