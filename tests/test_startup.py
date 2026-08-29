from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from clt_helper.qt_startup import (
    EXPANSION_END,
    FILL_END,
    StartupSequence,
    StartupSplash,
    StartupTiming,
)


TEST_TIMING = StartupTiming(duration_ms=70)


class StartupSplashTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application = QApplication.instance() or QApplication([])
        self.splash = StartupSplash(TEST_TIMING)
        self.splash.resize(800, 450)

    def tearDown(self) -> None:
        self.splash.close()

    def test_splash_is_transparent_and_does_not_take_input(self) -> None:
        flags = self.splash.windowFlags()

        self.assertTrue(self.splash.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertTrue(flags & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(flags & Qt.WindowType.WindowTransparentForInput)

    def test_timeline_requests_reveal_once_and_completes(self) -> None:
        reveal_spy = QSignalSpy(self.splash.reveal_requested)
        completed_spy = QSignalSpy(self.splash.completed)

        self.splash.start()
        QTest.qWait(TEST_TIMING.duration_ms + 40)

        self.assertEqual(reveal_spy.count(), 1)
        self.assertEqual(completed_spy.count(), 1)

    def test_filled_logo_keeps_transparent_center(self) -> None:
        self.splash.show()
        self.splash._set_progress(0.5)
        self.application.processEvents()
        image = self.splash.grab().toImage()
        scale = image.width() / self.splash.width()
        logical_logo = self.splash._logo_rect()
        center_x = image.width() // 2
        center_y = image.height() // 2
        ring_offset = round(logical_logo.width() * 0.40 * scale)
        center = image.pixelColor(center_x, center_y)
        right_ring = image.pixelColor(center_x + ring_offset, center_y)

        self.assertEqual(center.alpha(), 0)
        self.assertGreater(right_ring.alpha(), 0)

    def test_sequence_reveals_main_window_and_closes_splash(self) -> None:
        window = QMainWindow()
        window.setCentralWidget(QWidget())
        sequence = StartupSequence(self.splash, window)

        self.splash.show()
        sequence.start()
        self.splash._animation.stop()
        self.assertTrue(window.isVisible())
        self.assertTrue(window.isMaximized())
        self.assertEqual(window.windowOpacity(), 0.0)

        self.splash._set_progress(FILL_END)
        self.application.processEvents()

        self.assertTrue(window.isVisible())
        self.assertEqual(window.windowOpacity(), 0.0)

        midpoint = (FILL_END + EXPANSION_END) / 2
        self.splash._set_progress(midpoint)
        self.application.processEvents()
        self.assertAlmostEqual(
            window.windowOpacity(),
            self.splash._transition_progress(),
            delta=0.01,
        )
        self.assertAlmostEqual(
            (1.0 - self.splash._transition_progress()) + window.windowOpacity(),
            1.0,
            delta=0.01,
        )

        self.splash._set_progress(EXPANSION_END)
        self.application.processEvents()
        self.assertEqual(window.windowOpacity(), 1.0)
        self.assertFalse(self.splash.isVisible())

        self.splash.completed.emit()
        self.application.processEvents()

        self.assertTrue(window.isVisible())
        self.assertEqual(window.windowOpacity(), 1.0)
        self.assertFalse(self.splash.isVisible())
        window.close()

    def test_transition_uses_cached_logo_texture(self) -> None:
        first = self.splash._renderer.transition_texture()
        second = self.splash._renderer.transition_texture()

        self.assertEqual(first.cacheKey(), second.cacheKey())


if __name__ == "__main__":
    unittest.main()
