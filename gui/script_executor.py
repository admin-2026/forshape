"""
Script executor for running Python scripts in normal, teardown, or quick rebuild mode.

This module provides a unified interface for executing Python scripts with support for:
- Teardown mode (TEARDOWN_MODE flag) - removes objects before recreation
- Quick rebuild mode (QUICK_REBUILD_MODE flag) - skips construction if objects match
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
from enum import Enum


class ExecutionMode(Enum):
    """Execution mode for running scripts."""
    NORMAL = "normal"
    TEARDOWN = "teardown"
    QUICK_REBUILD = "quick_rebuild"


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
    """Executes Python scripts with support for teardown mode, quick rebuild mode, and output capture."""

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
        mode: ExecutionMode = ExecutionMode.NORMAL,
        import_freecad: bool = True
    ) -> ScriptExecutionResult:
        """
        Execute a Python script in the specified execution mode.

        Args:
            script_content: The script content to execute
            script_path: Path to the script file (for __file__ variable)
            mode: Execution mode (NORMAL, TEARDOWN, or QUICK_REBUILD)
            import_freecad: If True, import FreeCAD modules into execution namespace

        Returns:
            ScriptExecutionResult with success status, output, and error (if any)
        """
        # Set execution mode flags
        if mode == ExecutionMode.TEARDOWN:
            builtins.TEARDOWN_MODE = True
        elif mode == ExecutionMode.QUICK_REBUILD:
            builtins.QUICK_REBUILD_MODE = True

        # Add script's directory to sys.path so imports work
        script_dir = str(script_path.parent)
        path_added = False
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
            path_added = True

        # Track modules before execution to detect new imports
        modules_before = set(sys.modules.keys())

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
            # Remove imported modules from script directory to allow reloading
            # This ensures edited files are reloaded on next execution
            modules_after = set(sys.modules.keys())
            new_modules = modules_after - modules_before

            for module_name in new_modules:
                module = sys.modules.get(module_name)
                if module is not None and hasattr(module, '__file__') and module.__file__:
                    # Check if module is from the script's directory
                    module_path = Path(module.__file__).parent
                    if str(module_path) == script_dir:
                        del sys.modules[module_name]

            # Remove script directory from sys.path if we added it
            if path_added and script_dir in sys.path:
                sys.path.remove(script_dir)

            # Always reset mode flags
            if mode == ExecutionMode.TEARDOWN:
                builtins.TEARDOWN_MODE = False
            elif mode == ExecutionMode.QUICK_REBUILD:
                builtins.QUICK_REBUILD_MODE = False

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
            script_content, script_path, mode=ExecutionMode.TEARDOWN, import_freecad=import_freecad
        )

        # Run in normal mode
        normal_result = ScriptExecutor.execute(
            script_content, script_path, mode=ExecutionMode.NORMAL, import_freecad=import_freecad
        )

        return teardown_result, normal_result

    @staticmethod
    def execute_with_quick_rebuild(
        script_content: str,
        script_path: Path,
        import_freecad: bool = True
    ) -> ScriptExecutionResult:
        """
        Execute a script in quick rebuild mode.

        Quick rebuild mode skips construction if objects with matching labels and types exist.
        This is useful for fast iteration during development.

        Args:
            script_content: The script content to execute
            script_path: Path to the script file
            import_freecad: If True, import FreeCAD modules into execution namespace

        Returns:
            ScriptExecutionResult from quick rebuild execution
        """
        # Run in quick rebuild mode
        return ScriptExecutor.execute(
            script_content, script_path, mode=ExecutionMode.QUICK_REBUILD, import_freecad=import_freecad
        )
