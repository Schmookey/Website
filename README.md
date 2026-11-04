# Schmookey's World

The source for [schmookey.xyz](https://schmookey.xyz), a small personal website about technology, music, television, books, and independent publishing. The site is **static**, with no PHP, server-side database, build process, or npm publishing requirement.

## Local preview

From the repository root, run:

```bash
python3 -m http.server 8000
```

Then visit [http://localhost:8000](http://localhost:8000). Do not open HTML files directly using `file://`: browser restrictions can prevent JSON requests from working. External services need an internet connection, but the site's navigation, layout and locally stored content work without them.

## Layout and data

- `index.html`, `about.html`, `now.html`, `listening.html`: main pages.
- `blog/`, `music/`, `random/`: sections and posts.
- `assets/css/style.css`: shared styling.
- `assets/js/main.js`: activity feed, Webmentions, ListenBrainz and other widgets.
- `assets/js/archive.js`: blog and music archive lists.
- `assets/data/`: local posts, recent reading/watching and updates.
- `feed.xml`, `atom.xml`, `feed.json`, `sitemap.xml`: feeds and discovery.

The site deliberately uses **hidden IndieWeb metadata** (`h-card`, `u-url`, `dt-published`, `u-syndication`, `rel="me"`) for identity, syndication and Webmentions. Preserve it when editing pages.

## Checks

Install the optional validation dependencies and run:

```bash
python3 -m pip install lxml tinycss2 Pillow
python3 tests/validate_site.py
node --check assets/js/main.js
node --check assets/js/archive.js
node tests/test_security.js
```

GitHub Actions runs equivalent checks on pull requests and pushes to `main`. There is intentionally no `package.json` or npm publication workflow.

## Third-party integrations

The site can load data from ListenBrainz, Webmention.io and social platforms, and contains third-party webring resources. External services may be unavailable or change independently of this repository. The web-ring scripts on `webrings.html` are third-party code running in the visitor's browser. Review them if the hosting providers change.

## Licensing and reuse

`LICENSE` contains the **MIT licence for website source code**. That does **not** mean all photographs, artwork, logos, text quotations or third-party resources in the site are MIT-licensed. The site also displays a Creative Commons badge. Refer to [docs/CONTENT-LICENSING.md](docs/CONTENT-LICENSING.md) before reusing content or redistributing media.

Please open an issue before proposing major design or integration changes. This repository mirrors the website's source; **it does not automatically deploy to the live site**.
