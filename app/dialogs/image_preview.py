"""
Image preview and annotation dialog.
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QColor, QFont, QPixmap
from PySide2.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from ..widgets.drawable_label import DrawableImageLabel


class ImagePreviewDialog(QDialog):
    """Dialog for previewing captured screenshot before attaching."""

    def __init__(self, image_path, parent=None):
        """
        Initialize the image preview dialog.

        Args:
            image_path: Path to the image file to preview
            parent: Parent widget
        """
        super().__init__(parent)
        self.confirmed = False
        self.original_pixmap = None
        self.scroll_area = None
        self.image_label = None
        self.image_path = image_path
        self.setup_ui(image_path)

    def setup_ui(self, image_path):
        """Setup the dialog UI."""
        self.setWindowTitle("Preview & Annotate Screenshot")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Add title label
        title_label = QLabel("Preview and annotate screenshot:")
        title_label.setFont(QFont("Consolas", 10, QFont.Bold))
        layout.addWidget(title_label)

        # Add file path label
        file_label = QLabel(f"File: {image_path}")
        file_label.setFont(QFont("Consolas", 9))
        file_label.setWordWrap(True)
        layout.addWidget(file_label)

        # Create drawing tools toolbar
        tools_layout = QHBoxLayout()

        # Color selection
        color_label = QLabel("Pen Color:")
        color_label.setFont(QFont("Consolas", 9))
        tools_layout.addWidget(color_label)

        # Preset color buttons
        self.color_buttons = []
        preset_colors = [
            ("Red", QColor(255, 0, 0)),
            ("Green", QColor(0, 255, 0)),
            ("Blue", QColor(0, 0, 255)),
            ("Yellow", QColor(255, 255, 0)),
            ("White", QColor(255, 255, 255)),
            ("Black", QColor(0, 0, 0)),
        ]

        for name, color in preset_colors:
            btn = QPushButton(name)
            btn.setFixedSize(60, 25)
            btn.setStyleSheet(
                f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'};"
            )
            btn.clicked.connect(lambda checked, c=color: self.set_pen_color(c))
            tools_layout.addWidget(btn)
            self.color_buttons.append(btn)

        # Custom color button
        custom_color_btn = QPushButton("Custom...")
        custom_color_btn.setFixedSize(70, 25)
        custom_color_btn.clicked.connect(self.choose_custom_color)
        tools_layout.addWidget(custom_color_btn)

        tools_layout.addSpacing(20)

        # Pen width selection
        width_label = QLabel("Pen Width:")
        width_label.setFont(QFont("Consolas", 9))
        tools_layout.addWidget(width_label)

        self.width_combo = QComboBox()
        self.width_combo.addItems(["1", "2", "3", "5", "8", "10", "15"])
        self.width_combo.setCurrentText("3")
        self.width_combo.currentTextChanged.connect(self.on_width_changed)
        tools_layout.addWidget(self.width_combo)

        tools_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("Clear Drawings")
        clear_btn.clicked.connect(self.clear_drawings)
        tools_layout.addWidget(clear_btn)

        layout.addLayout(tools_layout)

        # Create scroll area for the image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        # Create drawable image label
        self.image_label = DrawableImageLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # Load the original image
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            error_label = QLabel("Error: Could not load image")
            error_label.setStyleSheet("color: red;")
            self.scroll_area.setWidget(error_label)
        else:
            # Initial scaling will happen in showEvent
            pass

        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area, stretch=1)

        # Add instruction label
        instruction_label = QLabel(
            "Draw on the image to highlight areas or add annotations.\n"
            "Use the tools above to change pen color and width. Click 'Confirm' to attach, or 'Cancel' to discard."
        )
        instruction_label.setFont(QFont("Consolas", 9))
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Confirm")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancel")
        button_box.accepted.connect(self.on_confirm)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def showEvent(self, event):
        """Handle dialog show event - scale image to fit."""
        super().showEvent(event)
        self.scale_image_to_fit()

    def resizeEvent(self, event):
        """Handle dialog resize event - rescale image to fit new size."""
        super().resizeEvent(event)
        # Note: Resizing disabled for drawable images to maintain drawing accuracy
        # self.scale_image_to_fit()

    def scale_image_to_fit(self):
        """Scale the image to fit the available scroll area size."""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return

        # Get available size (scroll area size minus margins)
        available_size = self.scroll_area.size()
        # Account for scrollbar space and margins
        target_width = available_size.width() - 40
        target_height = available_size.height() - 40

        # Scale pixmap to fit while maintaining aspect ratio
        scaled_pixmap = self.original_pixmap.scaled(
            target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Set the scaled image to the drawable label
        self.image_label.set_image(scaled_pixmap)
        self.image_label.adjustSize()

    def set_pen_color(self, color):
        """Set the pen color for drawing."""
        self.image_label.set_pen_color(color)

    def choose_custom_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.image_label.set_pen_color(color)

    def on_width_changed(self, width_text):
        """Handle pen width change."""
        try:
            width = int(width_text)
            self.image_label.set_pen_width(width)
        except ValueError:
            pass

    def clear_drawings(self):
        """Clear all drawings from the image."""
        self.image_label.clear_drawings()

    def on_confirm(self):
        """Handle confirm button click - save annotated image."""
        self.confirmed = True

        # Get the annotated image
        annotated_pixmap = self.image_label.get_annotated_image()
        if annotated_pixmap:
            # Save the annotated image to the same path (overwrite)
            annotated_pixmap.save(self.image_path)

        self.accept()

    def is_confirmed(self):
        """Return whether the user confirmed the image."""
        return self.confirmed
