from __future__ import annotations

import re


PAIR_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:[xX×]|\s+)\s*(\d+(?:\.\d+)?)\s*$")


def parse_pair(text: str) -> tuple[float, float] | None:
    match = PAIR_PATTERN.fullmatch(text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def parse_int_pair(text: str) -> tuple[int, int] | None:
    pair = parse_pair(text)
    if not pair:
        return None
    left, right = pair
    if not left.is_integer() or not right.is_integer():
        return None
    if left <= 0 or right <= 0:
        return None
    return int(left), int(right)


def parse_positive_float(text: str) -> float | None:
    try:
        value = float(text.strip())
    except ValueError:
        return None
    return value if value > 0 else None


def format_number(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")
