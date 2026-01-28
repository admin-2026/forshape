"""
Request builder for ForShape AI agent.

This module builds requests for AI interactions by combining:
- System message with API docs and tool instructions
- User context from FORSHAPE.md
- Current FreeCAD document structure
- Image handling for multimodal messages
"""

import os
from typing import Optional, Tuple, Dict, List, TYPE_CHECKING
from .context_provider import ContextProvider
from .tools.tool_manager import ToolManager

if TYPE_CHECKING:
    from .user_input_queue import UserInputQueue


class RequestBuilder:
    """Builds context and messages for AI requests."""

    def __init__(self, context_provider: ContextProvider):
        """
        Initialize the request builder.

        Args:
            context_provider: ContextProvider instance for loading raw data (API docs, document structure)
        """
        self.context_provider = context_provider
        self._system_message_cache: Optional[str] = None
        self._input_queue: Optional['UserInputQueue'] = None

    @property
    def input_queue(self) -> Optional['UserInputQueue']:
        """Get the current input queue."""
        return self._input_queue

    @input_queue.setter
    def input_queue(self, queue: 'UserInputQueue') -> None:
        """Set the input queue for the current request."""
        self._input_queue = queue

    def _build_base_message(self, api_docs: Optional[str] = None) -> str:
        """
        Build the base system message.

        Args:
            api_docs: Optional API documentation content to include

        Returns:
            Base system message
        """
        prefix = "You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Use tool to print and inspect FreeCAD object details. There could be existing scripts to generate the Freecad document. Update the script instead of creating a new one. Generated script should be saved to file without asking user. Introduce functions to encapsulate construction of logically related parts. Use constants to define values. Boolean operation label should have '_cut', '_fuse', '_common' suffix. For hyphen, use ascii one '-'. Use professional or widely used terminologies to name things. Boolean operations don't automatically copy the object. To get separate results from multiple boolean operations, you must copy the object first. DO NOT generate any test files or run any tests. Only read files helpful for the task. DO NOT read unrelated files. Offset is used when constructing object or its components. Transformation is used for moving finished object to desired location. Object should be constructed at the origin and then transformed to the desired final location."

        template_files_info = """

# Project File Structure

The working directory follows a modular organization pattern with core template files and optional modular build files:

## Core Template Files:

1. **constants.py** - Project constants and parameters
   - Contains all dimensional constants, tolerances, and configuration values
   - Define all numeric values here instead of hardcoding them in other files
   - Example: lengths, widths, heights, clearances, tolerances
   - Imported by other scripts using `from constants import *`

2. **main.py** - Main orchestrator script
   - The primary entry point that constructs all geometries
   - Imports and calls builder functions from <object_name>_build.py files
   - Contains a main orchestrator function (e.g., build_model()) that coordinates all builds
   - Should remain high-level and delegate detailed construction to build files
   - Example: `from case_build import build_case` then call `build_case()` in main

3. **export.py** - Export operations
   - Handles exporting models to STEP files or other formats
   - Contains export_models() function that exports finished parts
   - Uses Export.export(label, filepath) from shapes.export
   - Keeps export logic separate from construction logic

4. **import.py** - Import and placement of external geometry
   - Imports external geometry (VRML, STEP files, etc.)
   - Places imported objects in the correct positions using Transform
   - Useful for importing PCBs, reference components, or assemblies
   - Uses ImportGeometry.import_geometry() and Transform.translate_to()

## Modular Build Files (Optional):

5. **<object_name>_build.py** - Object-specific build modules
   - Contains all logic for building a specific object or component
   - Example: `case_build.py`, `lid_build.py`, `bracket_build.py`
   - Must have an orchestrator function (e.g., `build_case()`, `build_lid()`) that completes the entire object
   - The orchestrator function is imported and called by main.py
   - Should be runnable as a standalone script for testing: `if __name__ == '__main__': build_case()`
   - Imports constants from constants.py
   - May import shared utilities from <feature>_lib.py files
   - Contains helper functions specific to that object
   - Use functions to encapsulate construction of logically related parts

6. **<feature>_lib.py** - Shared utility libraries
   - Contains reusable logic and helper functions shared across multiple build files
   - Example: `fasteners_lib.py`, `mounting_lib.py`, `connectors_lib.py`
   - Pure utility functions that can be used by any <object_name>_build.py
   - Does not build complete objects, only provides reusable components
   - Example functions: create_bolt_pattern(), add_mounting_holes(), create_connector_cutout()
   - Imported by build files: `from fasteners_lib import create_bolt_pattern`
   - Promotes code reuse and consistency across the project

## File Organization Guidelines:

When users ask to modify their project, update the appropriate file(s):
- Dimension/parameter changes → constants.py
- Overall build coordination → main.py
- Object-specific construction → <object_name>_build.py
- Reusable utilities/helpers → <feature>_lib.py
- Export configuration → export.py
- External component placement → import.py

When creating new objects:
- Create a new <object_name>_build.py with an orchestrator function
- Import and call it from main.py
- Extract any reusable logic into appropriate <feature>_lib.py files
"""

        best_practices = """
### Best Practices

- When a user reports an error in a generated script, **read the script first** to understand the issue
- After generating new code, you can **directly write or edit the script file** instead of just showing code
- Use **list_files** to explore the project structure when needed
- Always verify changes by reading the file after editing
- Use **find_objects_by_regex** to locate objects when you need to reference them by pattern
- Avoid inserting dangerous code into the generated script.
"""

        if api_docs:
            return f"{prefix}{template_files_info}\n\nBelow is the complete API documentation:\n\n{api_docs}\n\n{best_practices}"
        else:
            return f"{prefix}{template_files_info}\n\n{best_practices}"

    def load_api_docs(self) -> Optional[str]:
        """
        Load API documentation from shapes/README.md.

        Returns:
            README.md content if file exists, None otherwise
        """
        readme_path = self.context_provider.get_readme_path()
        try:
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"Warning: Could not load README.md: {e}")
            return None

    def build_system_message(self, tool_manager: 'ToolManager') -> str:
        """
        Build the complete system message with API docs and tool instructions.

        Args:
            tool_manager: ToolManager instance for tool usage instructions

        Returns:
            Complete system message
        """
        # Load API documentation
        api_docs = self.load_api_docs()

        # Build base message with API docs
        base_message = self._build_base_message(api_docs)

        # Add tool usage instructions
        base_message += tool_manager.get_tool_usage_instructions()

        return base_message

    def load_forshape_context(self) -> Optional[str]:
        """
        Load user context from FORSHAPE.md in the working directory.

        Returns:
            FORSHAPE.md content if file exists, None otherwise
        """
        forshape_path = self.context_provider.get_forshape_path()
        try:
            if os.path.exists(forshape_path):
                with open(forshape_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            return None
        except Exception as e:
            print(f"Warning: Could not load FORSHAPE.md: {e}")
            return None

    def get_context(self, tool_manager: 'ToolManager') -> Tuple[str, Optional[str]]:
        """
        Get both system message and user context.

        Args:
            tool_manager: ToolManager instance for tool instructions

        Returns:
            Tuple of (system_message, forshape_context)
            - system_message: Always returns a string (built from API docs and tool instructions)
            - forshape_context: Combined context from FORSHAPE.md and document structure
        """
        system_message = self.build_system_message(tool_manager)
        forshape_context = self.load_forshape_context()
        document_structure = self.context_provider.get_document_structure()

        # Combine contexts
        contexts = []
        if forshape_context:
            contexts.append(forshape_context)
        if document_structure:
            contexts.append("# Current Document Structure\n\n```\n" + document_structure + "```")

        combined_context = "\n\n".join(contexts) if contexts else None
        return system_message, combined_context

    def build_request(self, tool_manager: 'ToolManager') -> Tuple[str, str, str]:
        """
        Build the system message and augmented user input for an AI request.

        The system message is cached after the first call for efficiency.
        The user message is augmented with FORSHAPE.md context if available.

        Args:
            tool_manager: ToolManager instance for tool instructions

        Returns:
            Tuple of (system_message, augmented_input, initial_message)
            - system_message: Cached system message with tool instructions
            - augmented_input: User message augmented with FORSHAPE.md context
            - initial_message: The raw initial message from the input queue

        Raises:
            ValueError: If input_queue has not been set
        """
        if self._input_queue is None:
            raise ValueError("input_queue must be set before calling build_request")

        # Get the initial message from the queue
        initial_message = self._input_queue.get_initial_message()

        # Get system message (cache it on first call)
        if self._system_message_cache is None:
            system_message, forshape_context = self.get_context(tool_manager)
            self._system_message_cache = system_message
        else:
            system_message = self._system_message_cache
            forshape_context = self.load_forshape_context()

        # Build augmented input with user preferences if available
        if forshape_context:
            augmented_input = f"[User Preferences]\n{forshape_context}\n\n[User Request]\n{initial_message}"
        else:
            augmented_input = initial_message

        return system_message, augmented_input, initial_message

    # ========== Image Message Building ==========

    @staticmethod
    def create_image_url_content(base64_image: str) -> Dict:
        """
        Create an image_url content object for OpenAI messages.

        Args:
            base64_image: Base64-encoded image string

        Returns:
            Image URL content dict
        """
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            }
        }

    @staticmethod
    def create_image_message(text: str, base64_image: str) -> Dict:
        """
        Create an OpenAI message with both text and image content.

        Args:
            text: The text content to include with the image
            base64_image: Base64-encoded image string

        Returns:
            Message dict with text and image_url content
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                RequestBuilder.create_image_url_content(base64_image)
            ]
        }

    @staticmethod
    def create_multi_image_message(text: str, base64_images: List[str]) -> Dict:
        """
        Create an OpenAI message with text and multiple image content.

        Args:
            text: The text content to include with the images
            base64_images: List of base64-encoded image strings

        Returns:
            Message dict with text and multiple image_url content
        """
        content = [
            {
                "type": "text",
                "text": text
            }
        ]

        # Add all images to the content array
        for base64_image in base64_images:
            content.append(RequestBuilder.create_image_url_content(base64_image))

        return {
            "role": "user",
            "content": content
        }

    def build_user_message(self, text: str, image_data: Optional[Dict] = None) -> Dict:
        """
        Build a complete user message, handling optional image data.

        Args:
            text: The text content of the message
            image_data: Optional dict or list of dicts containing captured image data

        Returns:
            Message dict ready for API call
        """
        if not image_data:
            return {"role": "user", "content": text}

        # Handle both single image (dict) and multiple images (list)
        images_list = image_data if isinstance(image_data, list) else [image_data]

        # Filter valid images
        valid_images = []
        for img in images_list:
            if img and img.get("success"):
                base64_image = img.get("image_base64")
                if base64_image and not base64_image.startswith("Error"):
                    valid_images.append(base64_image)

        # Create message with text and image(s)
        if valid_images:
            return self.create_multi_image_message(text, valid_images)
        else:
            # No valid images, just send text
            return {"role": "user", "content": text}
