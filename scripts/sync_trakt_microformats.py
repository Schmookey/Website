#!/usr/bin/env python3
"""Synchronise the static Trakt h-entry on About from the public watch snapshot.

Keeps HTML-only Microformats2 parsers up to date without changing the existing
Trakt JavaScript widget or publishing anything to the website host.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "assets/data/trakt-history.json"
ABOUT = ROOT / "about.html"
START = "<!-- TRAKT_MF2_START: generated from assets/data/trakt-history.json -->"
END = "<!-- TRAKT_MF2_END -->"
SAFE_POSTER = re.compile(
    r"^https://image\.tmdb\.org/t/p/w(?:92|154|185|200|300|342|500)/"
    r"[A-Za-z0-9._-]+\.(?:jpg|jpeg|png|webp)$", re.I
)


def safe_item_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    url = urlsplit(value)
    if (url.scheme != "https" or url.netloc != "trakt.tv" or
            url.username or url.password or url.query or url.fragment):
        return ""
    if not re.fullmatch(r"/(?:shows|movies)/[A-Za-z0-9._%-]+", url.path):
        return ""
    return value


def build_card(item: dict) -> str:
    title = str(item.get("title") or "").strip()
    url = safe_item_url(item.get("link"))
    watched = item.get("watched_at")
    if not title or not url or not isinstance(watched, str):
        raise ValueError("Cannot publish a static watch without title, item URL and watch date.")
    date = datetime.fromisoformat(watched.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("Watch time must contain timezone information.")
    date = date.astimezone(timezone.utc)
    image = item.get("cover")
    artwork = (
        f'<img class="media-thumb" src="{html.escape(image, quote=True)}" '
        f'alt="Poster for {html.escape(title, quote=True)}" loading="lazy" '
        f'referrerpolicy="no-referrer">'
        if isinstance(image, str) and SAFE_POSTER.fullmatch(image) else
        '<span class="trakt-about-thumb">TRAKT</span>'
    )
    details = []
    if item.get("type") == "TV Show":
        season, episode = item.get("season"), item.get("episode_number")
        if type(season) is int and type(episode) is int and season >= 0 and episode >= 0:
            details.append(f"S{season:02d}E{episode:02d}")
        if isinstance(item.get("episode"), str) and item["episode"].strip():
            details.append(item["episode"].strip())
    if type(item.get("year")) is int:
        details.append(str(item["year"]))
    subtitle = (f'<p class="media-subtitle">{html.escape(" · ".join(details))}</p>'
                if details else "")
    display_date = date.strftime("%-d %b %Y, %H:%M UTC")
    return f"""<!-- TRAKT_MF2_START: generated from assets/data/trakt-history.json -->
    <article class="media-card trakt-about-card h-entry">
      <div class="media-thumb-wrap">
        {artwork}
      </div>
      <div class="media-meta">
        <p class="media-label">Last Watched</p>
        <p class="media-title p-name"><a class="u-watch-of" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(title)}</a></p>
        {subtitle}
        <time class="media-submeta dt-published" datetime="{date.isoformat(timespec='milliseconds').replace('+00:00', 'Z')}">Watched {display_date}</time>
      </div>
    </article>
    <!-- TRAKT_MF2_END -->"""


def synchronise(about: Path = ABOUT, snapshot: Path = SNAPSHOT) -> bool:
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("Invalid Trakt snapshot")
    if not data["items"]:
        print("No watch entries; retaining current HTML.")
        return False
    source = about.read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("Expected exactly one static Trakt microformat marker pair.")
    begin = source.index(START)
    finish = source.index(END, begin) + len(END)
    content = source[:begin] + build_card(data["items"][0]) + source[finish:]
    if content == source:
        return False
    about.write_text(content, encoding="utf-8")
    return True


if __name__ == "__main__":
    print("Updated static About Trakt microformat:" , synchronise())
