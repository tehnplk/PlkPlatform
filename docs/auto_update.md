# Auto Update

Plk Platform checks for updates after startup when running as a PyInstaller executable.
Development runs through `uv run start.py` skip update installation unless `PLK_UPDATE_ALLOW_DEV=1`.

## Configure Endpoint

Set either:

```powershell
$env:PLK_UPDATE_MANIFEST_URL = "https://example.com/plkplatform/latest.json"
```

or place `update_config.json` next to `PlkPlatform.exe`:

```json
{
  "manifest_url": "https://example.com/plkplatform/latest.json"
}
```

## Manifest Format

The endpoint must return JSON:

```json
{
  "version": "0.1.1",
  "url": "https://example.com/plkplatform/PlkPlatform.exe",
  "sha256": "optional lowercase sha256",
  "release_date": "2026-04-24",
  "notes": "optional release notes"
}
```

`sha256` is optional, but production releases should include it. The app downloads the new executable to `%LOCALAPPDATA%\PlkPlatform\updates`, verifies the hash when supplied, starts a small PowerShell updater, then closes. The updater replaces the current executable after the process exits, so the next time the user opens Plk Platform they get the new version.
