"""Protect the Mega Drive article layout and offline search from regressions."""
from pathlib import Path
import unittest

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = sorted((ROOT / "blog/posts").glob("*.html")) + sorted((ROOT / "music/posts").glob("*.html"))
PUBLISHED = [p for p in PUBLISHED if p.name != "blog-template.html"]


class MegaDriveSearchTests(unittest.TestCase):
    def test_published_articles_keep_banner_socials_and_indieweb_markup(self):
        for page in PUBLISHED:
            with self.subTest(page=page.name):
                doc = html.parse(str(page))
                self.assertEqual(len(doc.xpath('//header[contains(@class,"header")]//img[contains(@src,"header-banner.webp")]')), 1)
                self.assertEqual(len(doc.xpath('//nav[contains(@class,"menu")]')), 1)
                self.assertEqual(len(doc.xpath('//main/article[contains(@class,"h-entry") and contains(@class,"post-container")]')), 1)
                self.assertEqual(len(doc.xpath('//aside[contains(@class,"sidebar") and contains(@class,"left")]//div[contains(@class,"badge-grid")]')), 1)
                badges = doc.xpath('//aside[contains(@class,"sidebar") and contains(@class,"left")]//div[contains(@class,"badge-grid")]/a')
                self.assertGreaterEqual(len(badges), 5)
                self.assertTrue(all(a.get("href") for a in badges))
                self.assertTrue(doc.xpath('//script[contains(@src,"main.js")]'))

    def test_only_articles_load_two_column_layout(self):
        js = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        article_js = (ROOT / "assets/js/article-sidebar.js").read_text(encoding="utf-8")
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        # The article layout and script must exist in HTML even if JS fails.
        for page in PUBLISHED + [ROOT / "blog/posts/blog-template.html"]:
            with self.subTest(page=page.name):
                doc = html.parse(str(page))
                self.assertEqual(len(doc.xpath(
                    '//div[contains(concat(" ",normalize-space(@class)," ")," article-layout ")]'
                )), 1)
                self.assertEqual(doc.xpath(
                    '//script[contains(@src,"/assets/js/article-sidebar.js")]/@src'
                ), ["/assets/js/article-sidebar.js"])
        self.assertNotIn('function loadArticleSidebar()', js)
        self.assertIn('layout.classList.add("article-layout")', article_js)
        self.assertIn('.layout.article-layout > .sidebar.right{', css)
        self.assertIn('display:none;', css)
        self.assertIn('.layout.article-layout{', css)
        self.assertIn('grid-template-columns:minmax(210px,240px) minmax(0,1fr)', css)
        for colour in ("#0b0f1f", "#c1121f", "#1e40ff", "#fff"):
            self.assertIn(colour, css)
        self.assertIn('social.append(badges)', article_js)
        self.assertIn('width:88px;', css)
        self.assertIn('height:31px;', css)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))', css)
        self.assertIn('@media(max-width:768px)', css)

    def test_four_sidebar_boxes_are_siblings_and_include_static_links(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "article_builder", ROOT / "scripts/build_content.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        records, _ = builder.content_items(ROOT)
        generated = builder.build_article_sidebars(ROOT, records)

        for article in PUBLISHED:
            with self.subTest(article=article.name):
                doc = html.fromstring(generated[article.relative_to(ROOT).as_posix()])
                sections = doc.xpath(
                    '//aside[contains(concat(" ",normalize-space(@class)," ")," article-sidebar ")]'
                    '/section'
                )
                self.assertEqual(
                    [section.get("class").split()[0] if "site-search-widget" in section.get("class")
                     else next(name for name in section.get("class").split()
                               if name in {"article-related-posts", "article-more-posts", "article-social-badges"})
                     for section in sections],
                    ["site-search-widget", "article-related-posts",
                     "article-more-posts", "article-social-badges"]
                )
                self.assertEqual(len(sections), 4)
                self.assertTrue(sections[0].xpath('.//input[@type="search"]'))
                self.assertTrue(sections[1].xpath('.//li/a[contains(@href,"/posts/")]'))
                self.assertTrue(sections[2].xpath('.//li/a[contains(@href,"/blog/posts/")]'))
                self.assertGreaterEqual(len(sections[3].xpath('.//div[contains(@class,"badge-grid")]/a')), 5)
                self.assertEqual(len(sections[0].xpath('.//section')), 0)
                self.assertNotIn("Loading posts", html.tostring(sections[1], encoding="unicode"))
                self.assertEqual(generated[article.relative_to(ROOT).as_posix()],
                                 article.read_text(encoding="utf-8-sig"))

        css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("FOUR INDEPENDENT MEGA DRIVE ARTICLE SIDEBAR PANELS", css)
        self.assertIn("background:transparent;", css)
        search_js = (ROOT / "assets/js/site-search.js").read_text(encoding="utf-8")
        self.assertIn('const existing = sidebar.querySelector(".site-search-widget")', search_js)
        self.assertIn('widget.dataset.searchReady = "true"', search_js)

    def test_related_posts_can_cross_blog_and_music_tags(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "article_builder_related", ROOT / "scripts/build_content.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        posts = builder.load(ROOT, "assets/data/posts.json")
        blog = next(p for p in posts if p["url"].endswith("this-week-23-29-march.html"))
        related, more = builder.article_recommendations(blog, posts)
        self.assertTrue(any(p["section"] == "music" for p, _ in related))
        self.assertTrue(all(p["section"] == "blog" for p in more))
        self.assertTrue(all(p["url"] != blog["url"] for p, _ in related))
        self.assertFalse({p["url"] for p, _ in related} & {p["url"] for p in more})

    def test_search_is_local_and_has_accessible_results(self):
        doc = html.parse(str(ROOT / "search.html"))
        self.assertTrue(doc.xpath('//*[@id="site-search-page-query"]'))
        self.assertTrue(doc.xpath('//*[@id="site-search-results"]'))
        self.assertTrue(doc.xpath('//meta[@name="robots" and @content="noindex,follow"]'))
        js = (ROOT / "assets/js/site-search.js").read_text(encoding="utf-8")
        self.assertIn('"/assets/data/search-index.json"', js)
        self.assertIn('aria-live="polite"', js)
        self.assertNotIn('google.com/search', js)
        self.assertNotIn('algolia', js)
        self.assertTrue((ROOT / "assets/data/search-index.json").exists())
        import importlib.util
        import json
        module_path = ROOT / "scripts/build_content.py"
        spec = importlib.util.spec_from_file_location("schmookey_builder", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        records, updates = module.content_items(ROOT)
        index = json.loads(module.build_search_index(ROOT, records, updates))
        self.assertTrue(index["items"])
        self.assertEqual({item["section"] for item in index["items"]}, {"blog", "music"})
        self.assertTrue(all(item["url"].startswith(("/blog/posts/", "/music/posts/"))
                            for item in index["items"]))
        self.assertFalse(any("/now.html" == item["url"] for item in index["items"]))
        self.assertEqual(len(index["items"]), len(records))
        self.assertIn('item.section === "music"', js)
        sidebar = (ROOT / "assets/js/article-sidebar.js").read_text(encoding="utf-8")
        # Search includes both sections, and related items may include music
        # when they share a meaningful tag (e.g. streaming or listenbrainz).
        self.assertIn('const candidates = posts.filter(item => item.url !== current.url)', sidebar)
        self.assertIn('ranked.filter(pair => pair.common.length > 0)', sidebar)
        self.assertIn('const blogPosts = candidates.filter(item => item.section === "blog")', sidebar)
        self.assertIn('const recent = blogPosts.filter(item => !seen.has(item.url))', sidebar)
        self.assertIn('const seen = new Set(similar.map(item => item.url))', sidebar)
        import json
        metadata = json.loads((ROOT / "assets/data/posts.json").read_text(encoding="utf-8"))
        blog = next(item for item in metadata if item["url"].endswith("this-week-23-29-march.html"))
        music = next(item for item in metadata if item["section"] == "music")
        self.assertTrue(set(blog["tags"]) & set(music["tags"]),
                        "Fixture should test a genuine cross-section tag match")
        self.assertNotIn('value="pages"', (ROOT / "search.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
