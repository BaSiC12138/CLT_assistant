from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from PySide6.QtCore import QStandardPaths

from .constants import resource_path
from .mapping_generator import generate_mapping
from .models import Configuration
from .routing import RoutedCard, route_cards


CONTROLLER_OUTPUT_PORTS: dict[str, int] = {
    "X2s": 2,
    "X4s": 4,
    "A100": 2,
    "X6": 6,
    "X7": 8,
    "X8E": 8,
    "X12": 12,
    "X12m": 12,
    "X16E": 16,
    "X16E-3D": 16,
    "X20": 20,
    "X26m": 26,
    "X40m": 40,
    "X20-3D": 20,
    "Z5": 16,
    "A35": 1,
    "A500": 8,
    "A800": 16,
    "A200": 4,
}

MAPPING_TEMPLATE = "assets/mapping_v10_template.mapping"


def controller_output_slots(controller_model: str) -> int:
    try:
        return CONTROLLER_OUTPUT_PORTS[controller_model]
    except KeyError as error:
        raise ValueError(f"未知设备型号，无法确定输出槽数：{controller_model}") from error


def default_mapping_directory() -> Path:
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DesktopLocation
    )
    if not location:
        raise OSError("无法获取当前用户的桌面目录。")
    return Path(location)


def default_mapping_stem(configuration: Configuration) -> str:
    screen = configuration.screen
    plan = configuration.plan
    return (
        f"{screen.pixels_w}×{screen.pixels_h}_"
        f"{plan.cards_w}×{plan.cards_h}_assistantBeta"
    )


def build_mapping_configs(configuration: Configuration) -> tuple[dict[str, Any], ...]:
    if configuration.plan.required_ports != configuration.plan.primary_ports:
        raise ValueError("环路备份方案暂不支持导出单份Mapping。")
    plan = configuration.plan
    slots = plan.controller_output_ports
    cards_by_device: dict[int, list[dict[str, int]]] = defaultdict(list)

    for card in route_cards(configuration):
        device_index = (card.port - 1) // slots
        if device_index >= plan.controller_count:
            raise ValueError("Mapping使用的设备数超过方案计算结果。")
        local_port = (card.port - 1) % slots + 1
        cards_by_device[device_index].append(
            {
                "device": 1,
                "port": local_port,
                "chain": card.chain,
                "x": card.x,
                "y": card.y,
                "width": card.width,
                "height": card.height,
            }
        )

    configs: list[dict[str, Any]] = []
    for device_index in range(plan.controller_count):
        cards = cards_by_device.get(device_index, [])
        if not cards:
            raise ValueError(f"设备{device_index + 1}没有可导出的接收卡。")
        configs.append(
            {
                "output_port_slots": slots,
                # V10 stores row count at 0x47 and column count at 0x49.
                "screen": {"columns": plan.cards_h, "rows": plan.cards_w},
                "unused_port_size": {
                    "x": 0,
                    "y": 0,
                    "width": plan.card_pixels_w,
                    "height": max(band.card_pixels_h for band in plan.bands),
                },
                "cards": cards,
                "port_areas": {},
            }
        )
    return tuple(configs)


def generate_configuration_mappings(
    configuration: Configuration,
    directory: Path | None = None,
    stem: str | None = None,
) -> tuple[Path, ...]:
    output_directory = Path(directory) if directory is not None else default_mapping_directory()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_stem = stem or default_mapping_stem(configuration)
    configs = build_mapping_configs(configuration)
    template = resource_path(MAPPING_TEMPLATE)
    outputs: list[Path] = []

    for index, config in enumerate(configs, start=1):
        suffix = f"_设备{index}" if len(configs) > 1 else ""
        output = output_directory / f"{output_stem}{suffix}.mapping"
        generate_mapping(template, output, config)
        outputs.append(output)
    return tuple(outputs)
