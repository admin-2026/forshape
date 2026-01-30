"""
Tool Call Simulator for AI Agent.

This module provides a meta-tool that simulates an LLM making a tool call.
It allows calling other registered tools programmatically.
"""

import json
from typing import Dict, List, Callable, Any, Optional


from .base import ToolBase


class ToolCallTools(ToolBase):
    """
    Tool Call Simulator.

    Provides a meta-tool that can invoke other registered tools,
    simulating how an LLM would make tool calls.
    """

    def __init__(self):
        """Initialize the tool call simulator."""
        self._tool_manager = None

    def set_tool_manager(self, tool_manager: Any) -> None:
        """
        Set the tool manager reference for executing tools.

        Args:
            tool_manager: ToolManager instance to use for tool execution
        """
        self._tool_manager = tool_manager

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        definition = [
            {
                "type": "function",
                "function": {
                    "name": "ToolCall",
                    "description": "Simulate an LLM tool call by invoking another registered tool. Use this to programmatically call any available tool with specified arguments.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tool_name": {
                                "type": "string",
                                "description": "The name of the tool to call (e.g., 'calculate', 'read_file')."
                            },
                            "tool_arguments": {
                                "type": "object",
                                "description": "The arguments to pass to the tool as a JSON object. Example: {\"expression\": \"2 + 3\"} for calculate tool."
                            }
                        },
                        "required": ["tool_name", "tool_arguments"]
                    }
                }
            }
        ]
        # The ToolCallTools is a metatool which is not for LLM, hide it from LLM but
        # still let ToolManager be able to call it, if correct args are provided.
        definition = []
        return definition

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "ToolCall": self._tool_call_tool,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for tool call simulator."""
        instruction = """
### Tool Call Simulator
1. **ToolCall** - Invoke another registered tool programmatically

### Usage
This meta-tool allows you to call other tools by specifying:
- `tool_name`: The name of the tool to invoke
- `tool_arguments`: A JSON object containing the arguments for that tool

### Examples

**Call the calculate tool:**
> Use ToolCall with tool_name="calculate", tool_arguments={"expression": "2 + 3 * 4"}

**Call a file tool:**
> Use ToolCall with tool_name="read_file", tool_arguments={"file_path": "example.txt"}
"""
        # The ToolCallTools is a metatool which is not for LLM, hide it from LLM but
        # still let ToolManager be able to call it, if correct args are provided.
        instruction = ""
        return instruction

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(self, tool_name: str, tool_result: Any) -> str:
        """Create a JSON success response."""
        # Try to parse the tool result if it's JSON
        parsed_result = tool_result
        if isinstance(tool_result, str):
            try:
                parsed_result = json.loads(tool_result)
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as string if not valid JSON

        response = {
            "success": True,
            "tool_called": tool_name,
            "result": parsed_result
        }
        return json.dumps(response, indent=2)

    def _tool_call_tool(self, tool_name: str, tool_arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Implementation of the ToolCall meta-tool.
        Invokes another registered tool with the specified arguments.

        Args:
            tool_name: The name of the tool to call
            tool_arguments: Arguments to pass to the tool (default: empty dict)

        Returns:
            JSON string with result or error message
        """
        try:
            # Validate tool_name is provided
            if not tool_name or not isinstance(tool_name, str):
                return self._json_error("tool_name must be a non-empty string")

            tool_name = tool_name.strip()
            if not tool_name:
                return self._json_error("tool_name cannot be empty")

            # Prevent recursive calls to ToolCall
            if tool_name == "ToolCall":
                return self._json_error("Cannot recursively call ToolCall")

            # Default to empty dict if no arguments provided
            if tool_arguments is None:
                tool_arguments = {}

            # Validate tool_arguments is a dict
            if not isinstance(tool_arguments, dict):
                return self._json_error(
                    "tool_arguments must be a JSON object",
                    received_type=type(tool_arguments).__name__
                )

            # Check if tool manager is available
            if self._tool_manager is None:
                return self._json_error(
                    "Tool manager not configured. Cannot execute tools."
                )

            # Check if the tool exists
            if tool_name not in self._tool_manager.tool_functions:
                available_tools = list(self._tool_manager.tool_functions.keys())
                # Remove ToolCall from the list to avoid confusion
                if "ToolCall" in available_tools:
                    available_tools.remove("ToolCall")
                return self._json_error(
                    f"Unknown tool: {tool_name}",
                    available_tools=available_tools
                )

            # Execute the tool
            result = self._tool_manager.execute_tool(tool_name, tool_arguments)

            return self._json_success(tool_name, result)

        except Exception as e:
            return self._json_error(
                f"Error calling tool: {str(e)}",
                tool_name=tool_name
            )
