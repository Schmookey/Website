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

if __name__ == "__main__":
    unittest.main()
