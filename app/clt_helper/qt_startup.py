from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from PySide6.QtCore import QObject, QRect, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QCursor, QPaintEvent, QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from .qt_startup_logo import StartupLogoRenderer


STARTUP_DURATION_MS = 1480
OUTLINE_COMPLETE_MS = 317
FILL_COMPLETE_MS = 1021
OUTLINE_END = OUTLINE_COMPLETE_MS / STARTUP_DURATION_MS
FILL_END = FILL_COMPLETE_MS / STARTUP_DURATION_MS
EXPANSION_END = 1.0
LOGO_DIAMETER_RATIO = 0.24
MAX_LOGO_DIAMETER = 260.0
EXPANSION_OVERSCAN = 1.35
PAINT_MARGIN = 12.0


@dataclass(frozen=True)
class StartupTiming:
    duration_ms: int = STARTUP_DURATION_MS


DEFAULT_STARTUP_TIMING = StartupTiming()


def _phase(progress: float, start: float, end: float) -> float:
    return max(0.0, min(1.0, (progress - start) / (end - start)))


def _ease_out(value: float) -> float:
    return 1.0 - (1.0 - value) ** 3


class StartupSplash(QWidget):
    reveal_requested = Signal()
    transition_changed = Signal(float)
    completed = Signal()

    def __init__(self, timing: StartupTiming = DEFAULT_STARTUP_TIMING) -> None:
        flags = (
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._timing = timing
        self._progress = 0.0
        self._reveal_emitted = False
        self._renderer = StartupLogoRenderer()
        self._animation = self._build_animation()

    def _build_animation(self) -> QVariantAnimation:
        animation = QVariantAnimation(self)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(self._timing.duration_ms)
        animation.valueChanged.connect(self._set_progress)
        animation.finished.connect(self.completed.emit)
        return animation

    def show_on_cursor_screen(self) -> None:
        screen = QApplication.screenAt(QCursor.pos())
        if screen is None:
            raise RuntimeError("No screen is available at the cursor position")
        self.setGeometry(screen.geometry())
        self.show()
        self.raise_()

    def start(self) -> None:
        self._progress = 0.0
        self._reveal_emitted = False
        self._animation.start()

    def _set_progress(self, value: object) -> None:
        old_bounds = self._paint_bounds()
        self._progress = float(value)
        transition = self._transition_progress()
        if self._progress >= FILL_END and not self._reveal_emitted:
            self._reveal_emitted = True
            self.reveal_requested.emit()
        if self._reveal_emitted:
            self.transition_changed.emit(transition)
        dirty = old_bounds.united(self._paint_bounds())
        self.update(dirty)

    def _transition_progress(self) -> float:
        return _ease_out(_phase(self._progress, FILL_END, EXPANSION_END))

    def _logo_rect(self, scale: float = 1.0) -> QRectF:
        diameter = min(min(self.width(), self.height()) * LOGO_DIAMETER_RATIO, MAX_LOGO_DIAMETER)
        diameter *= scale
        center = self.rect().center()
        return QRectF(
            center.x() - diameter / 2,
            center.y() - diameter / 2,
            diameter,
            diameter,
        )

    def _paint_bounds(self) -> QRect:
        logo = self._logo_rect()
        if self._progress >= FILL_END:
            logo = self._transition_rect(self._transition_progress())
        return logo.adjusted(-PAINT_MARGIN, -PAINT_MARGIN, PAINT_MARGIN, PAINT_MARGIN).toAlignedRect()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._progress < FILL_END:
            self._paint_compact_logo(painter)
            return
        self._paint_transition(painter)

    def _paint_compact_logo(self, painter: QPainter) -> None:
        logo = self._logo_rect()
        self._renderer.paint_outline(painter, logo)
        fill = _ease_out(_phase(self._progress, OUTLINE_END, FILL_END))
        if fill <= 0.0:
            return
        self._renderer.paint_fill(painter, logo, fill, opacity=1.0)
        self._renderer.paint_light_point(painter, logo, fill)

    def _paint_transition(self, painter: QPainter) -> None:
        transition = self._transition_progress()
        texture = self._renderer.transition_texture()
        target = self._transition_rect(transition)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(1.0 - transition)
        painter.drawPixmap(target, texture, QRectF(texture.rect()))

    def _transition_rect(self, transition: float) -> QRectF:
        max_scale = self._maximum_expansion_scale()
        scale = 1.0 + (max_scale - 1.0) * transition
        return self._logo_rect(scale)

    def _maximum_expansion_scale(self) -> float:
        logo_diameter = self._logo_rect().width()
        screen_diagonal = hypot(self.width(), self.height())
        return screen_diagonal * EXPANSION_OVERSCAN / logo_diameter


class StartupSequence(QObject):
    def __init__(self, splash: StartupSplash, window: QMainWindow) -> None:
        super().__init__(window)
        self._splash = splash
        self._window = window
        splash.reveal_requested.connect(self._reveal_window)
        splash.transition_changed.connect(self._set_window_opacity)
        splash.completed.connect(self._complete)

    def start(self) -> None:
        self._prepare_window()
        self._splash.start()

    def _prepare_window(self) -> None:
        if self._window.centralWidget() is None:
            raise RuntimeError("The main window content is not ready for startup reveal")
        screen = self._splash.screen()
        if screen is None:
            raise RuntimeError("The startup screen is no longer available")
        self._window.setGeometry(screen.availableGeometry())
        self._window.setWindowOpacity(0.0)
        self._window.showMaximized()
        QApplication.processEvents()

    def _reveal_window(self) -> None:
        if not self._window.isVisible():
            raise RuntimeError("The pre-rendered main window is no longer visible")

    def _set_window_opacity(self, progress: float) -> None:
        self._window.setWindowOpacity(progress)
        if progress >= 1.0:
            self._splash.hide()

    def _complete(self) -> None:
        if not self._window.isVisible():
            raise RuntimeError("The main window closed before startup completed")
        self._window.setWindowOpacity(1.0)
        self._splash.close()
