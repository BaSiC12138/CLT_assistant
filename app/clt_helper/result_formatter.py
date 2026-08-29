from __future__ import annotations

from .cabinet_dimensions import format_cabinet_millimeters
from .models import LoadPlan, ModuleSpec, Preferences, ReceiverDiscount, ScreenGeometry
from .parsing import format_number
from .server_planner import SERVER_SELECTION_NOTE, format_resolution_four_k, select_server


def format_result(
    module: ModuleSpec,
    screen: ScreenGeometry,
    plan: LoadPlan,
    *,
    preferences: Preferences,
    discount: ReceiverDiscount | None,
    cabinet_shape: tuple[int, int] | None = None,
) -> str:
    screen_section = _screen_section(module, screen)
    receiver_section = _receiver_section(plan, discount)
    if cabinet_shape:
        screen_section = _cabinet_screen_section(module, screen, cabinet_shape)
        receiver_section = _cabinet_receiver_section(plan)
    sections = (
        screen_section,
        receiver_section,
        _network_section(plan, preferences),
        _result_section(plan, screen, preferences),
    )
    return "".join(sections)


def _screen_section(module: ModuleSpec, screen: ScreenGeometry) -> str:
    resolution = format_resolution_four_k(
        screen.pixels_w,
        screen.pixels_h,
        separator=" x ",
    )
    return (
        "========屏幕信息=======\n"
        f"规格：P {format_number(module.pitch)} "
        f"[{format_number(module.width_mm)}mm x {format_number(module.height_mm)}mm]\n"
        f"模组点数：{module.pixels_w} x {module.pixels_h}\n"
        f"屏幕总分辨率：{resolution}\n"
        f"模组宽x高：{screen.modules_w} x {screen.modules_h}\n"
    )


def _cabinet_screen_section(
    module: ModuleSpec,
    screen: ScreenGeometry,
    cabinet_shape: tuple[int, int],
) -> str:
    cabinet_mm = (
        module.width_mm * cabinet_shape[0],
        module.height_mm * cabinet_shape[1],
    )
    cabinet_pixels = (
        module.pixels_w * cabinet_shape[0],
        module.pixels_h * cabinet_shape[1],
    )
    resolution = format_resolution_four_k(
        screen.pixels_w,
        screen.pixels_h,
        separator=" x ",
    )
    cabinet_mm_text = format_cabinet_millimeters(cabinet_mm).replace("×", " x ")
    return (
        "========屏幕信息=======\n"
        f"点间距：P {format_number(module.pitch)}\n"
        f"箱体尺寸：{cabinet_mm_text} mm\n"
        f"箱体点数：{cabinet_pixels[0]} x {cabinet_pixels[1]}\n"
        f"屏幕总分辨率：{resolution}\n"
    )


def _receiver_section(
    plan: LoadPlan,
    discount: ReceiverDiscount | None,
) -> str:
    discount_text = ""
    if discount is not None:
        discount_text = f"接收卡打折数量：{discount.label}（每卡{discount.value}张模组宽）\n"
    rows = "".join(
        f"接收卡 [{band.row_count}行]：{plan.card_pixels_w} x {band.card_pixels_h} "
        f"[{plan.card_modules_w} x {band.card_modules_h}]\n"
        for band in plan.bands
    )
    return "========接收卡设计=======\n" + discount_text + rows


def _cabinet_receiver_section(plan: LoadPlan) -> str:
    rows = "".join(
        f"接收卡 [{band.row_count}行]：单箱{plan.card_pixels_w} x "
        f"{band.card_pixels_h}点\n"
        for band in plan.bands
    )
    return "========接收卡设计=======\n" + rows


def _network_section(plan: LoadPlan, preferences: Preferences) -> str:
    backup = ""
    if preferences.loop_backup:
        backup = f"主链路：{plan.primary_ports}口，主备合计：{plan.required_ports}口\n"
    return (
        "========网口带载设计=======\n"
        f"单口带载：{plan.port_group_w} x {plan.port_group_h} 张接收卡\n"
        f"单口像素上限：{plan.port_capacity}\n"
        f"屏幕需要：{plan.primary_ports} 根主网线\n"
        f"{backup}"
    )


def _result_section(
    plan: LoadPlan,
    screen: ScreenGeometry,
    preferences: Preferences,
) -> str:
    accessories = "".join(f"配件：{item}\n" for item in plan.accessories)
    notes = "".join(f"注意：{item}\n" for item in plan.notes)
    server = _server_section(screen, preferences)
    return (
        "========配置结果=======\n"
        f"接收卡：{plan.receiver_model} × {plan.card_count}\n"
        f"排布：{plan.cards_w} x {plan.cards_h}\n"
        f"主控：{plan.controller_model} × {plan.controller_count}"
        f"（{plan.controller_output_ports}网口/台）\n"
        f"{server}{accessories}{notes}"
    )


def _server_section(screen: ScreenGeometry, preferences: Preferences) -> str:
    if preferences.asynchronous:
        return ""
    total_pixels = screen.pixels_w * screen.pixels_h
    server = select_server(total_pixels)
    return f"服务器：{server}\n注意：{SERVER_SELECTION_NOTE}\n"
