#!/usr/bin/env python3
"""Static website checks for GitHub Actions and local development.

Requires: lxml, tinycss2, Pillow (installed by the site-checks workflow).
Does not contact external services or execute site JavaScript.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote
import io
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET

from lxml import html
from PIL import Image
import tinycss2

# Older libxml2 versions report standard HTML5 elements as unknown.
# Do not suppress warnings for unrecognised/non-HTML5 tag names.
HTML5_ELEMENTS = frozenset({
    "article", "aside", "audio", "bdi", "canvas", "data", "datalist",
    "details", "dialog", "figcaption", "figure", "footer", "header",
    "main", "mark", "meter", "nav", "output", "picture", "progress",
    "rp", "rt", "ruby", "section", "source", "summary", "template",
    "time", "track", "video", "wbr",
})

ROOT = Path(__file__).resolve().parent.parent
FILES = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob("*") if p.is_file()}
ERRORS: list[str] = []


def error(msg: str) -> None:
    ERRORS.append(msg)


def internal_target(page: str, address: str) -> str | None:
    value = address.strip()
    if not value or value.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if host and host not in {"schmookey.xyz", "www.schmookey.xyz"}:
        return None
    if (parsed.scheme in ("http", "https") and not host) or (parsed.netloc and not host):
        return None
    # Protocol-relative remote URLs are ignored; local URLs must be absolute-root or relative.
    if value.startswith("//"):
        return None

    raw = unquote(parsed.path) or "/"
    if raw.startswith("/"):
        path = raw.lstrip("/")
    else:
        path = posixpath.join(posixpath.dirname(page), raw)
    path = posixpath.normpath(path)
    if path in {".", ""}:
        return "index.html"
    if path.startswith("../"):
        error(f"{page}: link goes above site root: {address}")
        return None
    if raw.endswith("/") or path not in FILES and not Path(path).suffix:
        path = posixpath.join(path, "index.html")
    return path


def check_html() -> int:
    count = 0
    for page, file in sorted(FILES.items()):
        if not page.endswith(".html"):
            continue
        count += 1
        contents = file.read_text(encoding="utf-8-sig")
        parser = html.HTMLParser(recover=True)
        doc = html.document_fromstring(contents, parser=parser)
        for item in parser.error_log:
            if item.level_name not in {"ERROR", "FATAL"}:
                continue
            if item.type_name == "HTML_UNKNOWN_TAG":
                match = re.fullmatch(r"Tag ([A-Za-z][A-Za-z0-9-]*) invalid", item.message)
                if match and match.group(1).lower() in HTML5_ELEMENTS:
                    continue
            error(f"{page}: HTML parser: {item}")

        ids = [node.get("id") for node in doc.xpath("//*[@id]")]
        duplicates = [id_value for id_value, found in Counter(ids).items() if found > 1]
        for id_value in duplicates:
            error(f"{page}: duplicate id: {id_value}")
        for image in doc.xpath("//img"):
            if image.get("alt") is None:
                error(f"{page}: image missing alt: {image.get('src', '(no src)')}")
        for node in doc.iter():
            for attr in ("href", "src", "poster"):
                link = node.get(attr)
                if not link:
                    continue
                target = internal_target(page, link)
                if target and target not in FILES:
                    error(f"{page}: missing {target} referenced by {node.tag}[{attr}]")
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        if canonical and internal_target(page, canonical[0]) != page:
            if not (page == "index.html" and canonical[0] == "https://schmookey.xyz"):
                error(f"{page}: canonical URL doesn't resolve to itself: {canonical[0]}")
    return count


def check_data() -> tuple[int, int]:
    json_count = xml_count = 0
    for path, file in sorted(FILES.items()):
        if path.endswith((".json", ".webmanifest")):
            json_count += 1
            try:
                obj = json.loads(file.read_text(encoding="utf-8-sig"))
                if path == "assets/data/posts.json":
                    if not isinstance(obj, list):
                        error(f"{path}: posts data must be a list")
                    else:
                        for post in obj:
                            link = post.get("url", "")
                            if not re.fullmatch(r"/(?:blog|music)/posts/[a-zA-Z0-9_-]+\.html", str(link)):
                                error(f"{path}: unsafe or unexpected article URL: {link}")
                            elif link.lstrip("/") not in FILES:
                                error(f"{path}: article not found: {link}")
            except (ValueError, OSError) as exc:
                error(f"{path}: JSON invalid: {exc}")
        if path.endswith(".xml"):
            xml_count += 1
            try:
                ET.parse(file)
            except ET.ParseError as exc:
                error(f"{path}: XML invalid: {exc}")
    return json_count, xml_count


def check_css_and_images() -> tuple[int, int]:
    css_count = images = 0
    for path, file in sorted(FILES.items()):
        suffix = file.suffix.lower()
        if suffix == ".css":
            css_count += 1
            for token in tinycss2.parse_stylesheet(file.read_text(encoding="utf-8")):
                if token.type == "error":
                    error(f"{path}: CSS parse error: {token.message}")
        if suffix in {".gif", ".png", ".jpg", ".jpeg", ".ico", ".webp"}:
            images += 1
            try:
                with Image.open(io.BytesIO(file.read_bytes())) as image:
                    image.verify()
            except (OSError, ValueError) as exc:
                error(f"{path}: invalid image: {exc}")
    return css_count, images


def check_metadata() -> None:
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    doc = html.fromstring(home)
    if not doc.xpath('//body//*[@hidden][contains(concat(" ",normalize-space(@class)," ")," u-url ")]'):
        error("index.html: deliberately hidden IndieWeb u-url is missing")
    if not doc.xpath('//body//*[contains(concat(" ",normalize-space(@class)," ")," h-card ")]'):
        error("index.html: IndieWeb h-card is missing from body")
    if not doc.xpath('//link[@rel="webmention"]'):
        error("index.html: webmention endpoint discovery missing")
    if "schmookey.neocities" in "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in FILES.values()
        if p.suffix.lower() in {".html", ".js", ".css", ".json", ".xml", ".txt", ".webmanifest", ".md"}
    ).lower():
        error("Legacy Schmookey Neocities domain still appears in site content")
    if "guestbook.html" in FILES:
        error("guestbook.html must not be present in the release")


def main() -> int:
    html_pages = check_html()
    json_count, xml_count = check_data()
    css_count, image_count = check_css_and_images()
    check_metadata()
    print(f"Checked {html_pages} HTML pages, {json_count} JSON/manifest files, "
          f"{xml_count} XML files, {css_count} stylesheets, and {image_count} images")
    if ERRORS:
        print(f"FAILED: {len(ERRORS)} errors")
        for issue in ERRORS:
            print(f" - {issue}")
        return 1
    print("PASS: all static checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
