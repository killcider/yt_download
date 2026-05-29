from PySide6.QtWidgets import QApplication

from yt_downloader.app import MainWindow, UrlProgress


def test_progress_bar_uses_average_url_progress() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.url_progress = {
        "https://example.test/1": UrlProgress(),
        "https://example.test/2": UrlProgress(),
    }

    window._update_url_progress("https://example.test/1", 50)
    assert window.progress_bar.value() == 25

    window._update_url_progress("https://example.test/2", 100)
    assert window.progress_bar.value() == 75

    app.quit()


def test_progress_does_not_move_backward_for_split_streams() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.url_progress = {"https://example.test/1": UrlProgress()}

    window._update_url_progress("https://example.test/1", 100)
    window._update_url_progress("https://example.test/1", 30)

    assert window.progress_bar.value() == 100
    assert window.url_progress["https://example.test/1"].percent == 100

    app.quit()


def test_finished_logs_failure_summary() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.url_progress = {
        "https://example.test/good": UrlProgress(percent=100, finished=True),
        "https://example.test/bad": UrlProgress(),
    }

    window._on_download_failures([("https://example.test/bad", "not available")])
    window._on_finished()

    log_text = [window.log_list.item(index).text() for index in range(window.log_list.count())]
    assert any("https://example.test/bad" in item and "not available" in item for item in log_text)
    assert any("1 succeeded, 1 failed" in item for item in log_text)

    app.quit()
