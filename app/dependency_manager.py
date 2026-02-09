"""
Dependency management for ForShape AI.

This module handles checking and installing required dependencies,
particularly the OpenAI library.
"""

import subprocess
import sys
from pathlib import Path

from PySide2.QtWidgets import QApplication, QMessageBox


class DependencyManager:
    """Manages dependency checking and installation for ForShape AI."""

    # Configuration for all dependencies
    DEPENDENCIES = {
        "openai": {
            "prompt_before_install": True,
        },
        "markdown": {
            "prompt_before_install": False,
        },
        "keyring": {
            "prompt_before_install": False,
        },
        "ruff": {
            "prompt_before_install": False,
        },
    }

    def __init__(self, local_lib_dir: Path):
        """
        Initialize the dependency manager.

        Args:
            local_lib_dir: Path to local library directory for installations
        """
        self.local_lib_dir = local_lib_dir
        self.available = {pkg: False for pkg in self.DEPENDENCIES}
        self.error_message = ""

    def check_and_install_all(self) -> tuple[bool, str]:
        """
        Check all dependencies and install any that are missing.

        This method checks all configured dependencies and prompts the user
        to install any missing packages in a single batch.

        Returns:
            tuple: (success: bool, error_message: str)
        """
        # Add local library directory to sys.path if it exists
        if self.local_lib_dir.exists() and str(self.local_lib_dir) not in sys.path:
            sys.path.insert(0, str(self.local_lib_dir))

        # Check which packages are missing
        missing_packages = []
        for package_name in self.DEPENDENCIES:
            try:
                __import__(package_name)
                self.available[package_name] = True
            except ImportError:
                missing_packages.append(package_name)

        # If no packages are missing, return success
        if not missing_packages:
            return True, ""

        # Determine if any missing package requires prompting
        requires_prompt = any(self.DEPENDENCIES[pkg].get("prompt_before_install", False) for pkg in missing_packages)

        if requires_prompt:
            return self._prompt_and_install_all(missing_packages)
        else:
            # Install without prompting
            return self._install_all_packages(missing_packages)

    def _prompt_and_install_all(self, missing_packages: list[str]) -> tuple[bool, str]:
        """
        Prompt user to install all missing packages.

        Args:
            missing_packages: List of package names to install

        Returns:
            tuple: (success: bool, error_message: str)
        """
        # Create a minimal QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Build message listing missing packages
        packages_list = "\n".join(f"  - {pkg}" for pkg in missing_packages)
        message = (
            f"The following required libraries are not installed:\n\n"
            f"{packages_list}\n\n"
            f"Would you like to install them now using pip?"
        )

        # Ask user if they want to install
        reply = QMessageBox.question(
            None, "Required Libraries Not Found", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            QMessageBox.information(
                None,
                "Installation Cancelled",
                "Some required libraries are not installed.\n\nThe application will not load.",
            )
            error_msg = "Required libraries not installed. User declined installation."
            for pkg in missing_packages:
                self.available[pkg] = False
            self.error_message = error_msg
            return False, error_msg

        # Show installing message
        QMessageBox.information(
            None,
            "Installing",
            f"Installing required libraries to:\n{self.local_lib_dir}\n\nThis may take a moment. Click OK to continue.",
            QMessageBox.Ok,
        )

        # Install all missing packages
        success, error_msg = self._install_all_packages(missing_packages)

        if success:
            QMessageBox.information(
                None,
                "Installation Complete",
                f"All required libraries have been successfully installed!\n\n"
                f"Location: {self.local_lib_dir}\n\n"
                "The application will now start.",
                QMessageBox.Ok,
            )
        else:
            QMessageBox.critical(
                None, "Installation Failed", f"{error_msg}\n\nPlease try installing manually.", QMessageBox.Ok
            )

        return success, error_msg

    def _install_all_packages(self, package_names: list[str]) -> tuple[bool, str]:
        """
        Install multiple packages to local directory.

        Args:
            package_names: List of package names to install

        Returns:
            tuple: (success: bool, error_message: str)
        """
        failed_packages = []

        for package_name in package_names:
            success, error_msg = self._install_package(package_name)
            if not success:
                failed_packages.append((package_name, error_msg))

        if failed_packages:
            failed_list = "\n".join(f"  - {pkg}: {err}" for pkg, err in failed_packages)
            error_msg = f"Failed to install some packages:\n{failed_list}"
            self.error_message = error_msg
            return False, error_msg

        return True, ""

    def check_and_install(self, package_name: str) -> tuple[bool, str]:
        """
        Check if a package is installed. If not, attempt to install it.

        Args:
            package_name: Name of the package to check and install

        Returns:
            tuple: (success: bool, error_message: str)
        """
        if package_name not in self.DEPENDENCIES:
            error_msg = f"Unknown package: {package_name}"
            return False, error_msg

        # Add local library directory to sys.path if it exists
        if self.local_lib_dir.exists() and str(self.local_lib_dir) not in sys.path:
            sys.path.insert(0, str(self.local_lib_dir))

        try:
            __import__(package_name)
            self.available[package_name] = True
            self.error_message = ""
            return True, ""
        except ImportError:
            config = self.DEPENDENCIES[package_name]
            if config.get("prompt_before_install", False):
                return self._prompt_and_install_single(package_name, config)
            else:
                return self._install_package(package_name)

    def _prompt_and_install_single(self, package_name: str, config: dict) -> tuple[bool, str]:
        """
        Prompt user to install a single package.

        Args:
            package_name: Name of the package to install
            config: Configuration dict for the package

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
            f"{package_name.title()} Library Not Found",
            f"The {package_name} library is required but not installed.\n\nWould you like to install it now using pip?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.No:
            error_msg = f"{package_name} library not installed. User declined installation."
            self.available[package_name] = False
            self.error_message = error_msg
            return False, error_msg

        # Show installing message
        QMessageBox.information(
            None,
            "Installing",
            f"Installing {package_name} library to:\n{self.local_lib_dir}\n\n"
            "This may take a moment. Click OK to continue.",
            QMessageBox.Ok,
        )

        # Try to install
        success, error_msg = self._install_package(package_name)

        # Show result message
        if success:
            QMessageBox.information(
                None,
                "Installation Complete",
                f"{package_name} library has been successfully installed!\n\n"
                f"Location: {self.local_lib_dir}\n\n"
                "The application will now continue.",
                QMessageBox.Ok,
            )
        else:
            QMessageBox.critical(
                None,
                "Installation Failed",
                f"{error_msg}\n\n"
                f"Please install manually using:\npip install --target {self.local_lib_dir} {package_name}",
                QMessageBox.Ok,
            )

        return success, error_msg

    def _install_package(self, package_name: str) -> tuple[bool, str]:
        """
        Install a package to local directory.

        Args:
            package_name: Name of the package to install

        Returns:
            tuple: (success: bool, error_message: str)
        """
        try:
            # Create the libs subdirectory if it doesn't exist
            self.local_lib_dir.mkdir(parents=True, exist_ok=True)

            # Install package to the libs subdirectory using pip with --target flag
            subprocess.check_call(["pip", "install", "--target", str(self.local_lib_dir), package_name])

            # Add the local library directory to sys.path
            if str(self.local_lib_dir) not in sys.path:
                sys.path.insert(0, str(self.local_lib_dir))

            self.available[package_name] = True
            return True, ""

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install {package_name} library: {str(e)}"
            self.available[package_name] = False
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error during {package_name} installation: {str(e)}"
            self.available[package_name] = False
            return False, error_msg

    def is_available(self, package_name: str) -> bool:
        """
        Check if a package is available.

        Args:
            package_name: Name of the package to check

        Returns:
            bool: True if package is available, False otherwise
        """
        return self.available.get(package_name, False)

    def get_error_message(self) -> str:
        """
        Get the error message if a package is not available.

        Returns:
            str: Error message
        """
        return self.error_message
