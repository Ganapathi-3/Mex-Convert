"""
Elumichai — About Dialog
=================================
Shows application name, version, credits, and license information.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPixmap, QPainterPath, QPen
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
        self.setWindowTitle("About Elumichai")
        self.setFixedSize(380, 360)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # -- Lemon icon ------------------------------------------------------
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        size = 72
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        lemon = QPainterPath()
        lemon.moveTo(size * 0.16, size * 0.59)
        lemon.cubicTo(size * 0.12, size * 0.39, size * 0.28, size * 0.18, size * 0.47, size * 0.17)
        lemon.cubicTo(size * 0.67, size * 0.15, size * 0.84, size * 0.28, size * 0.83, size * 0.47)
        lemon.cubicTo(size * 0.82, size * 0.67, size * 0.60, size * 0.82, size * 0.39, size * 0.83)
        lemon.cubicTo(size * 0.25, size * 0.83, size * 0.17, size * 0.73, size * 0.16, size * 0.59)
        lemon.closeSubpath()
        p.setBrush(QColor("#F5D547"))
        p.setPen(QPen(QColor("#C59A16"), max(1, size // 24)))
        p.drawPath(lemon)
        p.setBrush(QColor("#FFF2A6"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(size * 0.25), int(size * 0.28), int(size * 0.16), int(size * 0.09))
        leaf = QPainterPath()
        leaf.moveTo(size * 0.45, size * 0.20)
        leaf.cubicTo(size * 0.50, size * 0.03, size * 0.72, size * 0.04, size * 0.68, size * 0.17)
        leaf.cubicTo(size * 0.61, size * 0.23, size * 0.52, size * 0.23, size * 0.45, size * 0.20)
        p.setBrush(QColor("#4E9F46"))
        p.drawPath(leaf)
        p.end()
        icon_lbl.setPixmap(pix)
        layout.addWidget(icon_lbl)

        # -- App name -------------------------------------------------------
        name_lbl = QLabel("Elumichai")
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
