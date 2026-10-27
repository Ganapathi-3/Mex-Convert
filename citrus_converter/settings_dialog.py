"""
Citrus Converter — Settings Dialog
====================================
Allows the user to configure output location, theme, notifications,
and inspect which CLI conversion tools are installed.
"""

from __future__ import annotations

import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QCheckBox,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QDialogButtonBox,
    QWidget,
    QGridLayout,
)

# Colour tokens
ACCENT_COLOR = "#FF9500"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#f44336"
TEXT_SECONDARY = "#999999"

# CLI tools the app can leverage
_TOOLS = [
    ("ffmpeg", "Video / audio conversion"),
    ("convert", "ImageMagick — image conversion"),
    ("pandoc", "Document conversion"),
    ("libreoffice", "Office document conversion"),
    ("gs", "Ghostscript — PDF tools"),
]


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(440, 520)

        # Load current settings
        try:
            from citrus_converter.config import Config
            self._config = Config()
        except Exception:
            self._config = None

        self._build_ui()
        self._load_values()

    # === UI construction ==================================================
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)

        # -- Output location -------------------------------------------------
        out_group = QGroupBox("Output Location")
        out_lay = QVBoxLayout(out_group)

        self._out_combo = QComboBox()
        self._out_combo.addItems(["Same folder as input", "Custom folder", "Ask each time"])
        self._out_combo.currentIndexChanged.connect(self._on_output_mode_changed)
        out_lay.addWidget(self._out_combo)

        browse_row = QHBoxLayout()
        self._out_path = QLineEdit()
        self._out_path.setPlaceholderText("/path/to/output")
        self._out_path.setEnabled(False)
        browse_row.addWidget(self._out_path)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setFixedWidth(90)
        self._browse_btn.setEnabled(False)
        self._browse_btn.clicked.connect(self._browse_output)
        browse_row.addWidget(self._browse_btn)

        out_lay.addLayout(browse_row)
        root.addWidget(out_group)

        # -- Appearance ------------------------------------------------------
        appear_group = QGroupBox("Appearance")
        appear_lay = QFormLayout(appear_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light", "System"])
        appear_lay.addRow("Theme:", self._theme_combo)

        root.addWidget(appear_group)

        # -- Behaviour -------------------------------------------------------
        behave_group = QGroupBox("Behaviour")
        behave_lay = QVBoxLayout(behave_group)

        self._notify_cb = QCheckBox("Show desktop notifications on completion")
        self._notify_cb.setChecked(True)
        behave_lay.addWidget(self._notify_cb)

        self._background_cb = QCheckBox("Start in the background (tray only)")
        self._background_cb.setChecked(True)
        behave_lay.addWidget(self._background_cb)

        self._sound_cb = QCheckBox("Play a sound while navigating the wheel")
        self._sound_cb.setChecked(True)
        behave_lay.addWidget(self._sound_cb)

        self._overwrite_cb = QCheckBox("Confirm before overwriting files")
        self._overwrite_cb.setChecked(True)
        behave_lay.addWidget(self._overwrite_cb)

        root.addWidget(behave_group)

        # -- Installed tools -------------------------------------------------
        tools_group = QGroupBox("Installed Tools")
        tools_lay = QGridLayout(tools_group)
        tools_lay.setColumnStretch(1, 1)

        for row, (cmd, desc) in enumerate(_TOOLS):
            found = shutil.which(cmd) is not None
            indicator = QLabel("●")
            indicator.setStyleSheet(
                f"color: {SUCCESS_COLOR};" if found else f"color: {ERROR_COLOR};"
            )
            indicator.setFixedWidth(18)
            indicator.setAlignment(Qt.AlignCenter)

            name_lbl = QLabel(f"<b>{cmd}</b>")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

            status_lbl = QLabel("found" if found else "not found")
            status_lbl.setStyleSheet(
                f"color: {SUCCESS_COLOR}; font-size: 11px;"
                if found
                else f"color: {ERROR_COLOR}; font-size: 11px;"
            )

            tools_lay.addWidget(indicator, row, 0)
            tools_lay.addWidget(name_lbl, row, 1)
            tools_lay.addWidget(desc_lbl, row, 2)
            tools_lay.addWidget(status_lbl, row, 3)

        root.addWidget(tools_group)

        # -- Buttons ---------------------------------------------------------
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._save_and_accept)
        btn_box.rejected.connect(self.reject)
        root.addWidget(btn_box)

    # === value helpers ====================================================
    def _load_values(self) -> None:
        if self._config is None:
            return
        try:
            mode = self._config.get("output_location", "same")
            mode_map = {"same": 0, "custom": 1, "ask": 2}
            self._out_combo.setCurrentIndex(mode_map.get(mode, 0))

            self._out_path.setText(self._config.get("output_custom_path", ""))

            theme = self._config.get("theme", "dark").capitalize()
            idx = self._theme_combo.findText(theme)
            if idx >= 0:
                self._theme_combo.setCurrentIndex(idx)

            self._notify_cb.setChecked(self._config.get("notifications", True))
            self._overwrite_cb.setChecked(self._config.get("confirm_overwrite", True))
            self._background_cb.setChecked(self._config.get("start_in_background", True))
            self._sound_cb.setChecked(self._config.get("navigation_sound", True))
        except Exception:
            pass

    def _save_and_accept(self) -> None:
        if self._config is not None:
            try:
                mode_map = {0: "same", 1: "custom", 2: "ask"}
                self._config.set("output_location", mode_map.get(self._out_combo.currentIndex(), "same"))
                self._config.set("output_custom_path", self._out_path.text())
                self._config.set("theme", self._theme_combo.currentText().lower())
                self._config.set("notifications", self._notify_cb.isChecked())
                self._config.set("confirm_overwrite", self._overwrite_cb.isChecked())
                self._config.set("start_in_background", self._background_cb.isChecked())
                self._config.set("navigation_sound", self._sound_cb.isChecked())
                self._config.save()
            except Exception:
                pass
        self.accept()

    # === slots ============================================================
    def _on_output_mode_changed(self, index: int) -> None:
        custom = index == 1
        self._out_path.setEnabled(custom)
        self._browse_btn.setEnabled(custom)

    def _browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._out_path.setText(folder)
