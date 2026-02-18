<h1 align="center">ForShape AI <img src="forshape_icon.svg" alt="ForShape AI icon" width="32" height="32" /></h1>

<p align="center">
  <img src="assets/readme/teaser_shape.jpg" alt="Teaser shape" width="50%" />
</p>

<p align="center">
  <a href="https://discord.gg/kgqWRRvCqu"><img src="https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://forum.freecad.org/viewtopic.php?t=103176"><img src="https://img.shields.io/badge/FreeCAD_Forum-Topic-orange?logo=freecad&logoColor=white" alt="FreeCAD Forum" /></a>
</p>

ForShape AI is an AI-powered FreeCAD plugin that lets you create and manipulate 3D shapes through natural language.

**Workflow:** User input → AI agent → Python code → 3D parametric design. You describe what you want in natural language, the AI agent translates your description into FreeCAD Python scripts, and FreeCAD executes them to produce parametric 3D models.

## Installation

### Prerequisites

- FreeCAD v1.0.2 or later installed.

### Toolbar Installation

Install ForShape AI as a toolbar button in FreeCAD's Part and PartDesign workbenches.

#### Step 1: Run the install script

First, please download this repository and extract it to your preferred location on your system.

In FreeCAD's Python console, run:

```python
script_folder = 'C:/path/to/your/download'; exec(open(f'{script_folder}/install_macro.py').read())
```

Replace `C:/path/to/your/download` with the actual path to the forshape app folder.

#### Step 2: Restart FreeCAD

Close and reopen FreeCAD. A **ForShape AI** toolbar button with an icon <img src="forshape_icon.svg" alt="ForShape AI icon" width="24" height="24"> will appear when you switch to the **Part** or **Part Design** workbench.

#### Step 3: Click the toolbar button

Click the ForShape AI button to launch the assistant.

### Reinstallation

If you move the project folder to a new location, re-run the install script with the updated path:

```python
script_folder = 'C:/new/path/to/new/location'; exec(open(f'{script_folder}/install_macro.py').read())
```

Then restart FreeCAD.

## Getting Started

1. To launch the application, click the chat bubble icon <img src="forshape_icon.svg" alt="ForShape AI icon" width="20" height="20" />. Upon first launch, you will be prompted to install the necessary dependencies.

<p align="center">
  <img src="assets/readme/dependency_install.jpg" alt="Dependency installation prompt" width="50%" />
</p>

2. To use the AI features, please provide your own LLM API key. Navigate to the **Model** menu and select **Add API Key** to configure your credentials.

   *Note: Only one API key from your preferred provider is required.*

<p align="center">
  <img src="assets/readme/set_api_key.jpg" alt="API key configuration" width="50%" />
</p>

3. Enter your design prompt in the input field and press Enter. The AI agent will assist you in generating parametric 3D models based on your description.

<p align="center">
  <img src="assets/readme/type_prompt.jpg" alt="Typing a prompt" width="50%" />
</p>

4. Once the AI agent has generated the necessary scripts, click the **Build** button. FreeCAD will then construct the 3D object based on the generated code.

<p align="center">
  <img src="assets/readme/build.jpg" alt="Building the object" width="50%" />
</p>

5. After building, you may fine-tune your design using the **Variables** view, which displays all parameters and expressions used in generating the 3D object. To save your work, use the **Export** button to export the final model.

<p align="center">
  <img src="assets/readme/var_view.jpg" alt="Variables view and export" width="50%" />
</p>

## Tips

### Communicating with the AI for Geometry and Parametric Design

**Use X, Y, Z coordinates — avoid vague directional words.**
Relative terms like width, height, depth, front, back, top, bottom, left, and right are ambiguous and can confuse the AI. Use axis-aligned language instead: "extend 50mm in X", "move 10mm in Z", "rotate 90° around the Y axis". For example, instead of "make the box wider and shorter", say "increase X to 80mm and decrease Z to 15mm".

**Use standard geometric terminology.**
Terms like extrude, revolve, loft, chamfer, fillet, boolean union/difference/intersection, and mirror are well understood by the AI and produce more accurate results.

**Describe spatial relationships explicitly.**
Specify how parts relate to each other using coordinates and axes: "center the hole on the face with the highest Z value", "align the cylinder's axis with the Z axis", "place the bracket flush against the face at X=0".

**Expose parameters by name.**
If you want something to be adjustable later, say so: "use a variable `wall_thickness` for the wall width so I can change it". Named variables appear in the Variables view and can be tweaked without regenerating the design.

**Build incrementally.**
Start with the base shape, confirm it looks right, then ask for features one at a time: holes, fillets, cutouts. This makes it easier to catch errors early.

**Describe symmetry and patterns.**
The AI handles repetition well when you name it: "4 evenly spaced holes on a 60mm bolt circle", "mirror the bracket about the YZ plane", "linear pattern of 6 ribs with 10mm spacing".

**State what should stay fixed vs. what can vary.**
For example: "keep the outer diameter fixed at 100mm, but let the wall thickness be a parameter".


## Development

The best way to get started with development is probably using an AI agent. The agent can read the codebase, understand the project structure, and help you implement features or fix bugs with full context.

### Project Structure


- **`agent/`** — AI agent orchestration: LLM API integration, multi-step workflows, tool execution, chat history, and API key management.
- **`app/`** — GUI and application layer: main window, configuration, UI components, widgets, and background workers.
- **`shapes/`** — FreeCAD shape generation library: parametric primitives, boolean operations, transforms, edge features, and export. See [`shapes/README.md`](shapes/README.md) for the API reference.
