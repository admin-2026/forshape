"""
File selector dialog for choosing Python files to run.
"""

from PySide2.QtGui import QFont
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout


class PythonFileSelector(QDialog):
    """Dialog for selecting a Python file to run."""

    def __init__(self, python_files, parent=None):
        """
        Initialize the file selector dialog.

        Args:
            python_files: List of Python file paths
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_file = None
        self.setup_ui(python_files)

    def setup_ui(self, python_files):
        """Setup the dialog UI."""
        self.setWindowTitle("Select Python File to Run")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Add label
        label = QLabel("Select a Python file to run:")
        label.setFont(QFont("Consolas", 10))
        layout.addWidget(label)

        # Add list widget
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Consolas", 9))

        for file_path in python_files:
            item = QListWidgetItem(file_path)
            self.file_list.addItem(item)

        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_list)

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_item_double_clicked(self, item):
        """Handle double-click on a list item."""
        self.selected_file = item.text()
        self.accept()

    def on_ok_clicked(self):
        """Handle OK button click."""
        current_item = self.file_list.currentItem()
        if current_item:
            self.selected_file = current_item.text()
            self.accept()

    def get_selected_file(self):
        """Return the selected file path."""
        return self.selected_file
