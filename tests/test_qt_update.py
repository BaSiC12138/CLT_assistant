from __future__ import annotations

import unittest
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton

from clt_helper.qt_update import UpdateController, UpdateDialog
from clt_helper.updates import ReleaseAsset, ReleaseInfo, UpdateService


DOWNLOAD_URL = "https://github.com/example/download/CLTassistant.exe"
THREAD_WAIT_MS = 1000


def release_info(notes: str = "新增自动更新功能。") -> ReleaseInfo:
    asset = ReleaseAsset("CLTassistant-V1.0.2.exe", DOWNLOAD_URL)
    return ReleaseInfo("1.0.2", "V1.0.2", notes, "https://github.com/example", asset)


class UpdateDialogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qt_app = QApplication.instance() or QApplication([])

    def test_displays_version_and_chinese_release_notes(self) -> None:
        dialog = UpdateDialog(release_info(), lambda _url: True)
        try:
            labels = {label.text() for label in dialog.findChildren(QLabel)}
            notes = dialog.findChild(QPlainTextEdit, "UpdateNotes")
            self.assertIn("发现新版本 V1.0.2", labels)
            self.assertIsNotNone(notes)
            self.assertEqual(notes.toPlainText(), "新增自动更新功能。")
        finally:
            dialog.close()

    def test_update_button_opens_executable_download(self) -> None:
        opened: list[str] = []
        dialog = UpdateDialog(release_info(), lambda url: opened.append(url) is None)
        button = next(item for item in dialog.findChildren(QPushButton) if item.text() == "立即更新")
        button.click()
        self.assertEqual(opened, [DOWNLOAD_URL])
        self.assertEqual(dialog.result(), UpdateDialog.DialogCode.Accepted)

    def test_browser_failure_is_visible(self) -> None:
        dialog = UpdateDialog(release_info(), lambda _url: False)
        button = next(item for item in dialog.findChildren(QPushButton) if item.text() == "立即更新")
        with patch("clt_helper.qt_update.QMessageBox.warning") as warning:
            button.click()
        warning.assert_called_once()

    def test_controller_finishes_background_check(self) -> None:
        service = UpdateService("1.0.2", lambda: release_payload())
        parent = UpdateDialog(release_info(), lambda _url: True)
        controller = UpdateController(parent, service)
        completed = QSignalSpy(controller.check_finished)
        event_loop = QEventLoop()
        controller.check_finished.connect(event_loop.quit)
        try:
            controller.start()
            if completed.count() == 0:
                QTimer.singleShot(THREAD_WAIT_MS, event_loop.quit)
                event_loop.exec()
            self.assertEqual(completed.count(), 1)
        finally:
            parent.close()


def release_payload() -> dict[str, object]:
    return {
        "tag_name": "V1.0.2",
        "name": "V1.0.2",
        "body": "新增自动更新功能。",
        "html_url": "https://github.com/example/releases/tag/V1.0.2",
        "assets": [{"name": "app.exe", "browser_download_url": DOWNLOAD_URL}],
    }


if __name__ == "__main__":
    unittest.main()
