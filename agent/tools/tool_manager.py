"""
Tool Manager for AI Agent.

This module provides a tool manager that orchestrates tool registration
and execution. All tools are injected via register_provider().
"""

import json
from typing import Any, Callable, Optional

from ..logger_protocol import LoggerProtocol
from .base import ToolBase


class ToolManager:
    """
    Orchestrates tool registration and execution.

    All tools are injected via register_provider().
    No GUI-specific code - user interaction is handled by UserInputWaiter.
    """

    def __init__(self, logger: LoggerProtocol):
        """
        Initialize the tool manager.

        Args:
            logger: LoggerProtocol instance for tool call logging
        """
        self.logger = logger

        # Tool provider storage
        self._tool_providers: list[ToolBase] = []
        self._tools: list[dict] = []
        self._tool_functions: dict[str, Callable[..., str]] = {}
        self._tool_to_provider: dict[str, ToolBase] = {}

    def register_provider(self, provider: ToolBase) -> None:
        """
        Register a tool provider.

        Args:
            provider: ToolBase instance to register
        """
        self._tool_providers.append(provider)
        self._tools.extend(provider.get_definitions())
        self._tool_functions.update(provider.get_functions())

        # Map each tool name to its provider
        tool_names = provider.get_names()
        for tool_name in tool_names:
            self._tool_to_provider[tool_name] = provider

        # Log registered tools
        self.logger.info(f"Registered tools: {', '.join(tool_names)}")

    def execute_tool(self, tool_name: str, tool_arguments: dict[str, Any]) -> str:
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

    def get_tools(self) -> list[dict]:
        """
        Get the tool definitions.

        Returns:
            List of tool definitions
        """
        return self._tools

    @property
    def tools(self) -> list[dict]:
        """Alias for get_tools() for backward compatibility."""
        return self._tools

    @property
    def tool_functions(self) -> dict[str, Callable[..., str]]:
        """Get the tool functions dictionary for backward compatibility."""
        return self._tool_functions

    def get_provider(self, tool_name: str) -> Optional[ToolBase]:
        """
        Get the provider for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolBase instance that provides this tool, or None if not found
        """
        return self._tool_to_provider.get(tool_name)

    def get_tool_usage_instructions(self) -> str:
        """
        Get comprehensive tool usage instructions for the AI agent.

        Assembles instructions from all registered tool providers.

        Returns:
            Formatted string with tool usage instructions
        """
        # Collect instructions from all registered providers
        provider_instructions = []
        for provider in self._tool_providers:
            instructions = provider.get_tool_instructions()
            if instructions and instructions.strip():
                provider_instructions.append(instructions.strip())

        # Build the complete instructions
        parts = [
            "\n## Available Tools\n",
            "You have access to the following tools:\n",
            "Use these tools proactively to provide a better user experience!\n",
        ]

        # Add provider-specific instructions
        if provider_instructions:
            parts.append("\n".join(provider_instructions))

        return "\n".join(parts)
