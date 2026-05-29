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

