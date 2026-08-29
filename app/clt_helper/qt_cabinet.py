from __future__ import annotations

from .cabinet_dimensions import dimensions_from_pixels
from .calculator import screen_from_modules
from .catalog import DEFAULT_CABINET_PIXELS, DEFAULT_MODULE_PIXELS
from .models import ModuleSpec, ScreenGeometry
from .parsing import parse_int_pair, parse_positive_float


MODULE_PIXELS_POSITION = (1, 0)
CABINET_PIXELS_POSITION = (0, 2)


class ApplicationCabinetMixin:
    def _dirty_entries(self) -> tuple:
        return self.size_entry, self.pixels_entry, self.screen_boxes

    def _update_cabinet_fields(
        self,
        enabled: bool,
        module: ModuleSpec | None,
    ) -> None:
        self.field_widgets["pixels"][0].setText("箱体点数" if enabled else "模组点数")
        placeholder = DEFAULT_CABINET_PIXELS if enabled else DEFAULT_MODULE_PIXELS
        self.pixels_entry.setPlaceholderText(placeholder.replace("x", "×"))
        self._place_pixels_field(CABINET_PIXELS_POSITION if enabled else MODULE_PIXELS_POSITION)
        self.size_entry.setReadOnly(self.auto_checkbox.isChecked() and not enabled)
        self.pixels_entry.setReadOnly(self.auto_checkbox.isChecked() and not enabled)
        if enabled:
            if module:
                self.pixels_entry.setText(DEFAULT_CABINET_PIXELS)
            return
        if self.auto_checkbox.isChecked() and self.module_options:
            module = self.module_options[self.module_index]
        if module:
            self._show_module(module)

    def _place_pixels_field(self, position: tuple[int, int]) -> None:
        row, column = position
        label, entry = self.field_widgets["pixels"]
        self.parameter_form_layout.addWidget(label, row, column)
        self.parameter_form_layout.addWidget(entry, row, column + 1)

    def _manual_cabinet_module(self, interface: str) -> ModuleSpec | None:
        pixels = parse_int_pair(self.pixels_entry.text())
        pitch = parse_positive_float(self.pitch_entry.text())
        if not pixels or not pitch:
            return None
        dimensions = dimensions_from_pixels(pitch, pixels)
        return ModuleSpec(
            pitch,
            dimensions.millimeters[0],
            dimensions.millimeters[1],
            pixels[0],
            pixels[1],
            interface,
        )

    def _manual_module_from_fields(self, interface: str) -> ModuleSpec | None:
        size = parse_int_pair(self.size_entry.text())
        pixels = parse_int_pair(self.pixels_entry.text())
        if not size or not pixels:
            return None
        pitch = parse_positive_float(self.pitch_entry.text()) or size[0] / pixels[0]
        return ModuleSpec(pitch, size[0], size[1], pixels[0], pixels[1], interface)

    def _cabinet_screen(self, module: ModuleSpec) -> ScreenGeometry | None:
        boxes = parse_int_pair(self.screen_boxes.text())
        return screen_from_modules(module, boxes) if boxes else None

    def _cabinet_options(self) -> tuple[str | None, tuple[int, int] | None]:
        if not self.cabinet_mode_button.isChecked():
            return None, None
        return self.receiver_combo.currentText(), (1, 1)
