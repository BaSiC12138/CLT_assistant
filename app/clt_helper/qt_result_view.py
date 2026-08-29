from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .models import Configuration
from .result_presenter import ResultItem, ResultSectionData, build_result_sections

COMPACT_RESULT_COLUMNS = 1
RESULT_HIGHLIGHT_COLUMNS = 2
COPYABLE_TEXT_FLAGS = (
    Qt.TextInteractionFlag.TextSelectableByMouse
    | Qt.TextInteractionFlag.TextSelectableByKeyboard
)
SELECTION_BACKGROUND = QColor("#1769ef")
SELECTION_TEXT = QColor("#ffffff")
SECTION_OBJECT_NAMES = {
    "屏幕信息": "ResultSectionScreen",
    "接收卡设计": "ResultSectionReceiver",
    "网口带载设计": "ResultSectionNetwork",
}


def enable_text_copy(label: QLabel) -> None:
    label.setTextInteractionFlags(COPYABLE_TEXT_FLAGS)
    label.setCursor(Qt.CursorShape.IBeamCursor)
    palette = label.palette()
    palette.setColor(QPalette.ColorRole.Highlight, SELECTION_BACKGROUND)
    palette.setColor(QPalette.ColorRole.HighlightedText, SELECTION_TEXT)
    label.setPalette(palette)


class ResultView(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ResultScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("ResultContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(9, 6, 9, 8)
        self.content_layout.setSpacing(5)
        self.content_layout.addStretch(1)
        self.setWidget(self.content)

    def set_configuration(self, configuration: Configuration) -> None:
        self._clear_sections()
        screen, receiver, network, highlight = build_result_sections(configuration)
        self.content_layout.addWidget(_summary_row((screen, receiver, network)))
        self.content_layout.addWidget(_ResultSection(highlight))
        self.content_layout.addStretch(1)

    def _clear_sections(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class _ResultSection(QFrame):
    def __init__(self, section: ResultSectionData) -> None:
        super().__init__()
        object_name = (
            "ResultSectionHighlight"
            if section.emphasis
            else SECTION_OBJECT_NAMES[section.title]
        )
        self.setObjectName(object_name)
        vertical_policy = (
            QSizePolicy.Policy.Maximum
            if section.emphasis
            else QSizePolicy.Policy.Expanding
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, vertical_policy)
        layout = _section_layout(self, section.emphasis)
        title = _section_title(section.title, section.emphasis)
        layout.addWidget(title)
        layout.addLayout(_items_grid(section.items, section.emphasis), 1)
        for note in section.notes:
            layout.addWidget(_note_label(note))


def _section_layout(section: QFrame, emphasis: bool) -> QVBoxLayout | QHBoxLayout:
    if emphasis:
        layout = QVBoxLayout(section)
        layout.setContentsMargins(11, 7, 11, 8)
        layout.setSpacing(4)
        return layout
    layout = QVBoxLayout(section)
    layout.setContentsMargins(10, 8, 10, 9)
    layout.setSpacing(5)
    return layout


def _summary_row(sections: tuple[ResultSectionData, ...]) -> QWidget:
    row = QWidget()
    row.setObjectName("ResultSummaryRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(7)
    for section in sections:
        layout.addWidget(_ResultSection(section), 1)
    return row


def _section_title(title: str, emphasis: bool) -> QLabel:
    label = QLabel(title)
    label.setObjectName("ResultHighlightTitle" if emphasis else "ResultSectionTitle")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    enable_text_copy(label)
    return label


def _items_grid(items: tuple[ResultItem, ...], emphasis: bool) -> QGridLayout:
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(9)
    grid.setVerticalSpacing(3)
    columns = RESULT_HIGHLIGHT_COLUMNS if emphasis else COMPACT_RESULT_COLUMNS
    for index, item in enumerate(items):
        label = _item_label(item, emphasis)
        grid.addWidget(label, index // columns, index % columns)
    for column in range(columns):
        grid.setColumnStretch(column, 1)
    return grid


def _item_label(item: ResultItem, emphasis: bool) -> QLabel:
    label = QLabel(
        f"<span>{escape(item.label)}</span>&nbsp;&nbsp;<b>{escape(item.value)}</b>"
    )
    label.setObjectName("ResultHighlightItem" if emphasis else "ResultItem")
    label.setTextFormat(Qt.TextFormat.RichText)
    enable_text_copy(label)
    label.setWordWrap(True)
    return label


def _note_label(text: str) -> QLabel:
    label = QLabel(f"注意：{text}")
    label.setObjectName("ResultNote")
    enable_text_copy(label)
    label.setWordWrap(True)
    return label
