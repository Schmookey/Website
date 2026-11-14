"""Offline tests for crawler-readable static Trakt Microformats2 markup."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/sync_trakt_microformats.py"
spec = importlib.util.spec_from_file_location("trakt_microformats", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class StaticTraktTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.about = self.base / "about.html"
        self.snapshot = self.base / "trakt.json"
        self.about.write_text("Before " + sync.START +
                              "old static card" + sync.END + " After",
                              encoding="utf-8")

    def write_snapshot(self, title="New Watch", link="https://trakt.tv/shows/sample"):
        self.snapshot.write_text(json.dumps({
            "generated_at": "2026-11-14T04:00:00Z",
            "items": [{"title": title, "type": "TV Show", "episode": "Pilot",
                       "season": 1, "episode_number": 2,
                       "watched_at": "2026-11-13T20:03:00Z", "link": link,
                       "cover": "https://image.tmdb.org/t/p/w200/sample.jpg"}]
        }), encoding="utf-8")

    def test_html_entry_is_regenerated_and_idempotent(self):
        self.write_snapshot()
        self.assertTrue(sync.synchronise(self.about, self.snapshot))
        result = self.about.read_text(encoding="utf-8")
        self.assertIn('class="media-card trakt-about-card h-entry"', result)
        self.assertIn('class="u-watch-of" href="https://trakt.tv/shows/sample"', result)
        self.assertIn('S01E02 · Pilot', result)
        self.assertIn('class="media-submeta dt-published"', result)
        self.assertTrue(result.startswith("Before "))
        self.assertTrue(result.endswith(" After"))
        self.assertFalse(sync.synchronise(self.about, self.snapshot))

    def test_escaping(self):
        self.write_snapshot('<script>alert("x")</script>')
        self.assertTrue(sync.synchronise(self.about, self.snapshot))
        result = self.about.read_text(encoding="utf-8")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_rejects_unsafe_link_without_damaging_file(self):
        original = self.about.read_bytes()
        self.write_snapshot(link="https://evil.example/show")
        with self.assertRaises(ValueError):
            sync.synchronise(self.about, self.snapshot)
        self.assertEqual(original, self.about.read_bytes())

    def test_missing_markers_do_not_modify_file(self):
        self.about.write_text("<html></html>", encoding="utf-8")
        self.write_snapshot()
        with self.assertRaises(ValueError):
            sync.synchronise(self.about, self.snapshot)
        self.assertEqual(self.about.read_text(encoding="utf-8"), "<html></html>")

    def test_no_history_keeps_existing_html(self):
        self.snapshot.write_text('{"items":[]}', encoding="utf-8")
        self.assertFalse(sync.synchronise(self.about, self.snapshot))
        self.assertIn("old static card", self.about.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
