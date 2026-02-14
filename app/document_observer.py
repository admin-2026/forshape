"""
FreeCAD document observer for monitoring active document changes.

This module provides functionality to observe FreeCAD document events
and trigger appropriate actions when the active document changes.
"""

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .logger import Logger
    from .prestart_checker import PrestartChecker
    from .ui import ConversationView


class ActiveDocumentObserver:
    """Observer for FreeCAD active document changes."""

    def __init__(
        self,
        prestart_checker: "PrestartChecker",
        logger: "Logger",
        message_handler: "ConversationView",
        enable_ai_mode_callback: Optional[Callable[[], None]] = None,
        enable_prestart_mode_callback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the active document observer.

        Args:
            prestart_checker: PrestartChecker instance to run on document changes
            logger: Logger instance for logging
            message_handler: Message handler for displaying messages to user
            enable_ai_mode_callback: Optional callback to enable AI mode when checks pass
            enable_prestart_mode_callback: Optional callback to re-enable prestart check mode
        """
        self.prestart_checker = prestart_checker
        self.logger = logger
        self.message_handler = message_handler
        self.enable_ai_mode_callback = enable_ai_mode_callback
        self.enable_prestart_mode_callback = enable_prestart_mode_callback
        self._registered = False
        self._last_document_path = None

    def register(self) -> bool:
        """
        Register this observer with FreeCAD.

        Returns:
            True if registration successful, False otherwise
        """
        try:
            import FreeCADGui

            FreeCADGui.addDocumentObserver(self)
            self._registered = True

            # Store the initial document path
            import FreeCAD as App

            if App.ActiveDocument and App.ActiveDocument.FileName:
                self._last_document_path = App.ActiveDocument.FileName

            return True
        except Exception as e:
            self.logger.error(f"Failed to register document observer: {e}")
            return False

    def unregister(self) -> bool:
        """
        Unregister this observer from FreeCAD.

        Returns:
            True if unregistration successful, False otherwise
        """
        if not self._registered:
            return True

        try:
            import FreeCADGui

            FreeCADGui.removeDocumentObserver(self)
            self._registered = False
            return True
        except Exception as e:
            self.logger.error(f"Failed to unregister document observer: {e}")
            return False

    def slotActivateDocument(self, doc):
        """
        Called when the active document changes.

        Args:
            doc: The new active GUI document (Gui.Document, can be None)
        """
        try:
            # doc is a Gui.Document, need to access the underlying App.Document
            app_doc = doc.Document if doc else None

            # Get the document path
            doc_path = app_doc.FileName if app_doc else None

            # Only run checks if the document path actually changed
            # This avoids unnecessary reruns when switching between views of the same document
            if doc_path == self._last_document_path:
                return

            self._last_document_path = doc_path

            if app_doc:
                self.logger.info(f"Active document changed to: {app_doc.Name}")
                self.message_handler.append_message(
                    "System",
                    f"📄 **Active Document Changed**\n\n"
                    f"Active document changed to: `{app_doc.Name}`\n\n"
                    f"Running prestart checks...",
                )
            else:
                self.logger.info("Active document closed (no active document)")
                self.message_handler.append_message(
                    "System",
                    "⚠️ **No Active Document**\n\n"
                    "The active document was closed.\n\n"
                    "Please open or create a document to continue.",
                )
                return

            # Run prestart checker
            status = self.prestart_checker.check()

            # Handle the result
            if status == "ready":
                # All checks passed, enable AI mode if callback provided
                if self.enable_ai_mode_callback:
                    self.enable_ai_mode_callback()
            elif status == "error":
                # Fatal error occurred
                pass
            else:
                # Re-enable prestart check mode so user input is routed to prestart handler
                if self.enable_prestart_mode_callback:
                    self.enable_prestart_mode_callback()

        except Exception as e:
            self.logger.error(f"Error in active document observer: {e}")
            self.message_handler.append_message("System", f"❌ **Error in Document Observer**\n\n{str(e)}")

    def __del__(self):
        """Ensure observer is unregistered when destroyed."""
        self.unregister()
