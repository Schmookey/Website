#!/usr/bin/env python3
"""Conservative Neocities publisher: preview by default, never prune.

Requires the NEOCITIES_API_KEY Actions secret. Only explicit paths are eligible.
No repository data, secrets, or Neocities backups are printed to logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
API = "https://neocities.org/api"
EXPECTED_DOMAIN = "schmookey.xyz"
# Explicit allowlist. The manually edited site-updates JSON is never uploaded.
PUBLISH_FILES = (
    "assets/js/main.js",
    "assets/css/style.css",
    "privacy.html",
)


def request(path: str, key: str, *, method: str = "GET",
            data: bytes | None = None, content_type: str | None = None) -> dict:
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    if content_type is not None:
        headers["Content-Type"] = content_type
    req = Request(API + path, method=method, headers=headers, data=data)
    try:
        with urlopen(req, timeout=35) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(
            f"Neocities request {path} failed ({type(exc).__name__}); "
            "no further files will be uploaded."
        ) from None
    if not isinstance(result, dict) or result.get("result") != "success":
        raise RuntimeError(f"Neocities API returned an error for {path}.")
    return result


def verify_destination(info: dict) -> None:
    site = info.get("info")
    if not isinstance(site, dict):
        raise RuntimeError("No verified Neocities site identity was returned.")
    domain = str(site.get("domain") or "").lower().strip().rstrip(".")
    if domain != EXPECTED_DOMAIN:
        raise RuntimeError(
            "Neocities API key does not identify the expected custom domain "
            f"{EXPECTED_DOMAIN}; refusing to continue."
        )
    if not site.get("sitename"):
        raise RuntimeError("Neocities API response did not identify a site.")
    print("Verified Neocities destination: " + domain)


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def build_upload_payload(paths: list[str]) -> tuple[bytes, str]:
    # Multipart field names are the remote destination paths.
    boundary = "schmookey-manual-upload-boundary"
    pieces = []
    for relative in paths:
        path = ROOT / relative
        pieces.append((
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{relative}"; '
            f'filename="{path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("ascii"))
        pieces.append(path.read_bytes())
        pieces.append(b"\r\n")
    pieces.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(pieces), "multipart/form-data; boundary=" + boundary


def run(deploy: bool = False) -> None:
    key = os.environ.get("NEOCITIES_API_KEY", "").strip()
    if not key:
        raise RuntimeError("NEOCITIES_API_KEY secret has not been configured.")
    # Prevent uploads to the wrong Neocities account.
    verify_destination(request("/info", key))
    remote = request("/list", key).get("files")
    if not isinstance(remote, list):
        raise RuntimeError("Neocities file list was unavailable.")
    existing = {
        item["path"]: item.get("sha1_hash")
        for item in remote
        if isinstance(item, dict) and isinstance(item.get("path"), str)
        and not item.get("is_directory")
    }
    changes = []
    for relative in PUBLISH_FILES:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"Missing or unsafe local file: {relative}")
        if existing.get(relative) == sha1(path):
            print("UNCHANGED " + relative)
        else:
            changes.append(relative)
            print("DIFFERS   " + relative)
    print(f"Files selected: {len(PUBLISH_FILES)}; differing: {len(changes)}.")
    if not deploy:
        print("PREVIEW ONLY: No changes made to Neocities.")
        return
    if not changes:
        print("No upload needed; no files modified.")
        return
    body, content_type = build_upload_payload(changes)
    request("/upload", key, method="POST", data=body, content_type=content_type)
    print("Uploaded only these paths: " + ", ".join(changes))
    print("No other files were modified and none were deleted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preview", action="store_true", help="Read-only comparison")
    modes.add_argument("--deploy", action="store_true", help="Upload allowlisted changes")
    args = parser.parse_args()
    try:
        run(deploy=args.deploy)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
