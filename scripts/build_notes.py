#!/usr/bin/env python3
"""Publish short, plain-text IndieWeb Notes without a Micropub server.

The only authored data is assets/data/notes.json. All generated HTML and feeds
are deterministic. User text is always HTML/XML escaped.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://schmookey.xyz"
SOURCE = Path("assets/data/notes.json")
INDEX = Path("notes/index.html")
BEGIN = "<!-- BEGIN GENERATED NOTES -->"
END = "<!-- END GENERATED NOTES -->"
IDENTIFIER = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-\d+$")
ATOM = "http://www.w3.org/2005/Atom"
IMAGE_PATH = re.compile(r"^/assets/images/[a-zA-Z0-9_-][a-zA-Z0-9_./-]*\.(?:jpg|jpeg|png|gif|webp|avif)$", re.I)



def published(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Note date must be a string")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid note date") from exc
    if date.tzinfo is None:
        raise ValueError("Note date must include a timezone")
    return date.astimezone(timezone.utc)


def verify_image(root: Path, path: str, alt: str) -> None:
    """Allow only public, local, repository-stored images with descriptive alt text."""
    if not isinstance(path, str) or not IMAGE_PATH.fullmatch(path):
        raise ValueError("Image must be a local /assets/images/ file (JPEG, PNG, GIF, WebP or AVIF)")
    relative = Path(path.lstrip("/"))
    if ".." in relative.parts or not (root / relative).is_file():
        raise ValueError("Image is missing from assets/images or uses an unsafe path")
    if not isinstance(alt, str) or not alt.strip() or len(alt) > 300:
        raise ValueError("Provide an image description (1–300 characters)")
    if re.search(r"[\x00-\x1f]", alt):
        raise ValueError("Image description contains unsupported characters")


def note_url(note: dict) -> str:
    return f"/notes/{note['id']}.html"


def read_notes(root: Path = ROOT) -> list[dict]:
    data = json.loads((root / SOURCE).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Notes source must be a JSON list")
    seen = set()
    for note in data:
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object")
        key = note.get("id")
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or key in seen:
            raise ValueError("Invalid or duplicate note identifier")
        seen.add(key)
        date = published(note.get("date"))
        if not key.startswith(date.strftime("%Y-%m-%d") + "-"):
            raise ValueError("Note identifier must match its UTC publication day")
        body = note.get("content")
        if (not isinstance(body, str) or not body.strip() or len(body) > 2000
                or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", body)):
            raise ValueError("Note content must contain 1–2000 characters")
        picture = note.get("image", "")
        alt = note.get("image_alt", "")
        if picture:
            verify_image(root, picture, alt)
        elif alt:
            raise ValueError("Image description requires an image")
        if note.get("syndicate", "none") not in {"none", "mastodon", "bluesky", "both"}:
            raise ValueError("Invalid Note syndication option")
        tags = note.get("tags", [])
        if not isinstance(tags, list) or len(tags) > 10 or any(
            not isinstance(tag, str) or not re.fullmatch(r"[a-z0-9][a-z0-9 -]{0,39}", tag)
            for tag in tags
        ):
            raise ValueError("Invalid note tags")
    return sorted(data, key=lambda item: (published(item["date"]), item["id"]), reverse=True)


def add_note(root: Path, content: str, tags: str, run_id: str,
             image: str = "", image_alt: str = "", syndicate: str = "none") -> str:
    if (not isinstance(content, str) or not content.strip() or len(content) > 2000
            or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", content)):
        raise ValueError("Note must contain 1–2000 safe plain-text characters")
    if not re.fullmatch(r"\d+", run_id):
        raise ValueError("Publishing requires GitHub's numeric workflow run ID")
    if image:
        verify_image(root, image, image_alt)
    elif image_alt:
        raise ValueError("Image description requires an image")
    if syndicate not in {"none", "mastodon", "bluesky", "both"}:
        raise ValueError("Invalid Note syndication option")
    parsed_tags = list(dict.fromkeys(
        word.strip().lower() for word in tags.split(",") if word.strip()
    ))
    now = datetime.now(timezone.utc)
    identifier = now.strftime("%Y-%m-%d-%H%M%S") + "-" + run_id
    note = {
        "id": identifier,
        "date": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "content": content.strip(),
        "tags": parsed_tags,
    }
    if syndicate != "none":
        note["syndicate"] = syndicate
    if image:
        note["image"] = image
        note["image_alt"] = image_alt.strip()
    notes = read_notes(root)
    for existing in notes:
        # A rerun of a successful job must never create a duplicate social note.
        if existing["id"].endswith("-" + run_id):
            if (existing["content"] != note["content"]
                    or existing.get("tags", []) != parsed_tags
                    or existing.get("image", "") != image
                    or existing.get("image_alt", "") != image_alt.strip()
                    or existing.get("syndicate", "none") != syndicate):
                raise ValueError("This run ID already belongs to a different note")
            return note_url(existing)
    if len(parsed_tags) > 10 or any(not re.fullmatch(r"[a-z0-9][a-z0-9 -]{0,39}", tag) for tag in parsed_tags):
        raise ValueError("Invalid note tags")
    notes.append(note)
    (root / SOURCE).write_text(
        json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    read_notes(root)  # Validate newly supplied text, tags and identifier.
    return note_url(note)


def paragraphs(body: str) -> str:
    blocks = re.split(r"\n\s*\n", body.strip())
    return "\n".join(
        "      <p>" + escape(block).replace("\n", "<br>\n") + "</p>"
        for block in blocks
    )


def timeline_webmentions(note: dict) -> str:
    canonical = BASE + note_url(note)
    return f'''    <section class="note-webmentions" data-note-target="{canonical}" aria-label="Note interactions">
      <div class="hud-meta">
        <span class="meta-pill">💬 <span class="visually-hidden">Replies: </span><span data-wm-replies>–</span></span>
        <span class="meta-pill">❤️ <span class="visually-hidden">Likes: </span><span data-wm-likes>–</span></span>
        <span class="meta-pill">🔁 <span class="visually-hidden">Reposts: </span><span data-wm-reposts>–</span></span>
      </div>
      <details>
        <summary>Replies Terminal</summary>
        <div class="comments-list" data-wm-comments aria-live="polite">
          <noscript><p>JavaScript is required to load transmissions.</p></noscript>
        </div>
        <button class="comment-button" data-wm-reload type="button">Reload Terminal</button>
      </details>
    </section>
'''


def entry(note: dict, timeline: bool = False) -> str:
    url = note_url(note)
    stamp = published(note["date"])
    machine = stamp.isoformat(timespec="seconds").replace("+00:00", "Z")
    human = stamp.strftime("%-d %B %Y, %H:%M UTC")
    tags = "".join(
        f'<a class="p-category" href="/notes/">{escape(tag)}</a> '
        for tag in note.get("tags", [])
    )
    photo = ""
    if note.get("image"):
        photo = (
            '      <figure class="notes-photo">\n'
            f'        <img class="u-photo" src="{escape(note["image"], quote=True)}" '
            f'alt="{escape(note["image_alt"], quote=True)}" loading="lazy">\n'
            '      </figure>\n'
        )
    return (
        '  <article class="h-entry">\n'
        f'    <time class="dt-published" datetime="{machine}">{human}</time>\n'
        '    <div class="e-content">\n'
        f'{paragraphs(note["content"])}\n'
        f'{photo}'
        '    </div>\n'
        f'    <p class="notes-permalink"><a class="u-url" href="{url}">Permalink</a></p>\n'
        '    <p class="notes-author"><a class="p-author h-card" href="/about.html">Schmookey</a></p>\n'
        f'    <p class="notes-tags">{tags}</p>\n' +
        (timeline_webmentions(note) if timeline else '') +
        '  </article>'
    )


def render_index(template: str, notes: list[dict]) -> str:
    if template.count(BEGIN) != 1 or template.count(END) != 1:
        raise ValueError("Notes index generation markers are missing or duplicated")
    visible = "\n".join(entry(item, timeline=True) for item in notes) if notes else (
        '    <p class="notes-empty">Nothing posted here yet. '
        'My short notes will appear here once I start publishing.</p>'
    )
    first, remainder = template.split(BEGIN, 1)
    _, last = remainder.split(END, 1)
    return first + BEGIN + "\n" + visible + "\n    " + END + last


def render_page(template: str, note: dict) -> str:
    url = note_url(note)
    canonical = BASE + url
    heading = "NOTE | SCHMOOKEY"
    intro = "Short note by Schmookey."
    for before, after in (
        ("<title>NOTES | SCHMOOKEY</title>", f"<title>{heading}</title>"),
        ('href="https://schmookey.xyz/notes/"', f'href="{canonical}"'),
        ('content="NOTES | SCHMOOKEY"', f'content="{heading}"'),
        ('content="https://schmookey.xyz/notes/"', f'content="{canonical}"'),
        ('content="website"', 'content="article"'),
        ('content="Short thoughts, observations and links from Schmookey. An independent IndieWeb notes feed."', f'content="{intro}"'),
    ):
        if before not in template:
            raise ValueError(f"Expected Notes template fragment missing: {before}")
        template = template.replace(before, after)
    main = re.compile(r'<main class="center panel notes-page h-feed">.*?</main>', re.S)
    replacement = (
        '<main class="center panel notes-page">\n'
        '  <header class="notes-heading">\n'
        '    <h1>NOTE</h1><p><a href="/notes/">All notes</a></p>\n'
        '  </header>\n'
        '  <section class="notes-stream" aria-label="Note">\n'
        f'{entry(note)}\n'
        '  </section>\n'
        f'''  <section class="comments-panel" aria-labelledby="comments">
    <h2 id="comments" class="comments-title">💬 Replies Terminal</h2>
    <div class="hud-meta" aria-label="Note interactions">
      <span class="meta-pill">💬 <span class="visually-hidden">Replies: </span><span id="wm-replies">0</span></span>
      <span class="meta-pill">❤️ <span class="visually-hidden">Likes: </span><span id="wm-likes">0</span></span>
      <span class="meta-pill">🔁 <span class="visually-hidden">Reposts: </span><span id="wm-reposts">0</span></span>
    </div>
    <p class="comment-intro">Fediverse replies, boosts, likes and other Webmentions are logged below.</p>
    <div id="comments-list" class="comments-list" aria-live="polite">
      <noscript><p class="system-msg">JavaScript is required to load transmissions.</p></noscript>
    </div>
    <div class="comment-options">
      <button class="comment-button" id="load-comments-btn" type="button">Reload Terminal</button>
    </div>
    <details class="fediverse-details">
      <summary>Reply on Fediverse</summary>
      <p>Paste this URL into your client:</p>
      <pre class="fediverse-link-box">{canonical}</pre>
    </details>
  </section>
'''
        '</main>'
    )
    page, count = main.subn(lambda _: replacement, template)
    if count != 1:
        raise ValueError("Cannot locate Notes main panel in template")
    return page


def rss_feed(notes: list[dict]) -> str:
    if not notes:
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<?xml-stylesheet type="text/xsl" href="/assets/xsl/rss.xsl"?>\n'
                '<rss version="2.0"><channel><title>Schmookey Notes</title>'
                '<link>https://schmookey.xyz/notes/</link>'
                '<description>Short thoughts and observations from Schmookey.</description>'
                '</channel></rss>\n')
    channel = ET.Element("channel")
    for name, value in (
        ("title", "Schmookey Notes"),
        ("link", BASE + "/notes/"),
        ("description", "Short thoughts and observations from Schmookey."),
    ):
        ET.SubElement(channel, name).text = value
    for note in notes:
        item = ET.SubElement(channel, "item")
        url = BASE + note_url(note)
        for name, value in (
            ("title", note["content"].splitlines()[0][:90]),
            ("link", url),
            ("guid", url),
            ("pubDate", format_datetime(published(note["date"]), usegmt=True)),
            ("description", note["content"]),
        ):
            el = ET.SubElement(item, name)
            el.text = value
            if name == "guid":
                el.set("isPermaLink", "true")
        for tag in note.get("tags", []):
            ET.SubElement(item, "category").text = tag
    root = ET.Element("rss", {"version": "2.0"})
    root.append(channel)
    ET.indent(root, space="  ")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<?xml-stylesheet type="text/xsl" href="/assets/xsl/rss.xsl"?>\n'
            + ET.tostring(root, encoding="unicode") + "\n")


def atom_feed(notes: list[dict]) -> str:
    if not notes:
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<feed xmlns="http://www.w3.org/2005/Atom"><title>Schmookey Notes</title>'
                '<id>https://schmookey.xyz/notes/</id>'
                '<link rel="alternate" href="https://schmookey.xyz/notes/"/>'
                '<updated>2026-11-17T00:00:00Z</updated></feed>\n')
    ET.register_namespace("", ATOM)
    ns = lambda name: f"{{{ATOM}}}{name}"
    feed = ET.Element(ns("feed"))
    ET.SubElement(feed, ns("title")).text = "Schmookey Notes"
    ET.SubElement(feed, ns("id")).text = BASE + "/notes/"
    ET.SubElement(feed, ns("link"), {"rel": "alternate", "href": BASE + "/notes/"})
    ET.SubElement(feed, ns("link"), {"rel": "self", "href": BASE + "/notes/atom.xml"})
    ET.SubElement(feed, ns("updated")).text = (
        published(notes[0]["date"]).isoformat(timespec="seconds").replace("+00:00", "Z")
        if notes else "2026-11-17T00:00:00Z"
    )
    author = ET.SubElement(feed, ns("author"))
    ET.SubElement(author, ns("name")).text = "Schmookey"
    for note in notes:
        entry_node = ET.SubElement(feed, ns("entry"))
        url = BASE + note_url(note)
        for name, value in (
            ("id", url),
            ("title", note["content"].splitlines()[0][:90]),
            ("updated", published(note["date"]).isoformat(timespec="seconds").replace("+00:00", "Z")),
            ("published", published(note["date"]).isoformat(timespec="seconds").replace("+00:00", "Z")),
        ):
            ET.SubElement(entry_node, ns(name)).text = value
        ET.SubElement(entry_node, ns("link"), {"rel": "alternate", "href": url})
        ET.SubElement(entry_node, ns("content"), {"type": "text"}).text = note["content"]
        for tag in note.get("tags", []):
            ET.SubElement(entry_node, ns("category"), {"term": tag})
    ET.indent(feed, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(feed, encoding="unicode") + "\n"


def outputs(root: Path) -> dict[Path, str]:
    notes = read_notes(root)
    index_template = (root / INDEX).read_text(encoding="utf-8")
    results = {
        INDEX: render_index(index_template, notes),
        Path("notes/feed.xml"): rss_feed(notes),
        Path("notes/atom.xml"): atom_feed(notes),
    }
    for note in notes:
        results[Path(note_url(note).lstrip("/"))] = render_page(index_template, note)
    return results


def generate(root: Path, check: bool = False) -> None:
    changes = []
    for path, content in outputs(root).items():
        destination = root / path
        current = destination.read_text(encoding="utf-8") if destination.exists() else None
        if current != content:
            changes.append(str(path))
            if not check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
    if check and changes:
        raise SystemExit("Generated Notes files are out of date: " + ", ".join(changes))
    print(("Checked" if check else "Generated") + f" Notes ({len(read_notes(root))} published).")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        if args.check:
            parser.error("--publish cannot be used with --check")
        url = add_note(ROOT, os.environ.get("NOTE_CONTENT", ""),
                       os.environ.get("NOTE_TAGS", ""), os.environ.get("GITHUB_RUN_ID", ""),
                       os.environ.get("NOTE_IMAGE", ""), os.environ.get("NOTE_IMAGE_ALT", ""),
                       os.environ.get("NOTE_SYNDICATE", "none"))
        print("Prepared " + BASE + url)
    generate(ROOT, check=args.check)


if __name__ == "__main__":
    main()
