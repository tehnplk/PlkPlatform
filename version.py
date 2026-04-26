import os


VERSION = "0.1.8"
RELEASE = "2026-04-26"

# Endpoint must return JSON:
# {"version":"0.1.1","url":"https://.../PlkPlatform.exe","sha256":"optional"}
DEFAULT_UPDATE_MANIFEST_URL = "https://platform.plkhealth.go.th/plkplatform/latest.json"
UPDATE_MANIFEST_URL = (
    os.environ.get("PLK_UPDATE_MANIFEST_URL", "").strip()
    or DEFAULT_UPDATE_MANIFEST_URL
)
