from __future__ import annotations

MIN_CARD_FONT_SIZE = 8
MAX_CARD_FONT_SIZE = 40
MAX_DETAIL_FONT_SIZE = 42
CARD_WIDTH_FONT_RATIO = 0.18
CARD_HEIGHT_FONT_RATIO = 0.20
MIN_CARD_PADDING = 5
MAX_CARD_PADDING = 18
CARD_PADDING_RATIO = 0.08


def card_font_sizes(cell_width: float, cell_height: float) -> tuple[int, int]:
    index_size = max(
        MIN_CARD_FONT_SIZE,
        min(
            MAX_CARD_FONT_SIZE,
            round(cell_width * CARD_WIDTH_FONT_RATIO),
            round(cell_height * CARD_HEIGHT_FONT_RATIO),
        ),
    )
    return index_size, min(MAX_DETAIL_FONT_SIZE, index_size + 2)


def card_padding(cell_width: float) -> int:
    return max(
        MIN_CARD_PADDING,
        min(MAX_CARD_PADDING, round(cell_width * CARD_PADDING_RATIO)),
    )
