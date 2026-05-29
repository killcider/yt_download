from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from threading import Event

import imageio_ffmpeg
import yt_dlp


class DownloadCancelled(Exception):
    """Raised when the user stops the current download batch."""


ProgressCallback = Callable[[str, str, float | None], None]

QUALITY_FORMATS = {
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best",
    "2160p": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]/best",
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
}


def normalize_quality(quality: str) -> str:
    return quality if quality in QUALITY_FORMATS else "720p"


class YoutubeDownloader:
    def __init__(
        self,
        output_dir: Path,
        progress_callback: ProgressCallback,
        max_workers: int = 4,
        quality: str = "720p",
    ) -> None:
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self.max_workers = max(1, min(max_workers, 8))
        self.quality = normalize_quality(quality)
        self.cancel_requested = Event()

    def cancel(self) -> None:
        self.cancel_requested.set()

    def download_many(self, urls: list[str]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not urls:
            return

        queued: list[str] = []
        for index, url in enumerate(urls, start=1):
            self.progress_callback(url, f"Starting {index}/{len(urls)}", None)
            queued.append(url)

        failures: list[tuple[str, str]] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(queued))) as executor:
            pending = {executor.submit(self._download_one, url): url for url in queued}
            while pending:
                if self.cancel_requested.is_set():
                    for future in pending:
                        future.cancel()
                    raise DownloadCancelled

                done, _ = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
                for future in done:
                    url = pending.pop(future)
                    try:
                        future.result()
                    except DownloadCancelled:
                        self.cancel()
                    except Exception as exc:
                        failures.append((url, str(exc)))
                        self.progress_callback(url, f"Failed: {exc}", None)

        if self.cancel_requested.is_set():
            raise DownloadCancelled

        if failures:
            failed_list = "\n".join(f"- {url}: {message}" for url, message in failures)
            raise RuntimeError(f"{len(failures)} download(s) failed:\n{failed_list}")

    def _download_one(self, url: str) -> None:
        options = {
            "format": QUALITY_FORMATS[self.quality],
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "merge_output_format": "mp4",
            "noplaylist": True,
            "outtmpl": str(self.output_dir / "%(title).200B.%(ext)s"),
            "progress_hooks": [lambda status: self._handle_progress(url, status)],
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

    def _handle_progress(self, url: str, status: dict) -> None:
        if self.cancel_requested.is_set():
            raise DownloadCancelled

        state = status.get("status")
        if state == "downloading":
            downloaded = status.get("downloaded_bytes") or 0
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            percent = (downloaded / total * 100) if total else None
            speed = status.get("_speed_str", "").strip()
            eta = status.get("_eta_str", "").strip()
            detail = "Downloading"
            if speed:
                detail += f" | {speed}"
            if eta:
                detail += f" | ETA {eta}"
            self.progress_callback(url, detail, percent)
        elif state == "finished":
            filename = Path(status.get("filename", "")).name
            detail = f"Finished: {filename}" if filename else "Finished"
            self.progress_callback(url, detail, 100.0)


def parse_urls(text: str) -> list[str]:
    urls: list[str] = []
    for raw_line in text.splitlines():
        value = raw_line.strip()
        if not value:
            continue
        urls.extend(part.strip() for part in value.split() if part.strip())
    return urls
