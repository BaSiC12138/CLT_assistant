from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QStyle,
    QToolButton,
    QWidget,
)


class BrandMark(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(34, 34)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(38, 38)

    def paintEvent(self, _event: QEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height()) - 2
        rect = QRectF((self.width() - size) / 2, (self.height() - size) / 2, size, size)
        painter.setPen(Qt.PenStyle.NoPen)
        for start, color in ((90, "#1769ef"), (210, "#18b86b"), (330, "#f44343")):
            painter.setBrush(QColor(color))
            painter.drawPie(rect, start * 16, 120 * 16)
        inner = rect.adjusted(size * 0.28, size * 0.28, -size * 0.28, -size * 0.28)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#d5dfef"), 1))
        painter.drawEllipse(inner)


class TitleBar(QFrame):
    def __init__(self, target: QMainWindow, settings_menu: QMenu) -> None:
        super().__init__(target)
        self._target = target
        self.setObjectName("Header")
        self._build_layout(settings_menu)
        target.installEventFilter(self)

    def _build_layout(self, settings_menu: QMenu) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 7, 0, 7)
        layout.setSpacing(10)
        self.brand_mark = BrandMark()
        layout.addWidget(self.brand_mark)
        self._add_identity(layout)
        layout.addSpacing(18)
        self.status_label = QLabel("●  当前参数可配置")
        self.status_label.setObjectName("StatusChip")
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        self.settings_button = self._settings_button(settings_menu)
        layout.addWidget(self.settings_button)
        self._add_window_buttons(layout)

    @staticmethod
    def _add_identity(layout: QHBoxLayout) -> None:
        title = QLabel("CLTassistant")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        version = QLabel("Beta")
        version.setObjectName("VersionBadge")
        layout.addWidget(version)

    def _settings_button(self, menu: QMenu) -> QToolButton:
        button = QToolButton()
        button.setObjectName("SettingsButton")
        button.setText("配置选项  ▾")
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setMenu(menu)
        return button

    def _add_window_buttons(self, layout: QHBoxLayout) -> None:
        self.minimize_button = self._control_button("WindowMinimizeButton", "最小化")
        self.maximize_button = self._control_button("WindowMaximizeButton", "最大化")
        self.close_button = self._control_button("WindowCloseButton", "关闭")
        self.minimize_button.clicked.connect(self._target.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(self._target.close)
        for button in (self.minimize_button, self.maximize_button, self.close_button):
            layout.addWidget(button)
        self._update_maximize_icon()

    def _control_button(self, name: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName(name)
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        return button

    def _toggle_maximized(self) -> None:
        if self._target.isMaximized():
            self._target.showNormal()
            return
        self._target.showMaximized()

    def _update_maximize_icon(self) -> None:
        style = self.style()
        maximum = QStyle.StandardPixmap.SP_TitleBarNormalButton
        if not self._target.isMaximized():
            maximum = QStyle.StandardPixmap.SP_TitleBarMaxButton
        self.minimize_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton))
        self.maximize_button.setIcon(style.standardIcon(maximum))
        self.close_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self._target and event.type() == QEvent.Type.WindowStateChange:
            self._update_maximize_icon()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._target.windowHandle():
            self._target.windowHandle().startSystemMove()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
