"""Protect the published November article and archive links from ZIP regressions."""
import json
import unittest
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
POST_URL = "/blog/posts/november_update.html"
ARTICLE = ROOT / POST_URL.lstrip("/")


class NovemberPublishingTests(unittest.TestCase):
    def test_article_has_consistent_publish_date_and_indexability(self):
        page = html.fromstring(ARTICLE.read_text(encoding="utf-8"))
        publication = "2026-11-15T12:00:00+00:00"
        self.assertEqual(
            page.xpath("//time[contains(concat(' ',normalize-space(@class),' '),' dt-published ')]/@datetime")[0],
            publication,
        )
        metadata = page.xpath("//script[@type='application/ld+json']/text()")
        self.assertTrue(metadata)
        data = json.loads(metadata[0])
        self.assertEqual(data["datePublished"], publication)
        robots = page.xpath("//meta[@name='robots']/@content")
        self.assertFalse(any("noindex" in value.lower() for value in robots))

    def test_archive_links_point_to_existing_canonical_article(self):
        posts = json.loads((ROOT / "assets/data/posts.json").read_text(encoding="utf-8"))
        november = [entry for entry in posts if entry.get("title") == "November Update"]
        self.assertEqual(len(november), 1)
        self.assertEqual(november[0]["url"], POST_URL)
        self.assertTrue(ARTICLE.is_file())
        blog = html.fromstring((ROOT / "blog/index.html").read_text(encoding="utf-8"))
        article_links = blog.xpath("//a[contains(@href,'november_update')]/@href")
        self.assertTrue(article_links)
        self.assertTrue(all(link == POST_URL for link in article_links))
        self.assertEqual(
            blog.xpath("//a[contains(@href,'November%20Update')]/@href"), [],
        )


if __name__ == "__main__":
    unittest.main()
