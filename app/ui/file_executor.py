"""
Python file execution for ForShape AI GUI.

This module provides functionality for scanning, selecting, and executing
Python files in various modes (build, teardown, incremental build).
"""

import glob
import os
import sys
import traceback
from pathlib import Path

from PySide2.QtWidgets import QDialog

from ..dialogs import PythonFileSelector
from ..script_executor import ExecutionMode, ScriptExecutor


class FileExecutor:
    """Handles Python file scanning and execution."""

    def __init__(self, config, message_handler, logger):
        """
        Initialize the file executor.

        Args:
            config: ConfigurationManager instance for accessing working directory
            message_handler: MessageHandler instance for displaying messages
            logger: Logger instance
        """
        self.config = config
        self.message_handler = message_handler
        self.logger = logger

    def scan_python_files(self):
        """
        Scan the working directory for Python files.

        Returns:
            List of Python file paths relative to the working directory
        """
        python_files = []

        # Get working directory from context provider
        working_dir = self.config.working_dir

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

    def scan_runnable_python_files(self):
        """
        Scan the working directory for Python files that contain __main__.
        These are files that can be run independently.

        Returns:
            List of Python file paths relative to the working directory that contain __main__
        """
        runnable_files = []

        # Get working directory from context provider
        working_dir = self.config.working_dir

        # Find all .py files in the working directory (non-recursive)
        pattern = os.path.join(working_dir, "*.py")
        files = glob.glob(pattern)

        # Check each file for __main__
        for file_path in files:
            try:
                # Get the filename
                filename = os.path.basename(file_path)

                # Skip import.py and export.py (they will have separate buttons)
                if filename in ["import.py", "export.py"]:
                    continue

                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    # Check if the file contains __main__
                    if "__main__" in content:
                        rel_path = os.path.relpath(file_path, working_dir)
                        runnable_files.append(rel_path)
            except Exception as e:
                # Skip files that can't be read
                self.logger.debug(f"Could not read {file_path}: {e}")
                continue

        # Sort alphabetically
        runnable_files.sort()

        return runnable_files

    def _execute_python_file_with_mode(self, file_path, mode, action_name):
        """
        Generic helper to execute a Python file with a specific execution mode.

        Args:
            file_path: Path to the Python file to run
            mode: ExecutionMode enum value or 'with_teardown' for execute_with_teardown
            action_name: Action name for messages (e.g., "Teardown", "Incremental build", "Build")

        Returns:
            None
        """
        self.message_handler.append_message("[SYSTEM]", f"{action_name}: {file_path}")

        # Get absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            self.message_handler.display_error(f"File not found: {file_path}")
            return

        # Add project directory to sys.path if not already there
        project_dir = str(self.config.get_project_dir())
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        try:
            # Read the script content
            with open(abs_path, encoding="utf-8") as f:
                script_content = f.read()

            path_obj = Path(abs_path)

            # Execute based on mode
            if mode == "with_teardown":
                # Execute with teardown first, then normal
                teardown_result, normal_result = ScriptExecutor.execute_with_teardown(
                    script_content, path_obj, import_freecad=False
                )

                # Display teardown output if any
                if teardown_result.output.strip():
                    self.message_handler.append_message("[TEARDOWN OUTPUT]", teardown_result.output.strip())

                # Display normal execution output if any
                if normal_result.output.strip():
                    self.message_handler.append_message("[OUTPUT]", normal_result.output.strip())

                # Check results
                if teardown_result.success and normal_result.success:
                    self.message_handler.append_message(
                        "[SYSTEM]", f"{action_name} completed successfully: {file_path}"
                    )
                elif not teardown_result.success:
                    error_msg = f"Error during teardown of {file_path}:\n{teardown_result.error}"
                    self.message_handler.display_error(error_msg)
                else:
                    error_msg = f"Error running {file_path}:\n{normal_result.error}"
                    self.message_handler.display_error(error_msg)
            else:
                # Execute with specific mode
                result = ScriptExecutor.execute(script_content, path_obj, mode=mode, import_freecad=False)

                # Display output if any
                if result.output.strip():
                    self.message_handler.append_message("[OUTPUT]", result.output.strip())

                if result.success:
                    self.message_handler.append_message(
                        "[SYSTEM]", f"{action_name} completed successfully: {file_path}"
                    )
                else:
                    error_msg = f"Error during {action_name.lower()} of {file_path}:\n{result.error}"
                    self.message_handler.display_error(error_msg)

        except Exception:
            # Format and display the error
            error_msg = f"Error executing {file_path}:\n{traceback.format_exc()}"
            self.message_handler.display_error(error_msg)

    def run_python_file(self, file_path):
        """
        Run a Python file with teardown first, then normal execution.

        Args:
            file_path: Path to the Python file to run
        """
        self._execute_python_file_with_mode(file_path, "with_teardown", "Building (with teardown)")

    def redo_python_file(self, file_path):
        """
        Teardown a Python file - run the script in teardown mode to remove objects.

        Args:
            file_path: Path to the Python file to teardown
        """
        self._execute_python_file_with_mode(file_path, ExecutionMode.TEARDOWN, "Tearing down")

    def incremental_build_python_file(self, file_path):
        """
        Incremental build a Python file - run the script in incremental build mode.

        Args:
            file_path: Path to the Python file to run
        """
        self._execute_python_file_with_mode(file_path, ExecutionMode.INCREMENTAL_BUILD, "Incremental building")

    def on_run_script(self, parent_window):
        """
        Handle Rebuild button click.

        Args:
            parent_window: Parent window for the file selector dialog
        """
        # Scan for runnable Python files (files with __main__)
        python_files = self.scan_runnable_python_files()

        if not python_files:
            self.message_handler.append_message(
                "[SYSTEM]",
                "No runnable Python files found in the working directory.\n(Only files with __main__ are shown)",
            )
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, parent_window)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.run_python_file(selected_file)

    def on_redo_script(self, parent_window):
        """
        Handle Teardown button click.

        Args:
            parent_window: Parent window for the file selector dialog
        """
        # Scan for runnable Python files (files with __main__)
        python_files = self.scan_runnable_python_files()

        if not python_files:
            self.message_handler.append_message(
                "[SYSTEM]",
                "No runnable Python files found in the working directory.\n(Only files with __main__ are shown)",
            )
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, parent_window)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.redo_python_file(selected_file)

    def on_incremental_build_script(self, parent_window):
        """
        Handle Incremental Build button click.

        Args:
            parent_window: Parent window for the file selector dialog
        """
        # Scan for runnable Python files (files with __main__)
        python_files = self.scan_runnable_python_files()

        if not python_files:
            self.message_handler.append_message(
                "[SYSTEM]",
                "No runnable Python files found in the working directory.\n(Only files with __main__ are shown)",
            )
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, parent_window)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.incremental_build_python_file(selected_file)

    def on_export_clicked(self):
        """Handle Export button click - run export.py from the working directory."""
        # Get working directory from context provider
        working_dir = self.config.working_dir
        export_file = os.path.join(working_dir, "export.py")

        # Check if export.py exists
        if not os.path.exists(export_file):
            self.message_handler.append_message("[SYSTEM]", "export.py not found in the working directory.")
            return

        # Run the export script in normal mode
        self._execute_python_file_with_mode(export_file, ExecutionMode.NORMAL, "Exporting")

    def on_import_clicked(self):
        """Handle Import button click - run import.py from the working directory."""
        # Get working directory from context provider
        working_dir = self.config.working_dir
        import_file = os.path.join(working_dir, "import.py")

        # Check if import.py exists
        if not os.path.exists(import_file):
            self.message_handler.append_message("[SYSTEM]", "import.py not found in the working directory.")
            return

        # Run the import script in normal mode
        self._execute_python_file_with_mode(import_file, ExecutionMode.NORMAL, "Importing")
