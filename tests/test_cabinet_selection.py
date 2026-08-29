from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.models import Preferences


def cabinet_plan(
    shape: tuple[int, int],
    preferences: Preferences = Preferences(),
    receiver: str | None = None,
):
    module = matching_modules(2.5)[0]
    screen_modules = shape[0] * 2, shape[1] * 2
    screen = screen_from_modules(module, screen_modules)
    return calculate_configuration(
        module,
        screen,
        preferences,
        receiver_override=receiver,
        card_shape_override=shape,
    ).plan


class CabinetSelectionTests(unittest.TestCase):
    def test_auto_selects_smallest_capable_k_series_receiver(self) -> None:
        cases = (
            ((4, 6), "K5+"),
            ((5, 5), "K8"),
            ((6, 6), "K10"),
        )
        for shape, expected in cases:
            with self.subTest(shape=shape):
                self.assertEqual(cabinet_plan(shape).receiver_model, expected)

    def test_manual_selection_is_not_silently_upgraded(self) -> None:
        with self.assertRaisesRegex(ValueError, r"K5\+单卡带载上限"):
            cabinet_plan((6, 6), receiver="K5+")

    def test_each_k_series_model_can_be_selected_manually(self) -> None:
        for model in ("K5+", "K8", "K10"):
            with self.subTest(model=model):
                plan = cabinet_plan((2, 3), receiver=model)
                self.assertEqual(plan.receiver_model, model)

    def test_active_3d_halving_can_promote_auto_selection_to_k10(self) -> None:
        plan = cabinet_plan((4, 4), Preferences(feature_3d=True))

        self.assertEqual(plan.receiver_model, "K10")
        self.assertEqual(plan.port_capacity, 325_000)

    def test_auto_fails_when_no_k_series_receiver_can_carry_cabinet(self) -> None:
        with self.assertRaisesRegex(ValueError, r"K5\+、K8、K10均无法满足"):
            cabinet_plan((7, 7))


if __name__ == "__main__":
    unittest.main()
