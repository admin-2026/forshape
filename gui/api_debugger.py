"""
API Debugger module for dumping LLM API request/response data to files.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class APIDebugger:
    """Handles dumping of API request and response data to files for debugging."""

    def __init__(self, enabled: bool = False, output_dir: Optional[str] = None):
        """
        Initialize the API debugger.

        Args:
            enabled: Whether data dumping is enabled
            output_dir: Directory to save dumps (defaults to .forshape/api_dumps)
        """
        self.enabled = enabled
        self.output_dir = output_dir or os.path.join(".forshape", "api_dumps")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.request_counter = 0

        if self.enabled:
            self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def set_enabled(self, enabled: bool):
        """Enable or disable data dumping."""
        self.enabled = enabled
        if self.enabled:
            self._ensure_output_dir()

    def _sanitize_for_json(self, obj: Any) -> Any:
        """
        Recursively sanitize objects to be JSON serializable.

        Args:
            obj: Object to sanitize

        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj]
        else:
            # For objects that aren't directly serializable, convert to string
            return str(obj)

    def dump_request(
        self,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        tool_choice: str = "auto",
        additional_data: Optional[Dict] = None
    ):
        """
        Dump API request data to a file.

        Args:
            model: Model being used
            messages: Messages array
            tools: Tools definition
            tool_choice: Tool choice setting
            additional_data: Any additional metadata to include
        """
        if not self.enabled:
            return

        self.request_counter += 1
        timestamp = datetime.now().isoformat()

        data = {
            "type": "request",
            "timestamp": timestamp,
            "session_id": self.session_id,
            "request_number": self.request_counter,
            "model": model,
            "messages": self._sanitize_for_json(messages),
            "tools": self._sanitize_for_json(tools) if tools else None,
            "tool_choice": tool_choice,
        }

        if additional_data:
            data["additional_data"] = self._sanitize_for_json(additional_data)

        filename = f"{self.session_id}_req_{self.request_counter:03d}.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to dump request data: {e}")

    def dump_response(
        self,
        response: Any,
        token_usage: Optional[Dict] = None,
        additional_data: Optional[Dict] = None
    ):
        """
        Dump API response data to a file.

        Args:
            response: API response object
            token_usage: Token usage statistics
            additional_data: Any additional metadata to include
        """
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        # Extract relevant response data
        response_data = {
            "type": "response",
            "timestamp": timestamp,
            "session_id": self.session_id,
            "request_number": self.request_counter,
            "token_usage": token_usage,
        }

        # Try to extract response details
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                message_data = {
                    "role": getattr(choice.message, 'role', None),
                    "content": getattr(choice.message, 'content', None),
                }

                # Include tool calls if present
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    message_data["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in choice.message.tool_calls
                    ]

                response_data["message"] = message_data
                response_data["finish_reason"] = getattr(choice, 'finish_reason', None)

            # Include model and ID if available
            if hasattr(response, 'model'):
                response_data["model"] = response.model
            if hasattr(response, 'id'):
                response_data["response_id"] = response.id

        except Exception as e:
            # If extraction fails, include raw response as string
            response_data["raw_response"] = str(response)
            response_data["extraction_error"] = str(e)

        if additional_data:
            response_data["additional_data"] = self._sanitize_for_json(additional_data)

        filename = f"{self.session_id}_resp_{self.request_counter:03d}.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to dump response data: {e}")

    def dump_tool_execution(
        self,
        tool_name: str,
        tool_arguments: str,
        tool_result: str,
        tool_call_id: Optional[str] = None
    ):
        """
        Dump tool execution data to a file.

        Args:
            tool_name: Name of the tool executed
            tool_arguments: Arguments passed to the tool
            tool_result: Result from tool execution
            tool_call_id: ID of the tool call
        """
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        data = {
            "type": "tool_execution",
            "timestamp": timestamp,
            "session_id": self.session_id,
            "request_number": self.request_counter,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "arguments": tool_arguments,
            "result": tool_result
        }

        # Create a sub-file for each tool execution
        filename = f"{self.session_id}_tool_{self.request_counter:03d}_{tool_name}.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to dump tool execution data: {e}")
