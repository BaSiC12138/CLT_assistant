from __future__ import annotations

from pathlib import Path

from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QAbstractButton, QApplication, QMessageBox

from .calculator import calculate_configuration, infer_screen
from .catalog import (
    DEFAULT_CABINET_MODEL,
    DEFAULT_MODULE_PIXELS,
    DEFAULT_MODULE_SIZE,
    DEFAULT_PITCH,
    DEFAULT_PITCH_VALUE,
    DEFAULT_SCREEN_CABINETS,
    DEFAULT_SCREEN_MODULES,
    matching_modules,
)
from .diagram import open_diagram, render_diagram
from .mapping_export import generate_configuration_mappings
from .models import (
    InterfaceMode,
    ModuleSpec,
    Preferences,
    ReceiverDiscount,
    ScreenGeometry,
    ScreenInputs,
    UnitMode,
)
from .parsing import parse_positive_float
from .plain_text_formatter import format_plain_text


class ApplicationBehaviorMixin:
    def _initialize_startup_state(self) -> None:
        self._reset_mode_states()
        for entry in self._startup_entries():
            entry.clear()
        self.receiver_combo.setCurrentText(DEFAULT_CABINET_MODEL)
        self.discount_combo.setCurrentIndex(0)
        self._reset_feature_actions()
        self.auto_checkbox.setChecked(True)
        self.screen_source = "modules"
        self.module_options = ()
        self.module_index = 0
        self._set_mode(UnitMode.MODULE)
        self._set_status("等待输入参数", False)

    def _startup_entries(self) -> tuple:
        return (
            self.pitch_entry,
            self.size_entry,
            self.pixels_entry,
            self.screen_modules,
            self.screen_physical,
            self.screen_pixels,
            self.screen_boxes,
        )

    def _connect_signals(self) -> None:
        self.module_mode_button.clicked.connect(lambda: self._set_mode(UnitMode.MODULE))
        self.cabinet_mode_button.clicked.connect(lambda: self._set_mode(UnitMode.CABINET))
        self.special_mode_button.clicked.connect(lambda: self._set_mode(UnitMode.SPECIAL))
        self.pitch_entry.textEdited.connect(self._on_pitch_changed)
        self._connect_module_screen_signals()
        for entry in self._dirty_entries():
            entry.textEdited.connect(self._mark_dirty)
        self.auto_checkbox.toggled.connect(self._toggle_auto)
        self.switch_button.clicked.connect(self._switch_module)
        self.configure_button.clicked.connect(self._configure_scheme)
        self.copy_plain_button.clicked.connect(self._copy_plain_text)
        self.view_button.clicked.connect(self._open_diagram)
        self.mapping_button.clicked.connect(self._export_mapping)
        self.receiver_combo.currentTextChanged.connect(self._mark_dirty)
        self.discount_combo.currentIndexChanged.connect(self._mark_dirty)
        exclusions = (
            (self.async_checkbox, (self.point_checkbox, self.feature_3d_checkbox, self.hdr_checkbox)),
            (self.point_checkbox, (self.async_checkbox,)),
            (self.feature_3d_checkbox, (self.async_checkbox, self.hdr_checkbox)),
            (self.hdr_checkbox, (self.async_checkbox, self.feature_3d_checkbox)),
        )
        for option, others in exclusions:
            option.toggled.connect(
                lambda enabled, peers=others: self._toggle_exclusive_features(enabled, peers)
            )

    def _toggle_exclusive_features(
        self,
        enabled: bool,
        others: tuple[QAbstractButton, ...],
    ) -> None:
        if enabled:
            for option in others:
                option.setChecked(False)
        self._mark_dirty()

    def _update_parameter_row_stretch(self, box_mode: bool) -> None:
        for row in range(self.parameter_form_layout.rowCount()):
            self.parameter_form_layout.setRowStretch(row, 0)
        self._set_parameter_form_density(compact=not box_mode)

    def _toggle_auto(self, enabled: bool) -> None:
        read_only = enabled and not self.cabinet_mode_button.isChecked()
        self.size_entry.setReadOnly(read_only)
        self.pixels_entry.setReadOnly(read_only)
        if enabled:
            self._on_pitch_changed(self.pitch_entry.text())
        self._mark_dirty()

    def _on_pitch_changed(self, text: str) -> None:
        if self.cabinet_mode_button.isChecked():
            self._mark_dirty()
            return
        if not self.auto_checkbox.isChecked():
            self._mark_dirty()
            return
        pitch = parse_positive_float(text)
        self.module_options = matching_modules(pitch) if pitch else ()
        self.module_index = 0
        if self.module_options:
            self._show_module(self.module_options[0])
        self._mark_dirty()

    def _switch_module(self) -> None:
        if self.cabinet_mode_button.isChecked():
            return
        if len(self.module_options) < 2:
            return
        self.module_index = (self.module_index + 1) % len(self.module_options)
        self._show_module(self.module_options[self.module_index])
        self._mark_dirty()

    def _show_module(self, module: ModuleSpec) -> None:
        self.size_entry.setText(module.size_text)
        self.pixels_entry.setText(module.pixels_text)
        self.module_status.setText(f"模组 · {module.interface}")
        self._refresh_module_screen_fields()

    def _set_screen_source(self, source: str) -> None:
        self.screen_source = source
        self._mark_dirty()

    def _current_module(self) -> ModuleSpec | None:
        if self._active_mode is UnitMode.SPECIAL:
            return None
        if self.cabinet_mode_button.isChecked():
            interface = "320接口" if self.interface_320_action.isChecked() else "75接口"
            if self.auto_checkbox.isChecked() and self.module_options:
                interface = self.module_options[self.module_index].interface
            return self._manual_cabinet_module(interface)
        if self.auto_checkbox.isChecked():
            return self.module_options[self.module_index] if self.module_options else None
        interface = "320接口" if self.interface_320_action.isChecked() else "75接口"
        return self._manual_module_from_fields(interface)

    def _current_screen(self, module: ModuleSpec) -> ScreenGeometry | None:
        if self.cabinet_mode_button.isChecked():
            return self._cabinet_screen(module)
        values = self._screen_values()
        inputs = ScreenInputs(
            module_count=values["modules"] if self.screen_source == "modules" else "",
            physical_size=values["physical"] if self.screen_source == "physical" else "",
            pixel_size=values["pixels"] if self.screen_source == "pixels" else "",
        )
        return infer_screen(module, inputs)

    def _screen_values(self) -> dict[str, str]:
        return {
            "modules": self.screen_modules.text(),
            "physical": self.screen_physical.text(),
            "pixels": self.screen_pixels.text(),
        }

    def _preferences(self) -> Preferences:
        interface = InterfaceMode(self.interface_group.checkedAction().data())
        return Preferences(
            point_to_point=self.point_checkbox.isChecked(),
            asynchronous=self.async_checkbox.isChecked(),
            feature_3d=self.feature_3d_checkbox.isChecked(),
            feature_hdr=self.hdr_checkbox.isChecked(),
            loop_backup=self.backup_action.isChecked(),
            fiber_transmission=self.fiber_action.isChecked(),
            interface=interface,
            receiver_discount=ReceiverDiscount(self.discount_combo.currentData()),
            copy_text=self.copy_action.isChecked(),
        )

    def _configure_scheme(self) -> None:
        if self._active_mode is UnitMode.SPECIAL:
            return
        module = self._current_module()
        screen = self._current_screen(module) if module else None
        if not module or not screen:
            QMessageBox.warning(self, "参数错误", "请填写一组完整且匹配的模组与屏幕参数。")
            return
        receiver, card_shape = self._cabinet_options()
        try:
            self.configuration = calculate_configuration(
                module,
                screen,
                self._preferences(),
                receiver_override=receiver,
                card_shape_override=card_shape,
            )
        except ValueError as error:
            QMessageBox.warning(self, "参数错误", str(error))
            return
        self._display_configuration(screen)

    def _display_configuration(self, screen: ScreenGeometry) -> None:
        self.result_view.set_configuration(self.configuration)
        self._show_derived_screen(screen)
        self._update_diagram()
        if self.copy_action.isChecked():
            QApplication.clipboard().setText(self.configuration.result_text)
        self._set_status("方案与带载图已同步", True)

    def _update_diagram(self) -> None:
        if self.configuration is None:
            return
        image = render_diagram(self.configuration)
        self._diagram_pixmap = QPixmap.fromImage(ImageQt(image))
        plan = self.configuration.plan
        screen = self.configuration.screen
        self.diagram_summary.setText(
            f"{screen.pixels_w} × {screen.pixels_h}   ·   {plan.receiver_model} × {plan.card_count}   ·   "
            f"{plan.primary_ports} 个主网口   ·   {plan.controller_model} × {plan.controller_count}"
        )
        self.diagram_view.set_pixmap(self._diagram_pixmap)

    def _open_diagram(self) -> None:
        if self.configuration is None:
            QMessageBox.information(self, "温馨提示", "请先完成配置。")
            return
        open_diagram(self.configuration, Path.cwd())

    def _copy_plain_text(self) -> None:
        if self.configuration is None:
            QMessageBox.information(self, "温馨提示", "请先完成配置。")
            return
        text = format_plain_text(self.configuration)
        QApplication.clipboard().setText(text)
        self._set_status("纯文本已复制", True)

    def _export_mapping(self) -> None:
        if self.configuration is None:
            QMessageBox.information(self, "温馨提示", "请先完成配置。")
            return
        try:
            outputs = generate_configuration_mappings(self.configuration)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Mapping生成失败", str(error))
            return
        paths = "\n".join(str(path) for path in outputs)
        QMessageBox.information(self, "Mapping已生成", f"文件已保存：\n{paths}")
        self._set_status("Mapping已生成", True)

    def _mark_dirty(self, *_args: object) -> None:
        self._set_status("参数已修改，等待重新配置", False)

    def _set_status(self, text: str, success: bool) -> None:
        color = "#10a35e" if success else "#1769ef"
        for label in (self.header_status, self.footer_status):
            label.setText(f"●  {text}")
            label.setStyleSheet(f"color:{color};")

    def _reset_defaults(self) -> None:
        self._reset_mode_states()
        self.pitch_entry.setText(DEFAULT_PITCH)
        self.size_entry.setText(DEFAULT_MODULE_SIZE)
        self.pixels_entry.setText(DEFAULT_MODULE_PIXELS)
        self.screen_modules.setText(DEFAULT_SCREEN_MODULES)
        self.screen_physical.clear()
        self.screen_pixels.clear()
        self.screen_boxes.setText(DEFAULT_SCREEN_CABINETS)
        self.receiver_combo.setCurrentText(DEFAULT_CABINET_MODEL)
        self.discount_combo.setCurrentIndex(0)
        self._reset_feature_actions()
        self.auto_checkbox.setChecked(True)
        self.screen_source = "modules"
        self.module_options = matching_modules(DEFAULT_PITCH_VALUE)
        self.module_index = 0
        self._show_module(self.module_options[0])
        self._set_mode(UnitMode.MODULE)
        self._mark_dirty()

    def _reset_feature_actions(self) -> None:
        actions = (
            self.backup_action,
            self.fiber_action,
            self.point_checkbox,
            self.async_checkbox,
            self.feature_3d_checkbox,
            self.hdr_checkbox,
        )
        for action in actions:
            action.setChecked(False)
