from __future__ import annotations

import sys
import dis
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader

from version import VERSION


def extract_embedded_version(executable_path: Path) -> str:
    archive = CArchiveReader(str(executable_path))
    pyz_entry = archive.toc.get("PYZ.pyz")
    if pyz_entry is None:
        raise RuntimeError("PYZ.pyz not found in executable")

    pyz_offset = archive._start_offset + pyz_entry[0]
    pyz = ZlibArchiveReader(str(executable_path), pyz_offset)
    code = pyz.extract("version")

    previous_instruction = None
    for instruction in dis.get_instructions(code):
        if (
            instruction.opname == "STORE_NAME"
            and instruction.argval == "VERSION"
            and previous_instruction is not None
            and previous_instruction.opname == "LOAD_CONST"
        ):
            return str(previous_instruction.argval)
        previous_instruction = instruction

    raise RuntimeError("VERSION constant not found in executable")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts\\verify_pyinstaller_version.py dist\\PlkPlatform.exe")
        return 2

    executable_path = Path(sys.argv[1])
    embedded_version = extract_embedded_version(executable_path)
    if embedded_version != VERSION:
        print(f"ERROR: {executable_path} embeds VERSION {embedded_version}, expected {VERSION}")
        return 1

    print(f"OK: {executable_path} embeds VERSION {embedded_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
