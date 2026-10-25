"""Safe acquisition of the public C-MAPSS ZIP archive."""

from __future__ import annotations

import hashlib
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from prescriptxai import __version__

LOGGER = logging.getLogger(__name__)
_CHUNK_SIZE = 1024 * 1024


class DatasetDownloadError(RuntimeError):
    """Raised when retrieval fails, with manual recovery instructions in its message."""


def verify_archive(path: Path, expected_sha256: str | None = None) -> str:
    """Verify ZIP CRCs and optional SHA-256, returning the locally computed digest."""
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
        raise DatasetDownloadError(
            f"SHA-256 mismatch for {path}: expected {expected_sha256}, observed {digest}"
        )
    try:
        with zipfile.ZipFile(path) as archive:
            if not archive.namelist():
                raise DatasetDownloadError(f"ZIP archive is empty: {path}")
            corrupt = archive.testzip()
            if corrupt is not None:
                raise DatasetDownloadError(f"ZIP CRC check failed for member {corrupt!r}")
            nested_name = next(
                (name for name in archive.namelist() if Path(name).name == "CMAPSSData.zip"),
                None,
            )
            if nested_name is not None:
                with zipfile.ZipFile(BytesIO(archive.read(nested_name))) as nested:
                    if not nested.namelist() or nested.testzip() is not None:
                        raise DatasetDownloadError("nested CMAPSSData.zip failed integrity checks")
    except zipfile.BadZipFile as error:
        raise DatasetDownloadError(f"not a valid C-MAPSS ZIP archive: {path}") from error
    return digest


def download_archive(
    url: str,
    destination: Path,
    timeout_seconds: int,
    expected_sha256: str | None = None,
) -> Path:
    """Download a ZIP archive to disk and verify its central directory.

    Parameters
    ----------
    url:
        Configured HTTP(S) URL of the dataset archive.
    destination:
        Destination path under the configured raw-data directory.
    timeout_seconds:
        Network timeout supplied by application configuration.

    Returns
    -------
    Path
        The verified archive path.
    """
    if not url.startswith(("https://", "http://")):
        raise ValueError("dataset URL must use HTTP or HTTPS")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": f"prescriptxai/{__version__}"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response, partial.open("wb") as output:
            while chunk := response.read(_CHUNK_SIZE):
                output.write(chunk)
        if not zipfile.is_zipfile(partial):
            raise DatasetDownloadError(f"downloaded file is not a valid ZIP archive: {url}")
        verify_archive(partial, expected_sha256)
        partial.replace(destination)
    except (HTTPError, URLError, TimeoutError, OSError, zipfile.BadZipFile) as error:
        partial.unlink(missing_ok=True)
        raise DatasetDownloadError(
            _manual_download_message(
                url, destination, f"failed to download or verify dataset: {error}"
            )
        ) from error
    except DatasetDownloadError as error:
        partial.unlink(missing_ok=True)
        if "Save the downloaded archive" in str(error):
            raise
        raise DatasetDownloadError(
            _manual_download_message(url, destination, str(error))
        ) from error
    LOGGER.info("Downloaded and verified C-MAPSS archive at %s", destination)
    return destination


def _manual_download_message(url: str, destination: Path, reason: str) -> str:
    """Provide explicit next steps without substituting generated or synthetic data."""
    return (
        f"{reason}. Manual download required. Download NASA C-MAPSS from the configured "
        f"source ({url}) or the NASA Prognostics Center of Excellence C-MAPSS dataset page. "
        f"Save the original ZIP archive as {destination}; do not unpack individual files. "
        "Then rerun `prescriptxai data prepare --subset FD001`. No substitute data was created."
    )
