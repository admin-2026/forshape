"""
Tool Executor for shared tool execution logic.

This module provides a ToolExecutor class that encapsulates the logic for
executing tool calls and processing their results. Used by both Step and
ToolCallStep to avoid code duplication.
"""

import json
from typing import List, Dict, Optional, Any, Callable, Tuple

from ..tools.tool_manager import ToolManager
from ..api_debugger import APIDebugger
from ..logger_protocol import LoggerProtocol
from ..request.tool_call_message import ToolCall


class ToolExecutor:
    """
    Shared tool execution logic for Step and ToolCallStep.

    Handles executing tool calls and processing their results into
    message dicts suitable for conversation history.
    """

    def __init__(
        self,
        tool_manager: ToolManager,
        logger: Optional[LoggerProtocol] = None
    ):
        """
        Initialize the ToolExecutor.

        Args:
            tool_manager: ToolManager instance with registered tools
            logger: Optional LoggerProtocol instance for logging
        """
        self.tool_manager = tool_manager
        self.logger = logger

    def _log_error(self, message: str):
        """Log error message if logger is available."""
        if self.logger:
            self.logger.error(message)

    def execute_tool_calls(
        self,
        tool_calls: List[Any],
        api_debugger: Optional[APIDebugger] = None,
        cancellation_check: Optional[Callable[[], bool]] = None
    ) -> Tuple[List[Dict], bool]:
        """
        Execute tool calls and return result messages.

        Args:
            tool_calls: List of tool calls (either ToolCall objects or API response objects)
            api_debugger: Optional APIDebugger instance for dumping tool execution data
            cancellation_check: Optional function that returns True if cancellation requested

        Returns:
            Tuple of (result_messages, was_cancelled) where result_messages is a list
            of tool result message dicts and was_cancelled indicates if cancelled
        """
        result_messages = []

        for tool_call in tool_calls:
            # Check for cancellation during tool execution
            if cancellation_check and cancellation_check():
                return result_messages, True

            # Handle both ToolCall objects and API response tool_call objects
            if isinstance(tool_call, ToolCall):
                tool_name = tool_call.name
                tool_args = tool_call.arguments
                tool_call_id = tool_call.id
                raw_arguments = json.dumps(tool_args)
            else:
                # API response format (has .function.name, .function.arguments, .id)
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments
                tool_call_id = tool_call.id
                try:
                    tool_args = json.loads(raw_arguments)
                except json.JSONDecodeError as e:
                    self._log_error(f"JSON parsing failed for tool '{tool_name}'")
                    self._log_error(f"Error: {e}")
                    self._log_error(f"Raw arguments (len={len(raw_arguments)}): {raw_arguments[:500]}...")
                    if len(raw_arguments) > 500:
                        self._log_error(f"...end of raw arguments: ...{raw_arguments[-200:]}")
                    raise

            # Execute the tool
            tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

            # Dump tool execution data if debugger is enabled
            if api_debugger:
                api_debugger.dump_tool_execution(
                    tool_name=tool_name,
                    tool_arguments=raw_arguments,
                    tool_result=tool_result,
                    tool_call_id=tool_call_id
                )

            # Get the provider and let it process the result
            tool_provider = self.tool_manager.get_provider(tool_name)
            if tool_provider:
                provider_result_messages = tool_provider.process_result(
                    tool_call_id, tool_name, tool_result
                )
                for result_message in provider_result_messages:
                    message_dict = result_message.get_message()
                    if message_dict:
                        result_messages.append(message_dict)

        return result_messages, False
