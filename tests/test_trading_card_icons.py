"""Trading-card artwork, responsive pixel styling and accessible stats."""
from pathlib import Path
import unittest
from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
ICONS = ("coffee", "energy", "sleep", "game-controller", "book", "waypoint", "cassette")

class TradingCardIconsTests(unittest.TestCase):
    def test_local_art_and_replaced_elements(self):
        doc = html.parse(str(ROOT / "about.html"))
        card, = doc.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," profile-card ")]')
        for icon in ICONS:
            src = "/assets/images/" + icon + ".svg"
            asset = etree.parse(str(ROOT / src.lstrip("/"))).getroot()
            self.assertEqual(asset.get("viewBox"), "0 0 24 24")
            self.assertEqual(asset.get("shape-rendering"), "crispEdges")
            images = card.xpath('.//img[@src=$src]', src=src)
            self.assertEqual(len(images), 2 if icon == "cassette" else 1)
            self.assertTrue(all(img.get("alt") == "" for img in images))
        for emoji in ("☕", "⚡", "🌙", "🎮", "📖", "📍"):
            self.assertNotIn(emoji, card.text_content())
        self.assertEqual(card.xpath('.//h1[@class="p-name"]/text()'), ["Schmookey"])
        portrait, = card.xpath('.//div[@class="profile-card-portrait"]/img[@class="u-photo"]')
        self.assertEqual(portrait.get("src"), "/assets/images/allen_16bit_portrait.png")
        self.assertEqual((portrait.get("width"), portrait.get("height")), ("624", "624"))
        self.assertTrue((ROOT / portrait.get("src").lstrip("/")).is_file())
        for service in ("fediverse", "mastodon", "bluesky"):
            src = "/assets/images/" + service + "-16bit.svg"
            asset = etree.parse(str(ROOT / src.lstrip("/"))).getroot()
            self.assertEqual(asset.get("viewBox"), "0 0 32 32")
            self.assertEqual(asset.get("shape-rendering"), "crispEdges")
            logo, = card.xpath('.//a/img[@class="profile-card-logo" and @src=$src]', src=src)
            self.assertEqual(logo.get("alt"), "")
            self.assertEqual((logo.get("width"), logo.get("height")), ("32", "32"))
            self.assertIn(service, logo.getparent().text_content().lower())
            self.assertEqual(logo.getparent().get("rel"), "me")
        nav, = card.xpath('.//nav[@class="profile-card-socials"]')
        links = nav.xpath('./a')
        self.assertEqual([link.text_content().strip() for link in links],
                         ["Fediverse", "GitHub", "Mastodon", "Bluesky"])
        self.assertEqual([link.get("href") for link in links], [
            "https://fed.brid.gy/ap/@schmookey@mastodon.social",
            "https://github.com/Schmookey",
            "https://mastodon.social/@schmookey",
            "https://bsky.app/profile/schmookey.xyz",
        ])
        self.assertIn("u-url", links[0].get("class").split())
        for link in links:
            self.assertIn("profile-card-link", link.get("class").split())
            self.assertEqual(link.get("rel"), "me")
            logo, = link.xpath('./img[@class="profile-card-logo"]')
            self.assertEqual((logo.get("width"), logo.get("height")), ("32", "32"))
            self.assertEqual(logo.get("alt"), "")
        github_logo, = links[1].xpath('./img')
        self.assertEqual(github_logo.get("src"), "/assets/images/github.svg")
        github_asset = etree.parse(str(ROOT / "assets/images/github.svg")).getroot()
        self.assertEqual(github_asset.get("viewBox"), "0 0 32 32")
        self.assertEqual(github_asset.get("shape-rendering"), "crispEdges")
        for name, value in (("coffee", 85), ("energy", 70), ("sleep", 30)):
            bar, = card.xpath('.//*[@role="progressbar" and @aria-labelledby=$label]', label="card-" + name)
            self.assertEqual(bar.get("aria-valuenow"), str(value))
            self.assertEqual(bar.xpath('./span/@style'), ["width:" + str(value) + "%"])

    def test_pixel_styling_is_scoped_to_card(self):
        css = (ROOT / "assets/css/about-profile-card.css").read_text()
        self.assertIn('font-family: "Press Start 2P", monospace;', css)
        self.assertIn('.about-page .profile-card-bar::after', css)
        self.assertIn('repeating-linear-gradient(to right', css)
        self.assertNotIn('.profile-cassette::before', css)
        self.assertNotIn('.profile-cassette::after', css)
        self.assertNotIn('data-schmookey-theme', css)
        self.assertIn('.about-page .profile-card-portrait::after', css)
        self.assertIn('border: 5px solid #ffcf51;', css)
        self.assertIn('object-fit: cover;', css)
        self.assertIn('pointer-events: none;', css)

if __name__ == "__main__":
    unittest.main()
