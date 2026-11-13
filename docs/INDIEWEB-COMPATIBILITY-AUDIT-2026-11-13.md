# IndieWeb compatibility audit — 13 November 2026

Scope: [Schmookey's World](https://schmookey.xyz), reviewed from the source
in `Schmookey/Website` on GitHub. **This is not a verified live Neocities audit.**
The public site and `.well-known` URLs could not be independently fetched
during this review. GitHub is a development source: the live site may differ.

## Existing strengths (preserve)

- Main pages declare the Webmention.io receiver:
  `<link rel="webmention" href="https://webmention.io/schmookey.xyz/webmention">`.
- The homepage exposes `h-card` and `rel="me"` profile references.
- Blog entries already use `h-entry`, `u-url`, `p-name`,
  `dt-published`, `e-content`, and `u-author`. The blog index uses post cards.
- Articles declare canonical URLs, and the site publishes RSS, Atom and JSON feeds.
- Several entries include **real** Mastodon/Bluesky `u-syndication` links.
  Preserve them and do not add invented links.
- Browser-side Webmention rendering is implemented in `assets/js/main.js`
  and requests `https://webmention.io/api/mentions.jf2?target=...` using the
  page's canonical URL. HTML escaping and URL checks help limit injection risks.

## Findings and suggested follow-up

### 1. Received mentions: needs end-to-end live verification — high priority

The JavaScript only displays mentions where `wm-property` is
`in-reply-to`, `like-of` or `repost-of`. Simple `mention-of` links,
bookmarks and other valid interactions are currently **not displayed**.
If desired, include these in a separate, thoroughly tested UI change while
preserving the present privacy and URL checks.

The checked-in `assets/data/webmentions.json` has an empty `children`
array, but the live comments widget calls **Webmention.io directly**.
Therefore that file does **not** demonstrate whether the live widget receives
or displays Webmentions.

Verify each article's exact canonical target and receiver registration with
Webmention.io. Test with a genuine linking source page (not a self-generated
fake response). Check the Webmention.io dashboard and browser developer
tools for target mismatches, rejected responses and Cross-Origin Resource
Sharing issues. Do not interpret an empty response as a broken receiver
without checking whether any mentions were actually sent.

### 2. Sending Webmentions — high priority, separate from receiving

The site advertises a *receiver*. No automatic outgoing Webmention sender
was identified in the reviewed source. When an article links to another
Webmention-enabled website, sending a Webmention is a separate step.

For a static Neocities site, a manually invoked sender or a separate
opt-in build/publishing step could be introduced. Do **not** assume
`indielib` sends Webmentions: its README points to a separate Go
Webmention library.

Important safety requirement: only send notifications for **published,
public, intentional links**, not drafts, arbitrary text, URLs supplied by
visitors or `rel="me"`/navigation/asset links. Implement rate limits and
idempotence before any automatic sending.

### 3. Publication time inconsistencies — medium priority

Some blog documents expose different instants across their social
`article:published_time` metadata and Microformats
`dt-published` element:

| Article | Social publication time | Microformats publication time |
| --- | --- | --- |
| `physical-media.html` | `2026-04-17T22:40:00+00:00` | `2026-03-29T22:40:00+01:00` |
| `august_updates.html` | `2026-08-12T20:45:00+00:00` | `2026-08-12T20:45:00+01:00` |
| `post1.html` | `2026-03-07T09:10:30+00:00` | `2026-03-07T10:30:00+00:00` |
| `this-week-23-29-march.html` | `2026-03-29T22:20:00+00:00` | `2026-03-29T22:20:00+01:00` |

These should be reconciled against the **actual original publication time**,
and any published feed timestamps and metadata, rather than guessing which is
correct. Date changes were deliberately **not made** in this PR.

### 4. Bridgy Fed custom address — pending hosting support

The repository includes feed discovery, Microformats and some syndication
links, but this does not prove the custom Fediverse address is federating.
Historically, `/.well-known/host-meta` and `/.well-known/webfinger`
have returned 404 on the live site; they could **not be rechecked here**.

If the desired Bridgy Fed setup requires protocol-specific redirects with
query-string preservation, confirm that the actual hosting layer supports
them. Merely uploading static files may not reproduce those redirects.
Do not announce a successful integration until independently tested.

### 5. Feed and profile consistency — medium priority

The repository includes RSS, Atom, JSON feed discovery and `rel="me"`
links. The static checks already validate XML/JSON syntax and internal links.
A later audit can test the feeds with external feed validators and review
whether the article publication dates match the feeds and canonical URLs.

## What this change actually does

- Adds offline IndieWeb metadata tests in
  `tests/test_indieweb_metadata.py`.
- Runs the checks in existing GitHub Actions static validation.
- Adds this report. **No blog text, feeds, styling, live widgets, secrets,
  Neocities upload or outgoing Webmention automation were changed.**

## Why not install indielib?

`hacdias/indielib` is a Go package for IndieAuth, Micropub and
Microformats post discovery; it is not an installable JavaScript widget or
Webmention reception service. It would require a separate server/backend
for its IndieAuth and Micropub components. For this existing static site,
fixing markup and Webmention handling directly is smaller and safer.

References:

- [indielib source](https://github.com/hacdias/indielib)
- [Webmention specification](https://www.w3.org/TR/webmention/)
- [Microformats2 vocabulary](https://microformats.org/wiki/microformats2)
- [Webmention.io](https://webmention.io/)
- [IndieWeb wiki](https://indieweb.org/)
