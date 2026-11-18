"""Offline safety tests for post-deployment social syndication."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verified_syndication", ROOT / "scripts/verified_syndication.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Response:
    status = 200
    headers = {"Content-Type": "text/html; charset=utf-8"}

    def __init__(self, path: str, body: str):
        self.url = module.BASE + path
        self.body = body.encode("utf-8")

    def geturl(self):
        return self.url

    def read(self, size):
        return self.body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Opener:
    def __init__(self, response):
        self.response = response

    def open(self, req, timeout):
        return self.response


class VerifiedSyndicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for folder in ("assets/data", "blog/posts", "notes", "social"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        (self.root / "social/syndication-state.json").write_text(
            '{"version":1,"entries":{}}', encoding="utf-8"
        )
        (self.root / "assets/data/notes.json").write_text("[]", encoding="utf-8")
        self.path = "/blog/posts/example.html"
        self.html = ('<html><head><link rel="canonical" href="'
                     + module.BASE + self.path
                     + '"/></head><body><div class="e-content">'
                     + 'An entirely new article with a recognisable opening paragraph.'
                     + '</div></body></html>')
        (self.root / self.path.lstrip("/")).write_text(self.html, encoding="utf-8")
        self.post = {"title": "Example", "section": "blog", "url": self.path,
                     "date": "2026-11-19T12:00:00+00:00"}
        (self.root / "assets/data/posts.json").write_text(json.dumps([self.post]), encoding="utf-8")

    def test_new_blog_is_opted_in_but_old_posts_are_excluded(self):
        self.assertEqual(len(list(module.candidates(self.root))), 1)
        posts = [dict(self.post, date="2026-03-01T00:00:00Z")]
        (self.root / "assets/data/posts.json").write_text(json.dumps(posts), encoding="utf-8")
        self.assertEqual(list(module.candidates(self.root)), [])

    def test_notes_default_to_website_only_and_have_individual_choices(self):
        note = {"id": "2026-11-19-120000-1234", "content": "A test note"}
        (self.root / "assets/data/notes.json").write_text(json.dumps([note]), encoding="utf-8")
        self.assertEqual(len(list(module.candidates(self.root))), 1)
        note["syndicate"] = "bluesky"
        (self.root / "assets/data/notes.json").write_text(json.dumps([note]), encoding="utf-8")
        self.assertEqual(list(module.candidates(self.root))[1]["platforms"], ("bluesky",))
        note["syndicate"] = "invalid"
        (self.root / "assets/data/notes.json").write_text(json.dumps([note]), encoding="utf-8")
        with self.assertRaises(module.PublicationError):
            list(module.candidates(self.root))

    def test_verification_requires_matching_canonical_and_content(self):
        target = next(module.candidates(self.root))
        self.assertEqual(module.verify_live(self.root, target, Opener(Response(self.path, self.html))),
                         module.BASE + self.path)
        stale = self.html.replace("An entirely new article", "Outdated article")
        with self.assertRaises(module.PublicationError):
            module.verify_live(self.root, target, Opener(Response(self.path, stale)))
        bad = Response(self.path, self.html)
        bad.url = module.BASE + "/wrong.html"
        with self.assertRaises(module.PublicationError):
            module.verify_live(self.root, target, Opener(bad))

    def test_preview_never_posts_or_fetches_and_pending_prevents_retries(self):
        with patch.object(module, "verify_live", side_effect=AssertionError("network")):
            module.run(self.root)
        ledger = module.read_ledger(self.root)
        ledger["entries"][self.path] = {"mastodon": {"status": "pending"},
                                       "bluesky": {"status": "posted"}}
        (self.root / module.LEDGER).write_text(json.dumps(ledger), encoding="utf-8")
        with patch.object(module, "verify_live", side_effect=AssertionError("network")):
            module.run(self.root, execute=False)

    def test_execution_requires_explicit_activation_before_network(self):
        with patch.dict("os.environ", {"SOCIAL_SYNDICATION_ENABLED": "false"}):
            with patch.object(module, "verify_live", side_effect=AssertionError("network")):
                with self.assertRaises(module.PublicationError):
                    module.run(self.root, execute=True)

    def test_account_checks_and_post_length(self):
        target = next(module.candidates(self.root))
        message = module.message(target, module.BASE + self.path, 270)
        self.assertIn(module.BASE + self.path, message)
        self.assertLessEqual(len(message), 270)
        with patch.dict("os.environ", {"MASTODON_ACCESS_TOKEN": "fake"}):
            with patch.object(module, "api_get", return_value={"username": "wrong"}):
                with self.assertRaises(module.PublicationError):
                    module.mastodon(target, module.BASE + self.path)

    def test_production_ledger_is_initially_empty(self):
        ledger = module.read_ledger(ROOT)
        self.assertEqual(ledger["version"], 1)
        self.assertEqual(ledger["entries"], {})


if __name__ == "__main__":
    unittest.main()
