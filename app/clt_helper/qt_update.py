from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .updates import ReleaseInfo, UpdateService


BrowserOpener = Callable[[str], bool]
DIALOG_WIDTH = 520
DIALOG_HEIGHT = 360


def open_in_browser(url: str) -> bool:
    return QDesktopServices.openUrl(QUrl(url))


class UpdateThread(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, service: UpdateService, parent: QObject) -> None:
        super().__init__(parent)
        self._service = service

    def run(self) -> None:
        try:
            self.completed.emit(self._service.check())
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            self.failed.emit(message)


class UpdateDialog(QDialog):
    def __init__(
        self,
        release: ReleaseInfo,
        open_browser: BrowserOpener,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._release = release
        self._open_browser = open_browser
        self.setWindowTitle("发现新版本")
        self.setModal(True)
        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel(f"发现新版本 V{self._release.version}")
        title.setObjectName("UpdateTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("更新内容"))
        notes = QPlainTextEdit(self._release.notes or "暂无更新说明。")
        notes.setObjectName("UpdateNotes")
        notes.setReadOnly(True)
        layout.addWidget(notes, 1)
        layout.addLayout(self._build_actions())

    def _build_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addStretch(1)
        later = QPushButton("稍后")
        update = QPushButton("立即更新")
        update.setDefault(True)
        later.clicked.connect(self.reject)
        update.clicked.connect(self._download)
        layout.addWidget(later)
        layout.addWidget(update)
        return layout

    def _download(self) -> None:
        if self._open_browser(self._release.asset.download_url):
            self.accept()
            return
        QMessageBox.warning(self, "打开失败", "无法打开浏览器下载最新版本。")


class UpdateController(QObject):
    check_finished = Signal()

    def __init__(
        self,
        parent: QWidget,
        service: UpdateService,
        open_browser: BrowserOpener = open_in_browser,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._service = service
        self._open_browser = open_browser
        self._thread: UpdateThread | None = None
        self._dialog: UpdateDialog | None = None

    @Slot()
    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("更新检查已在运行")
        thread = UpdateThread(self._service, self)
        thread.completed.connect(self._handle_result)
        thread.failed.connect(self._handle_failure)
        thread.finished.connect(self._clear_thread)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        thread.start()

    def wait_for_completion(self) -> None:
        if self._thread is not None:
            self._thread.wait()

    @Slot(object)
    def _handle_result(self, release: object) -> None:
        if release is None:
            return
        if not isinstance(release, ReleaseInfo):
            raise TypeError("更新检查返回了无效结果")
        dialog = UpdateDialog(release, self._open_browser, self._parent)
        dialog.finished.connect(self._clear_dialog)
        self._dialog = dialog
        dialog.open()

    @Slot(str)
    def _handle_failure(self, message: str) -> None:
        QMessageBox.warning(self._parent, "更新检查失败", message)

    @Slot()
    def _clear_thread(self) -> None:
        self._thread = None
        self.check_finished.emit()

    @Slot()
    def _clear_dialog(self) -> None:
        self._dialog = None
