from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent

PixelScaler = Callable[[int], int]
FONT_FAMILY = "Microsoft YaHei"
FONT_COMPACT_RESULT_PT = 7
FONT_TINY_PT = 8
FONT_SMALL_PT = 9
FONT_LABEL_PT = 10
FONT_RESULT_PT = 10
FONT_BODY_PT = 11
FONT_SECTION_PT = 12
FONT_TITLE_PT = 15
MUTED_TEXT_COLOR = "#52617a"


class ApplicationStyleMixin:
    def resizeEvent(self, event: QEvent) -> None:
        super().resizeEvent(event)
        scale = max(0.88, min(1.35, min(self.width() / 1440, self.height() / 810)))
        if abs(scale - self._last_scale) >= 0.02:
            self._last_scale = scale
            self._apply_scale(scale)

    def _apply_scale(self, scale: float) -> None:
        px = lambda value: max(1, round(value * scale))
        self.brand_mark.setFixedSize(px(38), px(38))
        self.setStyleSheet(application_stylesheet(px))


def application_stylesheet(px: PixelScaler) -> str:
    return "".join(
        (
            _window_styles(px),
            _panel_styles(px),
            _field_styles(px),
            _button_styles(px),
            _result_styles(px),
            _footer_styles(px),
        )
    )


def _window_styles(px: PixelScaler) -> str:
    return f"""
        QMainWindow, QWidget#Central, QWidget#Workspace {{ background:#e9eef7; color:#253047; }}
        QFrame#Header {{ min-height:{px(58)}px; max-height:{px(58)}px;
            background:#fbfdff; border-bottom:{px(1)}px solid #ccd9ec; }}
        QLabel#AppTitle {{ color:#1f2b42; font:{px(FONT_TITLE_PT)}pt '{FONT_FAMILY}'; font-weight:600; }}
        QLabel#VersionBadge {{ color:#1769ef; background:#e6efff; border-radius:{px(7)}px;
            padding:{px(4)}px {px(10)}px; font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#StatusChip {{ color:#52617a; background:#eef4fc; border:{px(1)}px solid #d9e5f5;
            border-radius:{px(7)}px; min-width:{px(235)}px; padding:{px(7)}px {px(12)}px;
            font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; }}
        QToolButton#SettingsButton {{ color:#253047; background:#ffffff;
            border:{px(1)}px solid #d5dfef; border-radius:{px(7)}px;
            padding:{px(8)}px {px(14)}px; font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}'; }}
        QToolButton#SettingsButton:hover {{ background:#edf3fb; }}
        QToolButton#WindowMinimizeButton, QToolButton#WindowMaximizeButton,
        QToolButton#WindowCloseButton {{ background:transparent; border:none; border-radius:0;
            min-width:{px(48)}px; max-width:{px(48)}px; min-height:{px(56)}px; max-height:{px(56)}px;
            padding:0; }}
        QToolButton#WindowMinimizeButton:hover, QToolButton#WindowMaximizeButton:hover {{
            background:#e8eef7; }}
        QToolButton#WindowCloseButton:hover {{ background:#e5484d; }}
    """


def _panel_styles(px: PixelScaler) -> str:
    return f"""
        QFrame#Panel {{ background:#f8fbff; border:{px(1)}px solid #ffffff;
            border-radius:{px(14)}px; }}
        QFrame#PanelHeader {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f5f9ff,stop:1 #e3edfb);
            border-radius:{px(11)}px; min-height:{px(40)}px; }}
        QFrame#AccentBar {{ min-height:{px(27)}px; max-height:{px(27)}px;
            border-radius:{px(2)}px; }}
        QLabel#Kicker {{ color:{MUTED_TEXT_COLOR}; font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#PanelTitle {{ color:#1f2b42; font:{px(FONT_SECTION_PT)}pt '{FONT_FAMILY}';
            font-weight:600; }}
    """


def _field_styles(px: PixelScaler) -> str:
    return f"""
        QLabel#FieldLabel, QLabel#MutedText {{ color:{MUTED_TEXT_COLOR};
            font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}'; font-weight:500; }}
        QLineEdit, QComboBox {{ min-height:{px(32)}px; color:#253047; background:#ffffff;
            border:{px(1)}px solid #d5dfef; border-radius:{px(8)}px; padding:0 {px(9)}px;
            font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}'; }}
        QLineEdit:read-only {{ background:#f0f5fb; color:#50617d; }}
        QFrame#BoxOptions {{ background:transparent; border:none; }}
        QCheckBox {{ color:#253047; font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}';
            spacing:{px(7)}px; }}
        QCheckBox::indicator {{ width:{px(17)}px; height:{px(17)}px; }}
    """


def _button_styles(px: PixelScaler) -> str:
    return f"""
        QPushButton#ModeButton {{ color:#253047; background:#e5edf8; border:none;
            border-radius:{px(8)}px; min-height:{px(36)}px; padding:0 {px(14)}px;
            font:{px(FONT_SECTION_PT)}pt '{FONT_FAMILY}'; font-weight:600; }}
        QPushButton#ModeButton:checked {{ color:white; background:#1769ef; }}
        QPushButton#SecondaryButton {{ color:#253047; background:#e8eef8; border:none;
            border-radius:{px(8)}px; min-height:{px(31)}px; padding:0 {px(11)}px;
            font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}'; }}
        QPushButton#PlainTextCopyButton {{ color:#1769ef; background:#edf4ff;
            border:{px(1)}px solid #bcd5f7; border-radius:{px(8)}px;
            min-height:{px(29)}px; padding:0 {px(10)}px;
            font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; font-weight:600; }}
        QPushButton#PlainTextCopyButton:hover {{ color:#ffffff; background:#1769ef; }}
        QPushButton#PrimaryButton {{ color:white;
            background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3180ff,stop:1 #1769ef);
            border:none; border-radius:{px(10)}px; min-height:{px(40)}px;
            padding:0 {px(16)}px; font:{px(FONT_BODY_PT)}pt '{FONT_FAMILY}'; font-weight:600; }}
        QPushButton#PrimaryButton:hover {{ background:#0f56cf; }}
    """


def _result_styles(px: PixelScaler) -> str:
    return f"""
        QLabel#SuccessBadge {{ color:#10a35e; background:#e4f7ee; border-radius:{px(8)}px;
            padding:{px(5)}px {px(10)}px; font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#DiagramStatus {{ color:#10a35e; font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}'; }}
        QScrollArea#ResultScroll, QScrollArea#ResultScroll QWidget#qt_scrollarea_viewport,
        QWidget#ResultContent {{ background:transparent; border:none; }}
        QWidget#ResultSummaryRow {{ background:transparent; border:none; }}
        QFrame#ResultSectionScreen {{
            background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #edf5ff);
            border:{px(1)}px solid #bcd5f7; border-radius:{px(8)}px; min-height:{px(116)}px; }}
        QFrame#ResultSectionReceiver {{
            background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #edf9f3);
            border:{px(1)}px solid #b8e2cf; border-radius:{px(8)}px; min-height:{px(116)}px; }}
        QFrame#ResultSectionNetwork {{
            background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #fff5e9);
            border:{px(1)}px solid #f0d0aa; border-radius:{px(8)}px; min-height:{px(116)}px; }}
        QFrame#ResultSectionHighlight {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f8fbff,stop:1 #d8e9ff);
            border:{px(2)}px solid #4b8de8; border-radius:{px(8)}px; }}
        QLabel#ResultSectionTitle {{ font:{px(FONT_SMALL_PT)}pt '{FONT_FAMILY}';
            font-weight:700; }}
        QFrame#ResultSectionScreen QLabel#ResultSectionTitle {{ color:#1769ef; }}
        QFrame#ResultSectionReceiver QLabel#ResultSectionTitle {{ color:#10a35e; }}
        QFrame#ResultSectionNetwork QLabel#ResultSectionTitle {{ color:#f08a32; }}
        QLabel#ResultItem {{ color:#40516b; font:{px(FONT_COMPACT_RESULT_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#ResultHighlightTitle {{ color:#0b56b3; font:{px(FONT_BODY_PT)}pt '{FONT_FAMILY}';
            font-weight:700; }}
        QLabel#ResultHighlightItem {{ color:#1f3d63; font:{px(FONT_RESULT_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#ResultNote {{ color:#4e6380; font:{px(FONT_TINY_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#DiagramSummary {{ color:{MUTED_TEXT_COLOR}; background:#eaf1fb; border-radius:{px(9)}px;
            padding:{px(8)}px {px(12)}px; margin:{px(9)}px {px(14)}px 0 {px(14)}px;
            font:{px(FONT_LABEL_PT)}pt '{FONT_FAMILY}'; }}
        QFrame#DiagramSurface {{ background:#ffffff; border:{px(1)}px solid #efaaaa;
            border-radius:{px(12)}px; margin:{px(9)}px {px(14)}px {px(14)}px {px(14)}px; }}
    """


def _footer_styles(px: PixelScaler) -> str:
    return f"""
        QFrame#Footer {{ min-height:{px(27)}px; max-height:{px(27)}px; background:#f8fbff; }}
        QLabel#FooterStatus {{ color:#10a35e; font:{px(FONT_TINY_PT)}pt '{FONT_FAMILY}'; }}
        QLabel#FooterText {{ color:{MUTED_TEXT_COLOR}; font:{px(FONT_TINY_PT)}pt '{FONT_FAMILY}'; }}
    """
