from __future__ import annotations

import argparse
import ctypes
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from pywinauto import Desktop, clipboard, keyboard, mouse
from pywinauto.timings import Timings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from clt_helper.calculator import calculate_configuration, infer_screen, screen_from_modules  # noqa: E402
from clt_helper.catalog import matching_modules  # noqa: E402
from clt_helper.models import InterfaceMode, Preferences, ScreenInputs  # noqa: E402
from banana003_cases import Case, SUITES  # noqa: E402
from banana003_reporting import compare_fields, parse_result, write_report  # noqa: E402


ORIGINAL_TITLE = "CLT方案小助手"
REPORT_ROOT = Path(r"D:\ChatGpt\CLT\_assistant\comparison-reports")

FIELD_POINTS = {
    "pitch": (283, 193),
    "modules": (374, 653),
    "physical": (374, 733),
    "pixels": (374, 813),
}
CONFIGURE_POINT = (168, 1044)
RESULT_POINT = (900, 700)


class OriginalDriver:
    def __init__(self) -> None:
        self.window = Desktop(backend="win32").window(title=ORIGINAL_TITLE)
        if not self.window.exists(timeout=5):
            raise RuntimeError(f"未找到正在运行的原版窗口：{ORIGINAL_TITLE}")
        self.window.set_focus()
        keyboard.send_keys("{ESC}")
        time.sleep(0.2)
        self.rect = self.window.rectangle()
        self.option_state = {
            "point_to_point": False,
            "asynchronous": False,
            "feature_3d": False,
            "interface_75": False,
            "interface_320": False,
            "auto_discount": False,
        }
        self.cabinet_mode = False

    def point(self, relative: tuple[int, int]) -> tuple[int, int]:
        return self.rect.left + relative[0], self.rect.top + relative[1]

    def click(self, relative: tuple[int, int]) -> None:
        x, y = self.point(relative)
        user32 = ctypes.windll.user32
        user32.SetCursorPos(x, y)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.02)

    def move(self, relative: tuple[int, int]) -> None:
        x, y = self.point(relative)
        ctypes.windll.user32.SetCursorPos(x, y)
        time.sleep(0.08)

    def toggle_main_option(self, item_y: int) -> None:
        mouse.click(coords=self.point((75, 80)))
        time.sleep(0.2)
        mouse.move(coords=self.point((145, 125)))
        time.sleep(0.35)
        mouse.click(coords=self.point((365, item_y)))
        time.sleep(0.2)

    def toggle_receiver_option(self, item: str) -> None:
        mouse.click(coords=self.point((75, 80)))
        time.sleep(0.2)
        mouse.move(coords=self.point((145, 181)))
        time.sleep(0.35)
        if item == "auto_discount":
            mouse.click(coords=self.point((375, 220)))
            time.sleep(0.2)
            return
        mouse.move(coords=self.point((375, 181)))
        time.sleep(0.45)
        mouse.click(coords=self.point((580, 181 if item == "interface_75" else 220)))
        time.sleep(0.2)

    def set_options(self, case: Case) -> None:
        desired = {
            "point_to_point": case.point_to_point,
            "asynchronous": case.asynchronous,
            "feature_3d": case.feature_3d,
            "interface_75": case.interface == "75",
            "interface_320": case.interface == "320",
            "auto_discount": case.auto_discount,
        }
        main_items = {"point_to_point": 126, "asynchronous": 163, "feature_3d": 201}
        for name, item_y in main_items.items():
            if desired[name] != self.option_state[name]:
                self.toggle_main_option(item_y)
                self.option_state[name] = desired[name]
        for name in ("interface_75", "interface_320", "auto_discount"):
            if desired[name] != self.option_state[name]:
                self.toggle_receiver_option(name)
                self.option_state[name] = desired[name]
        keyboard.send_keys("{ESC}{ESC}{ESC}", pause=0.02)
        mouse.click(coords=self.point((700, 80)))
        time.sleep(0.08)

    def set_cabinet_mode(self, enabled: bool) -> None:
        if enabled == self.cabinet_mode:
            return
        self.window.set_focus()
        keyboard.send_keys("{ESC}{ESC}{ESC}", pause=0.02)
        mouse.click(coords=self.point((700, 80)))
        time.sleep(0.15)
        mouse.click(coords=self.point((205, 80)))
        time.sleep(0.35)
        mouse.click(coords=self.point((245, 163 if enabled else 126)))
        time.sleep(0.5)
        self.cabinet_mode = enabled

    def copy_result(self) -> str:
        self.click(RESULT_POINT)
        keyboard.send_keys("^a^c", pause=0.005)
        for _ in range(6):
            time.sleep(0.1)
            try:
                result = clipboard.GetData()
            except Exception:
                keyboard.send_keys("^c", pause=0.005)
                continue
            if "屏幕信息" in result:
                return result.replace("\r", "")
            keyboard.send_keys("^c", pause=0.005)
        return ""

    def replace(self, field: str, value: str) -> None:
        self.click(FIELD_POINTS[field])
        keyboard.send_keys("^a{BACKSPACE}", pause=0.005)
        if value:
            keyboard.send_keys(value, pause=0.005)

    def run(self, case: Case) -> str:
        self.set_cabinet_mode(bool(case.cabinet_modules))
        self.set_options(case)
        if case.cabinet_modules:
            return self.run_cabinet(case)
        self.replace("modules", "")
        self.replace("physical", "")
        self.replace("pixels", "")
        self.replace("pitch", case.pitch)
        time.sleep(0.05)
        if case.screen_modules:
            self.replace("modules", case.screen_modules)
        elif case.screen_physical:
            self.replace("physical", case.screen_physical)
        else:
            self.replace("pixels", case.screen_pixels)
        time.sleep(0.03)
        self.click(CONFIGURE_POINT)
        time.sleep(0.15)
        result = self.copy_result()
        if "屏幕信息" not in result:
            raise RuntimeError(f"{case.name} 未读取到有效原版结果")
        return result

    def run_cabinet(self, case: Case) -> str:
        fields = {
            "modules": (374, 753),
            "physical": (374, 833),
            "pixels": (374, 913),
            "screen_cabinets": (374, 1073),
            "cabinet_modules": (293, 533),
        }
        for point in fields.values():
            self.click(point)
            keyboard.send_keys("^a{BACKSPACE}", pause=0.005)
        self.replace("pitch", case.pitch)
        self.click(fields["cabinet_modules"])
        keyboard.send_keys(case.cabinet_modules, pause=0.005)
        self.click(fields["screen_cabinets"])
        keyboard.send_keys(case.screen_cabinets, pause=0.005)
        self.click((168, 1183))
        time.sleep(0.2)
        result = self.copy_result()
        if "屏幕信息" not in result:
            raise RuntimeError(f"{case.name} 未读取到有效原版箱体结果")
        return result


def run_new(case: Case) -> str:
    options = matching_modules(float(case.pitch))
    if not options:
        raise RuntimeError(f"新版目录中没有 P{case.pitch} 模组")
    module = options[0]
    card_shape = None
    if case.cabinet_modules:
        card_shape = tuple(int(value) for value in re.split(r"[xX×*\s]+", case.cabinet_modules))
        cabinet_grid = tuple(int(value) for value in re.split(r"[xX×*\s]+", case.screen_cabinets))
        screen = screen_from_modules(
            module,
            (card_shape[0] * cabinet_grid[0], card_shape[1] * cabinet_grid[1]),
        )
    else:
        screen = infer_screen(
            module,
            ScreenInputs(case.screen_modules, case.screen_physical, case.screen_pixels),
        )
    if screen is None:
        raise RuntimeError(f"新版无法解析屏幕参数：{case.name}")
    interface = {
        "auto": InterfaceMode.AUTO,
        "75": InterfaceMode.HUB75,
        "320": InterfaceMode.HUB320,
    }[case.interface]
    preferences = Preferences(
        point_to_point=case.point_to_point,
        asynchronous=case.asynchronous,
        feature_3d=case.feature_3d,
        interface=interface,
        copy_text=True,
    )
    return calculate_configuration(
        module,
        screen,
        preferences,
        receiver_override=case.receiver_override or None,
        card_shape_override=card_shape,
    ).result_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--suite", choices=tuple(SUITES), default="base")
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    Timings.fast()
    cases = SUITES[args.suite][: args.limit or None]
    if args.only:
        cases = tuple(case for case in cases if case.name == args.only)
        if not cases:
            parser.error(f"suite {args.suite!r} 中不存在案例 {args.only!r}")
    driver = OriginalDriver()
    records = []
    for index, case in enumerate(cases, 1):
        original_text = driver.run(case)
        new_text = run_new(case)
        original_fields = parse_result(original_text)
        new_fields = parse_result(new_text)
        differences = compare_fields(original_fields, new_fields)
        records.append(
            {
                "case": asdict(case),
                "original": original_fields,
                "new": new_fields,
                "differences": differences,
                "original_text": original_text,
                "new_text": new_text,
            }
        )
        print(f"[{index:02d}/{len(cases):02d}] {case.name}: {'MATCH' if not differences else 'DIFF ' + ','.join(differences)}", flush=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path, md_path = write_report(records, stamp, REPORT_ROOT)
    print(json_path)
    print(md_path)
    return 1 if any(record["differences"] for record in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
