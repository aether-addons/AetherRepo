# AGENTS.md — AetherRepo Working Standards

Kodi install repository output for Aether add-ons: https://github.com/aether-addons/AetherRepo.
Current scraper add-on source/development lives in sibling repo: https://github.com/aether-addons/AetherScraper.

## Required AI workflow

1. Treat this repo as generated release output, not source development workspace.
2. Make add-on code changes in the matching source repo first (currently `../AetherScraper` for scraper add-ons).
3. Bump changed add-on versions in source `addon.xml` files before rebuilding release zips.
4. Rebuild from this repo after source changes:

```bash
python3 build_repo.py
python3 scripts/validate_repo.py .
```

5. Default feed must stay GitHub raw:

```text
https://raw.githubusercontent.com/aether-addons/AetherRepo/main/
```

6. Use `python3 build_repo.py --local-file-url` only for local Kodi testing; never commit local `file://` feed URLs.
7. Keep generated files committed:
   - `addons.xml`
   - `addons.xml.md5`
   - `addons.xml.sha256`
   - `repository.aetherscraper/*.zip`
   - hosted add-on `*.zip` files
8. Keep package layout clean: each zip has exactly one top-level folder matching add-on id and contains `addon.xml`.
9. Do not commit cache/dev artifacts (`__pycache__`, `.ruff_cache`, `.pi-lens`, test output, venvs).
10. Commit/push matching source repo changes first, then commit/push this regenerated repo output.
11. If adding new add-ons, add source folder under the matching source repo (currently `../AetherScraper` for scraper add-ons), then include with `--addon addon.id` or update `DEFAULT_ADDONS` in `build_repo.py`.
12. Validate CI config when changing workflows.

## CI

`.github/workflows/ci.yml` checks out both repos, rebuilds the feed, validates zip/checksum/layout, and fails if generated files are not committed.

## Safety

- Do not publish add-ons that bypass DRM, paywalls, anti-bot systems, or access controls.
- Do not publish secrets, API keys, cookies, tokens, logs, cache DBs, or user data.
- Repository URLs should remain HTTPS GitHub raw URLs for public installs.
