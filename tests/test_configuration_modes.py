from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication, QLabel

from clt_helper.models import UnitMode
from clt_helper.qt_application import CLTApplication
from tests.ui_test_helpers import configured_window


class ConfigurationModeTests(unittest.TestCase):
    @staticmethod
    def _result_labels_text(window: CLTApplication) -> str:
        return "\n".join(label.text() for label in window.result_view.findChildren(QLabel))

    def test_cabinet_pixels_update_millimeters_and_screen_geometry(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window._set_mode(UnitMode.CABINET)
            window.auto_checkbox.setChecked(False)
            window.pitch_entry.setText("2.5")
            window.screen_boxes.setText("2x1")
            window.pixels_entry.setText("320x240")
            window.pixels_entry.textEdited.emit("320x240")
            qt_app.processEvents()

            window._configure_scheme()
            assert window.configuration is not None
            module = window.configuration.module
            screen = window.configuration.screen
            self.assertEqual((module.width_mm, module.height_mm), (800, 600))
            self.assertEqual((screen.pixels_w, screen.pixels_h), (640, 240))
            self.assertEqual((screen.width_m, screen.height_m), (1.6, 0.6))
        finally:
            window.close()

    def test_cabinet_pitch_changes_dimensions_without_rewriting_pixels(self) -> None:
        QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window._set_mode(UnitMode.CABINET)
            window.pixels_entry.setText("256x192")
            window.pitch_entry.setText("2")
            window._on_pitch_changed("2")
            self.assertEqual(window.pixels_entry.text(), "256x192")
            window._configure_scheme()
            assert window.configuration is not None
            self.assertIn("箱体尺寸：512 x 384 mm", window.configuration.result_text)
        finally:
            window.close()

    def test_cabinet_pixels_are_independent_of_catalog_module(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window._set_mode(UnitMode.CABINET)
            window.pitch_entry.setText("1.53")
            window._on_pitch_changed("1.53")
            qt_app.processEvents()

            self.assertEqual(window.pixels_entry.text(), "344x258")
            window._configure_scheme()
            assert window.configuration is not None
            self.assertIn("箱体尺寸：526 x 395 mm", window.configuration.result_text)
        finally:
            window.close()

    def test_cabinet_fields_override_catalog_module_and_receiver_load(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = CLTApplication()
        try:
            window._set_mode(UnitMode.CABINET)
            window.pitch_entry.setText("1.25")
            window._on_pitch_changed("1.25")
            window.screen_boxes.setText("2x1")
            window.pixels_entry.setText("480x270")
            window.pixels_entry.textEdited.emit("480x270")
            qt_app.processEvents()

            window._configure_scheme()
            assert window.configuration is not None
            configuration = window.configuration
            self.assertEqual(
                (configuration.module.width_mm, configuration.module.height_mm),
                (600, 337.5),
            )
            self.assertEqual(
                (configuration.module.pixels_w, configuration.module.pixels_h),
                (480, 270),
            )
            self.assertEqual(
                (configuration.plan.card_pixels_w, configuration.plan.card_pixels_h),
                (480, 270),
            )
            self.assertIn("箱体尺寸：600 x 337.5 mm", configuration.result_text)
            self.assertIn("箱体点数：480 x 270", configuration.result_text)
            self.assertIn("单箱480 x 270点", configuration.result_text)
        finally:
            window.close()

    def test_hdr_option_reconfigures_receiver_and_port_capacity(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = CLTApplication()
        try:
            window.pitch_entry.setText("2")
            window._on_pitch_changed("2")
            window.screen_modules.setText("12x15")
            window.screen_source = "modules"
            window.hdr_checkbox.setChecked(True)
            window._configure_scheme()
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertEqual(window.configuration.plan.receiver_model, "E80-G2")
            self.assertEqual(window.configuration.plan.port_capacity, 487_500)
            self.assertIn("E80-G2", self._result_labels_text(window))
        finally:
            window.close()

    def test_3d_and_hdr_checkboxes_are_mutually_exclusive(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = CLTApplication()
        try:
            window.feature_3d_checkbox.setChecked(True)
            window.hdr_checkbox.setChecked(True)
            qt_app.processEvents()

            self.assertFalse(window.feature_3d_checkbox.isChecked())
            self.assertTrue(window.hdr_checkbox.isChecked())
        finally:
            window.close()

    def test_3d_checkbox_reconfigures_port_capacity(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window.feature_3d_checkbox.setChecked(True)
            window._configure_scheme()
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertEqual(window.configuration.plan.port_capacity, 325_000)
            self.assertIn("325000", self._result_labels_text(window))
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
