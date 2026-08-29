from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontInfo
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QSizePolicy, QWidget

from clt_helper.models import UnitMode
from clt_helper.qt_application import CLTApplication
from clt_helper.qt_style import FONT_FAMILY, FONT_RESULT_PT, application_stylesheet
from tests.ui_test_helpers import configured_window


class ParameterLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qt_app = QApplication.instance() or QApplication([])
        self.window = configured_window()

    def tearDown(self) -> None:
        self.window.close()

    def _apply_base_scale(self) -> None:
        self.window._apply_scale(1.0)
        self.window.show()
        self.qt_app.processEvents()

    def test_uses_microsoft_yahei_for_scaled_styles(self) -> None:
        stylesheet = application_stylesheet(lambda value: value)
        self.assertEqual(FONT_FAMILY, "Microsoft YaHei")
        self.assertIn("'Microsoft YaHei'", stylesheet)
        self.assertIn("font:11pt", stylesheet)

    def test_mode_buttons_use_short_labels_and_emphasized_font(self) -> None:
        self._apply_base_scale()
        module_font = QFontInfo(self.window.module_mode_button.font())
        self.assertEqual(self.window.module_mode_button.text(), "模组")
        self.assertEqual(self.window.cabinet_mode_button.text(), "箱体")
        self.assertEqual(self.window.special_mode_button.text(), "特殊")
        self.assertEqual(module_font.pointSize(), 12)
        self.assertGreaterEqual(module_font.weight(), 600)

    def test_result_content_uses_smaller_font(self) -> None:
        self._apply_base_scale()
        result_item = self.window.result_view.findChild(QLabel, "ResultHighlightItem")
        self.assertIsNotNone(result_item)
        assert result_item is not None
        result_font = QFontInfo(result_item.font())
        self.assertEqual(FONT_RESULT_PT, 10)
        self.assertEqual(result_font.pointSize(), FONT_RESULT_PT)

    def test_compact_result_sections_use_smaller_font_than_highlight(self) -> None:
        self._apply_base_scale()
        compact_item = self.window.result_view.findChild(QLabel, "ResultItem")
        highlight_item = self.window.result_view.findChild(QLabel, "ResultHighlightItem")
        self.assertIsNotNone(compact_item)
        self.assertIsNotNone(highlight_item)
        assert compact_item is not None and highlight_item is not None
        compact_size = QFontInfo(compact_item.font()).pointSize()
        highlight_size = QFontInfo(highlight_item.font()).pointSize()
        self.assertEqual(compact_size, 7)
        self.assertEqual(highlight_size, 10)

    def test_result_sections_keep_order_and_highlight_configuration(self) -> None:
        self._apply_base_scale()
        section_names = (
            "ResultSectionScreen",
            "ResultSectionReceiver",
            "ResultSectionNetwork",
            "ResultSectionHighlight",
        )
        frames = [
            self.window.result_view.findChild(QFrame, name) for name in section_names
        ]
        self.assertTrue(all(frame is not None for frame in frames))
        summary = self.window.result_view.findChild(QWidget, "ResultSummaryRow")
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(self.window.result_view.content_layout.indexOf(summary), 0)
        self.assertEqual(self.window.result_view.content_layout.indexOf(frames[3]), 1)
        summary_layout = summary.layout()
        self.assertEqual([summary_layout.indexOf(frame) for frame in frames[:3]], [0, 1, 2])
        widths = [frame.width() for frame in frames[:3]]
        self.assertLessEqual(max(widths) - min(widths), 1)

    def test_parameter_and_output_titles_are_left_aligned_without_kickers(self) -> None:
        labels = self.window.findChildren(QLabel)
        texts = {label.text() for label in labels}
        self.assertNotIn("输入", texts)
        self.assertNotIn("结果", texts)
        panel_titles = [
            label for label in labels if label.text() in {"参数配置", "方案输出"}
        ]
        self.assertEqual(len(panel_titles), 2)
        expected = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        self.assertEqual([label.alignment() for label in panel_titles], [expected] * 2)

    def test_cabinet_second_row_uses_standard_field_labels(self) -> None:
        self._apply_base_scale()
        labels = (self.window.screen_boxes_label, self.window.receiver_label)
        self.assertEqual({label.text() for label in labels}, {"屏幕箱体数", "接收卡选型"})
        self.assertTrue(all(QFontInfo(label.font()).pointSize() == 10 for label in labels))

    def test_hidden_cabinet_rows_do_not_reserve_stretch_space(self) -> None:
        self.window._set_mode(UnitMode.CABINET)
        stretches = [self.window.parameter_form_layout.rowStretch(row) for row in range(4)]
        self.assertEqual(stretches, [0, 0, 0, 0])
        self.assertEqual(self.window.parameter_form_layout.verticalSpacing(), 9)
        policy = self.window.parameter_form_widget.sizePolicy().verticalPolicy()
        self.assertEqual(policy, QSizePolicy.Policy.Maximum)

    def test_module_mode_uses_compact_natural_height(self) -> None:
        self.window._set_mode(UnitMode.CABINET)
        self.window._set_mode(UnitMode.MODULE)
        stretches = [self.window.parameter_form_layout.rowStretch(row) for row in range(4)]
        self.assertEqual(stretches, [0, 0, 0, 0])
        self.assertEqual(self.window.parameter_form_layout.verticalSpacing(), 4)
        policy = self.window.parameter_form_widget.sizePolicy().verticalPolicy()
        self.assertEqual(policy, QSizePolicy.Policy.Maximum)


if __name__ == "__main__":
    unittest.main()
