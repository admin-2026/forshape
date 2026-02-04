"""
Attachment widget for displaying pending file/image attachments as removable chips.
"""

import os

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class AttachmentChip(QWidget):
    """A single removable chip displaying an attachment filename."""

    remove_clicked = Signal(object)

    def __init__(self, attachment_data, chip_type, parent=None):
        """
        Args:
            attachment_data: The attachment dict (image result or file info)
            chip_type: "image" or "file"
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.attachment_data = attachment_data
        self.chip_type = chip_type

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        # Icon + filename
        if chip_type == "image":
            icon = "\U0001f4f7"
            filepath = attachment_data.get("file", "image")
            name = os.path.basename(filepath)
            bg_color = "#d4edda"
            border_color = "#a3d9a5"
        else:
            icon = "\U0001f4ce"
            name = attachment_data.get("name", "file")
            bg_color = "#d1ecf1"
            border_color = "#9ecfda"

        label = QLabel(f"{icon} {name}")
        layout.addWidget(label)

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet(
            "QPushButton { border: none; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { color: red; }"
        )
        close_btn.clicked.connect(lambda: self.remove_clicked.emit(self.attachment_data))
        layout.addWidget(close_btn)

        self.setStyleSheet(
            f"AttachmentChip {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; }}"
        )


class AttachmentWidget(QWidget):
    """Container widget that displays all pending attachments as removable chips."""

    attachment_removed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch()

        self.captured_images = []
        self.attached_files = []
        self.hide()

    def set_state_references(self, captured_images, attached_files):
        """Set references to the shared attachment lists."""
        self.captured_images = captured_images
        self.attached_files = attached_files

    def refresh(self):
        """Rebuild all chips from current list state. Auto-hides when empty."""
        # Remove existing chips (keep the stretch at the end)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add image chips
        for img_data in self.captured_images:
            chip = AttachmentChip(img_data, "image")
            chip.remove_clicked.connect(self._on_chip_removed)
            self._layout.insertWidget(self._layout.count() - 1, chip)

        # Add file chips
        for file_data in self.attached_files:
            chip = AttachmentChip(file_data, "file")
            chip.remove_clicked.connect(self._on_chip_removed)
            self._layout.insertWidget(self._layout.count() - 1, chip)

        # Auto-hide when empty
        has_items = len(self.captured_images) > 0 or len(self.attached_files) > 0
        self.setVisible(has_items)

    def _on_chip_removed(self, attachment_data):
        """Remove an attachment and refresh the display."""
        if attachment_data in self.captured_images:
            self.captured_images.remove(attachment_data)
            self.refresh()
            self.attachment_removed.emit("image", attachment_data)
        elif attachment_data in self.attached_files:
            self.attached_files.remove(attachment_data)
            self.refresh()
            self.attachment_removed.emit("file", attachment_data)
