"""
Script execution tools for AI Agent.

This module provides tools for executing Python scripts
in the FreeCAD environment.
"""

import json
from typing import Dict, List, Callable, Optional
from pathlib import Path

from agent.tools.base import ToolBase
from agent.permission_manager import PermissionManager
from gui.script_executor import ScriptExecutor


class ExecutionTools(ToolBase):
    """
    Script execution tools - injected into ToolManager.

    Provides: run_python_script
    """

    def __init__(
        self,
        working_dir: str,
        permission_manager: Optional[PermissionManager] = None
    ):
        """
        Initialize execution tools.

        Args:
            working_dir: Working directory for resolving script paths
            permission_manager: Optional permission manager for access control
        """
        self.working_dir = working_dir
        self.permission_manager = permission_manager

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_python_script",
                    "description": "Load and execute a Python script from the working directory. The script will be executed in the FreeCAD Python environment with access to FreeCAD modules and the Context class. Requires user permission before execution. Automatically runs in teardown mode first to clean up existing objects before running in normal mode.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "script_path": {
                                "type": "string",
                                "description": "The path to the Python script to execute. Can be relative to the working directory or absolute."
                            },
                            "description": {
                                "type": "string",
                                "description": "A brief description of what the script does (shown to user in permission request)."
                            }
                        },
                        "required": ["script_path", "description"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "run_python_script": self._tool_run_python_script,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for execution tools."""
        return """
### Script Execution Tools
1. **run_python_script** - Load and execute a Python script in the FreeCAD environment

### Script Execution Examples

**User says: "Run the box script"**
> Use run_python_script with script_path="box.py" and description="Creates a box shape"

**User says: "Execute my shape generator"**
> Use run_python_script with the appropriate script path and a description of what it does
"""

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the working directory."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            working_dir = Path(self.working_dir)
            path_obj = working_dir / path_obj
        return path_obj.resolve()

    def _check_permission(self, path: str, action: str, is_directory: bool = False) -> Optional[str]:
        """Check permission for a file/directory operation."""
        if self.permission_manager:
            if not self.permission_manager.request_permission(path, action, is_directory=is_directory):
                return json.dumps({
                    "error": f"Permission denied: {path}",
                    "permission_denied": True
                })
        return None

    def _validate_file_exists(self, path: Path) -> Optional[str]:
        """Validate that a file exists and is a file."""
        if not path.exists():
            return json.dumps({"error": f"File does not exist: {path}"})
        if not path.is_file():
            return json.dumps({"error": f"Path is not a file: {path}"})
        return None

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _tool_run_python_script(
        self,
        script_path: str,
        description: str,
        teardown_first: bool = True
    ) -> str:
        """
        Implementation of the run_python_script tool.
        Executes a Python script from the working directory with user permission.
        Always runs teardown first to clean up existing objects before normal execution.

        Args:
            script_path: Path to the Python script to execute
            description: Description of what the script does (for permission request)
            teardown_first: Internal parameter to control teardown behavior (defaults to True)

        Returns:
            JSON string with execution results or error message
        """
        try:
            resolved_path = self._resolve_path(script_path)

            # Validate that it's a Python file
            if not str(resolved_path).endswith('.py'):
                return self._json_error(f"File must be a Python script (.py): {resolved_path}")

            # Validate file exists
            file_error = self._validate_file_exists(resolved_path)
            if file_error:
                return file_error

            # Check permission
            perm_error = self._check_permission(str(resolved_path), "execute", is_directory=False)
            if perm_error:
                # Add description to permission error
                error_dict = json.loads(perm_error)
                error_dict["description"] = description
                return json.dumps(error_dict)

            # Read the script content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Execute the script using ScriptExecutor
            if teardown_first:
                # Run in teardown mode first, then normal mode
                teardown_result, normal_result = ScriptExecutor.execute_with_teardown(
                    script_content, resolved_path, import_freecad=True
                )
                success = normal_result.success
                output = normal_result.output
                error_msg = normal_result.error
                teardown_output = teardown_result.output
            else:
                # Run in normal mode only
                result = ScriptExecutor.execute(
                    script_content, resolved_path, teardown_mode=False, import_freecad=True
                )
                success = result.success
                output = result.output
                error_msg = result.error
                teardown_output = None

            if success:
                result = {
                    "success": True,
                    "script": str(resolved_path),
                    "description": description,
                    "output": output.strip() if output else "(no output)",
                    "message": "Script executed successfully"
                }
                if teardown_first and teardown_output is not None:
                    result["teardown_output"] = teardown_output.strip() if teardown_output else "(no teardown output)"
                    result["message"] = "Script executed successfully (with teardown first)"
                return json.dumps(result, indent=2)
            else:
                result = {
                    "success": False,
                    "script": str(resolved_path),
                    "description": description,
                    "error": error_msg,
                    "output": output.strip() if output else "(no output)"
                }
                if teardown_first and teardown_output is not None:
                    result["teardown_output"] = teardown_output.strip() if teardown_output else "(no teardown output)"
                return json.dumps(result, indent=2)

        except UnicodeDecodeError:
            return self._json_error(f"Cannot read script file (encoding issue): {script_path}")
        except Exception as e:
            return self._json_error(f"Error executing script: {str(e)}")
