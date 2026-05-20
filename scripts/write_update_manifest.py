from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from version import RELEASE, VERSION


DEFAULT_URL = "https://platform.plkhealth.go.th/plkplatform/PlkPlatform.exe"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    executable_path: Path,
    version: str,
    url: str,
    release_date: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "version": version,
        "url": url,
        "sha256": file_sha256(executable_path),
        "release_date": release_date,
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write latest.json for PlkPlatform auto update."
    )
    parser.add_argument(
        "executable",
        nargs="?",
        default="dist/PlkPlatform.exe",
        help="Path to built PlkPlatform.exe.",
    )
    parser.add_argument(
        "--output",
        default="dist/latest.json",
        help="Path to write latest.json.",
    )
    parser.add_argument("--version", default=VERSION, help="Release version.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Download URL in manifest.")
    parser.add_argument(
        "--release-date",
        default=RELEASE or date.today().isoformat(),
        help="Release date in YYYY-MM-DD format.",
    )
    parser.add_argument("--notes", default="", help="Release notes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    executable_path = Path(args.executable)
    output_path = Path(args.output)

    manifest = build_manifest(
        executable_path=executable_path,
        version=args.version,
        url=args.url,
        release_date=args.release_date,
        notes=args.notes,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_path} with sha256 {manifest['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
