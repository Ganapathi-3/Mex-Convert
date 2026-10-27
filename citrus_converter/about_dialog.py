"""
Citrus Converter — About Dialog
=================================
Shows application name, version, credits, and license information.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
)

ACCENT_COLOR = "#FF9500"
TEXT_SECONDARY = "#999999"


class AboutDialog(QDialog):
    """Simple 'About' dialog with app information and credits."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Citrus Converter")
        self.setFixedSize(380, 360)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # -- Icon (reuse the programmatic orange circle) ---------------------
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        size = 72
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(ACCENT_COLOR))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, size - 4, size - 4)
        p.setBrush(QColor("#4CAF50"))
        p.drawEllipse(size // 2 - 4, 4, 12, 8)
        p.end()
        icon_lbl.setPixmap(pix)
        layout.addWidget(icon_lbl)

        # -- App name -------------------------------------------------------
        name_lbl = QLabel("Citrus Converter")
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setFont(QFont("Sans", 18, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(name_lbl)

        # -- Version ---------------------------------------------------------
        ver_lbl = QLabel("Version 1.0.0")
        ver_lbl.setAlignment(Qt.AlignCenter)
        ver_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(ver_lbl)

        # -- Description -----------------------------------------------------
        desc_lbl = QLabel(
            "A fast, beautiful file converter for Linux.\n"
            "Drop any file and pick a target format."
        )
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 13px; margin: 8px 20px;")
        layout.addWidget(desc_lbl)

        # -- Credits ---------------------------------------------------------
        credits_lbl = QLabel(
            "<span style='color:#999;font-size:12px;'>"
            "Powered by "
            "<b>FFmpeg</b>, <b>ImageMagick</b>, <b>Pandoc</b>, <b>LibreOffice</b>"
            "</span>"
        )
        credits_lbl.setAlignment(Qt.AlignCenter)
        credits_lbl.setWordWrap(True)
        layout.addWidget(credits_lbl)

        # -- License ---------------------------------------------------------
        license_lbl = QLabel(
            "<a href='https://opensource.org/licenses/MIT' "
            "style='color:#FF9500; text-decoration:none;'>"
            "MIT License</a>"
        )
        license_lbl.setAlignment(Qt.AlignCenter)
        license_lbl.setOpenExternalLinks(True)
        layout.addWidget(license_lbl)

        # -- Close button ----------------------------------------------------
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
