from __future__ import annotations

from .controller_display import format_board_details
from .models import Configuration, LoadBand, LoadPlan
from .parsing import format_number
from .server_planner import select_server

PART_SEPARATOR = " + "
BAND_SEPARATOR = "/"


def format_plain_text(configuration: Configuration) -> str:
    plan = configuration.plan
    pitch_and_controller = (
        f"P{format_number(configuration.module.pitch)}："
        f"{_controller_text(plan)}"
    )
    receiver = (
        f"{plan.card_count}张{plan.receiver_model}接收卡"
        f"【{_receiver_loads(plan)}】"
    )
    parts = (
        pitch_and_controller,
        receiver,
        f"{plan.required_ports}根网线",
        _server_text(configuration),
    )
    return PART_SEPARATOR.join(parts)


def _controller_text(plan: LoadPlan) -> str:
    text = f"{plan.controller_count}台{plan.controller_model}主控"
    board_details = format_board_details(plan.controller_boards)
    return f"{text}（{board_details}）" if board_details else text


def _receiver_loads(plan: LoadPlan) -> str:
    loads = dict.fromkeys(_receiver_load(plan, band) for band in plan.bands)
    return BAND_SEPARATOR.join(loads)


def _receiver_load(plan: LoadPlan, band: LoadBand) -> str:
    return (
        f"{plan.card_modules_w}宽{band.card_modules_h}高"
        f"（{plan.card_pixels_w}*{band.card_pixels_h}）"
    )


def _server_text(configuration: Configuration) -> str:
    if configuration.preferences.asynchronous:
        return "无需配置服务器"
    screen = configuration.screen
    return f"1台服务器{select_server(screen.pixels_w * screen.pixels_h)}"
