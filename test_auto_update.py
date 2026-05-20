from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from AutoUpdate_logic import parse_update_info


SCRIPT_PATH = Path(__file__).resolve().parent / "scripts" / "write_update_manifest.py"


class AutoUpdateManifestTests(unittest.TestCase):
    def _load_manifest_script(self) -> dict[str, object]:
        if not SCRIPT_PATH.exists():
            self.fail(f"Missing manifest writer script: {SCRIPT_PATH}")
        return runpy.run_path(str(SCRIPT_PATH))

    def test_parse_update_info_rejects_malformed_sha256(self) -> None:
        payload = (
            b'{"version":"1.0.9",'
            b'"url":"https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe",'
            b'"sha256":"5508c9a3abc7891db3b2b87177c88d0893e9b76cc4df1b15d9ee2b4db4f7986"}'
        )

        with self.assertRaisesRegex(ValueError, "sha256"):
            parse_update_info(payload)

    def test_manifest_writer_hashes_executable_bytes(self) -> None:
        namespace = self._load_manifest_script()
        build_manifest = namespace["build_manifest"]

        with tempfile.TemporaryDirectory() as temp_dir:
            executable_path = Path(temp_dir) / "PlkPlatform.exe"
            executable_bytes = b"new release executable"
            executable_path.write_bytes(executable_bytes)

            manifest = build_manifest(
                executable_path=executable_path,
                version="1.0.9",
                url="https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe",
                release_date="2026-05-20",
                notes="test notes",
            )

        self.assertEqual(manifest["version"], "1.0.9")
        self.assertEqual(manifest["url"], "https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe")
        self.assertEqual(manifest["sha256"], hashlib.sha256(executable_bytes).hexdigest())
        self.assertEqual(manifest["release_date"], "2026-05-20")
        self.assertEqual(manifest["notes"], "test notes")

    def test_manifest_writer_cli_runs_from_project_root(self) -> None:
        if not SCRIPT_PATH.exists():
            self.fail(f"Missing manifest writer script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as temp_dir:
            executable_path = Path(temp_dir) / "PlkPlatform.exe"
            output_path = Path(temp_dir) / "latest.json"
            executable_bytes = b"cli executable"
            executable_path.write_bytes(executable_bytes)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(executable_path),
                    "--output",
                    str(output_path),
                    "--version",
                    "1.0.9",
                    "--release-date",
                    "2026-05-20",
                    "--notes",
                    "cli notes",
                ],
                cwd=Path(__file__).resolve().parent,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["sha256"], hashlib.sha256(executable_bytes).hexdigest())
        self.assertEqual(manifest["notes"], "cli notes")


if __name__ == "__main__":
    unittest.main()
