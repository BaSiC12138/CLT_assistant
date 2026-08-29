from __future__ import annotations

from .models import ControllerBoardSelection

DETAIL_SEPARATOR = "；"

def format_board_details(
    selections: tuple[ControllerBoardSelection, ...],
) -> str:
    return DETAIL_SEPARATOR.join(
        f"{selection.count}张{selection.model}{selection.role.value}卡"
        for selection in selections
    )
