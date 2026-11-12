# Neocities manual deployment — deliberately disabled

The repository and the live Neocities site are **not automatically synchronised**.
This workflow is installed so the deployment can be reviewed and enabled **later**,
after a complete copy of the current live Neocities site has been saved.

**Current state: disabled. Installing or merging this workflow does not upload
anything to Neocities.** It has no push or timer triggers, and it will not run
merely because a commit is merged.

## Backup received and checked — 12 November 2026

A ZIP download of the live Neocities website was provided on 12 November 2026.
Its archive integrity check passed (118 website files), and its copies of all
three deployable paths below match the corresponding files in GitHub `main`
after the backup reconciliation in pull request #15.

This **does not verify that the live Neocities server has remained unchanged**
since the download. Before enabling any upload, run the read-only **preview**
action and check the returned live-file differences. If the preview reports
differences, review those individually against the backup and GitHub.
If all selected files say **UNCHANGED**, no deployment is necessary.

The backup ZIP was provided separately; **it is not committed to GitHub**.
Retain your own copy outside Neocities and GitHub.

## Trakt-only publishing (new, deliberately manual)

The Trakt API connection now works: GitHub refreshes
`assets/data/trakt-history.json` from the verified public Trakt account
`Pati3nt_Z3ro`. **GitHub commits do not automatically publish to Neocities.**

The existing guarded deployment workflow now has a **group** selector:

- `trakt-widget` (recommended for the first deployment): only
  `assets/data/trakt-history.json` and `assets/js/trakt-history.js`.
- `trakt-snapshot` (recommended for later history refreshes): only
  `assets/data/trakt-history.json`.
- `site` (the original legacy allowlist): only
  `assets/js/main.js`, `assets/css/style.css` and `privacy.html`.

The Trakt groups **never upload** `about.html`, `now-watching.html`,
`assets/data/site-updates.json`, social icons, or any other edited files.
The new history JSON already contains real viewing data. Confirm you're
comfortable publishing that data before deploying.

**First run a read-only comparison:** in Actions, open
**Neocities manual deployment (disabled by default)** → **Run workflow**,
choose `action=preview`, `group=trakt-widget`, branch `main`.
Check the two statuses and that the remote domain is `schmookey.xyz`.
No upload occurs in preview mode.

**Only after a fresh live-site backup and reviewing the preview:** set the
Actions repository variable `NEOCITIES_DEPLOY_ENABLED=true`, then manually
run the workflow with `action=deploy`, `group=trakt-widget` and the exact
confirmation `DEPLOY SCHMOOKEY.XYZ`. It uploads only selected differing
files, never deletes remote content, and preserves unrelated edits.

After the initial widget deployment, use `trakt-snapshot` to publish
subsequent JSON updates without replacing the browser script again.
This is manual; scheduled GitHub history refreshes do **not** trigger a
Neocities upload. Automatic publishing is intentionally not enabled.

If your live pages do not yet load `/assets/js/trakt-history.js`, updating
only those two files will not create the widget. Review `about.html` and
`now-watching.html` separately rather than overwriting manually edited
Neocities HTML blindly.

## Trakt publishing when GitHub Actions variables cannot be added

If GitHub returns **“Unable to add variable. Please try again.”** while creating
`NEOCITIES_DEPLOY_ENABLED`, use the dedicated workflow
[Publish Trakt to Neocities (manual backup-confirmed)](../.github/workflows/neocities-trakt-confirmed-deploy.yml).
The original deployment workflow and its required variable remain unchanged.

1. Download and independently keep an up-to-date copy of the **live** Neocities
   site before publishing. This workflow cannot create a remote backup.
2. On the `main` branch, run the new workflow with `action=preview` and
   `group=trakt-widget`; inspect which files differ. Preview never uploads.
3. To publish, manually run it again on `main`, selecting `action=deploy`
   and `group=trakt-widget`. Enter **both** exact confirmations:
   - `BACKUP VERIFIED SCHMOOKEY.XYZ`
   - `DEPLOY TRAKT TO SCHMOOKEY.XYZ`
4. Verify the workflow log says that the expected custom domain was confirmed
   and reports precisely which Trakt files were uploaded.

For later data-only refreshes, choose `trakt-snapshot` and make the same
explicit confirmations after checking the latest live copy. The new workflow
has no push or schedule trigger and supports **only** these two Trakt groups:
`trakt-widget` uploads the history JSON and Trakt widget JavaScript;
`trakt-snapshot` uploads just the JSON. No HTML, CSS, site updates, icons,
or other files can be selected through this workflow. The API key stays in
the existing GitHub Actions secret, never in the website or workflow logs.

## What is protected

Only these three paths can be uploaded by the legacy `site` group:

- `assets/js/main.js`
- `assets/css/style.css`
- `privacy.html`

The separate Trakt groups above additionally allow only the Trakt JSON and
Trakt widget JavaScript. In particular, `assets/data/site-updates.json` and all other JSON/content,
images, HTML articles and manually edited remote files are **not touched**.
There is no delete, prune, or site-wide synchronisation operation.

## Safely inspect the differences (read-only)

After the workflow appears in the Actions tab:

1. Open **Actions → Neocities manual deployment (disabled by default)**.
2. Choose **Run workflow**, leaving **action = preview**, and choose the
   appropriate **group** (`trakt-widget`, `trakt-snapshot`, or legacy `site`).
3. The workflow uses the `NEOCITIES_API_KEY` secret to check the destination
   site and compare file hashes. It lists only the files in the selected group
   which differ. **Preview never uploads or modifies files.**

The API key must belong to the custom domain `schmookey.xyz`; a mismatched
site identity causes the check to stop rather than risk publishing elsewhere.

## Later: enable deliberate uploads (not yet)

**Only after you have downloaded or otherwise independently backed up the
latest *live* site:**

1. In **Settings → Secrets and variables → Actions → Variables**, create
   the repository variable `NEOCITIES_DEPLOY_ENABLED` with value `true`.
   The variable does not currently exist and is intentionally not set here.
2. Manually run this same workflow with **action = deploy**.
3. Type `DEPLOY SCHMOOKEY.XYZ` into the confirmation field.
4. The script checks the destination domain and remote hashes first,
   then uploads **only differing files from the fixed allowlist**.

Removing the variable or changing its value away from `true` disables
uploads again. No API key value should ever be committed, pasted into an
issue, or printed to Actions logs.

The workflow does not create backups and does not guarantee that GitHub is
synchronised with any later remote edits. Before each deployment, confirm that
a fresh copy of live-site content exists, review the preview output and make
sure no remote manual changes will be overwritten.

Implementation: `.github/workflows/neocities-manual-deploy.yml` and
`scripts/neocities_manual_deploy.py`. The API endpoints are documented at
https://neocities.org/api.
