from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication, QLabel

from clt_helper.constants import APP_TITLE, APP_VERSION, VERSION_TEXT
from clt_helper.qt_application import CLTApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = PROJECT_ROOT / "app" / "assets" / "app.ico"
ICON_SOURCE_PATH = PROJECT_ROOT / "app" / "assets" / "app_icon.png"
EXPECTED_ICON_SIZES = {
    (16, 16),
    (20, 20),
    (24, 24),
    (32, 32),
    (40, 40),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
}


class BrandingTests(unittest.TestCase):
    def test_application_icon_has_transparent_center_and_background(self) -> None:
        with Image.open(ICON_SOURCE_PATH) as icon:
            alpha = icon.getchannel("A")
            center = (icon.width // 2, icon.height // 2)
            self.assertEqual(alpha.getpixel((0, 0)), 0)
            self.assertEqual(alpha.getpixel(center), 0)
            self.assertEqual(alpha.getextrema()[1], 255)

    def test_windows_icon_contains_standard_sizes(self) -> None:
        with Image.open(ICON_PATH) as icon:
            self.assertEqual(set(icon.ico.sizes()), EXPECTED_ICON_SIZES)

    def test_application_uses_release_branding(self) -> None:
        qt_app = QApplication.instance() or QApplication([])
        window = CLTApplication()
        try:
            labels = {label.text() for label in window.findChildren(QLabel)}
            self.assertEqual(APP_TITLE, "CLTassistant V1.0.1")
            self.assertEqual(window.windowTitle(), APP_TITLE)
            self.assertIn(f"V{APP_VERSION}", labels)
            self.assertIn(VERSION_TEXT, labels)
            qt_app.processEvents()
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
