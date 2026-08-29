from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker

from .catalog import matching_modules
from .models import ModuleSpec, UnitMode
from .parsing import parse_positive_float


@dataclass(frozen=True, kw_only=True)
class ModeInputState:
    pitch: str
    size: str
    pixels: str
    screen_modules: str
    screen_physical: str
    screen_pixels: str
    screen_source: str
    auto_match: bool
    module_index: int
    module_status: str


class ApplicationModeStateMixin:
    def _reset_mode_states(self) -> None:
        self._mode_input_states: dict[UnitMode, ModeInputState] = {}
        self._active_mode: UnitMode | None = None
        self._last_standard_mode = UnitMode.MODULE

    def _set_mode(self, mode: UnitMode) -> None:
        previous = getattr(self, "_active_mode", None)
        if previous is mode:
            return
        transition_module = self._transition_module(previous)
        if previous is not None and previous is not UnitMode.SPECIAL:
            previous_state = self._capture_mode_state()
            self._mode_input_states = {
                **self._mode_input_states,
                previous: previous_state,
            }
        self._apply_mode_visibility(mode)
        if mode is UnitMode.SPECIAL:
            self._active_mode = mode
            self._mark_dirty()
            return
        box_mode = mode is UnitMode.CABINET
        state = self._mode_input_states.get(mode)
        self._update_cabinet_fields(box_mode, None if state else transition_module)
        if state:
            self._restore_mode_state(mode, state)
        self._active_mode = mode
        self._last_standard_mode = mode
        self._mark_dirty()

    def _transition_module(self, previous: UnitMode | None) -> ModuleSpec | None:
        if previous is UnitMode.SPECIAL:
            previous = self._last_standard_mode
        if previous is None:
            return self._selected_catalog_module()
        if previous is UnitMode.MODULE and self.auto_checkbox.isChecked():
            return self._selected_catalog_module()
        interface = self._transition_interface()
        if previous is UnitMode.MODULE:
            return self._manual_module_from_fields(interface)
        return self._manual_cabinet_module(interface)

    def _selected_catalog_module(self) -> ModuleSpec | None:
        if not self.module_options:
            return None
        return self.module_options[self.module_index]

    def _transition_interface(self) -> str:
        if self.auto_checkbox.isChecked():
            module = self._selected_catalog_module()
            if module:
                return module.interface
        return "320接口" if self.interface_320_action.isChecked() else "75接口"

    def _apply_mode_visibility(self, mode: UnitMode) -> None:
        special_mode = mode is UnitMode.SPECIAL
        box_mode = mode is UnitMode.CABINET
        self._set_standard_parameter_visibility(not special_mode)
        self.special_frame.setVisible(special_mode)
        self.box_frame.setVisible(box_mode)
        for name in ("size", "modules", "physical", "resolution"):
            for widget in self.field_widgets[name]:
                widget.setVisible(not box_mode)
        self.module_mode_button.setChecked(mode is UnitMode.MODULE)
        self.cabinet_mode_button.setChecked(box_mode)
        self.special_mode_button.setChecked(special_mode)
        module_mode = mode is UnitMode.MODULE
        self.discount_label.setVisible(module_mode)
        self.discount_combo.setVisible(module_mode)
        self.discount_combo.setEnabled(module_mode)
        self.module_status.setVisible(module_mode)
        self._update_parameter_row_stretch(box_mode)

    def _capture_mode_state(self) -> ModeInputState:
        return ModeInputState(
            pitch=self.pitch_entry.text(),
            size=self.size_entry.text(),
            pixels=self.pixels_entry.text(),
            screen_modules=self.screen_modules.text(),
            screen_physical=self.screen_physical.text(),
            screen_pixels=self.screen_pixels.text(),
            screen_source=self.screen_source,
            auto_match=self.auto_checkbox.isChecked(),
            module_index=self.module_index,
            module_status=self.module_status.text(),
        )

    def _restore_mode_state(self, mode: UnitMode, state: ModeInputState) -> None:
        widgets = self._mode_state_widgets()
        blockers = tuple(QSignalBlocker(widget) for widget in widgets)
        try:
            self._set_mode_widget_values(state)
        finally:
            del blockers
        pitch = parse_positive_float(state.pitch)
        self.module_options = matching_modules(pitch) if pitch else ()
        last_index = max(0, len(self.module_options) - 1)
        self.module_index = min(state.module_index, last_index)
        self.screen_source = state.screen_source
        box_mode = mode is UnitMode.CABINET
        read_only = state.auto_match and not box_mode
        self.size_entry.setReadOnly(read_only)
        self.pixels_entry.setReadOnly(read_only)

    def _mode_state_widgets(self) -> tuple:
        return (
            self.pitch_entry,
            self.size_entry,
            self.pixels_entry,
            self.screen_modules,
            self.screen_physical,
            self.screen_pixels,
            self.auto_checkbox,
        )

    def _set_mode_widget_values(self, state: ModeInputState) -> None:
        self.pitch_entry.setText(state.pitch)
        self.size_entry.setText(state.size)
        self.pixels_entry.setText(state.pixels)
        self.screen_modules.setText(state.screen_modules)
        self.screen_physical.setText(state.screen_physical)
        self.screen_pixels.setText(state.screen_pixels)
        self.auto_checkbox.setChecked(state.auto_match)
        self.module_status.setText(state.module_status)
