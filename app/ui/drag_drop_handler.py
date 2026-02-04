"""
Drag and drop handling for ForShape AI GUI.

This module provides functionality for handling drag and drop of images
and Python files onto the main window.
"""

import os
import traceback

from PySide2.QtGui import QDragEnterEvent, QDropEvent


class DragDropHandler:
    """Handles drag and drop operations for images and Python files."""

    def __init__(self, message_handler, logger, image_context=None):
        """
        Initialize the drag and drop handler.

        Args:
            message_handler: MessageHandler instance for displaying messages
            logger: Logger instance
            image_context: Optional ImageContext instance for saving images
        """
        self.message_handler = message_handler
        self.image_context = image_context
        self.logger = logger

        # These will be set by the main window
        self.captured_images = []
        self.attached_files = []
        self.is_ai_busy = False
        self.input_field = None
        self.attachment_widget = None

    def set_state_references(
        self, captured_images, attached_files, is_ai_busy_callback, input_field, attachment_widget=None
    ):
        """
        Set references to shared state from the main window.

        Args:
            captured_images: List reference for captured images
            attached_files: List reference for attached files
            is_ai_busy_callback: Callable that returns whether AI is busy
            input_field: QTextEdit for input field
            attachment_widget: Optional AttachmentWidget for displaying attachment chips
        """
        self.captured_images = captured_images
        self.attached_files = attached_files
        self.is_ai_busy_callback = is_ai_busy_callback
        self.input_field = input_field
        self.attachment_widget = attachment_widget

    def update_input_placeholder(self):
        """Update the input field placeholder text based on attached files."""
        if not self.input_field:
            return

        self.input_field.setPlaceholderText(
            "Type your message here... - Drag & drop images or .py files to attach\nPress Enter to send, Shift+Enter for new line"
        )

    def drag_enter_event(self, event: QDragEnterEvent):
        """Handle drag enter event to accept file drops."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are files
            urls = event.mimeData().urls()
            has_files = any(url.isLocalFile() for url in urls)
            if has_files:
                event.acceptProposedAction()
        else:
            event.ignore()

    def drag_move_event(self, event):
        """Handle drag move event for visual feedback."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def drop_event(self, event: QDropEvent):
        """Handle file drop event for images and Python files."""
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        # Get the list of dropped files
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if not files:
            event.ignore()
            return

        # Categorize files by type
        image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
        image_files = []
        python_files = []
        unsupported_files = []

        for file_path in files:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in image_extensions:
                image_files.append(file_path)
            elif file_ext == ".py":
                python_files.append(file_path)
            else:
                unsupported_files.append(file_path)

        # Process image files
        for file_path in image_files:
            self.handle_dropped_image(file_path)

        # Process Python files
        for file_path in python_files:
            self.handle_dropped_python_file(file_path)

        # Show message for unsupported files
        if unsupported_files:
            file_names = ", ".join([os.path.basename(f) for f in unsupported_files])
            self.message_handler.append_message(
                "System", f"Skipped unsupported file(s): {file_names}\n(Supported: images and .py files)"
            )

        event.acceptProposedAction()

    def handle_dropped_image(self, file_path: str):
        """
        Handle a dropped image file by converting it to base64 and adding it to the list.

        Args:
            file_path: Path to the dropped image file
        """
        if self.is_ai_busy_callback and self.is_ai_busy_callback():
            self.message_handler.append_message("System", "AI is currently processing. Please wait...")
            return

        try:
            import base64

            # Read and encode the image
            with open(file_path, "rb") as image_file:
                image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Determine the file extension for saving
            file_ext = os.path.splitext(file_path)[1].lower()

            # Copy the image to the history folder (same as capture does)
            if self.image_context:
                history_dir = self.image_context.images_dir
                os.makedirs(history_dir, exist_ok=True)

                # Generate timestamped filename
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"dropped_{timestamp}{file_ext}"
                new_file_path = os.path.join(history_dir, new_filename)

                # Copy the file
                import shutil

                shutil.copy2(file_path, new_file_path)
                stored_path = new_file_path
            else:
                stored_path = file_path

            # Add the image data to the list (same format as captured images)
            self.captured_images.append(
                {
                    "success": True,
                    "file": stored_path,
                    "image_base64": image_base64,  # Just the base64 string, not the data URL
                }
            )

            if self.attachment_widget:
                self.attachment_widget.refresh()

            # Show success message
            self.message_handler.append_message(
                "System",
                f"Image added!\nFile: {os.path.basename(file_path)}\nSaved to: {stored_path}",
            )

        except Exception:
            error_msg = f"Error processing dropped image:\n{traceback.format_exc()}"
            self.message_handler.append_message("System", error_msg)

    def handle_dropped_python_file(self, file_path: str):
        """
        Handle a dropped Python file by reading its content and adding it to the attached files list.

        Args:
            file_path: Path to the dropped Python file
        """
        if self.is_ai_busy_callback and self.is_ai_busy_callback():
            self.message_handler.append_message("System", "AI is currently processing. Please wait...")
            return

        try:
            # Read the Python file content
            with open(file_path, encoding="utf-8") as f:
                file_content = f.read()

            # Store the file info
            file_info = {"path": file_path, "name": os.path.basename(file_path), "content": file_content}
            self.attached_files.append(file_info)

            # Update UI
            self.update_input_placeholder()
            if self.attachment_widget:
                self.attachment_widget.refresh()

            # Show success message
            self.message_handler.append_message(
                "System",
                f"Python file attached!\nFile: {os.path.basename(file_path)}",
            )

        except Exception:
            error_msg = f"Error processing dropped Python file:\n{traceback.format_exc()}"
            self.message_handler.append_message("System", error_msg)
