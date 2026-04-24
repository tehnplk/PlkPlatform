import os


VERSION = "0.1.0"
RELEASE = "2026-04-24"

# Endpoint must return JSON:
# {"version":"0.1.1","url":"https://.../PlkPlatform.exe","sha256":"optional"}
UPDATE_MANIFEST_URL = os.environ.get("PLK_UPDATE_MANIFEST_URL", "").strip()
