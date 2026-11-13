#!/usr/bin/env python3
"""Publish the non-secret Trakt Client ID for browser-side public history reads.

Never publish TRAKT_CLIENT_SECRET, TMDB_ACCESS_TOKEN, or OAuth access tokens.
"""
import json
import os
import re
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "assets/data/trakt-public-config.json"

def main() -> None:
    client_id = os.environ.get("TRAKT_CLIENT_ID", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{8,256}", client_id):
        raise SystemExit("Valid public TRAKT_CLIENT_ID required; config not changed.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"client_id": client_id}, indent=2) + "\n",
        encoding="utf-8"
    )
    print("Created browser-facing public Trakt Client ID configuration (value not logged).")

if __name__ == "__main__":
    main()
