from __future__ import annotations

from dataclasses import dataclass, replace

from .hardware import (
    CABINET_RECEIVER_MODELS,
    RECEIVER_LIMITS,
    THREE_D_RECEIVER_DIVISOR,
    ReceiverLimits,
)
from .models import Preferences


@dataclass(frozen=True)
class CabinetReceiverRequest:
    selected_model: str | None
    width: int
    height: int
    preferences: Preferences


def _effective_limits(limits: ReceiverLimits, preferences: Preferences) -> ReceiverLimits:
    if not preferences.feature_3d:
        return limits
    return replace(
        limits,
        max_pixels=limits.max_pixels // THREE_D_RECEIVER_DIVISOR,
        module_limit=max(1, limits.module_limit // THREE_D_RECEIVER_DIVISOR),
    )


def validate_receiver_load(
    model: str,
    width: int,
    height: int,
    *,
    preferences: Preferences,
) -> None:
    limits = _effective_limits(RECEIVER_LIMITS[model], preferences)
    dimensions_fit = width <= limits.max_width and height <= limits.max_height
    if dimensions_fit and width * height <= limits.max_pixels:
        return
    raise ValueError(
        f"{model}单卡带载上限为{limits.max_width}×{limits.max_height}像素，"
        f"当前模式不超过{limits.max_pixels}像素，单卡需要{width}×{height}像素。"
    )


def select_cabinet_receiver(request: CabinetReceiverRequest) -> str:
    selected = (request.selected_model or "自动").strip()
    if selected != "自动":
        _validate_cabinet_model(selected)
        _validate_cabinet_request(selected, request)
        return selected
    model = next(
        (item for item in CABINET_RECEIVER_MODELS if _cabinet_request_fits(item, request)),
        None,
    )
    if model:
        return model
    raise ValueError(
        f"当前箱体单卡需要{request.width}×{request.height}像素，"
        "K5+、K8、K10均无法满足当前模式带载。"
    )


def _validate_cabinet_model(model: str) -> None:
    if model not in CABINET_RECEIVER_MODELS:
        raise ValueError(f"箱体模式不支持接收卡型号：{model}")


def _validate_cabinet_request(model: str, request: CabinetReceiverRequest) -> None:
    validate_receiver_load(
        model,
        request.width,
        request.height,
        preferences=request.preferences,
    )


def _cabinet_request_fits(model: str, request: CabinetReceiverRequest) -> bool:
    limits = _effective_limits(RECEIVER_LIMITS[model], request.preferences)
    dimensions_fit = (
        request.width <= limits.max_width
        and request.height <= limits.max_height
    )
    return dimensions_fit and request.width * request.height <= limits.max_pixels

