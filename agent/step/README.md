# Step Module

This module contains the step execution framework for the AI agent pipeline.

## Overview

A **Step** represents a single execution unit in the AI agent workflow. Each step has its own request builder, tool manager, and configuration. Steps can be chained together using **StepJump** classes to control the flow of execution.

## Components

### Step

The main execution unit that runs a tool-calling loop until completion.

```python
from agent.step import Step

step = Step(
    name="main",
    request_builder=request_builder,
    tool_executor=tool_executor,
    max_iterations=50,
    logger=logger,
    step_jump=NextStepJump("next_step"),
)
```

### StepJump

Abstract base class that determines the next step after a step completes.

```python
from agent.step import StepJump

class MyStepJump(StepJump):
    def get_next_step(self, result: StepResult) -> Optional[str]:
        # Return next step name or None to stop
        return "next_step"
```

### NextStepJump

A simple StepJump that always jumps to a fixed next step.

```python
from agent.step import NextStepJump

step_jump = NextStepJump("lint")  # Always goes to "lint" step
```

### DynamicStepJump

A StepJump that checks a `StepJumpController` for dynamic jump/call requests from tools.

```python
from agent.step import DynamicStepJump
from agent import StepJumpController

controller = StepJumpController({"main": ["lint", "export"]})
step_jump = DynamicStepJump(controller, fallback=NextStepJump("lint"))
```

### StepResult

Dataclass returned by step execution containing:
- `history_messages`: Messages to save to chat history
- `api_messages`: Raw API messages from step execution
- `token_usage`: Token usage statistics
- `status`: "completed", "cancelled", "error", "max_iterations", or "call_pending"
- `step_jump`: The StepJump to use for determining the next step

## Step Flow Control

### Jump vs Call

The step module supports two types of flow control via `StepJumpTools`:

#### Jump (One-way transfer)

```
Main Step → jump_to_step("lint") → Lint Step → (follows lint's step_jump)
```

- Execution transfers to the target step
- Does **not** return to the calling step
- Calling step's context is discarded

#### Call (With return)

```
Main Step → call_step("lint") → Lint Step → Main Step resumes
```

- Execution transfers to the target step
- After target completes, returns to calling step
- Calling step's **messages are preserved** and restored on return
- The called step's result is appended to the messages

### How Call Works

1. **LLM invokes `call_step("lint")`** during main step execution
2. **StepJumpController** records:
   - Target step: "lint"
   - Return step: "main"
3. **Step detects call pending**, saves its `messages` to controller
4. **Step returns** with `status="call_pending"`
5. **DynamicStepJump** returns target step ("lint")
6. **Lint step runs** and completes
7. **DynamicStepJump** sees pending return, returns "main"
8. **Main step resumes**:
   - Restores saved messages
   - Appends info about lint's result
   - Continues execution from where it left off

### Message Preservation

When a step calls another step, its full API message history is preserved:

```
Messages before call:
[system, user, assistant+tool_calls, tool_result, assistant+tool_calls, tool_result]

After call returns:
[system, user, assistant+tool_calls, tool_result, assistant+tool_calls, tool_result,
 user: "[Called step completed with result: ...]"]
```

This allows the LLM to maintain full context of its previous work.

## Configuration

### StepJumpController

Controls which steps can jump/call to which other steps:

```python
from agent import StepJumpController

controller = StepJumpController(
    valid_destinations={
        "main": ["lint", "lint_err_fix"],  # main can jump/call to lint or lint_err_fix
        "lint_err_fix": ["lint"],           # lint_err_fix can only jump/call to lint
    }
)
```

### Registering Step Jump Tools

To enable jump/call tools for a step:

```python
from agent import StepJumpTools

# Register for "main" step
step_jump_tools = StepJumpTools(controller, current_step="main")
tool_manager.register_provider(step_jump_tools)
```

## Status Values

| Status | Description |
|--------|-------------|
| `completed` | Step finished normally with a final response |
| `cancelled` | User cancelled the operation |
| `error` | An exception occurred during execution |
| `max_iterations` | Step hit the maximum iteration limit |
| `call_pending` | Step yielded to a called step (will resume later) |

## Example: Complete Setup

```python
from agent import (
    AIAgent, Step, DynamicStepJump, NextStepJump,
    StepJumpController, StepJumpTools, ToolManager, ToolExecutor
)

# Define valid destinations
controller = StepJumpController({
    "main": ["lint", "export"],
    "lint": ["main"],
})

# Create tool manager for main step
tool_manager = ToolManager()
# ... register other tools ...
tool_manager.register_provider(StepJumpTools(controller, "main"))

# Create steps
main_step = Step(
    name="main",
    request_builder=request_builder,
    tool_executor=ToolExecutor(tool_manager),
    step_jump=DynamicStepJump(controller, fallback=NextStepJump("lint")),
)

lint_step = Step(
    name="lint",
    request_builder=lint_request_builder,
    tool_executor=lint_tool_executor,
    step_jump=DynamicStepJump(controller),  # No fallback = stops after lint
)

# Create agent
agent = AIAgent(
    api_key=api_key,
    model=model,
    steps={"main": main_step, "lint": lint_step},
    start_step="main",
    step_jump_controller=controller,
    # ... other params ...
)
```
