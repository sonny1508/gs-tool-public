@echo off
:: Maya user install. All copy logic lives in _core\install_core.bat.
:: GlendaStudio\ is studio-owned and mirrored: files removed upstream are removed here.
:: modules\ and plug-ins\ are shared with other installers, so ours are only added.
:: Nothing goes into the per-version folders: Maya.env and prefs belong to the artist.
setlocal
set "CORE=%~dp0..\..\_core\install_core.bat"
set "MAYA=%USERPROFILE%\Documents\maya"

call "%CORE%" "Environment\Autodesk\Maya\GlendaStudio" "%MAYA%\GlendaStudio" mirror
if errorlevel 1 goto :end
call "%CORE%" "Environment\Autodesk\Maya\modules" "%MAYA%\modules"
if errorlevel 1 goto :end
call "%CORE%" "Environment\Autodesk\Maya\plug-ins" "%MAYA%\plug-ins"

:end
endlocal & exit /b %ERRORLEVEL%
