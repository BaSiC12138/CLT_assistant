from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiverLimits:
    model: str
    max_pixels: int
    max_width: int
    max_height: int
    module_limit: int


@dataclass(frozen=True)
class ControllerLimits:
    model: str
    ports: int
    max_pixels: int
    max_width: int
    max_height: int
    max_4k_inputs: int = 0


BASE_PORT_CAPACITY = 650_000
HDR_PORT_CAPACITY = BASE_PORT_CAPACITY * 3 // 4
THREE_D_PORT_CAPACITY = BASE_PORT_CAPACITY // 2
THREE_D_RECEIVER_DIVISOR = 2
MAX_PORT_LOAD_HEIGHT = 1024
RECEIVER_MAX_PIXELS = 512 * 512

RECEIVER_LIMITS: dict[str, ReceiverLimits] = {
    "5A-75E": ReceiverLimits("5A-75E", RECEIVER_MAX_PIXELS, 512, 512, 16),
    "E80": ReceiverLimits("E80", RECEIVER_MAX_PIXELS, 512, 512, 8),
    "E120": ReceiverLimits("E120", RECEIVER_MAX_PIXELS, 512, 512, 12),
    "E320": ReceiverLimits("E320", RECEIVER_MAX_PIXELS, 512, 512, 8),
    "E80-G2": ReceiverLimits("E80-G2", RECEIVER_MAX_PIXELS, 512, 512, 8),
    "K5+": ReceiverLimits("K5+", 512 * 384, 512, 384, 64),
    "K8": ReceiverLimits("K8", 640 * 360, 640, 360, 16),
    "K10": ReceiverLimits("K10", 768 * 432, 768, 432, 16),
}

CABINET_RECEIVER_MODELS = ("K5+", "K8", "K10")

SYNC_CONTROLLER_LIMITS: tuple[ControllerLimits, ...] = (
    ControllerLimits("X2s", 2, 1_310_000, 4096, 2560),
    ControllerLimits("X4s", 4, 2_600_000, 4096, 2560),
    ControllerLimits("X6", 6, 3_900_000, 8192, 4096),
    ControllerLimits("X7", 8, 5_200_000, 8192, 4096),
    ControllerLimits("X8E", 8, 5_240_000, 16_384, 8192, 2),
    ControllerLimits("X12", 12, 7_800_000, 8192, 4096),
    ControllerLimits("X12m", 12, 7_860_000, 16_384, 8192, 2),
    ControllerLimits("X16E", 16, 10_480_000, 16_384, 8192, 2),
    ControllerLimits("X20", 20, 13_000_000, 16_384, 8192, 2),
    ControllerLimits("X26m", 26, 17_030_000, 16_384, 8192, 2),
    ControllerLimits("X40m", 40, 26_210_000, 16_384, 8192, 2),
)

ASYNC_CONTROLLER_LIMITS: tuple[ControllerLimits, ...] = (
    ControllerLimits("A35", 1, 650_000, 4096, 3840),
    ControllerLimits("A100", 2, 1_300_000, 4096, 2560),
    ControllerLimits("A200", 4, 2_300_000, 4096, 2560),
    ControllerLimits("A500", 8, 5_200_000, 7680, 4096),
    ControllerLimits("A800", 16, 8_800_000, 8192, 4320),
)

THREE_D_CONTROLLER_LIMITS: tuple[ControllerLimits, ...] = (
    ControllerLimits("X16E-3D", 16, 10_480_000, 16_384, 8192, 2),
    ControllerLimits("X20-3D", 20, 13_000_000, 16_384, 8192, 2),
)

HDR_CONTROLLER_LIMITS: tuple[ControllerLimits, ...] = (
    ControllerLimits("Z5", 16, 9_830_000, 16_384, 8192, 3),
)
