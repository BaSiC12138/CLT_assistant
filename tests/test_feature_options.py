from __future__ import annotations

import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from clt_helper.models import UnitMode
from clt_helper.qt_application import CLTApplication
from tests.ui_test_helpers import configured_window


class FeatureOptionTests(unittest.TestCase):
    def test_feature_checkboxes_replace_point_and_async_menu_items(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            assert window.configuration is not None
            normal_model = window.configuration.plan.controller_model
            menu_texts = tuple(action.text() for action in window.settings_menu.actions())
            self.assertNotIn("异步盒子", menu_texts)
            self.assertNotIn("点对点控屏", menu_texts)

            window.async_checkbox.setChecked(True)
            window._configure_scheme()
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertTrue(window._preferences().asynchronous)
            self.assertEqual(window.configuration.plan.controller_model, "A200")
            self.assertNotEqual(window.configuration.plan.controller_model, normal_model)
        finally:
            window.close()

    def test_point_to_point_is_first_and_changes_controller_selection(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            layout = window.point_checkbox.parentWidget().layout()
            checkboxes = tuple(layout.itemAt(index).widget() for index in range(1, 5))
            self.assertEqual(
                tuple(checkbox.text() for checkbox in checkboxes),
                ("点对点", "异步功能", "主动式3D", "HDR"),
            )
            window.screen_modules.setText("32x12")
            window.screen_source = "modules"
            window.point_checkbox.setChecked(True)
            window._configure_scheme()
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertTrue(window._preferences().point_to_point)
            self.assertEqual(window.configuration.plan.controller_model, "X12m")
        finally:
            window.close()

    def test_async_is_mutually_exclusive_in_standard_modes(self) -> None:
        QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            for mode in (UnitMode.MODULE, UnitMode.CABINET):
                with self.subTest(mode=mode):
                    window._set_mode(mode)
                    window.point_checkbox.setChecked(True)
                    window.feature_3d_checkbox.setChecked(True)
                    window.async_checkbox.setChecked(True)
                    self.assertTrue(window.async_checkbox.isChecked())
                    self.assertFalse(window.point_checkbox.isChecked())
                    self.assertFalse(window.feature_3d_checkbox.isChecked())
                    self.assertFalse(window.hdr_checkbox.isChecked())

                    window.hdr_checkbox.setChecked(True)
                    self.assertFalse(window.async_checkbox.isChecked())
                    window.async_checkbox.setChecked(True)
                    window.point_checkbox.setChecked(True)
                    self.assertFalse(window.async_checkbox.isChecked())
        finally:
            window.close()

    def test_async_over_forty_ports_displays_no_device_error(self) -> None:
        QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window.screen_modules.setText("80x60")
            window.screen_source = "modules"
            window.async_checkbox.setChecked(True)
            with patch("clt_helper.qt_behavior.QMessageBox.warning") as warning:
                window._configure_scheme()

            warning.assert_called_once_with(window, "参数错误", "无设备满足")
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
