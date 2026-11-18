#!/usr/bin/env python3
"""Deterministically update RSS/Atom/JSON feeds and static blog/music cards.

Author new posts and their metadata in assets/data/posts.json. Author Now,
privacy and changelog announcements in assets/data/site-updates.json.
Existing feed summaries and authored card assets/blurbs are preserved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://schmookey.xyz"
ATOM_NS = "http://www.w3.org/2005/Atom"
FEEDS = ("feed.json", "feed.xml", "atom.xml")
INDEXES = {"blog": "blog/index.html", "music": "music/index.html"}
POST_RE = re.compile(r"^/(blog|music)/posts/[A-Za-z0-9_-]+\.html$")
UPDATE_URLS = {"/now.html", "/privacy.html", "/changelog.html"}
FIRST_SENTENCE = re.compile(r"(?<=[.!?])(?:\s+|$)")
FEED_MAIN = re.compile(r'(<main class="center panel h-feed">)([\s\S]*?)(</main>)')


def timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Date needs an explicit timezone: {value}")
    return dt.astimezone(timezone.utc)


def iso(value: str) -> str:
    return timestamp(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def slug(text: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", text.lower()))


def load(root: Path, relative: str):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def get_post(root: Path, item: dict):
    path = item["url"]
    match = POST_RE.fullmatch(path)
    if not match or match.group(1) != item["section"]:
        raise ValueError(f"Invalid or mismatched post URL: {path}")
    file = root / path.lstrip("/")
    if not file.is_file():
        raise ValueError(f"Missing post file: {path}")
    return html.document_fromstring(file.read_text(encoding="utf-8-sig"))


def first_sentence(doc) -> str:
    regions = doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," e-content ")]')
    if not regions:
        raise ValueError("Post has no e-content")
    region = regions[0]
    for node in region.xpath('.//p|.//div'):
        if node.xpath('ancestor::figure|ancestor::blockquote|ancestor::nav|ancestor::*[@hidden]'):
            continue
        text = " ".join(" ".join(node.itertext()).split())
        if text:
            # Avoid treating a short teaser or image caption as an article blurb.
            return FIRST_SENTENCE.split(text, maxsplit=1)[0].strip()
    text = " ".join(" ".join(region.itertext()).split())
    if not text:
        raise ValueError("Post body is empty")
    return FIRST_SENTENCE.split(text, maxsplit=1)[0].strip()


def image_data(doc, item: dict, root: Path) -> tuple[str, str]:
    src = item.get("cardImage")
    alt = item.get("cardImageAlt")
    if not src:
        images = doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," e-content ")]//figure//img')
        if images:
            src = images[0].get("src")
            alt = alt or images[0].get("alt")
        else:
            src = (doc.xpath('//meta[@property="og:image"]/@content') or [None])[0]
    if not src:
        raise ValueError(f"No card image available: {item['url']}")
    if src.startswith(BASE + "/"):
        src = src[len(BASE):]
    elif not src.startswith("/"):
        src = "/" + str((Path(item["url"].lstrip("/")).parent / src)).replace("\\", "/")
        # Canonicalise ../ segments and refuse traversal beyond the site.
        import posixpath
        src = posixpath.normpath(src)
    if not src.startswith("/") or src.startswith("//") or not (root / src.lstrip("/")).is_file():
        raise ValueError(f"Card image not in repository: {src}")
    return src, alt or item["title"]


def content_items(root: Path):
    posts = load(root, "assets/data/posts.json")
    updates = load(root, "assets/data/site-updates.json")
    if not isinstance(posts, list) or not isinstance(updates, list):
        raise ValueError("Source metadata must be a list")
    records = []
    for post in posts:
        doc = get_post(root, post)
        records.append((post, doc))
    for update in updates:
        if update["url"] not in UPDATE_URLS:
            raise ValueError(f"Unexpected site update URL: {update['url']}")
        if not (root / update["url"].lstrip("/")).is_file():
            raise ValueError(f"Missing site update page: {update['url']}")
        timestamp(update["date"])
    return records, updates


def build_feeds(root: Path, records, updates) -> dict[str, str]:
    old = load(root, "feed.json")
    previous = {item["id"]: item for item in old["items"]}
    items = []
    for post, doc in records:
        ident = "urn:schmookey:post:" + Path(post["url"]).stem
        desc = previous.get(ident, {}).get("content_text")
        if not desc:
            desc = (doc.xpath('//meta[@name="description"]/@content') or [None])[0]
        desc = desc or first_sentence(doc)
        items.append({"id": ident, "url": BASE + post["url"], "title": post["title"],
                      "content_text": desc, "date_published": iso(post["date"])})
    for update in updates:
        ident = f"urn:schmookey:update:{slug(update['title'])}:{update['date']}"
        items.append({"id": ident, "url": BASE + update["url"], "title": update["title"],
                      "content_text": update["summary"], "date_published": iso(update["date"])})
    # Keep historical entries that have been removed from the two source lists.
    ids = {item["id"] for item in items}
    items.extend(item for item in old["items"] if item["id"] not in ids)
    if not items or len(set(x["id"] for x in items)) != len(items):
        raise ValueError("Feed is empty or contains duplicate IDs")
    items.sort(key=lambda item: timestamp(item["date_published"]), reverse=True)
    old["items"] = items
    result = {"feed.json": json.dumps(old, ensure_ascii=False, indent=2) + "\n"}

    rss = ET.fromstring((root / "feed.xml").read_text(encoding="utf-8"))
    channel = rss.find("channel")
    if channel is None:
        raise ValueError("RSS channel missing")
    build = channel.find("lastBuildDate")
    if build is None:
        raise ValueError("RSS lastBuildDate missing")
    build.text = format_datetime(timestamp(items[0]["date_published"]), usegmt=True)
    for entry in channel.findall("item"):
        channel.remove(entry)
    for item in items:
        node = ET.SubElement(channel, "item")
        for tag, value in [
            ("title", item["title"]), ("link", item["url"]), ("guid", item["id"]),
            ("pubDate", format_datetime(timestamp(item["date_published"]), usegmt=True)),
            ("description", item["content_text"]),
        ]:
            ET.SubElement(node, tag, {"isPermaLink": "false"} if tag == "guid" else {}).text = value

    atom = ET.fromstring((root / "atom.xml").read_text(encoding="utf-8"))
    tag = lambda key: f"{{{ATOM_NS}}}{key}"
    updated = atom.find(tag("updated"))
    if updated is None:
        raise ValueError("Atom updated timestamp missing")
    updated.text = items[0]["date_published"]
    for entry in atom.findall(tag("entry")):
        atom.remove(entry)
    for item in items:
        node = ET.SubElement(atom, tag("entry"))
        ET.SubElement(node, tag("title")).text = item["title"]
        ET.SubElement(node, tag("link"), {"href": item["url"], "rel": "alternate"})
        ET.SubElement(node, tag("id")).text = item["id"]
        ET.SubElement(node, tag("updated")).text = item["date_published"]
        ET.SubElement(node, tag("published")).text = item["date_published"]
        ET.SubElement(node, tag("summary")).text = item["content_text"]
    for name, tree in [("feed.xml", rss), ("atom.xml", atom)]:
        ET.indent(tree, space="  ")
        header = "<?xml version='1.0' encoding='utf-8'?>\n"
        if name == "feed.xml":
            header += '<?xml-stylesheet type="text/xsl" href="/assets/xsl/rss.xsl"?>\n'
        result[name] = header + ET.tostring(tree, encoding="unicode")
    return result


def make_card(root: Path, post: dict, doc) -> str:
    url = post["url"]
    img, alt = image_data(doc, post, root)
    title = post.get("cardTitle") or post["title"]
    blurb = post.get("cardBlurb") or first_sentence(doc)
    dt = timestamp(post["date"])
    date_label = dt.strftime("%d %B %Y")
    link = escape(url, quote=True)
    return (
        '  <article class="h-entry post-card">\n'
        f'    <a class="p-author h-card" href="{BASE}/" hidden></a>\n'
        f'    <a class="post-image u-url" href="{link}">\n'
        f'      <img class="u-photo" src="{escape(img, quote=True)}" alt="{escape(alt, quote=True)}" loading="lazy">\n'
        '    </a>\n'
        '    <div class="post-content">\n'
        f'      <h2 class="p-name"><a href="{link}">{escape(title)}</a></h2>\n'
        f'      <time class="dt-published" datetime="{escape(post["date"], quote=True)}">{date_label}</time>\n'
        f'      <p class="p-summary">{escape(blurb)}</p>\n'
        f'      <a class="read-more" href="{link}">Read More →</a>\n'
        '    </div>\n'
        f'    <a class="post-card-area-link" href="{link}" aria-hidden="true" tabindex="-1"></a>\n'
        '  </article>\n'
    )


def build_cards(root: Path, records) -> dict[str, str]:
    output = {}
    for section, rel in INDEXES.items():
        listing = [(p, doc) for p, doc in records if p["section"] == section]
        listing.sort(key=lambda item: timestamp(item[0]["date"]), reverse=True)
        content = (root / rel).read_text(encoding="utf-8")
        matches = list(FEED_MAIN.finditer(content))
        if len(matches) != 1:
            raise ValueError(f"Could not locate the one listing region: {rel}")
        output[rel] = FEED_MAIN.sub(
            lambda match: match.group(1) + "\n" +
            "".join(make_card(root, p, doc) for p, doc in listing) + match.group(3),
            content, count=1)
    return output



# Public static pages that should be indexed. Templates, 404 pages and
# test endpoints are intentionally excluded from search engine sitemaps.
SITEMAP_PAGES = (
    ("/", "index.html"),
    ("/about.html", "about.html"),
    ("/now.html", "now.html"),
    ("/listening.html", "listening.html"),
    ("/now-watching.html", "now-watching.html"),
    ("/blog/", "blog/index.html"),
    ("/music/", "music/index.html"),
    ("/random/", "random/index.html"),
    ("/notes/", "notes/index.html"),
    ("/blog-archive.html", "blog-archive.html"),
    ("/music-archive.html", "music-archive.html"),
    ("/webrings.html", "webrings.html"),
    ("/changelog.html", "changelog.html"),
    ("/privacy.html", "privacy.html"),
)


def build_sitemap(root: Path, records, updates) -> str:
    """Sitemap entries from published pages only, with meaningful lastmod dates.

    Do not manufacture a 'last modified today' date for every file on each
    generation. Blog entries use publication or optional modification dates;
    Now, privacy and changelog use their latest site-updates.json entries.
    """
    modified = {}
    for section in INDEXES:
        dates = [timestamp(post.get("updated") or post["date"]) for post, _ in records
                 if post["section"] == section]
        if dates:
            modified[f"/{section}/"] = max(dates).date().isoformat()
    for update in updates:
        link = update["url"]
        latest = timestamp(update["date"]).date().isoformat()
        if latest > modified.get(link, ""):
            modified[link] = latest

    paths = []
    for url, local_file in SITEMAP_PAGES:
        if not (root / local_file).is_file():
            raise ValueError(f"Public sitemap page is missing: {local_file}")
        paths.append((url, modified.get(url)))
    for post, _ in sorted(records, key=lambda pair: timestamp(pair[0]["date"]), reverse=True):
        lastmod = timestamp(post.get("updated") or post["date"]).date().isoformat()
        paths.append((post["url"], lastmod))
    # The independent Notes generator owns the individual note pages and feeds.
    # Include verified generated Notes URLs whenever the main sitemap is rebuilt.
    notes = load(root, "assets/data/notes.json")
    if not isinstance(notes, list):
        raise ValueError("Notes source must be a JSON list")
    seen_notes = set()
    for note in notes:
        note_id = note.get("id") if isinstance(note, dict) else None
        if not isinstance(note_id, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}-\d{6}-\d+", note_id):
            raise ValueError("Invalid note ID in sitemap source")
        if note_id in seen_notes:
            raise ValueError("Duplicate note ID in sitemap source")
        seen_notes.add(note_id)
        local_file = root / "notes" / f"{note_id}.html"
        if not local_file.is_file():
            raise ValueError(f"Missing generated note page: {local_file}")
        paths.append((f"/notes/{note_id}.html", timestamp(note["date"]).date().isoformat()))
    if len({url for url, _ in paths}) != len(paths):
        raise ValueError("Duplicate sitemap URLs")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<?xml-stylesheet type="text/xsl" href="/assets/xsl/sitemap.xsl"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod in paths:
        lines.extend(['  <url>', f'    <loc>{escape(BASE + url)}</loc>'])
        if lastmod is not None:
            lines.append(f'    <lastmod>{lastmod}</lastmod>')
        lines.append('  </url>')
    lines.append('</urlset>')
    return "\n".join(lines) + "\n"



def build_search_index(root: Path, records, updates) -> str:
    """Create an offline, same-origin index of published blog and music articles.

    Uses the already-curated post list rather than scanning drafts, archives,
    source code or private assets. Preserves original content spelling.
    """
    def normalise(text: str) -> str:
        return " ".join(str(text).split())

    def visible_text(node) -> str:
        # Avoid HTML scripts, hidden IndieWeb metadata and duplicated navigation.
        for unwanted in node.xpath(
            './/script|.//style|.//noscript|.//nav|.//aside|.//*[@hidden]|'
            './/*[contains(concat(" ",normalize-space(@class)," ")," post-tags ")]'
        ):
            unwanted.drop_tree()
        return normalise(node.text_content())[:15000]

    items = []
    for post, doc in records:
        url = post["url"]
        sections = doc.xpath(
            '//*[contains(concat(" ",normalize-space(@class)," ")," e-content ")]'
        )
        if not sections:
            raise ValueError(f"Missing searchable post body: {url}")
        # Copy the element so that removing invisible children cannot modify
        # the original parsed article used by the publishing generator.
        from copy import deepcopy
        body = visible_text(deepcopy(sections[0]))
        summary = post.get("cardBlurb") or first_sentence(doc)
        items.append({
            "url": url, "title": post["title"], "section": post["section"],
            "summary": normalise(summary), "date": iso(post["date"]),
            "tags": post.get("tags", []), "text": body,
        })

    if len({item["url"] for item in items}) != len(items):
        raise ValueError("Search-index URLs must be unique")
    return json.dumps({
        "version": 1, "items": items,
    }, ensure_ascii=False, indent=2) + "\n"



# Sidebar links are stored in article HTML as a resilient static baseline.
# No JavaScript or data fetch is required to see the four independent boxes.
ARTICLE_SIDEBAR_MARKERS = (
    ("<!-- BEGIN GENERATED RELATED POSTS -->", "<!-- END GENERATED RELATED POSTS -->"),
    ("<!-- BEGIN GENERATED MORE POSTS -->", "<!-- END GENERATED MORE POSTS -->"),
)
GENERIC_RECOMMENDATION_TAGS = {"blog", "music", "update", "updates"}


def article_recommendations(current: dict, posts: list[dict]) -> tuple[list, list]:
    """Related may cross blog/music on real shared tags; More is recent blog."""
    def tags(post: dict) -> set[str]:
        return {str(tag).casefold() for tag in post.get("tags", [])} - GENERIC_RECOMMENDATION_TAGS

    others = [post for post in posts if post["url"] != current["url"]]
    current_tags = tags(current)
    ranked = [(post, current_tags & tags(post)) for post in others]
    ranked.sort(key=lambda pair: (
        len(pair[1]),
        pair[0]["section"] == current["section"],
        timestamp(pair[0]["date"]),
    ), reverse=True)
    related = [(post, common) for post, common in ranked if common][:3]
    recent_blog = sorted((post for post in others if post["section"] == "blog"),
                         key=lambda post: timestamp(post["date"]), reverse=True)
    for post in recent_blog:
        if len(related) >= 3:
            break
        if all(existing["url"] != post["url"] for existing, _ in related):
            related.append((post, set()))

    related_urls = {post["url"] for post, _ in related}
    more = [post for post in recent_blog if post["url"] not in related_urls][:4]
    return related, more


def build_article_sidebars(root: Path, records) -> dict[str, str]:
    """Fill the existing separated sidebar boxes; preserve all other post HTML."""
    posts = [post for post, _ in records]

    def item_html(post: dict, label: str) -> str:
        name = post.get("cardTitle") or post["title"]
        return ("        <li><a href=\"%s\">%s</a><small>%s</small></li>" %
                (escape(post["url"], quote=True), escape(name), escape(label)))

    output = {}
    for current in posts:
        related, more = article_recommendations(current, posts)
        related_html = "\n".join(item_html(post,
            " · ".join(sorted(common)[:2]) if common else post["section"].upper())
            for post, common in related)
        more_html = "\n".join(item_html(post, "BLOG") for post in more)

        relative = current["url"].lstrip("/")
        content = (root / relative).read_text(encoding="utf-8-sig")
        for (begin, end), body in zip(ARTICLE_SIDEBAR_MARKERS, (related_html, more_html)):
            pattern = re.compile(re.escape(begin) + r"[\s\S]*?" + re.escape(end))
            matches = list(pattern.finditer(content))
            if len(matches) != 1:
                raise ValueError(f"Expected one generated sidebar region in {relative}: {begin}")
            content = pattern.sub(lambda _m: begin + "\n" + body + "\n        " + end,
                                  content, count=1)
        output[relative] = content
    return output



def run(root: Path, check: bool) -> int:
    records, updates = content_items(root)
    outputs = {**build_feeds(root, records, updates), **build_cards(root, records),
               "sitemap.xml": build_sitemap(root, records, updates),
               "assets/data/search-index.json": build_search_index(root, records, updates),
               **build_article_sidebars(root, records)}
    changes = [rel for rel, value in outputs.items()
               if (root / rel).read_text(encoding="utf-8") != value]
    if not check:
        for rel in changes:
            (root / rel).write_text(outputs[rel], encoding="utf-8")
    print(("Stale: " if check else "Generated: ") + (", ".join(changes) if changes else "nothing to update"))
    return 1 if check and changes else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        sys.exit(run(ROOT, args.check))
    except (ValueError, KeyError, OSError, ET.ParseError) as exc:
        raise SystemExit(f"Content build failed: {exc}") from None
