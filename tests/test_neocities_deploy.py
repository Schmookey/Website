"""Offline safety checks for the manual Neocities deployment helper."""
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/neocities_manual_deploy.py"
spec = importlib.util.spec_from_file_location("neocities_manual_deploy", SCRIPT)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class ManualDeploymentTests(unittest.TestCase):
    def test_only_explicit_files_are_eligible(self):
        self.assertEqual(
            deploy.PUBLISH_FILES,
            ("assets/js/main.js", "assets/css/style.css", "privacy.html"),
        )
        self.assertNotIn("assets/data/site-updates.json", deploy.PUBLISH_FILES)

    def test_trakt_groups_never_include_manual_pages(self):
        self.assertEqual(
            deploy.DEPLOYMENT_GROUPS["trakt-snapshot"],
            ("assets/data/trakt-history.json",),
        )
        self.assertEqual(
            deploy.DEPLOYMENT_GROUPS["trakt-widget"],
            ("assets/data/trakt-history.json", "assets/js/trakt-history.js"),
        )
        for group in ("trakt-snapshot", "trakt-widget"):
            for protected in (
                "assets/data/site-updates.json", "about.html",
                "now-watching.html", "assets/css/style.css",
                "assets/js/main.js",
            ):
                self.assertNotIn(protected, deploy.DEPLOYMENT_GROUPS[group])

    def test_trakt_preview_is_read_only_and_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative in deploy.DEPLOYMENT_GROUPS["trakt-widget"]:
                file = root / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("trakt-only", encoding="utf-8")
            listing = []
            def api(path, _key, **kwargs):
                self.assertNotEqual(path, "/upload")
                if path == "/info":
                    return {"result": "success",
                            "info": {"sitename": "schmookey", "domain": "schmookey.xyz"}}
                return {"result": "success", "files": listing}
            with patch.object(deploy, "ROOT", root), \\
                 patch.dict(os.environ, {"NEOCITIES_API_KEY": "test-secret"}), \\
                 patch.object(deploy, "request", side_effect=api) as calls:
                deploy.run(deploy=False, group="trakt-widget")
            self.assertEqual(calls.call_count, 2)

    def test_trakt_upload_uses_only_scoped_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative in deploy.DEPLOYMENT_GROUPS["trakt-snapshot"]:
                file = root / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("trakt-json-only", encoding="utf-8")
            uploads = []
            def api(path, _key, **kwargs):
                if path == "/info":
                    return {"result": "success",
                            "info": {"sitename": "schmookey", "domain": "schmookey.xyz"}}
                if path == "/list":
                    return {"result": "success", "files": []}
                self.assertEqual(path, "/upload")
                uploads.append(kwargs["data"])
                return {"result": "success"}
            with patch.object(deploy, "ROOT", root), \\
                 patch.dict(os.environ, {"NEOCITIES_API_KEY": "test-secret"}), \\
                 patch.object(deploy, "request", side_effect=api):
                deploy.run(deploy=True, group="trakt-snapshot")
            self.assertEqual(len(uploads), 1)
            self.assertIn(b'name="assets/data/trakt-history.json"', uploads[0])
            self.assertNotIn(b"site-updates.json", uploads[0])
            self.assertNotIn(b'filename="about.html"', uploads[0])
            self.assertNotIn(b"trakt-history.js", uploads[0])

    def test_unknown_deploy_group_is_rejected_before_api_access(self):
        with self.assertRaisesRegex(RuntimeError, "Unknown deployment group"):
            deploy.run(deploy=True, group="../../about.html")

    def test_wrong_site_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "expected custom domain"):
            deploy.verify_destination(
                {"info": {"sitename": "other", "domain": "other.example"}}
            )
        with self.assertRaisesRegex(RuntimeError, "expected custom domain"):
            deploy.verify_destination(
                {"info": {"sitename": "other", "domain": None}}
            )

    def test_preview_never_calls_upload(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative in deploy.PUBLISH_FILES:
                file = root / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("repo-content", encoding="utf-8")
            listing = [{"path": path, "sha1_hash": "not-current", "is_directory": False}
                       for path in deploy.PUBLISH_FILES]
            def api(path, _key, **kwargs):
                self.assertNotEqual(path, "/upload", "Preview must never upload")
                return {"result": "success",
                        "info": {"sitename": "schmookey", "domain": "schmookey.xyz"}
                        } if path == "/info" else {"result": "success", "files": listing}
            with patch.object(deploy, "ROOT", root), \
                 patch.dict(os.environ, {"NEOCITIES_API_KEY": "test-secret"}), \
                 patch.object(deploy, "request", side_effect=api) as mock_request:
                deploy.run(deploy=False)
            self.assertEqual(mock_request.call_count, 2)

    def test_upload_payload_cannot_include_unlisted_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rel = deploy.PUBLISH_FILES[0]
            file = root / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b"hello")
            with patch.object(deploy, "ROOT", root):
                body, content_type = deploy.build_upload_payload([rel])
            self.assertIn(b'name="assets/js/main.js"', body)
            self.assertIn(b"hello", body)
            self.assertNotIn(b"site-updates.json", body)
            self.assertTrue(content_type.startswith("multipart/form-data;"))

    def test_request_errors_do_not_echo_api_token(self):
        with patch.dict(os.environ, {"NEOCITIES_API_KEY": "private-test-token"}), \
             patch.object(deploy, "request", side_effect=RuntimeError("API failed")):
            with self.assertRaises(RuntimeError) as raised:
                deploy.run(deploy=False)
        self.assertNotIn("private-test-token", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
