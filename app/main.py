from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from clt_helper.qt_application import CLTApplication
from clt_helper.qt_checkbox_style import CheckboxStyle
from clt_helper.qt_startup import StartupSequence, StartupSplash


def main() -> None:
    application = QApplication(sys.argv)
    application.setStyle(CheckboxStyle())
    application.setFont(QFont("Microsoft YaHei", 11))
    splash = StartupSplash()
    splash.show_on_cursor_screen()
    application.processEvents()
    window = CLTApplication()
    startup = StartupSequence(splash, window)
    startup.start()
    raise SystemExit(application.exec())


if __name__ == "__main__":
    main()
