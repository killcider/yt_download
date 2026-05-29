from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event

import imageio_ffmpeg
import yt_dlp


class DownloadCancelled(Exception):
    """Raised when the user stops the current download batch."""


class DownloadFailed(Exception):
    def __init__(self, failures: list[tuple[str, str]]) -> None:
        super().__init__(f"{len(failures)} download(s) failed")
        self.failures = failures


ProgressCallback = Callable[[str, str, float | None], None]

QUALITY_FORMATS = {
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best",
    "2160p": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]/best",
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
}


def normalize_quality(quality: str) -> str:
    return quality if quality in QUALITY_FORMATS else "720p"


@dataclass
class ComponentProgress:
    downloaded: float = 0.0
    total: float | None = None


@dataclass
class AggregateProgress:
    expected_total: float | None = None
    components: dict[str, ComponentProgress] = field(default_factory=dict)

    def update(self, key: str, downloaded: float, total: float | None) -> float | None:
        component = self.components.setdefault(key, ComponentProgress())
        component.downloaded = max(component.downloaded, downloaded)
        component.total = total or component.total

        if self.expected_total:
            downloaded_total = sum(item.downloaded for item in self.components.values())
            return min(100.0, downloaded_total / self.expected_total * 100)

        component_percents = [
            min(100.0, item.downloaded / item.total * 100)
            for item in self.components.values()
            if item.total
        ]
        if not component_percents:
            return None
        return sum(component_percents) / len(component_percents)


def expected_total_bytes(info: dict) -> float | None:
    requested_formats = info.get("requested_formats") or []
    if requested_formats:
        totals = [
            item.get("filesize") or item.get("filesize_approx")
            for item in requested_formats
            if item.get("filesize") or item.get("filesize_approx")
        ]
        return float(sum(totals)) if totals else None

    total = info.get("filesize") or info.get("filesize_approx")
    return float(total) if total else None


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
            raise DownloadFailed(failures)

    def _download_one(self, url: str) -> None:
        options = {
            "format": QUALITY_FORMATS[self.quality],
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "merge_output_format": "mp4",
            "noplaylist": True,
            "outtmpl": str(self.output_dir / "%(title).200B.%(ext)s"),
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            aggregate = AggregateProgress(expected_total_bytes(info))
            ydl.add_progress_hook(lambda status: self._handle_progress(url, status, aggregate))
            ydl.download([url])
            self.progress_callback(url, "Finished", 100.0)

    def _handle_progress(self, url: str, status: dict, aggregate: AggregateProgress) -> None:
        if self.cancel_requested.is_set():
            raise DownloadCancelled

        state = status.get("status")
        if state == "downloading":
            downloaded = status.get("downloaded_bytes") or 0
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            component_key = status.get("filename") or status.get("tmpfilename") or url
            percent = aggregate.update(
                str(component_key),
                float(downloaded),
                float(total) if total else None,
            )
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
            component_key = status.get("filename") or status.get("tmpfilename") or url
            downloaded = status.get("downloaded_bytes") or status.get("total_bytes") or 0
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            percent = aggregate.update(
                str(component_key),
                float(downloaded),
                float(total) if total else None,
            )
            detail = f"Finished part: {filename}" if filename else "Finished part"
            self.progress_callback(url, detail, percent)


def parse_urls(text: str) -> list[str]:
    urls: list[str] = []
    for raw_line in text.splitlines():
        value = raw_line.strip()
        if not value:
            continue
        urls.extend(part.strip() for part in value.split() if part.strip())
    return urls
