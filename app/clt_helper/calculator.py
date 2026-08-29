from __future__ import annotations

import math
from dataclasses import replace

from .controller_planner import ControllerRequest, plan_controller
from .module_receiver_planner import ReceiverPlan, ReceiverRequest, plan_receiver_options
from .models import (
    Configuration,
    LoadBand,
    LoadPlan,
    ModuleSpec,
    Preferences,
    ScreenGeometry,
    ScreenInputs,
)
from .parsing import parse_int_pair, parse_pair
from .port_planner import PortRequest, plan_ports
from .receiver_planner import (
    CabinetReceiverRequest,
    select_cabinet_receiver,
)
from .result_formatter import format_result

K5_MAX_CARDS_PER_PORT = 64


def screen_from_modules(module: ModuleSpec, pair: tuple[int, int]) -> ScreenGeometry:
    modules_w, modules_h = pair
    return ScreenGeometry(
        modules_w=modules_w,
        modules_h=modules_h,
        width_m=modules_w * module.width_mm / 1000,
        height_m=modules_h * module.height_mm / 1000,
        pixels_w=modules_w * module.pixels_w,
        pixels_h=modules_h * module.pixels_h,
    )


def infer_screen(
    module: ModuleSpec,
    inputs: ScreenInputs,
) -> ScreenGeometry | None:
    module_pair = parse_int_pair(inputs.module_count)
    if module_pair:
        return screen_from_modules(module, module_pair)
    physical_pair = parse_pair(inputs.physical_size)
    if physical_pair:
        return _screen_from_physical(module, physical_pair)
    pixel_pair = parse_int_pair(inputs.pixel_size)
    return _screen_from_pixels(module, pixel_pair) if pixel_pair else None


def _screen_from_physical(
    module: ModuleSpec,
    pair: tuple[float, float],
) -> ScreenGeometry | None:
    raw = pair[0] * 1000 / module.width_mm, pair[1] * 1000 / module.height_mm
    counts = _rounded_counts(raw)
    return screen_from_modules(module, counts) if counts else None


def _screen_from_pixels(
    module: ModuleSpec,
    pair: tuple[int, int],
) -> ScreenGeometry | None:
    raw = pair[0] / module.pixels_w, pair[1] / module.pixels_h
    counts = _rounded_counts(raw)
    return screen_from_modules(module, counts) if counts else None


def _rounded_counts(pair: tuple[float, float]) -> tuple[int, int] | None:
    width, height = round(pair[0]), round(pair[1])
    if width <= 0 or height <= 0:
        return None
    if abs(pair[0] - width) > 0.01 or abs(pair[1] - height) > 0.01:
        return None
    return width, height


def calculate_configuration(
    module: ModuleSpec,
    screen: ScreenGeometry,
    preferences: Preferences,
    *,
    receiver_override: str | None = None,
    card_shape_override: tuple[int, int] | None = None,
) -> Configuration:
    if card_shape_override:
        plan = _build_cabinet_plan(
            module,
            screen,
            preferences,
            card_shape=card_shape_override,
            receiver_override=receiver_override,
        )
    else:
        plan = _build_module_plan(
            module,
            screen,
            preferences,
            receiver_override=receiver_override,
        )
    discount = None if card_shape_override else preferences.receiver_discount
    result = format_result(
        module,
        screen,
        plan,
        preferences=preferences,
        discount=discount,
        cabinet_shape=card_shape_override,
    )
    return Configuration(
        module=module,
        screen=screen,
        plan=plan,
        preferences=preferences,
        cabinet_shape=card_shape_override,
        result_text=result,
    )


def _build_module_plan(
    module: ModuleSpec,
    screen: ScreenGeometry,
    preferences: Preferences,
    *,
    receiver_override: str | None,
) -> LoadPlan:
    request = ReceiverRequest(module, screen, preferences, receiver_override)
    plans = tuple(
        _finish_module_option(
            module=module,
            screen=screen,
            preferences=preferences,
            receiver=receiver,
        )
        for receiver in plan_receiver_options(request)
    )
    return min(plans, key=lambda plan: (plan.primary_ports, plan.card_count))


def _finish_module_option(
    *,
    module: ModuleSpec,
    screen: ScreenGeometry,
    preferences: Preferences,
    receiver: ReceiverPlan,
) -> LoadPlan:
    cards_w = math.ceil(screen.modules_w / receiver.modules_w)
    return _finish_plan(
        module=module,
        screen=screen,
        preferences=preferences,
        receiver_model=receiver.model,
        card_modules_w=receiver.modules_w,
        cards_w=cards_w,
        bands=receiver.bands,
        row_heights=_expand_row_heights(receiver.bands),
        max_cards_per_port=None,
    )


def _build_cabinet_plan(
    module: ModuleSpec,
    screen: ScreenGeometry,
    preferences: Preferences,
    *,
    card_shape: tuple[int, int],
    receiver_override: str | None,
) -> LoadPlan:
    modules_w, modules_h = card_shape
    card_width = modules_w * module.pixels_w
    card_height = modules_h * module.pixels_h
    receiver_model = select_cabinet_receiver(
        CabinetReceiverRequest(
            selected_model=receiver_override,
            width=card_width,
            height=card_height,
            preferences=preferences,
        )
    )
    cards_w = math.ceil(screen.modules_w / modules_w)
    cards_h = math.ceil(screen.modules_h / modules_h)
    band = LoadBand(modules_h, card_height, 1, cards_h)
    rows = tuple(card_height for _ in range(cards_h))
    return _finish_plan(
        module=module,
        screen=screen,
        preferences=preferences,
        receiver_model=receiver_model,
        card_modules_w=modules_w,
        cards_w=cards_w,
        bands=(band,),
        row_heights=rows,
        max_cards_per_port=(K5_MAX_CARDS_PER_PORT if receiver_model == "K5+" else None),
    )


def _finish_plan(
    *,
    module: ModuleSpec,
    screen: ScreenGeometry,
    preferences: Preferences,
    receiver_model: str,
    card_modules_w: int,
    cards_w: int,
    bands: tuple[LoadBand, ...],
    row_heights: tuple[int, ...],
    max_cards_per_port: int | None,
) -> LoadPlan:
    card_pixels_w = card_modules_w * module.pixels_w
    port_request = PortRequest(
        screen,
        cards_w,
        card_pixels_w,
        row_heights,
        preferences,
        max_cards_per_port,
    )
    ports = plan_ports(port_request)
    controller = plan_controller(ControllerRequest(screen, ports.required_ports, preferences))
    per_port = ports.group_w * ports.group_h
    updated_bands = tuple(replace(band, cards_per_port=per_port) for band in bands)
    return LoadPlan(
        card_modules_w,
        card_pixels_w,
        cards_w,
        updated_bands,
        ports.group_w,
        ports.group_h,
        ports.capacity,
        ports.primary_ports,
        ports.required_ports,
        receiver_model,
        controller.model,
        controller.count,
        controller.output_ports,
        controller.accessories,
        ports.notes + controller.notes,
        controller.boards,
    )


def _expand_row_heights(bands: tuple[LoadBand, ...]) -> tuple[int, ...]:
    return tuple(
        band.card_pixels_h
        for band in bands
        for _ in range(band.row_count)
    )
