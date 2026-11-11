# Neocities manual deployment — deliberately disabled

The repository and the live Neocities site are **not automatically synchronised**.
This workflow is installed so the deployment can be reviewed and enabled **later**,
after a complete copy of the current live Neocities site has been saved.

**Current state: disabled. Installing or merging this workflow does not upload
anything to Neocities.** It has no push or timer triggers, and it will not run
merely because a commit is merged.

## What is protected

Only these three paths can ever be uploaded by this workflow:

- `assets/js/main.js`
- `assets/css/style.css`
- `privacy.html`

In particular, `assets/data/site-updates.json` and all other JSON/content,
images, HTML articles and manually edited remote files are **not touched**.
There is no delete, prune, or site-wide synchronisation operation.

## Safely inspect the differences (read-only)

After the workflow appears in the Actions tab:

1. Open **Actions → Neocities manual deployment (disabled by default)**.
2. Choose **Run workflow**, leaving **action = preview**.
3. The workflow uses the `NEOCITIES_API_KEY` secret to check the destination
   site and compare file hashes. It lists only which of the three allowlisted
   files differ. **Preview never uploads or modifies files.**

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

The workflow does not create backups, and it does not prove that GitHub is a
complete copy of your live Neocities website. Do not enable deployment while
your latest live-site backup is unavailable.

Implementation: `.github/workflows/neocities-manual-deploy.yml` and
`scripts/neocities_manual_deploy.py`. The API endpoints are documented at
https://neocities.org/api.
