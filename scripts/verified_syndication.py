#!/usr/bin/env python3
"""Fail-closed, offline-testable live verification and social syndication.

External posting is impossible without SOCIAL_SYNDICATION_ENABLED=true and
account credentials. Pending posts stay blocked on failure to avoid duplicates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib import error, parse, request

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://schmookey.xyz"
LEDGER = Path("social/syndication-state.json")
START_DATE = datetime.fromisoformat("2026-11-18T15:45:00+00:00")
BLOG = re.compile(r"^/blog/posts/[A-Za-z0-9_-]+\.html$")
NOTE = re.compile(r"^/notes/\d{4}-\d{2}-\d{2}-\d{6}-\d+\.html$")
PLATFORMS = {
    "none": (), "mastodon": ("mastodon",),
    "bluesky": ("bluesky",), "both": ("mastodon", "bluesky"),
}


class PublicationError(Exception):
    """Operator-safe error; never includes API secrets or response bodies."""


def json_from(file: Path):
    return json.loads(file.read_text(encoding="utf-8"))


def candidates(root: Path):
    """Only new Blog posts and explicitly opted-in Notes; never old posts."""
    for post in json_from(root / "assets/data/posts.json"):
        if post.get("section") != "blog":
            continue
        path = post["url"]
        if not BLOG.fullmatch(path):
            raise PublicationError("Invalid Blog permalink")
        dt = datetime.fromisoformat(post["date"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise PublicationError("Blog date requires timezone")
        if dt <= START_DATE or post.get("syndicate") is False:
            continue
        yield {"path": path, "title": post["title"], "platforms": PLATFORMS["both"]}
    for note in json_from(root / "assets/data/notes.json"):
        mode = note.get("syndicate", "none")
        if mode not in PLATFORMS:
            raise PublicationError("Invalid Note syndication choice")
        if mode == "none":
            continue
        path = f"/notes/{note['id']}.html"
        if not NOTE.fullmatch(path):
            raise PublicationError("Invalid Note permalink")
        yield {"path": path, "title": note["content"], "platforms": PLATFORMS[mode]}


def local_sample(root: Path, target: dict) -> str:
    path = target["path"]
    if not (BLOG.fullmatch(path) or NOTE.fullmatch(path)):
        raise PublicationError("Unsupported publication path")
    file = root / path.lstrip("/")
    if not file.is_file() or file.is_symlink():
        raise PublicationError("Local published page is missing")
    doc = html.fromstring(file.read_text(encoding="utf-8-sig"))
    if doc.xpath('//link[@rel="canonical"]/@href') != [BASE + path]:
        raise PublicationError("Local canonical URL is inconsistent")
    blocks = doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " e-content ")]')
    if not blocks:
        raise PublicationError("Local article has no content")
    sample = " ".join(blocks[0].text_content().split())[:160]
    if len(sample) < 12:
        raise PublicationError("Insufficient content for live verification")
    return sample


def publication_urls(path: str) -> set[str]:
    """Only the known HTML permalink and its extensionless equivalent."""
    return {BASE + path, BASE + path.removesuffix(".html")}


class PublicationRedirect(request.HTTPRedirectHandler):
    def __init__(self, path: str):
        self.path = path

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if newurl not in publication_urls(self.path):
            raise PublicationError(f"Unexpected live redirect for {BASE + self.path}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def verify_live(root: Path, target: dict, opener=None) -> str:
    """Require HTTPS 200, a safe permalink, exact canonical URL and matching authored text."""
    path = target["path"]
    sample = local_sample(root, target)
    opener = opener or request.build_opener(PublicationRedirect(path))
    req = request.Request(BASE + path, headers={
        "User-Agent": "Schmookey-Publication-Verifier/1.0",
        "Accept": "text/html", "Cache-Control": "no-cache",
    })
    try:
        with opener.open(req, timeout=20) as response:
            if response.status != 200 or response.geturl() not in publication_urls(path):
                raise PublicationError(f"Live URL did not return the expected page: {BASE + path}")
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise PublicationError(f"Live URL did not return HTML: {BASE + path}")
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise PublicationError(f"Live page exceeded size limit: {BASE + path}")
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise PublicationError(f"Live URL could not be verified: {BASE + path}") from exc
    doc = html.fromstring(body)
    if doc.xpath('//link[@rel="canonical"]/@href') != [BASE + path]:
        raise PublicationError(f"Live page canonical does not match: {BASE + path}")
    blocks = doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " e-content ")]')
    if not blocks or not " ".join(blocks[0].text_content().split()).startswith(sample):
        raise PublicationError(f"Live page content is stale or unexpected: {BASE + path}")
    return BASE + path


def read_ledger(root: Path):
    data = json_from(root / LEDGER)
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("entries"), dict):
        raise PublicationError("Invalid syndication ledger")
    return data


def save_ledger(root: Path, data: dict, message: str):
    """Commit state before posting and again afterwards; fail closed on errors."""
    (root / LEDGER).write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for command in (
        ["git", "add", str(LEDGER)],
        ["git", "commit", "-m", message],
        ["git", "push", "origin", "HEAD:main"],
    ):
        try:
            subprocess.run(command, cwd=root, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            raise PublicationError("Could not persist syndication ledger in GitHub") from exc


def api_post(url: str, body: dict, headers=None):
    req = request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                          headers={"Accept": "application/json", "Content-Type": "application/json",
                                   **(headers or {})})
    try:
        with request.urlopen(req, timeout=20) as response:
            if not 200 <= response.status < 300:
                raise PublicationError("Social API rejected publication")
            return json.loads(response.read(250_000))
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise PublicationError("Social API failed; check pending record before retry") from exc


def api_get(url: str, headers: dict):
    req = request.Request(url, headers={"Accept": "application/json", **headers})
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read(250_000))
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise PublicationError("Unable to verify social account") from exc


def message(target, permalink, limit):
    heading = " ".join(target["title"].split())
    available = limit - len(permalink) - 2
    if available < 16:
        raise PublicationError("Permalink exceeds social message limit")
    if len(heading) > available:
        heading = heading[:available - 1].rstrip() + "…"
    return heading + "\n\n" + permalink


def mastodon(target, permalink):
    token = os.environ.get("MASTODON_ACCESS_TOKEN")
    if not token:
        raise PublicationError("MASTODON_ACCESS_TOKEN secret not configured")
    headers = {"Authorization": "Bearer " + token}
    account = api_get("https://mastodon.social/api/v1/accounts/verify_credentials", headers)
    if account.get("username", "").lower() != "schmookey":
        raise PublicationError("Mastodon credentials do not match intended account")
    key = hashlib.sha256(permalink.encode()).hexdigest()
    result = api_post("https://mastodon.social/api/v1/statuses",
                      {"status": message(target, permalink, 480), "visibility": "public"},
                      {**headers, "Idempotency-Key": "schmookey-" + key[:48]})
    url = result.get("url", "")
    if not url.startswith("https://mastodon.social/"):
        raise PublicationError("Mastodon post URL unconfirmed; reconcile pending record")
    return url


def bluesky(target, permalink):
    handle = os.environ.get("BSKY_HANDLE")
    password = os.environ.get("BSKY_APP_PASSWORD")
    if not handle or not password:
        raise PublicationError("Bluesky handle or app password not configured")
    session = api_post("https://bsky.social/xrpc/com.atproto.server.createSession",
                       {"identifier": handle, "password": password})
    if session.get("handle", "").lower() != "schmookey.xyz" or not session.get("did", "").startswith("did:plc:"):
        raise PublicationError("Bluesky credentials do not match intended account")
    if not session.get("accessJwt"):
        raise PublicationError("Bluesky session is missing its access token")
    msg = message(target, permalink, 270)
    start = len(msg[:msg.index(permalink)].encode("utf-8"))
    end = start + len(permalink.encode("utf-8"))
    rkey = "smk" + hashlib.sha256(permalink.encode()).hexdigest()[:21]
    record = {
        "$type": "app.bsky.feed.post", "text": msg,
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "facets": [{
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": permalink}],
        }],
    }
    result = api_post("https://bsky.social/xrpc/com.atproto.repo.createRecord", {
        "repo": session["did"], "collection": "app.bsky.feed.post",
        "rkey": rkey, "record": record,
    }, {"Authorization": "Bearer " + session["accessJwt"]})
    if result.get("uri") != f"at://{session['did']}/app.bsky.feed.post/{rkey}":
        raise PublicationError("Bluesky record unconfirmed; reconcile pending record")
    return f"https://bsky.app/profile/{parse.quote(handle, safe='.')}/post/{rkey}"


def run(root: Path, *, execute=False, verify_only=False):
    ledger = read_ledger(root)
    items = sorted(candidates(root), key=lambda item: item["path"])
    pending = [(target, platform) for target in items for platform in target["platforms"]
               if platform not in ledger["entries"].get(target["path"], {})]
    if not pending:
        print("No newly published, opted-in content.")
        return
    if len(pending) > 10:
        raise PublicationError("Syndication backlog too large; inspect before enabling")
    if not execute and not verify_only:
        for target, platform in pending:
            print("PREVIEW:", target["path"], "->", platform)
        return
    if execute and os.environ.get("SOCIAL_SYNDICATION_ENABLED") != "true":
        raise PublicationError("Social publishing has not been explicitly enabled")
    if execute:
        for _, platform in pending:
            if platform == "mastodon" and not os.environ.get("MASTODON_ACCESS_TOKEN"):
                raise PublicationError("Mastodon credentials are missing")
            if platform == "bluesky" and not (os.environ.get("BSKY_HANDLE") and os.environ.get("BSKY_APP_PASSWORD")):
                raise PublicationError("Bluesky credentials are missing")
    verified = {}
    for target, platform in pending:
        path = target["path"]
        if path not in verified:
            verified[path] = verify_live(root, target)
            print("Verified live:", path)
        if not execute:
            continue
        permalink = verified[path]
        ledger["entries"].setdefault(path, {})[platform] = {
            "status": "pending", "permalink": permalink,
        }
        save_ledger(root, ledger, "Claim social syndication " + platform + " " + path)
        result = mastodon(target, permalink) if platform == "mastodon" else bluesky(target, permalink)
        ledger["entries"][path][platform] = {
            "status": "posted", "permalink": permalink, "social_url": result,
        }
        save_ledger(root, ledger, "Record social syndication " + platform + " " + path)
        print("Published to", platform, result)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verify-only", action="store_true")
    group.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        run(ROOT, execute=args.execute, verify_only=args.verify_only)
    except (PublicationError, ValueError, KeyError, OSError) as exc:
        print("Publication stopped: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
