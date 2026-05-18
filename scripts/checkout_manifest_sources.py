#!/usr/bin/env python3
"""Clone source repositories listed in repo-sources.json."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def clone_url(repository: str, token: str | None) -> str:
    if token:
        return f"https://x-access-token:{token}@github.com/{repository}.git"
    return f"https://github.com/{repository}.git"


def main() -> int:
    parser = argparse.ArgumentParser(description="Clone source repos from repo-sources.json")
    parser.add_argument("manifest", help="JSON file with a sources list")
    parser.add_argument("dest", help="Destination folder for checked-out source repos")
    parser.add_argument(
        "--token-env",
        default="AETHER_SOURCE_TOKEN",
        help="Environment variable containing an optional GitHub token",
    )
    args = parser.parse_args()

    manifest = Path(args.manifest).resolve()
    dest_root = Path(args.dest).resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{manifest} must contain a non-empty 'sources' list")

    token = os.environ.get(args.token_env)
    dest_root.mkdir(parents=True, exist_ok=True)

    for entry in sources:
        if not isinstance(entry, dict):
            raise ValueError("source entries must be objects")
        repository = entry.get("repository")
        if not isinstance(repository, str) or "/" not in repository:
            raise ValueError("source entries need 'repository' like 'owner/name'")
        branch = entry.get("branch", "main")
        if not isinstance(branch, str) or not branch:
            raise ValueError(f"{repository} has invalid branch")
        path = entry.get("path")
        checkout_name = path if isinstance(path, str) and path else repository.rsplit("/", 1)[1]
        checkout_dir = dest_root / checkout_name
        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)
        print(f"Cloning {repository}@{branch} -> {checkout_dir}")
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                clone_url(repository, token),
                str(checkout_dir),
            ],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
