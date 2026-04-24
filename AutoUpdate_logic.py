from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from version import UPDATE_MANIFEST_URL, VERSION


UPDATE_TIMEOUT_SECONDS = 20
DOWNLOAD_CHUNK_SIZE = 1024 * 512


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str
    sha256: str = ""
    release_date: str = ""
    notes: str = ""


@dataclass(frozen=True)
class DownloadedUpdate:
    info: UpdateInfo
    staged_path: Path


def is_packaged_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def current_executable_path() -> Path:
    if is_packaged_app():
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()


def app_update_dir() -> Path:
    base_dir = os.environ.get("PLK_UPDATE_DIR")
    if base_dir:
        path = Path(base_dir)
    else:
        path = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "PlkPlatform" / "updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def configured_manifest_url() -> str:
    if UPDATE_MANIFEST_URL:
        return UPDATE_MANIFEST_URL

    config_path = current_executable_path().parent / "update_config.json"
    if not config_path.exists():
        return ""

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get("manifest_url", "")).strip()


def normalize_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw_part in version.strip().lstrip("vV").split("."):
        digits = ""
        for char in raw_part:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits or "0"))
    return tuple(parts)


def is_newer_version(candidate: str, current: str = VERSION) -> bool:
    candidate_parts = normalize_version(candidate)
    current_parts = normalize_version(current)
    max_len = max(len(candidate_parts), len(current_parts))
    candidate_parts += (0,) * (max_len - len(candidate_parts))
    current_parts += (0,) * (max_len - len(current_parts))
    return candidate_parts > current_parts


def parse_update_info(payload: bytes) -> UpdateInfo:
    data = json.loads(payload.decode("utf-8"))
    version = str(data.get("version", "")).strip()
    url = str(data.get("url", "")).strip()
    if not version or not url:
        raise ValueError("update manifest must include version and url")
    return UpdateInfo(
        version=version,
        url=url,
        sha256=str(data.get("sha256", "")).strip().lower(),
        release_date=str(data.get("release_date", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
    )


def fetch_update_info(manifest_url: str) -> UpdateInfo:
    request = urllib.request.Request(
        manifest_url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"PlkPlatform/{VERSION}",
        },
    )
    with urllib.request.urlopen(request, timeout=UPDATE_TIMEOUT_SECONDS) as response:
        return parse_update_info(response.read())


def download_update(info: UpdateInfo) -> Path:
    update_dir = app_update_dir()
    suffix = Path(urllib.parse.urlparse(info.url).path).suffix or ".exe"
    staged_path = update_dir / f"PlkPlatform-{info.version}{suffix}"
    temp_path = staged_path.with_suffix(f"{staged_path.suffix}.download")

    digest = hashlib.sha256()
    request = urllib.request.Request(
        info.url,
        headers={"User-Agent": f"PlkPlatform/{VERSION}"},
    )
    with urllib.request.urlopen(request, timeout=UPDATE_TIMEOUT_SECONDS) as response:
        with temp_path.open("wb") as file:
            while True:
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
                file.write(chunk)

    actual_hash = digest.hexdigest()
    if info.sha256 and actual_hash != info.sha256:
        temp_path.unlink(missing_ok=True)
        raise ValueError("downloaded update checksum does not match manifest")

    temp_path.replace(staged_path)
    return staged_path


def write_windows_updater_script(target_path: Path, staged_path: Path) -> Path:
    def ps_literal(value: Path) -> str:
        return "'" + str(value).replace("'", "''") + "'"

    script_path = app_update_dir() / "apply_update.ps1"
    backup_path = target_path.with_suffix(f"{target_path.suffix}.old")
    log_path = app_update_dir() / "update.log"
    script_path.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$pidToWait = {os.getpid()}",
                f"$target = {ps_literal(target_path)}",
                f"$staged = {ps_literal(staged_path)}",
                f"$backup = {ps_literal(backup_path)}",
                f"$log = {ps_literal(log_path)}",
                "function Log($message) { Add-Content -Path $log -Value \"$(Get-Date -Format o) $message\" }",
                "try {",
                "  Wait-Process -Id $pidToWait -ErrorAction SilentlyContinue",
                "  Start-Sleep -Milliseconds 800",
                "  if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force }",
                "  if (Test-Path -LiteralPath $target) { Move-Item -LiteralPath $target -Destination $backup -Force }",
                "  Move-Item -LiteralPath $staged -Destination $target -Force",
                "  Log 'Update applied successfully.'",
                "} catch {",
                "  Log $_.Exception.Message",
                "  if ((Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $target)) {",
                "    Move-Item -LiteralPath $backup -Destination $target -Force",
                "  }",
                "  exit 1",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    return script_path


def launch_update_installer(staged_path: Path) -> bool:
    target_path = current_executable_path()
    if not is_packaged_app():
        return False

    script_path = write_windows_updater_script(target_path, staged_path)
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(script_path),
        ],
        close_fds=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return True


class AutoUpdateWorker(QObject):
    update_ready = pyqtSignal(object)
    no_update = pyqtSignal()
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, manifest_url: str) -> None:
        super().__init__()
        self.manifest_url = manifest_url

    def run(self) -> None:
        try:
            if not self.manifest_url:
                self.no_update.emit()
                return

            if not is_packaged_app() and os.environ.get("PLK_UPDATE_ALLOW_DEV") != "1":
                self.no_update.emit()
                return

            info = fetch_update_info(self.manifest_url)
            if not is_newer_version(info.version):
                self.no_update.emit()
                return

            staged_path = download_update(info)
            self.update_ready.emit(DownloadedUpdate(info=info, staged_path=staged_path))
        except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AutoUpdateController(QObject):
    update_ready = pyqtSignal(object)
    no_update = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, manifest_url: str | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manifest_url = manifest_url if manifest_url is not None else configured_manifest_url()
        self._thread: QThread | None = None
        self._worker: AutoUpdateWorker | None = None

    def check_in_background(self) -> None:
        if self._thread is not None:
            return

        self._thread = QThread(self)
        self._worker = AutoUpdateWorker(self.manifest_url)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.update_ready.connect(self.update_ready)
        self._worker.no_update.connect(self.no_update)
        self._worker.failed.connect(self.failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_thread)
        self._thread.start()

    def _clear_thread(self) -> None:
        self._thread = None
        self._worker = None
