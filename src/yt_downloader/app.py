from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from yt_downloader.downloader import DownloadCancelled, YoutubeDownloader, parse_urls
from yt_downloader.paths import default_download_dir, ensure_directory


class DownloadWorker(QObject):
    progress = Signal(str, str, object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, urls: list[str], output_dir: Path, max_workers: int) -> None:
        super().__init__()
        self.downloader = YoutubeDownloader(output_dir, self.progress.emit, max_workers)
        self.urls = urls

    @Slot()
    def run(self) -> None:
        try:
            self.downloader.download_many(self.urls)
        except DownloadCancelled:
            self.failed.emit("Download stopped.")
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    def cancel(self) -> None:
        self.downloader.cancel()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.thread: QThread | None = None
        self.worker: DownloadWorker | None = None

        self.setWindowTitle("YT Download")
        self.setMinimumSize(860, 620)
        self._build_ui()
        self._set_busy(False)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("YT Download")
        title.setObjectName("Title")
        subtitle = QLabel("Paste one or more YouTube links and download them by video title.")
        subtitle.setObjectName("Subtitle")

        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")
        self.url_input.setMinimumHeight(150)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit(str(default_download_dir()))
        self.folder_input.setPlaceholderText("Download folder")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._select_folder)
        folder_row.addWidget(self.folder_input, 1)
        folder_row.addWidget(browse_button)

        concurrency_row = QHBoxLayout()
        concurrency_label = QLabel("Parallel downloads")
        self.concurrency_input = QSpinBox()
        self.concurrency_input.setRange(1, 8)
        self.concurrency_input.setValue(4)
        concurrency_row.addWidget(concurrency_label)
        concurrency_row.addWidget(self.concurrency_input)
        concurrency_row.addStretch(1)

        button_row = QHBoxLayout()
        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("PrimaryButton")
        self.download_button.clicked.connect(self._start_download)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_download)
        button_row.addStretch(1)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.download_button)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("Divider")

        status_label = QLabel("Status")
        status_label.setObjectName("SectionLabel")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.log_list = QListWidget()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.url_input)
        layout.addLayout(folder_row)
        layout.addLayout(concurrency_row)
        layout.addLayout(button_row)
        layout.addWidget(divider)
        layout.addWidget(status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_list, 1)

        self.setCentralWidget(root)

    def _select_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select download folder",
            self.folder_input.text(),
        )
        if selected:
            self.folder_input.setText(selected)

    def _start_download(self) -> None:
        urls = parse_urls(self.url_input.toPlainText())
        if not urls:
            QMessageBox.warning(self, "No links", "Paste at least one YouTube link.")
            return

        output_dir = ensure_directory(Path(self.folder_input.text()).expanduser())
        self.folder_input.setText(str(output_dir))
        self.log_list.clear()
        self.progress_bar.setValue(0)
        self._log(f"Saving to: {output_dir}")
        self._log(f"Parallel downloads: {self.concurrency_input.value()}")

        self.thread = QThread(self)
        self.worker = DownloadWorker(urls, output_dir, self.concurrency_input.value())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_thread)
        self._set_busy(True)
        self.thread.start()

    def _stop_download(self) -> None:
        if self.worker:
            self.worker.cancel()
            self._log("Stopping after the current yt-dlp operation responds...")

    @Slot(str, str, object)
    def _on_progress(self, url: str, message: str, percent: object) -> None:
        if isinstance(percent, float | int):
            self.progress_bar.setValue(max(0, min(100, int(percent))))
        self._log(f"{message} | {url}")

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._log(f"Error: {message}")

    @Slot()
    def _on_finished(self) -> None:
        self._set_busy(False)
        self._log("Done.")

    @Slot()
    def _clear_thread(self) -> None:
        self.thread = None
        self.worker = None

    def _set_busy(self, busy: bool) -> None:
        self.download_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.url_input.setEnabled(not busy)
        self.folder_input.setEnabled(not busy)
        self.concurrency_input.setEnabled(not busy)

    def _log(self, message: str) -> None:
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()


def apply_dark_theme(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QWidget {
            background: #121418;
            color: #e7eaf0;
            font-size: 14px;
        }
        #Title {
            font-size: 30px;
            font-weight: 700;
        }
        #Subtitle {
            color: #9ba4b3;
            margin-bottom: 6px;
        }
        #SectionLabel {
            color: #c5cad3;
            font-weight: 700;
        }
        QPlainTextEdit, QLineEdit, QListWidget, QSpinBox {
            background: #1b1f27;
            border: 1px solid #343a46;
            border-radius: 8px;
            padding: 10px;
            selection-background-color: #3478f6;
        }
        QPushButton {
            background: #252b35;
            border: 1px solid #3c4452;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: #303746;
        }
        QPushButton:disabled {
            color: #697181;
            background: #1b1f27;
        }
        #PrimaryButton {
            background: #2f7df6;
            border-color: #2f7df6;
            color: white;
        }
        #PrimaryButton:hover {
            background: #4a91ff;
        }
        QProgressBar {
            background: #1b1f27;
            border: 1px solid #343a46;
            border-radius: 8px;
            height: 22px;
            text-align: center;
        }
        QProgressBar::chunk {
            background: #2f7df6;
            border-radius: 7px;
        }
        #Divider {
            color: #2b313c;
        }
        """
    )


def main() -> int:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
