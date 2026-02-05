"""Variables view widget for displaying variables."""

import ast
import os

from PySide2.QtCore import QFileSystemWatcher
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import (
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


class VariablesView(QWidget):
    """Widget for displaying variables from constants.py."""

    def __init__(self, working_dir=None, parent=None):
        """Initialize the Variables view.

        Args:
            working_dir: Project working directory path
            parent: Parent widget
        """
        super().__init__(parent)
        # Use working directory to find constants.py
        if working_dir:
            self.constants_path = os.path.join(working_dir, "constants.py")
        else:
            self.constants_path = "constants.py"
        self._setup_ui()
        self._setup_file_watcher()
        self._load_variables()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Refresh button at the top
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 5)

        self.refresh_button = QPushButton("Refresh Variables")
        self.refresh_button.setFont(QFont("Consolas", 9))
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

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

        layout.addLayout(search_layout)

        # Table widget to display variables below the button
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Expression"])
        self.table.setFont(QFont("Consolas", 9))
        self.table.setMaximumHeight(600)

        # Make table read-only
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set column resize modes to Interactive (user can adjust)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)

        # Set initial column widths
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 200)

        layout.addWidget(self.table)

    def _setup_file_watcher(self):
        """Set up file system watcher for constants.py."""
        self.file_watcher = QFileSystemWatcher()
        self.watching_directory = False

        if os.path.exists(self.constants_path):
            # File exists, watch the file directly
            self.file_watcher.addPath(self.constants_path)
            self.file_watcher.fileChanged.connect(self._on_file_changed)
        else:
            # File doesn't exist, watch the directory for file creation
            directory = os.path.dirname(self.constants_path)
            if directory and os.path.exists(directory):
                self.file_watcher.addPath(directory)
                self.file_watcher.directoryChanged.connect(self._on_directory_changed)
                self.watching_directory = True

    def _on_file_changed(self, path):
        """Handle file change event.

        Args:
            path: Path to the changed file
        """
        # Reload variables when file changes
        self._load_variables()

        # Re-add the file to the watcher (required after some editors save by delete+create)
        if path not in self.file_watcher.files():
            if os.path.exists(path):
                self.file_watcher.addPath(path)

    def _on_directory_changed(self, path):
        """Handle directory change event (monitors for file creation).

        Args:
            path: Path to the changed directory
        """
        # Check if constants.py was created
        if os.path.exists(self.constants_path):
            # File was created, switch from directory watching to file watching
            if self.watching_directory:
                # Stop watching directory
                directory = os.path.dirname(self.constants_path)
                if directory in self.file_watcher.directories():
                    self.file_watcher.removePath(directory)
                self.file_watcher.directoryChanged.disconnect(self._on_directory_changed)

                # Start watching file
                self.file_watcher.addPath(self.constants_path)
                self.file_watcher.fileChanged.connect(self._on_file_changed)
                self.watching_directory = False

            # Load variables from newly created file
            self._load_variables()
        else:
            # File might have been deleted, refresh to show "not found"
            self._load_variables()

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._load_variables()

    def _on_search_changed(self, text):
        """Handle search text change.

        Args:
            text: Search text entered by user
        """
        self._highlight_matching_rows(text)

    def _load_variables(self):
        """Load and display variables from constants.py."""
        if not os.path.exists(self.constants_path):
            self._show_not_found_message()
            return

        try:
            with open(self.constants_path, encoding="utf-8") as f:
                content = f.read()

            # Get both parsed expressions and resolved values
            variables = self._parse_and_resolve_variables(content)
            self._update_table(variables)
        except Exception as e:
            self._show_error_message(str(e))

    def _parse_expressions(self, content):
        """Parse variable expressions from Python source using AST.

        Args:
            content: File content as string

        Returns:
            Dictionary mapping variable names to their source expressions
        """
        expressions = {}
        try:
            tree = ast.parse(content)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            name = target.id
                            expression = ast.get_source_segment(content, node.value)
                            if expression:
                                expressions[name] = expression
        except SyntaxError:
            pass
        return expressions

    def _parse_and_resolve_variables(self, content):
        """Parse variables and resolve their values by executing constants.py.

        Args:
            content: File content as string

        Returns:
            List of tuples (name, resolved_value, expression)
        """
        expressions = self._parse_expressions(content)
        resolved_values = self._execute_constants(content)

        variables = []
        for name, expression in expressions.items():
            resolved_value = resolved_values.get(name, "N/A")
            variables.append((name, resolved_value, expression))

        return variables

    def _execute_constants(self, content):
        """Execute constants.py content and return resolved variable values.

        Args:
            content: File content as string

        Returns:
            Dictionary of variable names to resolved values
        """
        try:
            # Create a namespace for execution
            namespace = {}

            # Execute the content
            exec(content, namespace)

            # Extract only uppercase variables (constants)
            resolved = {}
            for name, value in namespace.items():
                if name.isupper() and not name.startswith("_"):
                    resolved[name] = str(value)

            return resolved
        except Exception:
            # If execution fails, return empty dict
            return {}

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

            # Expression column
            expr_item = QTableWidgetItem(expression)
            self.table.setItem(row, 2, expr_item)

    def _show_not_found_message(self):
        """Display a message when constants.py is not found."""
        self.table.setRowCount(1)
        message_item = QTableWidgetItem("constants.py not found")
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

        for row in range(self.table.rowCount()):
            # Get the variable name from the first column
            name_item = self.table.item(row, 0)
            if name_item:
                variable_name = name_item.text().lower()

                # Check if search text matches (case-insensitive)
                if search_lower and search_lower in variable_name:
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
