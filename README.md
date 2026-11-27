# gs-tool-public

Glenda Studio's artist tools for Maya, 3ds Max, Blender and Substance 3D Painter:
modeling, UV, normals, review and file export tools, plus the menus and shelves that
put them in front of artists.

This repository is published automatically from the studio's internal repository, so it
is read-only: please open an issue rather than a pull request.

## What's here

`Environment/` holds one folder per application, laid out exactly like the user folder it
installs into, so installing is a straight copy:

| Folder                               | Copies into                                           |
| ------------------------------------ | ----------------------------------------------------- |
| `Environment/Autodesk/Maya`          | `%USERPROFILE%\Documents\maya`                        |
| `Environment/Autodesk/3dsMax`        | `%LOCALAPPDATA%\Autodesk\3dsMax`                      |
| `Environment/Blender`                | `%APPDATA%\Blender Foundation\Blender`                |
| `Environment/Adobe/SubstancePainter` | `%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter` |

- **Maya** (2022 and 2026): everything lives in `GlendaStudio/`, wired into every Maya
  version by `modules/GlendaStudio.mod`. Maya shows a **GSPipeline** menu and shelf, and
  the older **GSTools** menu and shelf.
- **3ds Max** (2023, 2025, 2026, 2027): a **GSTools** menu in the main menu bar, built at
  startup.
- **Blender** (3.6, 4.5, 5.2): a **GS Pipeline** tab in the 3D View sidebar, plus a few
  add-ons. A startup script enables them.
- **Substance 3D Painter**: a **GS Pipeline** menu, a PBR validator filter, and GS Asset
  Bridge.

## Installing

On Windows, run `Deploy\install_local.bat` from a clone of this repo. It copies every
application's folder into your user profile and closes when it's done. To install one
application only, run its installer under `Deploy\`, for example
`Deploy\Autodesk\Maya\maya_install_user.bat`.

The installers only add and update files, with one exception: `Documents\maya\GlendaStudio`
is made an exact copy of the repo's, so keep your own Maya scripts somewhere else.

Restart the application afterwards.

## Good to know

- A few tools are built around the studio's network: GS File Transfer sends files between
  studio machines, and GS Asset Bridge receives assets from the studio's asset manager.
  Outside the studio they open but have nothing to talk to.
- At startup Maya looks for the studio's plug-ins (MayaScanner, UVPackmaster) and prints a
  line for each one it can't find, then carries on.
- Some tools, mostly in Maya's `GSTools/`, started as free tools by other authors and have
  been reworked since. Their headers credit the original authors.

## Licence

MIT, see [LICENSE](LICENSE). Tools adapted from other authors keep the terms stated in
their own headers.
