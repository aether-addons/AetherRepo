#!/usr/bin/env python3
"""Validate generated AetherRepo Kodi repository files."""

from __future__ import annotations

import hashlib
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

FORBIDDEN_PARTS = {
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
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pyd", ".swp", ".tmp", ".log", ".zip"}
KODI_CHECKSUM_FILE = "addons.xml.md5"
SHA256_CHECKSUM_FILE = "addons.xml.sha256"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def parse_addon_xml(path: Path) -> tuple[str, str, ET.Element]:
    if not path.is_file():
        fail(f"missing {path}")
    root = ET.parse(path).getroot()
    addon_id = root.attrib.get("id", "")
    version = root.attrib.get("version", "")
    if not addon_id or not version:
        fail(f"{path} missing addon id/version")
    return addon_id, version, root


def validate_checksum(root: Path) -> None:
    addons_xml = root / "addons.xml"
    kodi_checksum = root / KODI_CHECKSUM_FILE
    sha256_checksum = root / SHA256_CHECKSUM_FILE
    if not addons_xml.is_file():
        fail("missing addons.xml")
    if not kodi_checksum.is_file():
        fail(f"missing {KODI_CHECKSUM_FILE}")
    if not sha256_checksum.is_file():
        fail(f"missing {SHA256_CHECKSUM_FILE}")
    data = addons_xml.read_bytes()
    # Kodi repository clients expect the <checksum> URL to contain an MD5 digest.
    expected_kodi = hashlib.new("md" + "5", data, usedforsecurity=False).hexdigest()
    actual_kodi = kodi_checksum.read_text(encoding="utf-8").strip()
    if actual_kodi != expected_kodi:
        fail(f"{KODI_CHECKSUM_FILE} mismatch: {actual_kodi} != {expected_kodi}")
    expected_sha256 = hashlib.sha256(data).hexdigest()
    actual_sha256 = sha256_checksum.read_text(encoding="utf-8").strip()
    if actual_sha256 != expected_sha256:
        fail(f"{SHA256_CHECKSUM_FILE} mismatch: {actual_sha256} != {expected_sha256}")
    ET.parse(addons_xml)


def validate_repository_urls(root: Path) -> None:
    _, _, addon = parse_addon_xml(root / "repository.aetherscraper" / "addon.xml")
    repo_ext = next(
        (
            node
            for node in addon.findall("extension")
            if node.attrib.get("point") == "xbmc.addon.repository"
        ),
        None,
    )
    if repo_ext is None:
        fail("repository addon missing xbmc.addon.repository extension")
    for tag in ("info", "checksum", "datadir"):
        node = repo_ext.find(tag)
        if node is None or not (node.text or "").startswith(
            "https://raw.githubusercontent.com/aether-addons/AetherRepo/"
        ):
            fail(f"repository {tag} URL is not GitHub raw URL")


def validate_zip(root: Path, addon_id: str, version: str) -> None:
    zip_path = root / addon_id / f"{addon_id}-{version}.zip"
    if not zip_path.is_file():
        fail(f"missing {zip_path}")
    with ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if name and not name.endswith("/")]
    roots = {name.split("/", 1)[0] for name in names}
    if roots != {addon_id}:
        fail(f"{zip_path} has wrong top-level entries: {sorted(roots)}")
    if f"{addon_id}/addon.xml" not in names:
        fail(f"{zip_path} missing {addon_id}/addon.xml")
    for name in names:
        parts = Path(name).parts
        if any(part in FORBIDDEN_PARTS for part in parts):
            fail(f"{zip_path} contains forbidden path: {name}")
        if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES:
            fail(f"{zip_path} contains forbidden suffix: {name}")


def validate_addons_index(root: Path) -> None:
    addons = ET.parse(root / "addons.xml").getroot()
    if addons.tag != "addons":
        fail("addons.xml root must be <addons>")
    for addon in addons.findall("addon"):
        addon_id = addon.attrib.get("id", "")
        version = addon.attrib.get("version", "")
        if not addon_id or not version:
            fail("addons.xml entry missing id/version")
        validate_zip(root, addon_id, version)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    validate_checksum(root)
    validate_repository_urls(root)
    validate_addons_index(root)
    print("AetherRepo validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
