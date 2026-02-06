"""
AI request/response cycle management for ForShape AI GUI.

This module provides functionality for managing AI requests, responses,
cancellation, and token updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import QCoreApplication, Qt

from agent.request import ImageMessage, TextMessage
from agent.step_config import StepConfig, StepConfigRegistry

from ..workers import AIWorker

if TYPE_CHECKING:
    from agent.ai_agent import AIAgent
    from agent.history_logger import HistoryLogger


class AIRequestController:
    """Manages AI request/response cycle, worker thread, and token updates."""

    def __init__(self, logger):
        """
        Initialize the AI request controller.

        Args:
            logger: Logger instance
        """
        self.logger = logger

        # AI-related state
        self.ai_client: AIAgent = None
        self.history_logger: HistoryLogger = None
        self.is_ai_busy = False
        self.current_step_config = None
        self.worker = None

        # References that will be set later
        self.message_handler = None
        self.token_status_label = None
        self.cancel_button = None
        self.main_window = None

    def set_ai_client(self, ai_client: AIAgent):
        """Set the AI client reference."""
        self.ai_client = ai_client

    def set_history_logger(self, history_logger: HistoryLogger):
        """Set the history logger reference."""
        self.history_logger = history_logger

    def set_message_handler(self, message_handler):
        """Set the message handler reference."""
        self.message_handler = message_handler

    def set_token_status_label(self, token_status_label):
        """Set the token status label reference."""
        self.token_status_label = token_status_label

    def set_cancel_button(self, cancel_button):
        """Set the cancel button reference."""
        self.cancel_button = cancel_button

    def set_main_window(self, main_window):
        """Set the main window reference for bringing to front."""
        self.main_window = main_window

    def is_busy(self) -> bool:
        """Check if AI is currently processing."""
        return self.is_ai_busy

    def add_pending_message(self, text: str):
        """
        Add a message to be processed during the current AI iteration.

        Args:
            text: The message text to add
        """
        if self.current_step_config:
            self.current_step_config.add_pending_message(text)
            if self.message_handler:
                self.message_handler.append_message(
                    "System", "✓ Your message will be added to the ongoing conversation..."
                )
        else:
            if self.message_handler:
                self.message_handler.append_message("System", "⚠ AI is currently processing. Please wait...")

    def submit_request(self, text: str, attached_files: list, captured_images: list) -> StepConfig:
        """
        Submit an AI request with the given text and attachments.

        Args:
            text: The user's input text
            attached_files: List of attached file info dicts
            captured_images: List of captured image dicts

        Returns:
            The StepConfig used for this request
        """
        # Log user input
        if self.history_logger:
            self.history_logger.log_conversation("user", text)

        # Build initial_messages for the main step (files and images)
        initial_messages = []

        # Add attached files as TextMessage
        if attached_files:
            file_count = len(attached_files)
            if self.message_handler:
                word = "file" if file_count == 1 else "files"
                self.message_handler.append_message("System", f"📎 Attaching {file_count} Python {word} to message...")
            for file_info in attached_files:
                file_content = f"[Attached Python file: {file_info['name']}]\n```python\n{file_info['content']}\n```"
                initial_messages.append(TextMessage("user", file_content))

        # Add images as ImageMessage
        if captured_images:
            image_count = len(captured_images)
            if self.message_handler:
                word = "image" if image_count == 1 else "images"
                self.message_handler.append_message("System", f"📷 Attaching {image_count} {word} to message...")
            initial_messages.append(ImageMessage("Screenshot of the FreeCAD scene:", captured_images))

        # Show in-progress indicator
        if self.message_handler:
            self.message_handler.create_agent_progress_widget()

        # Force UI to update to show the processing indicator
        QCoreApplication.processEvents()

        # Set busy state
        self.is_ai_busy = True

        # Show cancel button when AI starts processing
        if self.cancel_button:
            self.cancel_button.setVisible(True)

        # Create StepConfig with the user input and store it for pending messages
        main_step_config = StepConfig(initial_message=text)
        self.current_step_config = main_step_config

        # Create StepConfigRegistry and set the main step config
        step_configs = StepConfigRegistry()
        step_configs.set_config("main", main_step_config)
        # step_configs.set_config("router", main_step_config)

        # Append messages for main step if any exist
        if initial_messages:
            step_configs.append_messages("main", initial_messages)

        # Create and start worker thread for AI processing with step configs
        self.worker = AIWorker(self.ai_client, text, step_configs)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.token_update.connect(self.on_token_update)
        self.worker.step_response.connect(self.on_step_response)
        self.worker.start()

        # Reset and show token status label for new request
        if self.token_status_label:
            self.token_status_label.reset()

        return main_step_config

    def cancel_request(self):
        """Cancel the current AI processing."""
        if not self.is_ai_busy or not self.worker:
            return

        # Request cancellation from the worker
        self.worker.cancel()

        # Show cancellation message
        if self.message_handler:
            self.message_handler.append_message("System", "Cancellation requested. Waiting for AI to stop...")

        # Force UI to update
        QCoreApplication.processEvents()

    def on_token_update(self, token_data: dict):
        """
        Handle token usage updates during AI processing.

        Args:
            token_data: Dict with token usage information including iteration number
        """
        if self.token_status_label:
            self.token_status_label.update_tokens(token_data)

        if token_data:
            # Force UI update
            QCoreApplication.processEvents()

    def on_ai_response(self, message: str, is_error: bool, token_data: dict = None):
        """
        Handle AI response completion from worker thread.

        Args:
            message: Error message (only used when is_error is True)
            is_error: True if this is an error message, False otherwise
            token_data: Optional dict with token usage information
        """
        # Update the token status label to show final count
        if self.token_status_label:
            self.token_status_label.finalize(token_data)

        # Display error if any (success responses are handled by on_step_response)
        if is_error:
            if self.history_logger:
                self.history_logger.log_conversation("error", message)
            if self.message_handler:
                self.message_handler.display_error(message)

        # Play notification sound when AI finishes
        self.play_notification_sound()

        # Bring main window to front when AI finishes
        if self.main_window:
            self.main_window.raise_()
            self.main_window.activateWindow()
            # Restore window if minimized
            if self.main_window.isMinimized():
                self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        # Reset busy state
        self.is_ai_busy = False

        # Clear the step config
        self.current_step_config = None

        # Hide cancel button when AI finishes
        if self.cancel_button:
            self.cancel_button.setVisible(False)

        # Clean up worker thread
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        if self.message_handler:
            self.message_handler.agent_progress_done()

    def on_step_response(self, step_name: str, response: str):
        """
        Handle step response from worker thread for async printing.

        Args:
            step_name: The name of the step that completed
            response: The response from the step
        """
        # Display the step response
        if self.message_handler:
            self.message_handler.append_message("AI", response)

    def play_notification_sound(self):
        """Play a notification sound when AI finishes processing."""
        try:
            import platform

            if platform.system() == "Windows":
                import winsound

                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                print("\a")  # ASCII bell character
        except Exception as e:
            self.logger.debug(f"Could not play notification sound: {e}")
