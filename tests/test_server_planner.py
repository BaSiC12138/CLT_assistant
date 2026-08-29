from __future__ import annotations

import unittest

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.models import Preferences
from clt_helper.server_planner import (
    FOUR_K_PIXELS,
    SERVER_OUT_OF_RANGE,
    SERVER_SELECTION_NOTE,
    select_server,
)


class ServerPlannerTests(unittest.TestCase):
    def test_server_models_follow_exact_4k_boundaries(self) -> None:
        cases = (
            (1, "CS4K-G3"),
            (2, "CS6K-G3"),
            (4, "CS8K-G3"),
            (8, "CS16K（双显卡）"),
            (12, "CS16K（三显卡）"),
            (16, "CS16K（四显卡）"),
        )
        previous_limit = 0
        for units, expected in cases:
            with self.subTest(units=units, boundary="lower"):
                self.assertEqual(select_server(previous_limit * FOUR_K_PIXELS + 1), expected)
            with self.subTest(units=units, boundary="upper"):
                self.assertEqual(select_server(units * FOUR_K_PIXELS), expected)
            previous_limit = units

    def test_pixels_above_sixteen_4k_are_explicitly_unconfigured(self) -> None:
        pixels = 16 * FOUR_K_PIXELS + 1

        self.assertEqual(select_server(pixels), SERVER_OUT_OF_RANGE)

    def test_configuration_output_contains_server_and_required_note(self) -> None:
        module = matching_modules(2.0)[0]
        screen = screen_from_modules(module, (12, 6))
        configuration = calculate_configuration(module, screen, Preferences())

        self.assertIn("服务器：CS4K-G3", configuration.result_text)
        self.assertIn(f"注意：{SERVER_SELECTION_NOTE}", configuration.result_text)

    def test_asynchronous_configuration_omits_server_selection(self) -> None:
        module = matching_modules(2.0)[0]
        screen = screen_from_modules(module, (12, 6))
        configuration = calculate_configuration(
            module,
            screen,
            Preferences(asynchronous=True),
        )

        self.assertNotIn("服务器：", configuration.result_text)
        self.assertNotIn(SERVER_SELECTION_NOTE, configuration.result_text)
        self.assertTrue(configuration.plan.controller_model.startswith("A"))


if __name__ == "__main__":
    unittest.main()
