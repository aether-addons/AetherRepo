#!/usr/bin/env python3
"""Build Kodi repository files for Aether Repo.

GitHub layout:
- AetherScraper: source/development repository
- AetherRepo: Kodi install repository with addons.xml, checksums, and zips
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile

REPO_ID = "repository.aetherscraper"
REPO_NAME = "Aether Repo"
REPO_VERSION = "0.1.3"
GITHUB_OWNER = "aether-addons"
GITHUB_REPOSITORY = "AetherRepo"
DEFAULT_BRANCH = "main"
DEFAULT_ADDONS = [
    "script.module.aetherscraper",
    "plugin.program.aetherscraper",
]
EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".pi-lens",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "tests",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".swp", ".tmp", ".log", ".zip"}
EXCLUDE_FILES = {"index.html"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def github_raw_url(branch: str = DEFAULT_BRANCH) -> str:
    return f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/{branch}/"


def github_pages_url() -> str:
    return f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPOSITORY}/"


def default_windows_file_url(root: Path) -> str:
    """Convert local path to Kodi-friendly file URL for manual local testing."""
    absolute_root = root.absolute()
    parts = absolute_root.parts
    if len(parts) > 3 and parts[0] == "/" and parts[1] == "mnt" and len(parts[2]) == 1:
        drive = parts[2].upper() + ":"
        rest = "/".join(quote(p) for p in parts[3:])
        return f"file:///{drive}/{rest}/"
    return absolute_root.as_uri().rstrip("/") + "/"


def parse_addon(addon_dir: Path) -> tuple[str, str, ET.Element]:
    addon_xml = addon_dir / "addon.xml"
    if not addon_xml.is_file():
        raise FileNotFoundError(f"missing {addon_xml}")
    element = ET.parse(addon_xml).getroot()
    addon_id = element.attrib.get("id", "")
    version = element.attrib.get("version", "")
    if not addon_id or not version:
        raise ValueError(f"{addon_xml} missing addon id/version")
    if addon_id != addon_dir.name:
        raise ValueError(f"{addon_xml} id '{addon_id}' != folder '{addon_dir.name}'")
    return addon_id, version, element


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    if path.name in EXCLUDE_FILES:
        return True
    if path.name.startswith(".") and path.name not in {".gitignore"}:
        return True
    return path.suffix.lower() in EXCLUDE_SUFFIXES


def zip_addon(addon_dir: Path, out_zip: Path) -> None:
    addon_id, _, _ = parse_addon(addon_dir)
    if out_zip.exists():
        out_zip.unlink()
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_zip, "w", ZIP_DEFLATED) as archive:
        for file_path in sorted(addon_dir.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(addon_dir)
            if should_skip(rel):
                continue
            archive.write(file_path, Path(addon_id, rel).as_posix())
    with ZipFile(out_zip) as archive:
        names = archive.namelist()
    needed = f"{addon_id}/addon.xml"
    if needed not in names:
        raise RuntimeError(f"zip invalid: missing {needed}")
    bad = [name for name in names if not name.startswith(f"{addon_id}/")]
    if bad:
        raise RuntimeError(f"zip invalid: bad top-level entry {bad[0]}")


def indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + level * "  "
    children = list(element)
    if children:
        if not element.text or not element.text.strip():
            element.text = pad + "  "
        for child in children:
            indent(child, level + 1)
        last_child = children[-1]
        if not last_child.tail or not last_child.tail.strip():
            last_child.tail = pad
    if level and (not element.tail or not element.tail.strip()):
        element.tail = pad


def write_repository_addon(root: Path, source: Path, datadir_url: str) -> Path:
    repo_dir = root / REPO_ID
    resources = repo_dir / "resources"
    resources.mkdir(parents=True, exist_ok=True)

    # Reuse AetherScraper icon/fanart if available.
    source_base = source / "script.module.aetherscraper" / "resources"
    for name in ("icon.png", "fanart.png"):
        src = source_base / name
        dst = resources / name
        if src.is_file():
            shutil.copy2(src, dst)

    addon_xml = repo_dir / "addon.xml"
    addon_xml.write_text(
        f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n"""
        f'''<addon id="{REPO_ID}" version="{REPO_VERSION}" name="{REPO_NAME}" provider-name="AetherScraper">\n'''
        f"""  <requires>\n"""
        f"""    <import addon="xbmc.addon" version="12.0.0" />\n"""
        f"""  </requires>\n"""
        f'''  <extension point="xbmc.addon.repository" name="{REPO_NAME}">\n'''
        f"""    <dir>\n"""
        f"""      <info compressed="false">{datadir_url}addons.xml</info>\n"""
        f"""      <checksum>{datadir_url}addons.xml.md5</checksum>\n"""
        f"""      <datadir zip="true">{datadir_url}</datadir>\n"""
        f"""      <hashes>false</hashes>\n"""
        f"""    </dir>\n"""
        f"""  </extension>\n"""
        f"""  <extension point="xbmc.addon.metadata">\n"""
        f"""    <summary lang="en_GB">Repository for AetherScraper add-ons.</summary>\n"""
        f"""    <description lang="en_GB">Installs and updates AetherScraper modules and companion add-ons.</description>\n"""
        f"""    <platform>all</platform>\n"""
        f"""    <license>MIT</license>\n"""
        f"""    <assets>\n"""
        f"""      <icon>resources/icon.png</icon>\n"""
        f"""      <fanart>resources/fanart.png</fanart>\n"""
        f"""    </assets>\n"""
        f"""  </extension>\n"""
        f"""</addon>\n""",
        encoding="utf-8",
    )
    return repo_dir


def write_pages_indexes(root: Path, addon_dirs: list[Path]) -> None:
    """Write simple GitHub Pages index for Kodi File Manager browsing."""
    (root / ".nojekyll").write_text("", encoding="utf-8")

    repo_dir = next(addon_dir for addon_dir in addon_dirs if addon_dir.name == REPO_ID)
    repo_id, repo_version, _ = parse_addon(repo_dir)
    zip_name = f"{repo_id}-{repo_version}.zip"

    repo_index = root / repo_id / "index.html"
    repo_index.write_text(
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8">'
        f"<title>Index of /AetherRepo/{html.escape(repo_id)}</title></head>\n"
        "<body>\n"
        f"  <h1>Index of /AetherRepo/{html.escape(repo_id)}</h1>\n"
        "  <ul>\n"
        f'    <li><a href="{html.escape(zip_name)}">{html.escape(zip_name)}</a></li>\n'
        "  </ul>\n"
        "</body></html>\n",
        encoding="utf-8",
    )

    (root / "index.html").write_text(
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8">'
        "<title>Index of /AetherRepo</title></head>\n"
        "<body>\n"
        "  <h1>Index of /AetherRepo</h1>\n"
        "  <p>Open repository.aetherscraper, then install the repository zip in Kodi.</p>\n"
        "  <ul>\n"
        f'    <li><a href="{html.escape(repo_id)}/">{html.escape(repo_id)}/</a></li>\n'
        "  </ul>\n"
        "</body></html>\n",
        encoding="utf-8",
    )


def write_addons_xml(root: Path, addon_dirs: list[Path]) -> None:
    addons = ET.Element("addons")
    for addon_dir in addon_dirs:
        _, _, element = parse_addon(addon_dir)
        addons.append(element)
    indent(addons)
    xml_bytes = ET.tostring(addons, encoding="utf-8", xml_declaration=True)
    addons_xml = root / "addons.xml"
    addons_xml.write_bytes(xml_bytes + b"\n")
    data = addons_xml.read_bytes()
    # Kodi repository clients expect the <checksum> URL to contain an MD5 digest.
    kodi_digest = hashlib.new("md" + "5", data, usedforsecurity=False).hexdigest()
    (root / "addons.xml.md5").write_text(kodi_digest, encoding="utf-8")
    (root / "addons.xml.sha256").write_text(
        hashlib.sha256(data).hexdigest(), encoding="utf-8"
    )
    ET.parse(addons_xml)  # fail fast if malformed


def build(source: Path, addon_ids: list[str], datadir_url: str) -> None:
    root = repo_root()
    repo_dir = write_repository_addon(root, source, datadir_url)

    addon_dirs = [repo_dir]
    for addon_id in addon_ids:
        addon_dir = source / addon_id
        parse_addon(addon_dir)
        addon_dirs.append(addon_dir)

    for addon_dir in addon_dirs:
        addon_id, version, _ = parse_addon(addon_dir)
        zip_addon(addon_dir, root / addon_id / f"{addon_id}-{version}.zip")

    write_addons_xml(root, addon_dirs)
    write_pages_indexes(root, addon_dirs)

    print(f"Repository: {root}")
    print(f"Source:     {source}")
    print(f"Data URL:   {datadir_url}")
    for addon_dir in addon_dirs:
        addon_id, version, _ = parse_addon(addon_dir)
        print(f"OK: {addon_id}/{addon_id}-{version}.zip")
    print("OK: addons.xml")
    print("OK: addons.xml.md5")
    print("OK: addons.xml.sha256")


def main() -> int:
    root = repo_root()
    default_branch = os.environ.get("GITHUB_REF_NAME") or DEFAULT_BRANCH
    parser = argparse.ArgumentParser(description="Build AetherScraper Kodi repository")
    parser.add_argument(
        "--source",
        default=str(root.parent / "AetherScraper"),
        help="Folder containing source addon folders",
    )
    parser.add_argument(
        "--github-branch",
        default=default_branch,
        help="GitHub branch used for default raw.githubusercontent.com datadir URL",
    )
    parser.add_argument(
        "--datadir-url",
        default=None,
        help="URL ending with / used by Kodi repository; default is GitHub raw URL",
    )
    parser.add_argument(
        "--local-file-url",
        action="store_true",
        help="Use a local file:// datadir URL for manual testing instead of GitHub raw URL",
    )
    parser.add_argument(
        "--addon",
        action="append",
        dest="addons",
        help="Addon id to host; repeatable. Defaults to all supported Aether add-ons.",
    )
    args = parser.parse_args()

    addons = args.addons or DEFAULT_ADDONS
    if args.datadir_url:
        datadir_url = args.datadir_url
    elif args.local_file_url:
        datadir_url = default_windows_file_url(root)
    else:
        datadir_url = github_pages_url()
    build(Path(args.source).resolve(), addons, datadir_url.rstrip("/") + "/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
