from __future__ import annotations

import unittest

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPixmap, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsView

from clt_helper.qt_diagram_view import DEFAULT_FIT_SCALE, DiagramView


class DiagramViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance() or QApplication([])
        self.view = DiagramView()
        self.view.resize(800, 500)
        self.view.set_pixmap(QPixmap(2800, 1400))
        self.view.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.view.close()

    def test_uses_original_pixmap_and_hand_dragging(self) -> None:
        assert self.view.pixmap is not None
        self.assertEqual(self.view.pixmap.size().toTuple(), (2800, 1400))
        self.assertEqual(
            self.view.dragMode(),
            QGraphicsView.DragMode.ScrollHandDrag,
        )

    def test_default_fit_leaves_preview_margin(self) -> None:
        fitted = self.view.transform().mapRect(self.view.sceneRect())
        width_ratio = fitted.width() / self.view.viewport().width()

        self.assertAlmostEqual(width_ratio, DEFAULT_FIT_SCALE, delta=0.02)

    def test_mouse_wheel_zooms(self) -> None:
        before = self.view.transform().m11()
        event = QWheelEvent(
            QPointF(400, 250),
            QPointF(400, 250),
            QPoint(),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollUpdate,
            False,
        )

        self.view.wheelEvent(event)

        self.assertGreater(self.view.transform().m11(), before)
        self.assertTrue(event.isAccepted())

    def test_mouse_drag_pans_zoomed_view(self) -> None:
        self.view.scale(2, 2)
        horizontal = self.view.horizontalScrollBar()
        vertical = self.view.verticalScrollBar()
        before = horizontal.value(), vertical.value()

        QTest.mousePress(self.view.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(400, 250))
        QTest.mouseMove(self.view.viewport(), QPoint(300, 180), delay=20)
        QTest.mouseRelease(self.view.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(300, 180))
        self.app.processEvents()

        self.assertNotEqual((horizontal.value(), vertical.value()), before)


if __name__ == "__main__":
    unittest.main()
