from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass


VERSION_PATTERN = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)$")
JsonObject = Mapping[str, object]
ReleaseFetcher = Callable[[], JsonObject]


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    title: str
    notes: str
    page_url: str
    asset: ReleaseAsset


class UpdateService:
    def __init__(self, current_version: str, fetch_latest: ReleaseFetcher) -> None:
        self._current_version = current_version
        self._fetch_latest = fetch_latest

    def check(self) -> ReleaseInfo | None:
        release = release_from_payload(self._fetch_latest())
        if parse_version(release.version) <= parse_version(self._current_version):
            return None
        return release


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"无效版本号：{value}")
    return tuple(int(part) for part in match.groups())


def release_from_payload(payload: JsonObject) -> ReleaseInfo:
    tag = _required_text(payload, "tag_name")
    version = ".".join(str(part) for part in parse_version(tag))
    title = _optional_text(payload, "name") or f"V{version}"
    notes = _optional_text(payload, "body")
    page_url = _required_text(payload, "html_url")
    asset = _windows_asset(payload.get("assets"))
    return ReleaseInfo(version, title, notes, page_url, asset)


def _windows_asset(value: object) -> ReleaseAsset:
    if not isinstance(value, list):
        raise ValueError("Release 附件格式无效")
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("Release 附件条目格式无效")
        name = _required_text(item, "name")
        if name.lower().endswith(".exe"):
            return ReleaseAsset(name, _required_text(item, "browser_download_url"))
    raise ValueError("最新 Release 未提供 Windows EXE 附件")


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Release 缺少有效字段：{key}")
    return value.strip()


def _optional_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"Release 字段格式无效：{key}")
    return value.strip()
