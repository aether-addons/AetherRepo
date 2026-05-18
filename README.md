# AetherRepo

Kodi repository output for Aether add-ons.

GitHub raw feed:

```text
https://raw.githubusercontent.com/aether-addons/AetherRepo/main/
```

Current scraper add-on source repo:

```text
https://github.com/aether-addons/AetherScraper
```

## Hosted add-ons

- `repository.aetherscraper`
- `script.module.aetherscraper`
- `plugin.program.aetherscraper`

More add-ons can be hosted by pointing `--source` at source folders for any Aether add-on family and passing more `--addon` flags to `build_repo.py`.

## Build

From this folder, with `../AetherScraper` checked out for current scraper add-ons:

```bash
python3 build_repo.py
python3 scripts/validate_repo.py .
```

Default build writes GitHub raw URLs for `aether-addons/AetherRepo` branch `main`.

Local test build:

```bash
python3 build_repo.py --local-file-url
```

Custom branch or URL:

```bash
python3 build_repo.py --github-branch dev
python3 build_repo.py --datadir-url "https://raw.githubusercontent.com/aether-addons/AetherRepo/main/"
```

## Install in Kodi

1. Download or clone this repo.
2. In Kodi: **Add-ons -> Install from zip file**.
3. Pick latest `repository.aetherscraper/repository.aetherscraper-*.zip`.
4. Use **Install from repository -> Aether Repo**.
5. Install wanted add-ons from **Aether Repo**. For current scraper tools, Kodi also installs `script.module.aetherscraper` dependency.

## Generated files

- `addons.xml`
- `addons.xml.md5` (Kodi compatibility)
- `addons.xml.sha256`
- `repository.aetherscraper/repository.aetherscraper-*.zip`
- `script.module.aetherscraper/script.module.aetherscraper-*.zip`
- `plugin.program.aetherscraper/plugin.program.aetherscraper-*.zip`
