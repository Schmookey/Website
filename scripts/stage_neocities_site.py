#!/usr/bin/env python3
"""Stage only public website files for the Neocities Marketplace action.

No deployment occurs here. Never stage source code, CI configuration, secret
files, repository archives, or automatically managed Trakt history.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ROOT_FILES = {
    "404.html", "BingSiteAuth.xml", "about.html", "atom.xml",
    "blog-archive.html", "changelog.html", "feed.json", "feed.xml",
    "index.html", "listening.html", "music-archive.html",
    "now-watching.html", "now.html", "offline.html", "privacy.html",
    "robots.txt", "site.webmanifest", "sitemap.xml", "webrings.html",
    "android-chrome-192x192.png", "android-chrome-512x512.png",
    "apple-touch-icon.png", "favicon-16x16.png", "favicon-32x32.png",
    "favicon.ico", "internet_archive.gif",
}
DIRECTORIES = ("assets", "blog", "music", "random")
ASSET_EXTENSIONS = {".html", ".css", ".js", ".json", ".png", ".jpg",
                    ".jpeg", ".gif", ".webp", ".svg", ".ico", ".avif",
                    ".woff", ".woff2", ".webmanifest"}
SKIP = {
    "assets/data/trakt-history.json",  # GitHub Actions owns this snapshot
}


def stage(destination: Path = PUBLIC) -> list[str]:
    if destination.resolve() == ROOT.resolve() or ROOT.resolve() in destination.resolve().parents and destination.resolve() == ROOT:
        raise ValueError("Refusing to stage into repository root")
    staged: list[str] = []
    for source in sorted(ROOT.rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(ROOT)
        rel = relative.as_posix()
        if destination.resolve() in source.resolve().parents:
            continue
        if rel in SKIP:
            continue
        if rel not in ROOT_FILES and not (
            relative.parts[0] in DIRECTORIES
            and source.suffix.lower() in ASSET_EXTENSIONS
        ):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        staged.append(rel)
    if "index.html" not in staged or "assets/css/style.css" not in staged:
        raise RuntimeError("Required website files are missing")
    if "assets/data/trakt-history.json" in staged:
        raise RuntimeError("Trakt history must not enter generic deployment")
    return staged


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PUBLIC)
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    files = stage(args.output)
    print(f"Staged {len(files)} public website files (no Trakt snapshot).")
