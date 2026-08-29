from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageColor

from clt_helper.calculator import calculate_configuration, screen_from_modules
from clt_helper.diagram import (
    CANVAS_BACKGROUND,
    CANVAS_MARGIN,
    CARD_INSET,
    CABLE_COLOR,
    CANVAS_SIZE,
    PORT_PALETTE,
    generate_diagram,
    render_diagram,
)
from clt_helper.models import ModuleSpec, Preferences
from clt_helper.parsing import parse_int_pair


class ParsingAndDiagramTests(unittest.TestCase):
    def test_accepts_x_space_and_multiplication_formats(self) -> None:
        self.assertEqual(parse_int_pair("128x64"), (128, 64))
        self.assertEqual(parse_int_pair("128 64"), (128, 64))
        self.assertEqual(parse_int_pair("128×64"), (128, 64))

    def test_generates_viewable_jpeg(self) -> None:
        module = ModuleSpec(2.5, 320, 160, 128, 64)
        screen = screen_from_modules(module, (12, 12))
        configuration = calculate_configuration(module, screen, Preferences())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "图示.jpg"

            generate_diagram(configuration, output)

            with Image.open(output) as image:
                self.assertEqual(image.size, CANVAS_SIZE)
                self.assertEqual(image.format, "JPEG")

    def test_diagram_uses_distinct_port_colors_and_cable_arrows(self) -> None:
        module = ModuleSpec(2.5, 320, 160, 128, 64)
        screen = screen_from_modules(module, (12, 12))
        configuration = calculate_configuration(module, screen, Preferences())

        image = render_diagram(configuration)
        colors = image.getcolors(maxcolors=CANVAS_SIZE[0] * CANVAS_SIZE[1])
        assert colors is not None
        present = {color for _, color in colors}

        self.assertIn(ImageColor.getrgb(PORT_PALETTE[0]), present)
        self.assertIn(ImageColor.getrgb(PORT_PALETTE[1]), present)
        self.assertIn(ImageColor.getrgb(CABLE_COLOR), present)

    def test_receiver_cards_have_rounded_corners(self) -> None:
        module = ModuleSpec(2.5, 320, 160, 128, 64)
        screen = screen_from_modules(module, (12, 12))
        configuration = calculate_configuration(module, screen, Preferences())

        image = render_diagram(configuration)
        corner = CANVAS_MARGIN + CARD_INSET

        self.assertEqual(image.getpixel((corner, corner)), ImageColor.getrgb(CANVAS_BACKGROUND))


if __name__ == "__main__":
    unittest.main()
