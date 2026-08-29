from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QStandardPaths

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.catalog import matching_modules
from clt_helper.mapping_export import (
    CONTROLLER_OUTPUT_PORTS,
    build_mapping_configs,
    controller_output_slots,
    default_mapping_directory,
    default_mapping_stem,
    generate_configuration_mappings,
    route_cards,
)
from clt_helper.mapping_generator import (
    CARD_COUNT_OFFSET,
    INNER_FIXED_HEADER_SIZE,
    decode_outer,
    parse_template,
)
from clt_helper.models import Preferences, ReceiverDiscount


def build_configuration(pitch: float, modules: tuple[int, int], preferences=Preferences()):
    module = matching_modules(pitch)[0]
    screen = screen_from_modules(module, modules)
    return calculate_configuration(module, screen, preferences)


class MappingExportTests(unittest.TestCase):
    def test_default_mapping_directory_uses_current_users_desktop(self) -> None:
        expected = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DesktopLocation
        )

        self.assertEqual(default_mapping_directory(), Path(expected))

    def test_omitted_mapping_directory_resolves_desktop_at_export_time(self) -> None:
        configuration = build_configuration(2.5, (20, 8))
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            with patch(
                "clt_helper.mapping_export.default_mapping_directory",
                return_value=destination,
            ) as resolver:
                outputs = generate_configuration_mappings(
                    configuration,
                    stem="desktop-scheme",
                )

        resolver.assert_called_once_with()
        self.assertEqual(outputs[0].parent, destination)

    def test_default_name_uses_resolution_and_receiver_grid(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        configuration = build_configuration(2.0, (12, 15), preferences)

        self.assertEqual(
            default_mapping_stem(configuration),
            "1920×1200_6×2_assistantBeta",
        )
        with tempfile.TemporaryDirectory() as temporary:
            outputs = generate_configuration_mappings(configuration, Path(temporary))

        self.assertEqual(outputs[0].name, "1920×1200_6×2_assistantBeta.mapping")

    def test_controller_models_define_physical_output_slots(self) -> None:
        expected = {
            "X2s": 2,
            "X4s": 4,
            "A100": 2,
            "X6": 6,
            "X7": 8,
            "X8E": 8,
            "X12": 12,
            "X12m": 12,
            "X16E": 16,
            "X16E-3D": 16,
            "X20": 20,
            "X26m": 26,
            "X40m": 40,
            "X20-3D": 20,
            "Z5": 16,
            "A35": 1,
            "A500": 8,
            "A800": 16,
            "A200": 4,
        }
        self.assertEqual(CONTROLLER_OUTPUT_PORTS, expected)
        for model, slots in expected.items():
            with self.subTest(model=model):
                self.assertEqual(controller_output_slots(model), slots)

    def test_mapping_uses_balanced_receiver_rows(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        configuration = build_configuration(2.0, (12, 15), preferences)

        cards = route_cards(configuration)

        self.assertEqual(len(cards), 12)
        self.assertEqual([(item.port, item.chain) for item in cards[:3]], [(1, 1), (1, 2), (1, 3)])
        self.assertEqual([(item.x, item.y) for item in cards[:3]], [(0, 0), (320, 0), (640, 0)])
        self.assertEqual(cards[6].port, 3)
        self.assertEqual(cards[6].y, 640)
        self.assertEqual(cards[-1].port, 4)

    def test_mapping_slots_follow_selected_device(self) -> None:
        configuration = build_configuration(2.5, (20, 8))

        config = build_mapping_configs(configuration)[0]

        self.assertEqual(configuration.plan.controller_model, "X4s")
        self.assertEqual(configuration.plan.primary_ports, 3)
        self.assertEqual(config["output_port_slots"], 4)

    def test_v10_header_stores_rows_before_columns(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.TWO)
        configuration = build_configuration(2.0, (12, 15), preferences)

        config = build_mapping_configs(configuration)[0]

        self.assertEqual(config["screen"], {"columns": 2, "rows": 6})
        self.assertEqual((config["cards"][0]["x"], config["cards"][0]["y"]), (0, 0))
        self.assertEqual((config["cards"][-1]["x"], config["cards"][-1]["y"]), (1600, 640))

    def test_one_row_by_six_columns_keeps_axis_order(self) -> None:
        configuration = build_configuration(2.0, (6, 6))

        config = build_mapping_configs(configuration)[0]

        self.assertEqual((configuration.plan.cards_w, configuration.plan.cards_h), (6, 1))
        self.assertEqual(config["screen"], {"columns": 1, "rows": 6})
        self.assertEqual(
            [(card["x"], card["y"]) for card in config["cards"]],
            [(0, 0), (160, 0), (320, 0), (480, 0), (640, 0), (800, 0)],
        )

    def test_discount_remainder_card_uses_actual_screen_width(self) -> None:
        preferences = Preferences(receiver_discount=ReceiverDiscount.FOUR)
        configuration = build_configuration(2.5, (10, 4), preferences)

        cards = route_cards(configuration)

        self.assertEqual(configuration.plan.cards_w, 3)
        first_row = cards[: configuration.plan.cards_w]
        self.assertEqual([(card.x, card.width) for card in first_row], [(0, 512), (512, 512), (1024, 256)])

    def test_generated_mapping_passes_crc_and_structure_checks(self) -> None:
        configuration = build_configuration(2.5, (20, 8))

        with tempfile.TemporaryDirectory() as temporary:
            outputs = generate_configuration_mappings(configuration, Path(temporary), "scheme")
            data = outputs[0].read_bytes()

        template = parse_template(data)
        _, payload = decode_outer(data)
        card_count = struct.unpack_from("<H", payload, CARD_COUNT_OFFSET)[0]
        slots = struct.unpack_from("<H", payload, INNER_FIXED_HEADER_SIZE)[0]
        self.assertEqual(len(template.port_records), 4)
        self.assertEqual(card_count, configuration.plan.card_count)
        self.assertEqual(slots, 4)

    def test_multiple_devices_generate_one_mapping_per_device(self) -> None:
        configuration = build_configuration(2.5, (220, 160))
        self.assertGreater(configuration.plan.controller_count, 1)

        with tempfile.TemporaryDirectory() as temporary:
            outputs = generate_configuration_mappings(configuration, Path(temporary), "multi")
            parsed = [parse_template(path.read_bytes()) for path in outputs]

        self.assertEqual(len(outputs), configuration.plan.controller_count)
        expected_slots = configuration.plan.controller_output_ports
        self.assertTrue(all(len(item.port_records) == expected_slots for item in parsed))

    def test_multiple_devices_append_unique_device_suffixes(self) -> None:
        configuration = build_configuration(2.5, (220, 160))

        with tempfile.TemporaryDirectory() as temporary:
            outputs = generate_configuration_mappings(configuration, Path(temporary))

        expected_stem = default_mapping_stem(configuration)
        self.assertEqual(
            [path.name for path in outputs],
            [
                f"{expected_stem}_设备{index}.mapping"
                for index in range(1, configuration.plan.controller_count + 1)
            ],
        )

    def test_backup_mapping_fails_explicitly(self) -> None:
        configuration = build_configuration(2.0, (12, 15), Preferences(loop_backup=True))

        with self.assertRaisesRegex(ValueError, "环路备份"):
            build_mapping_configs(configuration)


if __name__ == "__main__":
    unittest.main()
