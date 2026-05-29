from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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
from yt_downloader.i18n import get_texts
from yt_downloader.paths import default_download_dir, ensure_directory

QUALITY_CHOICES = [
    ("720p", "quality_720p"),
    ("1080p", "quality_1080p"),
    ("2160p", "quality_2160p"),
    ("best", "quality_best"),
]


class DownloadWorker(QObject):
    progress = Signal(str, str, object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        urls: list[str],
        output_dir: Path,
        max_workers: int,
        quality: str,
    ) -> None:
        super().__init__()
        texts = get_texts()
        self.downloader = YoutubeDownloader(output_dir, self.progress.emit, max_workers, quality)
        self.urls = urls
        self.download_stopped = texts["download_stopped"]

    @Slot()
    def run(self) -> None:
        try:
            self.downloader.download_many(self.urls)
        except DownloadCancelled:
            self.failed.emit(self.download_stopped)
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
        self.texts = get_texts()

        self.setWindowTitle(self.texts["app_title"])
        self.setMinimumSize(860, 620)
        self._build_ui()
        self._set_busy(False)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel(self.texts["app_title"])
        title.setObjectName("Title")
        subtitle = QLabel(self.texts["subtitle"])
        subtitle.setWordWrap(True)
        subtitle.setObjectName("Subtitle")

        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(self.texts["url_placeholder"])
        self.url_input.setMinimumHeight(150)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit(str(default_download_dir()))
        self.folder_input.setPlaceholderText(self.texts["download_folder"])
        browse_button = QPushButton(self.texts["browse"])
        browse_button.clicked.connect(self._select_folder)
        folder_row.addWidget(self.folder_input, 1)
        folder_row.addWidget(browse_button)

        concurrency_row = QHBoxLayout()
        concurrency_label = QLabel(self.texts["parallel_downloads"])
        self.concurrency_input = QSpinBox()
        self.concurrency_input.setRange(1, 8)
        self.concurrency_input.setValue(4)
        concurrency_row.addWidget(concurrency_label)
        concurrency_row.addWidget(self.concurrency_input)
        concurrency_row.addStretch(1)

        quality_row = QHBoxLayout()
        quality_label = QLabel(self.texts["quality"])
        self.quality_input = QComboBox()
        for quality_id, label_key in QUALITY_CHOICES:
            self.quality_input.addItem(self.texts[label_key], quality_id)
        self.quality_input.setCurrentIndex(3)
        quality_row.addWidget(quality_label)
        quality_row.addWidget(self.quality_input)
        quality_row.addStretch(1)

        button_row = QHBoxLayout()
        self.download_button = QPushButton(self.texts["download"])
        self.download_button.setObjectName("PrimaryButton")
        self.download_button.clicked.connect(self._start_download)
        self.stop_button = QPushButton(self.texts["stop"])
        self.stop_button.clicked.connect(self._stop_download)
        button_row.addStretch(1)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.download_button)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("Divider")

        status_label = QLabel(self.texts["status"])
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
        layout.addLayout(quality_row)
        layout.addLayout(button_row)
        layout.addWidget(divider)
        layout.addWidget(status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_list, 1)

        self.setCentralWidget(root)

    def _select_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            self.texts["select_folder"],
            self.folder_input.text(),
        )
        if selected:
            self.folder_input.setText(selected)

    def _start_download(self) -> None:
        urls = parse_urls(self.url_input.toPlainText())
        if not urls:
            QMessageBox.warning(
                self,
                self.texts["no_links_title"],
                self.texts["no_links_message"],
            )
            return

        output_dir = ensure_directory(Path(self.folder_input.text()).expanduser())
        self.folder_input.setText(str(output_dir))
        self.log_list.clear()
        self.progress_bar.setValue(0)
        self._log(self.texts["saving_to"].format(path=output_dir))
        self._log(self.texts["parallel_count"].format(count=self.concurrency_input.value()))
        self._log(self.texts["selected_quality"].format(quality=self.quality_input.currentText()))

        self.thread = QThread(self)
        self.worker = DownloadWorker(
            urls,
            output_dir,
            self.concurrency_input.value(),
            str(self.quality_input.currentData()),
        )
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
            self._log(self.texts["stopping"])

    @Slot(str, str, object)
    def _on_progress(self, url: str, message: str, percent: object) -> None:
        if isinstance(percent, float | int):
            self.progress_bar.setValue(max(0, min(100, int(percent))))
        self._log(f"{message} | {url}")

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._log(self.texts["error"].format(message=message))

    @Slot()
    def _on_finished(self) -> None:
        self._set_busy(False)
        self._log(self.texts["done"])

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
        self.quality_input.setEnabled(not busy)

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
        QPlainTextEdit, QLineEdit, QListWidget, QSpinBox, QComboBox {
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
