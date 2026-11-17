# Publishing an article or site update

GitHub's `main` branch is the source of truth. Commit the article or page and its metadata; GitHub Actions generates RSS, Atom, JSON Feed, the blog/music cards and the sitemap, checks the result, then publishes approved files to Neocities.

## New blog or music post

1. Add the public article file to `blog/posts/<slug>.html` or `music/posts/<slug>.html`.
2. Add an entry to `assets/data/posts.json`. Each entry needs the public `title`, root-relative `url`, timezone-aware `date`, matching `section` (`blog` or `music`), and normal archive fields `readingTime` and `tags`.
3. Optional `cardImage`, `cardImageAlt`, `cardBlurb`, and `cardTitle` override how the listing card looks. Existing post overrides are kept. Without overrides, the builder uses the first image in the article, the first full sentence in its post body, and the ordinary title.
4. Commit the changes to `main`. The automation maintains `blog/index.html` or `music/index.html`, `feed.json`, `feed.xml`, `atom.xml`, and `sitemap.xml`. Existing cards remain accessible and large portions are clickable.

## Now, privacy, and changelog changes

Update `now.html`, `privacy.html`, or `changelog.html` **and** add a new announcement to `assets/data/site-updates.json` with `type`, `title`, `url`, `date` (including timezone), and `summary`. Allowed URLs are `/now.html`, `/privacy.html`, and `/changelog.html`.

The new announcement goes into all three feeds and updates the page's `lastmod` date in the sitemap. Editing the page without an announcement will not create a new feed entry or invent a modification date.

## Workflow and validation

Run locally, from the repo root, after installing `lxml`:

```bash
python3 -m pip install lxml
python3 scripts/build_content.py
python3 scripts/build_content.py --check
```

On GitHub, `.github/workflows/content-sync.yml` runs on relevant `main` updates and commits generated content when needed. Existing site checks validate the generated output; the deployment workflow rebuilds it before staging. The normal `NEOCITIES_AUTO_DEPLOY_ENABLED` gate still applies. The Trakt history file remains excluded from generic uploads.

The sitemap contains public pages and published articles only (no templates, 404 page, drafts, tests or source files). Article `lastmod` is the post publication date unless you set an optional timezone-aware `updated` field in `posts.json`. Site-update pages take their latest announcement date. Pages without reliable modification metadata omit `lastmod` rather than claiming an artificial update.
