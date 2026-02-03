"""
Visualization tools for AI Agent.

This module provides tools for capturing screenshots and other
visual representations of FreeCAD content.
"""

import io
import json
import sys
from contextlib import contextmanager
from typing import Callable, Optional

from agent.request import ImageMessage, MessageElement, ToolResultMessage
from agent.tools.base import ToolBase
from shapes.image_context import ImageContext


class VisualizationTools(ToolBase):
    """
    Visualization tools - injected into ToolManager.

    Provides: capture_screenshot
    """

    def __init__(self, image_context: ImageContext):
        """
        Initialize visualization tools.

        Args:
            image_context: ImageContext instance for screenshot capture
        """
        self.image_context = image_context

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "capture_screenshot",
                    "description": "Capture a screenshot of the FreeCAD 3D view. Automatically saves to history/images folder with timestamp. Can capture entire scene or focus on a specific object, from various perspectives (front, top, isometric, etc.). Supports multiple perspectives in a single call.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Optional object label/name to focus on. If not specified, captures entire scene.",
                            },
                            "perspective": {
                                "type": "string",
                                "description": "View angle: 'front', 'back', 'top', 'bottom', 'left', 'right', or 'isometric' (default: 'isometric'). Ignored if perspectives is specified.",
                            },
                            "perspectives": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of perspectives for multiple captures. Example: ['front', 'top', 'isometric']. When provided, ignores the 'perspective' parameter.",
                            },
                        },
                        "required": [],
                    },
                },
            }
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "capture_screenshot": self._tool_capture_screenshot,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for visualization tools."""
        return """
### FreeCAD Visualization Tools
1. **capture_screenshot** - Capture screenshots of the FreeCAD 3D view from various perspectives

### Visualization Examples

**User says: "Take a screenshot of the model"**
> Use capture_screenshot (no parameters needed - auto-saves with timestamp)

**User says: "Capture the box from the front view"**
> Use capture_screenshot with target="box", perspective="front"

**User says: "Take screenshots from multiple angles"**
> Use capture_screenshot with perspectives=["front", "top", "isometric"]

**User says: "Show me what the object looks like"**
> Use capture_screenshot to capture an image of the object and return the image
"""

    def process_result(self, tool_call_id: str, tool_name: str, tool_result: str) -> list[MessageElement]:
        """
        Process a tool result and return MessageElements for the conversation.

        For capture_screenshot, adds image messages so the LLM can see the screenshots.

        Args:
            tool_call_id: The ID of the tool call
            tool_name: The name of the tool that was called
            tool_result: The result from the tool execution

        Returns:
            List of MessageElements to add to the conversation
        """
        messages = [ToolResultMessage(tool_call_id, tool_name, tool_result)]

        # Add screenshot images to conversation for capture_screenshot tool
        if tool_name == "capture_screenshot":
            screenshot_messages = self._build_screenshot_messages(tool_result)
            messages.extend(screenshot_messages)

        return messages

    def _build_screenshot_messages(self, tool_result: str) -> list[MessageElement]:
        """
        Build conversation messages from screenshot tool result.

        Args:
            tool_result: JSON string from capture_screenshot tool

        Returns:
            List of MessageElements for the screenshots
        """
        messages = []

        try:
            result_data = json.loads(tool_result)

            if not result_data.get("success"):
                return messages

            # Check if we have single or multiple images
            if "image_base64" in result_data:
                # Single image
                base64_image = result_data["image_base64"]
                if base64_image and not base64_image.startswith("Error"):
                    messages.append(
                        ImageMessage(
                            "Here is the screenshot that was just captured:",
                            {"success": True, "image_base64": base64_image},
                        )
                    )

            elif "images" in result_data:
                # Multiple images with perspective labels
                messages.append(
                    ImageMessage("Here are the screenshots that were just captured:", result_data["images"])
                )

        except (json.JSONDecodeError, Exception):
            pass  # Silently ignore errors in screenshot message building

        return messages

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    @contextmanager
    def _capture_output(self):
        """Context manager for capturing stdout and stderr."""
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

    def _tool_capture_screenshot(
        self, target: Optional[str] = None, perspective: str = "isometric", perspectives: Optional[list[str]] = None
    ) -> str:
        """
        Implementation of the capture_screenshot tool.
        Automatically saves screenshots to history/images folder with timestamp.
        Returns the image data as base64 so the LLM can see it.

        Args:
            target: Optional object label/name to focus on
            perspective: View angle (default: "isometric")
            perspectives: Optional list of perspectives for multiple captures

        Returns:
            JSON string with success or error message, including base64-encoded image(s)
        """
        try:
            # Check if image_context is available
            if self.image_context is None:
                return json.dumps({"success": False, "message": "ImageContext not configured"})

            with self._capture_output() as get_output:
                # Call image_context.capture_encoded() - handles both capture and base64 encoding
                result = self.image_context.capture_encoded(
                    target=target, perspective=perspective, perspectives=perspectives
                )
                output = get_output()

            # Check if capture was successful
            if result is None:
                return json.dumps(
                    {"success": False, "message": output.strip() if output else "Screenshot capture failed"}, indent=2
                )

            # Add captured output to the result
            result["output"] = output.strip()

            # Add success message if not present
            if "message" not in result:
                if "images" in result:
                    result["message"] = "Screenshots captured successfully"
                else:
                    result["message"] = "Screenshot captured successfully"

            return json.dumps(result, indent=2)

        except Exception as e:
            return self._json_error(f"Error capturing screenshot: {str(e)}")
