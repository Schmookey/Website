"""Offline regression tests for the simple GitHub-powered Notes publisher."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from lxml import html, etree as LET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_notes", ROOT / "scripts/build_notes.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class NotesPublishingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Each fixture must start empty, even when the live repository contains
        # newly generated notes from the workflow under test.
        template = self.root / "notes/index.html"
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text(
            builder.render_index(
                (ROOT / "notes/index.html").read_text(encoding="utf-8"), []
            ),
            encoding="utf-8",
        )
        source = self.root / "assets/data/notes.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("[]\n", encoding="utf-8")

    def test_current_repository_notes_are_valid(self):
        self.assertIsInstance(builder.read_notes(ROOT), list)

    def test_empty_notes_preserve_existing_page_and_feed_data(self):
        outputs = builder.outputs(self.root)
        self.assertEqual(outputs[Path("notes/index.html")],
                         (self.root / "notes/index.html").read_text(encoding="utf-8"))
        rss = ET.fromstring(outputs[Path("notes/feed.xml")])
        self.assertEqual(rss.findall("./channel/item"), [])
        atom = ET.fromstring(outputs[Path("notes/atom.xml")])
        self.assertEqual(atom.findall("{http://www.w3.org/2005/Atom}entry"), [])

    def test_publish_generates_safe_individual_html_feed_and_xml(self):
        text = 'A <script>alert("x")</script> & a short note.\n\nSecond paragraph.'
        url = builder.add_note(self.root, text, "indieweb, linux", "12345")
        self.assertTrue(url.startswith("/notes/2026-") or url.startswith("/notes/20"))
        outputs = builder.outputs(self.root)
        doc = html.fromstring(outputs[Path(url.lstrip("/"))])
        self.assertEqual(doc.xpath('//link[@rel="canonical"]/@href'),
                         [builder.BASE + url])
        entry = doc.xpath('//main//article[contains(@class,"h-entry")]')
        self.assertEqual(len(entry), 1)
        self.assertEqual(len(entry[0].xpath('.//script')), 0)
        self.assertIn('<script>alert("x")</script>', entry[0].text_content())
        self.assertEqual(len(entry[0].xpath('.//time[contains(@class,"dt-published")]')), 1)
        self.assertEqual(entry[0].xpath('.//a[contains(@class,"u-url")]/@href'), [url])
        self.assertEqual(entry[0].xpath('.//a[contains(@class,"p-author")]/@href'),
                         ["/about.html"])
        index = html.fromstring(outputs[Path("notes/index.html")])
        self.assertEqual(len(index.xpath('//main//article[contains(@class,"h-entry")]')), 1)
        rss = ET.fromstring(outputs[Path("notes/feed.xml")])
        self.assertEqual(rss.findtext("./channel/item/description"), text)
        atom = ET.fromstring(outputs[Path("notes/atom.xml")])
        ns = "{http://www.w3.org/2005/Atom}"
        self.assertEqual(atom.findtext(f"{ns}entry/{ns}content"), text)
        builder.generate(self.root)
        builder.generate(self.root, check=True)

    def test_notes_rss_renders_using_same_retro_stylesheet_as_main_feed(self):
        instruction = '<?xml-stylesheet type="text/xsl" href="/assets/xsl/rss.xsl"?>'
        self.assertIn(instruction, (ROOT / "notes/feed.xml").read_text(encoding="utf-8"))
        self.assertIn(instruction, builder.rss_feed([]))
        self.assertIn(instruction, builder.rss_feed(builder.read_notes(ROOT)))
        stylesheet = LET.XSLT(LET.parse(str(ROOT / "assets/xsl/rss.xsl")))
        notes_xml = LET.parse(str(ROOT / "notes/feed.xml"))
        result = html.fromstring(str(stylesheet(notes_xml)))
        self.assertEqual(result.xpath('string(//title)'), "NOTES RSS | SCHMOOKEY")
        self.assertEqual(result.xpath('string(//span[@class="brand"])'), "Schmookey.xyz")
        self.assertEqual(result.xpath('string(//h1)'), "Notes RSS Feed")
        self.assertEqual(result.xpath('//a[@class="site-link"]/@href'), ["https://schmookey.xyz/notes/"])
        self.assertIn("https://schmookey.xyz/notes/feed.xml", result.text_content())
        self.assertEqual(
            result.xpath('//div[@class="entry"]//h2/a/@href'),
            notes_xml.xpath('/rss/channel/item/link/text()'),
        )
        main_xml = LET.parse(str(ROOT / "feed.xml"))
        main = html.fromstring(str(stylesheet(main_xml)))
        self.assertEqual(main.xpath('string(//title)'), "RSS | SCHMOOKEY")
        self.assertEqual(main.xpath('string(//h1)'), "RSS Feed")
        self.assertEqual(main.xpath('//a[@class="site-link"]/@href'), ["https://schmookey.xyz/"])

    def test_republishing_same_workflow_run_is_idempotent(self):
        first = builder.add_note(self.root, "Short original note", "linux", "888")
        second = builder.add_note(self.root, "Short original note", "linux", "888")
        self.assertEqual(first, second)
        self.assertEqual(len(builder.read_notes(self.root)), 1)
        with self.assertRaises(ValueError):
            builder.add_note(self.root, "Changed note", "linux", "888")

    def test_images_use_u_photo_and_accessible_alt_text(self):
        images = self.root / "assets/images"
        images.mkdir(parents=True)
        (images / "example.webp").write_bytes(b"test image fixture")
        url = builder.add_note(
            self.root, "A note with a photograph.", "indieweb", "999",
            "/assets/images/example.webp", 'A photo of a screen & desk.'
        )
        results = builder.outputs(self.root)
        for page in (Path(url.lstrip("/")), Path("notes/index.html")):
            doc = html.fromstring(results[page])
            pictures = doc.xpath('//article[contains(@class,"h-entry")]//img[contains(@class,"u-photo")]')
            self.assertEqual(len(pictures), 1)
            self.assertEqual(pictures[0].get("src"), "/assets/images/example.webp")
            self.assertEqual(pictures[0].get("alt"), "A photo of a screen & desk.")
            self.assertEqual(pictures[0].get("loading"), "lazy")

    def test_invalid_image_paths_and_missing_alt_are_rejected(self):
        images = self.root / "assets/images"
        images.mkdir(parents=True)
        (images / "good.png").write_bytes(b"fixture")
        for picture, alt in (
            ("/assets/images/missing.png", "Description"),
            ("https://example.com/photo.png", "Description"),
            ("/assets/images/../../secret.png", "Description"),
            ("/assets/images/good.png", ""),
            ("/assets/images/good.png", "x" * 301),
            ("", "Description without an image"),
        ):
            with self.subTest(image=picture, alt=alt), self.assertRaises(ValueError):
                builder.add_note(self.root, "Text", "", "777", picture, alt)

    def test_invalid_content_and_tags_are_rejected(self):
        for text in ("", "   ", "x" * 2001):
            with self.subTest(text=text[:20]), self.assertRaises(ValueError):
                builder.add_note(self.root, text, "", "555")
        for tags in ("<script>", "wrong_underscore", "x" * 50):
            with self.subTest(tags=tags), self.assertRaises(ValueError):
                builder.add_note(self.root, "Example", tags, "555")

    def test_broken_generated_notes_source_is_rejected(self):
        data = [{
            "id": "../bad",
            "date": "2026-11-17T12:00:00Z",
            "content": "Example",
        }]
        (self.root / "assets/data/notes.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            builder.read_notes(self.root)


if __name__ == "__main__":
    unittest.main()
