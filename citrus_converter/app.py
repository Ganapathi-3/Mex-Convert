"""
Citrus Converter — Main Application
====================================
Subclasses QApplication to manage the app lifecycle, system tray, theming,
and command-line argument handling.
"""

import sys

from PySide6.QtCore import Qt, QLockFile
from PySide6.QtGui import QIcon, QPainter, QPixmap, QColor
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Colour constants shared across every module
# ---------------------------------------------------------------------------
ACCENT_COLOR = "#FF9500"        # Orange
BG_DARK = "#1e1e1e"             # Dark background
BG_CARD = "#2d2d2d"             # Card / panel background
TEXT_PRIMARY = "#ffffff"         # White text
TEXT_SECONDARY = "#999999"      # Grey text
SUCCESS_COLOR = "#4CAF50"       # Green
ERROR_COLOR = "#f44336"         # Red

# ---------------------------------------------------------------------------
# Global dark stylesheet
# ---------------------------------------------------------------------------
DARK_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
}}
QMenuBar {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid #3d3d3d;
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {ACCENT_COLOR};
    border-radius: 4px;
}}
QMenu {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #3d3d3d;
    padding: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT_COLOR};
    border-radius: 4px;
}}
QMenu::separator {{
    height: 1px;
    background: #3d3d3d;
    margin: 4px 8px;
}}
QStatusBar {{
    background-color: {BG_CARD};
    color: {TEXT_SECONDARY};
    border-top: 1px solid #3d3d3d;
    font-size: 12px;
}}
QPushButton {{
    background-color: {ACCENT_COLOR};
    color: {TEXT_PRIMARY};
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: #FFa830;
}}
QPushButton:pressed {{
    background-color: #e08600;
}}
QLabel {{
    color: {TEXT_PRIMARY};
}}
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid #555;
    border-radius: 4px;
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_COLOR};
    border-color: {ACCENT_COLOR};
}}
QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_COLOR};
}}
QLineEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 10px;
}}
QGroupBox {{
    color: {ACCENT_COLOR};
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f5f5f5;
    color: #222;
}
QMenuBar {
    background-color: #fff;
    color: #222;
    border-bottom: 1px solid #ddd;
}
QMenuBar::item:selected {
    background-color: #FF9500;
    color: #fff;
    border-radius: 4px;
}
QMenu {
    background-color: #fff;
    color: #222;
    border: 1px solid #ddd;
}
QMenu::item:selected {
    background-color: #FF9500;
    color: #fff;
    border-radius: 4px;
}
QStatusBar {
    background-color: #fff;
    color: #888;
    border-top: 1px solid #ddd;
}
QPushButton {
    background-color: #FF9500;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #FFa830; }
QPushButton:pressed { background-color: #e08600; }
QLabel { color: #222; }
QCheckBox { color: #222; }
QComboBox {
    background-color: #fff;
    color: #222;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 6px 12px;
}
QLineEdit {
    background-color: #fff;
    color: #222;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 6px 10px;
}
QGroupBox {
    color: #FF9500;
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""


def _make_app_icon(size: int = 64) -> QIcon:
    """Generate a simple orange-circle app icon programmatically."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(ACCENT_COLOR))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    # Small leaf-like accent
    painter.setBrush(QColor("#4CAF50"))
    painter.drawEllipse(size // 2 - 4, 4, 12, 8)
    painter.end()
    return QIcon(pix)


class CitrusApp(QApplication):
    """Main application object for Citrus Converter."""

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self._already_running = False
        self._single_instance_lock = None
        self._acquire_single_instance()
        if self._already_running:
            return

        self.setApplicationName("Citrus Converter")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("CitrusProject")
        self.setQuitOnLastWindowClosed(False)

        # Determine run-mode ------------------------------------------------
        self._cli_mode = "--cli" in argv

        # Theme --------------------------------------------------------------
        try:
            from citrus_converter.config import Config
            self._config = Config()
            theme = self._config.get("theme", "dark")
        except Exception:
            self._config = None
            theme = "dark"

        self.apply_theme(theme)
        self.setWindowIcon(_make_app_icon())

        if not self._cli_mode:
            from citrus_converter.main_window import MainWindow
            from citrus_converter.system_tray import SystemTray

            # Main window
            self.main_window = MainWindow()

            # System tray
            self.tray = SystemTray(_make_app_icon(), self.main_window)
            self.tray.show()
            from citrus_converter.global_drag import GlobalDragMonitor
            self.global_drag = GlobalDragMonitor(self.main_window.radial_menu, self)
            self.aboutToQuit.connect(self.tray.hide)
            self.aboutToQuit.connect(self.global_drag.stop)
            self.aboutToQuit.connect(self._release_single_instance)

            # Citrus is a background utility: launching it should not put a
            # small converter window in front of the user's work.  A supplied
            # file path is the explicit exception and opens the wheel at once.
            file_args = [arg for arg in argv[1:] if not arg.startswith("-") and arg != "--drop-target"]
            if file_args:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self.main_window.present_files(file_args))

    def _acquire_single_instance(self) -> None:
        """Prevent duplicate tray icons from repeated autostart launches."""
        from pathlib import Path
        lock_path = Path.home() / ".config" / "citrus-converter" / "instance.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(lock_path))
        lock.setStaleLockTime(30000)
        if not lock.tryLock(100):
            self._already_running = True
            return
        self._single_instance_lock = lock

    def _release_single_instance(self) -> None:
        if self._single_instance_lock is not None:
            self._single_instance_lock.unlock()
            self._single_instance_lock = None

    # ------------------------------------------------------------------
    def apply_theme(self, theme: str) -> None:
        """Apply the given theme stylesheet ('dark', 'light', or 'system')."""
        if theme == "light":
            self.setStyleSheet(LIGHT_STYLESHEET)
        else:
            # 'dark' or 'system' both default to dark for now
            self.setStyleSheet(DARK_STYLESHEET)

    # ------------------------------------------------------------------
    @staticmethod
    def run() -> int:
        """Convenience entry-point: create the app and exec."""
        app = CitrusApp(sys.argv)
        if app._cli_mode:
            # In CLI mode the GUI is not started; other code drives conversion.
            return 0
        return app.exec()
