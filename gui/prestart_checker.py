"""
Prestart checker for FreeCAD document validation.

This module provides functionality to check if FreeCAD has an active document
and that the working directory is properly configured before starting the AI agent.
"""

import os
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .main_window import ForShapeMainWindow
    from .context_provider import ContextProvider
    from .logger import Logger


class PrestartChecker:
    """Handles prestart checks for FreeCAD document and working directory validation."""

    def __init__(self, context_provider: 'ContextProvider', logger: 'Logger'):
        """
        Initialize the prestart checker.

        Args:
            context_provider: Context provider for working directory management
            logger: Logger instance for logging check results
        """
        self.context_provider = context_provider
        self.logger = logger
        self.status: Literal["waiting", "dir_mismatch", "ready", "error"] = "waiting"

    def check(self, window: 'ForShapeMainWindow') -> Literal["waiting", "dir_mismatch", "ready", "error"]:
        """
        Check if FreeCAD has an active document and it's saved in the current directory.

        Uses chatbox for interaction instead of modal dialogs so user can interact with FreeCAD.

        Args:
            window: The main window instance to display messages

        Returns:
            Status string: "ready" if checks passed, "waiting" if waiting for user action,
                          "dir_mismatch" if directory needs confirmation, "error" if fatal error
        """
        try:
            import FreeCAD as App
        except ImportError:
            window.append_message("System",
                "❌ **FreeCAD Not Available**\n\n"
                "FreeCAD module could not be imported. Please run this from FreeCAD's Python console.")
            self.status = "error"
            return "error"

        # Check 1: Is there an active document?
        if App.ActiveDocument is None:
            window.append_message("System",
                "⚠️ **No Active Document**\n\n"
                "There is no active FreeCAD document.\n\n"
                "**Please do the following:**\n"
                "1. In FreeCAD, create a new document (File → New)\n"
                "2. Save the document (File → Save)\n"
                "3. Come back here and type anything (e.g., 'ready') to continue")
            self.status = "waiting"
            return "waiting"

        # Check 2: Is the document saved?
        doc_path = App.ActiveDocument.FileName
        if not doc_path or doc_path == "":
            window.append_message("System",
                f"⚠️ **Document Not Saved**\n\n"
                f"The active document '{App.ActiveDocument.Name}' has not been saved yet.\n\n"
                f"**Please do the following:**\n"
                f"1. In FreeCAD, save the document (File → Save or Ctrl+S)\n"
                f"2. Come back here and type anything (e.g., 'ready') to continue")
            self.status = "waiting"
            return "waiting"

        # Check 3: Does the working directory match the document's directory?
        doc_dir = os.path.dirname(os.path.abspath(doc_path))
        current_dir = os.path.abspath(self.context_provider.working_dir)

        if doc_dir != current_dir:
            window.append_message("System",
                f"⚠️ **Working Directory Mismatch**\n\n"
                f"The current working directory does not match the document's location.\n\n"
                f"📁 **Document location:** `{doc_dir}`\n"
                f"📂 **Current directory:** `{current_dir}`\n\n"
                f"**Options:**\n"
                f"• Type **'yes'** to change working directory to match document location\n"
                f"• Type **'no'** to continue with current directory\n"
                f"• Type **'cancel'** to exit")
            self.status = "dir_mismatch"
            return "dir_mismatch"

        # All checks passed
        self.logger.info(f"Prestart checks passed. Document: {doc_path}, Working dir: {self.context_provider.working_dir}")
        window.append_message("System",
            f"✅ **All Checks Passed!**\n\n"
            f"📄 Document: `{os.path.basename(doc_path)}`\n"
            f"📂 Working directory: `{self.context_provider.working_dir}`\n\n"
            f"You can now start chatting with the AI!")
        self.status = "ready"
        return "ready"

    def handle_directory_mismatch(self, window: 'ForShapeMainWindow', user_input: str) -> bool:
        """
        Handle user response to directory mismatch.

        Args:
            window: The main window instance
            user_input: User's response (yes/no/cancel)

        Returns:
            True to continue checks, False to exit
        """
        try:
            import FreeCAD as App
        except ImportError:
            window.append_message("System", "❌ FreeCAD not available")
            return False

        response = user_input.strip().lower()

        if response == "cancel":
            window.append_message("System", "❌ Setup cancelled. You can close the window.")
            self.status = "error"
            return False
        elif response == "yes":
            doc_path = App.ActiveDocument.FileName if App.ActiveDocument else None
            if not doc_path:
                window.append_message("System", "⚠️ Document is no longer available. Please save it again.")
                return True

            doc_dir = os.path.dirname(os.path.abspath(doc_path))
            try:
                os.chdir(doc_dir)
                self.context_provider.working_dir = doc_dir
                self.logger.info(f"Changed working directory to: {doc_dir}")
                window.append_message("System",
                    f"✅ **Directory Changed**\n\n"
                    f"Working directory changed to: `{doc_dir}`\n\n"
                    f"Rechecking setup...")
                return True
            except Exception as e:
                window.append_message("System",
                    f"❌ **Error Changing Directory**\n\n"
                    f"Failed to change working directory: {str(e)}\n\n"
                    f"You can close the window.")
                self.status = "error"
                return False
        elif response == "no":
            window.append_message("System", "Continuing with current directory. Rechecking setup...")
            return True
        else:
            window.append_message("System", "⚠️ Please type 'yes', 'no', or 'cancel'")
            return True

    def get_status(self) -> Literal["waiting", "dir_mismatch", "ready", "error"]:
        """
        Get the current status of prestart checks.

        Returns:
            Current status
        """
        return self.status

    def is_ready(self) -> bool:
        """
        Check if prestart checks have passed.

        Returns:
            True if ready, False otherwise
        """
        return self.status == "ready"
