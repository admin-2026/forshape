from agent import HistoryEditStep, NextStepJump, StepJumpTools, ToolCallStep, ToolExecutor
from agent.chat_history_manager import HistoryPolicy
from agent.request import DynamicContent, FileLoader, Instruction, RequestBuilder, ToolCall, ToolCallMessage
from agent.tools.tool_manager import ToolManager
from app import Step
from app.forshape.instructions import (
    BASE_INSTRUCTION,
    BEST_PRACTICES,
    LINT_ERR_FIX_SYSTEM,
    LINT_ERR_FIX_USER,
    REVIEW_SYSTEM,
    REVIEW_USER,
    ROUTER_SYSTEM,
    TEMPLATE_FILES_INFO,
)
from app.forshape.step_jumps import ChangedFilesStepJump, LintStepJump
from app.tools import ConstantsTools


def build_doc_print_step(tool_executor, logger) -> ToolCallStep:
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
    return ToolCallStep(
        name="doc_print",
        tool_executor=tool_executor,
        messages=[doc_print_tool_call],
        logger=logger,
        step_jump=NextStepJump("main"),
    )


def build_main_step(config, logger, edit_history, image_context, wait_manager, permission_manager):
    from agent.tools.calculator_tools import CalculatorTools
    from agent.tools.file_access_tools import FileAccessTools
    from agent.tools.interaction_tools import InteractionTools
    from app.tools import FreeCADTools, VisualizationTools

    tool_manager = ToolManager(logger=logger)

    file_access_tools = FileAccessTools(
        working_dir=config.working_dir,
        logger=logger,
        permission_manager=permission_manager,
        edit_history=edit_history,
        exclude_folders=[config.get_forshape_folder_name(), ".git", "__pycache__"],
        exclude_patterns=[],
    )
    tool_manager.register_provider(file_access_tools)

    interaction_tools = InteractionTools(wait_manager)
    tool_manager.register_provider(interaction_tools)

    calculator_tools = CalculatorTools()
    tool_manager.register_provider(calculator_tools)

    freecad_tools = FreeCADTools(permission_manager=permission_manager)
    tool_manager.register_provider(freecad_tools)

    if image_context is not None:
        visualization_tools = VisualizationTools(image_context=image_context)
        tool_manager.register_provider(visualization_tools)

    system_elements = [
        Instruction(BASE_INSTRUCTION + TEMPLATE_FILES_INFO, description="Base instructions and project structure"),
        FileLoader(str(config.get_solid_api_path()), required=True, description="Solid API documentation"),
        FileLoader(str(config.get_sketch_api_path()), required=True, description="Sketch API documentation"),
        Instruction(BEST_PRACTICES, description="Best practices"),
        DynamicContent(tool_manager.get_tool_usage_instructions, description="Tool usage instructions"),
    ]

    user_elements = [
        FileLoader(str(config.get_forshape_path()), required=False, description="User preferences"),
    ]

    request_builder = RequestBuilder(system_elements, user_elements)
    tool_executor = ToolExecutor(tool_manager=tool_manager, logger=logger)

    step = Step(
        name="main",
        request_builder=request_builder,
        tool_executor=tool_executor,
        max_iterations=50,
        logger=logger,
        step_jump=ChangedFilesStepJump("diff", edit_history),
    )

    return step, tool_executor


def build_router_step(
    config, logger, edit_history, image_context, wait_manager, permission_manager, step_jump_controller
):
    from agent.tools.calculator_tools import CalculatorTools
    from agent.tools.file_access_tools import FileAccessTools
    from agent.tools.interaction_tools import InteractionTools
    from app.tools import FreeCADTools, VisualizationTools

    router_tool_manager = ToolManager(logger=logger)

    file_access_tools = FileAccessTools(
        working_dir=config.working_dir,
        logger=logger,
        permission_manager=permission_manager,
        edit_history=edit_history,
        exclude_folders=[config.get_forshape_folder_name(), ".git", "__pycache__"],
        exclude_patterns=[],
    )
    router_tool_manager.register_provider(file_access_tools)

    interaction_tools = InteractionTools(wait_manager)
    router_tool_manager.register_provider(interaction_tools)

    calculator_tools = CalculatorTools()
    router_tool_manager.register_provider(calculator_tools)

    freecad_tools = FreeCADTools(permission_manager=permission_manager)
    router_tool_manager.register_provider(freecad_tools)

    if image_context is not None:
        visualization_tools = VisualizationTools(image_context=image_context)
        router_tool_manager.register_provider(visualization_tools)

    constants_tools = ConstantsTools(working_dir=str(config.working_dir), logger=logger)
    router_tool_manager.register_provider(constants_tools)

    step_jump_tools = StepJumpTools(controller=step_jump_controller, current_step="router")
    router_tool_manager.register_provider(step_jump_tools)

    router_system_elements = [
        Instruction(ROUTER_SYSTEM, description="Router instructions"),
        DynamicContent(router_tool_manager.get_tool_usage_instructions, description="Tool usage instructions"),
    ]

    router_user_elements = [
        FileLoader(str(config.get_forshape_path()), required=False, description="User preferences"),
    ]

    router_request_builder = RequestBuilder(router_system_elements, router_user_elements)
    router_tool_executor = ToolExecutor(tool_manager=router_tool_manager, logger=logger)

    router_step = Step(
        name="router",
        request_builder=router_request_builder,
        tool_executor=router_tool_executor,
        max_iterations=20,
        logger=logger,
        step_jump=None,
    )

    return router_step, router_tool_executor


def build_lint_step(config, logger) -> ToolCallStep:
    from agent.tools.python_lint_tools import PythonLintTools

    lint_tool_manager = ToolManager(logger=logger)
    lint_tool_manager.register_provider(PythonLintTools(exclude_dirs=[".git", ".forshape"]))
    lint_tool_executor = ToolExecutor(tool_manager=lint_tool_manager, logger=logger)

    lint_tool_call = ToolCallMessage(
        tool_calls=[
            ToolCall(
                name="lint_python",
                arguments={
                    "directory": str(config.working_dir),
                    "format": True,
                    "fix": True,
                    "ignore": ["F403", "F405"],
                },
                copy_result_to_response=True,
                key="lint_step_lint_python",
                policy=HistoryPolicy.LATEST,
            ),
        ]
    )

    return ToolCallStep(
        name="lint",
        tool_executor=lint_tool_executor,
        messages=[lint_tool_call],
        logger=logger,
        step_jump=LintStepJump("lint_err_fix"),
    )


def build_lint_err_fix_step(config, logger, edit_history, permission_manager) -> Step:
    from agent.tools.file_access_tools import FileAccessTools

    lint_err_fix_tool_manager = ToolManager(logger=logger)

    file_access_tools = FileAccessTools(
        working_dir=config.working_dir,
        logger=logger,
        permission_manager=permission_manager,
        edit_history=edit_history,
        exclude_folders=[config.get_forshape_folder_name(), ".git", "__pycache__"],
        exclude_patterns=[],
    )
    lint_err_fix_tool_manager.register_provider(file_access_tools)

    lint_err_fix_tool_executor = ToolExecutor(tool_manager=lint_err_fix_tool_manager, logger=logger)

    lint_err_fix_request_builder = RequestBuilder(
        system_elements=[Instruction(LINT_ERR_FIX_SYSTEM, description="Lint and compile error fix instructions")],
        user_elements=[Instruction(LINT_ERR_FIX_USER, description="Lint and compile error fix task")],
    )

    return Step(
        name="lint_err_fix",
        request_builder=lint_err_fix_request_builder,
        tool_executor=lint_err_fix_tool_executor,
        max_iterations=30,
        logger=logger,
        step_jump=NextStepJump("drop_lint_history"),
    )


def build_diff_step(edit_history, logger) -> ToolCallStep:
    from agent.tools.file_diff_tools import FileDiffTools

    diff_tool_manager = ToolManager(logger=logger)
    diff_tool_manager.register_provider(FileDiffTools(edit_history=edit_history))
    diff_tool_executor = ToolExecutor(tool_manager=diff_tool_manager, logger=logger)

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

    return ToolCallStep(
        name="diff",
        tool_executor=diff_tool_executor,
        messages=[diff_tool_call],
        logger=logger,
        step_jump=NextStepJump("review"),
    )


def build_review_step(config, logger, edit_history, permission_manager) -> Step:
    from agent.tools.file_access_tools import FileAccessTools

    review_tool_manager = ToolManager(logger=logger)

    file_access_tools = FileAccessTools(
        working_dir=config.working_dir,
        logger=logger,
        permission_manager=permission_manager,
        edit_history=edit_history,
        exclude_folders=[config.get_forshape_folder_name(), ".git", "__pycache__"],
        exclude_patterns=[],
    )
    review_tool_manager.register_provider(file_access_tools)

    review_tool_executor = ToolExecutor(tool_manager=review_tool_manager, logger=logger)

    review_request_builder = RequestBuilder(
        system_elements=[Instruction(REVIEW_SYSTEM, description="Code review instructions")],
        user_elements=[
            FileLoader(str(config.get_review_path()), required=False, description="User review instructions"),
            Instruction(REVIEW_USER, description="Code review task"),
        ],
    )

    return Step(
        name="review",
        request_builder=review_request_builder,
        tool_executor=review_tool_executor,
        max_iterations=30,
        logger=logger,
        step_jump=NextStepJump("drop_review_history"),
    )


def build_drop_lint_history_step(history_manager, logger) -> HistoryEditStep:
    return HistoryEditStep(
        name="drop_lint_history",
        history_manager=history_manager,
        step_names_to_drop=["lint", "lint_err_fix"],
        logger=logger,
    )


def build_drop_review_history_step(history_manager, logger) -> HistoryEditStep:
    return HistoryEditStep(
        name="drop_review_history",
        history_manager=history_manager,
        step_names_to_drop=["diff", "review"],
        logger=logger,
        step_jump=NextStepJump("lint"),
    )
