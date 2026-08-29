from __future__ import annotations

import json
from collections.abc import Mapping
from urllib.request import Request, urlopen


HTTP_TIMEOUT_SECONDS = 10
GITHUB_ACCEPT = "application/vnd.github+json"
USER_AGENT = "CLTassistant-Updater"


class GitHubReleaseClient:
    def __init__(self, latest_release_url: str) -> None:
        self._latest_release_url = latest_release_url

    def fetch_latest(self) -> Mapping[str, object]:
        request = Request(
            self._latest_release_url,
            headers={"Accept": GITHUB_ACCEPT, "User-Agent": USER_AGENT},
        )
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise ValueError("GitHub Release 响应不是 JSON 对象")
        return payload
