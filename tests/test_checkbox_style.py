from __future__ import annotations

import unittest

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QStyle, QStyleOption

from clt_helper.qt_checkbox_style import (
    CHECKBOX_CHECKED,
    CHECKBOX_UNCHECKED,
    CheckboxStyle,
)

INDICATOR_SIZE = 18


class CheckboxStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])
        cls.style = CheckboxStyle()

    def test_unchecked_indicator_has_white_fill_and_dark_border(self) -> None:
        image = self._render_indicator(QStyle.StateFlag.State_Enabled)
        self.assertEqual(image.pixelColor(9, 9), CHECKBOX_UNCHECKED)
        self._assert_dark_border(image.pixelColor(1, 9))

    def test_checked_indicator_has_blue_fill_and_dark_border(self) -> None:
        state = QStyle.StateFlag.State_Enabled | QStyle.StateFlag.State_On
        image = self._render_indicator(state)
        self.assertEqual(image.pixelColor(13, 13), CHECKBOX_CHECKED)
        self._assert_dark_border(image.pixelColor(1, 9))

    def _assert_dark_border(self, color: QColor) -> None:
        self.assertLess(max(color.red(), color.green(), color.blue()), 110)

    def _render_indicator(self, state: QStyle.StateFlag) -> QImage:
        image = QImage(INDICATOR_SIZE, INDICATOR_SIZE, QImage.Format.Format_ARGB32)
        image.fill(QColor("#ff00ff"))
        option = QStyleOption()
        option.rect = QRect(0, 0, INDICATOR_SIZE, INDICATOR_SIZE)
        option.state = state
        painter = QPainter(image)
        self.style.drawPrimitive(
            QStyle.PrimitiveElement.PE_IndicatorCheckBox,
            option,
            painter,
        )
        painter.end()
        return image


if __name__ == "__main__":
    unittest.main()
