from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.controller_planner import ControllerRequest, plan_controller
from clt_helper.hardware import RECEIVER_LIMITS
from clt_helper.mapping_export import build_mapping_configs
from clt_helper.models import Preferences, ScreenGeometry
from clt_helper.u_series_planner import U_CHASSIS, plan_u_series


def controller_request(pixels: int, ports: int, preferences: Preferences) -> ControllerRequest:
    width = 4000
    height = max(1, (pixels + width - 1) // width)
    screen = ScreenGeometry(1, 1, 1.0, 1.0, width, height)
    return ControllerRequest(screen=screen, required_ports=ports, preferences=preferences)


def dimension_request(
    dimensions: tuple[int, int],
    ports: int,
    preferences: Preferences,
) -> ControllerRequest:
    width, height = dimensions
    screen = ScreenGeometry(1, 1, 1.0, 1.0, width, height)
    return ControllerRequest(screen=screen, required_ports=ports, preferences=preferences)


class ProductSelectionTests(unittest.TestCase):
    def test_receiver_limits_follow_product_table(self) -> None:
        expected = {
            "5A-75E": (512, 512),
            "E80": (512, 512),
            "E120": (512, 512),
            "E320": (512, 512),
            "E80-G2": (512, 512),
            "K5+": (512, 384),
            "K8": (640, 360),
            "K10": (768, 432),
        }
        actual = {model: (item.max_width, item.max_height) for model, item in RECEIVER_LIMITS.items()}
        self.assertEqual(actual, expected)

    def test_async_selection_uses_excel_port_counts(self) -> None:
        cases = (
            (600_000, 1, "A35", 1),
            (1_000_000, 2, "A100", 2),
            (2_000_000, 3, "A200", 4),
            (4_000_000, 5, "A500", 8),
            (8_000_000, 9, "A800", 16),
        )
        preferences = Preferences(asynchronous=True)
        for pixels, ports, model, outputs in cases:
            with self.subTest(model=model):
                plan = plan_controller(controller_request(pixels, ports, preferences))
                self.assertEqual((plan.model, plan.output_ports), (model, outputs))

    def test_active_3d_module_mode_forbids_k_series(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (12, 12))
        plan = calculate_configuration(module, screen, Preferences(feature_3d=True)).plan

        self.assertEqual(plan.receiver_model, "E120")
        self.assertFalse(plan.receiver_model.startswith("K"))
        self.assertEqual(plan.controller_model, "X16E-3D")

    def test_single_controller_has_highest_priority_in_each_mode(self) -> None:
        cases = (
            (14_000_000, 21, Preferences(), "X26m", 26),
            (18_000_000, 27, Preferences(), "X40m", 40),
            (27_000_000, 41, Preferences(), "U3 Max", 60),
            (14_000_000, 21, Preferences(feature_3d=True), "U3 Max", 40),
            (10_000_000, 17, Preferences(feature_hdr=True), "U3 Max", 20),
        )
        for pixels, ports, preferences, model, outputs in cases:
            with self.subTest(model=model):
                plan = plan_controller(controller_request(pixels, ports, preferences))
                self.assertEqual((plan.model, plan.count), (model, 1))
                self.assertEqual(plan.output_ports, outputs)

    def test_async_a800_capacity_boundary_is_enforced(self) -> None:
        preferences = Preferences(asynchronous=True)
        exact_limit = dimension_request((4000, 2200), 16, preferences)
        over_limit = dimension_request((4001, 2200), 16, preferences)

        self.assertEqual(plan_controller(exact_limit).model, "A800")
        plan = plan_controller(over_limit)
        self.assertEqual((plan.model, plan.count), ("A4K + X16E", 1))

    def test_async_combo_player_uses_strict_full_hd_threshold(self) -> None:
        preferences = Preferences(asynchronous=True)
        below = dimension_request((1919, 1080), 17, preferences)
        threshold = dimension_request((1920, 1080), 17, preferences)

        self.assertEqual(plan_controller(below).model, "A2K + X20")
        self.assertEqual(plan_controller(threshold).model, "A4K + X20")

    def test_async_combo_keeps_point_to_point_dimension_checks(self) -> None:
        preferences = Preferences(asynchronous=True, point_to_point=True)
        request = dimension_request((9000, 500), 8, preferences)

        with self.assertRaisesRegex(ValueError, "异步功能不能与点对点"):
            plan_controller(request)

    def test_x12m_replaces_x12_only_when_point_to_point_needs_4k_input(self) -> None:
        dimensions = (7680, 1000)
        normal = dimension_request(dimensions, 12, Preferences())
        point_to_point = dimension_request(dimensions, 12, Preferences(point_to_point=True))

        self.assertEqual(plan_controller(normal).model, "X12")
        x12m_plan = plan_controller(point_to_point)
        self.assertEqual((x12m_plan.model, x12m_plan.output_ports), ("X12m", 12))

    def test_x12m_capacity_limit_is_enforced(self) -> None:
        preferences = Preferences(point_to_point=True)
        exact_limit = dimension_request((7860, 1000), 12, preferences)
        over_limit = dimension_request((7861, 1000), 12, preferences)

        self.assertEqual(plan_controller(exact_limit).model, "X12m")
        self.assertEqual(plan_controller(over_limit).model, "X16E")

    def test_point_to_point_enforces_4k_input_count_boundary(self) -> None:
        preferences = Preferences(point_to_point=True)
        two_4k = dimension_request((7680, 2160), 40, preferences)
        over_two_4k = dimension_request((7681, 2160), 40, preferences)

        self.assertEqual(plan_controller(two_4k).model, "X40m")
        self.assertEqual(plan_controller(over_two_4k).model, "U3 Max")

    def test_screenshot_case_uses_three_u_series_input_boards(self) -> None:
        request = dimension_request(
            (7740, 2580),
            40,
            Preferences(point_to_point=True),
        )

        plan = plan_controller(request)

        self.assertEqual((plan.model, plan.output_ports), ("U3 Max", 40))
        self.assertIn("输入板 1路HDMI2.0+1路DP1.2 × 3", plan.accessories)
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 2", plan.accessories)

    def test_async_combo_uses_x_series_and_rejects_over_forty_ports(self) -> None:
        preferences = Preferences(asynchronous=True)
        x26_plan = plan_controller(controller_request(14_000_000, 21, preferences))

        self.assertEqual((x26_plan.model, x26_plan.count), ("A4K + X26m", 1))
        with self.assertRaisesRegex(ValueError, "^无设备满足$"):
            plan_controller(controller_request(27_000_000, 41, preferences))

    def test_async_combo_exports_sync_controller_mapping_slots(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (60, 40))
        preferences = Preferences(asynchronous=True)
        configuration = calculate_configuration(module, screen, preferences)

        self.assertEqual(configuration.plan.controller_model, "A4K + X40m")
        self.assertEqual(build_mapping_configs(configuration)[0]["output_port_slots"], 40)

    def test_u_series_chassis_and_u20_board_thresholds(self) -> None:
        cases = (
            (60, 39_000_000, "U3 Max", 60),
            (61, 40_000_000, "U6 Max", 80),
            (100, 65_000_000, "U6 Max", 100),
            (101, 66_000_000, "U15 Max", 120),
        )
        for ports, pixels, model, outputs in cases:
            with self.subTest(model=model):
                plan = plan_u_series(ports, pixels)
                self.assertEqual((plan.model, plan.output_ports), (model, outputs))

        u9 = next(item for item in U_CHASSIS if item.model == "U9 Max")
        self.assertEqual((u9.slots, u9.max_input_boards, u9.max_ports), (20, 18, 100))

    def test_hdr_uses_u_series_and_dynamic_mapping_slots(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (60, 40))
        configuration = calculate_configuration(module, screen, Preferences(feature_hdr=True))
        plan = configuration.plan

        self.assertEqual(plan.controller_model, "U3 Max")
        self.assertEqual(plan.controller_output_ports, 60)
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 3", plan.accessories)
        self.assertIn("主控：U3 Max × 1（60网口/台）", configuration.result_text)
        self.assertEqual(build_mapping_configs(configuration)[0]["output_port_slots"], 60)


if __name__ == "__main__":
    unittest.main()
