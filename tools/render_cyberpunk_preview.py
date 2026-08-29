from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS_SIZE = (1920, 1080)
REGULAR_FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
BOLD_FONT = Path(r"C:\Windows\Fonts\msyhbd.ttc")
WHITE = "#FFFFFF"
TEXT = "#18304F"
MUTED = "#66809F"
BLUE = "#1769EF"
CYAN = "#00BFEA"
GREEN = "#14B86A"
PANEL_BORDER = "#D4E2F3"
PORT_COLORS = ("#00BFEA", "#FFB800", "#F04F9B", "#49C96D")


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = BOLD_FONT if bold else REGULAR_FONT
    return ImageFont.truetype(str(path), size)


def rounded_panel(
    image: Image.Image,
    box: tuple[int, int, int, int],
    *,
    fill: str,
    outline: str = PANEL_BORDER,
    radius: int = 8,
) -> None:
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shifted = (box[0], box[1] + 7, box[2], box[3] + 7)
    shadow_draw.rounded_rectangle(shifted, radius, fill=(49, 79, 122, 38))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)


def vertical_gradient(
    image: Image.Image,
    box: tuple[int, int, int, int],
    *,
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    radius: int = 8,
) -> None:
    width, height = box[2] - box[0], box[3] - box[1]
    gradient = Image.new("RGB", (width, height))
    gradient_draw = ImageDraw.Draw(gradient)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
        gradient_draw.line((0, y, width, y), fill=color)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width, height), radius, fill=255)
    image.paste(gradient, box[:2], mask)
    ImageDraw.Draw(image).rounded_rectangle(box, radius, outline=PANEL_BORDER, width=2)


def draw_brand_header(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1920, 78), fill=WHITE)
    draw.line((0, 77, 1920, 77), fill="#6786FF", width=3)
    center = (42, 39)
    for start, color in ((-90, "#1769EF"), (30, "#F44343"), (150, "#18B86B")):
        draw.arc((18, 15, 66, 63), start=start, end=start + 105, fill=color, width=12)
    draw.ellipse((34, 31, 50, 47), fill=WHITE, outline="#D4E2F3", width=2)
    draw.text((82, 38), "CLTassistant", font=font(30, bold=True), fill=TEXT, anchor="lm")
    draw.rounded_rectangle((294, 19, 366, 59), 8, fill="#E4EEFF")
    draw.text((330, 39), "Beta", font=font(17), fill=BLUE, anchor="mm")
    draw.text((1668, 39), "●  方案与带载图已同步", font=font(17), fill=GREEN, anchor="rm")
    draw.rounded_rectangle((1690, 16, 1888, 62), 8, fill="#F8FBFF", outline=PANEL_BORDER)
    draw.text((1778, 39), "配置选项", font=font(18, bold=True), fill=TEXT, anchor="mm")
    draw.polygon(((1860, 34), (1872, 34), (1866, 43)), fill=TEXT)


def draw_section_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    *,
    title: str,
    color: str,
) -> None:
    draw.rounded_rectangle((x, y, x + 6, y + 35), 3, fill=color)
    draw.text((x + 16, y + 18), title, font=font(23, bold=True), fill=TEXT, anchor="lm")


def draw_field(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    label: str,
    value: str,
) -> None:
    x1, y1, x2, y2 = box
    draw.text((x1, (y1 + y2) // 2), label, font=font(17), fill=MUTED, anchor="lm")
    input_x = x1 + 138
    draw.rounded_rectangle((input_x, y1, x2, y2), 7, fill="#FFFFFF", outline="#C9D9ED", width=2)
    draw.text((input_x + 16, (y1 + y2) // 2), value, font=font(18), fill=TEXT, anchor="lm")


def draw_parameters(image: Image.Image) -> None:
    panel = (18, 94, 620, 548)
    rounded_panel(image, panel, fill="#F9FCFF")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 96, 618, 154), 8, fill="#EDF4FF")
    draw_section_title(draw, 38, 108, title="参数配置", color=BLUE)
    draw.rounded_rectangle((448, 103, 520, 145), 8, fill=BLUE)
    draw.text((484, 124), "模组", font=font(20, bold=True), fill=WHITE, anchor="mm")
    draw.text((565, 124), "箱体", font=font(20, bold=True), fill=TEXT, anchor="mm")
    rows = (
        ("点间距 P", "1.86", "模组 mm", "320×160"),
        ("模组点数", "172×86", "屏幕块数", "12×12"),
        ("尺寸 m", "3.84×1.92", "分辨率", "2064×1032"),
    )
    for index, row in enumerate(rows):
        y = 170 + index * 58
        draw_field(draw, (42, y, 300, y + 44), label=row[0], value=row[1])
        draw_field(draw, (322, y, 596, y + 44), label=row[2], value=row[3])
    draw_field(draw, (42, 348, 596, 392), label="接收卡打折", value="不打折")
    draw.text((42, 421), "功能选项", font=font(17), fill=MUTED)
    options = ("点对点", "异步功能", "主动式3D", "HDR")
    for index, label in enumerate(options):
        x = 154 + index * 105
        draw.rounded_rectangle((x, 418, x + 20, 438), 5, fill=WHITE, outline="#22344E", width=2)
        draw.text((x + 28, 428), label, font=font(15), fill=TEXT, anchor="lm")
    draw.rounded_rectangle((42, 460, 64, 482), 5, fill="#CDE1FF", outline=BLUE, width=2)
    draw.line((47, 471, 52, 476, 60, 466), fill=BLUE, width=3)
    draw.text((74, 471), "自动匹配模组", font=font(16), fill=TEXT, anchor="lm")
    for x, width, label in ((42, 214, "配置并生成"), (268, 142, "打开原图"), (422, 174, "导出Mapping")):
        draw.rounded_rectangle((x, 494, x + width, 532), 8, fill=BLUE)
        draw.text((x + width // 2, 513), label, font=font(17, bold=True), fill=WHITE, anchor="mm")


def draw_output_bubble(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    title: str,
    lines: tuple[str, ...],
    accent: str,
) -> None:
    draw.rounded_rectangle(box, 8, fill="#F5F9FF", outline="#D5E3F3", width=2)
    draw.text((box[0] + 14, box[1] + 17), title, font=font(15, bold=True), fill=accent, anchor="lm")
    for index, line in enumerate(lines):
        draw.text((box[0] + 14, box[1] + 43 + index * 21), line, font=font(13), fill=TEXT)


def draw_output_panel(image: Image.Image) -> None:
    panel = (18, 566, 620, 1042)
    rounded_panel(image, panel, fill="#F9FCFF")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 568, 618, 626), 8, fill="#EDF4FF")
    draw_section_title(draw, 38, 578, title="方案输出", color="#FF9F43")
    draw.rounded_rectangle((520, 580, 596, 614), 8, fill="#E2F8ED")
    draw.text((558, 597), "● 已同步", font=font(14), fill=GREEN, anchor="mm")
    draw_output_bubble(draw, (38, 642, 214, 800), title="屏幕信息", lines=("P1.86", "320×160mm", "2064×1032", "12×12模组"), accent=BLUE)
    draw_output_bubble(draw, (224, 642, 400, 800), title="接收卡设计", lines=("E80 × 24", "排布 12×2", "单卡 1×6模组"), accent="#18A765")
    draw_output_bubble(draw, (410, 642, 596, 800), title="网口带载", lines=("4根主网线", "单口 6张卡", "上限 650000"), accent="#F08C35")
    draw.rounded_rectangle((38, 816, 596, 1022), 8, fill="#EAF3FF", outline="#8EB7F4", width=2)
    draw.text((56, 842), "配置结果", font=font(19, bold=True), fill=BLUE)
    results = ("接收卡  E80 × 24", "主控  X4s × 1（4网口/台）", "服务器  CS4K-G3")
    for index, line in enumerate(results):
        draw.text((56, 882 + index * 38), line, font=font(18, bold=True), fill=TEXT)


def add_glow_line(
    image: Image.Image,
    points: list[tuple[int, int]],
    *,
    color: str,
    width: int,
) -> None:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line(points, fill=color, width=width + 9, joint="curve")
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(image).line(points, fill=color, width=width, joint="curve")


def draw_mapping_grid(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    screen = (720, 282, 1858, 852)
    draw.rounded_rectangle(screen, 8, fill="#F8FCFF", outline="#72CFE8", width=2)
    for x in range(screen[0] + 20, screen[2], 32):
        draw.line((x, screen[1] + 1, x, screen[3] - 1), fill="#E0F2F8", width=1)
    for y in range(screen[1] + 20, screen[3], 32):
        draw.line((screen[0] + 1, y, screen[2] - 1, y), fill="#E0F2F8", width=1)
    cell_w, cell_h = 174, 125
    start_x, start_y = 790, 318
    for row in range(4):
        color = PORT_COLORS[row]
        centers = [
            (start_x + column * cell_w + 70, start_y + row * cell_h + 46)
            for column in range(6)
        ]
        route_end = (1780, centers[0][1])
        route = [(752, centers[0][1]), *centers, route_end]
        add_glow_line(image, route, color=color, width=4)
        for column in range(6):
            x = start_x + column * cell_w
            y = start_y + row * cell_h
            draw.rounded_rectangle((x, y, x + 140, y + 92), 7, fill="#FFFFFF", outline="#BED7EA", width=2)
            draw.rounded_rectangle((x + 37, y + 16, x + 103, y + 76), 6, fill="#ECFAFD", outline=color, width=3)
            draw.text((x + 70, y + 46), "172×516", font=font(14, bold=True), fill=TEXT, anchor="mm")
            draw.text((x + 70, y + 83), "E80", font=font(11), fill=MUTED, anchor="mm")
        draw.ellipse((736, centers[0][1] - 12, 760, centers[0][1] + 12), fill=WHITE, outline=color, width=4)
        draw.polygon(
            ((1780, centers[0][1]), (1766, centers[0][1] - 8), (1766, centers[0][1] + 8)),
            fill=color,
        )
        draw.text((700, centers[0][1]), f"P{row + 1}", font=font(14, bold=True), fill=color, anchor="rm")


def draw_cyber_panel(image: Image.Image) -> None:
    panel = (638, 94, 1902, 1042)
    rounded_panel(image, panel, fill="#F8FCFF")
    vertical_gradient(
        image,
        (640, 96, 1900, 172),
        start=(238, 247, 255),
        end=(228, 242, 255),
    )
    draw = ImageDraw.Draw(image)
    draw_section_title(draw, 660, 112, title="网线带载图", color=CYAN)
    draw.text((1872, 130), "●  方案与图同步刷新", font=font(16), fill=GREEN, anchor="rm")
    draw.rounded_rectangle((664, 188, 1876, 250), 8, fill="#EFF7FF", outline="#D4E6F5", width=2)
    summary = "2064 × 1032    E80 × 24    4 个主网口    X4s × 1（4网口/台）"
    draw.text((690, 219), summary, font=font(18, bold=True), fill=TEXT, anchor="lm")
    draw.rounded_rectangle((1618, 199, 1850, 239), 8, fill="#E1F8EF", outline="#AEE9CE")
    draw.text((1734, 219), "带载正常  62%", font=font(16, bold=True), fill=GREEN, anchor="mm")
    draw_mapping_grid(image)
    draw = ImageDraw.Draw(image)
    draw.text((738, 875), "P1.86  ·  640×480mm/箱  ·  6×4箱体", font=font(16), fill=MUTED)
    draw.text((1848, 875), "X  →", font=font(15, bold=True), fill=CYAN, anchor="rm")
    draw.rounded_rectangle((690, 914, 1876, 1008), 8, fill="#F0F7FD", outline="#D1E4F2", width=2)
    draw.text((716, 938), "网口图例", font=font(15, bold=True), fill=TEXT)
    for index, color in enumerate(PORT_COLORS):
        x = 824 + index * 240
        draw.ellipse((x, 930, x + 18, 948), fill=color)
        draw.text((x + 28, 939), f"网口 {index + 1}   6张卡", font=font(15), fill=TEXT, anchor="lm")
    draw.text((716, 982), "同色发光线路表示同一网口，箭头方向为信号走向", font=font(14), fill=MUTED)


def render(output: Path) -> None:
    image = Image.new("RGBA", CANVAS_SIZE, "#EAF0F8")
    vertical_gradient(
        image,
        (0, 78, 1920, 1080),
        start=(241, 247, 255),
        end=(229, 238, 249),
        radius=0,
    )
    draw_brand_header(image)
    draw_parameters(image)
    draw_output_panel(image)
    draw_cyber_panel(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output, quality=95)


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cyberpunk-preview.png")
    render(destination)
