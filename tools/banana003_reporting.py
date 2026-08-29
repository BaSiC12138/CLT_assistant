from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


def _search(pattern: str, text: str, cast=int):
    match = re.search(pattern, text)
    if not match:
        return None
    values = tuple(cast(value) for value in match.groups() if value is not None)
    return values[0] if len(values) == 1 else values


def _cards_per_port(text: str) -> int | None:
    legacy = _search(r"1根网线能连这样的接收卡\s*(\d+)\s*张", text)
    if legacy is not None:
        return legacy
    shape = _search(r"单口带载：\s*(\d+)\s*x\s*(\d+)\s*张", text)
    return shape[0] * shape[1] if shape else None


def parse_result(text: str) -> dict[str, object]:
    normalized = text.replace("\r", "")
    return {
        "pitch": _search(r"规格：P\s*([0-9.]+)", normalized, float),
        "module_mm": _search(r"\[(\d+)mm\s*x\s*(\d+)mm\]", normalized),
        "module_pixels": _search(r"(?:模组点数|点数\s*：)\s*(\d+)\s*x\s*(\d+)", normalized),
        "screen_pixels": _search(r"(?:整屏分辨率|分辨率)：\s*(\d+)\s*x\s*(\d+)", normalized),
        "screen_modules": _search(r"模组宽x高[：:]\s*(\d+)\s*x\s*(\d+)", normalized),
        "card_rows": _search(r"接收卡\s*\[\s*(\d+)行\s*\]", normalized),
        "card_pixels": _search(r"接收卡[^：\n]*：\s*(\d+)\s*x\s*(\d+)", normalized),
        "card_modules": _search(r"\[\s*(\d+)\s*x\s*(\d+)\s*\]", normalized),
        "cards_per_port": _cards_per_port(normalized),
        "required_ports": _search(r"屏幕需要[：:]\s*(\d+)\s*根(?:主)?网线", normalized),
        "receiver_model": _search(r"接收卡(?:类型:|：)\s*([^\s]+)", normalized, str),
        "card_total": _search(r"接收卡：[^\n]*×\s*(\d+)|总数:\s*(\d+)\s*=", normalized),
        "card_grid": _search(r"(?:排布：|总数:\s*\d+\s*=)\s*(\d+)\s*x\s*(\d+)", normalized),
        "controller_model": _search(r"主控(?:类型:|：)\s*([^\s]+)", normalized, str),
        "controller_count": _search(r"主控：[^\n]*×\s*(\d+)|主控类型:.*?数量:\s*(\d+)", normalized),
    }


def compare_fields(
    original: dict[str, object],
    new: dict[str, object],
) -> dict[str, dict[str, object]]:
    return {
        field: {"original": value, "new": new[field]}
        for field, value in original.items()
        if value != new[field]
    }


def write_report(
    records: list[dict[str, object]],
    stamp: str,
    report_root: Path,
) -> tuple[Path, Path]:
    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / f"banana003-differential-{stamp}.json"
    md_path = report_root / f"banana003-differential-{stamp}.md"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text("\n".join(_report_lines(records)), encoding="utf-8")
    return json_path, md_path


def _report_lines(records: list[dict[str, object]]) -> list[str]:
    matched = sum(not record["differences"] for record in records)
    lines = [
        "# 香蕉003版与 CLTassistant 差分测试",
        "",
        f"- 执行时间：{datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- 案例数：{len(records)}",
        f"- 完全一致：{matched}",
        f"- 存在差异：{len(records) - matched}",
        "",
        "| 案例 | 输入 | 结果 | 差异字段 |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(_summary_rows(records))
    lines.extend(("", "## 差异明细", ""))
    lines.extend(_difference_lines(records))
    return lines


def _summary_rows(records: list[dict[str, object]]) -> list[str]:
    rows = []
    for record in records:
        case = record["case"]
        differences = record["differences"]
        fields = "、".join(differences) if differences else "-"
        result = "一致" if not differences else "不同"
        rows.append(f"| {case['name']} | P{case['pitch']} / {_screen_input(case)} | {result} | {fields} |")
    return rows


def _difference_lines(records: list[dict[str, object]]) -> list[str]:
    lines = []
    for record in records:
        if not record["differences"]:
            continue
        case = record["case"]
        lines.extend((f"### {case['name']}（P{case['pitch']} / {_screen_input(case)}）", ""))
        for field, values in record["differences"].items():
            lines.append(f"- `{field}`：原版 `{values['original']}`；新版 `{values['new']}`")
        lines.append("")
    return lines


def _screen_input(case: dict[str, object]) -> str:
    direct = case["screen_modules"] or case["screen_physical"] or case["screen_pixels"]
    return str(direct or f"{case['cabinet_modules']} / {case['screen_cabinets']}")
