from pathlib import Path

from yt_downloader.paths import default_download_dir


def test_default_download_dir_uses_home_when_no_download_folder(tmp_path: Path) -> None:
    assert default_download_dir(tmp_path) == tmp_path


def test_default_download_dir_prefers_downloads(tmp_path: Path) -> None:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    assert default_download_dir(tmp_path) == downloads

