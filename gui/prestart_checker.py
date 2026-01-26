"""
Prestart checker for FreeCAD document validation and configuration setup.

This module provides functionality to check and setup:
- .forshape directory and configuration files
- API key for at least one configured provider
- FreeCAD active document
- Working directory configuration
- Template files (constants.py, main.py, export.py, import.py)
"""

import os
import shutil
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from .main_window import ForShapeMainWindow
    from agent.context_provider import ContextProvider
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
        6. API key availability for at least one configured provider

        Uses chatbox for interaction instead of modal dialogs so user can interact with FreeCAD.

        Args:
            window: The main window instance to display messages

        Returns:
            Status string: "ready" if all checks passed, "waiting" if waiting for user action,
                          "dir_mismatch" if directory needs confirmation, "need_api_key" if no API keys configured,
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

        # Check 6: API key availability for all configured providers
        from agent.api_key_manager import ApiKeyManager
        from agent.provider_config_loader import ProviderConfigLoader

        api_key_manager = ApiKeyManager()
        provider_loader = ProviderConfigLoader()

        # Get all configured providers
        configured_providers = provider_loader.get_providers()

        if not configured_providers:
            window.append_message("System",
                "⚠️ **No Providers Configured**\n\n"
                "No API providers found in provider-config.json. Please check your configuration.")
            self.status = "error"
            return "error"

        # Check API keys for each configured provider
        provider_info = {}
        providers_with_keys = []

        for provider in configured_providers:
            api_key = api_key_manager.get_api_key(provider.name)
            provider_info[provider.name] = {
                "display_name": provider.display_name,
                "has_key": api_key is not None
            }
            if api_key:
                providers_with_keys.append(provider.name)

        # Check if at least one provider has an API key
        if not providers_with_keys:
            message_lines = ["⚠️ **Missing API Keys**\n"]
            message_lines.append("No API keys are configured for any provider.\n")
            message_lines.append("\n**Available providers:**")

            for provider_name, info in provider_info.items():
                display_name = info["display_name"]
                message_lines.append(f"• **{display_name}** (`{provider_name}`)")

            message_lines.append("\n**To add an API key:**")
            message_lines.append("• Go to **Model menu** → **Add API Key** to configure at least one API key\n")
            message_lines.append("**After adding an API key:**")
            message_lines.append("• Type anything (e.g., 'ready') to continue")

            window.append_message("System", "\n".join(message_lines))
            self.status = "need_api_key"
            return "need_api_key"

        # Store the first available provider's API key
        self.api_key = api_key_manager.get_api_key(providers_with_keys[0])

        # All checks passed
        configured_keys = [f"{provider_info[p]['display_name']}" for p in provider_info if provider_info[p]['has_key']]
        self.logger.info(f"Prestart checks passed. Document: {doc_path}, Working dir: {self.context_provider.working_dir}, API keys: {', '.join(configured_keys)}")

        keys_message = ", ".join(configured_keys) if configured_keys else "None"
        window.append_message("System",
            f"✅ **All Checks Passed!**\n\n"
            f"📄 Document: `{os.path.basename(doc_path)}`\n"
            f"📂 Working directory: `{self.context_provider.working_dir}`\n"
            f"🔑 API keys configured: {keys_message}\n\n"
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

            # Copy template files to working directory if they don't exist
            self._setup_template_files(window)

            return True

        except Exception as e:
            window.append_message("System",
                f"❌ **Configuration Setup Failed**\n\n"
                f"Failed to create configuration directories:\n{str(e)}")
            self.logger.error(f"Failed to setup directories: {e}")
            return False

    def _setup_template_files(self, window: 'ForShapeMainWindow') -> None:
        """
        Copy template files to the working directory if they don't exist.

        Template files: constants.py, main.py, export.py, import.py

        Args:
            window: The main window instance to display messages
        """
        # Get the templates directory path (relative to this module)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(module_dir, 'templates')

        # Template files to copy
        template_files = ['constants.py', 'main.py', 'export.py', 'import.py']

        copied_files = []

        for filename in template_files:
            # Source: template file in gui/templates/
            source_path = os.path.join(templates_dir, filename)

            # Destination: working directory
            dest_path = os.path.join(self.context_provider.working_dir, filename)

            # Check if file already exists in working directory
            if os.path.exists(dest_path):
                self.logger.info(f"Template file already exists: {filename}")
                continue

            # Check if template source exists
            if not os.path.exists(source_path):
                self.logger.warning(f"Template source not found: {source_path}")
                continue

            # Copy the template file
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(filename)
                self.logger.info(f"Copied template file: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to copy template file {filename}: {e}")

        # Inform user if any files were copied
        if copied_files:
            files_list = "\n".join([f"• {f}" for f in copied_files])
            window.append_message("System",
                f"✅ **Template Files Created**\n\n"
                f"The following template files have been created in your working directory:\n"
                f"{files_list}\n\n"
                f"You can now customize these files for your project.")

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
