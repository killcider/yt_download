from yt_downloader.i18n import get_texts


def test_get_texts_falls_back_to_english_for_unknown_language() -> None:
    assert get_texts("unknown")["download"] == "Download"


def test_get_texts_supports_korean() -> None:
    assert get_texts("ko")["download"] == "다운로드"

