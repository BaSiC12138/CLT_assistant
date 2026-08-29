from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ICON_CANVAS_SIZE = 512
SUPERSAMPLING_SCALE = 8
OUTER_MARGIN = 28
INNER_RADIUS_RATIO = 0.37
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
RING_SECTORS = (
    (270, 390, (244, 67, 67)),
    (30, 150, (24, 184, 107)),
    (150, 270, (23, 105, 239)),
)


def _sector_mask(start_angle: int, end_angle: int) -> Image.Image:
    from PIL import ImageDraw

    high_size = ICON_CANVAS_SIZE * SUPERSAMPLING_SCALE
    margin = OUTER_MARGIN * SUPERSAMPLING_SCALE
    outer_bounds = (margin, margin, high_size - margin, high_size - margin)
    inner_radius = (high_size - margin * 2) * INNER_RADIUS_RATIO / 2
    center = high_size / 2
    inner_bounds = (
        center - inner_radius,
        center - inner_radius,
        center + inner_radius,
        center + inner_radius,
    )
    mask = Image.new("L", (high_size, high_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.pieslice(outer_bounds, start_angle, end_angle, fill=255)
    draw.ellipse(inner_bounds, fill=0)
    return mask.resize(
        (ICON_CANVAS_SIZE, ICON_CANVAS_SIZE),
        Image.Resampling.LANCZOS,
    )


def _compose_master() -> Image.Image:
    masks = [
        (_sector_mask(start, end), color)
        for start, end, color in RING_SECTORS
    ]
    master = Image.new("RGBA", (ICON_CANVAS_SIZE, ICON_CANVAS_SIZE))
    pixels = master.load()
    mask_pixels = [(mask.load(), color) for mask, color in masks]
    for y in range(ICON_CANVAS_SIZE):
        for x in range(ICON_CANVAS_SIZE):
            weights = [(mask[x, y], color) for mask, color in mask_pixels]
            alpha = min(255, sum(weight for weight, _ in weights))
            if alpha == 0:
                continue
            channels = tuple(
                round(sum(weight * color[channel] for weight, color in weights) / alpha)
                for channel in range(3)
            )
            pixels[x, y] = (*channels, alpha)
    return master


def build_icon(png_path: Path, ico_path: Path) -> None:
    master = _compose_master()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    master.save(png_path, format="PNG", optimize=True)
    master.save(ico_path, format="ICO", sizes=[(size, size) for size in ICON_SIZES])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the CLTassistant Windows icon")
    parser.add_argument("png", type=Path)
    parser.add_argument("ico", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_icon(args.png, args.ico)


if __name__ == "__main__":
    main()
