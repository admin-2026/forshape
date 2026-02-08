"""
Input area management for ForShape AI GUI.

This module provides functionality for creating and managing the input area,
including the input field, action buttons, and attachment widget.
"""

from PySide2.QtCore import QObject, Qt, Signal
from PySide2.QtGui import QFont
from PySide2.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .attachment_widget import AttachmentWidget
from .token_status_label import TokenStatusLabel
from .widgets import MultiLineInputField


class InputAreaManager(QObject):
    """Manages the input area including input field, buttons, and attachments."""

    # Signals for user actions
    submit_requested = Signal(str)  # text entered
    capture_requested = Signal()
    new_chat_requested = Signal()
    rewind_requested = Signal()
    cancel_requested = Signal()
    run_script_requested = Signal(str)  # mode: rebuild/teardown/incremental/export/import

    def __init__(self, message_formatter, logger):
        """
        Initialize the input area manager.

        Args:
            message_formatter: MessageFormatter instance for token status label
            logger: Logger instance
        """
        super().__init__()
        self.message_formatter = message_formatter
        self.logger = logger

        # UI elements
        self.input_field = None
        self.cancel_button = None
        self.capture_button = None
        self.new_chat_button = None
        self.rewind_button = None
        self.incremental_build_button = None
        self.run_button = None
        self.teardown_button = None
        self.export_button = None
        self.import_button = None
        self.attachment_widget = None
        self.token_status_label = None

        # State references (set later)
        self.captured_images = None
        self.attached_files = None

    def set_state_references(self, captured_images, attached_files):
        """
        Set references to shared state.

        Args:
            captured_images: List reference for captured images
            attached_files: List reference for attached files
        """
        self.captured_images = captured_images
        self.attached_files = attached_files

        if self.attachment_widget:
            self.attachment_widget.set_state_references(captured_images, attached_files)

    def create_widget(self, submit_callback) -> QWidget:
        """
        Create and return the input area widget.

        Args:
            submit_callback: Callback function for when user submits input

        Returns:
            The input area container widget
        """
        # Create input area with buttons
        input_container = QWidget()
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(5)

        # First row: Capture and New Chat buttons
        first_row = self._create_first_row()

        # Create attachment widget for showing pending attachments as chips
        self.attachment_widget = AttachmentWidget()

        # Second row: input field and cancel button
        second_row = self._create_second_row(submit_callback)

        # Third row: Build and Teardown buttons
        third_row = self._create_third_row()

        # Fourth row: Token usage status label
        self.token_status_label = TokenStatusLabel(self.message_formatter)

        # Add all rows to the input container
        input_container_layout.addWidget(first_row)
        input_container_layout.addWidget(self.attachment_widget)
        input_container_layout.addWidget(second_row)
        input_container_layout.addWidget(third_row)
        input_container_layout.addWidget(self.token_status_label)

        return input_container

    def _create_first_row(self) -> QWidget:
        """Create the first row with Capture, New Chat, and Rewind buttons."""
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        # Add Capture button
        self.capture_button = QPushButton("Capture")
        self.capture_button.setFont(QFont("Consolas", 10))
        self.capture_button.setToolTip(
            "Capture - take a screenshot of the current 3D scene to attach to next message\n\n"
            "Tip: You can also drag & drop image files onto the window!"
        )
        self.capture_button.clicked.connect(self.capture_requested.emit)

        # Add New Chat button
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.setFont(QFont("Consolas", 10))
        self.new_chat_button.setToolTip("New Chat - clear the chatbox and conversation history")
        self.new_chat_button.clicked.connect(self.new_chat_requested.emit)

        # Add Rewind button
        self.rewind_button = QPushButton("Rewind")
        self.rewind_button.setFont(QFont("Consolas", 10))
        self.rewind_button.setToolTip("Rewind - restore files from a previous checkpoint")
        self.rewind_button.clicked.connect(self.rewind_requested.emit)

        first_row_layout.addWidget(self.capture_button)
        first_row_layout.addWidget(self.new_chat_button)
        first_row_layout.addWidget(self.rewind_button)
        first_row_layout.addStretch()  # Push buttons to the left

        return first_row

    def _create_second_row(self, submit_callback) -> QWidget:
        """Create the second row with input field and cancel button."""
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("You:")
        self.input_field = MultiLineInputField()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText(
            "Type your message here... - Drag & drop images or .py files to attach\n"
            "Press Enter to send, Shift+Enter for new line"
        )
        self.input_field.submit_callback = submit_callback

        # Configure for 5 lines high with word wrap and scrolling
        self.input_field.setLineWrapMode(QTextEdit.WidgetWidth)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set height to approximately 5 lines
        font_metrics = self.input_field.fontMetrics()
        line_height = font_metrics.lineSpacing()
        self.input_field.setFixedHeight(line_height * 5 + 10)  # 5 lines + padding

        # Add Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(QFont("Consolas", 10))
        self.cancel_button.setToolTip("Cancel - stop the current AI processing")
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        self.cancel_button.setVisible(False)  # Initially hidden
        self.cancel_button.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")

        second_row_layout.addWidget(input_label)
        second_row_layout.addWidget(self.input_field, stretch=1)
        second_row_layout.addWidget(self.cancel_button)

        return second_row

    def _create_third_row(self) -> QWidget:
        """Create the third row with build/teardown/export/import buttons."""
        third_row = QWidget()
        third_row_layout = QHBoxLayout(third_row)
        third_row_layout.setContentsMargins(0, 0, 0, 0)

        # Incremental Build button disabled due to low usage
        # self.incremental_build_button = QPushButton("Incremental Build")
        # self.incremental_build_button.setFont(QFont("Consolas", 10))
        # self.incremental_build_button.setToolTip(
        #     "Incremental Build - run a script in incremental build mode (skips construction if objects exist)"
        # )
        # self.incremental_build_button.clicked.connect(lambda: self.run_script_requested.emit("incremental"))

        # Add Build button
        self.run_button = QPushButton("Build")
        self.run_button.setFont(QFont("Consolas", 10))
        self.run_button.setToolTip("Build - run a Python script from the working directory")
        self.run_button.clicked.connect(lambda: self.run_script_requested.emit("rebuild"))

        # Teardown button disabled due to low usage
        # self.teardown_button = QPushButton("Teardown")
        # self.teardown_button.setFont(QFont("Consolas", 10))
        # self.teardown_button.setToolTip("Teardown - run a script to teardown an object into components")
        # self.teardown_button.clicked.connect(lambda: self.run_script_requested.emit("teardown"))

        # Add Export button
        self.export_button = QPushButton("Export")
        self.export_button.setFont(QFont("Consolas", 10))
        self.export_button.setToolTip("Export - run export.py from the working directory")
        self.export_button.clicked.connect(lambda: self.run_script_requested.emit("export"))

        # Add Import button
        self.import_button = QPushButton("Import")
        self.import_button.setFont(QFont("Consolas", 10))
        self.import_button.setToolTip("Import - run import.py from the working directory")
        self.import_button.clicked.connect(lambda: self.run_script_requested.emit("import"))

        # third_row_layout.addWidget(self.incremental_build_button)
        third_row_layout.addWidget(self.run_button)
        # third_row_layout.addWidget(self.teardown_button)  # Disabled due to low usage
        third_row_layout.addWidget(self.export_button)
        third_row_layout.addWidget(self.import_button)
        third_row_layout.addStretch()  # Push buttons to the left

        return third_row

    def set_ai_busy(self, busy: bool):
        """
        Update UI state based on whether AI is busy.

        Args:
            busy: True if AI is processing, False otherwise
        """
        self.cancel_button.setVisible(busy)

    def clear_input(self):
        """Clear the input field."""
        if self.input_field:
            self.input_field.clear()

    def get_text(self) -> str:
        """Get the current text from the input field."""
        if self.input_field:
            return self.input_field.toPlainText().strip()
        return ""

    def refresh_attachments(self):
        """Refresh the attachment widget display."""
        if self.attachment_widget:
            self.attachment_widget.refresh()

    def update_input_placeholder(self):
        """Update the input field placeholder text based on attached files."""
        if not self.input_field:
            return

        self.input_field.setPlaceholderText(
            "Type your message here... - Drag & drop images or .py files to attach\n"
            "Press Enter to send, Shift+Enter for new line"
        )

    def connect_attachment_removed(self, callback):
        """
        Connect a callback to the attachment_removed signal.

        Args:
            callback: Function to call when an attachment is removed
        """
        if self.attachment_widget:
            self.attachment_widget.attachment_removed.connect(callback)
