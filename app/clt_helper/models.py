from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class UnitMode(str, Enum):
    MODULE = "模组配置"
    CABINET = "箱体配置"
    SPECIAL = "特殊模式"


class InterfaceMode(str, Enum):
    AUTO = "自动"
    HUB75 = "75接口"
    HUB320 = "320接口"


class ReceiverDiscount(int, Enum):
    NONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4

    @property
    def label(self) -> str:
        return {
            ReceiverDiscount.NONE: "不打折",
            ReceiverDiscount.TWO: "打2折",
            ReceiverDiscount.THREE: "打3折",
            ReceiverDiscount.FOUR: "打4折",
        }[self]


class BoardRole(str, Enum):
    INPUT = "输入板"
    OUTPUT = "输出板"


@dataclass(frozen=True)
class ModuleSpec:
    pitch: float
    width_mm: float
    height_mm: float
    pixels_w: int
    pixels_h: int
    interface: str = "75接口"

    @property
    def size_text(self) -> str:
        return f"{self.width_mm:g}x{self.height_mm:g}"

    @property
    def pixels_text(self) -> str:
        return f"{self.pixels_w}x{self.pixels_h}"


@dataclass(frozen=True)
class ScreenGeometry:
    modules_w: int
    modules_h: int
    width_m: float
    height_m: float
    pixels_w: int
    pixels_h: int

    @property
    def area_m2(self) -> float:
        return self.width_m * self.height_m


@dataclass(frozen=True)
class ScreenInputs:
    module_count: str = ""
    physical_size: str = ""
    pixel_size: str = ""


@dataclass(frozen=True)
class Preferences:
    point_to_point: bool = False
    asynchronous: bool = False
    feature_3d: bool = False
    feature_hdr: bool = False
    loop_backup: bool = False
    fiber_transmission: bool = False
    interface: InterfaceMode = InterfaceMode.AUTO
    receiver_discount: ReceiverDiscount = ReceiverDiscount.NONE
    copy_text: bool = True


@dataclass(frozen=True)
class LoadBand:
    card_modules_h: int
    card_pixels_h: int
    cards_per_port: int
    row_count: int


@dataclass(frozen=True)
class ControllerBoardSelection:
    role: BoardRole
    model: str
    count: int


@dataclass(frozen=True)
class LoadPlan:
    card_modules_w: int
    card_pixels_w: int
    cards_w: int
    bands: tuple[LoadBand, ...]
    port_group_w: int
    port_group_h: int
    port_capacity: int
    primary_ports: int
    required_ports: int
    receiver_model: str
    controller_model: str
    controller_count: int
    controller_output_ports: int
    accessories: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    controller_boards: tuple[ControllerBoardSelection, ...] = ()

    @property
    def cards_h(self) -> int:
        return sum(band.row_count for band in self.bands)

    @property
    def card_modules_h(self) -> int:
        return max(band.card_modules_h for band in self.bands)

    @property
    def card_pixels_h(self) -> int:
        return max(band.card_pixels_h for band in self.bands)

    @property
    def cards_per_port(self) -> int:
        return self.port_group_w * self.port_group_h

    @property
    def card_count(self) -> int:
        return self.cards_w * self.cards_h


@dataclass(frozen=True)
class Configuration:
    module: ModuleSpec
    screen: ScreenGeometry
    plan: LoadPlan
    preferences: Preferences
    cabinet_shape: tuple[int, int] | None
    result_text: str
