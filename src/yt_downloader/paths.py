from __future__ import annotations

import os
import sys
from pathlib import Path


def default_download_dir(home: Path | None = None) -> Path:
    home = home or Path.home()

    if sys.platform.startswith("win"):
        user_profile = Path(os.environ.get("USERPROFILE", str(home)))
        downloads = user_profile / "Downloads"
        return downloads if downloads.exists() else user_profile

    candidates = [
        Path(os.environ["XDG_DOWNLOAD_DIR"]).expanduser()
        if os.environ.get("XDG_DOWNLOAD_DIR")
        else None,
        home / "Downloads",
        home / "다운로드",
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    return home


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

