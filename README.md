# ForShape AI

ForShape AI is an AI-powered FreeCAD plugin that lets you create and manipulate 3D shapes through natural language.

**Workflow:** User input → AI agent → Python code → 3D parametric design. You describe what you want in plain language, the AI agent translates your description into FreeCAD Python scripts, and FreeCAD executes them to produce parametric 3D models.

## Installation

### Prerequisites

- FreeCAD v1.0.2 or later installed.

### Toolbar Installation

Install ForShape AI as a toolbar button in FreeCAD's Part and PartDesign workbenches.

#### Step 1: Run the install script

In FreeCAD's Python console, run:

```python
script_folder = 'C:/path/to/your/download'; exec(open(f'{script_folder}/install_macro.py').read())
```

Replace `C:/path/to/your/download` with the actual path to the forshape app folder.

#### Step 2: Restart FreeCAD

Close and reopen FreeCAD. A **ForShape AI** toolbar button with an icon will appear when you switch to the **Part** or **Part Design** workbench.

#### Step 3: Click the toolbar button

Click the ForShape AI button to launch the assistant.

### Reinstallation

If you move the project folder to a new location, re-run the install script with the updated path:

```python
script_folder = 'C:/new/path/to/new/location'; exec(open(f'{script_folder}/install_macro.py').read())
```

Then restart FreeCAD.

## Development

The best way to get started with development is probably using an AI agent. The agent can read the codebase, understand the project structure, and help you implement features or fix bugs with full context.

### Project Structure


- **`agent/`** — AI agent orchestration: LLM API integration, multi-step workflows, tool execution, chat history, and API key management.
- **`app/`** — GUI and application layer: main window, configuration, UI components, widgets, and background workers.
- **`shapes/`** — FreeCAD shape generation library: parametric primitives, boolean operations, transforms, edge features, and export. See [`shapes/README.md`](shapes/README.md) for the API reference.
