# Auto Update

Plk Platform checks for updates after startup when running as a PyInstaller executable.
Development runs through `uv run start.py` skip update installation unless `PLK_UPDATE_ALLOW_DEV=1`.

## Host
- ssh adminplk@61.19.112.242 -pw Plkhe@lth00051 -p 2233
- path /var/www/wwwroot/platform.plkhealth.go.th

## Base Url
- https://platform.plkhealth.go.th/
- local port =  3011

## Tool to Upload file
 - pscp

## Configure Endpoint

Set either:

```powershell
$env:PLK_UPDATE_MANIFEST_URL = "https://platform.plkhealth.go.th/plkplatform/latest.json"
```

or place `update_config.json` next to `PlkPlatform.exe`:

```json
{
  "manifest_url": "https://platform.plkhealth.go.th/plkplatform/latest.json"
}
```

## Manifest Format

The endpoint must return JSON:

```json
{
  "version": "0.1.1",
  "url": "https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe",
  "sha256": "optional lowercase sha256",
  "release_date": "2026-04-24",
  "notes": "optional release notes"
}
```

`sha256` is optional, but production releases should include it. The app downloads the new executable to `%LOCALAPPDATA%\PlkPlatform\updates`, verifies the hash when supplied, shows a confirmation dialog with an **OK** button, then closes after the user clicks OK and starts a small PowerShell updater. The updater replaces the current executable after the process exits, so the next time the user opens Plk Platform they get the new version.

## Build & Deploy

Server paths:
- Web root: `/www/wwwroot/platform.plkhealth.go.th/` (landing page `index.html`)
- Release dir: `/www/wwwroot/platform.plkhealth.go.th/plkplatform/` (`PlkPlatform.exe`, `latest.json`)
- Backend: systemd unit `plkplatform-web.service` runs `python3 -m http.server 3011` bound to `127.0.0.1`, nginx proxies `platform.plkhealth.go.th` → `127.0.0.1:3011`.

### 1. Bump version

Edit [`version.py`](../version.py) and change `VERSION` (e.g. `"0.1.3"` → `"0.1.4"`).

### 2. Build the executable

```powershell
uv run pyinstaller PlkPlatform.spec --noconfirm
```

Output: `dist\PlkPlatform.exe`.

### 3. Compute SHA256

```powershell
(Get-FileHash -Algorithm SHA256 -Path "dist\PlkPlatform.exe").Hash.ToLower()
```

### 4. Write `dist\latest.json`

```json
{
  "version": "0.1.4",
  "url": "https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe",
  "sha256": "<sha256 from step 3>",
  "release_date": "YYYY-MM-DD",
  "notes": "release notes"
}
```

### 5. Upload to server

The release dir is owned by `adminplk` (set once during initial setup); web files need to end up owned by `www:www`. Upload via `/tmp/` then move with `sudo`:

```bash
# from project root (Windows, bash)
pscp -P 2233 -pw "Plkhe@lth00051" -batch \
  dist/PlkPlatform.exe dist/latest.json \
  adminplk@61.19.112.242:/tmp/

plink -ssh -P 2233 -pw "Plkhe@lth00051" -batch adminplk@61.19.112.242 \
  "echo 'Plkhe@lth00051' | sudo -S mv /tmp/PlkPlatform.exe /tmp/latest.json /www/wwwroot/platform.plkhealth.go.th/plkplatform/ && \
   echo 'Plkhe@lth00051' | sudo -S chown www:www /www/wwwroot/platform.plkhealth.go.th/plkplatform/PlkPlatform.exe /www/wwwroot/platform.plkhealth.go.th/plkplatform/latest.json && \
   sha256sum /www/wwwroot/platform.plkhealth.go.th/plkplatform/PlkPlatform.exe"
```

Verify the printed sha256 matches step 3.

### 6. Verify

- `https://platform.plkhealth.go.th/plkplatform/latest.json` returns the new version
- `https://platform.plkhealth.go.th/` landing page shows the new version (it reads `latest.json` client-side)
- Open an older `PlkPlatform.exe` → the auto-update dialog should appear

### Managing the backend service

```bash
sudo systemctl status plkplatform-web
sudo systemctl restart plkplatform-web
sudo journalctl -u plkplatform-web -f
```

Unit file: `/etc/systemd/system/plkplatform-web.service`.
