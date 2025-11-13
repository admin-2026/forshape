"""
Dependency management for ForShape AI.

This module handles checking and installing required dependencies,
particularly the OpenAI library.
"""

import sys
import subprocess
from pathlib import Path
from PySide2.QtWidgets import QApplication, QMessageBox


class DependencyManager:
    """Manages dependency checking and installation for ForShape AI."""

    def __init__(self, local_lib_dir: Path):
        """
        Initialize the dependency manager.

        Args:
            local_lib_dir: Path to local library directory for installations
        """
        self.local_lib_dir = local_lib_dir
        self.openai_available = False
        self.markdown_available = False
        self.error_message = ""

    def check_and_install_openai(self) -> tuple[bool, str]:
        """
        Check if openai library is installed. If not, prompt user to install it locally.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        # Add local library directory to sys.path if it exists
        if self.local_lib_dir.exists() and str(self.local_lib_dir) not in sys.path:
            sys.path.insert(0, str(self.local_lib_dir))

        try:
            import openai
            self.openai_available = True
            self.error_message = ""
            return True, ""
        except ImportError:
            return self._prompt_and_install()

    def _prompt_and_install(self) -> tuple[bool, str]:
        """
        Prompt user to install OpenAI library and handle installation.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        # Create a minimal QApplication if it doesn't exist (needed for dialog)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Ask user if they want to install
        reply = QMessageBox.question(
            None,
            'OpenAI Library Not Found',
            'The OpenAI library is required but not installed.\n\n'
            'Would you like to install it now using pip?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            QMessageBox.information(
                None,
                'Installation Cancelled',
                'OpenAI library is required to run ForShape AI.\n\n'
                'Module will load but cannot be used.'
            )
            error_msg = "OpenAI library not installed. User declined installation."
            self.openai_available = False
            self.error_message = error_msg
            return False, error_msg

        # Try to install openai
        return self._install_openai()

    def _install_openai(self) -> tuple[bool, str]:
        """
        Install OpenAI library to local directory.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        try:
            QMessageBox.information(
                None,
                'Installing',
                f'Installing OpenAI library to:\n{self.local_lib_dir}\n\n'
                'This may take a moment. Click OK to continue.',
                QMessageBox.Ok
            )

            # Create the libs subdirectory if it doesn't exist
            self.local_lib_dir.mkdir(parents=True, exist_ok=True)

            # Install openai to the libs subdirectory using pip with --target flag
            subprocess.check_call(['pip', 'install', '--target', str(self.local_lib_dir), 'openai'])

            # Add the local library directory to sys.path
            if str(self.local_lib_dir) not in sys.path:
                sys.path.insert(0, str(self.local_lib_dir))

            QMessageBox.information(
                None,
                'Installation Complete',
                f'OpenAI library has been successfully installed!\n\n'
                f'Location: {self.local_lib_dir}\n\n'
                'The application will now start.',
                QMessageBox.Ok
            )

            self.openai_available = True
            self.error_message = ""
            return True, ""

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install OpenAI library: {str(e)}"
            QMessageBox.critical(
                None,
                'Installation Failed',
                f'{error_msg}\n\n'
                f'Please install manually using:\npip install --target {self.local_lib_dir} openai',
                QMessageBox.Ok
            )
            self.openai_available = False
            self.error_message = error_msg
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during installation: {str(e)}"
            QMessageBox.critical(
                None,
                'Installation Error',
                f'{error_msg}\n\n'
                f'Please install manually using:\npip install --target {self.local_lib_dir} openai',
                QMessageBox.Ok
            )
            self.openai_available = False
            self.error_message = error_msg
            return False, error_msg

    def check_and_install_markdown(self) -> tuple[bool, str]:
        """
        Check if markdown library is installed. If not, attempt to install it locally.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        # Add local library directory to sys.path if it exists
        if self.local_lib_dir.exists() and str(self.local_lib_dir) not in sys.path:
            sys.path.insert(0, str(self.local_lib_dir))

        try:
            import markdown
            self.markdown_available = True
            return True, ""
        except ImportError:
            return self._install_markdown()

    def _install_markdown(self) -> tuple[bool, str]:
        """
        Install markdown library to local directory without prompting.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        try:
            # Create the libs subdirectory if it doesn't exist
            self.local_lib_dir.mkdir(parents=True, exist_ok=True)

            # Install markdown to the libs subdirectory using pip with --target flag
            subprocess.check_call(['pip', 'install', '--target', str(self.local_lib_dir), 'markdown'])

            # Add the local library directory to sys.path
            if str(self.local_lib_dir) not in sys.path:
                sys.path.insert(0, str(self.local_lib_dir))

            self.markdown_available = True
            return True, ""

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install markdown library: {str(e)}"
            self.markdown_available = False
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during markdown installation: {str(e)}"
            self.markdown_available = False
            return False, error_msg

    def is_openai_available(self) -> bool:
        """
        Check if OpenAI library is available.

        Returns:
            bool: True if OpenAI is available, False otherwise
        """
        return self.openai_available

    def is_markdown_available(self) -> bool:
        """
        Check if markdown library is available.

        Returns:
            bool: True if markdown is available, False otherwise
        """
        return self.markdown_available

    def get_error_message(self) -> str:
        """
        Get the error message if OpenAI is not available.

        Returns:
            str: Error message
        """
        return self.error_message
