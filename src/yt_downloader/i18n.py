from __future__ import annotations

from locale import getlocale

TRANSLATIONS = {
    "en": {
        "app_title": "YT Download",
        "subtitle": "Paste one YouTube link per line. Press Enter to add multiple videos.",
        "url_placeholder": (
            "Add one YouTube link per line:\n"
            "https://www.youtube.com/watch?v=...\n"
            "https://youtu.be/..."
        ),
        "download_folder": "Download folder",
        "browse": "Browse",
        "parallel_downloads": "Parallel downloads",
        "download": "Download",
        "stop": "Stop",
        "status": "Status",
        "select_folder": "Select download folder",
        "no_links_title": "No links",
        "no_links_message": "Paste at least one YouTube link. Use Enter to add multiple links.",
        "download_stopped": "Download stopped.",
        "saving_to": "Saving to: {path}",
        "parallel_count": "Parallel downloads: {count}",
        "stopping": "Stopping after the current yt-dlp operation responds...",
        "error": "Error: {message}",
        "done": "Done.",
    },
    "ko": {
        "app_title": "YT Download",
        "subtitle": (
            "유튜브 링크를 한 줄에 하나씩 붙여넣으세요. "
            "Enter로 여러 영상을 추가할 수 있습니다."
        ),
        "url_placeholder": (
            "유튜브 링크를 한 줄에 하나씩 추가하세요:\n"
            "https://www.youtube.com/watch?v=...\n"
            "https://youtu.be/..."
        ),
        "download_folder": "다운로드 폴더",
        "browse": "찾아보기",
        "parallel_downloads": "동시 다운로드",
        "download": "다운로드",
        "stop": "중지",
        "status": "상태",
        "select_folder": "다운로드 폴더 선택",
        "no_links_title": "링크 없음",
        "no_links_message": (
            "유튜브 링크를 하나 이상 붙여넣으세요. "
            "Enter로 여러 링크를 추가할 수 있습니다."
        ),
        "download_stopped": "다운로드가 중지되었습니다.",
        "saving_to": "저장 위치: {path}",
        "parallel_count": "동시 다운로드: {count}",
        "stopping": "현재 yt-dlp 작업이 응답하면 중지합니다...",
        "error": "오류: {message}",
        "done": "완료.",
    },
}


def detect_language() -> str:
    locale_name = getlocale()[0] or ""
    if locale_name.lower().startswith("ko"):
        return "ko"
    return "en"


def get_texts(language: str | None = None) -> dict[str, str]:
    return TRANSLATIONS.get(language or detect_language(), TRANSLATIONS["en"])
