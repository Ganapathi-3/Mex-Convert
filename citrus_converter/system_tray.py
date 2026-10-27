"""
Elumichai - System Tray Icon
=====================================
Provides a persistent system-tray presence with context menu and
notification support.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QApplication,
)


class SystemTray(QSystemTrayIcon):
    """Orange-circle system tray icon with context menu."""

    def __init__(self, icon: QIcon, main_window, parent=None) -> None:
        super().__init__(icon, parent)
        self._main_window = main_window

        # Context menu -------------------------------------------------------
        menu = QMenu()

        settings_act = QAction("Settings…", menu)
        settings_act.triggered.connect(self._open_settings)
        menu.addAction(settings_act)

        about_act = QAction("About", menu)
        about_act.triggered.connect(self._show_about)
        menu.addAction(about_act)

        menu.addSeparator()

        quit_act = QAction("Quit", menu)
        quit_act.triggered.connect(QApplication.quit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)

    # === slots ============================================================
    def _open_settings(self) -> None:
        from citrus_converter.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._main_window)
        dlg.exec()

    def _show_about(self) -> None:
        from citrus_converter.about_dialog import AboutDialog
        AboutDialog(self._main_window).exec()

    # === public helpers ===================================================
    def notify(self, title: str, message: str) -> None:
        """Show a tray balloon notification."""
        self.showMessage(title, message, QSystemTrayIcon.Information, 4000)
