from __future__ import annotations

from locale import getlocale

TRANSLATIONS = {
    "en": {
        "app_title": "Social Video Download",
        "subtitle": "Paste one YouTube, TikTok, or Instagram link per line.",
        "url_placeholder": (
            "Add one video link per line:\n"
            "https://www.youtube.com/watch?v=...\n"
            "https://www.tiktok.com/@user/video/...\n"
            "https://www.instagram.com/reel/..."
        ),
        "download_folder": "Download folder",
        "browse": "Browse",
        "parallel_downloads": "Parallel downloads",
        "quality": "Quality",
        "quality_720p": "720p",
        "quality_1080p": "1080p",
        "quality_2160p": "4K (2160p)",
        "quality_best": "Best available",
        "download": "Download",
        "stop": "Stop",
        "status": "Status",
        "select_folder": "Select download folder",
        "no_links_title": "No links",
        "no_links_message": "Paste at least one YouTube, TikTok, or Instagram link.",
        "download_stopped": "Download stopped.",
        "saving_to": "Saving to: {path}",
        "parallel_count": "Parallel downloads: {count}",
        "selected_quality": "Quality: {quality}",
        "stopping": "Stopping after the current yt-dlp operation responds...",
        "error": "Error: {message}",
        "download_failed_item": "Failed: {url} | Reason: {reason}",
        "summary_success": "Completed: {count} download(s) succeeded.",
        "summary_with_failures": "Completed: {success} succeeded, {failed} failed.",
        "done": "Done.",
    },
    "ko": {
        "app_title": "Social Video Download",
        "subtitle": "유튜브, 틱톡, 인스타그램 링크를 한 줄에 하나씩 붙여넣으세요.",
        "url_placeholder": (
            "영상 링크를 한 줄에 하나씩 추가하세요:\n"
            "https://www.youtube.com/watch?v=...\n"
            "https://www.tiktok.com/@user/video/...\n"
            "https://www.instagram.com/reel/..."
        ),
        "download_folder": "다운로드 폴더",
        "browse": "찾아보기",
        "parallel_downloads": "동시 다운로드",
        "quality": "화질",
        "quality_720p": "720p",
        "quality_1080p": "1080p",
        "quality_2160p": "4K (2160p)",
        "quality_best": "최고화질",
        "download": "다운로드",
        "stop": "중지",
        "status": "상태",
        "select_folder": "다운로드 폴더 선택",
        "no_links_title": "링크 없음",
        "no_links_message": "유튜브, 틱톡, 인스타그램 링크를 하나 이상 붙여넣으세요.",
        "download_stopped": "다운로드가 중지되었습니다.",
        "saving_to": "저장 위치: {path}",
        "parallel_count": "동시 다운로드: {count}",
        "selected_quality": "화질: {quality}",
        "stopping": "현재 yt-dlp 작업이 응답하면 중지합니다...",
        "error": "오류: {message}",
        "download_failed_item": "실패: {url} | 이유: {reason}",
        "summary_success": "완료: {count}개 다운로드 성공.",
        "summary_with_failures": "완료: {success}개 성공, {failed}개 실패.",
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
