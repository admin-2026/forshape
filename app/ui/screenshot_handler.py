"""
Screenshot handling for ForShape AI GUI.

This module provides functionality for capturing screenshots,
showing preview dialogs, and encoding images.
"""

import base64

from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QDialog

from ..dialogs import ImagePreviewDialog


class ScreenshotHandler:
    """Handles screenshot capture, preview dialog, and encoding."""

    def __init__(self, image_context, logger):
        """
        Initialize the screenshot handler.

        Args:
            image_context: ImageContext instance for capturing screenshots
            logger: Logger instance
        """
        self.image_context = image_context
        self.logger = logger

        # References that will be set later
        self.message_handler = None
        self.captured_images = None
        self.attachment_widget = None
        self.is_ai_busy_callback = None

    def set_message_handler(self, message_handler):
        """Set the message handler reference."""
        self.message_handler = message_handler

    def set_state_references(self, captured_images, attachment_widget, is_ai_busy_callback):
        """
        Set references to shared state.

        Args:
            captured_images: List reference for captured images
            attachment_widget: AttachmentWidget for displaying attachment chips
            is_ai_busy_callback: Callable that returns whether AI is busy
        """
        self.captured_images = captured_images
        self.attachment_widget = attachment_widget
        self.is_ai_busy_callback = is_ai_busy_callback

    def set_image_context(self, image_context):
        """Update the image context reference."""
        self.image_context = image_context

    def capture(self, parent_widget):
        """
        Capture a screenshot, show preview, and add to pending attachments.

        Args:
            parent_widget: Parent widget for the preview dialog
        """
        if not self.image_context:
            if self.message_handler:
                self.message_handler.append_message("System", "ImageContext not configured")
            return

        if self.is_ai_busy_callback and self.is_ai_busy_callback():
            if self.message_handler:
                self.message_handler.append_message("System", "AI is currently processing. Please wait...")
            return

        # Show capturing message
        if self.message_handler:
            self.message_handler.append_message("System", "Capturing screenshot...")

        # Force UI to update
        QCoreApplication.processEvents()

        try:
            # Fit all objects in view before capturing (so user can see what will be captured)
            self.image_context.fit()

            # Capture screenshot with base64 encoding using image_context
            result = self.image_context.capture_encoded(perspective="isometric")

            if result is None or not result.get("success"):
                if self.message_handler:
                    self.message_handler.append_message("System", "Screenshot capture failed")
                return

            file_path = result.get("file", "unknown")

            # Show preview dialog for user to confirm or cancel (and potentially annotate)
            preview_dialog = ImagePreviewDialog(file_path, parent_widget)
            if preview_dialog.exec_() == QDialog.Accepted and preview_dialog.is_confirmed():
                # User confirmed - the annotated image has been saved to file_path
                # Re-encode the potentially modified image
                try:
                    with open(file_path, "rb") as image_file:
                        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

                    # Update the result with the new base64 encoding
                    result["image_base64"] = image_base64

                    # Add the captured (and potentially annotated) image data to the list
                    if self.captured_images is not None:
                        self.captured_images.append(result)

                    if self.attachment_widget:
                        self.attachment_widget.refresh()

                    # Show success message
                    if self.message_handler:
                        self.message_handler.append_message(
                            "System",
                            f"Screenshot confirmed!\nSaved to: {file_path}",
                        )
                except Exception as e:
                    if self.message_handler:
                        self.message_handler.append_message("System", f"Error encoding annotated image: {str(e)}")
            else:
                # User cancelled - discard the image
                if self.message_handler:
                    self.message_handler.append_message("System", "Screenshot cancelled. Image will not be attached.")

        except Exception:
            import traceback

            error_msg = f"Error capturing screenshot:\n{traceback.format_exc()}"
            if self.message_handler:
                self.message_handler.append_message("System", error_msg)
