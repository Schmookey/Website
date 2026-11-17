# Notes: static publishing foundation and future Micropub integration

The `/notes/` section is **independent** of Blog, Music, Random and Now. Its
navigation link sits between Random and Now. The public page has a Microformats2
`h-feed`, its own RSS and Atom discovery, and the site's existing Webmention
receiver. It contains no fabricated notes.

## Current stage

- `notes/index.html` is a public static page with a clear empty state.
- `assets/data/notes.json` is an empty future source collection. It is **not**
  automatically turned into published notes yet.
- `notes/feed.xml` and `notes/atom.xml` are valid empty feeds.
- The main post generator **does not** ingest notes.json yet; it continues to
  manage Blog and Music as before.
- The navigation and sitemap reference Notes.

**No Micropub service, Indiekit endpoint, GitHub write token, Mastodon
credential or Bluesky app password is provisioned by these changes.** Nothing
is posted to Mastodon or Bluesky automatically.

## Next development phase

Implement a validated notes-only generator that reads an explicit schema
(content, ISO 8601 publish date, immutable slug/ID, optional tags and reply
target), writes canonical individual `/notes/<id>.html` pages, updates
`notes/index.html`, the Notes RSS/Atom feeds and sitemap, and provides
`h-entry`, `e-content`, `dt-published`, `u-url` and author metadata.
Keep notes un-titled in the visible feed; feed titles can use excerpts.

Then deploy a separate authenticated Micropub server (e.g. Indiekit) which
writes **through a controlled GitHub workflow** and only to the notes source.
Micropub isn't a function of GitHub Pages or static Neocities hosting.
The public Notes HTML remains online whenever the writing service is offline.

For syndication, add separate opt-in Mastodon and Bluesky controls and durable
per-note status tracking. Send a note only after its canonical page is verified
to exist live on schmookey.xyz. Record real external post URLs as
`u-syndication`, and prevent duplicates during retries. Never expose service
tokens, app passwords, or write-capable GitHub credentials in public files.

GitHub Actions already has a review-gated Neocities deployment process; the
Micropub integration must not bypass that gate. Receiver functionality for
Webmentions is independent of Micropub, while displaying reactions may need
front-end changes.

No paid or always-on server has been configured here. Its hosting, cost and
availability can be decided independently of the static Notes site.
