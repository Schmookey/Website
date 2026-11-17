# Neocities ZIP reconciliation — 17 November 2026

Source: user-provided `neocities-schmookey(1).zip` (132 files), compared against the GitHub `main` file tree via Git blob SHA-1, with article text separately checked.

## Findings

- All shared files in the ZIP matched GitHub except **three files**: `assets/data/posts.json`, `blog/index.html` and `assets/data/trakt-history.json`.
- The ZIP's `blog/posts/November Update.html` uses a different name from GitHub's `blog/posts/november_update.html`. The article body in both copies matches exactly. They already contain existing Mastodon and Bluesky syndication links.
- The ZIP's blog index and `posts.json` point to `/blog/posts/November%20Update`, a path without a corresponding file in the uploaded ZIP. The blog index also has one read-more URL with `.html` appended. GitHub has already fixed all three links to `/blog/posts/november_update.html`. **Retain the GitHub versions** rather than reintroducing broken links.
- The uploaded ZIP includes an older Trakt history snapshot. GitHub's automatic snapshot shows **Amandaland — Careers Week** as the most recent watch (snapshot timestamp at comparison: 2026-11-17 04:32 UTC). **Retain the GitHub snapshot**, do not replace it with the ZIP's copy.
- The GitHub November article had a December publication date in JSON-LD and `dt-published`, despite its visible 15 November date and `posts.json` timestamp. The original also included `noindex, nofollow`. This PR aligns publication metadata to `2026-11-15T12:00:00+00:00` and removes the noindex directive; the article body is unchanged.
- Existing `main` has repo-only files including workflows, tests, and a newer Trakt updater; these remain untouched.

## Deliberately not changed

- `assets/data/trakt-history.json` and `assets/js/trakt-history.js`
- The already-correct `assets/data/posts.json` and `blog/index.html`
- The existing blog article paragraphs, images, CSS, social syndication links, and other pages
- Live Neocities, GitHub `main`, or automatic deployment activation

## Publishing notes

The reconciled canonical URL for November Update is `https://schmookey.xyz/blog/posts/november_update.html`. If the live Neocities site still serves the old filename with a space, coordinate canonical/redirect handling before removing that file, since older shared links may use it. The automated Neocities deploy is separately proposed in PR #36 and is still disabled pending review.
