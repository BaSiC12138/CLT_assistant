from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, infer_screen, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.models import (
    InterfaceMode,
    ModuleSpec,
    Preferences,
    ReceiverDiscount,
    ScreenInputs,
)


def configuration(
    pitch: float,
    modules: tuple[int, int],
    preferences: Preferences = Preferences(),
):
    module = matching_modules(pitch)[0]
    screen = screen_from_modules(module, modules)
    return calculate_configuration(module, screen, preferences)


class CalculatorTests(unittest.TestCase):
    def test_infers_screen_from_each_supported_input(self) -> None:
        module = matching_modules(2.5)[0]
        cases = (
            ScreenInputs(module_count="12 12"),
            ScreenInputs(physical_size="3.84x1.92"),
            ScreenInputs(pixel_size="1536x768"),
        )
        for inputs in cases:
            with self.subTest(inputs=inputs):
                screen = infer_screen(module, inputs)
                self.assertIsNotNone(screen)
                assert screen is not None
                self.assertEqual((screen.modules_w, screen.modules_h), (12, 12))

    def test_p2_scheme_obeys_updated_receiver_limits(self) -> None:
        result = configuration(
            2.0,
            (12, 15),
            Preferences(receiver_discount=ReceiverDiscount.TWO),
        )
        plan = result.plan

        self.assertEqual(plan.receiver_model, "5A-75E")
        self.assertEqual((plan.card_modules_w, plan.card_modules_h), (2, 8))
        self.assertEqual(plan.card_count, 12)
        self.assertEqual((plan.port_group_w, plan.port_group_h), (3, 1))
        self.assertEqual(plan.primary_ports, 4)
        self.assertEqual((plan.controller_model, plan.controller_count), ("X4s", 1))

    def test_p186_scheme_obeys_updated_receiver_limits(self) -> None:
        preferences = Preferences(
            point_to_point=True,
            fiber_transmission=True,
            receiver_discount=ReceiverDiscount.TWO,
        )
        result = configuration(1.86, (24, 27), preferences)
        plan = result.plan

        self.assertEqual((result.screen.pixels_w, result.screen.pixels_h), (4128, 2322))
        self.assertEqual(plan.receiver_model, "5A-75E")
        self.assertEqual((plan.card_modules_w, plan.card_modules_h), (2, 7))
        self.assertEqual(plan.card_count, 48)
        self.assertEqual((plan.port_group_w, plan.port_group_h), (3, 1))
        self.assertEqual(plan.primary_ports, 16)
        self.assertEqual(plan.controller_model, "X16E")
        self.assertIn("H16F光纤收发器 × 2", plan.accessories)

    def test_pdf_p5_example_uses_fewer_crossed_rows(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        plan = configuration(5.0, (60, 36), preferences).plan

        self.assertEqual(plan.receiver_model, "E120")
        self.assertEqual((plan.card_modules_w, plan.card_modules_h), (2, 6))
        self.assertEqual(plan.card_count, 180)
        self.assertEqual((plan.port_group_w, plan.port_group_h), (8, 3))
        self.assertEqual(plan.primary_ports, 8)
        self.assertEqual(plan.controller_model, "X7")

    def test_p2_twelve_by_six_keeps_confirmed_e80_scheme(self) -> None:
        result = configuration(2.0, (12, 6))
        plan = result.plan

        self.assertEqual((result.screen.pixels_w, result.screen.pixels_h), (1920, 480))
        self.assertEqual(plan.receiver_model, "E80")
        self.assertEqual((plan.card_modules_w, plan.card_modules_h), (1, 6))
        self.assertEqual(plan.card_count, 12)
        self.assertEqual(plan.cards_per_port, 8)
        self.assertEqual(plan.primary_ports, 2)
        self.assertEqual(plan.controller_model, "X2s")

    def test_3d_uses_dedicated_receiver_and_controller(self) -> None:
        module = matching_modules(2.0)[0]
        screen = screen_from_modules(module, (12, 8))
        preferences = Preferences(receiver_discount=ReceiverDiscount.THREE)
        normal = calculate_configuration(
            module,
            screen,
            preferences,
            receiver_override="E120",
        ).plan
        feature_3d = calculate_configuration(
            module,
            screen,
            Preferences(feature_3d=True, receiver_discount=ReceiverDiscount.THREE),
        ).plan

        self.assertEqual(feature_3d.card_modules_w, normal.card_modules_w)
        self.assertEqual((normal.card_modules_h, feature_3d.card_modules_h), (4, 3))
        self.assertGreater(feature_3d.card_count, normal.card_count)
        self.assertEqual(feature_3d.receiver_model, "E120")
        self.assertEqual(feature_3d.port_capacity, 325_000)
        self.assertGreater(feature_3d.primary_ports, normal.primary_ports)
        self.assertEqual(feature_3d.controller_model, "X16E-3D")

    def test_hdr_uses_e80_g2_and_seventy_five_percent_port_capacity(self) -> None:
        module = matching_modules(2.0)[0]
        screen = screen_from_modules(module, (12, 15))
        plan = calculate_configuration(module, screen, Preferences(feature_hdr=True)).plan

        self.assertEqual(plan.receiver_model, "E80-G2")
        self.assertEqual((plan.card_pixels_w, plan.card_pixels_h), (160, 640))
        self.assertEqual(plan.card_count, 24)
        self.assertEqual(plan.port_capacity, 487_500)
        self.assertEqual(plan.controller_model, "Z5")

    def test_loop_backup_doubles_required_outputs(self) -> None:
        plan = configuration(2.0, (12, 15), Preferences(loop_backup=True)).plan

        self.assertEqual(plan.primary_ports, 4)
        self.assertEqual(plan.required_ports, 8)
        self.assertEqual(plan.controller_model, "X7")

    def test_point_to_point_4k_requires_4k_input_controller(self) -> None:
        result = configuration(2.0, (16, 18), Preferences(point_to_point=True))

        self.assertIn(result.plan.controller_model, ("X8E", "X16E", "X20"))

    def test_only_p125_module_mode_keeps_e320(self) -> None:
        p125 = configuration(1.25, (30, 15)).plan
        p25 = configuration(
            2.5,
            (12, 8),
            Preferences(interface=InterfaceMode.HUB320),
        ).plan

        self.assertEqual(p125.receiver_model, "E320")
        self.assertEqual(p25.receiver_model, "E80")

    def test_forced_75_interface_uses_e80_for_short_screen(self) -> None:
        plan = configuration(
            1.53,
            (12, 8),
            Preferences(interface=InterfaceMode.HUB75),
        ).plan

        self.assertEqual(plan.receiver_model, "E80")

    def test_receiver_discount_controls_cards_per_row(self) -> None:
        cases = (
            (ReceiverDiscount.NONE, 12),
            (ReceiverDiscount.TWO, 6),
            (ReceiverDiscount.THREE, 4),
            (ReceiverDiscount.FOUR, 3),
        )
        for discount, expected_cards_w in cases:
            with self.subTest(discount=discount):
                preferences = Preferences(receiver_discount=discount)
                result = configuration(5.0, (12, 6), preferences)
                self.assertEqual(result.plan.card_modules_w, discount.value)
                self.assertEqual(result.plan.cards_w, expected_cards_w)
                self.assertIn(f"接收卡打折数量：{discount.label}", result.result_text)

    def test_receiver_discount_rejects_width_beyond_card_limit(self) -> None:
        preferences = Preferences(
            feature_hdr=True,
            receiver_discount=ReceiverDiscount.FOUR,
        )

        with self.assertRaisesRegex(ValueError, "调整接收卡打折数量"):
            configuration(1.25, (12, 6), preferences)

    def test_cabinet_mode_auto_selects_k5_for_matching_load(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (8, 12))
        result = calculate_configuration(
            module,
            screen,
            Preferences(),
            card_shape_override=(4, 6),
        )

        self.assertEqual(result.plan.receiver_model, "K5+")
        self.assertEqual((result.plan.card_pixels_w, result.plan.card_pixels_h), (512, 384))

    def test_k5_rejects_oversized_cabinet(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (10, 14))

        with self.assertRaisesRegex(ValueError, "512×384"):
            calculate_configuration(
                module,
                screen,
                Preferences(),
                receiver_override="K5+",
                card_shape_override=(5, 7),
            )

    def test_k5_cascade_is_capped_at_sixty_four_cards(self) -> None:
        module = ModuleSpec(10.0, 10, 10, 1, 1)
        screen = screen_from_modules(module, (100, 1))
        plan = calculate_configuration(
            module,
            screen,
            Preferences(),
            card_shape_override=(1, 1),
        ).plan

        self.assertEqual(plan.cards_per_port, 64)
        self.assertEqual(plan.primary_ports, 2)

    def test_hdr_allows_k5_cabinet_mode(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (8, 12))
        plan = calculate_configuration(
            module,
            screen,
            Preferences(feature_hdr=True),
            card_shape_override=(4, 6),
        ).plan

        self.assertEqual(plan.receiver_model, "K5+")
        self.assertEqual(plan.controller_model, "Z5")

    def test_3d_halves_k5_cabinet_receiver_capacity(self) -> None:
        module = matching_modules(2.5)[0]
        screen = screen_from_modules(module, (8, 12))

        with self.assertRaisesRegex(ValueError, "98304像素"):
            calculate_configuration(
                module,
                screen,
                Preferences(feature_3d=True),
                receiver_override="K5+",
                card_shape_override=(4, 6),
            )

    def test_observed_module_catalog_corrections(self) -> None:
        self.assertEqual(matching_modules(1.5)[0].pixels_text, "213x107")
        self.assertEqual(matching_modules(3.91)[0].pixels_text, "82x41")
        self.assertEqual(matching_modules(4.81)[0].pixels_text, "67x33")


if __name__ == "__main__":
    unittest.main()
