from __future__ import annotations

import unittest

from clt_helper.controller_display import format_board_details
from clt_helper.u_series_planner import plan_u_series


class USeriesInputBoardTests(unittest.TestCase):
    def test_u3_uses_single_4k_input_boards_when_slots_allow(self) -> None:
        plan = plan_u_series(required_ports=60, pixels=39_000_000)

        self.assertEqual((plan.model, plan.output_ports), ("U3 Max", 60))
        self.assertIn("输入板 1路HDMI2.0+1路DP1.2 × 5", plan.accessories)
        self.assertNotIn("输入板 2路HDMI+2路DP1.2 × 1", plan.accessories)
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 3", plan.accessories)
        self.assertIn("每台占用8/8个板卡槽，输入、输出板卡已联合校验。", plan.notes)

    def test_u15_uses_only_required_dual_input_boards(self) -> None:
        plan = plan_u_series(required_ports=400, pixels=260_000_000)

        self.assertEqual((plan.model, plan.output_ports), ("U15 Max", 400))
        self.assertIn("输入板 1路HDMI2.0+1路DP1.2 × 8", plan.accessories)
        self.assertIn("输入板 2路HDMI+2路DP1.2 × 12", plan.accessories)
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 20", plan.accessories)
        self.assertIn("每台主控的输入板合计可带载32个3840×2160信号。", plan.notes)
        self.assertIn("每台占用40/40个板卡槽，输入、输出板卡已联合校验。", plan.notes)
        self.assertEqual(
            format_board_details(plan.boards),
            "8张1路HDMI2.0+1路DP1.2输入板卡；"
            "12张2路HDMI+2路DP1.2输入板卡；"
            "20张U_OUT_20×1G_RJ45输出板卡",
        )

    def test_u_series_upgrade_order_still_checks_output_requirements(self) -> None:
        cases = (
            (60, 39_000_000, "U3 Max"),
            (61, 40_000_000, "U6 Max"),
            (101, 66_000_000, "U15 Max"),
        )
        for ports, pixels, expected in cases:
            with self.subTest(model=expected):
                self.assertEqual(plan_u_series(ports, pixels).model, expected)

    def test_multiple_u15_counts_input_and_output_boards_per_device(self) -> None:
        plan = plan_u_series(required_ports=401, pixels=260_000_001)

        self.assertEqual((plan.model, plan.count), ("U15 Max", 2))
        self.assertIn("输出板 U_OUT_20×1G_RJ45 × 22", plan.accessories)
        self.assertIn("输入板 1路HDMI2.0+1路DP1.2 × 32", plan.accessories)


if __name__ == "__main__":
    unittest.main()
