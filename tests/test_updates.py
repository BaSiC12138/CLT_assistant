from __future__ import annotations

import unittest

from clt_helper.updates import UpdateService, parse_version, release_from_payload


def release_payload(tag: str = "V1.0.2") -> dict[str, object]:
    return {
        "tag_name": tag,
        "name": "V1.0.2",
        "body": "新增自动更新功能。",
        "html_url": "https://github.com/example/releases/tag/V1.0.2",
        "assets": [
            {
                "name": "CLTassistant-V1.0.2.exe",
                "browser_download_url": "https://github.com/example/download/app.exe",
            }
        ],
    }


class VersionTests(unittest.TestCase):
    def test_parses_optional_v_prefix(self) -> None:
        self.assertEqual(parse_version("V1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_rejects_non_semantic_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "无效版本号"):
            parse_version("V1.2")


class ReleaseTests(unittest.TestCase):
    def test_parses_release_and_windows_asset(self) -> None:
        release = release_from_payload(release_payload())
        self.assertEqual(release.version, "1.0.2")
        self.assertEqual(release.notes, "新增自动更新功能。")
        self.assertEqual(release.asset.name, "CLTassistant-V1.0.2.exe")

    def test_requires_executable_asset(self) -> None:
        payload = release_payload()
        payload["assets"] = []
        with self.assertRaisesRegex(ValueError, "未提供 Windows EXE"):
            release_from_payload(payload)

    def test_returns_only_newer_release(self) -> None:
        newer = UpdateService("1.0.1", lambda: release_payload()).check()
        current = UpdateService("1.0.2", lambda: release_payload()).check()
        self.assertIsNotNone(newer)
        self.assertIsNone(current)


if __name__ == "__main__":
    unittest.main()
