#!/usr/bin/env python3
"""One-time checksum-verified copy of supplied Neocities ZIP's *public files*.

The hashes were computed against the user's 2026-11-13 ZIP. Nothing is sent to
Neocities; GitHub Actions fetches files from the public site into a review branch.
Protected: GitHub workflows, code, tests, docs, generated Trakt JSON and all
archive ZIPs. This script never deletes tracked files.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {
  "about.html":  "a36046506b7b7002bc4fc795288c9430087d2283",
  "assets/css/style.css":  "c47e898b149aab11e2659d65f6973cdbd820d1e9",
  "assets/data/site-updates.json":  "6998dbfd37e05db1f4e8490b07a4ccf3c765ac54",
  "assets/images/fediverse.png":  "17f9ffc71dec6352efa0ae129ce0b7b6a10c5a40",
  "assets/images/schmookey_trading_card.png":  "0d669230f7e95390829efbe209824e1c35fbf3b1",
  "assets/images/steam.gif":  "1f4fe29ddf0277418fd1a058b15ba32a65359fb6",
  "blog-archive.html":  "84fb34681b1e736c03382e51ea70dbec44e4db94",
  "blog/index.html":  "b6973979362a2230963403e4c9a037c1e6b86c16",
  "blog/posts/august_updates.html":  "a5fe3a294e1d8d99714a807d4bca8327e62cbfe0",
  "blog/posts/blog-template.html":  "908363dabebf03f8c3471d3b051df38f21a5c631",
  "blog/posts/coding_vibes.html":  "6f5d712d354baca4316be25dfeeae087bff41793",
  "blog/posts/physical-media.html":  "1e102d392b0ebd738564f4c5fd2319e95962e046",
  "blog/posts/podcast-blah-blah.html":  "7feeb980f03fd8c3401aa79d2a5bdb9e00cd3c51",
  "blog/posts/post1.html":  "ec52efc61e2c8da29dbc72004406dde0762a2032",
  "blog/posts/post2.html":  "a49ba09bd7ebbf2b12f873d07cc3e80f0cbc2d9f",
  "blog/posts/snluk.html":  "14d46049c848d91a48c0c22c80d28535ac0c0e2d",
  "blog/posts/this-week-23-29-march.html":  "0151e493a2f106c8eb22d3c23a97567c9a9d1f61",
  "changelog.html":  "1feb7f7fe500c0dfeda167358b400303feaf21d8",
  "index.html":  "a06685facbeb647a7c58ffca22c3a25e6e332785",
  "listening.html":  "e6e54d9297336833cf0e2f3b44ac4df1e283b73e",
  "music-archive.html":  "ae43ca789a46091ced18a643ac58d75ae626551a",
  "music/index.html":  "b4aea2e88083dbd8091114782382fc59f07476d1",
  "music/posts/listenbrainz.html":  "500f673a336f04cd5d2a6400f6f5d3ae877f9509",
  "now-watching.html":  "a515de99a0133b4b2698581a923a5830f91a01ac",
  "now.html":  "86fa2b3359b1327155afc216ee1d232c9e8573c4",
  "page-template.html":  "54d0889f085b9e6356dbfc0091065dbfcb58b9a9",
  "privacy.html":  "fc2366635fff8253f2c24fc39332ff725c5f18ec",
  "random/index.html":  "344d11a35fc89e45190511800f8c417854aca447",
  "webrings.html":  "180987221806d0fbb5b62b53b775f3e042d76527"
}

def main() -> None:
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != "sync/neocities-live-2026-11-13":
        raise SystemExit("Refusing to run outside import branch")
    data = {}
    for name, expected in EXPECTED.items():
        url = "https://schmookey.xyz/" + urllib.parse.quote(name, safe="/")
        req = urllib.request.Request(url, headers={"User-Agent": "Schmookey-Archive-Integrity-Importer/1.0", "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=25) as response:
            content = response.read(5_000_000)
            if response.read(1):
                raise ValueError(f"{name}: file exceeds 5 MB")
        got = hashlib.sha1(f"blob {len(content)}\0".encode("utf-8") + content).hexdigest()
        if got != expected:
            raise ValueError(f"{name}: live site differs from supplied ZIP: expected {expected}, found {got}")
        data[name] = content
        print(f"Verified {name}: {len(content)} bytes", flush=True)
    for name, content in data.items():
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    subprocess.check_call(["git", "add", "--", *EXPECTED.keys()], cwd=ROOT)
    if subprocess.call(["git", "diff", "--cached", "--quiet"], cwd=ROOT) == 0:
        print("All selected website files already match.")
        return
    subprocess.check_call(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT)
    subprocess.check_call(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=ROOT)
    subprocess.check_call(["git", "commit", "-m", "Sync latest checksum-verified Neocities pages, styles and artwork"], cwd=ROOT)
    subprocess.check_call(["git", "push", "origin", "HEAD:sync/neocities-live-2026-11-13"], cwd=ROOT)

if __name__ == "__main__":
    main()
