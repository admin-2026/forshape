# ForShape AI - FreeCAD Installation

## Prerequisites

- FreeCAD installed

## Toolbar Installation

Install ForShape AI as a toolbar button in FreeCAD's Part and PartDesign workbenches.

### Step 1: Run the install script

In FreeCAD's Python console, run:

```python
script_folder = 'C:/path/to/shape_gen_2'; exec(open(f'{script_folder}/install_macro.py').read())
```

Replace `C:/path/to/shape_gen_2` with the actual path to the forshape app folder.

### Step 2: Restart FreeCAD

Close and reopen FreeCAD. A **ForShape AI** toolbar button with an icon will appear when you switch to the **Part** or **Part Design** workbench.

### Step 3: Click the toolbar button

Click the ForShape AI button to launch the assistant.

## Reinstallation

If you move the project folder to a new location, re-run the install script with the updated path:

```python
script_folder = 'C:/new/path/to/shape_gen_2'; exec(open(f'{script_folder}/install_macro.py').read())
```

Then restart FreeCAD.
