from __future__ import annotations

import math
from dataclasses import dataclass

from .models import ModuleSpec
from .parsing import format_number


PIXEL_ROUNDING_TOLERANCE = 0.001
MILLIMETER_MATCH_TOLERANCE = 0.01
HALF_MILLIMETER = 0.5
FORMAT_TOLERANCE = 0.000_001


@dataclass(frozen=True)
class CabinetDimensions:
    pixels: tuple[int, int]
    millimeters: tuple[float, float]

    @property
    def pixels_text(self) -> str:
        return f"{self.pixels[0]}×{self.pixels[1]}"

    @property
    def millimeters_text(self) -> str:
        return format_cabinet_millimeters(self.millimeters)


def format_cabinet_millimeters(values: tuple[float, float]) -> str:
    return "×".join(_format_cabinet_millimeter(value) for value in values)


def _format_cabinet_millimeter(value: float) -> str:
    fraction = value - math.floor(value)
    if abs(fraction - HALF_MILLIMETER) <= FORMAT_TOLERANCE:
        return format_number(value, 1)
    return str(round(value))


def dimensions_from_module(
    module: ModuleSpec,
    cabinet_modules: tuple[int, int],
) -> CabinetDimensions:
    pixels = (
        module.pixels_w * cabinet_modules[0],
        module.pixels_h * cabinet_modules[1],
    )
    return dimensions_from_pixels(module.pitch, pixels)


def dimensions_from_pixels(
    pitch: float,
    pixels: tuple[int, int],
) -> CabinetDimensions:
    millimeters = pixels[0] * pitch, pixels[1] * pitch
    return CabinetDimensions(pixels=pixels, millimeters=millimeters)


def dimensions_from_millimeters(
    pitch: float,
    millimeters: tuple[float, float],
) -> CabinetDimensions | None:
    raw_pixels = millimeters[0] / pitch, millimeters[1] / pitch
    pixels = round(raw_pixels[0]), round(raw_pixels[1])
    if any(value <= 0 for value in pixels):
        return None
    differences = (abs(raw_pixels[0] - pixels[0]), abs(raw_pixels[1] - pixels[1]))
    if any(value > PIXEL_ROUNDING_TOLERANCE for value in differences):
        return None
    return CabinetDimensions(pixels=pixels, millimeters=millimeters)


def module_from_cabinet(
    dimensions: CabinetDimensions,
    cabinet_modules: tuple[int, int],
    *,
    pitch: float,
    interface: str,
) -> ModuleSpec | None:
    if not _pixels_match_module_grid(dimensions.pixels, cabinet_modules):
        return None
    expected = dimensions_from_pixels(pitch, dimensions.pixels)
    if not _millimeters_match(dimensions.millimeters, expected.millimeters):
        return None
    pixels_w = dimensions.pixels[0] // cabinet_modules[0]
    pixels_h = dimensions.pixels[1] // cabinet_modules[1]
    width_mm = dimensions.millimeters[0] / cabinet_modules[0]
    height_mm = dimensions.millimeters[1] / cabinet_modules[1]
    return ModuleSpec(pitch, width_mm, height_mm, pixels_w, pixels_h, interface)


def _pixels_match_module_grid(
    pixels: tuple[int, int],
    cabinet_modules: tuple[int, int],
) -> bool:
    return pixels[0] % cabinet_modules[0] == 0 and pixels[1] % cabinet_modules[1] == 0


def _millimeters_match(
    actual: tuple[float, float],
    expected: tuple[float, float],
) -> bool:
    return all(
        abs(actual_value - expected_value) <= MILLIMETER_MATCH_TOLERANCE
        for actual_value, expected_value in zip(actual, expected)
    )
