from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QProxyStyle, QStyle, QStyleOption

CHECKBOX_BORDER = QColor("#202020")
CHECKBOX_CHECK = QColor("#ffffff")
CHECKBOX_CHECKED = QColor("#1769ef")
CHECKBOX_DISABLED = QColor("#eef1f5")
CHECKBOX_HOVER = QColor("#edf4ff")
CHECKBOX_UNCHECKED = QColor("#ffffff")


class CheckboxStyle(QProxyStyle):
    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: object | None = None,
    ) -> None:
        if element != QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            super().drawPrimitive(element, option, painter, widget)
            return
        self._draw_checkbox(option, painter)

    @staticmethod
    def _draw_checkbox(option: QStyleOption, painter: QPainter) -> None:
        state = option.state
        checked = bool(state & QStyle.StateFlag.State_On)
        enabled = bool(state & QStyle.StateFlag.State_Enabled)
        hovered = bool(state & QStyle.StateFlag.State_MouseOver)
        bounds = QRectF(option.rect).adjusted(1.0, 1.0, -1.0, -1.0)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(CHECKBOX_BORDER, 1.4))
        painter.setBrush(_checkbox_fill(checked, enabled, hovered))
        painter.drawRoundedRect(bounds, 3.0, 3.0)
        if checked:
            _draw_checkmark(painter, bounds)
        painter.restore()


def _checkbox_fill(checked: bool, enabled: bool, hovered: bool) -> QColor:
    if checked:
        return CHECKBOX_CHECKED
    if not enabled:
        return CHECKBOX_DISABLED
    return CHECKBOX_HOVER if hovered else CHECKBOX_UNCHECKED


def _draw_checkmark(painter: QPainter, bounds: QRectF) -> None:
    path = QPainterPath()
    path.moveTo(_point(bounds, 0.22, 0.52))
    path.lineTo(_point(bounds, 0.42, 0.72))
    path.lineTo(_point(bounds, 0.79, 0.30))
    width = max(1.8, min(bounds.width(), bounds.height()) * 0.14)
    pen = QPen(CHECKBOX_CHECK, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path)


def _point(bounds: QRectF, x_ratio: float, y_ratio: float) -> QPointF:
    return QPointF(
        bounds.left() + bounds.width() * x_ratio,
        bounds.top() + bounds.height() * y_ratio,
    )
