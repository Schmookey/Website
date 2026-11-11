# Website review — 11 November 2026

This review covers the GitHub source repository, its workflows, and the Trakt
integration. Passing source checks do **not** prove that the live hosting copy
has been deployed or that external APIs work.

## Findings and priority

| Priority | Finding | Recommended action |
| --- | --- | --- |
| High | Trakt refresh returned HTTP 403 on the latest recorded run; the repository's history snapshot is an older manual entry. | Confirm the Production Client ID in the `TRAKT_CLIENT_ID` Actions secret and the application's approval status. Never publish the secret. The updater now reports actionable errors and preserves the snapshot. |
| High | The repository explicitly has no automatic deployment to the live hosting service. | Document and test a secure deployment approach before relying on six-hourly GitHub snapshot updates on the website. Do not automatically upload a JSON update until deployment credentials are intentionally configured. |
| Medium | The default `main` branch has no enforced branch protection. | Require the static website checks and pull-request review before merging, if the repository's GitHub plan supports the rules. |
| Medium | `webrings.html` embeds remote scripts that execute in the visitor's browsing context. | Consider replacing with reviewed static links or sandboxed third-party content. Validate a Content Security Policy in Report-Only mode where supported. |
| Medium | Parts of `assets/css/style.css` still use text sizes of 9–11px in media widgets. | Increase small text sizes and keyboard target sizes where they harm readability; test at 320–420px widths and 200% zoom. |
| Low | Several large PNG/JPEG sources coexist with smaller WebP derivatives (e.g. `assets/images/header-banner.png` versus `header-banner.webp`). | Verify which files are actually referenced, then remove unused duplicates or optimise source assets without losing attribution. |
| Low | `README.md` does not list the new Now Watching page and Trakt-specific test command in its introductory sections. | Update documentation in a future maintenance pass. |
| Low | TMDb poster assets should carry proper attribution if external TMDb API data or images are used. | Confirm and add TMDb notice and logo where TMDb's current terms require it. |

## Existing strengths

- Static HTML, CSS and JavaScript only; no PHP application runtime or database.
- CI validates internal links, content assets, JavaScript syntax, and targeted security tests.
- The Trakt widget loads public JSON and restricts poster and outgoing link URLs.
- Widget strings use `textContent` where Trakt data appears.
- GitHub Action credentials are passed via secrets rather than embedded in browser code.
- Separate privacy disclosures explain ListenBrainz, Trakt, and publicly shared media activity.

## Follow-up verification

1. Re-run `Refresh public Trakt watch history` after confirming the Production Client ID.
2. Check that the workflow succeeds **and** `assets/data/trakt-history.json` contains fresh records.
3. Verify the live site's HTML and JSON file reflect the GitHub snapshot; a successful GitHub commit alone is insufficient.
4. Test the latest About, Now Watching, and ListenBrainz pages using Firefox at desktop and mobile widths with keyboard-only navigation.
5. Re-check external service access, Webmention delivery, and site-side caching after deployment.

The Trakt HTTP status details and the repository findings were verified on
11 November 2026. API authorisation or a working live-host deployment are not
claimed in this report.
