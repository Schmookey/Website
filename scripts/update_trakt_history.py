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
from urllib.error import HTTPError, URLError

USER = "pat13nt_z3r0"
OUT = Path(__file__).resolve().parent.parent / "assets/data/trakt-history.json"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "User-Agent": "SchmookeysWorld-TraktWidget/1.0 (https://schmookey.xyz)",
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
    try:
        data = get_json("https://api.trakt.tv/users/" + USER + "/history?limit=30", headers)
    except HTTPError as exc:
        # Never print request headers or response bodies: they might contain secrets.
        if exc.code == 403:
            raise SystemExit(
                "Trakt returned HTTP 403 (Forbidden). Verify TRAKT_CLIENT_ID is "
                "the Production Client ID for an approved API app. If it is, "
                "check the app's API access status with Trakt. The existing "
                "history snapshot was not changed."
            ) from None
        if exc.code == 401:
            raise SystemExit(
                "Trakt returned HTTP 401 (Unauthorised). This endpoint may "
                "require an OAuth token, or the application credentials "
                "may be incorrect. Snapshot preserved."
            ) from None
        raise SystemExit(f"Trakt returned HTTP {exc.code}; snapshot preserved.") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(
            f"Trakt request failed ({type(exc).__name__}); snapshot preserved."
        ) from None
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
