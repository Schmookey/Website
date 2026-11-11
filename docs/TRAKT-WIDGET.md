# Trakt: Now Watching and About widget

This adds a **Trakt** watching journal (`/now-watching.html`) and a compact
**Last Watched** card to the About page. **ListenBrainz is unchanged.**

## How it works

A GitHub Actions job runs every six hours and on manual dispatch. It calls
the public Trakt history endpoint for `pat13nt_z3r0` and writes an
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

## Deployment

GitHub changes do not automatically update Neocities. Deploy the new HTML,
JavaScript, CSS and JSON to the hosting platform. To receive automated history
updates on Neocities, also arrange for the refreshed JSON to be uploaded from
GitHub. A GitHub Action committing JSON is not itself a Neocities deployment.

## References

- Original example: https://github.com/Schmookey/Trakt-Embed
- Trakt API: https://trakt.docs.apiary.io/
- TMDb API: https://developer.themoviedb.org/
