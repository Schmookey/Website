"""Offline checks for essential IndieWeb metadata on static site pages.

These tests deliberately do not send Webmentions or contact external services.
They verify GitHub's source HTML, not the separately hosted Neocities site.
"""
from pathlib import Path
import unittest

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://schmookey.xyz"
WEBMENTION = "https://webmention.io/schmookey.xyz/webmention"
POSTS = sorted((ROOT / "blog/posts").glob("*.html"))
POSTS = [p for p in POSTS if p.name != "blog-template.html"]


def has_class(tag, class_name):
    return class_name in (tag.get("class") or "").split()


class IndieWebMetadataTests(unittest.TestCase):
    def test_posts_are_discovered(self):
        self.assertGreaterEqual(len(POSTS), 7)

    def test_home_advertises_identity_feeds_and_webmentions(self):
        doc = html.parse(str(ROOT / "index.html"))
        self.assertEqual(
            doc.xpath('//link[@rel="webmention"]/@href'), [WEBMENTION]
        )
        self.assertTrue(doc.xpath('//body[contains(concat(" ",normalize-space(@class)," ")," h-card ")]'))
        for media_type in ("application/rss+xml", "application/atom+xml"):
            with self.subTest(media_type=media_type):
                self.assertEqual(len(doc.xpath(
                    '//link[@rel="alternate" and @type=$media]/@href',
                    media=media_type
                )), 1)

    def test_published_posts_have_discoverable_mf2_and_receiver(self):
        for page in POSTS:
            with self.subTest(page=page.name):
                doc = html.parse(str(page))
                canonical = DOMAIN + "/" + page.relative_to(ROOT).as_posix()
                self.assertEqual(doc.xpath('//link[@rel="canonical"]/@href'), [canonical])
                self.assertEqual(doc.xpath('//link[@rel="webmention"]/@href'), [WEBMENTION])
                entries = [tag for tag in doc.xpath("//article") if has_class(tag, "h-entry")]
                self.assertEqual(len(entries), 1, "Every article should expose one h-entry")
                entry = entries[0]
                descendants = list(entry.iter())
                self.assertTrue(
                    any(has_class(tag, "u-url") and tag.get("href") == canonical
                        for tag in descendants),
                    "Post u-url should match the canonical URL",
                )
                for required in ("p-name", "dt-published", "e-content", "u-author"):
                    self.assertTrue(
                        any(has_class(tag, required) for tag in descendants),
                        f"Article missing {required}",
                    )

    def test_feed_files_exist(self):
        for name in ("feed.xml", "atom.xml", "feed.json"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file())

    def test_about_profile_and_reading_microformats(self):
        doc = html.parse(str(ROOT / "about.html"))
        structured = doc.xpath('//script[@type="application/ld+json"]/text()')
        import json
        self.assertEqual(len(structured), 1)
        payload = json.loads(structured[0])
        self.assertEqual(payload["@type"], "ProfilePage")
        self.assertEqual(payload["mainEntity"]["@type"], "Person")
        book_cards = doc.xpath('//article[contains(concat(" ", normalize-space(@class), " "), " h-entry ")][.//*[contains(concat(" ", normalize-space(@class), " "), " p-read-of ")]]')
        self.assertEqual(len(book_cards), 1)
        self.assertTrue(book_cards[0].xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " h-cite ")]'))
        self.assertTrue(book_cards[0].xpath('.//img[contains(@src, "Walking Practice by Dolki Min.jpeg")]'))
        self.assertTrue(book_cards[0].xpath('.//a[@href="https://bookwyrm.social/book/902505/s/walking-practice"]'))
        self.assertTrue(doc.xpath('//*[@id="latest-listen"]'))
        self.assertTrue(doc.xpath('//*[@id="trakt-latest-card"]'))

    def test_blog_index_has_single_main_feed(self):
        doc = html.parse(str(ROOT / "blog/index.html"))
        self.assertEqual(len(doc.xpath('//main')), 1)
        self.assertEqual(len(doc.xpath('//main[contains(concat(" ", normalize-space(@class), " "), " h-feed ")]')), 1)
        self.assertGreaterEqual(len(doc.xpath('//main//article[contains(concat(" ", normalize-space(@class), " "), " h-entry ")]')), 9)

    def test_coding_vibes_has_blog_posting_and_project_microformats(self):
        import json
        doc = html.parse(str(ROOT / "blog/posts/coding_vibes.html"))
        structured = doc.xpath('//script[@type="application/ld+json"]/text()')
        self.assertEqual(len(structured), 1)
        payload = json.loads(structured[0])
        self.assertEqual(payload["@type"], "BlogPosting")
        self.assertEqual(payload["headline"], "Coding Vibes")
        self.assertEqual(payload["author"]["name"], "Schmookey")
        self.assertTrue(doc.xpath('//section[contains(concat(" ", normalize-space(@class), " "), " h-product ")]'))
        self.assertTrue(doc.xpath('//article[contains(concat(" ", normalize-space(@class), " "), " h-entry ")]'))

if __name__ == "__main__":
    unittest.main()
