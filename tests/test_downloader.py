from threading import Lock
from time import sleep

from yt_downloader.downloader import (
    QUALITY_FORMATS,
    SOCIAL_FORMAT,
    YOUTUBE_EXTRACTOR_ARGS,
    AggregateProgress,
    DownloadFailed,
    MediaDownloader,
    detect_platform,
    expected_total_bytes,
    format_for_url,
    normalize_quality,
    normalized_download_url,
    parse_urls,
    youtube_video_id,
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

    downloader = MediaDownloader(tmp_path, lambda *_args: None, max_workers=4)
    downloader._download_one = fake_download

    downloader.download_many([f"https://example.test/{index}" for index in range(8)])

    assert peak == 4


def test_downloader_clamps_parallel_limit(tmp_path) -> None:
    assert MediaDownloader(tmp_path, lambda *_args: None, max_workers=0).max_workers == 1
    assert MediaDownloader(tmp_path, lambda *_args: None, max_workers=20).max_workers == 8


def test_downloader_normalizes_quality(tmp_path) -> None:
    assert MediaDownloader(tmp_path, lambda *_args: None, quality="1080p").quality == "1080p"
    assert MediaDownloader(tmp_path, lambda *_args: None, quality="bad").quality == "720p"


def test_quality_formats_are_pixel_limited() -> None:
    assert "height<=720" in QUALITY_FORMATS["720p"]
    assert "height<=1080" in QUALITY_FORMATS["1080p"]
    assert "height<=2160" in QUALITY_FORMATS["2160p"]
    assert normalize_quality("best") == "best"


def test_detect_platform_from_common_social_domains() -> None:
    assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
    assert detect_platform("https://youtu.be/abc") == "youtube"
    assert detect_platform("https://vm.tiktok.com/abc") == "tiktok"
    assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"
    assert detect_platform("https://www.instagram.com/reel/abc/") == "instagram"
    assert detect_platform("https://example.test/video") == "generic"


def test_format_for_url_keeps_youtube_quality_and_uses_social_best() -> None:
    assert (
        format_for_url("https://www.youtube.com/watch?v=abc", "1080p")
        == QUALITY_FORMATS["1080p"]
    )
    assert format_for_url("https://www.tiktok.com/@user/video/123", "1080p") == SOCIAL_FORMAT
    assert format_for_url("https://www.instagram.com/reel/abc/", "2160p") == SOCIAL_FORMAT


def test_youtube_video_id_accepts_watch_short_embed_and_share_urls() -> None:
    assert youtube_video_id("https://www.youtube.com/watch?v=abc123&list=PL") == "abc123"
    assert youtube_video_id("https://youtu.be/abc123?si=share") == "abc123"
    assert youtube_video_id("https://www.youtube.com/shorts/abc123") == "abc123"
    assert youtube_video_id("https://www.youtube.com/embed/abc123") == "abc123"
    assert youtube_video_id("https://www.youtube-nocookie.com/embed/abc123") == "abc123"


def test_normalized_download_url_uses_watch_url_for_youtube_only() -> None:
    assert (
        normalized_download_url("https://www.youtube.com/embed/abc123?start=10")
        == "https://www.youtube.com/watch?v=abc123"
    )
    assert (
        normalized_download_url("https://www.tiktok.com/@user/video/123")
        == "https://www.tiktok.com/@user/video/123"
    )


def test_youtube_extractor_args_include_restricted_video_fallback_clients() -> None:
    clients = YOUTUBE_EXTRACTOR_ARGS["youtube"]["player_client"]

    assert "default" in clients
    assert "web_embedded" in clients
    assert "mweb" in clients
    assert "android" in clients
    assert "ios" in clients
    assert "tv" in clients


def test_expected_total_bytes_sums_split_streams() -> None:
    info = {
        "requested_formats": [
            {"filesize": 100},
            {"filesize_approx": 25},
        ]
    }

    assert expected_total_bytes(info) == 125


def test_aggregate_progress_groups_video_and_audio_components() -> None:
    progress = AggregateProgress(expected_total=125)

    assert progress.update("video", 100, 100) == 80
    assert progress.update("audio", 12.5, 25) == 90
    assert progress.update("audio", 25, 25) == 100


def test_download_many_raises_structured_failures(tmp_path) -> None:
    downloader = MediaDownloader(tmp_path, lambda *_args: None)

    def fake_download(url: str) -> None:
        if url.endswith("/bad"):
            raise RuntimeError("not available")

    downloader._download_one = fake_download

    try:
        downloader.download_many(["https://example.test/good", "https://example.test/bad"])
    except DownloadFailed as exc:
        assert exc.failures == [("https://example.test/bad", "not available")]
    else:
        raise AssertionError("Expected DownloadFailed")


def test_parse_urls_accepts_lines_and_whitespace() -> None:
    text = "https://a.example/watch?v=1\n\n https://b.example/x https://c.example/y "

    assert parse_urls(text) == [
        "https://a.example/watch?v=1",
        "https://b.example/x",
        "https://c.example/y",
    ]
