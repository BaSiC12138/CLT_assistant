from __future__ import annotations

import unittest

from clt_helper.models import Preferences, ScreenGeometry
from clt_helper.port_planner import PortRequest, plan_ports

CARD_WIDTH = 300
CARD_HEIGHT = 800


def port_request(cards_w: int) -> PortRequest:
    screen = ScreenGeometry(
        modules_w=cards_w,
        modules_h=2,
        width_m=1.0,
        height_m=1.0,
        pixels_w=cards_w * CARD_WIDTH,
        pixels_h=2 * CARD_HEIGHT,
    )
    return PortRequest(
        screen=screen,
        cards_w=cards_w,
        card_pixels_w=CARD_WIDTH,
        row_heights=(CARD_HEIGHT, CARD_HEIGHT),
        preferences=Preferences(),
    )


class PortPlannerTests(unittest.TestCase):
    def test_mode_capacity_boundaries_are_exact(self) -> None:
        cases = (
            (Preferences(), 650_000),
            (Preferences(feature_hdr=True), 487_500),
            (Preferences(feature_3d=True), 325_000),
        )
        for preferences, capacity in cases:
            with self.subTest(capacity=capacity):
                plan = plan_ports(_capacity_request(capacity, preferences))
                self.assertEqual(plan.capacity, capacity)
                with self.assertRaisesRegex(ValueError, "超过当前网口带载上限"):
                    plan_ports(_capacity_request(capacity + 1, preferences))

    def test_same_port_count_prefers_cards_from_one_row(self) -> None:
        plan = plan_ports(port_request(cards_w=4))

        self.assertEqual((plan.group_w, plan.group_h), (2, 1))
        self.assertEqual(plan.primary_ports, 4)

    def test_cross_row_saving_is_rejected_above_height_limit(self) -> None:
        plan = plan_ports(port_request(cards_w=5))

        self.assertEqual((plan.group_w, plan.group_h), (2, 1))
        self.assertEqual(plan.primary_ports, 6)

    def test_exactly_1024_pixels_can_cross_rows_to_save_ports(self) -> None:
        request = _request_with_height(cards_w=5, card_height=512)

        plan = plan_ports(request)

        self.assertEqual((plan.group_w, plan.group_h), (2, 2))
        self.assertEqual(plan.primary_ports, 3)

    def test_single_card_above_height_limit_is_rejected(self) -> None:
        request = _request_with_height(cards_w=1, card_height=1025)

        with self.assertRaisesRegex(ValueError, "不得超过1024像素"):
            plan_ports(request)


def _request_with_height(cards_w: int, card_height: int) -> PortRequest:
    screen = ScreenGeometry(
        modules_w=cards_w,
        modules_h=2,
        width_m=1.0,
        height_m=1.0,
        pixels_w=cards_w * CARD_WIDTH,
        pixels_h=2 * card_height,
    )
    return PortRequest(
        screen=screen,
        cards_w=cards_w,
        card_pixels_w=CARD_WIDTH,
        row_heights=(card_height, card_height),
        preferences=Preferences(),
    )


def _capacity_request(pixels: int, preferences: Preferences) -> PortRequest:
    screen = ScreenGeometry(1, 1, 1.0, 1.0, pixels, 1)
    return PortRequest(screen, 1, pixels, (1,), preferences)


if __name__ == "__main__":
    unittest.main()
