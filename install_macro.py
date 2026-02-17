"""
Install ForShape AI as a FreeCAD toolbar button via the Mod system.

Usage from FreeCAD Python console:
    script_folder = 'C:/path/to/shape_gen_2'; exec(open(f'{script_folder}/install_macro.py').read())
"""

import os
import shutil

import FreeCAD

_MIN_FC_VERSION = (1, 0, 2)


def _install(folder):
    fc_ver = tuple(int(x) for x in FreeCAD.Version()[:3])
    if fc_ver < _MIN_FC_VERSION:
        ver_str = ".".join(str(x) for x in fc_ver)
        min_str = ".".join(str(x) for x in _MIN_FC_VERSION)
        print(f"[Error] FreeCAD {min_str} or later is required (found {ver_str}). Installation aborted.")
        return

    MACRO_NAME = "ForShapeAI"
    MACRO_FILE = f"{MACRO_NAME}.FCMacro"
    ICON_FILE = "forshape_icon.svg"
    CMD_NAME = "ForShapeAI_Launch"

    macro_dir = FreeCAD.getUserMacroDir(True)
    mod_dir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", MACRO_NAME)

    steps = [
        "Copying macro file",
        "Copying icon",
        "Installing Mod module",
        "Adding toolbar",
        "Cleaning up old entries",
    ]
    total = len(steps)

    def progress(step_idx, detail=""):
        msg = f"[{step_idx + 1}/{total}] {steps[step_idx]}"
        if detail:
            msg += f": {detail}"
        print(msg)

    # Step 1: Copy .FCMacro to FreeCAD macro directory
    progress(0)
    src_macro = os.path.join(folder, MACRO_FILE)
    dst_macro = os.path.join(macro_dir, MACRO_FILE)
    shutil.copy2(src_macro, dst_macro)
    progress(0, f"copied to {dst_macro}")

    # Step 2: Copy icon to macro directory
    src_icon = os.path.join(folder, ICON_FILE)
    dst_icon = os.path.join(macro_dir, ICON_FILE)
    has_icon = os.path.exists(src_icon)
    if has_icon:
        progress(1)
        shutil.copy2(src_icon, dst_icon)
        progress(1, f"copied to {dst_icon}")
    else:
        progress(1, "skipped (icon not found)")

    # Step 3: Create Mod/ForShapeAI/InitGui.py
    # This registers the command on every FreeCAD startup via FreeCADGui.addCommand().
    # Unlike the Macro parameter system, this is NOT overwritten by MacroCommand::save().
    progress(2)
    os.makedirs(mod_dir, exist_ok=True)

    icon_path = dst_icon.replace("\\", "/")
    initgui_content = f'''\
import os
import sys

import FreeCAD
import FreeCADGui


class ForShapeAICommand:
    def GetResources(self):
        return {{
            "Pixmap": "{icon_path}",
            "MenuText": "ForShape AI",
            "ToolTip": "Launch ForShape AI - 3D shape generation assistant",
        }}

    def Activated(self):
        macro_path = os.path.join(FreeCAD.getUserMacroDir(True), "{MACRO_FILE}")
        exec(compile(open(macro_path).read(), macro_path, "exec"))

    def IsActive(self):
        return True


FreeCADGui.addCommand("{CMD_NAME}", ForShapeAICommand())
'''

    initgui_path = os.path.join(mod_dir, "InitGui.py")
    with open(initgui_path, "w") as f:
        f.write(initgui_content)
    progress(2, f"created {initgui_path}")

    # Store script folder in a param so the .FCMacro can find the project at runtime
    param = FreeCAD.ParamGet(f"User parameter:BaseApp/Preferences/{MACRO_NAME}")
    param.SetString("ScriptFolder", folder)
    progress(2, "script folder saved")

    # Step 4: Add toolbar to Global workbench
    progress(3)
    tb = FreeCAD.ParamGet(f"User parameter:BaseApp/Workbench/Global/Toolbar/Custom_{MACRO_NAME}")
    tb.SetString("Name", "ForShape AI")
    tb.SetString(CMD_NAME, "FreeCAD")
    tb.SetBool("Active", True)
    progress(3, "added to Global toolbar")

    # Step 5: Clean up old entries from previous install approaches
    progress(4)
    macros_root = FreeCAD.ParamGet("User parameter:BaseApp/Macro/Macros")
    for g in list(macros_root.GetGroups()):
        gp = FreeCAD.ParamGet(f"User parameter:BaseApp/Macro/Macros/{g}")
        if gp.GetString("Script") == MACRO_FILE:
            macros_root.RemGroup(g)
            print(f"  Removed old macro entry: {g}")
    # Clean up old non-numeric entry
    old_key = f"Std_Macro_{MACRO_NAME}"
    if old_key in macros_root.GetGroups():
        macros_root.RemGroup(old_key)
        print(f"  Removed old macro entry: {old_key}")
    # Clean up stale workbench-specific toolbars
    for wb in ["PartWorkbench", "PartDesignWorkbench"]:
        wb_root = FreeCAD.ParamGet(f"User parameter:BaseApp/Workbench/{wb}/Toolbar")
        for g in list(wb_root.GetGroups()):
            if MACRO_NAME in g:
                wb_root.RemGroup(g)
                print(f"  Removed stale toolbar: {wb}/Toolbar/{g}")
    # Clean up old toolbar command references
    for key in list(tb.GetStrings()):
        if key.startswith("Std_Macro_") and key != CMD_NAME:
            tb.RemString(key)
    progress(4, "done")

    print("[Done] Installation complete. Restart FreeCAD to see the toolbar button.")


_install(script_folder)  # noqa: F821
