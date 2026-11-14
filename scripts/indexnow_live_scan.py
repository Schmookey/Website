#!/usr/bin/env python3
"""Notify IndexNow only when PUBLIC pages on schmookey.xyz change.

The site is manually deployed, so GitHub commits do not prove that a page is
live. Poll the published sitemap and published HTML instead, and store only
SHA-256 fingerprints in the GitHub Actions cache. Never upload site files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

HOST = "schmookey.xyz"
SITEMAP = f"https://{HOST}/sitemap.xml"
INDEXNOW = "https://api.indexnow.org/indexnow"
MAX_URLS = 1000
MAX_HTML_BYTES = 6_000_000
KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,128}$")
DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")


def on_site(url: str) -> bool:
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.netloc == HOST
            and not parts.query and not parts.fragment and
            (parts.path.endswith(".html") or parts.path.endswith("/")))


def urls_in_sitemap(body: bytes) -> list[str]:
    root = ElementTree.fromstring(body)
    urls: list[str] = []
    for loc in root.findall(".//{*}url/{*}loc"):
        value = (loc.text or "").strip()
        if on_site(value) and value not in urls:
            urls.append(value)
            if len(urls) > MAX_URLS:
                raise ValueError("Sitemap lists too many eligible URLs")
    if not urls:
        raise ValueError("No eligible URLs found in the live sitemap")
    return urls


class RobotsMetadata(HTMLParser):
    """Read robot directives in the document head only."""
    def __init__(self) -> None:
        super().__init__()
        self.in_head = False
        self.noindex = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "head":
            self.in_head = True
        elif self.in_head and tag == "meta":
            fields = dict(attrs)
            if (fields.get("name") or "").lower() in ("robots", "bingbot"):
                directives = re.split(r"[,;\s]+", (fields.get("content") or "").lower())
                if "noindex" in directives or "none" in directives:
                    self.noindex = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self.in_head = False


def fetch(url: str, expect: str) -> bytes | None:
    request = Request(url, headers={"User-Agent": "SchmookeyIndexNow/1.0"})
    with urlopen(request, timeout=20) as response:
        actual = response.geturl()
        if actual != url and not on_site(actual):
            raise ValueError("Refusing a redirect outside the verified domain")
        if response.status != 200:
            raise ValueError(f"Non-200 response: {response.status}")
        mime = response.headers.get_content_type()
        if expect == "sitemap":
            if mime not in ("application/xml", "text/xml", "application/octet-stream"):
                raise ValueError("Unexpected sitemap content type")
            limit = 1_000_000
        else:
            if mime not in ("text/html", "application/xhtml+xml"):
                raise ValueError("Not an HTML page")
            if "noindex" in response.headers.get("X-Robots-Tag", "").lower():
                return None
            limit = MAX_HTML_BYTES
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError("Page exceeds size limit")
        if expect == "html":
            parser = RobotsMetadata()
            parser.feed(body.decode("utf-8", errors="replace"))
            if parser.noindex:
                return None
        return body


def read_state(path: Path) -> tuple[dict[str, str], bool]:
    if not path.exists():
        return {}, False
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("Unrecognised IndexNow state; refusing to lose history")
    hashes = raw.get("hashes")
    if not isinstance(hashes, dict) or any(
        not on_site(url) or not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest)
        for url, digest in hashes.items()
    ):
        raise ValueError("Invalid saved IndexNow fingerprints")
    return hashes, True


def write_state(path: Path, hashes: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps({"version": 1, "hashes": hashes}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def submit(urls: list[str], key: str) -> int:
    if not urls:
        return 0
    if not KEY_RE.fullmatch(key):
        raise ValueError("Invalid or missing IndexNow key")
    if len(urls) > MAX_URLS or any(not on_site(url) for url in urls):
        raise ValueError("Unsafe IndexNow submission URL")
    payload = json.dumps({"host": HOST, "key": key, "urlList": urls}).encode("utf-8")
    request = Request(INDEXNOW, data=payload, method="POST", headers={
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "SchmookeyIndexNow/1.0",
    })
    with urlopen(request, timeout=30) as response:
        status = response.status
    if status not in (200, 202):
        raise ValueError(f"IndexNow returned HTTP {status}")
    return status


def scan(state_file: Path, key: str, force_all: bool = False) -> dict[str, int]:
    previous, has_baseline = read_state(state_file)
    sitemap = fetch(SITEMAP, "sitemap")
    if sitemap is None:
        raise ValueError("Live sitemap unavailable")
    urls = urls_in_sitemap(sitemap)
    observed = previous.copy()
    changed: list[str] = []
    failures = 0
    for url in urls:
        try:
            body = fetch(url, "html")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            failures += 1
            print(f"SKIP {url}: {type(exc).__name__}")
            continue
        if body is None:
            print(f"SKIP {url}: noindex")
            continue
        digest = hashlib.sha256(body).hexdigest()
        if force_all or (has_baseline and previous.get(url) != digest):
            changed.append(url)
        observed[url] = digest

    if not any(url in observed and (force_all or url in previous or not has_baseline)
               for url in urls) and failures:
        raise RuntimeError("All live page checks failed; no IndexNow state saved")

    if not has_baseline and not force_all:
        print("Initial scan: storing a baseline; no unchanged pages will be submitted.")
    elif changed:
        status = submit(changed, key)
        print(f"IndexNow accepted {len(changed)} published URL(s): HTTP {status}")
    else:
        print("No new or changed published pages to notify.")

    # Save only after submission succeeded, so failures are retried next run.
    write_state(state_file, observed)
    return {"checked": len(urls), "submitted": len(changed), "failed": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--force-all", action="store_true",
                        help="Explicitly resubmit all verified public sitemap pages")
    args = parser.parse_args()
    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not KEY_RE.fullmatch(key):
        raise SystemExit("INDEXNOW_KEY must contain 8-128 letters, numbers or dashes.")
    result = scan(args.state, key, args.force_all)
    print(f"Live URLs checked: {result['checked']}; notified: {result['submitted']}; "
          f"fetch failures: {result['failed']}.")


if __name__ == "__main__":
    main()
