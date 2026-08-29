from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .constants import APP_TITLE, VERSION_TEXT, resource_path
from .models import InterfaceMode
from .qt_title_bar import TitleBar


class ApplicationShellMixin:
    def _build_window(self) -> None:
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(APP_TITLE)
        self.resize(1440, 810)
        self.setMinimumSize(1280, 720)
        icon = resource_path("assets/app.ico")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))

    def _build_settings_menu(self) -> None:
        self.settings_menu = QMenu(self)
        self.backup_action = self._check_action("环路备份")
        self.fiber_action = self._check_action("光纤传输")
        self.settings_menu.addSeparator()
        self._build_interface_actions()
        self.copy_action = self._check_action("复制方案文本", True)
        self.settings_menu.addSeparator()
        reset = self.settings_menu.addAction("恢复预设参数")
        reset.triggered.connect(self._reset_defaults)

    def _build_interface_actions(self) -> None:
        self.interface_group = QActionGroup(self)
        self.interface_group.setExclusive(True)
        self.interface_auto_action = self._interface_action(
            "接口自动",
            InterfaceMode.AUTO,
            checked=True,
        )
        self.interface_75_action = self._interface_action("75接口", InterfaceMode.HUB75)
        self.interface_320_action = self._interface_action("320接口", InterfaceMode.HUB320)

    def _check_action(self, text: str, checked: bool = False) -> QAction:
        action = self.settings_menu.addAction(text)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(self._mark_dirty)
        return action

    def _interface_action(
        self,
        text: str,
        mode: InterfaceMode,
        *,
        checked: bool = False,
    ) -> QAction:
        action = self.settings_menu.addAction(text)
        action.setCheckable(True)
        action.setChecked(checked)
        action.setData(mode.value)
        self.interface_group.addAction(action)
        action.toggled.connect(self._mark_dirty)
        return action

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())
        outer.addWidget(self._build_workspace(), 1)
        outer.addWidget(self._build_footer())

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        workspace.setObjectName("Workspace")
        grid = QGridLayout(workspace)
        grid.setContentsMargins(12, 10, 12, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for index in range(3):
            grid.setColumnStretch(index, 1)
        for index in range(2):
            grid.setRowStretch(index, 1)
        self._populate_workspace(grid)
        return workspace

    def _populate_workspace(self, grid: QGridLayout) -> None:
        self.parameters_panel, params_body = self._panel()
        self.output_panel, output_body = self._panel()
        self.diagram_panel, diagram_body = self._panel()
        grid.addWidget(self.parameters_panel, 0, 0)
        grid.addWidget(self.output_panel, 1, 0)
        grid.addWidget(self.diagram_panel, 0, 1, 2, 2)
        self._build_parameters(params_body)
        self._build_output(output_body)
        self._build_diagram(diagram_body)

    def _build_header(self) -> QWidget:
        self.title_bar = TitleBar(self, self.settings_menu)
        self.brand_mark = self.title_bar.brand_mark
        self.header_status = self.title_bar.status_label
        self.settings_button = self.title_bar.settings_button
        return self.title_bar

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("Footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(16, 3, 16, 3)
        self.footer_status = QLabel("●  当前参数可配置")
        self.footer_status.setObjectName("FooterStatus")
        layout.addWidget(self.footer_status)
        layout.addStretch(1)
        version = QLabel(VERSION_TEXT)
        version.setObjectName("FooterText")
        layout.addWidget(version)
        return footer

    def _panel(self) -> tuple[QFrame, QVBoxLayout]:
        panel = QFrame()
        panel.setObjectName("Panel")
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(18)
        shadow.setOffset(QPointF(0, 4))
        shadow.setColor(QColor(77, 99, 137, 55))
        panel.setGraphicsEffect(shadow)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return panel, layout

    def _panel_header(
        self,
        kicker: str,
        title: str,
        accent: str,
        *,
        trailing: QWidget | None = None,
    ) -> QFrame:
        header = QFrame()
        header.setObjectName("PanelHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 6, 14, 6)
        self._add_accent(layout, accent)
        self._add_panel_labels(layout, kicker, title)
        layout.addStretch(1)
        if trailing is not None:
            layout.addWidget(trailing)
        return header

    @staticmethod
    def _add_accent(layout: QHBoxLayout, accent: str) -> None:
        layout.addWidget(ApplicationShellMixin._accent_bar(accent))

    @staticmethod
    def _accent_bar(accent: str) -> QFrame:
        bar = QFrame()
        bar.setObjectName("AccentBar")
        bar.setStyleSheet(f"background:{accent};")
        bar.setFixedWidth(5)
        return bar

    @staticmethod
    def _add_panel_labels(layout: QHBoxLayout, kicker: str, title: str) -> None:
        labels = QVBoxLayout()
        labels.setSpacing(0)
        labels.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        if kicker:
            kicker_label = QLabel(kicker)
            kicker_label.setObjectName("Kicker")
            labels.addWidget(kicker_label)
        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        labels.addWidget(title_label)
        layout.addLayout(labels)
