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

from agent import NextStepJump, StepJump, StepJumpController, StepJumpTools, ToolCallStep, ToolExecutor
from agent.async_ops import PermissionInput, WaitManager
from agent.chat_history_manager import HistoryPolicy
from agent.permission_manager import PermissionManager
from agent.request import DynamicContent, FileLoader, Instruction, RequestBuilder, ToolCall, ToolCallMessage
from agent.tools.tool_manager import ToolManager
from app import (
    ActiveDocumentObserver,
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
from app.tools import ConstantsTools

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
   - Imports constants from constants.py or <object_name>_constants.py
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

7. **<object_name>_constants.py** - Object-specific constants
   - Contains constants specific to a particular object or component
   - Example: `case_constants.py`, `lid_constants.py`, `bracket_constants.py`
   - Use when an object has many constants that would clutter the main constants.py
   - Imported by the corresponding build file: `from case_constants import *`
   - Keeps object-specific values separate from project-wide constants

## File Organization Guidelines:

When users ask to modify their project, update the appropriate file(s):
- Dimension/parameter changes → constants.py
- Object-specific dimension/parameter changes → <object_name>_constants.py
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


class ChangedFilesStepJump(StepJump):
    """A StepJump that jumps to next step only if files were changed (edited or created)."""

    def __init__(self, next_step: str, edit_history):
        self._next_step = next_step
        self._edit_history = edit_history

    def get_next_step(self, result) -> Optional[str]:
        """Return next step only if files were changed, otherwise None to stop."""
        changed_files = self._edit_history.get_changed_files()
        if changed_files:
            return self._next_step
        return None


class LintStepJump(StepJump):
    """A StepJump that jumps to lint_err_fix only if there are lint issues."""

    def __init__(self, next_step: str):
        self._next_step = next_step

    def get_next_step(self, result) -> Optional[str]:
        """Return next step only if lint found issues, otherwise None to stop."""
        import json

        # Look through api_messages for the lint results
        for msg in result.api_messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                try:
                    tool_result = json.loads(content)
                    # Check if this is a lint result with issues
                    if tool_result.get("success") and tool_result.get("issue_count", 0) > 0:
                        return self._next_step
                except (json.JSONDecodeError, TypeError):
                    continue

        # No issues found, stop here
        return None


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

LINT_ERR_FIX_SYSTEM = """You are a code assistant that fixes Python lint errors.

Your task is to fix any lint errors reported from the previous step. Focus only on fixing the errors, do not make other changes.

Guidelines:
- Fix lint errors reported by the lint_python tool (code style, unused imports, etc.)
- Do not refactor or improve code beyond fixing the errors
- If there are no errors to fix, do nothing
- Use the edit_file tool to make corrections
"""

LINT_ERR_FIX_USER = (
    "Fix the lint errors shown in the results above. If there are no errors, respond that no fixes are needed."
)

ROUTER_SYSTEM = """You are an AI assistant router that helps users navigate different workflows for 3D shape creation.

## Your Role
You are the entry point for user requests. Based on what the user asks, you should:
1. Route them to the appropriate workflow using jump_to_step or call_step
2. Help them use utility tools directly (like analyze_constants, list_files)
3. Provide guidance on available workflows and tools

## Available Workflows
- **doc_print**: Prints current FreeCAD document structure and lists files, then goes to main workflow
- **main**: The primary workflow for creating and manipulating 3D shapes
- **lint**: Run code linting on Python files
- **lint_err_fix**: Fix lint errors in code

## When to Route vs Handle Directly
**Route to doc_print** when the user wants to:
- Create, modify, or manipulate 3D shapes (this shows document context first)
- Write or edit Python scripts for shape generation
- Work with FreeCAD documents
- Any substantial code generation task

**Route to main directly** when:
- You already know the document state or don't need to show it
- The user is continuing a previous task

**Handle directly** when the user wants to:
- Analyze constants in the project (use analyze_constants tool)
- List files in the project (use list_files tool)
- Get information about the project structure
- Ask questions that don't require code generation

## Guidelines
- Be concise in your responses
- If unsure whether to route or handle directly, ask the user for clarification
- Use jump_to_step (not call_step) when routing since these are primary workflows
- Prefer doc_print over main for shape creation tasks to provide full context
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
            self._init_success = False
            return

        # Mark initialization as successful
        self._init_success = True

        # Initialize prestart checker (will setup directories and check API key)
        self.logger = Logger(min_level=LogLevel.INFO)
        self.prestart_checker = PrestartChecker(
            self.config, self.logger, completion_callback=self._complete_initialization
        )

        # Store model preference for later
        self.model = model

        # These will be initialized after prestart checks pass
        self.history_logger = None
        self.ai_client = None

        # GUI window (will be created in run())
        self.main_window = None
        self.document_observer = None
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

        # Create StepJumpController for dynamic step flow control
        # Router can jump to doc_print (which goes to main), main, lint, lint_err_fix
        step_jump_controller = StepJumpController(
            valid_destinations={
                "router": ["doc_print", "main", "lint", "lint_err_fix"],
            }
        )

        # Create and configure tool manager for router step (has all tools + step jump tools)
        router_tool_manager = ToolManager(logger=self.logger)
        self._register_router_step_tools(router_tool_manager, wait_manager, permission_manager, step_jump_controller)

        router_system_elements = [
            Instruction(ROUTER_SYSTEM, description="Router instructions"),
            DynamicContent(router_tool_manager.get_tool_usage_instructions, description="Tool usage instructions"),
        ]

        router_user_elements = [
            FileLoader(str(self.config.get_forshape_path()), required=False, description="User preferences"),
        ]

        router_request_builder = RequestBuilder(router_system_elements, router_user_elements)
        router_tool_executor = ToolExecutor(tool_manager=router_tool_manager, logger=self.logger)

        # Create and configure tool manager for main step
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

        # Create the router step - entry point that routes user to workflows or handles utility tasks
        router_step = Step(
            name="router",
            request_builder=router_request_builder,
            tool_executor=router_tool_executor,
            max_iterations=20,
            logger=self.logger,
            step_jump=None,  # Router decides dynamically via StepJumpTools
        )

        # Create the main step with tool executor
        main_step = Step(
            name="main",
            request_builder=request_builder,
            tool_executor=tool_executor,
            max_iterations=50,
            logger=self.logger,
            step_jump=ChangedFilesStepJump("lint", self.edit_history),
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
                ),
                # ToolCall(
                #     name="compile_python",
                #     arguments={
                #         # "files": ["*.py"],
                #         "use_edit_history": True,
                #     },
                #     copy_result_to_response=True,
                #     key="lint_step_compile_python",
                #     policy=HistoryPolicy.LATEST,
                # ),
            ]
        )
        lint_step = ToolCallStep(
            name="lint",
            tool_executor=lint_tool_executor,
            messages=[lint_tool_call],
            logger=self.logger,
            step_jump=LintStepJump("lint_err_fix"),
        )

        # Create the lint_err_fix step to fix any lint errors found
        lint_err_fix_tool_manager = ToolManager(logger=self.logger)
        self._register_lint_err_fix_step_tools(lint_err_fix_tool_manager, permission_manager)
        lint_err_fix_tool_executor = ToolExecutor(tool_manager=lint_err_fix_tool_manager, logger=self.logger)

        lint_err_fix_request_builder = RequestBuilder(
            system_elements=[Instruction(LINT_ERR_FIX_SYSTEM, description="Lint and compile error fix instructions")],
            user_elements=[Instruction(LINT_ERR_FIX_USER, description="Lint and compile error fix task")],
        )
        lint_err_fix_step = Step(
            name="lint_err_fix",
            request_builder=lint_err_fix_request_builder,
            tool_executor=lint_err_fix_tool_executor,
            max_iterations=30,
            logger=self.logger,
            step_jump=NextStepJump("diff"),
        )

        # Create the diff step with its own tool executor containing only diff tools
        diff_tool_manager = ToolManager(logger=self.logger)
        self._register_diff_step_tools(diff_tool_manager)
        diff_tool_executor = ToolExecutor(tool_manager=diff_tool_manager, logger=self.logger)
        diff_tool_call = ToolCallMessage(
            tool_calls=[
                ToolCall(
                    name="diff_files",
                    arguments={},
                    copy_result_to_response=True,
                    key="diff_step_diff_files",
                    policy=HistoryPolicy.LATEST,
                ),
            ]
        )
        diff_step = ToolCallStep(
            name="diff",
            tool_executor=diff_tool_executor,
            messages=[diff_tool_call],
            logger=self.logger,
        )

        # Create AI agent with steps
        # Flow: router -> (main -> lint -> lint_err_fix -> diff) or direct tool use
        self.ai_client = AIAgent(
            api_key,
            model=agent_model,
            steps={
                "router": router_step,
                "doc_print": doc_print_step,
                "main": main_step,
                "lint": lint_step,
                "lint_err_fix": lint_err_fix_step,
                "diff": diff_step,
            },
            # start_step="router",  # routing is under construction
            start_step="doc_print",
            logger=self.logger,
            api_debugger=self.api_debugger,
            provider=provider,
            provider_config=provider_config,
            edit_history=self.edit_history,
            response_steps=["router", "main", "lint_err_fix"],
            step_jump_controller=step_jump_controller,
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
        # from agent.tools.python_compile_tools import PythonCompileTools
        from agent.tools.python_lint_tools import PythonLintTools

        tool_manager.register_provider(PythonLintTools(exclude_dirs=[".git", ".forshape"]))
        # tool_manager.register_provider(
        #     PythonCompileTools(
        #         working_dir=self.config.working_dir,
        #         edit_history=self.edit_history,
        #         logger=self.logger,
        #     )
        # )

    def _register_lint_err_fix_step_tools(
        self, tool_manager: ToolManager, permission_manager: PermissionManager
    ) -> None:
        """
        Register tools for the lint error fix step with the tool manager.

        Args:
            tool_manager: ToolManager instance to register tools with
            permission_manager: PermissionManager instance for permission checks
        """
        from agent.tools.file_access_tools import FileAccessTools

        file_access_tools = FileAccessTools(
            working_dir=self.config.working_dir,
            logger=self.logger,
            permission_manager=permission_manager,
            edit_history=self.edit_history,
            exclude_folders=[self.config.get_forshape_folder_name(), ".git", "__pycache__"],
            exclude_patterns=[],
        )
        tool_manager.register_provider(file_access_tools)

    def _register_diff_step_tools(self, tool_manager: ToolManager) -> None:
        """
        Register tools for the diff step with the tool manager.

        Args:
            tool_manager: ToolManager instance to register tools with
        """
        from agent.tools.file_diff_tools import FileDiffTools

        tool_manager.register_provider(FileDiffTools(edit_history=self.edit_history))

    def _register_router_step_tools(
        self,
        tool_manager: ToolManager,
        wait_manager: WaitManager,
        permission_manager: PermissionManager,
        step_jump_controller: StepJumpController,
    ) -> None:
        """
        Register tools for the router step with the tool manager.

        The router step has access to all main step tools plus ConstantsTools and StepJumpTools.

        Args:
            tool_manager: ToolManager instance to register tools with
            wait_manager: WaitManager instance for user interactions
            permission_manager: PermissionManager instance for permission checks
            step_jump_controller: StepJumpController for step flow control
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

        # Register constants analysis tools
        constants_tools = ConstantsTools(working_dir=str(self.config.working_dir), logger=self.logger)
        tool_manager.register_provider(constants_tools)

        # Register step jump tools for routing to other workflows
        step_jump_tools = StepJumpTools(controller=step_jump_controller, current_step="router")
        tool_manager.register_provider(step_jump_tools)

    def run(self):
        """Start the interactive GUI interface."""
        # Check if initialization was successful
        if not getattr(self, "_init_success", True):
            return 1

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
            window_close_callback=ForShapeAI._clear_active_window,
        )

        # Store the window as the active window
        ForShapeAI._active_window = self.main_window

        self.main_window.show()

        # Set the message handler for prestart checker
        self.prestart_checker.set_message_handler(self.main_window.message_handler)

        # Check for newer version in background
        self.prestart_checker.check_version()

        # Create and register document observer to monitor active document changes
        self.document_observer = ActiveDocumentObserver(
            prestart_checker=self.prestart_checker,
            logger=self.logger,
            message_handler=self.main_window.message_handler,
            enable_ai_mode_callback=self.main_window.enable_ai_mode,
        )
        if self.document_observer.register():
            self.logger.info("Document observer registered successfully")
        else:
            self.logger.warning("Failed to register document observer")

        # Run initial prestart check.
        # If status becomes "ready", the completion_callback on PrestartChecker
        # fires _complete_initialization automatically.
        status = self.prestart_checker.check()
        if status == "ready":
            self.main_window.enable_ai_mode()

        # Bring window to front after initialization
        self.main_window.raise_()
        self.main_window.activateWindow()

        # Start Qt event loop
        return app.exec_()

    def handle_exit(self):
        """Handle graceful exit of the application."""
        # Unregister document observer
        if self.document_observer is not None:
            self.document_observer.unregister()
            self.logger.info("Document observer unregistered")

        # Write session end marker to log
        if self.history_logger is not None:
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
