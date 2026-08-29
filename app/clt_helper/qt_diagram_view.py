from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

ZOOM_STEP = 1.18
DEFAULT_FIT_SCALE = 0.84
VIEW_BACKGROUND = "#edf4fb"


class DiagramView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._user_transformed = False
        self.setScene(self._scene)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QColor(VIEW_BACKGROUND))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )

    @property
    def pixmap(self) -> QPixmap | None:
        if self._pixmap_item is None:
            return None
        return self._pixmap_item.pixmap()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        if self._pixmap_item is None:
            self._pixmap_item = self._scene.addPixmap(pixmap)
            self._pixmap_item.setTransformationMode(
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self._user_transformed = False
        QTimer.singleShot(0, self.fit_to_view)

    def fit_to_view(self) -> None:
        if self._pixmap_item is None or self.viewport().width() < 10:
            return
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(DEFAULT_FIT_SCALE, DEFAULT_FIT_SCALE)
        self.centerOn(self._pixmap_item)
        self._user_transformed = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        steps = event.angleDelta().y() / 120
        if self._pixmap_item is None or steps == 0:
            event.ignore()
            return
        self.scale(ZOOM_STEP**steps, ZOOM_STEP**steps)
        self._user_transformed = True
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)
            return
        self.fit_to_view()
        event.accept()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if not self._user_transformed:
            self.fit_to_view()
