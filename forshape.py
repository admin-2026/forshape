"""
GUI AI interactive interface for shape generation.

This module provides an interactive GUI interface using PySide2 where users can
interact with an AI to generate, manipulate, and export 3D shapes.

Usage from Python REPL:
    >>> script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
    >>> from forshape import ForShapeAI
    >>> ai = ForShapeAI()
    >>> ai.run()
"""

# from importlib import reload
# reload(forshape); from forshape import ForShapeAI; ai = ForShapeAI(); ai.run()

import sys
from typing import Optional

from PySide2.QtWidgets import QApplication

from agent import StepJump, ToolCallStep, ToolExecutor
from agent.async_ops import PermissionInput, WaitManager
from agent.chat_history_manager import HistoryPolicy
from agent.permission_manager import PermissionManager
from agent.request import DynamicContent, FileLoader, Instruction, RequestBuilder, ToolCall, ToolCallMessage
from agent.tools.tool_manager import ToolManager
from app import (
    AIAgent,
    APIDebugger,
    ApiKeyManager,
    ConfigurationManager,
    DependencyManager,
    ForShapeMainWindow,
    HistoryLogger,
    Logger,
    LogLevel,
    PrestartChecker,
    Step,
)

# System message instructions
BASE_INSTRUCTION = """
You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Be concise.

## Tools and Inspection
- Use tools to print and inspect FreeCAD object details.

## Script Management
- There could be existing scripts to generate the FreeCAD document. Update the script instead of creating a new one.
- Generated scripts should be saved to file without asking user.
- DO NOT generate any test files or run any tests.
- Only read files helpful for the task. DO NOT read unrelated files.

## Code Organization
- Introduce functions to encapsulate construction of logically related parts.
- Use constants to define values.

## Naming Conventions
- Boolean operation labels should have '_cut', '_fuse', '_common' suffix.
- For hyphens, use the ASCII hyphen '-'. Only use ASCII chars in generated code.
- Use professional or widely used terminologies to name things.

## Boolean Operations
- Boolean operations don't automatically copy the object.
- To get separate results from multiple boolean operations, you must copy the object first.

## Positioning and Transformation
- Offset is used when constructing an object or its components.
- Transformation is used for moving a finished object to its desired location.
- Objects should be constructed at the origin and then transformed to the desired final location.
"""

TEMPLATE_FILES_INFO = """
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


class NextStepJump(StepJump):
    """A StepJump that always jumps to a fixed next step."""

    def __init__(self, next_step: str):
        self._next_step = next_step

    def get_next_step(self, result) -> str:
        return self._next_step


BEST_PRACTICES = """
### Best Practices

- When a user reports an error in a generated script, **read the script first** to understand the issue
- After generating new code, you can **directly write or edit the script file** instead of just showing code
- Use **list_files** to explore the project structure when needed
- Always verify changes by reading the file after editing
- Front means -Y direction. Back/REAR is +Y direction. Left is -X direction. Right is +X direction. Top is +Z direction. Bottom is -Z direction.
- Avoid inserting dangerous code into the generated script.
- After creating a new object, export it in the export.py. Usually, we export the top level object not components of the top level object.
"""


class ForShapeAI:
    """Main orchestrator class for the AI-powered GUI interface."""

    # Class variable to track the existing GUI window across instances
    _active_window = None

    @classmethod
    def _clear_active_window(cls):
        """Clear the active window reference when window is closed."""
        cls._active_window = None

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the ForShape AI application.

        Args:
            model: Optional AI model identifier to use
        """
        # Initialize configuration manager - single source of truth for working directory
        self.config = ConfigurationManager()
        # Note: Directory setup moved to prestart checker for interactive handling

        # Check and install all dependencies
        self.dependency_manager = DependencyManager(self.config.get_libs_dir())
        success, error_msg = self.dependency_manager.check_and_install_all()

        if not success:
            print(f"\n{'=' * 60}")
            print("ERROR: Cannot initialize ForShapeAI")
            print(f"{'=' * 60}")
            print(f"\n{error_msg}")
            print("\nPlease install the required libraries to use ForShape AI.")
            print(f"{'=' * 60}\n")
            return

        # Initialize prestart checker (will setup directories and check API key)
        # Create a minimal logger before directories exist
        self.logger = Logger(min_level=LogLevel.INFO)
        self.prestart_checker = PrestartChecker(self.config, self.logger)

        # Store model preference for later
        self.model = model

        # These will be initialized after prestart checks pass
        self.history_logger = None
        self.ai_client = None

        # GUI window (will be created in run())
        self.main_window = None
        self.running = True

    def _complete_initialization(self):
        """
        Complete initialization after prestart checks pass.

        This creates the AI agent, history logger, and other components that
        require the configuration directories and API key to exist.
        """
        # Reinitialize logger for terminal output
        self.logger = Logger(min_level=LogLevel.INFO)
        self.logger.info("ForShape AI initialization completed")

        # Initialize history logger
        self.history_logger = HistoryLogger(self.config.get_history_dir())

        # Initialize ImageContext for screenshot capture
        from shapes.image_context import ImageContext

        images_dir = self.config.get_history_dir() / "images"
        self.image_context = ImageContext(str(images_dir))

        # Initialize API debugger (disabled by default)
        self.api_debugger = APIDebugger(enabled=False, output_dir=str(self.config.get_api_dumps_dir()))

        # Initialize edit history for tracking file changes
        from agent.edit_history import EditHistory

        self.edit_history = EditHistory(
            working_dir=self.config.working_dir, edits_dir=str(self.config.get_edits_dir()), logger=self.logger
        )

        # Initialize AI agent with API key from keyring
        api_key_manager = ApiKeyManager()
        from agent.provider_config_loader import ProviderConfigLoader

        # Find the first provider with an API key
        provider_loader = ProviderConfigLoader()
        configured_providers = provider_loader.get_providers()

        provider = None
        api_key = None
        provider_config = None

        for prov_config in configured_providers:
            key = api_key_manager.get_api_key(prov_config.name)
            if key:
                provider = prov_config.name
                api_key = key
                provider_config = prov_config
                self.logger.info(f"Using provider: {prov_config.display_name} ({prov_config.name})")
                break

        if not api_key:
            self.logger.warning("No API keys found for any configured provider. AI features will not work.")
            # Default to openai for backwards compatibility
            provider = "openai"

        # Determine the model to use
        if provider_config and provider_config.default_model:
            agent_model = provider_config.default_model
        else:
            agent_model = self.model if self.model else "gpt-5.1"

        # Create wait manager and permission system
        wait_manager = WaitManager()
        permission_input = PermissionInput()
        permission_manager = PermissionManager(permission_requester=permission_input)

        # Create and configure tool manager with all tools
        tool_manager = ToolManager(logger=self.logger)
        self._register_main_step_tools(tool_manager, wait_manager, permission_manager)

        system_elements = [
            Instruction(BASE_INSTRUCTION + TEMPLATE_FILES_INFO, description="Base instructions and project structure"),
            FileLoader(str(self.config.get_readme_path()), required=True, description="API documentation"),
            Instruction(BEST_PRACTICES, description="Best practices"),
            DynamicContent(tool_manager.get_tool_usage_instructions, description="Tool usage instructions"),
        ]

        user_elements = [
            FileLoader(str(self.config.get_forshape_path()), required=False, description="User preferences"),
        ]

        # Create request builder for AI context
        request_builder = RequestBuilder(system_elements, user_elements)

        # Create tool executor shared by all steps
        tool_executor = ToolExecutor(tool_manager=tool_manager, logger=self.logger)

        # Create the doc_print step that calls print_document before main step
        doc_print_tool_call = ToolCallMessage(
            tool_calls=[
                ToolCall(
                    name="print_document",
                    arguments={},
                    copy_result_to_response=True,
                    description="The current FreeCAD document structure printed by print_document tool",
                    key="doc_print_step_print_document",
                    policy=HistoryPolicy.LATEST,
                ),
                ToolCall(
                    name="list_files",
                    arguments={"folder_path": "."},
                    copy_result_to_response=True,
                    description="The current files in the working directory listed by list_files tool",
                    key="doc_print_step_list_files",
                    policy=HistoryPolicy.LATEST,
                ),
            ]
        )
        doc_print_step = ToolCallStep(
            name="doc_print",
            tool_executor=tool_executor,
            messages=[doc_print_tool_call],
            logger=self.logger,
            step_jump=NextStepJump("main"),
        )

        # Create the main step with tool executor
        main_step = Step(
            name="main",
            request_builder=request_builder,
            tool_executor=tool_executor,
            max_iterations=50,
            logger=self.logger,
            step_jump=NextStepJump("lint"),
        )

        # Create the lint step with its own tool executor containing only lint tools
        lint_tool_manager = ToolManager(logger=self.logger)
        self._register_lint_step_tools(lint_tool_manager)
        lint_tool_executor = ToolExecutor(tool_manager=lint_tool_manager, logger=self.logger)
        lint_tool_call = ToolCallMessage(
            tool_calls=[
                ToolCall(
                    name="lint_python",
                    arguments={
                        "directory": str(self.config.working_dir),
                        "format": True,
                        "fix": True,
                        "ignore": ["F403", "F405"],
                    },
                    copy_result_to_response=True,
                    key="lint_step_lint_python",
                    policy=HistoryPolicy.LATEST,
                )
            ]
        )
        lint_step = ToolCallStep(
            name="lint",
            tool_executor=lint_tool_executor,
            messages=[lint_tool_call],
            logger=self.logger,
        )

        # Create AI agent with steps (doc_print runs before main, lint runs after main)
        self.ai_client = AIAgent(
            api_key,
            model=agent_model,
            steps={"doc_print": doc_print_step, "main": main_step, "lint": lint_step},
            start_step="doc_print",
            logger=self.logger,
            api_debugger=self.api_debugger,
            provider=provider,
            provider_config=provider_config,
            edit_history=self.edit_history,
            response_steps=["main", "lint"],
        )
        self.logger.info(f"AI client initialized with provider: {provider}, model: {agent_model}")

        # Update the main window with the initialized components
        if self.main_window:
            self.main_window.set_components(
                self.ai_client,
                self.history_logger,
                wait_manager,
                permission_input,
                self.logger,
                self.image_context,
                self.api_debugger,
            )

    def _register_main_step_tools(
        self, tool_manager: ToolManager, wait_manager: WaitManager, permission_manager: PermissionManager
    ) -> None:
        """
        Register tools for the main step with the tool manager.

        Args:
            tool_manager: ToolManager instance to register tools with
            wait_manager: WaitManager instance for user interactions
            permission_manager: PermissionManager instance for permission checks
        """
        from agent.tools.calculator_tools import CalculatorTools
        from agent.tools.file_access_tools import FileAccessTools
        from agent.tools.interaction_tools import InteractionTools
        from app.tools import FreeCADTools, VisualizationTools

        # Register file access tools
        file_access_tools = FileAccessTools(
            working_dir=self.config.working_dir,
            logger=self.logger,
            permission_manager=permission_manager,
            edit_history=self.edit_history,
            exclude_folders=[self.config.get_forshape_folder_name(), ".git", "__pycache__"],
            exclude_patterns=[],
        )
        tool_manager.register_provider(file_access_tools)

        # Register interaction tools
        interaction_tools = InteractionTools(wait_manager)
        tool_manager.register_provider(interaction_tools)

        # Register calculator tools
        calculator_tools = CalculatorTools()
        tool_manager.register_provider(calculator_tools)

        # Register FreeCAD object manipulation tools
        freecad_tools = FreeCADTools(permission_manager=permission_manager)
        tool_manager.register_provider(freecad_tools)

        # Register visualization tools if image_context is available
        if self.image_context is not None:
            visualization_tools = VisualizationTools(image_context=self.image_context)
            tool_manager.register_provider(visualization_tools)

    def _register_lint_step_tools(self, tool_manager: ToolManager) -> None:
        """
        Register tools for the lint step with the tool manager.

        Args:
            tool_manager: ToolManager instance to register tools with
        """
        from agent.tools.python_lint_tools import PythonLintTools

        tool_manager.register_provider(PythonLintTools())

    def run(self):
        """Start the interactive GUI interface."""
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Check if a window already exists and is visible
        if ForShapeAI._active_window is not None:
            try:
                # Check if the window is still valid and visible
                if ForShapeAI._active_window.isVisible():
                    # Bring the existing window to front
                    ForShapeAI._active_window.raise_()
                    ForShapeAI._active_window.activateWindow()
                    self.logger.info("Existing GUI window brought to front")
                    return 0
            except RuntimeError:
                # Window was deleted, clear the reference
                ForShapeAI._active_window = None

        # Create and show main window first (so user can see messages and interact with FreeCAD)
        # Pass None for components that haven't been initialized yet
        self.main_window = ForShapeMainWindow(
            ai_client=None,  # Will be set after prestart checks
            history_logger=None,  # Will be set after prestart checks
            logger=self.logger,
            config=self.config,
            exit_handler=self.handle_exit,
            prestart_checker=self.prestart_checker,
            completion_callback=self._complete_initialization,
            window_close_callback=ForShapeAI._clear_active_window,
        )

        # Store the window as the active window
        ForShapeAI._active_window = self.main_window

        self.main_window.show()

        # Run initial prestart check
        status = self.prestart_checker.check(self.main_window)
        if status == "ready":
            # All checks passed, complete initialization (which also sets components) and enable AI
            self._complete_initialization()
            self.main_window.enable_ai_mode()
        elif status == "error":
            # Fatal error, keep window open but AI disabled
            self.main_window.prestart_check_mode = False
        else:
            # Waiting for user action ("waiting", "dir_mismatch", or "need_api_key")
            # Window will handle user input and re-run checks
            pass

        # Start Qt event loop
        return app.exec_()

    def handle_exit(self):
        """Handle graceful exit of the application."""
        # Write session end marker to log
        self.history_logger.write_session_end()
        self.running = False


def start(model: Optional[str] = None):
    """
    Convenience function to start the interactive interface.

    Args:
        model: Optional AI model identifier to use
    """
    ai = ForShapeAI(model=model)
    ai.run()
