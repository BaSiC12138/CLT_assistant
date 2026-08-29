from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from .models import Configuration
from .routing import RoutedCard, route_cards
from .diagram_typography import card_font_sizes, card_padding

CANVAS_SIZE = (2800, 1400)
CANVAS_MARGIN = 8
CANVAS_BACKGROUND = "#edf4fb"
CARD_INSET = 6
CARD_RADIUS = 22
CARD_SHADOW_OFFSET = 5
CELL_BORDER_COLOR = "#fff6a8"
CABLE_COLOR = "#ffff88"
TEXT_COLOR = "#263238"
PORT_PALETTE = (
    "#d46a6d",
    "#6bc2cf",
    "#f3a0a4",
    "#8580bd",
    "#f2b54c",
    "#7da2d5",
    "#cb8555",
    "#8ea5ba",
    "#f6ce43",
    "#a08ed7",
    "#f5c79a",
    "#d1846f",
    "#5fbd78",
    "#cb64ad",
    "#b3d500",
    "#6d8fd0",
)


@dataclass(frozen=True)
class DiagramLayout:
    screen_width: int
    screen_height: int
    canvas_width: int = CANVAS_SIZE[0]
    canvas_height: int = CANVAS_SIZE[1]
    margin: int = CANVAS_MARGIN

    @property
    def usable_width(self) -> int:
        return self.canvas_width - self.margin * 2

    @property
    def usable_height(self) -> int:
        return self.canvas_height - self.margin * 2


def render_diagram(configuration: Configuration) -> Image.Image:
    cards = route_cards(configuration)
    layout = DiagramLayout(
        configuration.screen.pixels_w,
        configuration.screen.pixels_h,
    )
    image = Image.new("RGB", CANVAS_SIZE, CANVAS_BACKGROUND)
    draw = ImageDraw.Draw(image)
    _draw_card_backgrounds(draw, layout, cards)
    grouped = _cards_by_port(cards)
    _draw_cable_lines(draw, layout, grouped)
    _draw_card_labels(draw, layout, cards)
    _draw_cable_markers(draw, layout, grouped, configuration)
    return image


def generate_diagram(configuration: Configuration, output: Path) -> Path:
    image = render_diagram(configuration)
    image.save(output, format="JPEG", quality=94, subsampling=0)
    return output


def open_diagram(configuration: Configuration, directory: Path | None = None) -> Path:
    output = (directory or Path.cwd()) / "图示.jpg"
    generate_diagram(configuration, output)
    os.startfile(output)
    return output


def _draw_card_backgrounds(
    draw: ImageDraw.ImageDraw,
    layout: DiagramLayout,
    cards: tuple[RoutedCard, ...],
) -> None:
    for card in cards:
        box = _inset_box(_card_box(layout, card), CARD_INSET)
        shadow_box = _shift_box(box, CARD_SHADOW_OFFSET)
        color = _port_color(card.port)
        draw.rounded_rectangle(
            shadow_box,
            radius=CARD_RADIUS,
            fill=_darken(color, factor=0.72),
        )
        draw.rounded_rectangle(
            box,
            radius=CARD_RADIUS,
            fill=color,
            outline=CELL_BORDER_COLOR,
            width=3,
        )
        left, top, right, _ = box
        highlight = _lighten(color, factor=0.38)
        draw.line((left + CARD_RADIUS, top + 4, right - CARD_RADIUS, top + 4), fill=highlight, width=4)


def _draw_card_labels(
    draw: ImageDraw.ImageDraw,
    layout: DiagramLayout,
    cards: tuple[RoutedCard, ...],
) -> None:
    for card in cards:
        left, top, right, bottom = _card_box(layout, card)
        cell_width = right - left
        cell_height = bottom - top
        index_text = f"index: {card.chain}"
        width_text = f"W: {card.width}"
        height_text = f"H: {card.height}"
        index_size, detail_size = card_font_sizes(cell_width, cell_height)
        padding = card_padding(cell_width)
        index_font = _fit_font(draw, index_text, cell_width - padding * 2, preferred=index_size)
        detail_font = _fit_font(draw, width_text, cell_width - padding * 2, preferred=detail_size)
        draw.text((left + padding, top + padding), index_text, fill=TEXT_COLOR, font=index_font)
        draw.text((left + padding, top + cell_height * 0.30), width_text, fill=TEXT_COLOR, font=detail_font)
        draw.text((left + padding, top + cell_height * 0.57), height_text, fill=TEXT_COLOR, font=detail_font)


def _draw_cable_lines(
    draw: ImageDraw.ImageDraw,
    layout: DiagramLayout,
    grouped: dict[int, tuple[RoutedCard, ...]],
) -> None:
    for cards in grouped.values():
        centers = tuple(_card_center(layout, card) for card in cards)
        for start, end in zip(centers, centers[1:]):
            draw.line((*start, *end), fill=CABLE_COLOR, width=5)


def _draw_cable_markers(
    draw: ImageDraw.ImageDraw,
    layout: DiagramLayout,
    grouped: dict[int, tuple[RoutedCard, ...]],
    configuration: Configuration,
) -> None:
    for port, cards in grouped.items():
        centers = tuple(_card_center(layout, card) for card in cards)
        for start, end in zip(centers, centers[1:]):
            _draw_chevron(draw, start, end)
        _draw_start_marker(draw, layout, cards[0], configuration)
        _draw_end_marker(draw, centers[-1])


def _draw_chevron(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
) -> None:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= 1:
        return
    unit_x, unit_y = dx / length, dy / length
    point = (start[0] + dx * 0.52, start[1] + dy * 0.52)
    size = min(28, max(9, length * 0.12))
    back = (point[0] - unit_x * size, point[1] - unit_y * size)
    side_x, side_y = -unit_y * size * 0.58, unit_x * size * 0.58
    left = (back[0] + side_x, back[1] + side_y)
    right = (back[0] - side_x, back[1] - side_y)
    draw.line((*left, *point, *right), fill=CABLE_COLOR, width=5, joint="curve")


def _draw_start_marker(
    draw: ImageDraw.ImageDraw,
    layout: DiagramLayout,
    card: RoutedCard,
    configuration: Configuration,
) -> None:
    center = _card_center(layout, card)
    left, top, right, bottom = _card_box(layout, card)
    radius = min(58, max(9, min(right - left, bottom - top) * 0.18))
    box = (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
    )
    draw.ellipse(box, fill=_darken(_port_color(card.port), factor=0.68))
    label = _port_label(configuration, card.port)
    label_font = _fit_font(draw, label, radius * 1.55, preferred=30, minimum=8)
    draw.text(center, label, fill="white", font=label_font, anchor="mm")


def _draw_end_marker(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
) -> None:
    radius = 8
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=CABLE_COLOR,
    )


def _cards_by_port(
    cards: tuple[RoutedCard, ...],
) -> dict[int, tuple[RoutedCard, ...]]:
    grouped: dict[int, list[RoutedCard]] = {}
    for card in cards:
        grouped.setdefault(card.port, []).append(card)
    return {
        port: tuple(sorted(items, key=lambda card: card.chain))
        for port, items in grouped.items()
    }


def _card_box(
    layout: DiagramLayout,
    card: RoutedCard,
) -> tuple[float, float, float, float]:
    left = layout.margin + card.x / layout.screen_width * layout.usable_width
    top = layout.margin + card.y / layout.screen_height * layout.usable_height
    right = layout.margin + (card.x + card.width) / layout.screen_width * layout.usable_width
    bottom = layout.margin + (card.y + card.height) / layout.screen_height * layout.usable_height
    return left, top, right, bottom


def _card_center(
    layout: DiagramLayout,
    card: RoutedCard,
) -> tuple[float, float]:
    left, top, right, bottom = _card_box(layout, card)
    return (left + right) / 2, (top + bottom) / 2


def _port_label(configuration: Configuration, port: int) -> str:
    ports_per_controller = configuration.plan.controller_output_ports
    controller = (port - 1) // ports_per_controller + 1
    output = (port - 1) % ports_per_controller + 1
    return f"{controller}-{output}"


def _port_color(port: int) -> str:
    return PORT_PALETTE[(port - 1) % len(PORT_PALETTE)]


def _darken(color: str, *, factor: float) -> tuple[int, int, int]:
    return tuple(round(channel * factor) for channel in ImageColor.getrgb(color))


def _lighten(color: str, *, factor: float) -> tuple[int, int, int]:
    return tuple(
        round(channel + (255 - channel) * factor)
        for channel in ImageColor.getrgb(color)
    )


def _inset_box(box: tuple[float, float, float, float], amount: float) -> tuple[float, float, float, float]:
    left, top, right, bottom = box
    return left + amount, top + amount, right - amount, bottom - amount


def _shift_box(box: tuple[float, float, float, float], amount: float) -> tuple[float, float, float, float]:
    left, top, right, bottom = box
    return left + amount, top + amount, right + amount, bottom + amount


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: float,
    *,
    preferred: int,
    minimum: int = 8,
) -> ImageFont.FreeTypeFont:
    size = preferred
    while size > minimum:
        candidate = _font(size)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
        size -= 1
    return _font(minimum)


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    )
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)
