from __future__ import annotations

from math import cos, radians, sin

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient


INNER_RADIUS_RATIO = 0.60
SECTOR_SWEEP = 120.0
TRANSITION_TEXTURE_SIZE = 768
RING_SECTORS = (
    (90.0, QColor("#f44343")),
    (-30.0, QColor("#18b86b")),
    (-150.0, QColor("#1769ef")),
)


def _point_on_circle(rect: QRectF, angle: float) -> QPointF:
    angle_radians = radians(angle)
    return QPointF(
        rect.center().x() + rect.width() * cos(angle_radians) / 2,
        rect.center().y() - rect.height() * sin(angle_radians) / 2,
    )


def _sector_path(
    outer: QRectF,
    inner: QRectF,
    start: float,
    *,
    sweep: float,
) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(_point_on_circle(outer, start))
    path.arcTo(outer, start, -sweep)
    end_angle = start - sweep
    path.lineTo(_point_on_circle(inner, end_angle))
    path.arcTo(inner, end_angle, sweep)
    path.closeSubpath()
    return path


class StartupLogoRenderer:
    def __init__(self) -> None:
        self._transition_texture: QPixmap | None = None

    def paint_outline(self, painter: QPainter, logo: QRectF) -> None:
        outer, inner = self._ring_rects(logo)
        width = max(1.4, logo.width() * 0.008)
        painter.save()
        painter.setPen(QPen(QColor("#171b22"), width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(outer)
        painter.drawEllipse(inner)
        for angle, _ in RING_SECTORS:
            painter.drawLine(_point_on_circle(inner, angle), _point_on_circle(outer, angle))
        painter.restore()

    def paint_fill(
        self,
        painter: QPainter,
        logo: QRectF,
        fill: float,
        *,
        opacity: float,
    ) -> None:
        outer, inner = self._ring_rects(logo)
        sweep = SECTOR_SWEEP * fill
        paths = [
            (_sector_path(outer, inner, angle, sweep=sweep), color)
            for angle, color in RING_SECTORS
        ]
        self._paint_shadows(painter, paths, logo, opacity=opacity)
        light = logo.center() + QPointF(-logo.width() * 0.20, -logo.height() * 0.23)
        radius = logo.width() * 0.82
        for path, color in paths:
            painter.save()
            painter.setOpacity(opacity)
            painter.fillPath(path, self._volume_gradient(light, radius, color))
            painter.restore()

    def paint_light_point(self, painter: QPainter, logo: QRectF, opacity: float) -> None:
        outer, inner = self._ring_rects(logo)
        center = logo.center() + QPointF(-logo.width() * 0.21, -logo.height() * 0.23)
        radius = logo.width() * 0.075
        clip = self._ring_clip(outer, inner)
        highlight = QRadialGradient(center, radius)
        highlight.setColorAt(0.0, QColor(255, 255, 255, 230))
        highlight.setColorAt(0.35, QColor(255, 255, 255, 120))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.save()
        painter.setClipPath(clip)
        painter.setOpacity(opacity)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(highlight)
        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def transition_texture(self) -> QPixmap:
        if self._transition_texture is None:
            self._transition_texture = self._render_transition_texture()
        return self._transition_texture

    def _render_transition_texture(self) -> QPixmap:
        size = TRANSITION_TEXTURE_SIZE
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        logo = QRectF(8.0, 8.0, size - 16.0, size - 16.0)
        self.paint_fill(painter, logo, 1.0, opacity=1.0)
        self.paint_light_point(painter, logo, 1.0)
        painter.end()
        return pixmap

    def _ring_rects(self, logo: QRectF) -> tuple[QRectF, QRectF]:
        outer = logo.adjusted(1.0, 1.0, -1.0, -1.0)
        inset = outer.width() * (1.0 - INNER_RADIUS_RATIO) / 2
        return outer, outer.adjusted(inset, inset, -inset, -inset)

    def _paint_shadows(
        self,
        painter: QPainter,
        paths: list[tuple[QPainterPath, QColor]],
        logo: QRectF,
        *,
        opacity: float,
    ) -> None:
        offset = min(5.0, logo.width() * 0.015)
        painter.save()
        painter.translate(offset, offset * 1.5)
        painter.setOpacity(opacity * 0.26)
        for path, _ in paths:
            painter.fillPath(path, QColor("#102749"))
        painter.restore()

    def _volume_gradient(self, light: QPointF, radius: float, color: QColor) -> QRadialGradient:
        gradient = QRadialGradient(light, radius, light)
        gradient.setColorAt(0.0, color.lighter(190))
        gradient.setColorAt(0.18, color.lighter(145))
        gradient.setColorAt(0.48, color)
        gradient.setColorAt(0.78, color.darker(132))
        gradient.setColorAt(1.0, color.darker(176))
        return gradient

    def _ring_clip(self, outer: QRectF, inner: QRectF) -> QPainterPath:
        clip = QPainterPath()
        clip.setFillRule(Qt.FillRule.OddEvenFill)
        clip.addEllipse(outer)
        clip.addEllipse(inner)
        return clip
