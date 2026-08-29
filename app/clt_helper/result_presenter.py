from __future__ import annotations

from dataclasses import dataclass

from .cabinet_dimensions import format_cabinet_millimeters
from .models import Configuration, LoadBand
from .parsing import format_number
from .server_planner import SERVER_SELECTION_NOTE, format_resolution_four_k, select_server


@dataclass(frozen=True)
class ResultItem:
    label: str
    value: str


@dataclass(frozen=True)
class ResultSectionData:
    title: str
    items: tuple[ResultItem, ...]
    notes: tuple[str, ...] = ()
    emphasis: bool = False


def build_result_sections(
    configuration: Configuration,
) -> tuple[ResultSectionData, ...]:
    return (
        ResultSectionData("屏幕信息", _screen_items(configuration)),
        ResultSectionData("接收卡设计", _receiver_items(configuration)),
        ResultSectionData("网口带载设计", _network_items(configuration)),
        _configuration_section(configuration),
    )


def _screen_items(configuration: Configuration) -> tuple[ResultItem, ...]:
    if configuration.cabinet_shape:
        return _cabinet_screen_items(configuration)
    module = configuration.module
    screen = configuration.screen
    return (
        ResultItem("规格", f"P{format_number(module.pitch)}"),
        ResultItem(
            "模组",
            f"{format_number(module.width_mm)}×{format_number(module.height_mm)}mm",
        ),
        ResultItem("模组点数", f"{module.pixels_w}×{module.pixels_h}"),
        ResultItem(
            "屏幕总分辨率",
            format_resolution_four_k(screen.pixels_w, screen.pixels_h),
        ),
    )


def _cabinet_screen_items(configuration: Configuration) -> tuple[ResultItem, ...]:
    module = configuration.module
    screen = configuration.screen
    width, height = configuration.cabinet_shape or (1, 1)
    cabinet_mm = format_cabinet_millimeters(
        (module.width_mm * width, module.height_mm * height)
    )
    return (
        ResultItem("点间距", f"P{format_number(module.pitch)}"),
        ResultItem("箱体尺寸", f"{cabinet_mm}mm"),
        ResultItem("箱体点数", f"{module.pixels_w * width}×{module.pixels_h * height}"),
        ResultItem(
            "屏幕总分辨率",
            format_resolution_four_k(screen.pixels_w, screen.pixels_h),
        ),
    )


def _receiver_items(configuration: Configuration) -> tuple[ResultItem, ...]:
    plan = configuration.plan
    items: list[ResultItem] = []
    if not configuration.cabinet_shape:
        discount = configuration.preferences.receiver_discount
        items.append(ResultItem("打折", f"{discount.label} · 每卡{discount.value}张宽"))
    for band in plan.bands:
        items.append(_receiver_band_item(configuration, band))
    return tuple(items)


def _receiver_band_item(
    configuration: Configuration,
    band: LoadBand,
) -> ResultItem:
    plan = configuration.plan
    prefix = "单箱" if configuration.cabinet_shape else "单卡"
    value = f"{prefix}{plan.card_pixels_w}×{band.card_pixels_h}px"
    if not configuration.cabinet_shape:
        value += f" · {plan.card_modules_w}×{band.card_modules_h}模组"
    return ResultItem(f"{band.row_count}行", value)


def _network_items(configuration: Configuration) -> tuple[ResultItem, ...]:
    plan = configuration.plan
    items = [
        ResultItem("单口带载", f"{plan.port_group_w}×{plan.port_group_h}张卡"),
        ResultItem("像素上限", str(plan.port_capacity)),
        ResultItem("主网线", f"{plan.primary_ports}根"),
    ]
    if configuration.preferences.loop_backup:
        items.append(ResultItem("主备合计", f"{plan.required_ports}口"))
    return tuple(items)


def _configuration_section(configuration: Configuration) -> ResultSectionData:
    plan = configuration.plan
    items = [
        ResultItem("接收卡", f"{plan.receiver_model} × {plan.card_count}"),
        ResultItem("排布", f"{plan.cards_w}×{plan.cards_h}"),
        ResultItem(
            "主控",
            f"{plan.controller_model} × {plan.controller_count}"
            f"（{plan.controller_output_ports}网口/台）",
        ),
    ]
    notes: list[str] = []
    if not configuration.preferences.asynchronous:
        total_pixels = configuration.screen.pixels_w * configuration.screen.pixels_h
        items.append(ResultItem("服务器", select_server(total_pixels)))
        notes.append(SERVER_SELECTION_NOTE)
    items.extend(ResultItem("配件", item) for item in plan.accessories)
    notes.extend(plan.notes)
    return ResultSectionData("配置结果", tuple(items), tuple(notes), emphasis=True)
