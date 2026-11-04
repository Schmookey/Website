#!/usr/bin/env python3
"""Overlay the reviewed site archive on a GitHub preparation branch.

This script works only in a clean checkout of the specified release preparation
branch. It will not push, commit, or alter the live website. README, LICENSE,
GitHub workflows and release tooling are retained unless the ZIP includes them.
"""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

EXPECTED_BRANCH = 'release/schmookey-site-v1-prep'
PROTECTED_PREFIXES = ('.git/', '.github/', 'docs/', 'tests/', 'scripts/')
PROTECTED_FILES = {'README.md', 'LICENSE', '.gitignore'}


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True).strip()


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 scripts/sync_archive_to_git.py /path/to/schmookey-website-release-candidate.zip')
        return 2
    archive = Path(sys.argv[1]).expanduser().resolve()
    if not archive.is_file():
        print(f'Archive not found: {archive}')
        return 2
    root = Path(git('rev-parse', '--show-toplevel')).resolve()
    if Path.cwd().resolve() != root:
        print('Run this from the root of the Website repository.')
        return 2
    branch = git('branch', '--show-current')
    if branch != EXPECTED_BRANCH:
        print(f'Refusing to edit branch {branch!r}; switch to {EXPECTED_BRANCH!r}.')
        return 2
    if git('status', '--porcelain'):
        print('The repository has uncommitted changes. Please commit, stash or discard them first.')
        return 2
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            print('Archive CRC check failed. Nothing changed.')
            return 2
        paths = [i.filename for i in z.infolist() if not i.is_dir()]
        if not {'index.html', 'assets/js/main.js', 'assets/js/archive.js', 'site.webmanifest'} <= set(paths):
            print('This does not appear to be the complete reviewed website archive.')
            return 2
        for filename in paths:
            pp = PurePosixPath(filename)
            if pp.is_absolute() or '..' in pp.parts or '\\' in filename:
                print(f'Archive contains unsafe path: {filename}')
                return 2
        # Delete obsolete tracked website files, but preserve repo-only docs/CI.
        tracked = subprocess.check_output(['git', 'ls-files', '-z']).decode('utf-8').split('\0')
        stale = [p for p in tracked if p and p not in paths and
                 p not in PROTECTED_FILES and not p.startswith(PROTECTED_PREFIXES)]
        for p in stale:
            (root / p).unlink(missing_ok=True)
        for filename in paths:
            # Repo-only release configuration is authoritative over the ZIP.
            if filename in PROTECTED_FILES or filename.startswith(PROTECTED_PREFIXES):
                continue
            dest = root / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(filename) as source, dest.open('wb') as target:
                shutil.copyfileobj(source, target)
        print(f'Copied {len(paths)} reviewed site files; removed {len(stale)} obsolete tracked files.')
        print('Review changes with: git status --short && git diff --stat')
        print('When satisfied: git add -A && git commit -m "Sync reviewed site for v1.0.0" && git push -u origin '+EXPECTED_BRANCH)
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        print('Git operation failed:', exc)
        sys.exit(2)
