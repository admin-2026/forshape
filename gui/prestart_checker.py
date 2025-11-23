"""
Prestart checker for FreeCAD document validation and configuration setup.

This module provides functionality to check and setup:
- .forshape directory and configuration files
- OpenAI API key
- FreeCAD active document
- Working directory configuration
"""

import os
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from .main_window import ForShapeMainWindow
    from .context_provider import ContextProvider
    from .config_manager import ConfigurationManager
    from .logger import Logger


class PrestartChecker:
    """Handles prestart checks for configuration setup and FreeCAD document validation."""

    def __init__(self, context_provider: 'ContextProvider', config_manager: 'ConfigurationManager', logger: 'Logger'):
        """
        Initialize the prestart checker.

        Args:
            context_provider: Context provider for working directory management
            config_manager: Configuration manager for directory and API key management
            logger: Logger instance for logging check results
        """
        self.context_provider = context_provider
        self.config_manager = config_manager
        self.logger = logger
        self.status: Literal["waiting", "dir_mismatch", "ready", "error", "need_api_key"] = "waiting"
        self.api_key: Optional[str] = None

    def check(self, window: 'ForShapeMainWindow') -> Literal["waiting", "dir_mismatch", "ready", "error", "need_api_key"]:
        """
        Check configuration setup and FreeCAD document status.

        Performs checks in order:
        1. FreeCAD module availability
        2. Active document existence
        3. Document saved status
        4. Working directory match
        5. .forshape directory setup (in document's directory)
        6. API key availability

        Uses chatbox for interaction instead of modal dialogs so user can interact with FreeCAD.

        Args:
            window: The main window instance to display messages

        Returns:
            Status string: "ready" if all checks passed, "waiting" if waiting for user action,
                          "dir_mismatch" if directory needs confirmation, "need_api_key" if API key missing,
                          "error" if fatal error
        """
        # Check 1: FreeCAD availability
        try:
            import FreeCAD as App
        except ImportError:
            window.append_message("System",
                "❌ **FreeCAD Not Available**\n\n"
                "FreeCAD module could not be imported. Please run this from FreeCAD's Python console.")
            self.status = "error"
            return "error"

        # Check 2: Is there an active document?
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

        # Check 3: Is the document saved?
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

        # Check 4: Does the working directory match the document's directory?
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

        # At this point, working directory is correct
        # Check 5: Setup .forshape directory (now that we know the correct location)
        if not self._check_and_setup_directories(window):
            self.status = "error"
            return "error"

        # Check 6: API key availability
        provider_config = self.config_manager.get_provider_config()
        providers = provider_config.get("providers", {})
        self.api_key = providers.get("openai")

        if not self.api_key:
            config_file = self.config_manager.provider_config_file
            window.append_message("System",
                "⚠️ **OpenAI API Key Not Found**\n\n"
                f"No OpenAI API key was found in {config_file.name}. The AI features require an API key to function.\n\n"
                "**To add your API key:**\n"
                f"1. Create or edit: `{config_file}`\n"
                "2. Add your OpenAI API key in JSON format:\n"
                "```json\n"
                "{\n"
                '  "providers": {\n'
                '    "openai": "sk-proj-YOUR_KEY_HERE"\n'
                "  }\n"
                "}\n"
                "```\n\n"
                "**After adding the API key:**\n"
                "• Type anything (e.g., 'ready') to continue\n\n"
                "**Don't have an API key?**\n"
                "• Get one at: https://platform.openai.com/api-keys")
            self.status = "need_api_key"
            return "need_api_key"

        # All checks passed
        self.logger.info(f"Prestart checks passed. Document: {doc_path}, Working dir: {self.context_provider.working_dir}, API key: {'present' if self.api_key else 'missing'}")
        window.append_message("System",
            f"✅ **All Checks Passed!**\n\n"
            f"📄 Document: `{os.path.basename(doc_path)}`\n"
            f"📂 Working directory: `{self.context_provider.working_dir}`\n"
            f"🔑 API key: Configured\n\n"
            f"You can now start chatting with the AI!")
        self.status = "ready"
        return "ready"

    def _check_and_setup_directories(self, window: 'ForShapeMainWindow') -> bool:
        """
        Check and setup configuration directories and files.

        Args:
            window: The main window instance to display messages

        Returns:
            True if successful, False on error
        """
        try:
            # Use config_manager to setup directories
            created_items = self.config_manager.setup_directories()

            # Log what was created
            for item in created_items:
                self.logger.info(f"Setup: {item}")

            # Show what was created if anything
            if created_items:
                window.append_message("System",
                    "✅ **Configuration Setup**\n\n" +
                    "\n".join(created_items))

            return True

        except Exception as e:
            window.append_message("System",
                f"❌ **Configuration Setup Failed**\n\n"
                f"Failed to create configuration directories:\n{str(e)}")
            self.logger.error(f"Failed to setup directories: {e}")
            return False

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

                # Update config manager with new working directory
                self.config_manager.update_working_directory(doc_dir)

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
            # User wants to keep current directory - update config manager to use current dir
            current_dir = self.context_provider.working_dir
            self.config_manager.update_working_directory(current_dir)

            window.append_message("System", "Continuing with current directory. Rechecking setup...")
            return True
        else:
            window.append_message("System", "⚠️ Please type 'yes', 'no', or 'cancel'")
            return True

    def get_status(self) -> Literal["waiting", "dir_mismatch", "ready", "error", "need_api_key"]:
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

    def get_api_key(self) -> Optional[str]:
        """
        Get the API key after checks have passed.

        Returns:
            API key if available, None otherwise
        """
        return self.api_key
