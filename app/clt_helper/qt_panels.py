from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .catalog import (
    DEFAULT_MODULE_PIXELS,
    DEFAULT_MODULE_SIZE,
    DEFAULT_PITCH,
    DEFAULT_SCREEN_CABINETS,
    DEFAULT_SCREEN_MODULES,
    DEFAULT_SCREEN_PIXELS,
    DEFAULT_SCREEN_SIZE,
    RECEIVER_MODELS,
)
from .models import ReceiverDiscount
from .qt_diagram_view import DiagramView
from .qt_result_view import ResultView, enable_text_copy

MODULE_FORM_MARGINS = (16, 4, 16, 2)
MODULE_FORM_VERTICAL_SPACING = 4
CABINET_FORM_MARGINS = (16, 10, 16, 8)
CABINET_FORM_VERTICAL_SPACING = 9


@dataclass(frozen=True)
class FieldSpec:
    name: str
    row: int
    column: int
    text: str
    entry: QLineEdit


class ApplicationPanelsMixin:
    def _build_parameters(self, body: QVBoxLayout) -> None:
        header = self._panel_header(
            "",
            "参数配置",
            "#1769ef",
            trailing=self._mode_switch(),
        )
        body.addWidget(header)
        self._build_parameter_mode_content(body)

    def _mode_switch(self) -> QWidget:
        mode = QWidget()
        layout = QHBoxLayout(mode)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.module_mode_button = QPushButton("模组")
        self.cabinet_mode_button = QPushButton("箱体")
        self.special_mode_button = QPushButton("特殊")
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        for button in self._mode_buttons():
            button.setCheckable(True)
            button.setObjectName("ModeButton")
            self.mode_group.addButton(button)
            layout.addWidget(button)
        self.module_mode_button.setChecked(True)
        return mode

    def _mode_buttons(self) -> tuple[QPushButton, ...]:
        return self.module_mode_button, self.cabinet_mode_button, self.special_mode_button

    def _parameter_form(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("PanelContent")
        self.parameter_form_widget = widget
        form = QGridLayout(widget)
        form.setHorizontalSpacing(12)
        self.parameter_form_layout = form
        self._set_parameter_form_density(compact=True)
        self._create_parameter_entries()
        self._add_parameter_fields(form)
        return widget

    def _set_parameter_form_density(self, *, compact: bool) -> None:
        margins = MODULE_FORM_MARGINS if compact else CABINET_FORM_MARGINS
        spacing = (
            MODULE_FORM_VERTICAL_SPACING if compact else CABINET_FORM_VERTICAL_SPACING
        )
        self.parameter_form_layout.setContentsMargins(*margins)
        self.parameter_form_layout.setVerticalSpacing(spacing)
        self.parameter_form_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        self.parameter_form_widget.updateGeometry()

    def _create_parameter_entries(self) -> None:
        self.pitch_entry = QLineEdit()
        self.size_entry = QLineEdit()
        self.pixels_entry = QLineEdit()
        self.screen_modules = QLineEdit()
        self.screen_physical = QLineEdit()
        self.screen_pixels = QLineEdit()
        self._set_module_placeholders()
        self.field_widgets: dict[str, tuple[QLabel, QLineEdit]] = {}

    def _set_module_placeholders(self) -> None:
        placeholders = (
            (self.pitch_entry, DEFAULT_PITCH),
            (self.size_entry, DEFAULT_MODULE_SIZE),
            (self.pixels_entry, DEFAULT_MODULE_PIXELS),
            (self.screen_modules, DEFAULT_SCREEN_MODULES),
            (self.screen_physical, DEFAULT_SCREEN_SIZE),
            (self.screen_pixels, DEFAULT_SCREEN_PIXELS),
        )
        for entry, text in placeholders:
            entry.setPlaceholderText(text.replace("x", "×"))

    def _add_parameter_fields(self, form: QGridLayout) -> None:
        fields = (
            FieldSpec("pitch", 0, 0, "点间距 P", self.pitch_entry),
            FieldSpec("size", 0, 2, "模组 mm", self.size_entry),
            FieldSpec("pixels", 1, 0, "模组点数", self.pixels_entry),
            FieldSpec("modules", 1, 2, "屏幕块数", self.screen_modules),
            FieldSpec("physical", 2, 0, "尺寸 m", self.screen_physical),
            FieldSpec("resolution", 2, 2, "分辨率", self.screen_pixels),
        )
        for field in fields:
            self._add_field(form, field)
        self._add_discount_field(form)

    def _add_discount_field(self, form: QGridLayout) -> None:
        self.discount_label = QLabel("接收卡打折数量")
        self.discount_label.setObjectName("FieldLabel")
        self.discount_combo = QComboBox()
        self.discount_combo.setObjectName("FieldInput")
        for option in ReceiverDiscount:
            self.discount_combo.addItem(option.label, option.value)
        form.addWidget(self.discount_label, 3, 0)
        form.addWidget(self.discount_combo, 3, 1, 1, 3)

    def _add_field(
        self,
        form: QGridLayout,
        field: FieldSpec,
    ) -> None:
        label = QLabel(field.text)
        label.setObjectName("FieldLabel")
        field.entry.setObjectName("FieldInput")
        form.addWidget(label, field.row, field.column)
        form.addWidget(field.entry, field.row, field.column + 1)
        form.setColumnStretch(field.column + 1, 1)
        self.field_widgets[field.name] = label, field.entry

    def _box_options(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("BoxOptions")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 0, 16, 8)
        layout.setHorizontalSpacing(12)
        self.screen_boxes_label = QLabel("屏幕箱体数")
        self.screen_boxes_label.setObjectName("FieldLabel")
        self.screen_boxes = QLineEdit()
        self.screen_boxes.setObjectName("FieldInput")
        self.screen_boxes.setPlaceholderText(DEFAULT_SCREEN_CABINETS.replace("x", "×"))
        self.receiver_label = QLabel("接收卡选型")
        self.receiver_label.setObjectName("FieldLabel")
        self.receiver_combo = QComboBox()
        self.receiver_combo.setObjectName("FieldInput")
        self.receiver_combo.addItems(RECEIVER_MODELS)
        layout.addWidget(self.screen_boxes_label, 0, 0)
        layout.addWidget(self.screen_boxes, 0, 1)
        layout.addWidget(self.receiver_label, 0, 2)
        layout.addWidget(self.receiver_combo, 0, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return frame

    def _parameter_options(self) -> QWidget:
        options = QWidget()
        layout = QHBoxLayout(options)
        layout.setContentsMargins(16, 4, 16, 7)
        layout.setSpacing(10)
        self.auto_checkbox = QCheckBox("自动匹配模组")
        self.auto_checkbox.setChecked(True)
        self.switch_button = QPushButton("切换规格")
        self.switch_button.setObjectName("SecondaryButton")
        self.module_status = QLabel("模组 · 75接口")
        self.module_status.setObjectName("MutedText")
        layout.addWidget(self.auto_checkbox)
        layout.addWidget(self.switch_button)
        layout.addStretch(1)
        layout.addWidget(self.module_status)
        return options

    def _feature_options(self) -> QWidget:
        options = QWidget()
        layout = QHBoxLayout(options)
        layout.setContentsMargins(16, 4, 16, 7)
        layout.setSpacing(12)
        label = QLabel("功能选项")
        label.setObjectName("FieldLabel")
        self.point_checkbox = QCheckBox("点对点")
        self.async_checkbox = QCheckBox("异步功能")
        self.feature_3d_checkbox = QCheckBox("主动式3D")
        self.hdr_checkbox = QCheckBox("HDR")
        layout.addWidget(label)
        layout.addWidget(self.point_checkbox)
        layout.addWidget(self.async_checkbox)
        layout.addWidget(self.feature_3d_checkbox)
        layout.addWidget(self.hdr_checkbox)
        layout.addStretch(1)
        return options

    def _parameter_actions(self) -> QWidget:
        actions = QWidget()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(16, 2, 16, 12)
        layout.setSpacing(10)
        self.configure_button = self._primary_button("配置并生成")
        self.view_button = self._primary_button("打开原图")
        self.mapping_button = self._primary_button("导出Mapping")
        layout.addWidget(self.configure_button, 1)
        layout.addWidget(self.view_button)
        layout.addWidget(self.mapping_button)
        return actions

    @staticmethod
    def _primary_button(text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("PrimaryButton")
        return button

    def _build_output(self, body: QVBoxLayout) -> None:
        body.addWidget(
            self._panel_header(
                "",
                "方案输出",
                "#ff963f",
                trailing=self._output_header_actions(),
            )
        )
        self.result_view = ResultView()
        body.addWidget(self.result_view, 1)

    def _output_header_actions(self) -> QWidget:
        actions = QWidget()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.copy_plain_button = QPushButton("复制为纯文本形式")
        self.copy_plain_button.setObjectName("PlainTextCopyButton")
        self.output_synced_badge = QLabel("●  已同步")
        self.output_synced_badge.setObjectName("SuccessBadge")
        layout.addWidget(self.copy_plain_button)
        layout.addWidget(self.output_synced_badge)
        return actions

    def _build_diagram(self, body: QVBoxLayout) -> None:
        status = QLabel("●  方案与图同步刷新")
        status.setObjectName("DiagramStatus")
        header = self._panel_header("同步预览", "网线带载图", "#1769ef", trailing=status)
        body.addWidget(header)
        self.diagram_summary = QLabel("等待生成网线带载图")
        self.diagram_summary.setObjectName("DiagramSummary")
        enable_text_copy(self.diagram_summary)
        body.addWidget(self.diagram_summary)
        body.addWidget(self._diagram_surface(), 1)

    def _diagram_surface(self) -> QFrame:
        surface = QFrame()
        surface.setObjectName("DiagramSurface")
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(8, 8, 8, 8)
        self.diagram_view = DiagramView()
        self.diagram_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.diagram_view)
        return surface
