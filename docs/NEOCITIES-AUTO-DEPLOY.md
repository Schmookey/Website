# Neocities Marketplace automatic deployment (review-gated)

This proposal stages public site files and uses [Deploy to Neocities](https://github.com/marketplace/actions/deploy-to-neocities) **after** the existing Static website checks workflow succeeds on a `main` push.

## Safety constraints

- Automatic publishing is **disabled by default**. Set the repository Actions variable `NEOCITIES_AUTO_DEPLOY_ENABLED` to `true` only after reconciling current Neocities content with GitHub and confirming a backup.
- Reuses the existing GitHub Actions secret `NEOCITIES_API_KEY`. Do not commit API keys or include them in web-accessible files.
- Uses an immutable commit of Marketplace action v3.0.6. The deployment action's `cleanup: false` means it does not delete remote orphaned files.
- Files uploaded are staged in `public/`, excluding `.github/`, scripts, tests, Markdown, ZIP backups and other source files.
- **Never uploads** `assets/data/trakt-history.json`, which is independently maintained by GitHub Actions and fetched by the widget. Site announcements in `assets/data/site-updates.json` are now managed in GitHub, and are included in the public deployment together with the generated feeds and sitemap.
- GitHub Actions checks must pass first. Deployments verify that the tested revision is still `main` before any upload, and validate the Neocities API key's destination is `schmookey.xyz`.
- First test with the deployment variable unset. A manual `workflow_dispatch` defaults to preview only.
- This pipeline does **not** enable Mastodon/Bluesky syndication. That must be separately protected with live-publication verification and duplicate detection.

## Activation checklist

1. Download and keep a complete backup of Neocities.
2. Review discrepancies between Neocities and `main`, especially pages manually edited on Neocities.
3. Confirm that the `Static website checks` workflow succeeds on `main`.
4. Ensure `NEOCITIES_API_KEY` is set as an Actions repository secret (existing manual deploy workflows use the same secret).
5. Set `NEOCITIES_AUTO_DEPLOY_ENABLED=true` in Settings → Secrets and variables → Actions → Variables.
6. Trigger a new `main` push and verify that only intended files upload. To suspend publishing, remove or set that variable to `false`.

A successful staging test is not equivalent to a live deployment test. Review and enable only after backup reconciliation.
