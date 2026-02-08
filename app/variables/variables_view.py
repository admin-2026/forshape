"""Variables view widget for displaying variables."""

import glob
import os

from PySide2.QtCore import QFileSystemWatcher, QThread, Signal
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .constants_parser import ConstantsParser


class _ParseWorker(QThread):
    """Worker thread for parsing constants files."""

    finished = Signal(list, list)  # (all_variables, source_names)
    error = Signal(str)

    def __init__(self, working_dir, constants_files):
        super().__init__()
        self.working_dir = working_dir
        self.constants_files = constants_files

    def run(self):
        try:
            all_variables = []
            base_namespace = {}
            base_constants_path = os.path.join(self.working_dir, "constants.py")

            if os.path.exists(base_constants_path):
                with open(base_constants_path, encoding="utf-8") as f:
                    content = f.read()
                try:
                    exec(content, base_namespace)
                except Exception:
                    pass

            source_names = []
            for file_path in self.constants_files:
                source_name = os.path.basename(file_path)
                source_names.append(source_name)
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                parser = ConstantsParser(content)
                if file_path != base_constants_path:
                    variables = parser.parse_and_resolve(base_namespace=base_namespace)
                else:
                    variables = parser.parse_and_resolve()

                for name, resolved_value, expression in variables:
                    all_variables.append((source_name, name, resolved_value, expression))

            self.finished.emit(all_variables, source_names)
        except Exception as e:
            self.error.emit(str(e))


class VariablesView(QWidget):
    """Widget for displaying variables from constants.py and *_constants.py files."""

    def __init__(self, working_dir=None, parent=None):
        """Initialize the Variables view.

        Args:
            working_dir: Project working directory path
            parent: Parent widget
        """
        super().__init__(parent)
        self.working_dir = working_dir or "."
        self._files_changed = False
        self._parse_worker = None
        self._setup_ui()

    def showEvent(self, event):
        """Set up file watcher and load variables when shown."""
        super().showEvent(event)
        self._setup_file_watcher()
        self._files_changed = False
        self._load_variables()

    def hideEvent(self, event):
        """Stop file watcher when hidden."""
        super().hideEvent(event)
        self._stop_file_watcher()

    def _find_constants_files(self):
        """Find all constants files in the working directory.

        Returns:
            List of paths to constants files, with constants.py first if it exists
        """
        files = []
        base_constants = os.path.join(self.working_dir, "constants.py")

        # Add base constants.py first if it exists
        if os.path.exists(base_constants):
            files.append(base_constants)

        # Find all *_constants.py files
        pattern = os.path.join(self.working_dir, "*_constants.py")
        for path in glob.glob(pattern):
            if path not in files:
                files.append(path)

        return files

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Top row: Refresh button and file filter dropdown
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 5)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFont(QFont("Consolas", 9))
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        top_layout.addWidget(self.refresh_button)

        file_label = QLabel("File:")
        file_label.setFont(QFont("Consolas", 9))
        top_layout.addWidget(file_label)

        self.file_filter = QComboBox()
        self.file_filter.setFont(QFont("Consolas", 9))
        self.file_filter.currentTextChanged.connect(self._on_filter_changed)
        top_layout.addWidget(self.file_filter, 1)  # stretch factor 1

        layout.addLayout(top_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 5)

        search_label = QLabel("Search:")
        search_label.setFont(QFont("Consolas", 9))
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setFont(QFont("Consolas", 9))
        self.search_input.setPlaceholderText("Type to search variable names...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        self.prev_button = QPushButton("←")
        self.prev_button.setFont(QFont("Consolas", 9))
        self.prev_button.setFixedWidth(30)
        self.prev_button.clicked.connect(self._on_prev_clicked)
        search_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("→")
        self.next_button.setFont(QFont("Consolas", 9))
        self.next_button.setFixedWidth(30)
        self.next_button.clicked.connect(self._on_next_clicked)
        search_layout.addWidget(self.next_button)

        # Track matching rows and current index
        self._matching_rows = []
        self._current_match_index = -1

        layout.addLayout(search_layout)

        # Table widget to display variables below the button
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Expression"])
        self.table.setFont(QFont("Consolas", 9))
        self.table.setMaximumHeight(600)

        # Make table read-only
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Expression fills remaining space

        # Set initial column widths
        self.table.setColumnWidth(0, 150)  # Name
        self.table.setColumnWidth(1, 100)  # Value

        layout.addWidget(self.table)

        # Store all variables for filtering
        self._all_variables = []

    def _setup_file_watcher(self):
        """Set up file system watcher for constants files."""
        self._stop_file_watcher()
        self.file_watcher = QFileSystemWatcher()
        self._watched_files = set()

        # Always watch the directory for new constants files
        if os.path.exists(self.working_dir):
            self.file_watcher.addPath(self.working_dir)
            self.file_watcher.directoryChanged.connect(self._on_directory_changed)

        # Watch existing constants files
        self._update_watched_files()
        self.file_watcher.fileChanged.connect(self._on_file_changed)

    def _stop_file_watcher(self):
        """Stop and clean up the file system watcher."""
        if hasattr(self, "file_watcher") and self.file_watcher is not None:
            paths = self.file_watcher.files() + self.file_watcher.directories()
            if paths:
                self.file_watcher.removePaths(paths)
            self.file_watcher.deleteLater()
            self.file_watcher = None
            self._watched_files = set()

    def _update_watched_files(self):
        """Update the list of watched constants files."""
        if self.file_watcher is None:
            return
        current_files = set(self._find_constants_files())

        # Remove files that no longer exist
        for path in self._watched_files - current_files:
            if path in self.file_watcher.files():
                self.file_watcher.removePath(path)

        # Add new files
        for path in current_files - self._watched_files:
            if os.path.exists(path):
                self.file_watcher.addPath(path)

        self._watched_files = current_files

    def _mark_file_changed(self):
        """Mark that files have changed and update the Refresh button."""
        self._files_changed = True
        self.refresh_button.setText("Refresh (file changed)")
        self.refresh_button.setStyleSheet("QPushButton { color: #e65100; font-weight: bold; }")

    def _on_file_changed(self, path):
        """Handle file change event.

        Args:
            path: Path to the changed file
        """
        self._mark_file_changed()

        # Re-add the file to the watcher (required after some editors save by delete+create)
        if self.file_watcher is not None and path not in self.file_watcher.files():
            if os.path.exists(path):
                self.file_watcher.addPath(path)

    def _on_directory_changed(self, path):
        """Handle directory change event (monitors for file creation/deletion).

        Args:
            path: Path to the changed directory
        """
        self._update_watched_files()
        self._mark_file_changed()

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._files_changed = False
        self._update_watched_files()
        self._load_variables()

    def _on_search_changed(self, text):
        """Handle search text change.

        Args:
            text: Search text entered by user
        """
        self._highlight_matching_rows(text)
        # Jump to first match if there are any
        if self._matching_rows:
            self._current_match_index = 0
            self._scroll_to_current_match()

    def _on_prev_clicked(self):
        """Handle prev button click to go to previous match."""
        if not self._matching_rows:
            return
        self._current_match_index = (self._current_match_index - 1) % len(self._matching_rows)
        self._scroll_to_current_match()

    def _on_next_clicked(self):
        """Handle next button click to go to next match."""
        if not self._matching_rows:
            return
        self._current_match_index = (self._current_match_index + 1) % len(self._matching_rows)
        self._scroll_to_current_match()

    def _scroll_to_current_match(self):
        """Scroll to the current matching row."""
        if 0 <= self._current_match_index < len(self._matching_rows):
            row = self._matching_rows[self._current_match_index]
            self.table.scrollToItem(self.table.item(row, 0))

    def _on_filter_changed(self, text):
        """Handle file filter dropdown change.

        Args:
            text: Selected filter text
        """
        self._apply_filter()

    def _set_refresh_busy(self, busy):
        """Set the refresh button to busy or normal state."""
        self.refresh_button.setEnabled(not busy)
        if busy:
            self.refresh_button.setText("Parsing...")
            self.refresh_button.setStyleSheet("QPushButton { color: grey; }")
        else:
            self.refresh_button.setText("Refresh")
            self.refresh_button.setStyleSheet("")

    def _load_variables(self):
        """Load and display variables from all constants files in a background thread."""
        constants_files = self._find_constants_files()

        if not constants_files:
            self._all_variables = []
            self._update_file_filter([])
            self._show_not_found_message()
            return

        self._set_refresh_busy(True)

        self._parse_worker = _ParseWorker(self.working_dir, constants_files)
        self._parse_worker.finished.connect(self._on_parse_finished)
        self._parse_worker.error.connect(self._on_parse_error)
        self._parse_worker.start()

    def _on_parse_finished(self, all_variables, source_names):
        """Handle parsing completion from the worker thread."""
        self._all_variables = all_variables
        self._update_file_filter(source_names)
        self._apply_filter()
        self._set_refresh_busy(False)
        self._parse_worker = None

    def _on_parse_error(self, error_msg):
        """Handle parsing error from the worker thread."""
        self._show_error_message(error_msg)
        self._set_refresh_busy(False)
        self._parse_worker = None

    def _update_file_filter(self, source_names):
        """Update the file filter dropdown with available files.

        Args:
            source_names: List of source file names
        """
        current_selection = self.file_filter.currentText()
        self.file_filter.blockSignals(True)
        self.file_filter.clear()
        self.file_filter.addItem("All Files")
        for name in source_names:
            self.file_filter.addItem(name)

        # Restore previous selection if still valid
        index = self.file_filter.findText(current_selection)
        if index >= 0:
            self.file_filter.setCurrentIndex(index)
        else:
            self.file_filter.setCurrentIndex(0)
        self.file_filter.blockSignals(False)

    def _apply_filter(self):
        """Apply the current file filter and update the table."""
        selected = self.file_filter.currentText()

        if selected == "All Files":
            filtered = [(name, value, expr) for (source, name, value, expr) in self._all_variables]
        else:
            filtered = [
                (name, value, expr) for (source, name, value, expr) in self._all_variables if source == selected
            ]

        self._update_table(filtered)

    def _update_table(self, variables):
        """Update the table with parsed variables.

        Args:
            variables: List of tuples (name, resolved_value, expression)
        """
        self.table.setRowCount(len(variables))

        for row, (name, resolved_value, expression) in enumerate(variables):
            # Name column
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)

            # Value column (resolved)
            value_item = QTableWidgetItem(resolved_value)
            self.table.setItem(row, 1, value_item)

            # Expression column (with tooltip for long expressions)
            expr_item = QTableWidgetItem(expression)
            expr_item.setToolTip(expression)
            self.table.setItem(row, 2, expr_item)

    def _show_not_found_message(self):
        """Display a message when no constants files are found."""
        self.table.setRowCount(1)
        message_item = QTableWidgetItem("No constants files found")
        message_item.setFont(QFont("Consolas", 9))
        self.table.setItem(0, 0, message_item)
        self.table.setItem(0, 1, QTableWidgetItem(""))
        self.table.setItem(0, 2, QTableWidgetItem(""))

    def _show_error_message(self, error_msg):
        """Display an error message.

        Args:
            error_msg: Error message to display
        """
        self.table.setRowCount(1)
        error_item = QTableWidgetItem(f"Error loading variables: {error_msg}")
        error_item.setFont(QFont("Consolas", 9))
        self.table.setItem(0, 0, error_item)
        self.table.setItem(0, 1, QTableWidgetItem(""))
        self.table.setItem(0, 2, QTableWidgetItem(""))

    def _highlight_matching_rows(self, search_text):
        """Highlight rows that match the search text.

        Args:
            search_text: Text to search for in variable names
        """
        # Define colors
        highlight_color = QColor(255, 255, 200)  # Light yellow
        default_color = QColor(255, 255, 255)  # White

        search_lower = search_text.lower()
        self._matching_rows = []
        self._current_match_index = -1

        for row in range(self.table.rowCount()):
            # Get the variable name from the Name column (column 0)
            name_item = self.table.item(row, 0)
            if name_item:
                variable_name = name_item.text().lower()

                # Check if search text matches (case-insensitive)
                if search_lower and search_lower in variable_name:
                    self._matching_rows.append(row)
                    # Highlight the row
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(highlight_color)
                else:
                    # Reset to default color
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(default_color)
