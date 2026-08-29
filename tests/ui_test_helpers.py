from __future__ import annotations

from clt_helper.qt_application import CLTApplication


def configured_window() -> CLTApplication:
    window = CLTApplication()
    window._reset_defaults()
    window._configure_scheme()
    return window
