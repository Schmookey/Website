"""Privacy Policy uses the Now-page design without splitting the document."""
from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = [
    "[OVERVIEW]", "[DATA_COLLECTION]", "[LOCAL_STORAGE]",
    "[LISTENBRAINZ]", "[TRAKT]", "[THIRD_PARTY_MEDIA]",
    "[PUBLIC_ACTIVITY]", "[EXTERNAL_LINKS]", "[CHANGES]", "[CONTACT]",
]
PRIVACY_LINKS = {"https://metabrainz.org/privacy", "https://trakt.tv/privacy"}


class PrivacySingleDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = html.parse(str(ROOT / "privacy.html"))

    def test_now_style_header_and_unbroken_policy_article(self):
        mains = self.page.xpath('//main[contains(concat(" ",normalize-space(@class)," ")," privacy-main ")]')
        self.assertEqual(len(mains), 1)
        main = mains[0]
        self.assertIn("panel", main.get("class").split())
        header = main.xpath('./header[@class="privacy-16bit-header"]')
        self.assertEqual(len(header), 1)
        self.assertEqual(header[0].xpath("./h1/text()"), ["PRIVACY POLICY"])
        self.assertEqual(header[0].xpath("./p[@class='privacy-16bit-overline']/text()"),
                         ["SYSTEM FILE — PRIVACY POLICY"])
        self.assertEqual(header[0].xpath("./p[@class='privacy-16bit-updated']/strong/text()"),
                         ["Last updated:"])
        self.assertIn("11 November 2026", "".join(header[0].itertext()))
        articles = main.xpath('./article[@class="privacy-document"]')
        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article.xpath("./h2/text()"), HEADINGS)
        self.assertFalse(article.xpath("./section | .//*[contains(concat(' ', normalize-space(@class), ' '), ' panel ')]"))
        self.assertFalse(main.xpath("./div[@class='panel terminal']"))
        self.assertEqual(len(main.xpath("./article")), 1)
        self.assertEqual(article.xpath("./ul/li/text()"), ["IP address", "Browser type", "Date and time of visits"])
        self.assertEqual(article.xpath(".//a/@href"), ["https://metabrainz.org/privacy", "https://trakt.tv/privacy"])
        self.assertIn("INITIALISING DATA FILE...", "".join(article.itertext()))
        self.assertIn("END OF FILE", "".join(article.itertext()))
        # Keep the existing explanatory policy content rather than swapping in placeholder prose.
        for phrase in [
            "This is a small personal website created for fun.",
            "This website does not intentionally collect personal information directly from visitors.",
            "Some pages use your browser's local storage",
            "My website retrieves this information from my public ListenBrainz profile.",
            "The integration is designed to periodically retrieve my viewing activity",
            "You can browse the website without connecting your music or television accounts.",
            "Questions? Use the contact links available on the website.",
        ]:
            self.assertIn(phrase, " ".join(article.itertext()))

    def test_style_is_privacy_only_and_no_section_cards(self):
        self.assertEqual(self.page.xpath("//link[@rel='stylesheet'][@href='/assets/css/privacy-16bit.css']/@href"),
                         ["/assets/css/privacy-16bit.css"])
        style = (ROOT / "assets/css/privacy-16bit.css").read_text(encoding="utf-8")
        self.assertIn("background: #101832;", style)
        self.assertIn("border: 3px solid #1e40ff;", style)
        self.assertIn("repeating-linear-gradient", style)
        self.assertIn("border: 0;", style)
        self.assertIn("box-shadow: none;", style)
        self.assertNotIn(".privacy-card", style)
        # Every CSS selector belongs to the Privacy main panel, not shared layout/sidebar components.
        import re
        selectors = re.findall(r"(?:^|\n)([^{}]+)\{", re.sub(r"/\*.*?\*/", "", style, flags=re.S))
        scope = "body .layout.site-panel-layout > main.center.panel.privacy-main"
        for selector in selectors:
            selector = selector.strip()
            if selector.startswith("@media"):
                continue
            for part in selector.split(","):
                self.assertTrue(part.strip().startswith(scope), repr(part))

    def test_site_shell_kept_unchanged(self):
        self.assertEqual(len(self.page.xpath("//aside[contains(@class, 'site-panel-sidebar')]")), 1)
        self.assertEqual(len(self.page.xpath("//nav[@class='menu']")), 1)
        self.assertEqual(len(self.page.xpath("//header[@class='header']")), 1)
        self.assertEqual(len(self.page.xpath("//footer[@class='footer']")), 1)
        self.assertEqual(self.page.xpath("//script[@src='/assets/js/main.js']/@src"),
                         ["/assets/js/main.js"])


if __name__ == "__main__":
    unittest.main()
