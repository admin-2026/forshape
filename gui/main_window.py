"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                                QTextEdit, QLineEdit, QLabel, QGroupBox, QPushButton,
                                QMenuBar, QAction, QDialog, QListWidget, QListWidgetItem,
                                QDialogButtonBox, QScrollArea, QComboBox, QColorDialog)
from PySide2.QtCore import QCoreApplication, QThread, Signal, Qt, QProcess, QProcessEnvironment, QPoint
from PySide2.QtGui import QFont, QTextCursor, QColor, QPixmap, QPainter, QPen

import os
import sys
import glob
import io
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_agent import AIAgent
    from .history_logger import HistoryLogger
    from .logger import Logger


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


class DrawableImageLabel(QLabel):
    """A QLabel that allows drawing on the displayed image."""

    def __init__(self, parent=None):
        """Initialize the drawable image label."""
        super().__init__(parent)
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(255, 0, 0)  # Red by default
        self.pen_width = 3
        self.image = None
        self.drawing_layer = None
        self.setMouseTracking(False)

    def set_image(self, pixmap):
        """Set the image to display and create a drawing layer."""
        self.image = pixmap.copy()
        self.drawing_layer = QPixmap(pixmap.size())
        self.drawing_layer.fill(Qt.transparent)
        self.update_display()

    def update_display(self):
        """Update the display by compositing the image and drawing layer."""
        if self.image is None:
            return

        # Composite the original image with the drawing layer
        result = self.image.copy()
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.drawing_layer)
        painter.end()

        self.setPixmap(result)

    def set_pen_color(self, color):
        """Set the pen color for drawing."""
        self.pen_color = color

    def set_pen_width(self, width):
        """Set the pen width for drawing."""
        self.pen_width = width

    def clear_drawings(self):
        """Clear all drawings."""
        if self.drawing_layer:
            self.drawing_layer.fill(Qt.transparent)
            self.update_display()

    def get_annotated_image(self):
        """Get the final image with annotations."""
        if self.image is None:
            return None

        result = self.image.copy()
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.drawing_layer)
        painter.end()
        return result

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton and self.drawing_layer:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move event - draw on the image."""
        if self.drawing and event.buttons() & Qt.LeftButton and self.drawing_layer:
            painter = QPainter(self.drawing_layer)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            painter.end()

            self.last_point = event.pos()
            self.update_display()

    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self.drawing = False


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
            ("Black", QColor(0, 0, 0))
        ]

        for name, color in preset_colors:
            btn = QPushButton(name)
            btn.setFixedSize(60, 25)
            btn.setStyleSheet(f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'};")
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
            target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
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


class AIWorker(QThread):
    """Worker thread for handling AI API calls asynchronously."""

    # Signal emitted when AI processing is complete (response or error)
    finished = Signal(str, bool)  # (message, is_error)

    def __init__(self, ai_client: 'AIAgent', user_input: str, image_data=None):
        """
        Initialize the AI worker thread.

        Args:
            ai_client: The AIAgent instance
            user_input: The user's input to process
            image_data: Optional captured image data to attach
        """
        super().__init__()
        self.ai_client = ai_client
        self.user_input = user_input
        self.image_data = image_data

    def run(self):
        """Run the AI request in a separate thread."""
        try:
            response = self.ai_client.process_request(self.user_input, self.image_data)
            self.finished.emit(response, False)  # False = not an error
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.finished.emit(error_msg, True)  # True = is an error


class ForShapeMainWindow(QMainWindow):
    """Main window for the ForShape AI GUI application."""

    def __init__(self, ai_client: 'AIAgent', history_logger: 'HistoryLogger',
                 logger: 'Logger', context_provider, special_commands_handler, exit_handler,
                 image_context=None, prestart_checker=None, completion_callback=None, window_close_callback=None):
        """
        Initialize the main window.

        Args:
            ai_client: The AIAgent instance for AI interactions (can be None initially)
            history_logger: The HistoryLogger instance for logging (can be None initially)
            logger: The Logger instance for tool call logging
            context_provider: The ContextProvider instance for accessing working directory and project info
            special_commands_handler: Function to handle special commands
            exit_handler: Function to handle exit
            image_context: Optional ImageContext instance for capturing screenshots
            prestart_checker: Optional PrestartChecker instance for prestart validation
            completion_callback: Optional callback to complete initialization after checks pass
            window_close_callback: Optional callback to call when window is closed
        """
        super().__init__()
        self.ai_client = ai_client
        self.history_logger = history_logger
        self.logger = logger
        self.context_provider = context_provider
        self.image_context = image_context
        self.handle_special_commands = special_commands_handler
        self.handle_exit = exit_handler
        self.is_ai_busy = False  # Track if AI is currently processing
        self.pending_input = ""  # Store pending user input when AI is busy
        self.worker = None  # Current worker thread
        self.captured_image_data = None  # Store captured image to attach to next message

        # Prestart check mode
        self.prestart_checker = prestart_checker
        self.prestart_check_mode = True if prestart_checker else False  # Start in prestart check mode if checker provided
        self.completion_callback = completion_callback
        self.window_close_callback = window_close_callback

        # Connect logger signal to display handler
        if self.logger:
            self.logger.log_message.connect(self.on_log_message)

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface components."""
        self.setWindowTitle("ForShape AI - Interactive 3D Shape Generator")
        self.setMinimumSize(1000, 600)

        # Create menu bar
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")

        # Add toggle logs action
        self.toggle_logs_action = QAction("Show Logs", self)
        self.toggle_logs_action.setCheckable(True)
        self.toggle_logs_action.triggered.connect(self.toggle_log_panel)
        view_menu.addAction(self.toggle_logs_action)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create horizontal splitter for conversation and log
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Conversation area
        conversation_widget = QWidget()
        conversation_layout = QVBoxLayout(conversation_widget)
        conversation_layout.setContentsMargins(0, 0, 0, 0)

        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Consolas", 10))
        # Enable rich text (HTML) rendering for markdown support
        self.conversation_display.setAcceptRichText(True)

        # Set default stylesheet for better markdown rendering
        self.conversation_display.document().setDefaultStyleSheet("""
            p { margin: 5px 0; }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 3px;
                font-family: Consolas, monospace;
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, monospace;
            }
            strong { font-weight: bold; }
            em { font-style: italic; }
        """)

        conversation_layout.addWidget(self.conversation_display)

        # Right side: Log area
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("System Logs")
        log_label.setFont(QFont("Consolas", 10, QFont.Bold))
        log_layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setMaximumHeight(600)
        log_layout.addWidget(self.log_display)

        # Add both sides to splitter
        splitter.addWidget(conversation_widget)
        splitter.addWidget(self.log_widget)

        # Set initial splitter sizes (70% conversation, 30% logs)
        splitter.setSizes([700, 300])

        # Hide log panel by default
        self.log_widget.hide()

        main_layout.addWidget(splitter, stretch=1)

        # Create input area with button
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("You:")
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText("Type your message here... (/help for commands)")
        self.input_field.returnPressed.connect(self.on_user_input)

        # Add Build button
        self.run_button = QPushButton("Build")
        self.run_button.setFont(QFont("Consolas", 10))
        self.run_button.setToolTip("Build - run a Python script from the working directory")
        self.run_button.clicked.connect(self.on_run_script)

        # Add Teardown button
        self.redo_button = QPushButton("Teardown")
        self.redo_button.setFont(QFont("Consolas", 10))
        self.redo_button.setToolTip("Teardown - run a script in teardown mode to remove objects")
        self.redo_button.clicked.connect(self.on_redo_script)

        # Add Capture button
        self.capture_button = QPushButton("Capture")
        self.capture_button.setFont(QFont("Consolas", 10))
        self.capture_button.setToolTip("Capture - take a screenshot of the current 3D scene to attach to next message")
        self.capture_button.clicked.connect(self.on_capture_screenshot)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.run_button)
        input_layout.addWidget(self.redo_button)
        input_layout.addWidget(self.capture_button)

        # Add input container to main layout
        main_layout.addWidget(input_container)

        # Display welcome message
        self.display_welcome()

    def display_welcome(self):
        """Display welcome message in the conversation area."""
        # Check if AI client is initialized
        if self.ai_client:
            context_status = "✓ FORSHAPE.md loaded" if self.ai_client.context_provider.has_forshape() else "✗ No FORSHAPE.md"
            model_info = f"<strong>Using model:</strong> {self.ai_client.get_model()}<br>"
            context_info = f"<strong>Context:</strong> {context_status}"
            start_message = "Start chatting to generate 3D shapes!"
        else:
            # During prestart checks
            model_info = ""
            context_info = "<strong>Status:</strong> Setting up..."
            start_message = "Please complete the setup steps below to begin."

        welcome_html = f"""
<div style="font-family: Consolas, monospace; margin: 10px 0;">
<pre style="margin: 0;">{'='*60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{'='*60}</pre>
<p style="margin: 5px 0;">{model_info}{context_info}</p>

<p style="margin: 5px 0;"><strong>Commands:</strong><br>
  /help - Show help<br>
  /clear - Clear conversation history</p>

<p style="margin: 5px 0;">{start_message}</p>
<pre style="margin: 0;">{'='*60}</pre>
</div>
"""
        self.conversation_display.insertHtml(welcome_html)
        # Add line breaks after welcome message to separate from first user message
        self.conversation_display.insertHtml('<br><br>')

    def clear_conversation(self):
        """Clear the conversation display and AI history."""
        # Clear the AI agent's conversation history
        if self.ai_client:
            self.ai_client.clear_history()

        # Clear the conversation display
        self.conversation_display.clear()

        # Redisplay the welcome message
        self.display_welcome()

        # Show confirmation message
        self.append_message("System", "Conversation history cleared.")

    def set_components(self, ai_client: 'AIAgent', history_logger: 'HistoryLogger', logger: 'Logger' = None, image_context=None):
        """
        Set the AI client and history logger after initialization completes.

        Args:
            ai_client: The AIAgent instance
            history_logger: The HistoryLogger instance
            logger: Optional Logger instance to update (if logger was recreated)
            image_context: Optional ImageContext instance for capturing screenshots
        """
        self.ai_client = ai_client
        self.history_logger = history_logger

        # Update image_context if provided
        if image_context is not None:
            self.image_context = image_context

        # Update logger if provided
        if logger is not None:
            # Disconnect old logger
            if self.logger and hasattr(self.logger, 'log_message'):
                try:
                    self.logger.log_message.disconnect(self.on_log_message)
                except:
                    pass

            # Update to new logger
            self.logger = logger

            # Connect new logger
            if self.logger and hasattr(self.logger, 'log_message'):
                self.logger.log_message.connect(self.on_log_message)

    def handle_prestart_input(self, user_input: str):
        """
        Handle user input during prestart check mode.

        Args:
            user_input: The user's input
        """
        if not self.prestart_checker:
            return

        current_status = self.prestart_checker.get_status()

        if current_status == "dir_mismatch":
            # Handle directory mismatch response (yes/no/cancel)
            should_continue = self.prestart_checker.handle_directory_mismatch(self, user_input)
            if should_continue:
                # Re-run prestart checks
                status = self.prestart_checker.check(self)
                if status == "ready":
                    # Complete initialization if callback provided
                    if self.completion_callback:
                        self.completion_callback()
                    self.enable_ai_mode()
            else:
                # User cancelled or error
                self.prestart_check_mode = False
        else:
            # For "waiting", "need_api_key", or other status, re-run checks when user provides input
            status = self.prestart_checker.check(self)
            if status == "ready":
                # Complete initialization if callback provided
                if self.completion_callback:
                    self.completion_callback()
                self.enable_ai_mode()
            elif status == "error":
                self.prestart_check_mode = False

    def enable_ai_mode(self):
        """Enable normal AI interaction mode after prestart checks pass."""
        self.prestart_check_mode = False
        # Update welcome message to show full AI details now that ai_client is initialized
        if self.ai_client:
            context_status = "✓ FORSHAPE.md loaded" if self.ai_client.context_provider.has_forshape() else "✗ No FORSHAPE.md"
            self.append_message("System",
                f"🎉 **Initialization Complete!**\n\n"
                f"**Using model:** {self.ai_client.get_model()}\n"
                f"**Context:** {context_status}\n\n"
                f"You can now chat with the AI to generate 3D shapes!")

    def on_user_input(self):
        """Handle user input when Enter is pressed."""
        user_input = self.input_field.text().strip()

        if not user_input:
            return

        # Display user input
        self.append_message("You", user_input)

        # Clear input field
        self.input_field.clear()

        # Force UI to update immediately
        QCoreApplication.processEvents()

        # Handle prestart check mode
        if self.prestart_check_mode:
            self.handle_prestart_input(user_input)
            return

        # Check if AI client is available
        if not self.ai_client:
            self.append_message("[SYSTEM]", "⚠ AI is not yet initialized. Please wait for setup to complete.")
            return

        # Check if AI is currently busy
        if self.is_ai_busy:
            # Show message that AI is busy without clearing the input
            self.append_message("[SYSTEM]", "⚠ AI is currently processing. Please wait...")
            return

        # Log user input
        if self.history_logger:
            self.history_logger.log_conversation("user", user_input)

        # Handle special commands
        if self.handle_special_commands(user_input, self):
            return

        # Check if there's a captured image to attach
        has_image = self.captured_image_data is not None
        if has_image:
            self.append_message("System", "📷 Attaching captured screenshot to message...")

        # Show in-progress indicator
        self.append_message("AI", "⏳ Processing...")

        # Force UI to update to show the processing indicator
        QCoreApplication.processEvents()

        # Set busy state
        self.is_ai_busy = True

        # Create and start worker thread for AI processing with optional image
        self.worker = AIWorker(self.ai_client, user_input, self.captured_image_data)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.start()

        # Clear captured image data and reset button after sending
        if has_image:
            self.captured_image_data = None
            self.capture_button.setText("Capture")
            self.capture_button.setStyleSheet("")

    def on_ai_response(self, message: str, is_error: bool):
        """
        Handle AI response from worker thread.

        Args:
            message: The response message or error message
            is_error: True if this is an error message, False otherwise
        """
        # Remove the "Processing..." message
        self.remove_last_message()

        # Display the response or error
        if is_error:
            if self.history_logger:
                self.history_logger.log_conversation("error", message)
            self.display_error(message)
        else:
            if self.history_logger:
                self.history_logger.log_conversation("assistant", message)
            self.append_message("AI", message)

        # Reset busy state
        self.is_ai_busy = False

        # Clean up worker thread
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def markdown_to_html(self, text: str) -> str:
        """
        Convert markdown text to HTML.

        Args:
            text: Markdown text to convert

        Returns:
            HTML string
        """
        # Try to import markdown library (lazy import to allow dependency manager to install it first)
        try:
            import markdown as md

            # Configure markdown extensions for better rendering
            extensions = [
                'markdown.extensions.fenced_code',  # Code blocks with ```
                'markdown.extensions.tables',        # Tables
                'markdown.extensions.nl2br',         # Newline to <br>
                'markdown.extensions.codehilite',    # Syntax highlighting
            ]

            try:
                html_output = md.markdown(text, extensions=extensions)
                # Debug: Log that markdown conversion succeeded
                if self.logger:
                    self.logger.debug(f"Markdown converted to HTML: {html_output[:100]}...")
                return html_output
            except Exception as e:
                # Fallback if conversion fails
                if self.logger:
                    self.logger.warn(f"Markdown conversion failed: {e}, using fallback")
                import html
                text = html.escape(text)
                text = text.replace('\n', '<br>')
                return text

        except ImportError:
            # Fallback: basic HTML escaping and line break conversion if markdown not available
            if self.logger:
                self.logger.warn("Markdown library not available, using fallback rendering")
            import html
            text = html.escape(text)
            text = text.replace('\n', '<br>')
            return text

    def append_message(self, role: str, message: str):
        """
        Append a message to the conversation display with markdown support.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown)
        """
        # Move cursor to end before inserting
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

        # Convert markdown to HTML for AI messages
        if role == "AI":
            message_html = self.markdown_to_html(message)
            formatted_message = f'<div style="margin: 15px 0; padding: 8px; background-color: #f9f9f9; border-left: 3px solid #0066CC;"><strong style="color: #0066CC;">{role}:</strong><br>{message_html}</div>'
        else:
            # For user messages and system messages, use simpler formatting
            import html
            escaped_message = html.escape(message).replace('\n', '<br>')
            formatted_message = f'<div style="margin: 15px 0; padding: 8px;"><strong style="color: #333;">{role}:</strong><br>{escaped_message}</div>'

        # Use insertHtml instead of append for proper HTML rendering
        self.conversation_display.insertHtml(formatted_message)

        # Add a line break after each message to separate consecutive messages
        self.conversation_display.insertHtml('<br>')

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def remove_last_message(self):
        """Remove the last message from the conversation display."""
        # Get the document
        document = self.conversation_display.document()

        # Start from the end and work backwards to find and remove the last div block
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Move to the start of the document and select all
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        # Get HTML content
        html_content = cursor.selection().toHtml()

        # Find and remove the last message div (work from the end)
        # Look for the last occurrence of a div with our message styling
        last_div_start = html_content.rfind('<div style="margin: 15px 0; padding: 8px')

        if last_div_start != -1:
            # Find the closing </div> after this opening tag
            search_from = last_div_start + 10
            div_end = html_content.find('</div>', search_from)

            if div_end != -1:
                # Also remove the <br> that follows
                br_end = html_content.find('<br>', div_end)
                if br_end != -1 and br_end - div_end < 20:  # Make sure it's the immediate <br>
                    end_pos = br_end + 4  # Include the <br>
                else:
                    end_pos = div_end + 6  # Just </div>

                # Remove the last message div and br
                html_content = html_content[:last_div_start] + html_content[end_pos:]

                # Set the modified HTML back
                cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                cursor.insertHtml(html_content)

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def display_error(self, error_message: str):
        """
        Display an error message.

        Args:
            error_message: The error message to display
        """
        self.append_message("[ERROR]", error_message)

    def on_log_message(self, level: str, message: str, timestamp: str):
        """
        Handle log messages from the logger.

        Args:
            level: Log level (DEBUG, INFO, WARN, ERROR)
            message: Log message
            timestamp: Timestamp of the log
        """
        # Color code based on log level
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#0066CC",
            "WARN": "#FF8800",
            "ERROR": "#CC0000"
        }
        color = color_map.get(level, "#000000")

        # Format the log message with color
        formatted_log = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span><br>'

        # Move cursor to end before inserting
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

        # Insert HTML
        self.log_display.insertHtml(formatted_log)

        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

    def toggle_log_panel(self):
        """Toggle the visibility of the log panel."""
        if self.log_widget.isVisible():
            self.log_widget.hide()
            self.toggle_logs_action.setText("Show Logs")
            self.toggle_logs_action.setChecked(False)
        else:
            self.log_widget.show()
            self.toggle_logs_action.setText("Hide Logs")
            self.toggle_logs_action.setChecked(True)

    def scan_python_files(self):
        """
        Scan the working directory for Python files.

        Returns:
            List of Python file paths relative to the working directory
        """
        python_files = []

        # Get working directory from context provider
        working_dir = self.context_provider.working_dir

        # Find all .py files in the working directory (non-recursive)
        pattern = os.path.join(working_dir, "*.py")
        files = glob.glob(pattern)

        # Convert to relative paths
        for file_path in files:
            rel_path = os.path.relpath(file_path, working_dir)
            python_files.append(rel_path)

        # Sort alphabetically
        python_files.sort()

        return python_files

    def on_run_script(self):
        """Handle Build button click."""
        # Scan for Python files
        python_files = self.scan_python_files()

        if not python_files:
            self.append_message("[SYSTEM]", "No Python files found in the working directory.")
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.run_python_file(selected_file)

    def on_redo_script(self):
        """Handle Teardown button click."""
        # Scan for Python files
        python_files = self.scan_python_files()

        if not python_files:
            self.append_message("[SYSTEM]", "No Python files found in the working directory.")
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.redo_python_file(selected_file)

    def on_capture_screenshot(self):
        """Handle Capture button click - captures scene screenshot and stores it for next message."""
        if not self.image_context:
            self.append_message("[SYSTEM]", "ImageContext not configured")
            return

        if self.is_ai_busy:
            self.append_message("[SYSTEM]", "AI is currently processing. Please wait...")
            return

        # Show capturing message
        self.append_message("System", "Capturing screenshot...")

        # Force UI to update
        QCoreApplication.processEvents()

        try:
            # Fit all objects in view before capturing (so user can see what will be captured)
            self.image_context.fit()

            # Capture screenshot with base64 encoding using image_context
            result = self.image_context.capture_encoded(perspective="isometric")

            if result is None or not result.get("success"):
                self.append_message("[SYSTEM]", "Screenshot capture failed")
                return

            file_path = result.get("file", "unknown")

            # Show preview dialog for user to confirm or cancel (and potentially annotate)
            preview_dialog = ImagePreviewDialog(file_path, self)
            if preview_dialog.exec_() == QDialog.Accepted and preview_dialog.is_confirmed():
                # User confirmed - the annotated image has been saved to file_path
                # Re-encode the potentially modified image
                import base64
                try:
                    with open(file_path, 'rb') as image_file:
                        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Update the result with the new base64 encoding
                    result["image_base64"] = image_base64

                    # Store the captured (and potentially annotated) image data
                    self.captured_image_data = result

                    # Visual feedback - update button to show image is ready
                    self.capture_button.setText("Capture ✓")
                    self.capture_button.setStyleSheet("background-color: #90EE90;")

                    # Show success message
                    self.append_message("System",
                        f"Screenshot confirmed!\n"
                        f"Saved to: {file_path}\n"
                        f"The image will be attached to your next message.")
                except Exception as e:
                    self.append_message("[SYSTEM]", f"Error encoding annotated image: {str(e)}")
            else:
                # User cancelled - discard the image
                self.append_message("System", "Screenshot cancelled. Image will not be attached.")

        except Exception as e:
            import traceback
            error_msg = f"Error capturing screenshot:\n{traceback.format_exc()}"
            self.append_message("[SYSTEM]", error_msg)

    def redo_python_file(self, file_path):
        """
        Teardown a Python file - run the script in teardown mode to remove objects.

        Args:
            file_path: Path to the Python file to teardown
        """
        self.append_message("[SYSTEM]", f"Tearing down: {file_path}")

        # Get absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            self.display_error(f"File not found: {file_path}")
            return

        # Add project directory to sys.path if not already there
        project_dir = self.context_provider.get_project_dir()
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        try:
            # Read the script content
            with open(abs_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Teardown: Run script with TEARDOWN_MODE=True
            # Set TEARDOWN_MODE as a builtin so it's accessible from all modules
            import builtins
            builtins.TEARDOWN_MODE = True

            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            try:
                # Execute the script in teardown mode
                exec_globals = {
                    '__name__': '__main__',
                    '__file__': abs_path,
                }
                exec(script_content, exec_globals)

                # Get captured output
                stdout_output = sys.stdout.getvalue()
                stderr_output = sys.stderr.getvalue()

                # Display output if any
                if stdout_output.strip():
                    self.append_message("[OUTPUT]", stdout_output.strip())
                if stderr_output.strip():
                    self.append_message("[STDERR]", stderr_output.strip())

                # Success message
                self.append_message("[SYSTEM]", f"Teardown completed successfully: {file_path}")

            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # Reset TEARDOWN_MODE
                builtins.TEARDOWN_MODE = False

        except Exception as e:
            # Restore stdout and stderr in case of error
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            # Reset TEARDOWN_MODE
            import builtins
            builtins.TEARDOWN_MODE = False

            # Format and display the error
            error_msg = f"Error during redo of {file_path}:\n{traceback.format_exc()}"
            self.display_error(error_msg)

    def run_python_file(self, file_path):
        """
        Run a Python file in the current Python context (FreeCAD's interpreter).

        Args:
            file_path: Path to the Python file to run
        """
        self.append_message("[SYSTEM]", f"Running: {file_path}")

        # Get absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            self.display_error(f"File not found: {file_path}")
            return

        # Add project directory to sys.path if not already there
        project_dir = self.context_provider.get_project_dir()
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        try:
            # Read the script content
            with open(abs_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            try:
                # Execute the script in the current context
                # This allows it to access FreeCAD's App.activeDocument()
                exec(script_content, {'__name__': '__main__', '__file__': abs_path})

                # Get captured output
                stdout_output = sys.stdout.getvalue()
                stderr_output = sys.stderr.getvalue()

                # Display output if any
                if stdout_output.strip():
                    self.append_message("[OUTPUT]", stdout_output.strip())
                if stderr_output.strip():
                    self.append_message("[STDERR]", stderr_output.strip())

                # Success message
                self.append_message("[SYSTEM]", f"Finished running: {file_path}")

            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except Exception as e:
            # Restore stdout and stderr in case of error
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Format and display the error
            error_msg = f"Error executing {file_path}:\n{traceback.format_exc()}"
            self.display_error(error_msg)

    def closeEvent(self, event):
        """Handle window close event."""
        self.handle_exit()

        # Call the window close callback to clear the active window reference
        if self.window_close_callback:
            self.window_close_callback()

        event.accept()
