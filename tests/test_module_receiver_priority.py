from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.hardware import RECEIVER_LIMITS
from clt_helper.models import ModuleSpec, Preferences, ReceiverDiscount


def plan(
    pitch: float,
    modules: tuple[int, int],
    preferences: Preferences,
    *,
    receiver: str | None = None,
):
    module = matching_modules(pitch)[0]
    screen = screen_from_modules(module, modules)
    return calculate_configuration(
        module,
        screen,
        preferences,
        receiver_override=receiver,
    ).plan


class ModuleReceiverPriorityTests(unittest.TestCase):
    def test_module_receiver_hub_counts_match_product_specs(self) -> None:
        expected = {
            "5A-75E": 16,
            "E80": 8,
            "E120": 12,
            "E320": 8,
            "E80-G2": 8,
        }

        actual = {model: RECEIVER_LIMITS[model].module_limit for model in expected}
        self.assertEqual(actual, expected)

    def test_primary_ports_have_priority_over_receiver_count(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        selected = plan(5.0, (60, 36), preferences)
        five_a = plan(5.0, (60, 36), preferences, receiver="5A-75E")

        self.assertEqual((selected.receiver_model, selected.primary_ports), ("E120", 8))
        self.assertEqual((five_a.primary_ports, five_a.card_count), (9, 150))
        self.assertGreater(selected.card_count, five_a.card_count)

    def test_receiver_count_breaks_equal_port_tie(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        selected = plan(2.0, (12, 15), preferences)
        e80 = plan(2.0, (12, 15), preferences, receiver="E80")

        self.assertEqual((selected.receiver_model, selected.primary_ports), ("5A-75E", 4))
        self.assertEqual((e80.primary_ports, e80.card_count), (4, 24))
        self.assertEqual(selected.card_count, 12)

    def test_selected_discount_width_is_never_changed(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.THREE)
        for model in ("E80", "E120", "5A-75E"):
            with self.subTest(model=model):
                selected = plan(5.0, (12, 13), preferences, receiver=model)
                self.assertEqual(selected.card_modules_w, 3)

    def test_odd_height_is_balanced_top_to_bottom(self) -> None:
        selected = plan(5.0, (1, 13), Preferences(), receiver="E120")

        self.assertEqual(
            [(band.card_modules_h, band.row_count) for band in selected.bands],
            [(7, 1), (6, 1)],
        )

    def test_hub_count_limits_height_after_discount(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        selected = plan(5.0, (12, 13), preferences, receiver="E120")

        self.assertEqual(
            [(band.card_modules_h, band.row_count) for band in selected.bands],
            [(5, 1), (4, 2)],
        )
        self.assertEqual(selected.card_count, 18)

    def test_pixel_height_limit_applies_to_all_module_receivers(self) -> None:
        module = ModuleSpec(1.0, 1, 200, 1, 200)
        screen = screen_from_modules(module, (1, 13))
        selected = calculate_configuration(
            module,
            screen,
            Preferences(),
            receiver_override="E120",
        ).plan

        self.assertLessEqual(selected.card_pixels_h, 1024)
        self.assertEqual(selected.card_modules_h, 5)

    def test_all_k_series_are_rejected_in_module_mode(self) -> None:
        for model in ("K5+", "K8", "K10"):
            with self.subTest(model=model):
                with self.assertRaisesRegex(ValueError, "禁止使用K系列"):
                    plan(2.5, (12, 12), Preferences(), receiver=model)

    def test_e80_g2_is_rejected_without_hdr(self) -> None:
        with self.assertRaisesRegex(ValueError, "E80-G2仅用于.*HDR"):
            plan(2.5, (12, 12), Preferences(), receiver="E80-G2")


if __name__ == "__main__":
    unittest.main()
