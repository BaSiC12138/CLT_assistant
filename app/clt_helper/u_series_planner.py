from __future__ import annotations

import math
from dataclasses import dataclass

from .models import BoardRole, ControllerBoardSelection
from .server_planner import FOUR_K_PIXELS

U20_PORTS = 20
U20_PIXELS = 13_000_000
SINGLE_INPUT_BOARD = "1路HDMI2.0+1路DP1.2"
DUAL_INPUT_BOARD = "2路HDMI+2路DP1.2"
OUTPUT_BOARD = "U_OUT_20×1G_RJ45"


@dataclass(frozen=True)
class UChassis:
    model: str
    slots: int
    max_input_boards: int
    max_u20_boards: int
    max_1g_pixels: int

    @property
    def max_ports(self) -> int:
        return self.max_u20_boards * U20_PORTS


@dataclass(frozen=True)
class USeriesPlan:
    model: str
    count: int
    output_ports: int
    accessories: tuple[str, ...]
    notes: tuple[str, ...]
    boards: tuple[ControllerBoardSelection, ...]


@dataclass(frozen=True)
class InputBoardPlan:
    single_count: int
    dual_count: int

    @property
    def board_count(self) -> int:
        return self.single_count + self.dual_count

    @property
    def capacity_4k(self) -> int:
        return self.single_count + self.dual_count * 2


@dataclass(frozen=True)
class UBoardPlan:
    output_count: int
    input: InputBoardPlan


U_CHASSIS: tuple[UChassis, ...] = (
    UChassis("U3 Max", 8, 5, 3, 39_000_000),
    UChassis("U6 Max", 15, 10, 5, 65_000_000),
    UChassis("U9 Max", 20, 18, 5, 65_000_000),
    UChassis("U15 Max", 40, 30, 20, 260_000_000),
)


def plan_u_series(required_ports: int, pixels: int) -> USeriesPlan:
    for chassis in U_CHASSIS:
        boards = _plan_boards(chassis, required_ports, pixels)
        if boards:
            return _build_plan(chassis, 1, boards)
    count, boards = _plan_multiple_u15(required_ports, pixels)
    return _build_plan(U_CHASSIS[-1], count, boards)


def _plan_boards(
    chassis: UChassis,
    required_ports: int,
    pixels: int,
) -> UBoardPlan | None:
    output_count = max(
        math.ceil(required_ports / U20_PORTS),
        math.ceil(pixels / U20_PIXELS),
    )
    if output_count > chassis.max_u20_boards or pixels > chassis.max_1g_pixels:
        return None
    available_inputs = min(chassis.max_input_boards, chassis.slots - output_count)
    required_4k = math.ceil(pixels / FOUR_K_PIXELS)
    input_plan = _plan_input_boards(required_4k, available_inputs)
    return UBoardPlan(output_count, input_plan) if input_plan else None


def _plan_input_boards(required_4k: int, available_slots: int) -> InputBoardPlan | None:
    if required_4k > available_slots * 2:
        return None
    dual_count = max(0, required_4k - available_slots)
    single_count = required_4k - dual_count * 2
    return InputBoardPlan(single_count=single_count, dual_count=dual_count)


def _plan_multiple_u15(required_ports: int, pixels: int) -> tuple[int, UBoardPlan]:
    chassis = U_CHASSIS[-1]
    count = max(
        2,
        math.ceil(required_ports / chassis.max_ports),
        math.ceil(pixels / chassis.max_1g_pixels),
    )
    while True:
        ports_per_device = math.ceil(required_ports / count)
        pixels_per_device = math.ceil(pixels / count)
        boards = _plan_boards(chassis, ports_per_device, pixels_per_device)
        if boards:
            return count, boards
        count += 1


def _build_plan(
    chassis: UChassis,
    count: int,
    boards: UBoardPlan,
) -> USeriesPlan:
    output_ports = boards.output_count * U20_PORTS
    selections = _board_selections(boards, count)
    return USeriesPlan(
        model=chassis.model,
        count=count,
        output_ports=output_ports,
        accessories=_accessories(selections),
        notes=_notes(chassis, boards),
        boards=selections,
    )


def _board_selections(
    boards: UBoardPlan,
    device_count: int,
) -> tuple[ControllerBoardSelection, ...]:
    selections: list[ControllerBoardSelection] = []
    if boards.input.single_count:
        total = boards.input.single_count * device_count
        selections.append(ControllerBoardSelection(BoardRole.INPUT, SINGLE_INPUT_BOARD, total))
    if boards.input.dual_count:
        total = boards.input.dual_count * device_count
        selections.append(ControllerBoardSelection(BoardRole.INPUT, DUAL_INPUT_BOARD, total))
    output_total = boards.output_count * device_count
    selections.append(ControllerBoardSelection(BoardRole.OUTPUT, OUTPUT_BOARD, output_total))
    return tuple(selections)


def _accessories(
    selections: tuple[ControllerBoardSelection, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{selection.role.value} {selection.model} × {selection.count}"
        for selection in selections
    )


def _notes(chassis: UChassis, boards: UBoardPlan) -> tuple[str, ...]:
    used_slots = boards.output_count + boards.input.board_count
    return (
        f"每台{chassis.model}配置{boards.output_count}张U20输出板，"
        f"共{boards.output_count * U20_PORTS}个1G网口。",
        f"每台主控的输入板合计可带载{boards.input.capacity_4k}个3840×2160信号。",
        f"每台占用{used_slots}/{chassis.slots}个板卡槽，输入、输出板卡已联合校验。",
    )
