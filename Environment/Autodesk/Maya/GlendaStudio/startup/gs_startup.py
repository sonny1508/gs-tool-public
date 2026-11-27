"""
Glenda Studio Maya startup, shared by every Maya version.

modules/GlendaStudio.mod puts this folder on PYTHONPATH, and Maya runs every
userSetup.py it finds on sys.path, so userSetup.py here calls run() at launch.

Everything is queued with executeDeferred so it runs once the main window
exists, in this order: studio plug-ins, GSTools menu, GSPipeline menu + shelf,
studio shelves. Each is its own deferred call, so one failing doesn't stop the
others.

Studio plug-ins are loaded here and set to autoload, rather than shipped in a
pluginPrefs.mel, which Maya rewrites on exit. Our deferred call runs before
Maya's own autoload pass, so it is always the one that loads them.
"""
import os
import sys
import traceback

import maya.cmds as cmds
import maya.utils

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GSTOOLS_SCRIPTS = os.path.join(ROOT, "GSTools", "scripts")
GSPIPELINE_DIR = os.path.join(ROOT, "GSPipeline")

# (plug-in, first Maya version, last Maya version or None)
STUDIO_PLUGINS = [
    ("MayaScanner", 2022, None),
    ("MayaScannerCB", 2022, None),
    ("uvpackmaster3_lib", 2022, 2025),
    ("uvpackmaster3_maya", 2022, 2025),
    ("uvpackmaster4_lib", 2026, None),
    ("uvpackmaster4_maya", 2026, None),
]

_started = False


def _load_studio_plugins():
    version = cmds.about(apiVersion=True) // 10000
    was_modified = cmds.file(query=True, modified=True)
    for name, first, last in STUDIO_PLUGINS:
        if version < first or (last is not None and version > last):
            continue
        if not cmds.pluginInfo(name, query=True, loaded=True):
            try:
                cmds.loadPlugin(name, quiet=True)
            except RuntimeError:
                print("[GlendaStudio] {} is not installed on this machine.".format(name))
                continue
        cmds.pluginInfo(name, edit=True, autoload=True)
    # uvpackmaster creates a settings node in the scene when it loads, which marks
    # the empty startup scene as changed, so Maya asks to save it (and autosave
    # tries to). Same fix as Maya's own verifyCurrentRenderer in supportRenderers.mel.
    if not was_modified and not cmds.file(query=True, sceneName=True):
        cmds.file(modified=False)


def _guarded(label, fn):
    def run():
        try:
            fn()
        except Exception:
            cmds.warning("[GlendaStudio] {} failed to load, see the Script Editor.".format(label))
            traceback.print_exc()
    return run


def _boot_gstools():
    import gstools
    gstools.boot()


def _import_gspipeline():
    import GSPipeline  # noqa: F401  (queues its own menu + shelf build on import)


def _load_studio_shelves():
    import gs_shelves
    gs_shelves.load_studio_shelves()


def run():
    global _started
    if _started:  # userSetup.py runs once per sys.path entry it is found under
        return
    _started = True

    if GSTOOLS_SCRIPTS not in sys.path:
        sys.path.insert(0, GSTOOLS_SCRIPTS)
    if GSPIPELINE_DIR not in sys.path:
        sys.path.append(GSPIPELINE_DIR)

    if cmds.about(batch=True):
        return

    maya.utils.executeDeferred(_guarded("Studio plug-ins", _load_studio_plugins))
    maya.utils.executeDeferred(_guarded("GSTools", _boot_gstools))
    _guarded("GSPipeline", _import_gspipeline)()
    maya.utils.executeDeferred(_guarded("Studio shelves", _load_studio_shelves))
