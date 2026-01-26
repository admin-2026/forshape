"""
Visualization tools for AI Agent.

This module provides tools for capturing screenshots and other
visual representations of FreeCAD content.
"""

import io
import sys
import json
from typing import Dict, List, Callable, Optional
from contextlib import contextmanager

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

    def get_definitions(self) -> List[Dict]:
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
                                "description": "Optional object label/name to focus on. If not specified, captures entire scene."
                            },
                            "perspective": {
                                "type": "string",
                                "description": "View angle: 'front', 'back', 'top', 'bottom', 'left', 'right', or 'isometric' (default: 'isometric'). Ignored if perspectives is specified."
                            },
                            "perspectives": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Optional list of perspectives for multiple captures. Example: ['front', 'top', 'isometric']. When provided, ignores the 'perspective' parameter."
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "capture_screenshot": self._tool_capture_screenshot,
        }

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
        self,
        target: Optional[str] = None,
        perspective: str = "isometric",
        perspectives: Optional[List[str]] = None
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
                return json.dumps({
                    "success": False,
                    "message": "ImageContext not configured"
                })

            with self._capture_output() as get_output:
                # Call image_context.capture_encoded() - handles both capture and base64 encoding
                result = self.image_context.capture_encoded(
                    target=target,
                    perspective=perspective,
                    perspectives=perspectives
                )
                output = get_output()

            # Check if capture was successful
            if result is None:
                return json.dumps({
                    "success": False,
                    "message": output.strip() if output else "Screenshot capture failed"
                }, indent=2)

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
