from __future__ import annotations

import sys
from pathlib import Path


APP_VERSION = "1.0.1"
APP_TITLE = f"CLTassistant V{APP_VERSION}"
VERSION_TEXT = f"CLTassistant V{APP_VERSION}"
WINDOW_LOGICAL_SIZE = (1440, 810)


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative
