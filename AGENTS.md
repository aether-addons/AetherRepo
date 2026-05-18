# AGENTS.md — AetherRepo Working Standards

Kodi install repository output for Aether add-ons: https://github.com/aether-addons/AetherRepo.
Current scraper add-on source/development lives in sibling repo: https://github.com/aether-addons/AetherScraper.

## Required AI workflow

1. Treat this repo as generated Kodi install feed, not add-on source.
2. Source repos are listed in `repo-sources.json` (`sources[].repository`, `branch`, `addons`). Add new hosted add-ons there, not in `build_repo.py`.
3. Normal release flow is automatic:
   - change source repo add-on code
   - bump changed source `addon.xml` version
   - push source repo
   - source workflow dispatches `AetherRepo`
   - `AetherRepo/.github/workflows/publish.yml` clones all `repo-sources.json` sources, rebuilds, validates, commits generated feed
4. Do not manually edit generated feed/zips unless fixing repo tooling or user asks for local release rebuild.
5. Manual local rebuild/validation, if needed:

```bash
python3 scripts/checkout_manifest_sources.py repo-sources.json ../Sources
python3 build_repo.py --sources-manifest repo-sources.json --source-root ../Sources
python3 scripts/validate_repo.py .
```

6. Default feed must stay GitHub raw:

```text
https://raw.githubusercontent.com/aether-addons/AetherRepo/main/
```

7. Use `python3 build_repo.py --local-file-url` only for local Kodi testing; never commit local `file://` feed URLs.
8. Keep generated files committed when this repo is rebuilt: `addons.xml`, checksums, repo zip, hosted add-on zips/md5.
9. Keep zip layout clean: exactly one top-level folder matching add-on id, with `addon.xml`.
10. Do not commit cache/dev artifacts (`__pycache__`, `.ruff_cache`, `.pi-lens`, test output, venvs).
11. Validate CI config when changing workflows.

## CI / automation

- `publish.yml`: triggered by `repository_dispatch` from source repos or manual run; rebuilds and commits feed.
- `ci.yml`: rebuilds from `repo-sources.json`, validates, fails if generated output is stale.
- Each source repo that should auto-publish needs a small notify workflow that dispatches `aether-addons/AetherRepo` event `source-updated` using the GitHub App secrets.

## Safety

- Do not publish add-ons that bypass DRM, paywalls, anti-bot systems, or access controls.
- Do not publish secrets, API keys, cookies, tokens, logs, cache DBs, or user data.
- Repository URLs should remain HTTPS GitHub raw URLs for public installs.
