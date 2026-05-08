import os


VERSION = "1.0.6"
RELEASE = "2026-05-08"

# Endpoint must return JSON:
# {"version":"0.1.1","url":"https://.../PlkPlatform.exe","sha256":"optional"}
DEFAULT_UPDATE_MANIFEST_URL = "https://platform.plkhealth.go.th/plkplatform/latest.json"
UPDATE_MANIFEST_URL = (
    os.environ.get("PLK_UPDATE_MANIFEST_URL", "").strip()
    or DEFAULT_UPDATE_MANIFEST_URL
)
