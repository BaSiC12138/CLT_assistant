from __future__ import annotations

from functools import partial

from .models import ScreenGeometry
from .parsing import format_number


class ApplicationModuleSyncMixin:
    def _connect_module_screen_signals(self) -> None:
        for source, entry in self._screen_entries().items():
            entry.textEdited.connect(partial(self._on_module_screen_edited, source))
        self.size_entry.textEdited.connect(self._on_module_spec_edited)
        self.pixels_entry.textEdited.connect(self._on_module_spec_edited)

    def _on_module_screen_edited(self, source: str, _text: str) -> None:
        if self.cabinet_mode_button.isChecked():
            return
        self._set_screen_source(source)
        self._refresh_module_screen_fields()

    def _on_module_spec_edited(self, _text: str) -> None:
        self._refresh_module_screen_fields()

    def _refresh_module_screen_fields(self) -> None:
        if self.cabinet_mode_button.isChecked():
            return
        module = self._current_module()
        screen = self._current_screen(module) if module else None
        if not screen:
            self._clear_screen_derivatives()
            return
        self._show_derived_screen(screen)

    def _show_derived_screen(self, screen: ScreenGeometry) -> None:
        if self.cabinet_mode_button.isChecked():
            return
        values = {
            "modules": f"{screen.modules_w}×{screen.modules_h}",
            "physical": (
                f"{format_number(screen.width_m)}×{format_number(screen.height_m)}"
            ),
            "pixels": f"{screen.pixels_w}×{screen.pixels_h}",
        }
        for name, entry in self._screen_entries().items():
            if name != self.screen_source:
                entry.setText(values[name])

    def _clear_screen_derivatives(self) -> None:
        for name, entry in self._screen_entries().items():
            if name != self.screen_source:
                entry.clear()

    def _screen_entries(self) -> dict:
        return {
            "modules": self.screen_modules,
            "physical": self.screen_physical,
            "pixels": self.screen_pixels,
        }
