# File: AboutDialog.py
# Path: Source/Utils/AboutDialog.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  08:00PM
"""
Description: About Dialog for Anderson's Library.
Displays application information and branding.
"""

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtGui import QPixmap, QFont, QCursor
from PySide6.QtCore import Qt, QEvent, QPoint
from pathlib import Path
import logging


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Logger = logging.getLogger(self.__class__.__name__)

        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self.setStyleSheet("background-color: #780000;")

        self.label = QLabel(
            "Another Intuitive Product\nfrom the folks at\nBowersWorld.com"
        )
        self.label.setStyleSheet("color: #ffd200; font: bold 24px; text-align: center;")
        self.label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(str(Path(__file__).parent.parent.parent / "Assets" / "BowersWorld.png"))
        if pixmap.isNull():
            self.Logger.warning(f"Failed to load BowersWorld.png from {Path(__file__).parent.parent.parent / 'Assets' / 'BowersWorld.png'}")
        pixmap = pixmap.scaled(170, 170, Qt.KeepAspectRatio)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(pixmap)

        self.copyright_label = QLabel("\u00A9")
        self.copyright_label.setContentsMargins(0, 160, 0, 0)
        self.copyright_label.setStyleSheet(
            "color: #ffd200; font: bold 24px; text-align: center;"
        )

        self.icon_layout = QHBoxLayout()
        self.icon_layout.addWidget(QLabel("   "))
        self.icon_layout.addWidget(self.icon_label)
        self.icon_layout.addWidget(self.copyright_label)

        self.icon_layout.insertStretch(0, 1)
        self.icon_layout.insertStretch(4, 1)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.layout)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.icon_layout)

    def showEvent(self, event):
        if self.parent() is not None:
            parent_rect = self.parent().frameGeometry()
            self.move(parent_rect.center() - self.rect().center())
        super().showEvent(event)
