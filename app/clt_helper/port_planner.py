from __future__ import annotations

import math
from dataclasses import dataclass

from .hardware import (
    BASE_PORT_CAPACITY,
    HDR_PORT_CAPACITY,
    MAX_PORT_LOAD_HEIGHT,
    THREE_D_PORT_CAPACITY,
)
from .models import Preferences, ScreenGeometry


@dataclass(frozen=True)
class PortRequest:
    screen: ScreenGeometry
    cards_w: int
    card_pixels_w: int
    row_heights: tuple[int, ...]
    preferences: Preferences
    max_cards_per_port: int | None = None


@dataclass(frozen=True)
class PortPlan:
    group_w: int
    group_h: int
    capacity: int
    primary_ports: int
    required_ports: int
    notes: tuple[str, ...]


@dataclass(frozen=True)
class GroupCandidate:
    width: int
    height: int
    capacity: int


def plan_ports(request: PortRequest) -> PortPlan:
    _validate_row_heights(request.row_heights)
    capacity = _port_capacity(request.preferences)
    candidates = _valid_groups(request, capacity)
    if not candidates:
        raise ValueError("单张接收卡已经超过当前网口带载上限。")
    _, group_w, group_h = min(candidates)
    primary = _port_count(request, group_w, group_h)
    required = primary * (2 if request.preferences.loop_backup else 1)
    return PortPlan(group_w, group_h, capacity, primary, required, ())


def _validate_row_heights(row_heights: tuple[int, ...]) -> None:
    if max(row_heights) <= MAX_PORT_LOAD_HEIGHT:
        return
    raise ValueError(f"单张接收卡带载高度不得超过{MAX_PORT_LOAD_HEIGHT}像素。")


def _port_capacity(preferences: Preferences) -> int:
    if preferences.feature_3d:
        return THREE_D_PORT_CAPACITY
    if preferences.feature_hdr:
        return HDR_PORT_CAPACITY
    return BASE_PORT_CAPACITY


def _valid_groups(
    request: PortRequest,
    capacity: int,
) -> list[tuple[tuple[int, int, int, int, int], int, int]]:
    candidates = []
    for group_w in range(1, request.cards_w + 1):
        for group_h in range(1, len(request.row_heights) + 1):
            if _exceeds_card_limit(request, group_w, group_h):
                continue
            group = GroupCandidate(group_w, group_h, capacity)
            if not _all_blocks_fit(request, group):
                continue
            ports = _port_count(request, group_w, group_h)
            cards = group_w * group_h
            crosses_rows = int(group_h > 1)
            score = (ports, crosses_rows, group_h, -cards, -group_w)
            candidates.append((score, group_w, group_h))
    return candidates


def _exceeds_card_limit(request: PortRequest, width: int, height: int) -> bool:
    limit = request.max_cards_per_port
    return limit is not None and width * height > limit


def _all_blocks_fit(
    request: PortRequest,
    group: GroupCandidate,
) -> bool:
    for row in range(0, len(request.row_heights), group.height):
        height = sum(request.row_heights[row : row + group.height])
        if height > MAX_PORT_LOAD_HEIGHT:
            return False
        for column in range(0, request.cards_w, group.width):
            width = min(
                group.width * request.card_pixels_w,
                request.screen.pixels_w - column * request.card_pixels_w,
            )
            if width * height > group.capacity:
                return False
    return True


def _port_count(request: PortRequest, group_w: int, group_h: int) -> int:
    horizontal = math.ceil(request.cards_w / group_w)
    vertical = math.ceil(len(request.row_heights) / group_h)
    return horizontal * vertical

