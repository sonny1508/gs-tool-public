# -*- coding: utf-8 -*-
"""
GSPipeline tool configuration.

Defines exactly which tools appear in the GSPipeline menu/shelf, their order,
their display names, and their icons. Nothing is inferred from filenames - if a
script is not listed here, it is not loaded.

Project tools are listed in Projects/project_config.py instead, in the same
format, and appended after these when that folder is deployed. The public repo
leaves Projects/ out, so never list a project tool here.

Structure
---------
TOOLS is a list of entries. Each entry is one of:

  * A GROUP - a (label, children) tuple. It becomes a submenu. Children is
    itself a list of entries, so groups can nest to any depth:

        GSPipeline > 05 Review > LOD Checker

  * A TOOL - a dict:

        {
            "name":   "LOD Checker",                            # menu/shelf label
            "script": "Review/LOD_Checker/LOD_Checker_UI.py",   # relative to this folder
            "icon":   "LOD_Checker_Icon.png",                   # optional; in Icons/, omit for default
            "hotkey": "Ctrl+Shift+G",                           # optional; see below
        }

Both name and icon are explicit. Icons live in the Icons/ folder next to this
file; a tool with no "icon" (or a missing icon file) uses Maya's default.

"hotkey" binds a shortcut to the tool at startup, in the editable "GSTools"
hotkey set (cloned from Maya_Default if that's current, since Maya_Default is
locked). Modifiers are Ctrl, Alt and Shift, joined with '+'. A shortcut the
artist has already bound to something else is left alone, with a warning. Check
Maya's factory keys first: Maya20XX/scripts/startup/hotkeySetup.mel, where an
upper-case key means Shift.
"""

TOOLS = [
    ("01 Modeling", [
        {"name": "Edge Sensei",     "script": "Modeling/Edge_Sensei_UI.py",                  "icon": "Edge_Sensei_Icon.png"},
        {"name": "Vertex Painter",  "script": "Modeling/Vertex_Painter_UI.py"},
        {"name": "Speed Workflow",  "script": "Modeling/Speed_Workflow/Speed_Workflow_UI.py"},
    ]),

    ("02 Normals", [
        {"name": "GS Normal Tools", "script": "Normals/GS_Normal_Tools_UI.py", "icon": "GS_Normal_Tools_Icon.png"},
    ]),

    ("03 UV", [
        {"name": "Texel Density Visualizer",   "script": "UV/texel-density-visualizer/texel-density-visualizer.py",   "icon": "texel-density-visualzier-icon.png"},
        {"name": "UV Shell Scaler",            "script": "UV/uv-shell-scaler/uv-shell-scaler.py"},
    ]),

    ("04 Files I/O", [
        {"name": "GS File Export",   "script": "Files_IO/gs_file_export.py",   "icon": "GS_File_Export_Icon.png"},
        # Ctrl+Shift+G: free in Maya 2022 and 2026; the same key Blender's GS Pipeline uses.
        {"name": "GS File Transfer", "script": "Files_IO/gs_file_transfer.py", "icon": "GS_File_Transfer_Icon.png",
         "hotkey": "Ctrl+Shift+G"},
    ]),

    ("05 Review", [
        {"name": "LOD Checker",   "script": "Review/LOD_Checker/LOD_Checker_UI.py",     "icon": "LOD_Checker_Icon.png"},
        {"name": "Model Checker", "script": "Review/Model_Checker/modelChecker_UI.py", "icon": "Model_Checker_Icon.png"},
    ]),
]
