from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from clt_helper.constants import APP_VERSION, LATEST_RELEASE_API
from clt_helper.github_releases import GitHubReleaseClient
from clt_helper.qt_application import CLTApplication
from clt_helper.qt_checkbox_style import CheckboxStyle
from clt_helper.qt_startup import StartupSequence, StartupSplash
from clt_helper.qt_update import UpdateController
from clt_helper.updates import UpdateService


def main() -> None:
    application = QApplication(sys.argv)
    application.setStyle(CheckboxStyle())
    application.setFont(QFont("Microsoft YaHei", 11))
    splash = StartupSplash()
    splash.show_on_cursor_screen()
    application.processEvents()
    window = CLTApplication()
    startup = StartupSequence(splash, window)
    release_client = GitHubReleaseClient(LATEST_RELEASE_API)
    update_service = UpdateService(APP_VERSION, release_client.fetch_latest)
    update_controller = UpdateController(window, update_service)
    startup.completed.connect(update_controller.start)
    startup.start()
    exit_code = application.exec()
    update_controller.wait_for_completion()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
