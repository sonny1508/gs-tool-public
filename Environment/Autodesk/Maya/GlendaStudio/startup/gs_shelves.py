"""
Studio-owned shelves, rebuilt from the deployed files on every launch.

Maya writes every loaded shelf into prefs/shelves when it closes and loads that
copy on the next launch, so a deployed shelf file never reaches an artist after
their first session. Rebuilding the tab at startup makes the deployed file win;
whatever Maya saved on exit is replaced again on the next launch. Edits an
artist makes to these shelves by hand do not survive a restart.
"""
import os

import maya.cmds as cmds
import maya.mel as mel

SHELVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shelves")

# (file in GlendaStudio/shelves, first Maya version that gets it)
# shelf_GIANTS.mel is not in git: it links into Perforce, so it only exists on the share.
STUDIO_SHELVES = [
    ("shelf_GSTools.mel", 2022),
    ("shelf_GIANTS.mel", 2026),
]


def _shelf_top_level():
    top = mel.eval("$gsShelfTopTmp = $gShelfTopLevel")
    if top and cmds.shelfTabLayout(top, exists=True):
        return top
    return None


def replace_shelf(name, fill):
    """Recreate the shelf tab `name`, filled by fill(shelf), at the position it had.

    The position matters: Maya fills unopened tabs lazily by index (loadShelf in
    startup/shelf.mel reads optionVar shelfName<index>), so a tab that moved to
    the end would leave every later index pointing at the wrong shelf.
    """
    top = _shelf_top_level()
    if not top:
        return None

    tabs = cmds.shelfTabLayout(top, query=True, childArray=True) or []
    selected = cmds.shelfTabLayout(top, query=True, selectTab=True)
    index = tabs.index(name) + 1 if name in tabs else 0
    if index:
        cmds.deleteUI("{}|{}".format(top, name), layout=True)

    shelf = cmds.shelfLayout(name, parent=top)
    cmds.setParent(shelf)
    try:
        fill(shelf)
    finally:
        cmds.setParent(top)

    count = cmds.shelfTabLayout(top, query=True, numberOfChildren=True)
    if index and index != count:
        cmds.tabLayout(top, edit=True, moveTab=(count, index))
    if selected == name:
        cmds.shelfTabLayout(top, edit=True, selectTab=name)
    return shelf


def _source_shelf_file(path, name):
    mel.eval('source "{}";'.format(path.replace("\\", "/")))
    mel.eval("shelf_{}();".format(name))


def load_studio_shelves():
    version = cmds.about(apiVersion=True) // 10000
    for filename, first_version in STUDIO_SHELVES:
        if version < first_version:
            continue
        path = os.path.join(SHELVES_DIR, filename)
        name = os.path.splitext(filename)[0][len("shelf_"):]
        if not os.path.isfile(path):
            print("[GlendaStudio] {} shelf not deployed, keeping the last saved one.".format(name))
            continue
        try:
            replace_shelf(name, lambda shelf, p=path, n=name: _source_shelf_file(p, n))
        except Exception as exc:
            cmds.warning("[GlendaStudio] Could not rebuild the {} shelf: {}".format(name, exc))
