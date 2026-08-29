from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    pitch: str
    screen_modules: str = ""
    screen_physical: str = ""
    screen_pixels: str = ""
    point_to_point: bool = False
    asynchronous: bool = False
    feature_3d: bool = False
    interface: str = "auto"
    auto_discount: bool = False
    cabinet_modules: str = ""
    screen_cabinets: str = ""
    receiver_override: str = ""


BASE_CASES = (
    Case("P2.5-square-min", "2.5", "1x1"),
    Case("P2.5-square-2", "2.5", "2x2"),
    Case("P2.5-square-4", "2.5", "4x4"),
    Case("P2.5-wide-small", "2.5", "6x3"),
    Case("P2.5-wide", "2.5", "8x4"),
    Case("P2.5-default", "2.5", "12x12"),
    Case("P2.5-ultrawide", "2.5", "20x5"),
    Case("P2.5-square-20", "2.5", "20x20"),
    Case("P2.5-large", "2.5", "40x20"),
    Case("P2.5-large-portrait", "2.5", "20x40"),
    Case("P2.5-controller-boundary", "2.5", "60x30"),
    Case("P1.25-small", "1.25", "4x4"),
    Case("P1.25-medium", "1.25", "8x8"),
    Case("P1.25-default-shape", "1.25", "12x12"),
    Case("P1.25-wide", "1.25", "20x10"),
    Case("P1.5", "1.5", "12x8"),
    Case("P1.53", "1.53", "12x8"),
    Case("P1.667", "1.667", "16x10"),
    Case("P1.86", "1.86", "16x10"),
    Case("P2.0", "2", "16x10"),
    Case("P3.0", "3", "16x8"),
    Case("P3.076", "3.076", "16x10"),
    Case("P3.91", "3.91", "16x8"),
    Case("P4.0", "4", "20x10"),
    Case("P4.81", "4.81", "20x10"),
    Case("P5.0", "5", "24x12"),
    Case("P6.0", "6", "24x12"),
    Case("P8.0", "8", "30x15"),
    Case("P10.0", "10", "30x15"),
)

VERTICAL_CASES = tuple(
    Case(f"P2.5-height-{height}", "2.5", f"20x{height}")
    for height in (6, 8, 10, 12, 14, 15, 16, 17, 18, 24, 30, 31, 32, 33, 40, 48, 49)
) + tuple(
    Case(f"P{pitch}-height-{height}", pitch, f"12x{height}")
    for pitch in ("1.25", "1.5", "1.53", "1.667", "1.86", "2")
    for height in (6, 7, 8, 9, 10, 11, 12)
)

CONTROLLER_CASES = tuple(
    Case(f"P2.5-ports-{ports}", "2.5", f"{(ports - 1) * 6 + 1}x12")
    for ports in range(1, 25)
)

INPUT_CASES = (
    Case("modules-default", "2.5", screen_modules="12x12"),
    Case("physical-default", "2.5", screen_physical="3.84x1.92"),
    Case("pixels-default", "2.5", screen_pixels="1536x768"),
    Case("modules-wide", "1.53", screen_modules="20x8"),
    Case("physical-wide", "1.53", screen_physical="6.4x1.28"),
    Case("pixels-wide", "1.53", screen_pixels="4160x832"),
)

OPTION_CASES = (
    Case("options-default", "2.5", "12x12"),
    Case("point-to-point", "2.5", "12x12", point_to_point=True),
    Case("asynchronous", "2.5", "12x12", asynchronous=True),
    Case("feature-3d", "2.5", "12x12", feature_3d=True),
    Case("force-75", "1.53", "12x8", interface="75"),
    Case("force-320", "2.5", "12x12", interface="320"),
    Case("auto-discount", "2.5", "20x20", auto_discount=True),
    Case("combined", "1.53", "20x12", point_to_point=True, feature_3d=True, auto_discount=True),
)

CABINET_CASES = (
    Case("cabinet-default", "2.5", cabinet_modules="2x3", screen_cabinets="6x4", receiver_override="E320"),
    Case("cabinet-single", "2.5", cabinet_modules="1x1", screen_cabinets="12x12", receiver_override="E320"),
    Case("cabinet-wide", "2.5", cabinet_modules="4x2", screen_cabinets="5x3", receiver_override="E320"),
    Case("cabinet-P1.53", "1.53", cabinet_modules="2x2", screen_cabinets="6x4", receiver_override="E320"),
    Case("cabinet-P4", "4", cabinet_modules="4x4", screen_cabinets="5x5", receiver_override="E320"),
)

SUITES = {
    "base": BASE_CASES,
    "vertical": VERTICAL_CASES,
    "controller": CONTROLLER_CASES,
    "input": INPUT_CASES,
    "options": OPTION_CASES,
    "cabinet": CABINET_CASES,
}
