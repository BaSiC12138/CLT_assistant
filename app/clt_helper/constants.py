from __future__ import annotations

import sys
from pathlib import Path


APP_TITLE = "CLTassistant（Beta）"
VERSION_TEXT = "CLTassistant Beta · 方案算法校准中"
WINDOW_LOGICAL_SIZE = (1440, 810)


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative
