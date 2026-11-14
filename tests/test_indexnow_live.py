"""Offline tests for safe IndexNow notifications from published pages."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts/indexnow_live_scan.py"
spec = importlib.util.spec_from_file_location("indexnow_live_scan", MODULE)
indexnow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(indexnow)

SITEMAP = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           b'<url><loc>https://schmookey.xyz/about.html</loc></url>'
           b'<url><loc>https://schmookey.xyz/blog/</loc></url>'
           b'<url><loc>https://other.example/</loc></url></urlset>')


class IndexNowTests(unittest.TestCase):
    def test_sitemap_restricts_urls_to_verified_host(self):
        urls = indexnow.urls_in_sitemap(SITEMAP)
        self.assertEqual(urls, [
            "https://schmookey.xyz/about.html", "https://schmookey.xyz/blog/"
        ])
        for url in ("https://evil.example/", "http://schmookey.xyz/about.html",
                    "https://schmookey.xyz.evil.example/about.html",
                    "https://schmookey.xyz/about.html?test=1"):
            self.assertFalse(indexnow.on_site(url))

    def test_noindex_directive_in_head(self):
        parser = indexnow.RobotsMetadata()
        parser.feed('<head><meta name="robots" content="nofollow, noindex"></head>')
        self.assertTrue(parser.noindex)
        parser = indexnow.RobotsMetadata()
        parser.feed('<body><meta name="robots" content="noindex"></body>')
        self.assertFalse(parser.noindex)

    def test_first_scan_only_baselines_then_changes_are_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "pages.json"
            html = {"https://schmookey.xyz/about.html": b"<html>One</html>",
                    "https://schmookey.xyz/blog/": b"<html>Blog</html>"}
            def fetch(url, kind):
                return SITEMAP if kind == "sitemap" else html[url]
            with patch.object(indexnow, "fetch", side_effect=fetch), \
                 patch.object(indexnow, "submit", return_value=200) as submission:
                first = indexnow.scan(state, "sample-key-123456")
                self.assertEqual(first["submitted"], 0)
                self.assertFalse(submission.called)
                self.assertTrue(state.is_file())
                unchanged = indexnow.scan(state, "sample-key-123456")
                self.assertEqual(unchanged["submitted"], 0)
                html["https://schmookey.xyz/about.html"] = b"<html>Updated</html>"
                changed = indexnow.scan(state, "sample-key-123456")
                self.assertEqual(changed["submitted"], 1)
                submission.assert_called_once_with(
                    ["https://schmookey.xyz/about.html"], "sample-key-123456"
                )

    def test_failed_indexnow_submission_preserves_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "pages.json"
            with patch.object(indexnow, "fetch",
                              side_effect=lambda url, kind: SITEMAP if kind == "sitemap" else b"v1"), \
                 patch.object(indexnow, "submit"):
                indexnow.scan(state, "sample-key-123456")
            original = state.read_bytes()
            with patch.object(indexnow, "fetch",
                              side_effect=lambda url, kind: SITEMAP if kind == "sitemap" else b"v2"), \
                 patch.object(indexnow, "submit", side_effect=RuntimeError("No acceptance")):
                with self.assertRaises(RuntimeError):
                    indexnow.scan(state, "sample-key-123456")
            self.assertEqual(original, state.read_bytes())

    def test_nonindexable_page_is_never_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "pages.json"
            with patch.object(indexnow, "fetch",
                              side_effect=lambda url, kind: SITEMAP if kind == "sitemap" else None), \
                 patch.object(indexnow, "submit") as submission:
                result = indexnow.scan(state, "sample-key-123456", force_all=True)
                self.assertEqual(result["submitted"], 0)
                submission.assert_not_called()

    def test_batch_submission_is_host_restricted(self):
        with self.assertRaises(ValueError):
            indexnow.submit(["https://evil.example/blog/"], "sample-key-123456")
        with self.assertRaises(ValueError):
            indexnow.submit(["https://schmookey.xyz/blog/"], "unsafe key with space")


if __name__ == "__main__":
    unittest.main()
