from __future__ import annotations

from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget


class ApplicationSpecialModeMixin:
    def _build_parameter_mode_content(self, body: QVBoxLayout) -> None:
        self.parameter_form_widget = self._parameter_form()
        self.box_frame = self._box_options()
        self.feature_options_widget = self._feature_options()
        self.parameter_options_widget = self._parameter_options()
        self.parameter_actions_widget = self._parameter_actions()
        self._normal_parameter_widgets = (
            self.parameter_form_widget,
            self.feature_options_widget,
            self.parameter_options_widget,
            self.parameter_actions_widget,
        )
        body.addWidget(self.parameter_form_widget, 1)
        body.addWidget(self.box_frame)
        body.addWidget(self.feature_options_widget)
        body.addWidget(self.parameter_options_widget)
        body.addWidget(self.parameter_actions_widget)
        self.box_frame.hide()
        self.special_frame = self._blank_special_content()
        body.addWidget(self.special_frame, 1)
        self.special_frame.hide()

    @staticmethod
    def _blank_special_content() -> QFrame:
        frame = QFrame()
        frame.setObjectName("SpecialModeContent")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return frame

    def _set_standard_parameter_visibility(self, visible: bool) -> None:
        for widget in self._normal_parameter_widgets:
            widget.setVisible(visible)
