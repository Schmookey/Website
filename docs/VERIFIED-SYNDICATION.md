# Verified social syndication (opt-in)

This is an additional workflow. It does not replace the normal GitHub-to-Neocities
deployment, RSS, Atom, sitemap or Notes publishing workflows.

## How it works

1. Publish a new Blog post using the existing metadata and validation workflow, or
   create a new Note using **Actions → Publish an IndieWeb Note**.
2. For a Note, choose **none** (website only), **mastodon**, **bluesky**, or **both**.
   Existing Notes without a selection remain website only. A new Blog post
   published after 18 November 2026 15:45 UTC is eligible for both networks,
   unless its posts.json entry sets `"syndicate": false`.
3. The original article or Note is published to Neocities first. A successful
   Neocities deployment workflow then triggers a separate syndication workflow.
4. The syndication workflow checks the precise HTTPS permalink, HTTP status,
   canonical link, and first part of the authored text against the repository.
   Missing, redirected, stale, or incorrect pages stop publication.
5. When explicitly enabled, the workflow sends an excerpt and original permalink
   to the selected accounts and records the social URL.

**Nothing is posted by default.** The repository variable
`SOCIAL_SYNDICATION_ENABLED` must be explicitly set to `true`, and
appropriate GitHub Actions repository secrets must be configured:

- `MASTODON_ACCESS_TOKEN`: a token on mastodon.social for the `schmookey`
  account, with permission to create statuses.
- `BSKY_HANDLE`: the intended Bluesky account handle `schmookey.xyz`.
- `BSKY_APP_PASSWORD`: an app password for that Bluesky account.

Never commit secrets to the repository or include them in posts/Notes.

## Testing safely

Pull requests run the offline `tests/test_verified_syndication.py` suite and
the normal site checks. The normal Notes workflow remains available.

With the activation variable *unset*, a successful deployment runs only
live-page verification for any eligible content; no Mastodon/Bluesky POST calls
are made. **Actions → Verify live content and optionally syndicate** offers
a manual preview, with `verify_only` selected by default. In this mode it
lists eligible posts without publishing them. Turn off `verify_only` to
perform live verification while the activation variable remains disabled.

## Duplicate handling and recovery

The ledger at `social/syndication-state.json` stores a status for each
canonical permalink and each destination. Before submitting a social API
request, the workflow commits a **pending** record to `main`. Afterwards it
commits a **posted** record with the social URL. Any existing record, including
pending, is *never automatically retried*.

If a GitHub workflow fails after creating a pending record, check the social
account before making any corrections. An API request may have succeeded even
when the response was lost. Review or reconcile the state manually; don't
delete a pending record and retry without checking. Do not force-push over the
ledger. Posting is serialised by GitHub Actions concurrency.

The workflow checks that tokens point to the intended accounts before posting.
Mastodon uses a stable idempotency key; Bluesky uses a deterministic record key.
These are additional safeguards, not a reason to blindly retry.

A successful GitHub deployment check isn't by itself proof of a public post:
the separate HTTP and content check is essential. If a page is inaccessible or
stale, the workflow should fail with no social post for that page.

## Scope

New Blog posts and opted-in Notes only. No automatic backfill of old blog posts;
no syndication of Now, Changelog, Privacy, RSS, Trakt, or existing Notes. Site
content always remains the canonical source. Social networks are used only for
optional syndication; the website works without them.


## Previously shared content

The ledger may contain `manual-review` holds for content the owner has already shared manually. These entries suppress automatic publishing for the indicated platform without claiming a confirmed social post URL. Inspect the actual social account before removing any hold; leave it in place if the post already exists. Manual verify-only mode checks eligible, unheld content live and never publishes. Keep `SOCIAL_SYNDICATION_ENABLED` disabled until the account history and credentials have been reviewed.
