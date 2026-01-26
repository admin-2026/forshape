"""
Tool Manager for AI Agent.

This module provides a tool manager that orchestrates tool registration
and execution. All tools are injected via register methods.
"""

import json
from typing import List, Dict, Callable, Any, Optional

from PySide2.QtCore import QObject, Signal

from .tools.base import ToolBase
from .logger_protocol import LoggerProtocol


class ToolManager(QObject):
    """
    Orchestrates tool registration and execution.

    All tools are injected via register methods:
    - register_provider() for general tool providers
    - register_interaction_tools() for interaction tools (with clarification support)
    """

    # Signal to request clarification dialog on the main thread
    # Emits: list of questions
    clarification_requested = Signal(list)

    def __init__(self, logger: LoggerProtocol):
        """
        Initialize the tool manager.

        Args:
            logger: LoggerProtocol instance for tool call logging
        """
        super().__init__()
        self.logger = logger

        # Tool provider storage
        self._tool_providers: List[ToolBase] = []
        self._tools: List[Dict] = []
        self._tool_functions: Dict[str, Callable[..., str]] = {}

        # Tool references (set via register methods)
        self._interaction_tools = None

    def register_provider(self, provider: ToolBase) -> None:
        """
        Register a tool provider.

        Args:
            provider: ToolBase instance to register
        """
        self._tool_providers.append(provider)
        self._tools.extend(provider.get_definitions())
        self._tool_functions.update(provider.get_functions())

        # Log registered tools
        tool_names = provider.get_names()
        self.logger.info(f"Registered tools: {', '.join(tool_names)}")

    def start_conversation(self, conversation_id: str, user_request: Optional[str] = None) -> None:
        """
        Start a new conversation with the given ID.

        Notifies all registered tool providers about the new conversation.

        Args:
            conversation_id: Unique conversation ID from AIAgent
            user_request: Optional user request text to store with this checkpoint
        """
        for provider in self._tool_providers:
            provider.start_conversation(conversation_id, user_request)

    def register_interaction_tools(self, interaction_tools: ToolBase) -> None:
        """
        Register interaction tools and store reference for clarification responses.

        Args:
            interaction_tools: InteractionTools instance
        """
        self._interaction_tools = interaction_tools
        self.register_provider(interaction_tools)

    def set_clarification_response(self, responses: Optional[Dict], cancelled: bool = False) -> None:
        """
        Set the clarification response from the main thread.

        This method should be called from the main GUI thread after the
        clarification dialog is closed.

        Args:
            responses: Dictionary of responses from the dialog, or None if cancelled
            cancelled: Whether the user cancelled the dialog
        """
        if self._interaction_tools is None:
            self.logger.warn("Interaction tools not registered, cannot set clarification response")
            return
        self._interaction_tools.set_clarification_response(responses, cancelled)

    def execute_tool(self, tool_name: str, tool_arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            tool_arguments: Arguments to pass to the tool

        Returns:
            Tool execution result as string
        """
        if tool_name not in self._tool_functions:
            error_msg = f"Unknown tool: {tool_name}"
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

        # Log the tool call
        args_str = ", ".join([f"{k}={repr(v)}" for k, v in tool_arguments.items()])
        self.logger.info(f"Tool call: {tool_name}({args_str})")

        tool_func = self._tool_functions[tool_name]
        try:
            result = tool_func(**tool_arguments)

            # Check if result contains an error
            try:
                result_dict = json.loads(result)
                if "error" in result_dict:
                    self.logger.warn(f"Tool {tool_name} failed: {result_dict['error']}")
            except (json.JSONDecodeError, TypeError):
                pass  # Result is not JSON, which is fine

            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            self.logger.error(f"Tool {tool_name} error: {error_msg}")
            return json.dumps({"error": error_msg})

    def get_tools(self) -> List[Dict]:
        """
        Get the tool definitions.

        Returns:
            List of tool definitions
        """
        return self._tools

    @property
    def tools(self) -> List[Dict]:
        """Alias for get_tools() for backward compatibility."""
        return self._tools

    @property
    def tool_functions(self) -> Dict[str, Callable[..., str]]:
        """Get the tool functions dictionary for backward compatibility."""
        return self._tool_functions

    @staticmethod
    def get_tool_usage_instructions() -> str:
        """
        Get comprehensive tool usage instructions for the AI agent.

        Returns:
            Formatted string with tool usage instructions
        """
        return """

## Available Tools

You have access to the following tools:

### File Management Tools
1. **list_files** - List files and directories in any folder
2. **read_file** - Read the contents of any file
3. **edit_file** - Edit files by replacing content
4. **search_python_files** - Search for regex patterns in Python files within the working directory

### FreeCAD Object Tools
6. **print_object** - Print information about a FreeCAD object by label or name
7. **find_objects_by_regex** - Find objects whose label, name, or label2 matches a regex pattern
8. **print_document** - Print information about all objects in the active document
9. **rename_object** - Rename a FreeCAD object by changing its Label property
10. **remove_object** - Remove a FreeCAD object from the document

### FreeCAD Visualization Tools
11. **capture_screenshot** - Capture screenshots of the FreeCAD 3D view from various perspectives

### User Interaction Tools
12. **ask_user_clarification** - Ask the user one or more clarification questions and collect their responses

### Working with Generated Scripts

When users ask you to generate or modify Python scripts for shapes:
1. You can use your tools to **directly update the generated script files**
2. You can read existing scripts to understand what's already been created
3. You can edit scripts to fix issues, add features, or improve code
4. Scripts are typically stored in the working directory or shapes folder

### Working with FreeCAD Objects

When users ask about objects in their FreeCAD document:
1. Use **print_document** to see all objects in the scene
2. Use **print_object** with verbose=true to get detailed information about specific objects
3. Use **find_objects_by_regex** to search for objects by name patterns

### Best Practices

- When a user reports an error in a generated script, **read the script first** to understand the issue
- After generating new code, you can **directly write or edit the script file** instead of just showing code
- Use **list_files** to explore the project structure when needed
- Always verify changes by reading the file after editing
- Use **find_objects_by_regex** to locate objects when you need to reference them by pattern

### Example Workflows

**User says: "Add a red sphere to the scene"**
→ Generate the code and either tell the user to save it, OR directly edit their current script file

**User says: "The script has an error on line 15"**
→ Read the script file, identify the issue, edit the file to fix it, confirm the fix

**User says: "What scripts have I created?"**
→ List files in the working directory to show them their generated scripts

**User says: "Show me all objects in the document"**
→ Use print_document with verbose=true to show the full object hierarchy

**User says: "Find all boxes in the scene"**
→ Use find_objects_by_regex with pattern like "box.*" or "Box.*"

**User says: "Rename the box to 'MainBox'"**
→ Use rename_object with obj_or_label="box" and new_label="MainBox"

**User says: "Delete the sphere" or "Remove the cylinder"**
→ Use remove_object with obj_or_label="sphere" or "cylinder"

**User says: "Find all files that import FreeCAD"**
→ Use search_python_files with pattern="import FreeCAD" or "from FreeCAD"

**User says: "Search for all functions that create boxes"**
→ Use search_python_files with pattern="def.*box" (case insensitive if needed)

**User says: "Find usages of the Context class"**
→ Use search_python_files with pattern="Context\\." to find all references

**User says: "Take a screenshot of the model"**
→ Use capture_screenshot (no parameters needed - auto-saves with timestamp)

**User says: "Capture the box from the front view"**
→ Use capture_screenshot with target="box", perspective="front"

**User says: "Take screenshots from multiple angles"**
→ Use capture_screenshot with perspectives=["front", "top", "isometric"]

**User says: "Show me what the object looks like"**
→ Use capture_screenshot to capture an image of the object and return the image

**User says: "Create a custom shape"**
→ Use ask_user_clarification with questions like ["What type of shape do you want?", "What dimensions should it have?", "What color would you like?"]

**AI Agent needs clarification:**
→ If the user's request is ambiguous or missing key information, use ask_user_clarification to gather the necessary details before proceeding

Use these tools proactively to provide a better user experience!"""
