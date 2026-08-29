from __future__ import annotations

import unittest

from clt_helper.diagram_typography import card_font_sizes, card_padding


class DiagramTypographyTests(unittest.TestCase):
    def test_keeps_full_size_for_wide_receiver_cards(self) -> None:
        self.assertEqual(card_font_sizes(232, 692), (40, 42))
        self.assertEqual(card_padding(232), 18)

    def test_reduces_font_and_padding_for_dense_cabinet_grid(self) -> None:
        self.assertEqual(card_font_sizes(139, 139), (25, 27))
        self.assertEqual(card_padding(139), 11)


if __name__ == "__main__":
    unittest.main()
