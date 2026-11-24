"""Offline regression tests for narrowly scoped health-check classifications."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import site_health

PROFILE = "https://codeberg.org/schmookey"


class SiteHealthTests(unittest.TestCase):
    def check_error(self, url, status, internal=False, final_url=None):
        error = HTTPError(final_url or url, status, "test", {}, None)
        with patch.object(site_health, "public_url"), patch.object(site_health, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            return site_health.check(url, internal)

    def test_confirmed_profile_404_remains_visible_for_review(self):
        result = self.check_error(PROFILE, 404)
        self.assertEqual(result[:2], ("REVIEW", PROFILE))
        self.assertIn("HTTP 404", result[2])
        self.assertIn("verify in browser", result[2])

    def test_other_missing_links_still_fail(self):
        for url in ("https://codeberg.org/schmookey/missing",
                    "https://codeberg.org/another-profile",
                    "https://example.org/missing"):
            with self.subTest(url=url):
                self.assertEqual(self.check_error(url, 404)[0], "FAIL")

    def test_gone_and_internal_errors_still_fail(self):
        self.assertEqual(self.check_error(PROFILE, 410)[0], "FAIL")
        self.assertEqual(self.check_error(PROFILE, 404, internal=True)[0], "FAIL")
        self.assertEqual(self.check_error("https://schmookey.xyz/missing.html", 404, internal=True)[0], "FAIL")

    def test_redirect_to_missing_page_not_exempt(self):
        self.assertEqual(self.check_error(PROFILE, 404, final_url=PROFILE + "/missing")[0], "FAIL")

    def test_external_403_still_requires_review(self):
        self.assertEqual(self.check_error("https://libro.fm", 403)[0], "REVIEW")


if __name__ == "__main__":
    unittest.main()
