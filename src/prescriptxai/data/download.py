"""Safe acquisition of the public C-MAPSS ZIP archive."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)
_CHUNK_SIZE = 1024 * 1024


class DatasetDownloadError(RuntimeError):
    """Raised when the configured dataset cannot be downloaded or verified."""


def download_archive(url: str, destination: Path, timeout_seconds: int) -> Path:
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
    request = Request(url, headers={"User-Agent": "prescriptxai/0.1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response, partial.open("wb") as output:
            while chunk := response.read(_CHUNK_SIZE):
                output.write(chunk)
        if not zipfile.is_zipfile(partial):
            raise DatasetDownloadError(f"downloaded file is not a valid ZIP archive: {url}")
        with zipfile.ZipFile(partial) as archive:
            if not archive.namelist():
                raise DatasetDownloadError(f"downloaded ZIP archive is empty: {url}")
        partial.replace(destination)
    except (HTTPError, URLError, TimeoutError, OSError, zipfile.BadZipFile) as error:
        partial.unlink(missing_ok=True)
        raise DatasetDownloadError(f"failed to download or verify dataset from {url}") from error
    except DatasetDownloadError:
        partial.unlink(missing_ok=True)
        raise
    LOGGER.info("Downloaded and verified C-MAPSS archive at %s", destination)
    return destination
