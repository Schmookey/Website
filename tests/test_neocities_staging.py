"""Offline tests for the Marketplace action's safe staging folder."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/stage_neocities_site.py"
spec = importlib.util.spec_from_file_location("neocities_stager", SCRIPT)
stager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stager)


class NeocitiesStagingTests(unittest.TestCase):
    def test_notes_publish_dispatches_existing_gated_deployment(self):
        root = SCRIPT.parents[1]
        publish = (root / ".github/workflows/publish-note.yml").read_text(encoding="utf-8")
        deployment = (root / ".github/workflows/neocities-auto-deploy.yml").read_text(encoding="utf-8")
        self.assertIn('neocities-auto-deploy.yml/dispatches', publish)
        self.assertIn("inputs[preview_only]=false", publish)
        self.assertIn("NEOCITIES_AUTO_DEPLOY_ENABLED", deployment)
        self.assertIn("scripts/stage_neocities_site.py --output public", deployment)
        self.assertIn("Verify configured destination", deployment)
        self.assertIn("Recheck that the validated revision remains main", deployment)

    def test_protected_and_private_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "public"
            files = stager.stage(destination)
            self.assertIn("index.html", files)
            self.assertIn("assets/css/style.css", files)
            self.assertIn("assets/xsl/rss.xsl", files)
            self.assertIn("assets/xsl/sitemap.xsl", files)
            self.assertNotIn("assets/data/trakt-history.json", files)
            self.assertIn("assets/data/site-updates.json", files)
            self.assertIn("notes/index.html", files)
            self.assertIn("notes/feed.xml", files)
            self.assertIn("notes/atom.xml", files)
            self.assertFalse((destination / "assets/data/trakt-history.json").exists())
            self.assertFalse((destination / ".github").exists())
            self.assertFalse((destination / "scripts").exists())
            self.assertFalse((destination / "tests").exists())


if __name__ == "__main__":
    unittest.main()
