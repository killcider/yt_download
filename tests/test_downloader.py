from threading import Lock
from time import sleep

from yt_downloader.downloader import (
    QUALITY_FORMATS,
    YoutubeDownloader,
    normalize_quality,
    parse_urls,
)


def test_downloader_runs_up_to_configured_parallel_limit(tmp_path) -> None:
    active = 0
    peak = 0
    lock = Lock()

    def fake_download(_url: str) -> None:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        sleep(0.05)
        with lock:
            active -= 1

    downloader = YoutubeDownloader(tmp_path, lambda *_args: None, max_workers=4)
    downloader._download_one = fake_download

    downloader.download_many([f"https://example.test/{index}" for index in range(8)])

    assert peak == 4


def test_downloader_clamps_parallel_limit(tmp_path) -> None:
    assert YoutubeDownloader(tmp_path, lambda *_args: None, max_workers=0).max_workers == 1
    assert YoutubeDownloader(tmp_path, lambda *_args: None, max_workers=20).max_workers == 8


def test_downloader_normalizes_quality(tmp_path) -> None:
    assert YoutubeDownloader(tmp_path, lambda *_args: None, quality="1080p").quality == "1080p"
    assert YoutubeDownloader(tmp_path, lambda *_args: None, quality="bad").quality == "720p"


def test_quality_formats_are_pixel_limited() -> None:
    assert "height<=720" in QUALITY_FORMATS["720p"]
    assert "height<=1080" in QUALITY_FORMATS["1080p"]
    assert "height<=2160" in QUALITY_FORMATS["2160p"]
    assert normalize_quality("best") == "best"


def test_parse_urls_accepts_lines_and_whitespace() -> None:
    text = "https://a.example/watch?v=1\n\n https://b.example/x https://c.example/y "

    assert parse_urls(text) == [
        "https://a.example/watch?v=1",
        "https://b.example/x",
        "https://c.example/y",
    ]
