"""Regression tests for public Trakt snapshot generation; no external requests."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/update_trakt_history.py"
spec = importlib.util.spec_from_file_location("trakt_updater", SCRIPT)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class TraktUpdaterTests(unittest.TestCase):
    def test_episode_metadata_is_retained(self):
        row = {
            "type": "episode", "watched_at": "2026-11-10T12:00:00Z",
            "show": {"title": "Sample Show", "year": 2026,
                     "ids": {"slug": "sample-show"}},
            "episode": {"title": "Pilot", "season": 1, "number": 1},
        }
        entry = updater.normalise(row, "", {})
        self.assertEqual(entry["type"], "TV Show")
        self.assertEqual(entry["episode_number"], 1)
        self.assertEqual(entry["link"], "https://trakt.tv/shows/sample-show")

    def test_403_keeps_existing_snapshot_and_explains_action(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trakt-history.json"
            target.write_text('{"items":[{"title":"Existing"}]}', encoding="utf-8")
            original = target.read_bytes()
            forbidden = HTTPError("https://api.trakt.tv/users/example/history", 403,
                                  "Forbidden", {}, None)
            with patch.dict(os.environ, {"TRAKT_CLIENT_ID": "test-client-id"}), \
                 patch.object(updater, "OUT", target), \
                 patch.object(updater, "get_json", side_effect=forbidden):
                with self.assertRaises(SystemExit) as error:
                    updater.main()
            self.assertIn("Production Client ID", str(error.exception))
            self.assertNotIn("test-client-id", str(error.exception))
            self.assertEqual(target.read_bytes(), original)

    def test_valid_public_history_replaces_snapshot(self):
        response = [{"type": "movie", "watched_at": "2026-11-10T12:00:00Z",
                     "movie": {"title": "Sample Movie", "year": 2024,
                               "ids": {"slug": "sample-movie"}}}]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trakt-history.json"
            with patch.dict(os.environ, {"TRAKT_CLIENT_ID": "test-client-id"}), \
                 patch.object(updater, "OUT", target), \
                 patch.object(updater, "get_json", return_value=response):
                updater.main()
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["items"][0]["title"], "Sample Movie")
            self.assertEqual(len(data["items"]), 1)

    def test_empty_history_runs_safe_public_checks_without_overwriting(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trakt-history.json"
            target.write_text("keep", encoding="utf-8")
            def reply(url, headers):
                if "/history" in url:
                    return []
                if "/watched/movies" in url:
                    return [{"movie": {"title": "never-print-this-title"}}]
                if "/watched/shows" in url:
                    return []
                if "/stats" in url:
                    return {"movies": {"plays": 17}, "episodes": {"plays": 5},
                            "shows": {"watched": 2}}
                raise AssertionError("Unexpected endpoint")
            output = StringIO()
            with patch.dict(os.environ, {"TRAKT_CLIENT_ID": "private-test-client-id"}), \
                 patch.object(updater, "OUT", target), \
                 patch.object(updater, "get_json", side_effect=reply), \
                 redirect_stdout(output):
                with self.assertRaises(SystemExit) as exc:
                    updater.main()
            report = output.getvalue()
            self.assertIn("Public watched movies: visible", report)
            self.assertIn("Public watched shows: empty", report)
            self.assertIn("movies plays = 17", report)
            self.assertIn("No usable public history", str(exc.exception))
            self.assertNotIn("never-print-this-title", report)
            self.assertNotIn("private-test-client-id", report)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_unrecognised_history_row_shape_is_reported(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trakt-history.json"
            target.write_text("keep", encoding="utf-8")
            calls = []
            def reply(url, headers):
                calls.append(url)
                if "/history" in url:
                    return [{"type": "something-new", "title": "private-watch-title"}]
                return []
            output = StringIO()
            with patch.dict(os.environ, {"TRAKT_CLIENT_ID": "private-test-client-id"}), \
                 patch.object(updater, "OUT", target), \
                 patch.object(updater, "get_json", side_effect=reply), \
                 redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    updater.main()
            self.assertIn("other= 1", output.getvalue())
            self.assertIn("usable items: 0", output.getvalue())
            self.assertNotIn("private-watch-title", output.getvalue())
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")
            self.assertEqual(len(calls), 4)

    def test_public_probe_http_error_is_sanitised(self):
        from contextlib import redirect_stdout
        from io import StringIO
        def reply(url, headers):
            raise HTTPError(url, 403, "Forbidden", {}, None)
        output = StringIO()
        with patch.object(updater, "get_json", side_effect=reply), redirect_stdout(output):
            updater.diagnose_public_watch_visibility({"trakt-api-key": "secret"})
        report = output.getvalue()
        self.assertIn("Public watched movies: HTTP 403", report)
        self.assertIn("Public watch statistics: HTTP 403", report)
        self.assertNotIn("secret", report)

    def test_no_results_do_not_erase_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trakt-history.json"
            target.write_text("keep", encoding="utf-8")
            with patch.dict(os.environ, {"TRAKT_CLIENT_ID": "test-client-id"}), \
                 patch.object(updater, "OUT", target), \
                 patch.object(updater, "get_json", return_value=[]):
                with self.assertRaises(SystemExit):
                    updater.main()
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
