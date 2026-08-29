from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow

from .models import Configuration
from .qt_behavior import ApplicationBehaviorMixin
from .qt_cabinet import ApplicationCabinetMixin
from .qt_mode_state import ApplicationModeStateMixin
from .qt_module_sync import ApplicationModuleSyncMixin
from .qt_panels import ApplicationPanelsMixin
from .qt_shell import ApplicationShellMixin
from .qt_special_mode import ApplicationSpecialModeMixin
from .qt_style import ApplicationStyleMixin
from .qt_window_frame import ApplicationWindowFrameMixin


class CLTApplication(
    ApplicationBehaviorMixin,
    ApplicationModeStateMixin,
    ApplicationModuleSyncMixin,
    ApplicationCabinetMixin,
    ApplicationSpecialModeMixin,
    ApplicationPanelsMixin,
    ApplicationShellMixin,
    ApplicationStyleMixin,
    ApplicationWindowFrameMixin,
    QMainWindow,
):
    def __init__(self) -> None:
        super().__init__()
        self.configuration: Configuration | None = None
        self.module_options = ()
        self.module_index = 0
        self.screen_source = "modules"
        self._diagram_pixmap: QPixmap | None = None
        self._last_scale = 0.0
        self._build_window()
        self._build_settings_menu()
        self._build_ui()
        self._connect_signals()
        self._initialize_startup_state()
