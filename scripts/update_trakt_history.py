#!/usr/bin/env python3
"""Produce a public, credential-free Trakt history JSON snapshot.

GitHub Actions supplies TRAKT_CLIENT_ID (required) and TMDB_ACCESS_TOKEN
(optional). Never expose credentials in public HTML, JSON or workflow logs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

USER = "pat13nt_z3r0"
OUT = Path(__file__).resolve().parent.parent / "assets/data/trakt-history.json"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "trakt-api-version": "2",
}
TMDB_IMAGE = "https://image.tmdb.org/t/p/w200"


def get_json(url: str, headers: dict[str, str]) -> object:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def poster_for(kind: str, tmdb_id: object, token: str, cache: dict) -> str:
    if not token or not str(tmdb_id).isdigit():
        return ""
    key = (kind, str(tmdb_id))
    if key in cache:
        return cache[key]
    url = "https://api.themoviedb.org/3/" + kind + "/" + quote(str(tmdb_id))
    image = ""
    try:
        data = get_json(url, {
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        })
        path = data.get("poster_path") if isinstance(data, dict) else None
        if isinstance(path, str) and path.startswith("/") and "/" not in path[1:]:
            image = TMDB_IMAGE + path
    except (OSError, ValueError, TypeError) as exc:
        print("Poster not available for", kind, tmdb_id, type(exc).__name__)
    cache[key] = image
    return image


def normalise(row: dict, token: str, cache: dict) -> dict | None:
    kind = row.get("type")
    if kind not in ("show", "episode", "movie"):
        return None
    if kind == "movie":
        movie = row.get("movie") or {}
        title = movie.get("title")
        ids = movie.get("ids") or {}
        if not title:
            return None
        slug = ids.get("slug")
        link = "https://trakt.tv/movies/" + quote(str(slug)) if slug else "https://trakt.tv/users/" + USER
        return {
            "title": str(title), "type": "Movie",
            "year": movie.get("year"), "link": link,
            "cover": poster_for("movie", ids.get("tmdb"), token, cache),
            "watched_at": row.get("watched_at"),
        }
    show = row.get("show") or {}
    episode = row.get("episode") or {}
    title = show.get("title")
    if not title:
        return None
    ids = show.get("ids") or {}
    slug = ids.get("slug")
    link = "https://trakt.tv/shows/" + quote(str(slug)) if slug else "https://trakt.tv/users/" + USER
    result = {
        "title": str(title), "type": "TV Show",
        "episode": episode.get("title") or "",
        "season": episode.get("season"),
        "episode_number": episode.get("number"),
        "year": show.get("year"),
        "link": link,
        "cover": poster_for("tv", ids.get("tmdb"), token, cache),
        "watched_at": row.get("watched_at"),
    }
    return result


def main() -> None:
    client = os.environ.get("TRAKT_CLIENT_ID", "").strip()
    if not client:
        raise SystemExit("TRAKT_CLIENT_ID not configured; retaining existing snapshot.")
    headers = {**HEADERS, "trakt-api-key": client}
    token = os.environ.get("TMDB_ACCESS_TOKEN", "").strip()
    data = get_json("https://api.trakt.tv/users/" + USER + "/history?limit=30", headers)
    if not isinstance(data, list):
        raise SystemExit("Unexpected Trakt response: not a list; retaining snapshot.")
    cache = {}
    items = [item for row in data if isinstance(row, dict)
             if (item := normalise(row, token, cache)) is not None]
    # Empty data can mean history is private. Never overwrite a valid snapshot.
    if not items:
        raise SystemExit("No public watches returned; retaining existing snapshot.")
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Trakt public watch history (cached by GitHub Actions)",
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated public Trakt snapshot with", len(items), "items.")


if __name__ == "__main__":
    main()
