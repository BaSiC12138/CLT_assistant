from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QPoint
from PySide6.QtGui import QCursor

WM_NCHITTEST = 0x0084
FRAME_BORDER = 7
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17


def resize_hit_code(position: QPoint, width: int, height: int) -> int | None:
    left = position.x() < FRAME_BORDER
    right = position.x() >= width - FRAME_BORDER
    top = position.y() < FRAME_BORDER
    bottom = position.y() >= height - FRAME_BORDER
    if top:
        if left:
            return HTTOPLEFT
        return HTTOPRIGHT if right else HTTOP
    if bottom:
        if left:
            return HTBOTTOMLEFT
        return HTBOTTOMRIGHT if right else HTBOTTOM
    if left:
        return HTLEFT
    return HTRIGHT if right else None


class ApplicationWindowFrameMixin:
    def nativeEvent(self, event_type: bytes, message: int) -> tuple[bool, int]:
        if sys.platform == "win32" and _message_id(message) == WM_NCHITTEST:
            hit_code = self._resize_hit_code()
            if hit_code is not None:
                return True, hit_code
        return super().nativeEvent(event_type, message)

    def _resize_hit_code(self) -> int | None:
        if self.isMaximized():
            return None
        position = self.mapFromGlobal(QCursor.pos())
        return resize_hit_code(position, self.width(), self.height())


def _message_id(message: int) -> int:
    address = int(message)
    return ctypes.cast(address, ctypes.POINTER(wintypes.MSG)).contents.message
