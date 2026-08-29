from __future__ import annotations

from dataclasses import dataclass

from .models import Configuration, LoadBand


@dataclass(frozen=True)
class RoutedCard:
    port: int
    chain: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class BlockBounds:
    row: int
    column: int
    width: int
    height: int


def route_cards(configuration: Configuration) -> tuple[RoutedCard, ...]:
    rows = _card_rows(configuration)
    routed: list[RoutedCard] = []
    port = 1
    group_w = configuration.plan.port_group_w
    group_h = configuration.plan.port_group_h
    for row_start in range(0, len(rows), group_h):
        for column_start in range(0, configuration.plan.cards_w, group_w):
            bounds = BlockBounds(row_start, column_start, group_w, group_h)
            block = _block_cards(rows, bounds)
            routed.extend(_route_block(block, port))
            port += 1
    if port - 1 != configuration.plan.primary_ports:
        raise ValueError("Mapping网口分组与方案主链路网口数不一致。")
    return tuple(routed)


def _card_rows(configuration: Configuration) -> tuple[tuple[dict[str, int], ...], ...]:
    rows: list[tuple[dict[str, int], ...]] = []
    y = 0
    for band in configuration.plan.bands:
        for _ in range(band.row_count):
            rows.append(tuple(_row_cards(configuration, band, y)))
            y += band.card_pixels_h
    return tuple(rows)


def _row_cards(
    configuration: Configuration,
    band: LoadBand,
    y: int,
) -> list[dict[str, int]]:
    plan = configuration.plan
    screen = configuration.screen
    height = min(band.card_pixels_h, screen.pixels_h - y)
    cards = []
    for column in range(plan.cards_w):
        x = column * plan.card_pixels_w
        width = min(plan.card_pixels_w, screen.pixels_w - x)
        if width <= 0 or height <= 0:
            raise ValueError("Mapping接收卡坐标超出屏幕范围。")
        cards.append({"x": x, "y": y, "width": width, "height": height})
    return cards


def _block_cards(
    rows: tuple[tuple[dict[str, int], ...], ...],
    bounds: BlockBounds,
) -> tuple[dict[str, int], ...]:
    selected = rows[bounds.row : bounds.row + bounds.height]
    return tuple(
        card
        for row in selected
        for card in row[bounds.column : bounds.column + bounds.width]
    )


def _route_block(block: tuple[dict[str, int], ...], port: int) -> list[RoutedCard]:
    return [
        RoutedCard(port=port, chain=index, **area)
        for index, area in enumerate(block, start=1)
    ]
