@echo off
:: ============================================================================
::  install_core.bat  -  shared installer used by every per-DCC install_user.bat
::
::  Each DCC's install_user.bat is a thin wrapper that just calls this with:
::      call "<path>\install_core.bat" "<source subpath>" "<destination>" [mirror]
::  e.g.
::      call "...\_core\install_core.bat" "Environment\Blender" "%APPDATA%\Blender Foundation\Blender"
::
::  %1 = source subpath under the GSTools root (e.g. Environment\Blender)
::  %2 = destination directory
::  %3 = optional "mirror"
::
::  Default: additive copy. New and changed files are copied, nothing at the
::  destination is deleted, so it is safe to merge into a folder that also holds the
::  user's own files or other installers' files.
::
::  mirror: the destination becomes an exact copy of the source, and files that are
::  gone from the source are DELETED. Only for folders the studio owns outright
::  (e.g. Documents\maya\GlendaStudio). Refused unless source and destination have
::  the same folder name, so a typo can't wipe a parent folder. A caller can set
::  MIRROR_KEEP to file names that are never copied or deleted (files that only
::  exist at the destination, like share-only shelves).
::
::  The GSTools root is resolved by walking up from THIS file's own location until a
::  folder containing an "Environment" subfolder is found, so wrappers never need to
::  re-implement the walk-up logic. Run on login by the domain controller.
:: ============================================================================
setlocal EnableDelayedExpansion

if "%~1"=="" (
    echo [ERROR] install_core: missing source subpath argument.
    exit /b 1
)
if "%~2"=="" (
    echo [ERROR] install_core: missing destination argument.
    exit /b 1
)

:: GSTools root = the nearest ancestor of THIS file that contains an "Environment"
:: subfolder. We walk up from %~dp0 instead of assuming a fixed depth, so this keeps
:: working if the Deploy tree is moved/nested differently relative to the root.
set "ROOT="
for %%I in ("%~dp0.") do set "CURRENT=%%~fI"
:find_root
if exist "%CURRENT%\Environment\" (
    set "ROOT=%CURRENT%"
    goto :found_root
)
for %%I in ("%CURRENT%\..") do set "PARENT=%%~fI"
if /I "%PARENT%"=="%CURRENT%" (
    echo [ERROR] Could not find a folder containing 'Environment' above: %~dp0
    exit /b 1
)
set "CURRENT=%PARENT%"
goto :find_root
:found_root

set "SRC=%ROOT%\%~1"
set "DST=%~2"

if not exist "%SRC%" (
    echo [ERROR] Source not found: %SRC%
    exit /b 1
)

:: Dev-only cruft that must never be deployed: VCS metadata, agent config, editor
:: settings, Python bytecode caches, and the gitignored Library/ folder. Matched by
:: bare name so they're excluded wherever they appear in the tree. Harmless for the
:: per-DCC subtree copies (which don't contain these); essential for the full-root
:: server push in install_server.bat.
set "EXCLUDE_DIRS=.git .claude .vscode .idea __pycache__ __pycache_ Library"
set "EXCLUDE_FILES=.gitignore .gitattributes *.pyc *.md"

set "MODE=/E"
if /I "%~3"=="mirror" (
    for %%I in ("%SRC%\.") do set "SRC_NAME=%%~nxI"
    for %%I in ("%DST%\.") do set "DST_NAME=%%~nxI"
    if /I not "!SRC_NAME!"=="!DST_NAME!" (
        echo [ERROR] Refusing to mirror "!SRC_NAME!" into a folder named "!DST_NAME!": %DST%
        endlocal & exit /b 1
    )
    set "MODE=/MIR"
    if defined MIRROR_KEEP set "EXCLUDE_FILES=!EXCLUDE_FILES! !MIRROR_KEEP!"
)

:: robocopy flags:
::   /E       all subdirs incl. empty      /MIR      /E + delete what the source lacks
::   /DCOPY:DA  dir timestamps+attrs       /R:2 /W:2  light retry on locked files
::   /XD/XF   exclude the dirs/files above (excluded items are never deleted either)
::   /NP /NFL /NDL  quiet output
:: Without /XO a file whose size or timestamp differs is replaced, newer or older.
robocopy "%SRC%" "%DST%" %MODE% /DCOPY:DA /R:2 /W:2 /NP /NFL /NDL /XD %EXCLUDE_DIRS% /XF %EXCLUDE_FILES%

:: robocopy exit codes 0-7 are success/informational; >=8 is a real failure
if %ERRORLEVEL% GEQ 8 (
    echo [ERROR] robocopy failed with exit code %ERRORLEVEL%
    endlocal & exit /b %ERRORLEVEL%
)

echo [OK] Synced "%~1" -^> "%DST%"
endlocal & exit /b 0
