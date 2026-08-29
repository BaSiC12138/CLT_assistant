from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.models import Preferences
from clt_helper.plain_text_formatter import format_plain_text
from clt_helper.qt_application import CLTApplication
from tests.ui_test_helpers import configured_window

DEFAULT_TEXT = (
    "P1.86：1台X4s主控 + 24张E80接收卡【1宽6高（172*516）】"
    " + 4根网线 + 1台服务器CS4K-G3"
)


class PlainTextCopyTests(unittest.TestCase):
    def test_default_configuration_uses_required_format(self) -> None:
        app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            assert window.configuration is not None
            self.assertEqual(format_plain_text(window.configuration), DEFAULT_TEXT)
        finally:
            window.close()

    def test_async_configuration_omits_server(self) -> None:
        module = matching_modules(1.86)[0]
        screen = screen_from_modules(module, (12, 12))
        configuration = calculate_configuration(
            module,
            screen,
            Preferences(asynchronous=True),
        )

        self.assertTrue(format_plain_text(configuration).endswith(" + 无需配置服务器"))

    def test_mixed_receiver_heights_are_listed_in_order(self) -> None:
        module = matching_modules(1.25)[0]
        screen = screen_from_modules(module, (12, 9))
        configuration = calculate_configuration(module, screen, Preferences())

        text = format_plain_text(configuration)

        self.assertIn(
            "【1宽5高（256*640）/1宽4高（256*512）】",
            text,
        )

    def test_cabinet_configuration_uses_single_cabinet_load(self) -> None:
        module = matching_modules(1.86)[0]
        screen = screen_from_modules(module, (40, 30))
        configuration = calculate_configuration(
            module,
            screen,
            Preferences(),
            receiver_override="K5+",
            card_shape_override=(2, 3),
        )

        self.assertIn(
            "200张K5+接收卡【2宽3高（344*258）】",
            format_plain_text(configuration),
        )

    def test_u_series_controller_includes_board_details(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (60, 40))
        configuration = calculate_configuration(
            module,
            screen,
            Preferences(feature_hdr=True),
        )

        self.assertIn(
            "1台U3 Max主控（3张1路HDMI2.0+1路DP1.2输入板卡；"
            "3张U_OUT_20×1G_RJ45输出板卡）",
            format_plain_text(configuration),
        )

    def test_button_copies_current_configuration(self) -> None:
        app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            self.assertEqual(window.copy_plain_button.text(), "复制为纯文本形式")
            header_layout = window.copy_plain_button.parentWidget().layout()
            self.assertEqual(header_layout.indexOf(window.copy_plain_button), 0)
            self.assertEqual(header_layout.indexOf(window.output_synced_badge), 1)
            clipboard = Mock()
            with patch(
                "clt_helper.qt_behavior.QApplication.clipboard",
                return_value=clipboard,
            ):
                window.copy_plain_button.click()
            clipboard.setText.assert_called_once_with(DEFAULT_TEXT)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
