from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QLabel

from clt_helper.qt_application import CLTApplication
from clt_helper.qt_style import application_stylesheet
from tests.ui_test_helpers import configured_window

REMOVED_PORT_NOTE = "网口带载高度超过512像素，需用官方带载计算器复核。"
REQUIRED_SELECTION_FLAGS = (
    Qt.TextInteractionFlag.TextSelectableByMouse
    | Qt.TextInteractionFlag.TextSelectableByKeyboard
)


class CopyableResultsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance() or QApplication([])
        self.window = configured_window()

    def tearDown(self) -> None:
        self.window.close()

    def assert_copyable(self, label: QLabel) -> None:
        flags = label.textInteractionFlags()
        palette = label.palette()
        self.assertEqual(flags & REQUIRED_SELECTION_FLAGS, REQUIRED_SELECTION_FLAGS)
        self.assertEqual(label.cursor().shape(), Qt.CursorShape.IBeamCursor)
        self.assertEqual(
            palette.color(QPalette.ColorRole.Highlight),
            QColor("#1769ef"),
        )
        self.assertEqual(
            palette.color(QPalette.ColorRole.HighlightedText),
            QColor("#ffffff"),
        )

    def test_every_result_label_supports_text_selection(self) -> None:
        labels = self.window.result_view.findChildren(QLabel)

        self.assertTrue(labels)
        for label in labels:
            with self.subTest(text=label.text()):
                self.assert_copyable(label)

    def test_diagram_summary_supports_text_selection(self) -> None:
        self.assert_copyable(self.window.diagram_summary)

    def test_highlight_card_uses_light_background_and_dark_text(self) -> None:
        stylesheet = application_stylesheet(lambda value: value)

        self.assertIn("stop:0 #f8fbff,stop:1 #d8e9ff", stylesheet)
        self.assertIn("QLabel#ResultHighlightItem { color:#1f3d63", stylesheet)

    def test_removed_port_height_note_is_absent(self) -> None:
        assert self.window.configuration is not None

        self.assertNotIn(REMOVED_PORT_NOTE, self.window.configuration.plan.notes)
        self.assertNotIn(REMOVED_PORT_NOTE, self.window.configuration.result_text)


if __name__ == "__main__":
    unittest.main()
