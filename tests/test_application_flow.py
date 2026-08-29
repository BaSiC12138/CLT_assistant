from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from clt_helper.models import ReceiverDiscount, UnitMode
from clt_helper.qt_application import CLTApplication
from tests.ui_test_helpers import configured_window


class ApplicationFlowTests(unittest.TestCase):
    @staticmethod
    def _result_labels_text(window: CLTApplication) -> str:
        return "\n".join(
            label.text() for label in window.result_view.findChildren(QLabel)
        )

    @staticmethod
    def _replace_text(entry, value: str) -> None:
        entry.setText(value)
        entry.textEdited.emit(value)

    def test_startup_uses_empty_values_with_example_placeholders(self) -> None:
        QApplication.instance() or QApplication([])
        window = CLTApplication()
        try:
            entries = (
                (window.pitch_entry, "1.86"),
                (window.screen_modules, "12×12"),
                (window.screen_physical, "3.84×1.92"),
                (window.screen_pixels, "2064×1032"),
            )
            self.assertTrue(all(not entry.text() for entry, _ in entries))
            self.assertEqual(
                [entry.placeholderText() for entry, _ in entries],
                [placeholder for _, placeholder in entries],
            )
            self.assertIsNone(window.configuration)
        finally:
            window.close()

    def test_presets_use_p186_and_640_by_480_cabinet(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            self.assertEqual(window.pitch_entry.text(), "1.86")
            self.assertEqual(window.size_entry.text(), "320x160")
            self.assertEqual(window.pixels_entry.text(), "172x86")
            assert window.configuration is not None
            self.assertEqual(window.configuration.module.pitch, 1.86)

            window.show()
            qt_app.processEvents()
            window.cabinet_mode_button.click()
            self.assertEqual(window.pitch_entry.text(), "1.86")
            self.assertTrue(window.size_entry.isHidden())
            self.assertTrue(window.screen_modules.isHidden())
            self.assertEqual(window.pixels_entry.text(), "344x258")
            self.assertEqual(window.screen_boxes.text(), "6x4")
            QTest.mouseClick(window.configure_button, Qt.MouseButton.LeftButton)
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertIn("箱体尺寸：640 x 480 mm", window.configuration.result_text)
            result_labels = self._result_labels_text(window)
            self.assertIn("箱体尺寸", result_labels)
            self.assertIn("<b>640×480mm</b>", result_labels)
        finally:
            window.close()

    def test_receiver_discount_is_required_and_defaults_to_none(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            self.assertEqual(window.discount_combo.count(), 4)
            self.assertEqual(window.discount_combo.currentText(), "不打折")
            window.screen_modules.setText("12x6")
            window.screen_source = "modules"
            window.discount_combo.setCurrentIndex(ReceiverDiscount.TWO.value - 1)
            window._configure_scheme()
            qt_app.processEvents()

            assert window.configuration is not None
            self.assertEqual(window.configuration.plan.cards_w, 6)
            self.assertIn("打2折", self._result_labels_text(window))
        finally:
            window.close()

    def test_configure_and_resize_preserve_result(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window.screen_modules.setText("10x8")
            window.screen_source = "modules"
            window._configure_scheme()

            self.assertIsNotNone(window.configuration)
            assert window.configuration is not None
            before = window.configuration
            self.assertEqual(before.screen.modules_w, 10)
            self.assertEqual(before.screen.modules_h, 8)
            self.assertIn("1720 x 688", before.result_text)
            self.assertIsNotNone(window._diagram_pixmap)

            window.resize(1800, 1012)
            qt_app.processEvents()
            window.resize(1280, 720)
            qt_app.processEvents()

            self.assertIs(window.configuration, before)
            self.assertEqual(window.screen_modules.text(), "10x8")
            self.assertTrue(window.box_frame.isHidden())
        finally:
            window.close()

    def test_cabinet_mode_exposes_k_series_selection(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window._set_mode(UnitMode.CABINET)
            self.assertFalse(window.discount_combo.isEnabled())
            self.assertTrue(window.discount_label.isHidden())
            self.assertTrue(window.discount_combo.isHidden())
            self.assertTrue(window.module_status.isHidden())
            window.screen_boxes.setText("6x4")
            window._configure_scheme()
            qt_app.processEvents()

            self.assertEqual(window.receiver_combo.count(), 4)
            self.assertEqual(window.receiver_combo.currentText(), "自动")
            self.assertEqual(
                [window.receiver_combo.itemText(index) for index in range(4)],
                ["自动", "K5+", "K8", "K10"],
            )
            self.assertIsNotNone(window.configuration)
            assert window.configuration is not None
            self.assertEqual(window.configuration.plan.receiver_model, "K5+")
            self.assertIn("接收卡：K5+ × 24", window.configuration.result_text)

            window.receiver_combo.setCurrentText("K8")
            window._configure_scheme()
            self.assertEqual(window.configuration.plan.receiver_model, "K8")

            window._set_mode(UnitMode.MODULE)
            self.assertFalse(window.discount_label.isHidden())
            self.assertFalse(window.discount_combo.isHidden())
            self.assertTrue(window.discount_combo.isEnabled())
            self.assertFalse(window.module_status.isHidden())
        finally:
            window.close()

    def test_cabinet_mode_uses_two_by_two_parameter_layout(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window._set_mode(UnitMode.CABINET)
            qt_app.processEvents()

            modules_label, modules_entry = window.field_widgets["modules"]
            size_label, size_entry = window.field_widgets["size"]
            pixels_label, pixels_entry = window.field_widgets["pixels"]
            self.assertTrue(modules_label.isHidden())
            self.assertTrue(modules_entry.isHidden())
            self.assertTrue(size_label.isHidden())
            self.assertTrue(size_entry.isHidden())
            self.assertFalse(hasattr(window, "box_count_entry"))
            self.assertEqual(pixels_label.text(), "箱体点数")
            top = window.parameter_form_layout
            bottom = window.box_frame.layout()
            self.assertEqual(top.getItemPosition(top.indexOf(window.pitch_entry))[1], 1)
            self.assertEqual(top.getItemPosition(top.indexOf(pixels_entry))[1], 3)
            self.assertEqual(bottom.getItemPosition(bottom.indexOf(window.screen_boxes))[1], 1)
            self.assertEqual(bottom.getItemPosition(bottom.indexOf(window.receiver_combo))[1], 3)

            window._set_mode(UnitMode.MODULE)
            self.assertFalse(modules_entry.isHidden())
            self.assertFalse(size_entry.isHidden())
            self.assertEqual(size_label.text(), "模组 mm")
            self.assertEqual(size_entry.text(), "320x160")
            self.assertEqual(pixels_label.text(), "模组点数")
            self.assertEqual(pixels_entry.text(), "172x86")
        finally:
            window.close()

    def test_module_and_cabinet_parameters_are_independent(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window.show()
            QTest.mouseClick(window.auto_checkbox, Qt.MouseButton.LeftButton)
            self._replace_text(window.pitch_entry, "2.5")
            self._replace_text(window.size_entry, "300x150")
            self._replace_text(window.pixels_entry, "120x60")
            self._replace_text(window.screen_modules, "10x8")

            QTest.mouseClick(window.cabinet_mode_button, Qt.MouseButton.LeftButton)
            self._replace_text(window.pitch_entry, "1.25")
            self._replace_text(window.screen_boxes, "3x2")
            self._replace_text(window.pixels_entry, "480x270")
            qt_app.processEvents()

            QTest.mouseClick(window.module_mode_button, Qt.MouseButton.LeftButton)
            self.assertEqual(window.pitch_entry.text(), "2.5")
            self.assertEqual(window.size_entry.text(), "300x150")
            self.assertEqual(window.pixels_entry.text(), "120x60")
            self.assertEqual(window.screen_modules.text(), "10x8")
            QTest.mouseClick(window.configure_button, Qt.MouseButton.LeftButton)
            assert window.configuration is not None
            self.assertEqual(window.configuration.module.size_text, "300x150")
            self.assertEqual(window.configuration.module.pixels_text, "120x60")

            QTest.mouseClick(window.cabinet_mode_button, Qt.MouseButton.LeftButton)
            self.assertEqual(window.pitch_entry.text(), "1.25")
            self.assertEqual(window.pixels_entry.text(), "480x270")
            self.assertEqual(window.screen_boxes.text(), "3x2")
            QTest.mouseClick(window.configure_button, Qt.MouseButton.LeftButton)
            assert window.configuration is not None
            self.assertEqual(window.configuration.module.size_text, "600x337.5")
            self.assertEqual(window.configuration.module.pixels_text, "480x270")
        finally:
            window.close()

    def test_special_mode_is_blank_and_keeps_standard_states(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = configured_window()
        try:
            window.show()
            self._replace_text(window.screen_modules, "10x8")
            previous_configuration = window.configuration

            QTest.mouseClick(window.special_mode_button, Qt.MouseButton.LeftButton)
            qt_app.processEvents()

            self.assertEqual(window._active_mode, UnitMode.SPECIAL)
            self.assertTrue(window.special_mode_button.isChecked())
            self.assertTrue(window.special_frame.isVisible())
            self.assertIsNone(window.special_frame.layout())
            self.assertTrue(window.parameter_form_widget.isHidden())
            self.assertTrue(window.feature_options_widget.isHidden())
            self.assertTrue(window.parameter_options_widget.isHidden())
            self.assertTrue(window.parameter_actions_widget.isHidden())
            self.assertTrue(window.box_frame.isHidden())
            window._configure_scheme()
            self.assertIs(window.configuration, previous_configuration)

            QTest.mouseClick(window.module_mode_button, Qt.MouseButton.LeftButton)
            self.assertEqual(window.screen_modules.text(), "10x8")
        finally:
            window.close()

if __name__ == "__main__":
    unittest.main()
