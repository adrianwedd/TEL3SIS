from __future__ import annotations

from pathlib import Path
from typing import Tuple

import requests


DEFAULT_OUTPUT_DIR = Path("recordings/audio")


def download_recording(
    url: str, *, output_dir: Path = DEFAULT_OUTPUT_DIR, auth: Tuple[str, str]
) -> Path:
    """Download a Twilio recording URL to the given directory.

    Parameters
    ----------
    url: str
        The Twilio recording URL, without file extension.
    output_dir: Path, optional
        Directory where the audio file will be saved. Defaults to ``recordings/audio``.
    auth: Tuple[str, str]
        Tuple of ``(account_sid, auth_token)`` for HTTP basic auth.

    Returns
    -------
    Path
        Path to the downloaded recording file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = url.rstrip("/").split("/")[-1] + ".mp3"
    file_path = output_dir / file_name
    response = requests.get(f"{url}.mp3", auth=auth, timeout=10)
    response.raise_for_status()
    file_path.write_bytes(response.content)
    return file_path
