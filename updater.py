"""Consulta e baixa atualizações publicadas nas Releases do GitHub."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen


GITHUB_REPOSITORY = "arthurmxs/MergePdf"
INSTALLER_ASSET_NAME = "MergePdf-Setup.exe"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
REQUEST_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "MergePdf-updater",
}


class UpdateError(RuntimeError):
    """Raised when an update cannot be checked or downloaded."""


@dataclass(frozen=True)
class Release:
    """A release that has a compatible Windows installer."""

    version: str
    installer_url: str
    installer_size: int


def version_key(version: str) -> tuple[int, ...]:
    """Turn a tag such as ``v1.2.0`` into numbers suitable for comparison."""
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)", version.strip())
    if not match:
        raise ValueError(f"Versão inválida: {version!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(remote_version: str, current_version: str) -> bool:
    """Return whether the GitHub release is newer than the installed app."""
    remote = version_key(remote_version)
    current = version_key(current_version)
    size = max(len(remote), len(current))
    return remote + (0,) * (size - len(remote)) > current + (0,) * (size - len(current))


def get_latest_release() -> Release | None:
    """Get the latest non-draft release and its installer asset from GitHub."""
    try:
        request = Request(LATEST_RELEASE_URL, headers=REQUEST_HEADERS)
        with urlopen(request, timeout=5) as response:
            payload = json.load(response)
    except (URLError, OSError, json.JSONDecodeError) as error:
        raise UpdateError("Não foi possível verificar atualizações.") from error

    if payload.get("draft") or payload.get("prerelease"):
        return None

    for asset in payload.get("assets", []):
        if asset.get("name") == INSTALLER_ASSET_NAME and asset.get("browser_download_url"):
            return Release(
                version=str(payload.get("tag_name", "")),
                installer_url=str(asset["browser_download_url"]),
                installer_size=int(asset.get("size", 0)),
            )
    return None


def download_installer(release: Release) -> Path:
    """Download a release installer into the temporary folder and return its path."""
    destination = Path(tempfile.gettempdir()) / f"MergePdf-{release.version}-Setup.exe"
    temporary_file = destination.with_suffix(".download")
    try:
        request = Request(release.installer_url, headers=REQUEST_HEADERS)
        with urlopen(request, timeout=30) as response, temporary_file.open("wb") as output_file:
            while chunk := response.read(1024 * 1024):
                output_file.write(chunk)
        if release.installer_size and temporary_file.stat().st_size != release.installer_size:
            raise UpdateError("O instalador baixado está incompleto.")
        temporary_file.replace(destination)
    except (URLError, OSError) as error:
        temporary_file.unlink(missing_ok=True)
        raise UpdateError("Não foi possível baixar a atualização.") from error
    return destination
