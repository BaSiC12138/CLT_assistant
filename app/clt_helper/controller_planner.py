from __future__ import annotations

from dataclasses import dataclass, replace

from .hardware import (
    ASYNC_CONTROLLER_LIMITS,
    HDR_CONTROLLER_LIMITS,
    SYNC_CONTROLLER_LIMITS,
    THREE_D_CONTROLLER_LIMITS,
    ControllerLimits,
)
from .models import ControllerBoardSelection, Preferences, ScreenGeometry
from .server_planner import FOUR_K_PIXELS
from .u_series_planner import plan_u_series


FULL_HD_PIXELS = 1920 * 1080


@dataclass(frozen=True)
class ControllerRequest:
    screen: ScreenGeometry
    required_ports: int
    preferences: Preferences


@dataclass(frozen=True)
class ControllerPlan:
    model: str
    count: int
    output_ports: int
    accessories: tuple[str, ...]
    notes: tuple[str, ...]
    boards: tuple[ControllerBoardSelection, ...] = ()


def plan_controller(request: ControllerRequest) -> ControllerPlan:
    _validate_features(request.preferences)
    if request.preferences.asynchronous:
        return _asynchronous_plan(request)
    if request.preferences.feature_3d:
        return _single_or_u_plan(request, THREE_D_CONTROLLER_LIMITS)
    if request.preferences.feature_hdr:
        return _single_or_u_plan(request, HDR_CONTROLLER_LIMITS)
    return _single_or_u_plan(request, SYNC_CONTROLLER_LIMITS)


def _validate_features(preferences: Preferences) -> None:
    incompatible = (
        preferences.point_to_point
        or preferences.feature_3d
        or preferences.feature_hdr
    )
    if preferences.asynchronous and incompatible:
        raise ValueError("异步功能不能与点对点、主动式3D或HDR同时启用。")
    if preferences.asynchronous and preferences.loop_backup:
        raise ValueError("PDF未给出异步控制的环路备份算法。")


def _single_or_u_plan(
    request: ControllerRequest,
    catalog: tuple[ControllerLimits, ...],
) -> ControllerPlan:
    profile = next((item for item in catalog if _supports(item, request)), None)
    if profile:
        return _build_catalog_plan(profile, 1, request.preferences)
    pixels = request.screen.pixels_w * request.screen.pixels_h
    u_plan = plan_u_series(request.required_ports, pixels)
    return ControllerPlan(
        model=u_plan.model,
        count=u_plan.count,
        output_ports=u_plan.output_ports,
        accessories=u_plan.accessories + _accessories(request.preferences),
        notes=u_plan.notes + _controller_notes(request.preferences),
        boards=u_plan.boards,
    )


def _asynchronous_plan(request: ControllerRequest) -> ControllerPlan:
    profile = next(
        (item for item in ASYNC_CONTROLLER_LIMITS if _supports(item, request)),
        None,
    )
    if profile:
        return _build_catalog_plan(profile, 1, request.preferences)
    return _media_player_plan(request)


def _media_player_plan(request: ControllerRequest) -> ControllerPlan:
    pixels = request.screen.pixels_w * request.screen.pixels_h
    player = "A2K" if pixels < FULL_HD_PIXELS else "A4K"
    sync_preferences = replace(request.preferences, asynchronous=False)
    sync_request = ControllerRequest(
        screen=request.screen,
        required_ports=request.required_ports,
        preferences=sync_preferences,
    )
    sync_plan = _single_catalog_plan(sync_request, SYNC_CONTROLLER_LIMITS)
    combination_note = (
        f"异步播放器：{player} × 1；同步主控："
        f"{sync_plan.model} × {sync_plan.count}。"
    )
    return ControllerPlan(
        model=f"{player} + {sync_plan.model}",
        count=sync_plan.count,
        output_ports=sync_plan.output_ports,
        accessories=sync_plan.accessories,
        notes=(combination_note,) + sync_plan.notes,
        boards=sync_plan.boards,
    )


def _single_catalog_plan(
    request: ControllerRequest,
    catalog: tuple[ControllerLimits, ...],
) -> ControllerPlan:
    profile = next((item for item in catalog if _supports(item, request)), None)
    if profile is None:
        raise ValueError("无设备满足")
    return _build_catalog_plan(profile, 1, request.preferences)


def _build_catalog_plan(
    profile: ControllerLimits,
    count: int,
    preferences: Preferences,
) -> ControllerPlan:
    return ControllerPlan(
        model=profile.model,
        count=count,
        output_ports=profile.ports,
        accessories=_accessories(preferences),
        notes=_controller_notes(preferences),
    )


def _supports(profile: ControllerLimits, request: ControllerRequest) -> bool:
    screen = request.screen
    pixels = screen.pixels_w * screen.pixels_h
    if request.required_ports > profile.ports or pixels > profile.max_pixels:
        return False
    if screen.pixels_w > profile.max_width or screen.pixels_h > profile.max_height:
        return False
    return profile.max_4k_inputs >= _required_4k_inputs(request)


def _required_4k_inputs(request: ControllerRequest) -> int:
    if request.preferences.asynchronous or not request.preferences.point_to_point:
        return 0
    screen = request.screen
    if screen.pixels_w <= 1920 and screen.pixels_h <= 1200:
        return 0
    return (screen.pixels_w * screen.pixels_h + FOUR_K_PIXELS - 1) // FOUR_K_PIXELS


def _accessories(preferences: Preferences) -> tuple[str, ...]:
    accessories: list[str] = []
    if preferences.feature_3d:
        accessories.extend(("3D发射器 × 1", "3D眼镜 × 4"))
    if preferences.fiber_transmission:
        accessories.append("H16F光纤收发器 × 2")
    return tuple(accessories)


def _controller_notes(preferences: Preferences) -> tuple[str, ...]:
    notes: list[str] = []
    if preferences.feature_3d:
        notes.append("发送设备需选配3D版本。")
    if preferences.loop_backup:
        notes.append("环路备份按主、备网口数量翻倍计算。")
    return tuple(notes)
