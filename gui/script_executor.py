"""
Script executor for running Python scripts in normal or teardown mode.

This module provides a unified interface for executing Python scripts with support for:
- Teardown mode (TEARDOWN_MODE flag)
- Output capture (stdout/stderr)
- FreeCAD module imports
- Proper cleanup and error handling
"""

import sys
import io
import builtins
import traceback
from pathlib import Path
from typing import Tuple, Optional
from contextlib import contextmanager


class ScriptExecutionResult:
    """Result of a script execution."""

    def __init__(self, success: bool, output: str, error: Optional[str] = None):
        """
        Initialize script execution result.

        Args:
            success: Whether the script executed successfully
            output: Captured stdout/stderr output
            error: Error message if execution failed
        """
        self.success = success
        self.output = output
        self.error = error


class ScriptExecutor:
    """Executes Python scripts with support for teardown mode and output capture."""

    @staticmethod
    @contextmanager
    def _capture_output():
        """
        Context manager for capturing stdout and stderr.

        Yields:
            A function that returns the captured output as a string
        """
        captured = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = captured
            sys.stderr = captured
            yield lambda: captured.getvalue()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    @staticmethod
    def execute(
        script_content: str,
        script_path: Path,
        teardown_mode: bool = False,
        import_freecad: bool = True
    ) -> ScriptExecutionResult:
        """
        Execute a Python script in either normal or teardown mode.

        Args:
            script_content: The script content to execute
            script_path: Path to the script file (for __file__ variable)
            teardown_mode: If True, set TEARDOWN_MODE before execution
            import_freecad: If True, import FreeCAD modules into execution namespace

        Returns:
            ScriptExecutionResult with success status, output, and error (if any)
        """
        # Set teardown mode if requested
        if teardown_mode:
            builtins.TEARDOWN_MODE = True

        try:
            # Create execution namespace
            exec_globals = {
                '__name__': '__main__',
                '__file__': str(script_path),
            }

            # Import FreeCAD modules if requested
            if import_freecad:
                try:
                    import FreeCAD
                    import FreeCADGui
                    from shapes.context import Context
                    exec_globals['FreeCAD'] = FreeCAD
                    exec_globals['FreeCADGui'] = FreeCADGui
                    exec_globals['Context'] = Context
                    exec_globals['App'] = FreeCAD
                    exec_globals['Gui'] = FreeCADGui
                except ImportError:
                    # FreeCAD modules might not be available in all environments
                    pass

            success = True
            error_msg = None

            # Execute the script with output capture
            with ScriptExecutor._capture_output() as get_output:
                try:
                    exec(script_content, exec_globals)
                except Exception as e:
                    success = False
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    error_msg += f"\n\nTraceback:\n{traceback.format_exc()}"

                output = get_output()

            return ScriptExecutionResult(success, output, error_msg)

        finally:
            # Always reset TEARDOWN_MODE if it was set
            if teardown_mode:
                builtins.TEARDOWN_MODE = False

    @staticmethod
    def execute_with_teardown(
        script_content: str,
        script_path: Path,
        import_freecad: bool = True
    ) -> Tuple[ScriptExecutionResult, ScriptExecutionResult]:
        """
        Execute a script in teardown mode first, then in normal mode.

        Args:
            script_content: The script content to execute
            script_path: Path to the script file
            import_freecad: If True, import FreeCAD modules into execution namespace

        Returns:
            Tuple of (teardown_result, normal_result)
        """
        # Run in teardown mode first
        teardown_result = ScriptExecutor.execute(
            script_content, script_path, teardown_mode=True, import_freecad=import_freecad
        )

        # Run in normal mode
        normal_result = ScriptExecutor.execute(
            script_content, script_path, teardown_mode=False, import_freecad=import_freecad
        )

        return teardown_result, normal_result
