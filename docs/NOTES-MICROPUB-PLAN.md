# Notes publishing using GitHub Actions

The Notes section at `/notes/` is independent of Blog, Music and Now. The
site is static and requires **no Indiekit, always-on server or Micropub service**.

## How to publish

After the reviewed changes are merged to `main`:

1. Visit **Actions → Publish an IndieWeb Note** in the Website repository.
2. Select **Run workflow** on the **main** branch.
3. Enter your note (plain text, maximum 2,000 characters). Optional tags are
   comma-separated, such as `indieweb, linux`.
   Optionally, upload your photograph or GIF to the repository's `assets/images/`
   folder first, then supply its existing public path (for example
   `/assets/images/photo.webp`) and a meaningful image description.
   Accepted image types are JPEG, PNG, GIF, WebP and AVIF. The publisher will
   not download images from external websites.
4. Select **Run workflow** and check that the workflow finishes successfully.
5. Review the commit and the generated note in `/notes/`.

Publishing updates only the Notes source, Notes pages and feeds, and the shared
sitemap. The main Blog/Music content generator continues to operate separately.
Each note has an immutable URL in the form `/notes/YYYY-MM-DD-HHMMSS-RUNID.html`.

The workflow runs checks before committing and requests a second validation
run after committing (because GitHub's own workflow-token commits do not
automatically trigger ordinary push workflows). A failed push or validation
does not upload anything to Neocities.

## What gets generated

- `assets/data/notes.json` — source of authored notes
- `notes/index.html` — newest-first Notes page with an `h-feed`
- `notes/<id>.html` — canonical individual note with `h-entry`,
  `e-content`, `dt-published`, `u-url`, optional `u-photo` and author metadata
- `notes/feed.xml` and `notes/atom.xml` — Notes-only RSS and Atom
- `sitemap.xml` — published note permalinks

The publishing workflow escapes HTML content to prevent injected markup or
scripts, rejects malformed records and tags, and avoids duplicate publications
on retrying the same workflow run. An attached image must already exist in
`assets/images/`; only local image paths are allowed, and alternative text
is mandatory. The photo is marked `u-photo` inside the note's `e-content`.

## Local checks

```sh
python3 scripts/build_notes.py
python3 scripts/build_content.py
python3 scripts/build_notes.py --check
python3 scripts/build_content.py --check
python3 -m unittest discover -s tests -p 'test_notes_publishing.py' -v
```

## Deployment and social posting

**GitHub publication is not automatically a live Neocities deployment.** The
existing deployment workflow is explicitly review-gated by the
`NEOCITIES_AUTO_DEPLOY_ENABLED` repository variable; its safety controls are
preserved. The Neocities staging step includes the Notes HTML and RSS/Atom
files. Confirm the public note is accessible after deployment.

**Mastodon and Bluesky cross-posting are not implemented or enabled.**
Those integrations should be added only after public deployment can be
verified and a durable record prevents accidental duplicate posts. There is
no need to supply social credentials to the Notes publishing workflow.

Webmention.io remains the existing independent Webmention receiver. Notes
carry their own canonical URLs; displaying received replies on individual
Notes can be developed independently.
