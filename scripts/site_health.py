#!/usr/bin/env python3
"""Read-only HTTP link checks on the trusted main branch; no credentials."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin, urldefrag
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree
import ipaddress
import socket

BASE = "https://schmookey.xyz/"
ROOT = Path(__file__).resolve().parents[1]

def public_url(url):
    p = urlsplit(url)
    if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password or p.port not in (None, 80, 443):
        raise ValueError("Unsupported URL")
    addresses = socket.getaddrinfo(p.hostname, None, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Non-public destination")
    return url

class Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        if urlsplit(req.full_url).hostname == "schmookey.xyz":
            if urlsplit(newurl).hostname != "schmookey.xyz" or urlsplit(newurl).scheme != "https":
                raise ValueError("Unexpected site redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = {"a": "href", "img": "src", "script": "src", "iframe": "src", "link": "href"}.get(tag)
        if not key:
            return
        value = attrs.get(key, "")
        if value and value.startswith(("https://", "http://")):
            if tag == "link" and attrs.get("rel") in ("webmention", "pingback"):
                return
            self.urls.add(urldefrag(value)[0])

def targets():
    pages = {n.text for n in ElementTree.parse(ROOT / "sitemap.xml").findall(".//{*}loc") if n.text}
    external = set()
    for path in sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("blog/**/*.html")) + sorted(ROOT.glob("music/**/*.html")) + sorted(ROOT.glob("notes/**/*.html")) + sorted(ROOT.glob("random/**/*.html")):
        if "template" in path.name.lower() or path.name == "test-mention.html":
            continue
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        external.update(u for u in parser.urls if urlsplit(u).hostname != "schmookey.xyz")
    return sorted(pages | {BASE + p for p in ("feed.xml", "atom.xml", "feed.json", "sitemap.xml", "notes/feed.xml", "robots.txt")}), sorted(external)

def check(url, internal):
    try:
        public_url(url)
        opener = build_opener(ProxyHandler({}), Redirect())
        req = Request(url, headers={"User-Agent": "SchmookeySiteHealth/1.0", "Accept": "*/*"})
        with opener.open(req, timeout=12) as response:
            if internal:
                expected = {url, url.removesuffix(".html")} if url.endswith(".html") else {url}
                if response.geturl() not in expected or response.status != 200:
                    return "FAIL", url, "unexpected destination/status"
                if url.endswith((".html", "/")) and response.headers.get_content_type() != "text/html":
                    return "FAIL", url, "not HTML"
            return "OK", url, str(response.status)
    except HTTPError as exc:
        if not internal and exc.code not in (404, 410):
            return "REVIEW", url, f"HTTP {exc.code}"
        return "FAIL", url, f"HTTP {exc.code}"
    except (URLError, OSError, ValueError) as exc:
        return ("FAIL" if internal else "REVIEW"), url, type(exc).__name__

def main():
    pages, external = targets()
    if len(pages) + len(external) > 500:
        raise SystemExit("Link limit exceeded; review scope")
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda item: check(*item), [(u, True) for u in pages] + [(u, False) for u in external]))
    for status, url, detail in results:
        print(f"{status}: {url} ({detail})")
    failures = sum(s == "FAIL" for s, _, _ in results)
    reviews = sum(s == "REVIEW" for s, _, _ in results)
    print(f"Checked {len(results)} URLs; failures: {failures}; external review: {reviews}")
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
