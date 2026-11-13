# Trakt: Now Watching and About widget

This adds a **Trakt** watching journal (`/now-watching.html`) and a compact
**Last Watched** card to the About page. **ListenBrainz is unchanged.**

## How it works

A GitHub Actions job runs every six hours and on manual dispatch. It calls
the public Trakt history endpoint for `Pati3nt_Z3ro` (the account identifier in `https://app.trakt.tv/profile/Pati3nt_Z3ro`) and writes an
`assets/data/trakt-history.json` snapshot for a static site such as Neocities.
Both widgets load this file and never call Trakt with browser-side credentials.
The snapshot is public; only include viewing activity you are happy to publish.

## Enable automated updates

Under **Schmookey/Website → Settings → Secrets and variables → Actions**, add:

- `TRAKT_CLIENT_ID` — the **Production Client ID** for the registered Trakt application (required; Development and Production credentials are different)
- `TMDB_ACCESS_TOKEN` — TMDb API Read Access Token (optional, for posters)

Trakt viewing history must be publicly readable for the username configured in
`scripts/update_trakt_history.py`. No OAuth token is needed for this public
endpoint if the profile and history are public. The script deliberately fails
without overwriting the last working snapshot when the API is unavailable or
returns no history.

Run **Actions → Refresh public Trakt watch history → Run workflow** to test.

### HTTP 403 troubleshooting

A 403 is not evidence that a user's history is private. Trakt documents
HTTP 403 as an invalid API key or unapproved application. Confirm that
`TRAKT_CLIENT_ID` contains the Production **Client ID**, not the Client
Secret, and that the application has API access. Never paste secrets in an
issue or workflow log. The updater supplies the Trakt API headers, including
an identifying User-Agent.

If the correct Production Client ID still returns 403, check the application's
status with Trakt support. Do not rotate keys or create replacement apps to
circumvent an API restriction. A public user history endpoint that instead
returns 401 may require an OAuth access token; an OAuth integration would
need separate user approval and secure token storage.

The updater preserves the last valid JSON snapshot when an API request fails.
Its CI regression tests use mock API responses; green site checks do not prove
production Trakt access.
Check `assets/data/trakt-history.json` after the run. The workflow is triggered
on the repository's **default branch** only after this change is merged.

TMDb poster images are optional. Without TMDb credentials the widget displays
a labelled fallback when Trakt does not supply artwork. Existing cached
`The Sopranos` artwork is used in the initial snapshot.

## Diagnosing an approved app that returns no history

After confirming that the GitHub Actions secret `TRAKT_CLIENT_ID` is the
approved Production Client ID, run **Actions → Refresh public Trakt watch
history → Run workflow** (branch `main`). The script now logs:

- The number and type of rows returned by the public history endpoint.
- The number of entries that the widget can actually use.
- Whether Trakt resolves the configured public account slug and the public/private flag it reports (without printing profile details).
- Whether the public watched-movies and watched-shows endpoints return any
  entries or an HTTP error (without printing film or programme titles).
- Public aggregate watch counts if the account's public stats endpoint exposes
  them.

If the profile lookup does not resolve, or its returned slug does not match the configured username, correct the account identifier before changing authentication. If history returns zero rows but watched lists or stats are non-empty, the
problem is likely specific to history visibility or endpoint behaviour rather
than having no recorded watches. If all probes return empty data, that result
alone **does not prove** the profile or history is private. An HTTP 401 or 403
on the diagnostic endpoints is recorded as a status code without leaking keys.

These probes use only public endpoints and the configured Client ID. They do
**not** authorise private history access, use OAuth, print raw API responses,
or publish new JSON when the history is unusable. The existing snapshot is
preserved on failure. If viewing activity is not publicly retrievable, obtain
explicit permission before configuring user-authorised OAuth credentials.

## Automatic live updates on Neocities

The scheduled GitHub Actions updater runs every six hours and commits
`assets/data/trakt-history.json` to `main`, with optional TMDB posters.
The browser-side `assets/js/trakt-history.js` now loads that **public GitHub
snapshot** directly from
`https://raw.githubusercontent.com/Schmookey/Website/main/assets/data/trakt-history.json`.
The widget therefore receives new history on later page visits automatically,
without attempting a GitHub-to-Neocities upload.

To activate this behaviour, **manually upload the updated
`assets/js/trakt-history.js` file to Neocities once**. Do not upload an entire
site archive or overwrite manually edited About/Now Watching pages. Both pages
already reference this script. GitHub's raw file host is intended as a
public-file source; cross-origin availability and browser/network access still
need verification on the deployed site. The script falls back to the existing
`/assets/data/trakt-history.json` on Neocities if remote loading fails.
Visitors using the old script will continue to see whatever Neocities JSON
was last uploaded.

The browser makes no direct Trakt/TMDB API calls and never sees the API keys:
these stay exclusively in GitHub Actions secrets. The snapshot is public and
contains viewing activity; use this only for watches the account owner wishes
to publish. An open page refreshes its data about every 30 minutes while
visible. New entries may take up to the next scheduled GitHub Actions run plus
hosting cache propagation to appear; this is **not instantaneous**.
If external GitHub loading is blocked, the local fallback will be older until
manually replaced.

## Deployment

The initial widget HTML and CSS must already be present on Neocities, and
the updated Trakt JavaScript must be uploaded once. Thereafter the browser
can read GitHub's refreshed JSON directly, without Neocities publishing it.
No Neocities deployment workflow is needed for routine Trakt updates.

## References

- Original example: https://github.com/Schmookey/Trakt-Embed
- Trakt API: https://trakt.docs.apiary.io/
- TMDb API: https://developer.themoviedb.org/
