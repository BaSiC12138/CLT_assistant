from __future__ import annotations

from .parsing import format_number


FOUR_K_WIDTH = 3840
FOUR_K_HEIGHT = 2160
FOUR_K_PIXELS = FOUR_K_WIDTH * FOUR_K_HEIGHT
FOUR_K_RATIO_DIGITS = 2
MAX_SERVER_4K_UNITS = 16
SERVER_OUT_OF_RANGE = "超出当前服务器选型范围（大于16个3840×2160）"
SERVER_SELECTION_NOTE = (
    "该服务器选型仅为计算整屏总带载分辨率后的初步选型，"
    "更多具体选型应参考企微服务器群内关于每个信号EDID限制的说明及具体的主控型号选择"
)

SERVER_RULES: tuple[tuple[int, str], ...] = (
    (1, "CS4K-G3"),
    (2, "CS6K-G3"),
    (4, "CS8K-G3"),
    (8, "CS16K（双显卡）"),
    (12, "CS16K（三显卡）"),
    (MAX_SERVER_4K_UNITS, "CS16K（四显卡）"),
)


def select_server(total_pixels: int) -> str:
    for max_4k_units, model in SERVER_RULES:
        if total_pixels <= max_4k_units * FOUR_K_PIXELS:
            return model
    return SERVER_OUT_OF_RANGE


def format_four_k_units(total_pixels: int) -> str:
    return format_number(total_pixels / FOUR_K_PIXELS, FOUR_K_RATIO_DIGITS)


def format_resolution_four_k(
    width: int,
    height: int,
    *,
    separator: str = "×",
) -> str:
    units = format_four_k_units(width * height)
    return f"{width}{separator}{height}={units}个3840*2160"
