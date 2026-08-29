from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .hardware import RECEIVER_LIMITS, THREE_D_RECEIVER_DIVISOR, ReceiverLimits
from .models import InterfaceMode, LoadBand, ModuleSpec, Preferences, ScreenGeometry


MAX_MODULES_WIDE = 4
MAX_MODULES_HIGH = 10
MAX_PIXEL_HEIGHT = 1024
NORMAL_HUB75_MODELS = ("E80", "E120", "5A-75E")
THREE_D_HUB75_MODELS = ("E120", "5A-75E")
HDR_HUB75_MODELS = ("E80-G2",)


@dataclass(frozen=True)
class ReceiverRequest:
    module: ModuleSpec
    screen: ScreenGeometry
    preferences: Preferences
    override: str | None = None


@dataclass(frozen=True)
class ReceiverPlan:
    model: str
    modules_w: int
    modules_h: int
    bands: tuple[LoadBand, ...]


def plan_receiver_options(request: ReceiverRequest) -> tuple[ReceiverPlan, ...]:
    models = _candidate_models(request)
    options = tuple(
        plan
        for model in models
        if (plan := _build_plan(request, model)) is not None
    )
    if options:
        return options
    discount = request.preferences.receiver_discount.value
    raise ValueError(
        f"当前模组与打折方式无法满足接收卡限制：每卡{discount}张模组宽，"
        "请调整接收卡打折数量。"
    )


def _candidate_models(request: ReceiverRequest) -> tuple[str, ...]:
    if request.override:
        return (_normalize_override(request),)
    if request.preferences.feature_hdr:
        return HDR_HUB75_MODELS
    if request.preferences.feature_3d:
        return THREE_D_HUB75_MODELS
    if _uses_e320(request):
        return ("E320",)
    return NORMAL_HUB75_MODELS


def _normalize_override(request: ReceiverRequest) -> str:
    model = request.override.strip().upper()
    model = "E80" if model == "5A-75B" else model
    if model.startswith("K"):
        raise ValueError("模组配置模式禁止使用K系列接收卡。")
    if model not in RECEIVER_LIMITS:
        raise ValueError(f"未知接收卡型号：{request.override}")
    if model == "E80-G2" and not request.preferences.feature_hdr:
        raise ValueError("E80-G2仅用于模组配置模式的HDR方案。")
    if model == "E320" and not _uses_e320(request):
        raise ValueError("E320仅用于P1.25的HUB320模组方案。")
    return model


def _uses_e320(request: ReceiverRequest) -> bool:
    if request.module.pitch != 1.25:
        return False
    return request.preferences.interface is not InterfaceMode.HUB75


def _build_plan(request: ReceiverRequest, model: str) -> ReceiverPlan | None:
    width = min(request.preferences.receiver_discount.value, request.screen.modules_w)
    if width > MAX_MODULES_WIDE:
        return None
    limits = _effective_limits(RECEIVER_LIMITS[model], request.preferences)
    maximum = _maximum_height(request, limits, width)
    if maximum <= 0:
        return None
    bands = _balanced_bands(request.module, request.screen.modules_h, maximum)
    actual_height = max(band.card_modules_h for band in bands)
    return ReceiverPlan(model, width, actual_height, bands)


def _effective_limits(
    limits: ReceiverLimits,
    preferences: Preferences,
) -> ReceiverLimits:
    if not preferences.feature_3d:
        return limits
    return replace(limits, max_pixels=limits.max_pixels // THREE_D_RECEIVER_DIVISOR)


def _maximum_height(
    request: ReceiverRequest,
    limits: ReceiverLimits,
    width: int,
) -> int:
    module = request.module
    card_width = width * module.pixels_w
    row_pixels = card_width * module.pixels_h
    if card_width > limits.max_width or row_pixels > limits.max_pixels:
        return 0
    bounds = (
        MAX_MODULES_HIGH,
        limits.module_limit // width,
        limits.max_pixels // row_pixels,
        MAX_PIXEL_HEIGHT // module.pixels_h,
        request.screen.modules_h,
    )
    return min(bounds)


def _balanced_bands(
    module: ModuleSpec,
    screen_height: int,
    maximum: int,
) -> tuple[LoadBand, ...]:
    rows = math.ceil(screen_height / maximum)
    short_height, tall_rows = divmod(screen_height, rows)
    bands: list[LoadBand] = []
    if tall_rows:
        bands.append(_band(module, short_height + 1, tall_rows))
    short_rows = rows - tall_rows
    if short_rows:
        bands.append(_band(module, short_height, short_rows))
    return tuple(bands)


def _band(module: ModuleSpec, height: int, rows: int) -> LoadBand:
    return LoadBand(
        card_modules_h=height,
        card_pixels_h=height * module.pixels_h,
        cards_per_port=1,
        row_count=rows,
    )
