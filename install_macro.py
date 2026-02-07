"""
Install ForShape AI as a FreeCAD toolbar button via the Mod system.

Usage from FreeCAD Python console:
    script_folder = 'C:/path/to/shape_gen_2'; exec(open(f'{script_folder}/install_macro.py').read())
"""

import os
import shutil

import FreeCAD

_MACRO_NAME = "ForShapeAI"
_MACRO_FILE = f"{_MACRO_NAME}.FCMacro"
_ICON_FILE = "forshape_icon.svg"
_CMD_NAME = "ForShapeAI_Launch"

# script_folder is set by the caller before exec()
_folder = script_folder  # noqa: F821
_macro_dir = FreeCAD.getUserMacroDir(True)
_mod_dir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", _MACRO_NAME)

_steps = [
    "Copying macro file",
    "Copying icon",
    "Installing Mod module",
    "Adding toolbar",
    "Cleaning up old entries",
]
_total = len(_steps)


def _progress(step_idx, detail=""):
    msg = f"[{step_idx + 1}/{_total}] {_steps[step_idx]}"
    if detail:
        msg += f": {detail}"
    print(msg)


# Step 1: Copy .FCMacro to FreeCAD macro directory
_progress(0)
_src_macro = os.path.join(_folder, _MACRO_FILE)
_dst_macro = os.path.join(_macro_dir, _MACRO_FILE)
shutil.copy2(_src_macro, _dst_macro)
_progress(0, f"copied to {_dst_macro}")

# Step 2: Copy icon to macro directory
_src_icon = os.path.join(_folder, _ICON_FILE)
_dst_icon = os.path.join(_macro_dir, _ICON_FILE)
_has_icon = os.path.exists(_src_icon)
if _has_icon:
    _progress(1)
    shutil.copy2(_src_icon, _dst_icon)
    _progress(1, f"copied to {_dst_icon}")
else:
    _progress(1, "skipped (icon not found)")

# Step 3: Create Mod/ForShapeAI/InitGui.py
# This registers the command on every FreeCAD startup via FreeCADGui.addCommand().
# Unlike the Macro parameter system, this is NOT overwritten by MacroCommand::save().
_progress(2)
os.makedirs(_mod_dir, exist_ok=True)

_icon_path = _dst_icon.replace("\\", "/")
_initgui_content = f'''\
import os
import sys

import FreeCAD
import FreeCADGui


class ForShapeAICommand:
    def GetResources(self):
        return {{
            "Pixmap": "{_icon_path}",
            "MenuText": "ForShape AI",
            "ToolTip": "Launch ForShape AI - 3D shape generation assistant",
        }}

    def Activated(self):
        macro_path = os.path.join(FreeCAD.getUserMacroDir(True), "{_MACRO_FILE}")
        exec(compile(open(macro_path).read(), macro_path, "exec"))

    def IsActive(self):
        return True


FreeCADGui.addCommand("{_CMD_NAME}", ForShapeAICommand())
'''

_initgui_path = os.path.join(_mod_dir, "InitGui.py")
with open(_initgui_path, "w") as f:
    f.write(_initgui_content)
_progress(2, f"created {_initgui_path}")

# Store script folder in a param so the .FCMacro can find the project at runtime
_param = FreeCAD.ParamGet(f"User parameter:BaseApp/Preferences/{_MACRO_NAME}")
_param.SetString("ScriptFolder", _folder)
_progress(2, "script folder saved")

# Step 4: Add toolbar to Global workbench
_progress(3)
_tb = FreeCAD.ParamGet(f"User parameter:BaseApp/Workbench/Global/Toolbar/Custom_{_MACRO_NAME}")
_tb.SetString("Name", "ForShape AI")
_tb.SetString(_CMD_NAME, "FreeCAD")
_tb.SetBool("Active", True)
_progress(3, "added to Global toolbar")

# Step 5: Clean up old entries from previous install approaches
_progress(4)
_macros_root = FreeCAD.ParamGet("User parameter:BaseApp/Macro/Macros")
for _g in list(_macros_root.GetGroups()):
    _gp = FreeCAD.ParamGet(f"User parameter:BaseApp/Macro/Macros/{_g}")
    if _gp.GetString("Script") == _MACRO_FILE:
        _macros_root.RemGroup(_g)
        print(f"  Removed old macro entry: {_g}")
# Clean up old non-numeric entry
_old_key = f"Std_Macro_{_MACRO_NAME}"
if _old_key in _macros_root.GetGroups():
    _macros_root.RemGroup(_old_key)
    print(f"  Removed old macro entry: {_old_key}")
# Clean up stale workbench-specific toolbars
for _wb in ["PartWorkbench", "PartDesignWorkbench"]:
    _wb_root = FreeCAD.ParamGet(f"User parameter:BaseApp/Workbench/{_wb}/Toolbar")
    for _g in list(_wb_root.GetGroups()):
        if _MACRO_NAME in _g:
            _wb_root.RemGroup(_g)
            print(f"  Removed stale toolbar: {_wb}/Toolbar/{_g}")
# Clean up old toolbar command references
for _key in list(_tb.GetStrings()):
    if _key.startswith("Std_Macro_") and _key != _CMD_NAME:
        _tb.RemString(_key)
_progress(4, "done")

print("[Done] Installation complete. Restart FreeCAD to see the toolbar button.")
