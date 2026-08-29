from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication

from clt_helper.cabinet_dimensions import CabinetDimensions
from clt_helper.models import UnitMode
from clt_helper.qt_application import CLTApplication
from tests.ui_test_helpers import configured_window


class ModuleScreenSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qt_app = QApplication.instance() or QApplication([])
        self.window = configured_window()

    def tearDown(self) -> None:
        self.window.close()

    def _edit(self, entry, value: str) -> None:
        entry.setText(value)
        entry.textEdited.emit(value)
        self.qt_app.processEvents()

    def test_module_count_immediately_updates_size_and_resolution(self) -> None:
        self._edit(self.window.screen_modules, "10x8")

        self.assertEqual(self.window.screen_physical.text(), "3.2×1.28")
        self.assertEqual(self.window.screen_pixels.text(), "1720×688")

    def test_physical_size_immediately_updates_other_fields_and_plan(self) -> None:
        self._edit(self.window.screen_physical, "3.84x1.92")

        self.assertEqual(self.window.screen_modules.text(), "12×12")
        self.assertEqual(self.window.screen_pixels.text(), "2064×1032")
        self.window._configure_scheme()
        assert self.window.configuration is not None
        self.assertEqual(
            (self.window.configuration.screen.modules_w, self.window.configuration.screen.modules_h),
            (12, 12),
        )

    def test_resolution_immediately_updates_size_and_module_count(self) -> None:
        self._edit(self.window.screen_pixels, "3440x860")

        self.assertEqual(self.window.screen_modules.text(), "20×10")
        self.assertEqual(self.window.screen_physical.text(), "6.4×1.6")

    def test_cabinet_pixels_derive_whole_millimeters_in_result(self) -> None:
        self.window._set_mode(UnitMode.CABINET)
        self.window.pitch_entry.setText("1.53")
        self.window._on_pitch_changed("1.53")
        self._edit(self.window.pixels_entry, "416x312")
        self.window._configure_scheme()

        assert self.window.configuration is not None
        self.assertIn("箱体尺寸：636 x 477 mm", self.window.configuration.result_text)

    def test_cabinet_millimeters_round_decimals_but_keep_exact_halves(self) -> None:
        rounded = CabinetDimensions((1, 1), (639.84, 479.88))
        half = CabinetDimensions((1, 1), (600, 337.5))

        self.assertEqual(rounded.millimeters_text, "640×480")
        self.assertEqual(half.millimeters_text, "600×337.5")

    def test_custom_cabinet_pixels_keep_half_millimeter_dimensions(self) -> None:
        self.window._set_mode(UnitMode.CABINET)
        self.window.pitch_entry.setText("1.25")
        self.window._on_pitch_changed("1.25")
        self._edit(self.window.pixels_entry, "480x270")

        self.window._configure_scheme()
        assert self.window.configuration is not None
        self.assertEqual(self.window.configuration.module.height_mm, 337.5)


if __name__ == "__main__":
    unittest.main()
