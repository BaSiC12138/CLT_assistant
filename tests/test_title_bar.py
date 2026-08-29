from __future__ import annotations

import unittest

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication

from clt_helper.qt_application import CLTApplication
from clt_helper.qt_window_frame import (
    HTBOTTOM,
    HTBOTTOMLEFT,
    HTRIGHT,
    HTTOPLEFT,
    HTTOPRIGHT,
    resize_hit_code,
)


class TitleBarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qt_app = QApplication.instance() or QApplication([])
        self.window = CLTApplication()

    def tearDown(self) -> None:
        self.window.close()

    def test_window_uses_custom_frameless_title_bar(self) -> None:
        flags = self.window.windowFlags()

        self.assertTrue(flags & Qt.WindowType.FramelessWindowHint)
        self.assertEqual(self.window.title_bar.objectName(), "Header")
        self.assertEqual(self.window.settings_button.text(), "配置选项  ▾")
        self.assertEqual(self.window.title_bar.close_button.toolTip(), "关闭")

    def test_maximize_button_toggles_window_state(self) -> None:
        self.window.show()
        self.qt_app.processEvents()

        self.window.title_bar.maximize_button.click()
        self.qt_app.processEvents()
        self.assertTrue(self.window.isMaximized())

        self.window.title_bar.maximize_button.click()
        self.qt_app.processEvents()
        self.assertFalse(self.window.isMaximized())

    def test_resize_hit_codes_cover_edges_and_corners(self) -> None:
        width, height = 1280, 720

        self.assertEqual(resize_hit_code(QPoint(0, 0), width, height), HTTOPLEFT)
        self.assertEqual(resize_hit_code(QPoint(1279, 0), width, height), HTTOPRIGHT)
        self.assertEqual(resize_hit_code(QPoint(0, 719), width, height), HTBOTTOMLEFT)
        self.assertEqual(resize_hit_code(QPoint(640, 719), width, height), HTBOTTOM)
        self.assertEqual(resize_hit_code(QPoint(1279, 360), width, height), HTRIGHT)
        self.assertIsNone(resize_hit_code(QPoint(640, 360), width, height))


if __name__ == "__main__":
    unittest.main()
