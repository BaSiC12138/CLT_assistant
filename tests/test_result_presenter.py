from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.models import Preferences
from clt_helper.result_presenter import ResultSectionData, build_result_sections
from clt_helper.server_planner import SERVER_SELECTION_NOTE


def build_configuration(
    modules: tuple[int, int] = (12, 12),
    preferences: Preferences = Preferences(),
    cabinet_shape: tuple[int, int] | None = None,
):
    module = matching_modules(2.5)[0]
    screen = screen_from_modules(module, modules)
    return calculate_configuration(
        module,
        screen,
        preferences,
        card_shape_override=cabinet_shape,
    )


def section_text(section: ResultSectionData) -> str:
    items = tuple(f"{item.label} {item.value}" for item in section.items)
    return "\n".join(items + section.notes)


class ResultPresenterTests(unittest.TestCase):
    def test_sections_keep_required_order_and_default_values(self) -> None:
        configuration = build_configuration()
        sections = build_result_sections(configuration)

        self.assertEqual(
            tuple(section.title for section in sections),
            ("屏幕信息", "接收卡设计", "网口带载设计", "配置结果"),
        )
        screen = section_text(sections[0])
        self.assertIn("屏幕总分辨率 1536×768=0.14个3840*2160", screen)
        self.assertNotIn("约", screen)
        self.assertNotIn("模组数量", screen)
        self.assertIn("模组宽x高：12 x 12", configuration.result_text)
        self.assertIn("接收卡 E80 × 24", section_text(sections[3]))
        self.assertIn("主控 X2s × 1（2网口/台）", section_text(sections[3]))
        self.assertTrue(sections[3].emphasis)

    def test_async_result_omits_server_and_server_note(self) -> None:
        sections = build_result_sections(
            build_configuration(preferences=Preferences(asynchronous=True))
        )
        result = section_text(sections[3])

        self.assertNotIn("服务器", result)
        self.assertNotIn(SERVER_SELECTION_NOTE, result)

    def test_cabinet_sections_use_cabinet_dimensions(self) -> None:
        sections = build_result_sections(
            build_configuration(cabinet_shape=(2, 3))
        )
        screen = section_text(sections[0])

        self.assertIn("箱体尺寸 640×480mm", screen)
        self.assertIn("屏幕总分辨率 1536×768=0.14个3840*2160", screen)
        self.assertNotIn("模组块数", screen)
        self.assertIn("单箱256×192px", section_text(sections[1]))
        self.assertNotIn("打折", section_text(sections[1]))

    def test_u_series_accessories_and_notes_remain_visible(self) -> None:
        sections = build_result_sections(
            build_configuration((60, 40), Preferences(feature_hdr=True))
        )
        result = section_text(sections[3])

        self.assertIn("主控 U3 Max × 1", result)
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 3", result)
        self.assertIn("输入、输出板卡已联合校验", result)


if __name__ == "__main__":
    unittest.main()
